# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Remap Customer Complaint.status from the old 4-value set to the new
Complaint Management lifecycle. One-time, idempotent (only touches rows
still on an old value).

Old -> New:
  Open        -> New
  In Progress -> Under Review
  Resolved    -> Closed
  Rejected    -> Rejected
"""

import frappe

MAPPING = {
	"Open": "New",
	"In Progress": "Under Review",
	"Resolved": "Closed",
}


def execute():
	if not frappe.db.exists("DocType", "Customer Complaint"):
		return

	for old_status, new_status in MAPPING.items():
		frappe.db.set_value(
			"Customer Complaint",
			{"status": old_status},
			"status",
			new_status,
			update_modified=False,
		)

	frappe.db.commit()
