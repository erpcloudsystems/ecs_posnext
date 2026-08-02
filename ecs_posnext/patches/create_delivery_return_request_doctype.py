# Copyright (c) 2026, ECS and contributors
"""Create the 'Delivery Return Request' custom doctype (idempotent).

Raised from the dispatch board against an undispatched Delivery / Talabat order;
approved by a Call Center Manager / Deputy on Need My Action, which creates a
Sales Return credit note. See ecs_posnext/api/return_request.py.
"""

import frappe


def execute():
	if frappe.db.exists("DocType", "Delivery Return Request"):
		return

	frappe.get_doc({
		"doctype": "DocType",
		"name": "Delivery Return Request",
		"module": "POS Next",
		"custom": 1,
		"naming_rule": "Random",
		"autoname": "hash",
		"track_changes": 1,
		"editable_grid": 1,
		"fields": [
			{"fieldname": "sales_invoice", "label": "Sales Invoice", "fieldtype": "Link", "options": "Sales Invoice", "reqd": 1, "in_list_view": 1},
			{"fieldname": "custom_number_order", "label": "Order #", "fieldtype": "Data", "in_list_view": 1},
			{"fieldname": "order_type", "label": "Order Type", "fieldtype": "Data"},
			{"fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "Customer"},
			{"fieldname": "customer_name", "label": "Customer Name", "fieldtype": "Data"},
			{"fieldname": "mobile", "label": "Mobile", "fieldtype": "Data"},
			{"fieldname": "branch", "label": "Branch", "fieldtype": "Data"},
			{"fieldname": "grand_total", "label": "Grand Total", "fieldtype": "Currency"},
			{"fieldname": "reason", "label": "Reason", "fieldtype": "Small Text", "reqd": 1, "in_list_view": 1},
			{"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Pending\nApproved\nRejected", "default": "Pending", "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "requested_by", "label": "Requested By", "fieldtype": "Link", "options": "User"},
			{"fieldname": "approved_by", "label": "Approved / Rejected By", "fieldtype": "Link", "options": "User"},
			{"fieldname": "return_invoice", "label": "Return Invoice (Credit Note)", "fieldtype": "Link", "options": "Sales Invoice", "read_only": 1},
		],
		"permissions": [
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
			{"role": "Dispatcher", "read": 1, "write": 1, "create": 1},
			{"role": "Call center manager", "read": 1, "write": 1, "create": 1, "delete": 1},
			{"role": "Deputy Call Center Manager", "read": 1, "write": 1, "create": 1},
		],
	}).insert(ignore_permissions=True)
	frappe.db.commit()
