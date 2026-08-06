# Copyright (c) 2026, ECS and contributors
"""Shared logic for the Branch Requisition forms (Packaging & Supplies Request and
Products Request). Both are simple, submittable "what the branch wants" records; they do
not create any stock/procurement document by themselves.

Each form auto-loads the Items flagged for it:
- Packaging & Supplies Request -> Item.custom_is_packaging_supply = 1
- Products Request             -> Item.custom_is_finished_product = 1
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime


def _flagged_items(flag_field):
	rows = frappe.db.sql(
		"""
		SELECT i.name AS item_code, i.item_name, i.stock_uom
		FROM `tabItem` i
		WHERE i.disabled = 0
		  AND IFNULL(i.{flag}, 0) = 1
		ORDER BY i.item_name
		""".format(flag=flag_field),
		as_dict=True,
	)
	return [
		{"item_code": r.item_code, "item_name": r.item_name, "uom": r.stock_uom}
		for r in rows
	]


@frappe.whitelist()
def get_packaging_items():
	"""All packaging / consumable items (Item.custom_is_packaging_supply = 1)."""
	return _flagged_items("custom_is_packaging_supply")


@frappe.whitelist()
def get_product_items():
	"""All finished products (Item.custom_is_finished_product = 1)."""
	return _flagged_items("custom_is_finished_product")


def apply_defaults(doc):
	"""Common header defaults for both requisition forms."""
	if not doc.get("request_date"):
		doc.request_date = getdate(now_datetime())
	if not doc.get("requested_by"):
		doc.requested_by = frappe.session.user
	if doc.get("pos_profile"):
		if not doc.get("company"):
			doc.company = frappe.db.get_value("POS Profile", doc.pos_profile, "company")
		if not doc.get("warehouse"):
			doc.warehouse = frappe.db.get_value("POS Profile", doc.pos_profile, "warehouse")


def validate_requisition(doc):
	"""Shared validate: defaults + at least one line with a positive qty on submit."""
	apply_defaults(doc)
	if doc.docstatus == 1:
		positive = [r for r in (doc.get("items") or []) if flt(r.qty) > 0]
		if not positive:
			frappe.throw(_("Enter a request quantity for at least one item before submitting."))
