# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Cashier-shift layer for the POS Business Day system (additive / layered).

The live POS keeps creating `POS Opening Shift` / `POS Closing Shift`. This module
mirrors an opening shift into a `POS Cashier Shift` attached to a `POS Business Day`,
and drives the blind `POS Cashier Shift Closing` (single Expected Cash + shortage/overage).
Cash figures are derived by REUSING the mature reconciliation helpers in
`pos_closing_shift.py` — nothing is re-implemented from scratch.
"""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from ecs_posnext.api.business_day import collected_on_original, is_business_day_enabled, log_pos_event
from ecs_posnext.pos_next.doctype.pos_business_day.pos_business_day import get_or_create_for
from ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift import (
	_get_cash_mode_of_payment,
	get_base_value,
	get_payments_entries,
	get_pos_invoices,
)

_cash_type_cache = {}


def _is_cash_mode(mode):
	if not mode:
		return False
	if mode not in _cash_type_cache:
		_cash_type_cache[mode] = frappe.db.get_value("Mode of Payment", mode, "type") == "Cash"
	return _cash_type_cache[mode]


# ----------------------------------------------------------------------------
# Opening: mirror POS Opening Shift -> POS Cashier Shift + attach Business Day
# ----------------------------------------------------------------------------
def sync_cashier_shift_on_opening(opening_shift, method=None):
	"""doc_event hook on POS Opening Shift.on_submit."""
	if not is_business_day_enabled(opening_shift.pos_profile):
		return
	if frappe.db.exists("POS Cashier Shift", {"pos_opening_shift": opening_shift.name}):
		return

	bday = get_or_create_for(
		opening_shift.pos_profile,
		at_datetime=opening_shift.period_start_date,
		company=opening_shift.company,
		opened_by=opening_shift.user,
	)

	employee = frappe.db.get_value("Employee", {"user_id": opening_shift.user}, "name")
	opening_cash = _opening_cash_amount(opening_shift.name)

	shift = frappe.get_doc(
		{
			"doctype": "POS Cashier Shift",
			"pos_opening_shift": opening_shift.name,
			"pos_business_day": bday.name,
			"pos_profile": opening_shift.pos_profile,
			"company": opening_shift.company,
			"cashier_user": opening_shift.user,
			"employee": employee,
			"opening_datetime": opening_shift.period_start_date,
			"opening_cash": opening_cash,
			"status": "Open",
		}
	)
	shift.flags.ignore_permissions = True
	shift.insert(ignore_permissions=True)

	bday.refresh_summary(save=True)
	log_pos_event(
		action="Opening Shift",
		reference_doctype="POS Cashier Shift",
		reference_name=shift.name,
		pos_profile=opening_shift.pos_profile,
		pos_business_day=bday.name,
		new_value="Open",
	)
	return shift.name


def void_cashier_shift_on_opening_cancel(opening_shift, method=None):
	"""doc_event hook on POS Opening Shift.on_cancel.

	If the underlying opening shift is cancelled, its mirrored POS Cashier Shift must
	not be left dangling as "Open" — it would block its POS Business Day from ever
	closing (and can't be closed itself, since a closing can't link a cancelled doc).
	"""
	shift = frappe.db.get_value(
		"POS Cashier Shift", {"pos_opening_shift": opening_shift.name}, ["name", "status", "pos_business_day"], as_dict=True
	)
	if not shift or shift.status == "Cancelled":
		return

	frappe.db.set_value("POS Cashier Shift", shift.name, "status", "Cancelled")
	log_pos_event(
		action="Override",
		reference_doctype="POS Cashier Shift",
		reference_name=shift.name,
		pos_profile=opening_shift.pos_profile,
		pos_business_day=shift.pos_business_day,
		old_value=shift.status,
		new_value="Cancelled",
		reason=f"POS Opening Shift {opening_shift.name} was cancelled",
	)
	if shift.pos_business_day and frappe.db.exists("POS Business Day", shift.pos_business_day):
		frappe.get_doc("POS Business Day", shift.pos_business_day).refresh_summary(save=True)


@frappe.whitelist()
def backfill_open_shifts(pos_profile=None):
	"""Create the missing POS Cashier Shift + POS Business Day for shifts that were
	already Open before business-day control was enabled (or before this hook shipped).

	Idempotent — skips shifts that already have a Cashier Shift. Returns a summary.
	"""
	filters = {"docstatus": 1, "status": "Open", "pos_closing_shift": ["is", "not set"]}
	if pos_profile:
		filters["pos_profile"] = pos_profile

	created, skipped = [], []
	for row in frappe.get_all("POS Opening Shift", filters=filters, fields=["name", "pos_profile"]):
		if not is_business_day_enabled(row.pos_profile):
			continue
		if frappe.db.exists("POS Cashier Shift", {"pos_opening_shift": row.name}):
			skipped.append(row.name)
			continue
		opening = frappe.get_doc("POS Opening Shift", row.name)
		name = sync_cashier_shift_on_opening(opening)
		created.append({"opening_shift": row.name, "cashier_shift": name})
	frappe.db.commit()
	return {"created": created, "skipped": skipped}


def _opening_cash_amount(opening_shift_name):
	rows = frappe.get_all(
		"POS Opening Shift Detail",
		filters={"parent": opening_shift_name},
		fields=["mode_of_payment", "amount"],
	)
	return sum(flt(r.amount) for r in rows if _is_cash_mode(r.mode_of_payment))


# ----------------------------------------------------------------------------
# Cash figures for the blind close (reusing pos_closing_shift helpers)
# ----------------------------------------------------------------------------
def compute_cash_figures(opening_shift_name):
	"""Return the cash-drawer figures + per-mode reconciliation for a shift."""
	opening = frappe.get_doc("POS Opening Shift", opening_shift_name)
	pos_profile = opening.pos_profile
	cash_mode = _get_cash_mode_of_payment(pos_profile)

	opening_cash = _opening_cash_amount(opening_shift_name)
	cash_sales = cash_refunds = 0.0
	payments = {}
	pos_transactions = []

	invoices = get_pos_invoices(opening_shift_name, "Sales Invoice")
	for inv in invoices:
		cr = inv.get("conversion_rate")
		is_return = inv.get("is_return")
		# Phantom-refund guard: a return of an original that collected nothing must not
		# register any money paid back (cash OR credit). Such a return may still carry a
		# refund payment row from before the return fix; counting it would understate the
		# expected drawer and fake an overage. The transaction line is still recorded.
		if is_return and collected_on_original(inv.get("return_against")) <= 0:
			pos_transactions.append(
				{
					"sales_invoice": inv.name,
					"customer": inv.get("customer"),
					"grand_total": flt(inv.get("grand_total")),
					"posting_date": inv.get("posting_date"),
					"is_return": is_return,
				}
			)
			continue
		for p in inv.get("payments", []):
			amount = get_base_value(p, "amount", "base_amount", cr)
			if p.mode_of_payment == cash_mode:
				amount -= get_base_value(inv, "change_amount", "base_change_amount", cr)
			payments[p.mode_of_payment] = flt(payments.get(p.mode_of_payment, 0)) + amount
			if _is_cash_mode(p.mode_of_payment):
				if is_return:
					cash_refunds += abs(amount)
				else:
					cash_sales += amount
		pos_transactions.append(
			{
				"sales_invoice": inv.name,
				"customer": inv.get("customer"),
				"grand_total": flt(inv.get("grand_total")),
				"posting_date": inv.get("posting_date"),
				"is_return": is_return,
			}
		)

	# Payment Entries settled on this shift (COD / Call Center collections)
	call_center_cash_collected = 0.0
	for py in get_payments_entries(opening_shift_name):
		amount = get_base_value(py, "paid_amount", "base_paid_amount")
		payments[py.mode_of_payment] = flt(payments.get(py.mode_of_payment, 0)) + amount
		if _is_cash_mode(py.mode_of_payment):
			call_center_cash_collected += amount

	# Seed opening balances into the per-mode reconciliation
	reconciliation = {}
	for r in frappe.get_all(
		"POS Opening Shift Detail",
		filters={"parent": opening_shift_name},
		fields=["mode_of_payment", "amount"],
	):
		reconciliation[r.mode_of_payment] = {
			"mode_of_payment": r.mode_of_payment,
			"opening_amount": flt(r.amount),
			"expected_amount": flt(r.amount),
			"closing_amount": 0,
			"difference": 0,
		}
	for mode, amt in payments.items():
		row = reconciliation.setdefault(
			mode,
			{"mode_of_payment": mode, "opening_amount": 0, "expected_amount": 0, "closing_amount": 0, "difference": 0},
		)
		row["expected_amount"] = flt(row["expected_amount"]) + flt(amt)

	return frappe._dict(
		{
			"pos_profile": pos_profile,
			"company": opening.company,
			"shift_start": opening.period_start_date,
			"opening_cash": flt(opening_cash),
			"cash_sales": flt(cash_sales),
			"cash_refunds": flt(cash_refunds),
			"call_center_cash_collected": flt(call_center_cash_collected),
			"payment_reconciliation": list(reconciliation.values()),
			"pos_transactions": pos_transactions,
		}
	)


# ----------------------------------------------------------------------------
# Whitelisted API for the blind-close UI
# ----------------------------------------------------------------------------
@frappe.whitelist()
def prepare_cashier_shift_closing(pos_cashier_shift):
	"""Create (or fetch) a draft closing for a cashier shift, WITHOUT revealing
	expected figures. Only the non-blind fields are returned."""
	shift = frappe.get_doc("POS Cashier Shift", pos_cashier_shift)
	if shift.status == "Closed":
		frappe.throw(_("This cashier shift is already closed."))

	existing = frappe.db.exists(
		"POS Cashier Shift Closing", {"pos_cashier_shift": pos_cashier_shift, "docstatus": ["<", 2]}
	)
	if existing:
		doc = frappe.get_doc("POS Cashier Shift Closing", existing)
	else:
		# Blind: create an EMPTY draft. Figures + expected cash are computed by the
		# controller only after the drawer count is entered and saved.
		doc = frappe.new_doc("POS Cashier Shift Closing")
		doc.pos_cashier_shift = pos_cashier_shift
		doc.supervisor_employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
		doc.shift_end = now_datetime()
		doc.status = "Awaiting Count"
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
	return doc.as_dict()


@frappe.whitelist()
def submit_cashier_shift_closing(pos_cashier_shift_closing, counts=None, actual_credit=0, difference_reason=None):
	"""Post the counted cash + actual credit, compute + reveal reconciliation, and submit."""
	counts = frappe.parse_json(counts) if isinstance(counts, str) else (counts or {})
	doc = frappe.get_doc("POS Cashier Shift Closing", pos_cashier_shift_closing)
	for denom in ("cash_200_egp", "cash_100_egp", "cash_50_egp", "cash_20_egp", "cash_10_egp", "cash_5_egp", "cash_1_egp"):
		if denom in counts:
			doc.set(denom, counts.get(denom) or 0)
	doc.actual_credit = flt(actual_credit)
	doc.cash_counted = 1  # submitting through the API means the count was entered
	if difference_reason:
		doc.difference_reason = difference_reason
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	doc.submit()
	return doc.as_dict()


def auto_close_call_center_shifts(business_day=None):
	"""Close every OPEN Call Center cashier shift (optionally scoped to one business day).

	Call Center agents hold no physical drawer and the closing auto-balances
	(Actual = Expected), so there is nothing to count — these shifts can be closed with no
	human step. Safe + idempotent: skips non-Call-Center and already-closed shifts, and
	logs (never raises) on a per-shift failure so one bad shift can't block the rest.
	"""
	filters = {"status": "Open", "pos_profile": ["like", "%Call Center%"]}
	if business_day:
		filters["pos_business_day"] = business_day

	closed = []
	for name in frappe.get_all("POS Cashier Shift", filters=filters, pluck="name"):
		try:
			doc = prepare_cashier_shift_closing(name)
			submit_cashier_shift_closing(doc["name"], counts={}, actual_credit=0)
			closed.append(name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Auto-close Call Center shift {name} failed")
	return closed
