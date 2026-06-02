# Copyright (c) 2024, Youssef Restom and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AllOrdersSettings(Document):
	pass


@frappe.whitelist()
def get_user_date_range(user=None):
	"""Get date range for a specific user from All Orders Settings.

	The child table stores a 'days' field (number of past days).
	0 means unlimited (no restriction).
	"""
	if not user:
		user = frappe.session.user

	settings = frappe.get_single("All Orders Settings")

	for row in settings.user_date_ranges:
		if row.user == user:
			from frappe.utils import today, add_days
			days = row.days or 0
			date_to = add_days(today(), 1)
			date_from = add_days(date_to, -days) if days > 0 else None
			return {
				"days": days,
				"date_from": date_from,
				"date_to": date_to,
			}

	# No date range set for user - return None (will use shift range)
	return None
