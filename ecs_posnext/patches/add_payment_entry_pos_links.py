# Copyright (c) 2026, ECS and contributors
"""Add POS Business Day / POS Cashier Shift link fields to Payment Entry and backfill.

COD / Call Center collections are Payment Entries whose `reference_no` is the POS
Opening Shift. These fields make the Business-Day / Cashier-Shift links first-class on
the Payment Entry so they are filterable and linkable everywhere (not only via the
report's join). Stamped at collection time; this patch backfills the existing ones.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Payment Entry": [
				{
					"fieldname": "custom_pos_business_day",
					"label": "POS Business Day",
					"fieldtype": "Link",
					"options": "POS Business Day",
					"insert_after": "reference_no",
					"read_only": 1,
					"no_copy": 1,
				},
				{
					"fieldname": "custom_pos_cashier_shift",
					"label": "POS Cashier Shift",
					"fieldtype": "Link",
					"options": "POS Cashier Shift",
					"insert_after": "custom_pos_business_day",
					"read_only": 1,
					"no_copy": 1,
				},
			]
		},
		ignore_validate=True,
	)

	# Backfill: map each shift-linked Payment Entry through its POS Cashier Shift.
	frappe.db.sql(
		"""
		UPDATE `tabPayment Entry` pe
		INNER JOIN `tabPOS Cashier Shift` cs ON cs.pos_opening_shift = pe.reference_no
		SET pe.custom_pos_cashier_shift = cs.name,
		    pe.custom_pos_business_day = cs.pos_business_day
		WHERE pe.docstatus < 2 AND IFNULL(pe.custom_pos_cashier_shift, '') = ''
		"""
	)
	frappe.db.commit()
