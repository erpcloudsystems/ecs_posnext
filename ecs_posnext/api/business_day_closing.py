# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""POS Business Day closing validations (the 17 checks) and close/override API.

Each unmet check appends a `POS Closing Issue` row so the manager sees exactly what
blocks the close (never just a generic error). Checks are gated by the matching POS
Profile setting where one exists, and operational checks degrade gracefully when the
underlying doctype/field is not present.
"""

import frappe
from frappe import _
from frappe.utils import flt, get_datetime, now_datetime

from ecs_posnext.api.business_day import get_profile_day_settings, log_pos_event

NON_CLOSED_FOR_REOPEN = ("Open", "Closing Required", "Closing Overdue", "Ready to Close")


def _issue(issue_type, description, required_action, document_type=None, document_no=None, user_employee=None, amount=0):
	return {
		"issue_type": issue_type,
		"description": description,
		"required_action": required_action,
		"document_type": document_type,
		"document_no": document_no,
		"user_employee": user_employee,
		"amount": flt(amount),
		"status": "Open",
	}


def _day_invoice_scope(bd):
	"""Return (opening_shift_names, submitted_invoices, draft_invoices) for the day."""
	cashier_shifts = frappe.get_all(
		"POS Cashier Shift",
		filters={"pos_business_day": bd.name},
		fields=["name", "pos_opening_shift", "status", "cashier_user", "cashier_shift_closing"],
	)
	opening_names = [s.pos_opening_shift for s in cashier_shifts if s.pos_opening_shift]

	submitted = frappe.get_all(
		"Sales Invoice",
		filters={"custom_pos_business_day": bd.name, "docstatus": 1},
		fields=[
			"name", "grand_total", "outstanding_amount", "is_return", "status",
			"posa_pos_opening_shift", "custom_pos_business_day", "owner",
		],
	)
	drafts = []
	if opening_names:
		drafts = frappe.get_all(
			"Sales Invoice",
			filters={"posa_pos_opening_shift": ["in", opening_names], "docstatus": 0},
			fields=["name", "grand_total", "owner", "posa_pos_opening_shift"],
		)
	return cashier_shifts, opening_names, submitted, drafts


def collect_closing_issues(bd):
	"""Return a list of POS Closing Issue row dicts for a POS Business Day."""
	settings = get_profile_day_settings(bd.pos_profile)
	issues = []

	cashier_shifts, opening_names, submitted, drafts = _day_invoice_scope(bd)

	# 1 & 2 — open cashier shift / not closed
	if settings.get("custom_require_all_cashier_shifts_closed", 1):
		for s in cashier_shifts:
			# Only a genuinely Open shift blocks the close. A Cancelled shift (its
			# opening shift was cancelled) has nothing to reconcile and can never be
			# closed, so it must not block the day forever.
			if s.status == "Open":
				issues.append(
					_issue(
						"Cashier Shift Open",
						_("Cashier shift is not closed."),
						_("Close Cashier Shift"),
						document_type="POS Cashier Shift",
						document_no=s.name,
						user_employee=s.cashier_user,
					)
				)

	# 3 — actual counted cash not entered (draft closings)
	draft_closings = frappe.get_all(
		"POS Cashier Shift Closing",
		filters={"pos_business_day": bd.name, "docstatus": 0},
		fields=["name", "cashier", "actual_counted_cash", "difference", "difference_requires_approval", "approved_by"],
	)
	for c in draft_closings:
		if not flt(c.actual_counted_cash):
			issues.append(
				_issue(
					"Actual Cash Not Entered",
					_("Actual counted cash has not been entered for this cashier."),
					_("Enter Actual Cash"),
					document_type="POS Cashier Shift Closing",
					document_no=c.name,
					user_employee=c.cashier,
				)
			)

	# 17 — cashier difference awaiting manager approval (draft or submitted)
	pending_approval = frappe.get_all(
		"POS Cashier Shift Closing",
		filters={"pos_business_day": bd.name, "difference_requires_approval": 1, "approved_by": ["in", ["", None]]},
		fields=["name", "cashier", "difference"],
	)
	for c in pending_approval:
		issues.append(
			_issue(
				"Difference Needs Approval",
				_("Cashier cash difference needs Manager Approval."),
				_("Approve Difference"),
				document_type="POS Cashier Shift Closing",
				document_no=c.name,
				user_employee=c.cashier,
				amount=c.difference,
			)
		)

	# 4 & 5 — unpaid / partly paid submitted invoices
	for inv in submitted:
		if inv.is_return:
			continue
		outstanding = flt(inv.outstanding_amount)
		grand = flt(inv.grand_total)
		if grand <= 0 or outstanding <= 0:
			continue
		if outstanding >= grand and settings.get("custom_require_no_unpaid_invoices", 1):
			issues.append(
				_issue(
					"Unpaid Invoice", _("Invoice is not paid."), _("Collect Payment"),
					document_type="Sales Invoice", document_no=inv.name, user_employee=inv.owner, amount=outstanding,
				)
			)
		elif outstanding < grand and settings.get("custom_require_no_partly_paid_invoices", 1):
			issues.append(
				_issue(
					"Partly Paid Invoice", _("Invoice is only partly paid."), _("Collect Remaining Payment"),
					document_type="Sales Invoice", document_no=inv.name, user_employee=inv.owner, amount=outstanding,
				)
			)

	# 6 — draft orders
	if settings.get("custom_require_no_draft_orders", 1):
		for inv in drafts:
			issues.append(
				_issue(
					"Draft Order", _("Draft invoice/order not finalised."), _("Submit or Cancel"),
					document_type="Sales Invoice", document_no=inv.name, user_employee=inv.owner, amount=inv.grand_total,
				)
			)

	# 15 — submitted invoice on the day's shifts but not linked to this Business Day
	if opening_names:
		orphans = frappe.get_all(
			"Sales Invoice",
			filters={
				"posa_pos_opening_shift": ["in", opening_names],
				"docstatus": 1,
				"custom_pos_business_day": ["in", ["", None]],
			},
			fields=["name", "owner"],
		)
		for inv in orphans:
			issues.append(
				_issue(
					"Invoice Not Linked To Business Day",
					_("Submitted invoice is not linked to a POS Business Day."),
					_("Re-link Invoice"),
					document_type="Sales Invoice", document_no=inv.name, user_employee=inv.owner,
				)
			)

	# 16 — Next POS invoice linked to the day but with no opening shift
	for inv in submitted:
		if not inv.posa_pos_opening_shift:
			issues.append(
				_issue(
					"Invoice Not Linked To Cashier Shift",
					_("Next POS invoice is not linked to a POS Opening/Cashier Shift."),
					_("Re-link Invoice"),
					document_type="Sales Invoice", document_no=inv.name, user_employee=inv.owner,
				)
			)

	# 9 — open KDS orders. Off by default: it only makes sense once staff reliably
	# mark KDS orders Completed, otherwise stale tickets block every close.
	if settings.get("custom_require_no_open_kds_orders"):
		issues.extend(_kds_issues(bd, submitted, drafts))

	# 7, 8, 11, 12, 13, 14, 10 — best-effort operational checks
	issues.extend(_operational_issues(bd, settings, submitted, opening_names))

	return issues


def _kds_issues(bd, submitted, drafts):
	if not frappe.db.exists("DocType", "KDS Order"):
		return []
	# Returns never raise kitchen tickets, so never look for one against them.
	invoice_names = [i.name for i in submitted if not i.is_return] + [i.name for i in drafts]
	if not invoice_names:
		return []
	open_kds = frappe.get_all(
		"KDS Order",
		filters={"sales_invoice": ["in", invoice_names], "status": ["not in", ["Completed", "Cancelled"]]},
		fields=["name", "sales_invoice", "status"],
	)
	return [
		_issue(
			"KDS Order Open", _("Kitchen (KDS) order is still {0}.").format(k.status), _("Complete KDS Order"),
			document_type="KDS Order", document_no=k.name,
		)
		for k in open_kds
	]


def _operational_issues(bd, settings, submitted, opening_names):
	issues = []

	# 7 — On Hold orders (Sales Invoice `on_hold`/`is_hold` if present)
	if settings.get("custom_require_no_on_hold_orders", 1) and opening_names:
		hold_field = None
		for f in ("on_hold", "is_hold", "custom_on_hold"):
			if f in frappe.get_meta("Sales Invoice").get_valid_columns():
				hold_field = f
				break
		if hold_field:
			held = frappe.get_all(
				"Sales Invoice",
				filters={"posa_pos_opening_shift": ["in", opening_names], hold_field: 1, "docstatus": ["<", 2]},
				fields=["name", "owner"],
			)
			for inv in held:
				issues.append(
					_issue("Order On Hold", _("Order is on hold."), _("Release / Complete Order"),
						document_type="Sales Invoice", document_no=inv.name, user_employee=inv.owner)
				)

	# 13 & 14 — pending / failed Payment Entries referencing the day's shifts
	if opening_names:
		pending_pe = frappe.get_all(
			"Payment Entry",
			filters={"reference_no": ["in", opening_names], "docstatus": 0},
			fields=["name", "paid_amount"],
		)
		for pe in pending_pe:
			issues.append(
				_issue("Pending Payment Transaction", _("Payment Entry is not submitted."), _("Review / Submit Payment"),
					document_type="Payment Entry", document_no=pe.name, amount=pe.paid_amount)
			)

	return issues


@frappe.whitelist()
def validate_business_day_closable(business_day):
	doc = frappe.get_doc("POS Business Day", business_day)
	doc.refresh_summary()
	issues = doc.evaluate_closing_issues()
	doc.save(ignore_permissions=True)
	return {"closable": len(issues) == 0, "issues": issues, "count": len(issues)}


@frappe.whitelist()
def close_business_day(business_day, force=0, reason=None):
	force = frappe.parse_json(force) if isinstance(force, str) else force
	if force and not _can_override():
		frappe.throw(_("Only an Operations Manager can override and force-close a Business Day."))
	if force and not reason:
		frappe.throw(_("A reason is mandatory when overriding the close."))
	doc = frappe.get_doc("POS Business Day", business_day)
	doc.close(force=bool(force), reason=reason)
	return doc.as_dict()


@frappe.whitelist()
def reopen_business_day(business_day, reason=None):
	"""Reopen a closed POS Business Day (manager-only, reason mandatory, audit-logged).

	Needed whenever a day was closed while its operational window is still running —
	otherwise the closed-day guard would block all further trading with no way out.
	"""
	if not _can_override():
		frappe.throw(_("Only a Branch/Operations Manager can reopen a Business Day."))
	if not reason:
		frappe.throw(_("A reason is mandatory when reopening a Business Day."))

	doc = frappe.get_doc("POS Business Day", business_day)
	if doc.status != "Closed":
		frappe.throw(_("Business Day {0} is not closed.").format(business_day))

	# Don't reopen into a conflict with another live day for the same profile/date.
	clash = frappe.db.get_value(
		"POS Business Day",
		{
			"pos_profile": doc.pos_profile,
			"business_date": doc.business_date,
			"status": ["in", NON_CLOSED_FOR_REOPEN],
			"name": ["!=", doc.name],
		},
		"name",
	)
	if clash:
		frappe.throw(_("Another open Business Day ({0}) already exists for that date.").format(clash))

	# Refresh the operational window from the profile's CURRENT times — the stored
	# window may predate a correction to the profile's hours, and reopening against a
	# stale cut-off would put the day straight back into "Closing Required".
	from ecs_posnext.api.business_day import get_window_for_business_date

	window = get_window_for_business_date(doc.pos_profile, doc.business_date)
	doc.start_datetime = window.start_datetime
	doc.sales_cutoff_datetime = window.sales_cutoff_datetime
	doc.mandatory_closing_deadline = window.mandatory_closing_deadline

	# Come back in the right state for where we are in the window.
	new_status = "Open"
	if doc.sales_cutoff_datetime and now_datetime() > get_datetime(doc.sales_cutoff_datetime):
		new_status = "Closing Required"

	doc.status = new_status
	doc.closed_by = None
	doc.closing_datetime = None
	doc.save(ignore_permissions=True)

	log_pos_event(
		action="Reopening Business Day",
		reference_doctype="POS Business Day",
		reference_name=doc.name,
		pos_profile=doc.pos_profile,
		pos_business_day=doc.name,
		old_value="Closed",
		new_value=new_status,
		reason=reason,
	)
	return doc.as_dict()


def _can_override():
	roles = set(frappe.get_roles(frappe.session.user))
	return bool(roles & {"POSNext Operations Manager", "System Manager", "Administrator"})
