import frappe


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Coupon Code", "fieldname": "coupon_code", "fieldtype": "Data", "width": 130},
		{"label": "Request", "fieldname": "name", "fieldtype": "Link", "options": "Compensation Coupon Request", "width": 160},
		{"label": "Created By", "fieldname": "requested_by", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": "Approval Status", "fieldname": "approval_status", "fieldtype": "Data", "width": 110},
		{"label": "Approved By", "fieldname": "approved_by", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": "Issue Date", "fieldname": "issue_date", "fieldtype": "Date", "width": 110},
		{"label": "Expiry Date", "fieldname": "expiry_date", "fieldtype": "Date", "width": 110},
		{"label": "Redeemed", "fieldname": "redeemed", "fieldtype": "Data", "width": 90},
		{"label": "Redeemed Date", "fieldname": "redeemed_date", "fieldtype": "Datetime", "width": 150},
		{"label": "Related Complaint Number", "fieldname": "complaint_number", "fieldtype": "Data", "width": 170},
	]


def get_data(filters):
	conds = {}
	if filters.get("customer"):
		conds["customer"] = filters["customer"]
	if filters.get("approval_status"):
		conds["status"] = filters["approval_status"]
	if filters.get("branch"):
		conds["branch"] = filters["branch"]
	if filters.get("from_date") and filters.get("to_date"):
		conds["creation"] = ["between", [str(filters["from_date"]) + " 00:00:00", str(filters["to_date"]) + " 23:59:59"]]

	requests = frappe.get_all(
		"Compensation Coupon Request",
		filters=conds,
		fields=[
			"name", "customer", "customer_name", "branch", "status",
			"requested_by", "approved_by", "pos_coupon", "coupon_code", "complaint_number",
		],
		order_by="creation desc",
	)

	out = []
	for r in requests:
		coupon = None
		if r.pos_coupon and frappe.db.exists("POS Coupon", r.pos_coupon):
			coupon = frappe.db.get_value(
				"POS Coupon", r.pos_coupon,
				["valid_from", "valid_upto", "used", "last_used_on"],
				as_dict=True,
			)

		is_redeemed = bool(coupon and coupon.used)
		if filters.get("redeemed") == "Yes" and not is_redeemed:
			continue
		if filters.get("redeemed") == "No" and is_redeemed:
			continue

		out.append({
			"coupon_code": r.coupon_code,
			"name": r.name,
			"requested_by": r.requested_by,
			"approval_status": r.status,
			"approved_by": r.approved_by,
			"customer_name": r.customer_name,
			"branch": r.branch,
			"issue_date": coupon.valid_from if coupon else None,
			"expiry_date": coupon.valid_upto if coupon else None,
			"redeemed": "Yes" if is_redeemed else "No",
			"redeemed_date": coupon.last_used_on if coupon else None,
			"complaint_number": r.complaint_number,
		})

	return out
