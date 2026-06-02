# Copyright (c) 2026, Youssef Restom and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Inventory(Document):
	pass


@frappe.whitelist()
def get_items_for_inventory(warehouse):
	"""Get all stock items that have balance in the given warehouse."""
	if not warehouse:
		return []
	
	items = frappe.db.sql("""
		SELECT DISTINCT 
			sle.item_code,
			i.item_name,
			i.stock_uom
		FROM `tabStock Ledger Entry` sle
		INNER JOIN `tabItem` i ON i.name = sle.item_code
		WHERE sle.warehouse = %(warehouse)s
			AND i.disabled = 0
			AND i.is_stock_item = 1
			AND i.custom_inventory = 1
		ORDER BY i.item_name
	""", {"warehouse": warehouse}, as_dict=True)
	
	return items
