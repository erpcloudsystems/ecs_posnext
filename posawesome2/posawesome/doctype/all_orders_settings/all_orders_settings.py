# Copyright (c) 2024, Youssef Restom and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AllOrdersSettings(Document):
	pass


@frappe.whitelist()
def get_user_date_range(user=None):
	"""Get date range for a specific user from All Orders Settings."""
	if not user:
		user = frappe.session.user
	
	settings = frappe.get_single("All Orders Settings")
	
	for row in settings.user_date_ranges:
		if row.user == user:
			return {
				"date_from": row.date_from,
				"date_to": row.date_to
			}
	
	# No date range set for user - return None (will use whole day)
	return None
