# Copyright (c) 2026, ECS and contributors
"""Add a 'reject_reason' field to Delivery Return Request (idempotent).

Captured when a Call Center Manager rejects a return request, and shown back on the
dispatcher card so the dispatcher knows why the request was declined.
"""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Delivery Return Request"):
		return
	dt = frappe.get_doc("DocType", "Delivery Return Request")
	if any(f.fieldname == "reject_reason" for f in dt.fields):
		return
	dt.append("fields", {
		"fieldname": "reject_reason",
		"label": "Reject Reason",
		"fieldtype": "Small Text",
		"insert_after": "reason",
	})
	dt.flags.ignore_permissions = True
	dt.save(ignore_permissions=True)
	frappe.db.commit()
