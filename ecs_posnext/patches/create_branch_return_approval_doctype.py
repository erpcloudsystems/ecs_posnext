# Copyright (c) 2026, ECS and contributors
"""Create the 'Branch Return Approval' custom doctype (idempotent).

A return attempted past the KDS grace window (food likely already prepared) is held as
a PENDING request for the BRANCH MANAGER to approve on Need My Action. The stored return
payload is replayed (branch-approved) on approval, or discarded on reject.
See ecs_posnext/api/branch_return_approval.py.
"""

import frappe


def execute():
	if frappe.db.exists("DocType", "Branch Return Approval"):
		return

	frappe.get_doc({
		"doctype": "DocType",
		"name": "Branch Return Approval",
		"module": "POS Next",
		"custom": 1,
		"naming_rule": "Random",
		"autoname": "hash",
		"track_changes": 1,
		"editable_grid": 1,
		"fields": [
			{"fieldname": "sales_invoice", "label": "Sales Invoice", "fieldtype": "Link", "options": "Sales Invoice", "reqd": 1, "in_list_view": 1},
			{"fieldname": "custom_number_order", "label": "Order #", "fieldtype": "Data", "in_list_view": 1},
			{"fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "Customer"},
			{"fieldname": "customer_name", "label": "Customer Name", "fieldtype": "Data"},
			{"fieldname": "mobile", "label": "Mobile", "fieldtype": "Data"},
			{"fieldname": "branch", "label": "Branch", "fieldtype": "Data", "in_standard_filter": 1},
			{"fieldname": "grand_total", "label": "Grand Total", "fieldtype": "Currency"},
			{"fieldname": "return_source", "label": "Return Source", "fieldtype": "Data"},
			{"fieldname": "reason", "label": "Reason", "fieldtype": "Small Text", "in_list_view": 1},
			{"fieldname": "minutes_since_kds", "label": "Minutes Since KDS", "fieldtype": "Int"},
			{"fieldname": "invoice_payload", "label": "Invoice Payload", "fieldtype": "Long Text", "read_only": 1},
			{"fieldname": "data_payload", "label": "Data Payload", "fieldtype": "Long Text", "read_only": 1},
			{"fieldname": "status", "label": "Status", "fieldtype": "Select", "options": "Pending\nApproved\nRejected", "default": "Pending", "in_list_view": 1, "in_standard_filter": 1},
			{"fieldname": "requested_by", "label": "Requested By", "fieldtype": "Link", "options": "User"},
			{"fieldname": "approved_by", "label": "Approved / Rejected By", "fieldtype": "Link", "options": "User"},
			{"fieldname": "return_invoice", "label": "Return Invoice (Credit Note)", "fieldtype": "Link", "options": "Sales Invoice", "read_only": 1},
		],
		"permissions": [
			{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
			{"role": "POSNext Branch Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
			{"role": "Bransh Manager", "read": 1, "write": 1, "create": 1},
			{"role": "Dispatcher", "read": 1, "write": 1, "create": 1},
			{"role": "Call center manager", "read": 1, "write": 1, "create": 1},
		],
	}).insert(ignore_permissions=True)
	frappe.db.commit()
