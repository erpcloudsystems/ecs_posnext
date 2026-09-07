# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Backfill Customer Complaint.complaint_date from `creation` for rows where it
was never set — the doctype's "options": "today" is not a real default
mechanism, so complaints created via the API (which never set complaint_date
directly) ended up with a NULL value, silently excluding them from any report
filtering on complaint_date. One-time, idempotent.
"""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Customer Complaint"):
		return

	frappe.db.sql(
		"""
		UPDATE `tabCustomer Complaint`
		SET complaint_date = creation
		WHERE complaint_date IS NULL
		"""
	)
	frappe.db.commit()
