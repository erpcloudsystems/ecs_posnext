import frappe


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Complaint #", "fieldname": "complaint_number", "fieldtype": "Data", "width": 120},
		{"label": "Complaint", "fieldname": "name", "fieldtype": "Link", "options": "Customer Complaint", "width": 140},
		{"label": "Date", "fieldname": "complaint_date", "fieldtype": "Datetime", "width": 150},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 130},
		{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
		{"label": "Agent", "fieldname": "owner", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": "Complaint Details", "fieldname": "complaint_details", "fieldtype": "Data", "width": 260},
		{"label": "Type", "fieldname": "type", "fieldtype": "Data", "width": 110},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": "Resolution", "fieldname": "resolution_notes", "fieldtype": "Data", "width": 200},
		{"label": "Order Number", "fieldname": "order_number", "fieldtype": "Dynamic Link", "options": "order_doctype", "width": 150},
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 110},
		{"label": "Business Day", "fieldname": "pos_business_day", "fieldtype": "Link", "options": "POS Business Day", "width": 130},
		{"label": "Cashier Shift", "fieldname": "pos_cashier_shift", "fieldtype": "Link", "options": "POS Cashier Shift", "width": 130},
		{"label": "Order Date & Time", "fieldname": "order_datetime", "fieldtype": "Datetime", "width": 150},
		{"label": "Order Status", "fieldname": "order_status", "fieldtype": "Data", "width": 100},
		{"label": "Delivery Type", "fieldname": "delivery_type", "fieldtype": "Data", "width": 110},
		{"label": "Assigned Delivery", "fieldname": "assigned_delivery", "fieldtype": "Link", "options": "Delivery Assignment", "width": 140},
		{"label": "Resolved", "fieldname": "resolved", "fieldtype": "Int", "width": 80},
		{"label": "Compensation Coupon", "fieldname": "coupon_code", "fieldtype": "Data", "width": 150},
		{"label": "Accepted by Agent", "fieldname": "accepted", "fieldtype": "Int", "width": 130},
		{"label": "Used", "fieldname": "used", "fieldtype": "Int", "width": 70},
	]


def get_data(filters):
	conds = ["1=1"]
	values = {}

	# complaint_date is unreliable on older/older-style rows (was left NULL before
	# the backfill patch) — always fall back to `creation` so filtering/sorting
	# never silently drops rows.
	if filters.get("from_date") and filters.get("to_date"):
		conds.append("COALESCE(cc.complaint_date, cc.creation) BETWEEN %(from_date)s AND %(to_date)s")
		values["from_date"] = f"{filters['from_date']} 00:00:00"
		values["to_date"] = f"{filters['to_date']} 23:59:59"
	if filters.get("branch"):
		conds.append("cc.branch = %(branch)s")
		values["branch"] = filters["branch"]
	if filters.get("status"):
		conds.append("cc.status = %(status)s")
		values["status"] = filters["status"]
	if filters.get("customer"):
		conds.append("cc.customer = %(customer)s")
		values["customer"] = filters["customer"]
	if filters.get("agent"):
		conds.append("cc.owner = %(agent)s")
		values["agent"] = filters["agent"]
	if filters.get("pos_cashier_shift"):
		conds.append("cc.custom_pos_cashier_shift = %(pos_cashier_shift)s")
		values["pos_cashier_shift"] = filters["pos_cashier_shift"]
	if filters.get("pos_business_day"):
		conds.append("cc.custom_pos_business_day = %(pos_business_day)s")
		values["pos_business_day"] = filters["pos_business_day"]

	complaints = frappe.db.sql(
		f"""
		SELECT
			cc.name, cc.custom_complaint_number AS complaint_number,
			COALESCE(cc.complaint_date, cc.creation) AS complaint_date,
			cc.customer, cc.customer_name, cc.owner, cc.branch, cc.type, cc.status,
			cc.resolution_notes, cc.complaint_details,
			cc.custom_order_doctype AS order_doctype,
			cc.custom_order_reference AS order_number,
			cc.custom_pos_business_day AS pos_business_day,
			cc.custom_pos_cashier_shift AS pos_cashier_shift,
			da.name AS assigned_delivery,
			si.status AS order_status,
			si.posting_date AS order_posting_date,
			si.posting_time AS order_posting_time,
			da.status AS delivery_type
		FROM `tabCustomer Complaint` cc
		LEFT JOIN `tabSales Invoice` si
			ON cc.custom_order_doctype = 'Sales Invoice' AND cc.custom_order_reference = si.name
		LEFT JOIN (
			-- An order can go through several Delivery Assignments (reassignment
			-- after a failed/returned delivery) — only the latest one is relevant.
			SELECT da1.order_doctype, da1.order_reference, da1.name, da1.status
			FROM `tabDelivery Assignment` da1
			INNER JOIN (
				SELECT order_doctype, order_reference, MAX(creation) AS max_creation
				FROM `tabDelivery Assignment`
				GROUP BY order_doctype, order_reference
			) latest
				ON latest.order_doctype = da1.order_doctype
				AND latest.order_reference = da1.order_reference
				AND latest.max_creation = da1.creation
		) da
			ON da.order_doctype = cc.custom_order_doctype AND da.order_reference = cc.custom_order_reference
		WHERE {" AND ".join(conds)}
		ORDER BY COALESCE(cc.complaint_date, cc.creation) DESC
		""",
		values,
		as_dict=True,
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
			elif "complaint_number" in ccr_fields and c.complaint_number:
				ccr_filter = {"complaint_number": c.complaint_number}
			ccr = frappe.db.get_value(
				"Compensation Coupon Request", ccr_filter,
				["status", "pos_coupon", "coupon_code"], as_dict=True,
			) if ccr_filter else None
			if ccr:
				coupon_code = ccr.get("coupon_code")
				accepted = 1 if ccr.get("status") == "Approved" else 0
				if ccr.get("pos_coupon") and frappe.db.exists("POS Coupon", ccr.get("pos_coupon")):
					used = 1 if frappe.db.get_value("POS Coupon", ccr.get("pos_coupon"), "used") else 0

		order_datetime = None
		if c.order_posting_date:
			order_datetime = f"{c.order_posting_date} {c.order_posting_time or '00:00:00'}"

		out.append({
			"name": c.name,
			"complaint_number": c.complaint_number,
			"complaint_date": c.complaint_date,
			"customer": c.customer,
			"customer_name": c.customer_name,
			"owner": c.owner,
			"complaint_details": c.complaint_details,
			"branch": c.branch,
			"pos_business_day": c.pos_business_day,
			"pos_cashier_shift": c.pos_cashier_shift,
			"order_doctype": c.order_doctype,
			"order_number": c.order_number,
			"order_datetime": order_datetime,
			"order_status": c.order_status,
			"delivery_type": c.delivery_type,
			"assigned_delivery": c.assigned_delivery,
			"type": c.type,
			"status": c.status,
			"resolved": 1 if c.status == "Closed" else 0,
			"resolution_notes": c.resolution_notes,
			"coupon_code": coupon_code,
			"accepted": accepted,
			"used": used,
		})
	return out
