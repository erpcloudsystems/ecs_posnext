import frappe


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Complaint #", "fieldname": "complaint_number", "fieldtype": "Data", "width": 120},
		{"label": "Complaint", "fieldname": "name", "fieldtype": "Link", "options": "Customer Complaint", "width": 160},
		{"label": "Date", "fieldname": "complaint_date", "fieldtype": "Datetime", "width": 150},
		{"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 120},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": "Resolved", "fieldname": "resolved", "fieldtype": "Int", "width": 80},
		{"label": "Resolution", "fieldname": "resolution_notes", "fieldtype": "Data", "width": 240},
		{"label": "Compensation Coupon", "fieldname": "coupon_code", "fieldtype": "Data", "width": 150},
		{"label": "Accepted by Agent", "fieldname": "accepted", "fieldtype": "Int", "width": 130},
		{"label": "Used", "fieldname": "used", "fieldtype": "Int", "width": 70},
	]


def get_data(filters):
	conds = {}
	if filters.get("from_date") and filters.get("to_date"):
		conds["complaint_date"] = ["between", [str(filters["from_date"]) + " 00:00:00", str(filters["to_date"]) + " 23:59:59"]]
	if filters.get("branch"):
		conds["branch"] = filters["branch"]
	if filters.get("status"):
		conds["status"] = filters["status"]

	complaints = frappe.get_all(
		"Customer Complaint",
		filters=conds,
		fields=["name", "custom_complaint_number", "complaint_date", "customer_name",
				"branch", "type", "status", "resolution_notes"],
		order_by="complaint_date desc",
	)

	has_ccr = frappe.db.exists("DocType", "Compensation Coupon Request")
	ccr_fields = set(frappe.get_meta("Compensation Coupon Request").get_valid_columns()) if has_ccr else set()

	out = []
	for c in complaints:
		coupon_code = None
		accepted = 0   # coupon request approved by an agent/manager
		used = 0       # the issued coupon was actually used
		if has_ccr:
			ccr_filter = None
			if "complaint" in ccr_fields:
				ccr_filter = {"complaint": c.name}
			elif "complaint_number" in ccr_fields and c.custom_complaint_number:
				ccr_filter = {"complaint_number": c.custom_complaint_number}
			ccr = frappe.db.get_value(
				"Compensation Coupon Request", ccr_filter,
				["status", "pos_coupon", "coupon_code"], as_dict=True,
			) if ccr_filter else None
			if ccr:
				coupon_code = ccr.get("coupon_code")
				accepted = 1 if ccr.get("status") == "Approved" else 0
				if ccr.get("pos_coupon") and frappe.db.exists("POS Coupon", ccr.get("pos_coupon")):
					used = 1 if frappe.db.get_value("POS Coupon", ccr.get("pos_coupon"), "used") else 0

		out.append({
			"name": c.name,
			"complaint_number": c.custom_complaint_number,
			"complaint_date": c.complaint_date,
			"customer_name": c.customer_name,
			"branch": c.branch,
			"type": c.type,
			"status": c.status,
			"resolved": 1 if c.status == "Resolved" else 0,
			"resolution_notes": c.resolution_notes,
			"coupon_code": coupon_code,
			"accepted": accepted,
			"used": used,
		})
	return out
