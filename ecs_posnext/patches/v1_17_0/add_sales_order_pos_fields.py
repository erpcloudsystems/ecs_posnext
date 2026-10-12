# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
Give Sales Order the two POS fields the shift closing needs.

The POS has always sent `posa_pos_opening_shift` and the payment breakdown with
every order; Sales Order had neither field, so both were silently dropped. That
is why Close Shift reported zero - the money was collected, described, sent, and
then thrown away on arrival.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Order": [
				{
					"fieldname": "posa_pos_opening_shift",
					"label": "POS Opening Shift",
					"fieldtype": "Link",
					"options": "POS Opening Shift",
					"insert_after": "customer",
					"read_only": 1,
					"print_hide": 1,
					"description": "The shift this order was rung up in. Shift closing totals by this.",
				},
				{
					"fieldname": "posa_payments",
					"label": "POS Payments",
					"fieldtype": "Table",
					"options": "POS Order Payment",
					"insert_after": "posa_pos_opening_shift",
					"read_only": 1,
					"print_hide": 1,
					"description": "How the order was paid, per mode of payment. Sales Order has no payments table of its own, and without this the breakdown is lost.",
				},
			]
		},
		ignore_validate=True,
	)
