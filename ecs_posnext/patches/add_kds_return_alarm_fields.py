# Copyright (c) 2026, ECS and contributors
"""KDS returned-order alarm: return source on Sales Invoice + reload KDS doctypes.

Adds `custom_return_source` (Call Center / User) to Sales Invoice so the kitchen can
show WHO returned an order, and reloads KDS Order (new returned_* fields + Returned
status) and KDS Settings (return_grace_minutes) so the new schema is live.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Invoice": [
				{
					"fieldname": "custom_return_source",
					"label": "Return Source",
					"fieldtype": "Data",
					"insert_after": "return_against",
					"read_only": 1,
					"no_copy": 1,
					"description": "Who initiated the return — 'Call Center' or 'User' — used by the KDS alarm.",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.reload_doc("pos_next", "doctype", "kds_order")
	frappe.reload_doc("pos_next", "doctype", "kds_settings")
	frappe.db.commit()
