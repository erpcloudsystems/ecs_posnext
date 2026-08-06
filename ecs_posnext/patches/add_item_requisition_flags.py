# Copyright (c) 2026, ECS and contributors
"""Add two Branch Requisition flags to Item.

- `custom_is_packaging_supply` -> item shows in the Packaging & Supplies Request form.
- `custom_is_finished_product`  -> item shows in the Products Request form.

See ecs_posnext/pos_next/doctype/packaging_supplies_request and products_request.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Item": [
				{
					"fieldname": "custom_is_packaging_supply",
					"label": "Packaging / Supply Item",
					"fieldtype": "Check",
					"insert_after": "custom_include_in_blind_count",
					"default": "0",
					"description": "Show this item in the Packaging & Supplies Request form.",
				},
				{
					"fieldname": "custom_is_finished_product",
					"label": "Finished Product",
					"fieldtype": "Check",
					"insert_after": "custom_is_packaging_supply",
					"default": "0",
					"description": "Show this item in the Products Request form.",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.db.commit()
