# Copyright (c) 2026, ECS and contributors
"""Add a 'Free Delivery' flag to POS Profile.

When `custom_free_delivery` is ticked, every delivery order on that POS Profile has its
delivery charge waived (rate forced to 0), enforced entirely server-side — no POS UI
change. See ecs_posnext.api.customers.get_delivery_charge_for_territory and
ecs_posnext.api.invoices (delivery-charge block).
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"POS Profile": [
				{
					"fieldname": "custom_free_delivery",
					"label": "Free Delivery (waive delivery charges)",
					"fieldtype": "Check",
					"insert_after": "warehouse",
					"default": "0",
					"description": "When enabled, delivery orders on this profile carry no delivery charge.",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.db.commit()
