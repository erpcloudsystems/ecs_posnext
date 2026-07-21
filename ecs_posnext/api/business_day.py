# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Core helpers for the POS Business Day control system.

Nothing about operating hours is hardcoded here: every window is derived from the
per-profile Time settings added to POS Profile
(custom_business_day_start_time / custom_sales_cutoff_time /
custom_mandatory_closing_deadline_time).
"""

import datetime

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, get_time, getdate, now_datetime


def _as_time(value):
	"""Coerce a Frappe Time field value into a datetime.time (or None)."""
	if value in (None, ""):
		return None
	if isinstance(value, datetime.time):
		return value
	if isinstance(value, datetime.timedelta):
		# Frappe stores Time as timedelta since midnight
		total = int(value.total_seconds())
		return datetime.time(hour=(total // 3600) % 24, minute=(total % 3600) // 60, second=total % 60)
	return get_time(value)


def get_profile_day_settings(pos_profile):
	"""Return the raw business-day settings dict for a POS Profile."""
	fields = [
		"name",
		"company",
		"custom_enable_business_day_control",
		"custom_business_day_start_time",
		"custom_sales_cutoff_time",
		"custom_mandatory_closing_deadline_time",
		"custom_block_new_pos_opening_until_prev_closed",
		"custom_block_sales_after_cutoff",
		"custom_require_all_cashier_shifts_closed",
		"custom_require_no_unpaid_invoices",
		"custom_require_no_partly_paid_invoices",
		"custom_require_no_draft_orders",
		"custom_require_no_on_hold_orders",
		"custom_auto_close_business_day_when_ready",
	]
	return frappe.db.get_value("POS Profile", pos_profile, fields, as_dict=True) or frappe._dict()


def is_business_day_enabled(pos_profile):
	return bool(frappe.db.get_value("POS Profile", pos_profile, "custom_enable_business_day_control"))


def get_business_day_window(pos_profile, at_datetime=None):
	"""Derive the operational-day window that ``at_datetime`` falls into for a profile.

	Rule: the day starts at ``start_time``. A moment ``T`` belongs to business_date
	``date(T)`` when ``time(T) >= start_time``; otherwise (it is after midnight but
	before the next day start) it belongs to ``date(T) - 1``.

	The cut-off / deadline times roll over to the next calendar day whenever they are
	earlier in the clock than the start time (e.g. start 12:00, cut-off 05:00 -> next day).

	Returns a dict: ``business_date``, ``start_datetime``, ``sales_cutoff_datetime``,
	``mandatory_closing_deadline``.
	"""
	settings = get_profile_day_settings(pos_profile)
	at_datetime = get_datetime(at_datetime) if at_datetime else now_datetime()
	start_time = _as_time(settings.get("custom_business_day_start_time")) or datetime.time(0, 0, 0)

	# Which business_date does at_datetime belong to?
	if at_datetime.time() >= start_time:
		business_date = getdate(at_datetime)
	else:
		business_date = add_days(getdate(at_datetime), -1)

	return get_window_for_business_date(pos_profile, business_date)


def get_window_for_business_date(pos_profile, business_date):
	"""Window (start / cut-off / deadline) for a KNOWN business date.

	Use this when the business date is already decided. Do NOT round-trip an existing
	start_datetime through get_business_day_window() to recompute a window — if the
	profile's times have since changed, that would re-derive a *different* business date.
	"""
	settings = get_profile_day_settings(pos_profile)
	start_time = _as_time(settings.get("custom_business_day_start_time")) or datetime.time(0, 0, 0)
	cutoff_time = _as_time(settings.get("custom_sales_cutoff_time"))
	deadline_time = _as_time(settings.get("custom_mandatory_closing_deadline_time"))
	business_date = getdate(business_date)

	start_datetime = datetime.datetime.combine(business_date, start_time)

	def _rollover(t):
		if not t:
			return None
		dt = datetime.datetime.combine(business_date, t)
		if t <= start_time:
			dt = get_datetime(add_days(dt, 1))
		return dt

	return frappe._dict(
		{
			"business_date": business_date,
			"start_datetime": start_datetime,
			"sales_cutoff_datetime": _rollover(cutoff_time),
			"mandatory_closing_deadline": _rollover(deadline_time),
		}
	)


def _enforce_sales_cutoff(pos_profile, business_day):
	"""Block new sales once the profile's sales cut-off has passed (if configured)."""
	settings = get_profile_day_settings(pos_profile)
	if not settings.get("custom_block_sales_after_cutoff"):
		return
	bd = frappe.db.get_value(
		"POS Business Day", business_day, ["status", "sales_cutoff_datetime"], as_dict=True
	)
	if not bd:
		return
	if bd.status == "Closed":
		frappe.throw(_("This POS Business Day is closed. New sales are not allowed."))
	if bd.sales_cutoff_datetime and now_datetime() > get_datetime(bd.sales_cutoff_datetime):
		frappe.throw(
			_("Sales cut-off has been reached for {0}. New sales are blocked for this business day.").format(
				frappe.bold(pos_profile)
			)
		)


def _stamp_branch_business_day(invoice_doc):
	"""Attach a routed order to its TARGET BRANCH's Business Day — and nothing else.

	Deliberately sets NO cashier shift: الفاتورة تتبع الـBusiness Day، والأموال تتبع
	الكاشير اللي حصّل. Resolving from the invoice's `branch` (not the ordering profile)
	is what keeps Call Center orders visible on the branch's day even when the Call
	Center profile itself has no business-day control.
	"""
	branch = invoice_doc.get("branch")
	if not branch:
		return

	profile = frappe.db.get_value(
		"POS Profile",
		{"branch": branch, "custom_enable_business_day_control": 1, "disabled": 0},
		"name",
	)
	if not profile:
		return

	from ecs_posnext.pos_next.doctype.pos_business_day.pos_business_day import get_or_create_for

	day = get_or_create_for(profile)
	if not invoice_doc.get("is_return"):
		_enforce_sales_cutoff(profile, day.name)

	invoice_doc.custom_pos_business_day = day.name
	invoice_doc.custom_pos_cashier_shift = None


