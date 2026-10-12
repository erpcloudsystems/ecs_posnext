# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
Give Sales Order the table fields the POS has always been sending.

The POS sends `pos_table_session` and `pos_table_order` with every table-service
sale, and `submit_invoice` reads them back off the document to settle the check
and free the table in the same call that submits the sale. Sales Order had
neither field, so both were dropped on save and that read always came back
empty - the table stayed occupied with its bill already paid, and the only way
to free it was by hand from the Open Tables screen.

Same failure as `v1_17_0.add_sales_order_pos_fields`: the POS described what it
was doing and the document had nowhere to put it.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Order": [
				{
					"fieldname": "pos_table_session",
					"label": "POS Table Session",
					"fieldtype": "Link",
					"options": "POS Table Session",
					"insert_after": "posa_payments",
					"read_only": 1,
					"print_hide": 1,
					"description": "The table sitting this sale settled. Closing the table on checkout reads this.",
				},
				{
					"fieldname": "pos_table_order",
					"label": "POS Table Order",
					"fieldtype": "Link",
					"options": "POS Table Order",
					"insert_after": "pos_table_session",
					"read_only": 1,
					"print_hide": 1,
					"description": "The specific check this sale paid, which matters on a table split across several checks.",
				},
			]
		},
		ignore_validate=True,
	)
