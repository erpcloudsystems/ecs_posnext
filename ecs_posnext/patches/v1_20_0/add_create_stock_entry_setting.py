# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
Let a POS Profile stop issuing stock with its sales.

A POS sale has always written a Material Issue Stock Entry beside the Sales
Order, because a Sales Order on its own moves no stock. A site that issues its
stock some other way needs to be able to turn that off.

Defaults to on, so nothing changes for a profile that does not ask.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"POS Profile": [
				{
					"fieldname": "posa_stock_section",
					"label": "Stock",
					"fieldtype": "Section Break",
					"insert_after": "posa_edit_password",
				},
				{
					"fieldname": "posa_create_stock_entry",
					"label": "Create Stock Entry with POS Sales",
					"fieldtype": "Check",
					"insert_after": "posa_stock_section",
					"default": "1",
					"description": (
						"Issue stock with every POS sale through a Material Issue Stock Entry. "
						"A Sales Order moves no stock by itself, so turning this off means the "
						"POS records the sale but never reduces the balance - the stock has to "
						"be issued some other way."
					),
				},
			]
		},
		ignore_validate=True,
	)
