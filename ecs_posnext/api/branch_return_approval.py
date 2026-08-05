# -*- coding: utf-8 -*-
"""
Branch Return Approvals.

When a return is attempted PAST the KDS grace window (the order is already in the
kitchen and food is likely prepared), the return is NOT created immediately. Instead
the full return payload is held as a Pending request for the BRANCH MANAGER to approve
on Need My Action. On approval the stored payload is replayed with branch approval, so
the credit note is created; on reject nothing happens.
"""

import json

import frappe
from frappe import _
from frappe.utils import flt

APPROVER_ROLES = ("System Manager", "POSNext Branch Manager", "Bransh Manager")


def _require_approver():
	user = frappe.session.user
	if user == "Administrator":
		return
	if not set(APPROVER_ROLES) & set(frappe.get_roles(user)):
		frappe.throw(
			_("Only a Branch Manager can approve return approvals."), frappe.PermissionError
		)


@frappe.whitelist()
def request_branch_return_approval(sales_invoice, invoice_payload, data_payload=None, reason=None, return_source=None):
	"""Hold a past-grace return as a Pending branch-manager approval, storing the exact
	payload so it can be replayed (branch-approved) once approved."""
	if not frappe.db.exists("Sales Invoice", sales_invoice):
		frappe.throw(_("Sales Invoice {0} not found.").format(sales_invoice))

	inv = frappe.db.get_value(
		"Sales Invoice", sales_invoice,
		["customer", "customer_name", "contact_mobile", "branch", "custom_number_order", "grand_total", "pos_profile"],
		as_dict=True,
	) or {}

	# Minutes since the order reached the KDS (informational for the manager).
	minutes = None
	ot = frappe.db.get_value("KDS Order", {"sales_invoice": sales_invoice}, "order_time")
	if ot:
		from frappe.utils import now_datetime, time_diff_in_seconds
		minutes = int(time_diff_in_seconds(now_datetime(), ot) / 60)

	existing = frappe.db.exists(
		"Branch Return Approval", {"sales_invoice": sales_invoice, "status": "Pending"}
	)
	if existing:
		doc = frappe.get_doc("Branch Return Approval", existing)
	else:
		doc = frappe.new_doc("Branch Return Approval")
		doc.sales_invoice = sales_invoice

	doc.custom_number_order = inv.get("custom_number_order")
	doc.customer = inv.get("customer")
	doc.customer_name = inv.get("customer_name")
	doc.mobile = inv.get("contact_mobile")
	doc.branch = inv.get("branch")
	doc.grand_total = flt(inv.get("grand_total"))
	doc.return_source = return_source or "User"
	doc.reason = reason
	doc.minutes_since_kds = minutes
	doc.invoice_payload = invoice_payload if isinstance(invoice_payload, str) else json.dumps(invoice_payload)
	doc.data_payload = data_payload if isinstance(data_payload, str) else json.dumps(data_payload or {})
	doc.status = "Pending"
	doc.requested_by = frappe.session.user
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	# Push a realtime "needs action" alarm to the branch manager's screens so a
	# past-grace return waiting for approval is not just a silent row on Need My Action.
	try:
		frappe.publish_realtime(
			"kds_update",
			{
				"action": "order_needs_action",
				"invoice": sales_invoice,
				"number": inv.get("custom_number_order"),
				"branch": inv.get("branch"),
				"is_call_center": "call center" in (inv.get("pos_profile") or "").lower(),
				"return_source": doc.return_source,
				"return_reason": reason,
				"approval": doc.name,
			},
			after_commit=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "branch_return_approval realtime")

	return {"name": doc.name, "status": "Pending"}


@frappe.whitelist()
def get_pending_branch_return_approvals():
	"""Pending branch approvals for Need My Action, scoped to the manager's branch."""
	filters = {"status": "Pending"}
	try:
		from ecs_posnext.api.invoices import _get_user_branch_filter_info

		branch, is_cc = _get_user_branch_filter_info()
		# Branch managers overseeing all branches (or with no resolved branch) see all.
		roles = set(frappe.get_roles())
		all_branches = bool({"System Manager", "POSNext Operations Manager"} & roles)
		if not all_branches and not is_cc and branch:
			filters["branch"] = branch
	except Exception:
		pass
	return frappe.get_all(
		"Branch Return Approval",
		filters=filters,
		fields=[
			"name", "sales_invoice", "custom_number_order", "customer", "customer_name",
			"mobile", "branch", "grand_total", "return_source", "reason",
			"minutes_since_kds", "requested_by", "creation",
		],
		order_by="creation desc",
	)


@frappe.whitelist()
def approve_branch_return_approval(name):
	"""Approve → replay the stored return payload (branch-approved) to create the credit note."""
	_require_approver()
	req = frappe.get_doc("Branch Return Approval", name)
	if req.status != "Pending":
		frappe.throw(_("This request is already {0}.").format(req.status))

	# If already returned meanwhile, just link + close.
	existing_return = frappe.db.get_value(
		"Sales Invoice", {"return_against": req.sales_invoice, "is_return": 1, "docstatus": 1}, "name"
	)
	if existing_return:
		return_invoice = existing_return
	else:
		from ecs_posnext.api.invoices import submit_invoice

		data = json.loads(req.data_payload or "{}")
		data["branch_approved"] = 1  # this approval IS the branch sign-off
		res = submit_invoice(invoice=req.invoice_payload, data=json.dumps(data))
		return_invoice = res["name"]

	req.return_invoice = return_invoice
	req.status = "Approved"
	req.approved_by = frappe.session.user
	req.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "Approved", "return_invoice": return_invoice}


@frappe.whitelist()
def reject_branch_return_approval(name):
	"""Reject → discard the request; no return is created."""
	_require_approver()
	req = frappe.get_doc("Branch Return Approval", name)
	if req.status != "Pending":
		frappe.throw(_("This request is already {0}.").format(req.status))
	req.status = "Rejected"
	req.approved_by = frappe.session.user
	req.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "Rejected"}
