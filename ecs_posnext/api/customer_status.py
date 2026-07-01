# -*- coding: utf-8 -*-
"""
Customer VIP / Blacklist status change requests.

A cashier requests a status change from the customer profile; the request is
created as Pending and shown on the Need My Action page, where a manager
approves it (which applies the change to the Customer) or rejects it.
"""

import frappe
from frappe import _

APPROVER_ROLES = ("System Manager", "Bransh Manager")


def _require_approver():
	user = frappe.session.user
	if user == "Administrator":
		return
	if not set(APPROVER_ROLES) & set(frappe.get_roles(user)):
		frappe.throw(_("You are not permitted to approve customer status requests."), frappe.PermissionError)


@frappe.whitelist()
def get_customer_status(customer):
	"""Current VIP/blacklist state + any pending request for a customer."""
	if not customer or not frappe.db.exists("Customer", customer):
		return {}
	row = frappe.db.get_value(
		"Customer", customer, ["custom_vip", "custom_is_blacklist"], as_dict=True
	) or {}
	pending = frappe.get_all(
		"Customer Status Request",
		filters={"customer": customer, "status": "Pending"},
		fields=["name", "request_type", "enable"],
	)
	return {
		"is_vip": bool(row.get("custom_vip")),
		"is_blacklist": (row.get("custom_is_blacklist") == "Yes"),
		"pending": {p.request_type: p for p in pending},
	}


@frappe.whitelist()
def request_customer_status(customer, request_type, enable=1, pos_profile=None):
	"""Create (or refresh) a Pending status-change request for a customer."""
	if request_type not in ("VIP", "Blacklist"):
		frappe.throw(_("Invalid request type"))
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer not found"))

	enable = 1 if frappe.parse_json(enable) else 0
	cust = frappe.db.get_value(
		"Customer", customer, ["customer_name", "mobile_no"], as_dict=True
	) or {}

	# Branch of the requesting user (for Need My Action filtering)
	try:
		from ecs_posnext.api.invoices import _get_user_branch_filter_info
		branch, _is_cc = _get_user_branch_filter_info()
	except Exception:
		branch = None

	# Reuse an existing pending request of the same type instead of duplicating.
	existing = frappe.get_all(
		"Customer Status Request",
		filters={"customer": customer, "request_type": request_type, "status": "Pending"},
		pluck="name",
	)
	if existing:
		doc = frappe.get_doc("Customer Status Request", existing[0])
		doc.enable = enable
		doc.requested_by = frappe.session.user
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({
			"doctype": "Customer Status Request",
			"customer": customer,
			"customer_name": cust.get("customer_name"),
			"mobile": cust.get("mobile_no"),
			"branch": branch,
			"pos_profile": pos_profile,
			"request_type": request_type,
			"enable": enable,
			"status": "Pending",
			"requested_by": frappe.session.user,
		}).insert(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "status": "Pending"}


@frappe.whitelist()
def get_pending_customer_status_requests():
	"""Pending requests for the Need My Action page (branch-scoped)."""
	filters = {"status": "Pending"}
	try:
		from ecs_posnext.api.invoices import _get_user_branch_filter_info
		branch, is_cc = _get_user_branch_filter_info()
		if not is_cc and branch:
			filters["branch"] = branch
	except Exception:
		pass
	return frappe.get_all(
		"Customer Status Request",
		filters=filters,
		fields=[
			"name", "customer", "customer_name", "mobile", "branch",
			"request_type", "enable", "requested_by", "creation",
		],
		order_by="creation desc",
	)


@frappe.whitelist()
def approve_customer_status_request(name):
	"""Approve a request — apply the change to the Customer."""
	_require_approver()
	doc = frappe.get_doc("Customer Status Request", name)
	if doc.status != "Pending":
		frappe.throw(_("This request is already {0}.").format(doc.status))

	if doc.request_type == "VIP":
		frappe.db.set_value("Customer", doc.customer, "custom_vip", 1 if doc.enable else 0)
	elif doc.request_type == "Blacklist":
		frappe.db.set_value("Customer", doc.customer, "custom_is_blacklist", "Yes" if doc.enable else "No")

	doc.status = "Approved"
	doc.approved_by = frappe.session.user
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "Approved"}


@frappe.whitelist()
def reject_customer_status_request(name):
	"""Reject a request without changing the customer."""
	_require_approver()
	doc = frappe.get_doc("Customer Status Request", name)
	if doc.status != "Pending":
		frappe.throw(_("This request is already {0}.").format(doc.status))
	doc.status = "Rejected"
	doc.approved_by = frappe.session.user
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "Rejected"}
