# -*- coding: utf-8 -*-
"""
Delivery Return Requests.

A dispatcher raises a return request against an undispatched Delivery / Talabat
order from the dispatch board. The request is created as Pending and shown on the
Need My Action page, where a Call Center Manager / Deputy approves it — which
creates a Sales Return (credit note) reversing the original invoice — or rejects it.

Mirrors the Customer Status Request flow (request -> Need My Action -> approve/reject).
"""

import json

import frappe
from frappe import _
from frappe.utils import flt

APPROVER_ROLES = ("System Manager", "Call center manager", "Deputy Call Center Manager")


def _require_approver():
	user = frappe.session.user
	if user == "Administrator":
		return
	if not set(APPROVER_ROLES) & set(frappe.get_roles(user)):
		frappe.throw(
			_("Only a Call Center Manager / Deputy can approve return requests."),
			frappe.PermissionError,
		)


@frappe.whitelist()
def request_delivery_return(sales_invoice, reason=None):
	"""Create (or refresh) a Pending return request for an undispatched order."""
	if not reason or not str(reason).strip():
		frappe.throw(_("A reason is required to request a return."))
	if not frappe.db.exists("Sales Invoice", sales_invoice):
		frappe.throw(_("Sales Invoice {0} not found.").format(sales_invoice))

	inv = frappe.db.get_value(
		"Sales Invoice",
		sales_invoice,
		[
			"docstatus", "is_return", "customer", "customer_name", "contact_mobile",
			"branch", "custom_order_type", "custom_number_order", "grand_total",
		],
		as_dict=True,
	)
	if inv.docstatus != 1:
		frappe.throw(_("Only a submitted order can be returned."))
	if inv.is_return:
		frappe.throw(_("{0} is itself a return.").format(sales_invoice))

	# Already returned? Nothing to request.
	if frappe.db.exists(
		"Sales Invoice", {"return_against": sales_invoice, "is_return": 1, "docstatus": 1}
	):
		frappe.throw(_("Order {0} has already been returned.").format(sales_invoice))

	# Reuse an existing pending request instead of duplicating.
	existing = frappe.db.exists(
		"Delivery Return Request", {"sales_invoice": sales_invoice, "status": "Pending"}
	)
	if existing:
		doc = frappe.get_doc("Delivery Return Request", existing)
		doc.reason = reason
		doc.requested_by = frappe.session.user
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({
			"doctype": "Delivery Return Request",
			"sales_invoice": sales_invoice,
			"custom_number_order": inv.custom_number_order,
			"order_type": inv.custom_order_type,
			"customer": inv.customer,
			"customer_name": inv.customer_name,
			"mobile": inv.contact_mobile,
			"branch": inv.branch,
			"grand_total": flt(inv.grand_total),
			"reason": reason,
			"status": "Pending",
			"requested_by": frappe.session.user,
		}).insert(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "status": "Pending"}


@frappe.whitelist()
def get_pending_delivery_return_requests():
	"""Pending return requests for the Need My Action page (branch-scoped)."""
	filters = {"status": "Pending"}
	# Call Center Managers / Deputies (and System Managers) oversee every branch — no scope.
	overseer = bool(
		{"Call center manager", "Deputy Call Center Manager", "System Manager"} & set(frappe.get_roles())
	)
	if not overseer:
		try:
			from ecs_posnext.api.invoices import _get_user_branch_filter_info

			branch, is_cc = _get_user_branch_filter_info()
			if not is_cc and branch:
				filters["branch"] = branch
		except Exception:
			pass
	rows = frappe.get_all(
		"Delivery Return Request",
		filters=filters,
		fields=[
			"name", "sales_invoice", "custom_number_order", "order_type", "customer",
			"customer_name", "mobile", "branch", "grand_total", "reason",
			"requested_by", "creation",
		],
		order_by="creation desc",
	)
	# Enrich with the original invoice's POS context so the approval dialog can build the
	# return on the same profile / shift / currency as the sale.
	for r in rows:
		ctx = frappe.db.get_value(
			"Sales Invoice", r["sales_invoice"],
			["pos_profile", "posa_pos_opening_shift", "currency"], as_dict=True,
		) or {}
		r["pos_profile"] = ctx.get("pos_profile")
		r["pos_opening_shift"] = ctx.get("posa_pos_opening_shift")
		r["currency"] = ctx.get("currency")
	return rows