def apply_business_day_to_invoice(invoice_doc):
	"""Stamp custom_pos_business_day + custom_pos_cashier_shift on a POS invoice.

	Invoice follows the Business Day; the shift that owns it is the one linked to the
	invoice's POS Opening Shift. Also enforces the sales cut-off for new (non-return) sales.
	Safe no-op when business-day control is disabled for the profile.
	"""
	opening_shift = invoice_doc.get("posa_pos_opening_shift")
	shift_profile = (
		frappe.db.get_value("POS Opening Shift", opening_shift, "pos_profile") if opening_shift else None
	)

	# A ROUTED order — e.g. Call Center taking an order for a branch — was not created
	# by the cashier, so per the Mumo rules it follows the BRANCH's Business Day and is
	# given NO cashier shift. Its money reaches a shift only when someone actually
	# collects/settles it (a Payment Entry on that cashier's shift).
	# Detected structurally (ordering profile != the shift's profile), not by name.
	invoice_profile = invoice_doc.get("pos_profile")
	is_routed_order = bool(invoice_profile and shift_profile and invoice_profile != shift_profile)

	if not shift_profile or not is_business_day_enabled(shift_profile) or is_routed_order:
		_stamp_branch_business_day(invoice_doc)
		return

	cashier_shift = frappe.db.get_value(
		"POS Cashier Shift",
		{"pos_opening_shift": opening_shift},
		["name", "pos_business_day", "status"],
		as_dict=True,
	)
	if not cashier_shift or not cashier_shift.pos_business_day:
		return

	# Never attach anything to an already-closed (counted & reconciled) cashier shift —
	# doing so silently invalidates that cashier's closing figures. Applies to sales AND
	# returns: a refund must be owned by whoever is actually on the drawer now.
	if cashier_shift.status == "Closed":
		frappe.throw(
			_(
				"Cashier shift {0} is already closed and reconciled. "
				"Ask a supervisor to open a new shift before recording this transaction."
			).format(cashier_shift.name),
			title=_("Shift Already Closed"),
		)

	if not invoice_doc.get("is_return"):
		_enforce_sales_cutoff(shift_profile, cashier_shift.pos_business_day)

	invoice_doc.custom_pos_business_day = cashier_shift.pos_business_day
	invoice_doc.custom_pos_cashier_shift = cashier_shift.name


def assert_pos_invoice_cancellable(invoice):
	"""Raise if a business-day POS invoice may not be cancelled.

	Policy (per Mumo rules):
	  * A closed cashier shift / closed Business Day is locked — nothing in it may be
	    cancelled (sales AND returns).
	  * A normal POS sale must never be cancelled; reversals go through a Return /
	    Credit Note on the current open shift (so the reversal is owned and auditable).
	Only applies to invoices stamped with a POS Business Day (i.e. profiles with
	business-day control enabled) — all other invoices cancel as before.

	Accepts a Sales Invoice doc or its name. Call it EARLY (before any destructive
	side effects) so callers that swallow cancel errors still fail cleanly.
	"""
	if not invoice:
		return
	doc = frappe.get_doc("Sales Invoice", invoice) if isinstance(invoice, str) else invoice

	business_day = doc.get("custom_pos_business_day")
	if not business_day:
		return

	shift = doc.get("custom_pos_cashier_shift")
	shift_closed = shift and frappe.db.get_value("POS Cashier Shift", shift, "status") == "Closed"
	bd_closed = frappe.db.get_value("POS Business Day", business_day, "status") == "Closed"
	if shift_closed or bd_closed:
		frappe.throw(
			_(
				"This invoice belongs to a closed cashier shift / business day and cannot be cancelled. "
				"Reverse it with a Return / Credit Note on the current open shift."
			),
			title=_("Closed Period Locked"),
		)

	if not doc.get("is_return"):
		frappe.throw(
			_(
				"POS sales linked to a Business Day cannot be cancelled. "
				"Create a Return / Credit Note instead."
			),
			title=_("Use a Return"),
		)


def block_closed_period_invoice_cancel(doc, method=None):
	"""Sales Invoice before_cancel hook — the backstop for every cancel path."""
	assert_pos_invoice_cancellable(doc)


def log_pos_event(
	action,
	reference_doctype=None,
	reference_name=None,
	pos_profile=None,
	pos_business_day=None,
	old_value=None,
	new_value=None,
	reason=None,
	user=None,
	employee=None,
):
	"""Write a POS Audit Log row. No-ops safely if the doctype is not installed yet."""
	if not frappe.db.exists("DocType", "POS Audit Log"):
		return None
	try:
		doc = frappe.get_doc(
			{
				"doctype": "POS Audit Log",
				"action": action,
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				"pos_profile": pos_profile,
				"pos_business_day": pos_business_day,
				"user": user or frappe.session.user,
				"employee": employee,
				"datetime": now_datetime(),
				"old_value": None if old_value is None else str(old_value),
				"new_value": None if new_value is None else str(new_value),
				"reason": reason,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
		return doc.name
	except Exception:
		frappe.log_error(frappe.get_traceback(), "log_pos_event failed")
		return None
