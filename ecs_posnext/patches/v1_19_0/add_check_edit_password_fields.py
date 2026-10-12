# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
Give POS Profile the manager password that guards edits to an open check.

The password uses the `Password` fieldtype rather than `Data` on purpose: Frappe
keeps those in the `__Auth` table and hands the document out with a placeholder,
so the POS can be told *whether* a password is required without ever receiving
it. A `Data` field would be readable by anyone who can load the profile, which
is every cashier.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"POS Profile": [
				{
					"fieldname": "posa_check_edit_section",
					"label": "Check Edit Protection",
					"fieldtype": "Section Break",
					"insert_after": "posa_block_sale_beyond_available_qty",
				},
				{
					"fieldname": "posa_require_edit_password",
					"label": "Require Password to Edit an Open Check",
					"fieldtype": "Check",
					"insert_after": "posa_check_edit_section",
					"default": "0",
					"description": (
						"Ask for the password below before reducing a quantity, removing an item, "
						"clearing the cart or discounting while a table is open, and before "
						"cancelling a check or freeing a table that has an order."
					),
				},
				{
					"fieldname": "posa_edit_password",
					"label": "Check Edit Password",
					"fieldtype": "Password",
					"insert_after": "posa_require_edit_password",
					"depends_on": "eval:doc.posa_require_edit_password",
					"mandatory_depends_on": "eval:doc.posa_require_edit_password",
					"description": "Held by the supervisor. Never sent to the POS - it is checked on the server.",
				},
			]
		},
		ignore_validate=True,
	)
