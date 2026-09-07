# Copyright (c) 2026, ECS and contributors
"""Order additions (supplement orders) visibility for KDS + Dispatcher.

Adds `custom_parent_order` (Link to Sales Invoice) so a supplement invoice created
when a cashier adds items to an already-placed order is really linked back to the
original order, instead of only sharing a cosmetic `custom_number_order` prefix.
Reloads KDS Order / KDS Order Item (has_pending_addition / is_addition flags) and
Delivery Assignment (has_pending_addition flag) so the new schema is live.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Invoice": [
				{
					"fieldname": "custom_parent_order",
					"label": "Parent Order",
					"fieldtype": "Link",
					"options": "Sales Invoice",
					"insert_after": "custom_number_order",
					"read_only": 1,
					"no_copy": 1,
					"description": "Set when this invoice is a supplement (added items) to an already-placed order — links back to the original Sales Invoice.",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.reload_doc("pos_next", "doctype", "kds_order")
	frappe.reload_doc("pos_next", "doctype", "kds_order_item")
	frappe.reload_doc("pos_next", "doctype", "delivery_assignment")
	frappe.db.commit()
