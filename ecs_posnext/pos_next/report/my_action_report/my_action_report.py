import frappe

# Each source doctype on the Need My Action page, mapped to the common report shape.
# (doctype, type_label, reference_field, number_field, reason_field, decline_status)
SOURCES = [
	("Delivery Return Request", "Return Request", "sales_invoice", "custom_number_order", "reason", "Rejected"),
	("Branch Return Approval", "Branch Return Approval", "sales_invoice", "custom_number_order", "reason", "Rejected"),
	("Customer Status Request", "Customer Status Request", "customer", None, "request_type", "Rejected"),
	("Compensation Coupon Request", "Coupon Request", "customer", "complaint_number", None, "Rejected"),
]


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Type", "fieldname": "action_type", "fieldtype": "Data", "width": 170},
		{"label": "Reference", "fieldname": "reference", "fieldtype": "Data", "width": 160},
		{"label": "Order / Ref #", "fieldname": "number", "fieldtype": "Data", "width": 110},
		{"label": "Requested By", "fieldname": "requested_by", "fieldtype": "Link", "options": "User", "width": 170},
		{"label": "Approved / Declined By", "fieldname": "approved_by", "fieldtype": "Link", "options": "User", "width": 180},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Approved", "fieldname": "approved", "fieldtype": "Int", "width": 90},
		{"label": "Declined", "fieldname": "declined", "fieldtype": "Int", "width": 90},
		{"label": "Reason", "fieldname": "reason", "fieldtype": "Data", "width": 240},
		{"label": "Date", "fieldname": "date", "fieldtype": "Datetime", "width": 155},
	]


def get_data(filters):
	rows = []
	for dt, label, ref_field, num_field, reason_field, decline_status in SOURCES:
		if not frappe.db.exists("DocType", dt):
			continue
		conds = {}
		if filters.get("from_date") and filters.get("to_date"):
			conds["creation"] = ["between", [str(filters["from_date"]) + " 00:00:00", str(filters["to_date"]) + " 23:59:59"]]
		if filters.get("status"):
			conds["status"] = filters["status"]

		wanted = {"name", "status", "requested_by", "approved_by", "creation", ref_field}
		if num_field:
			wanted.add(num_field)
		if reason_field:
			wanted.add(reason_field)
		meta_fields = set(frappe.get_meta(dt).get_valid_columns())
		fields = [f for f in wanted if f in meta_fields]

		for r in frappe.get_all(dt, filters=conds, fields=fields, order_by="creation desc"):
			status = r.get("status") or ""
			# Skip still-pending items unless the user asked for them explicitly.
			if not filters.get("include_pending") and status == "Pending":
				continue
			rows.append({
				"action_type": label,
				"reference": r.get(ref_field),
				"number": r.get(num_field) if num_field else None,
				"requested_by": r.get("requested_by"),
				"approved_by": r.get("approved_by"),
				"status": status,
				"approved": 1 if status == "Approved" else 0,
				"declined": 1 if status == decline_status else 0,
				"reason": r.get(reason_field) if reason_field else None,
				"date": r.get("creation"),
			})

	rows.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
	return rows