def _create_return_credit_note(sales_invoice):
	"""Build + submit a full Sales Return (credit note) for the order. Runs privileged
	because approval is a manager action and the credit-note mapping enforces POS
	create permissions the approver may not personally hold."""
	from ecs_posnext.api.invoices import prepare_return_invoice, submit_invoice

	orig = frappe.db.get_value(
		"Sales Invoice", sales_invoice,
		["posa_pos_opening_shift", "pos_profile", "company", "customer"], as_dict=True,
	)
	original_user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		# Keep the return on the SAME shift/day as the original sale.
		data = prepare_return_invoice(sales_invoice, pos_opening_shift=orig.posa_pos_opening_shift)
		data.pop("_original_invoice", None)
		payload = {
			"doctype": "Sales Invoice",
			"pos_profile": orig.pos_profile,
			"customer": data.get("customer") or orig.customer,
			"company": data.get("company") or orig.company,
			"is_return": 1,
			"return_against": sales_invoice,
			"is_pos": 1,
			"update_stock": 1,
			"payments": [],  # undispatched order — no cash handed back (matches return fix)
			"items": [
				{
					"item_code": i["item_code"],
					"qty": -abs(flt(i["qty"])),
					"rate": i["rate"],
					"warehouse": i.get("warehouse"),
					"uom": i.get("uom"),
					"conversion_factor": i.get("conversion_factor", 1),
					"sales_invoice_item": i.get("sales_invoice_item"),
				}
				for i in data.get("items", [])
			],
			# Carry the original's tax rows (negated by make_sales_return) so the credit
			# note reverses tax too — submit_invoice recomputes percentage charges.
			"taxes": [
				{
					"charge_type": t.get("charge_type"),
					"account_head": t.get("account_head"),
					"description": t.get("description"),
					"rate": t.get("rate"),
					"cost_center": t.get("cost_center"),
					"included_in_print_rate": t.get("included_in_print_rate"),
					"row_id": t.get("row_id"),
					"tax_amount": t.get("tax_amount"),
				}
				for t in data.get("taxes", [])
			],
		}
		res = submit_invoice(invoice=payload, data=json.dumps({"force_submit": 1}))
		return res["name"]
	finally:
		frappe.set_user(original_user)


@frappe.whitelist()
def approve_delivery_return_request(name):
	"""Approve a request — create the Sales Return credit note and release the order."""
	_require_approver()
	req = frappe.get_doc("Delivery Return Request", name)
	if req.status != "Pending":
		frappe.throw(_("This request is already {0}.").format(req.status))

	if frappe.db.get_value("Sales Invoice", req.sales_invoice, "docstatus") != 1:
		frappe.throw(_("Order {0} is no longer a valid submitted invoice.").format(req.sales_invoice))

	# If it was already returned in the meantime, just link + close the request.
	existing_return = frappe.db.get_value(
		"Sales Invoice", {"return_against": req.sales_invoice, "is_return": 1, "docstatus": 1}, "name"
	)
	return_invoice = existing_return or _create_return_credit_note(req.sales_invoice)

	# Release any assignment holding this order.
	for da in frappe.get_all(
		"Delivery Assignment",
		filters={
			"order_reference": req.sales_invoice,
			"docstatus": ["!=", 2],
			"status": ["in", ["Assigned", "Picked Up", "Out for Delivery"]],
		},
		pluck="name",
	):
		frappe.db.set_value("Delivery Assignment", da, "status", "Returned")

	req.return_invoice = return_invoice
	req.status = "Approved"
	req.approved_by = frappe.session.user
	req.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "Approved", "return_invoice": return_invoice}


@frappe.whitelist()
def reject_delivery_return_request(name, reason=None):
	"""Reject a request without touching the order. The reason is shown back on the
	dispatcher card so the order becomes assignable again with context."""
	_require_approver()
	req = frappe.get_doc("Delivery Return Request", name)
	if req.status != "Pending":
		frappe.throw(_("This request is already {0}.").format(req.status))
	req.status = "Rejected"
	req.approved_by = frappe.session.user
	if req.meta.has_field("reject_reason"):
		req.reject_reason = reason
	req.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "Rejected"}
