# Copyright (c) 2026, ECS and contributors
"""Add a Fixed Item flag to Product Bundle Item (recipe rows).

A fixed recipe row is a built-in part of a regular meal (e.g. the fries in a meal):
the cashier can't remove it, KDS shows it as its own component at its own station,
and it is deducted from stock like any other recipe row.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Product Bundle Item": [
				{
					"fieldname": "custom_is_fixed",
					"label": "Fixed Item",
					"fieldtype": "Check",
					"insert_after": "show_in_pos",
					"default": "0",
					"in_list_view": 1,
					"description": "Built-in part of the meal: not removable in POS, shown on KDS as its own component.",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.db.commit()
