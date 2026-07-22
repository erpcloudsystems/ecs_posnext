import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters or {})
	return columns, data


def get_columns():
	return [
		{"label": "Invoice ID", "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
		{"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": "POS Profile", "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile", "width": 130},
		{"label": "POS Shift", "fieldname": "posa_pos_opening_shift", "fieldtype": "Link", "options": "POS Opening Shift", "width": 150},
		{"label": "POS Business Day", "fieldname": "custom_pos_business_day", "fieldtype": "Link", "options": "POS Business Day", "width": 150},
		{"label": "POS Cashier Shift", "fieldname": "custom_pos_cashier_shift", "fieldtype": "Link", "options": "POS Cashier Shift", "width": 150},
		{"label": "Order Type", "fieldname": "custom_order_type", "fieldtype": "Data", "width": 100},
	]


def get_data(filters):
	conditions = ["docstatus = 1"]
	values = {}

	if filters.get("from_date"):
		conditions.append("posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	if filters.get("branch"):
		conditions.append("branch = %(branch)s")
		values["branch"] = filters["branch"]
	if filters.get("pos_profile"):
		conditions.append("pos_profile = %(pos_profile)s")
		values["pos_profile"] = filters["pos_profile"]
	if filters.get("pos_shift"):
		conditions.append("posa_pos_opening_shift = %(pos_shift)s")
		values["pos_shift"] = filters["pos_shift"]
	if filters.get("pos_business_day"):
		conditions.append("custom_pos_business_day = %(pos_business_day)s")
		values["pos_business_day"] = filters["pos_business_day"]
	if filters.get("pos_cashier_shift"):
		conditions.append("custom_pos_cashier_shift = %(pos_cashier_shift)s")
		values["pos_cashier_shift"] = filters["pos_cashier_shift"]

	where_clause = " AND ".join(conditions)

	return frappe.db.sql(
		f"""
		SELECT
			name, customer_name, posting_date, grand_total, branch,
			pos_profile, posa_pos_opening_shift, custom_pos_business_day,
			custom_pos_cashier_shift, custom_order_type
		FROM `tabSales Invoice`
		WHERE {where_clause}
		ORDER BY posting_date DESC, posting_time DESC
		""",
		values=values,
		as_dict=True,
	)
