# Copyright (c) 2026, ECS and contributors
"""Add a 'Blind Count Default Item' flag to Item.

Items flagged with `custom_include_in_blind_count` are auto-loaded into every new Blind
Inventory Count sheet so the Branch Manager only has to enter counted quantities.
See ecs_posnext/pos_next/doctype/blind_inventory_count.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Item": [
				{
					"fieldname": "custom_include_in_blind_count",
					"label": "Include in Blind Inventory Count",
					"fieldtype": "Check",
					"insert_after": "is_stock_item",
					"default": "0",
					"description": "Auto-add this item to every new Blind Inventory Count sheet (end-of-day physical count).",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.db.commit()
