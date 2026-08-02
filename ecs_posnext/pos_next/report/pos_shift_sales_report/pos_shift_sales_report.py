import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters or {})
	return columns, data


def get_columns():
	return [
		{"label": "Type", "fieldname": "voucher_type", "fieldtype": "Data", "width": 110},
		{"label": "Voucher", "fieldname": "name", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 160},
		{"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Amount", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
		{"label": "Mode of Payment", "fieldname": "mode_of_payment", "fieldtype": "Data", "width": 130},
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": "POS Profile", "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile", "width": 130},
		{"label": "POS Shift", "fieldname": "posa_pos_opening_shift", "fieldtype": "Link", "options": "POS Opening Shift", "width": 150},
		{"label": "POS Business Day", "fieldname": "custom_pos_business_day", "fieldtype": "Link", "options": "POS Business Day", "width": 150},
		{"label": "POS Cashier Shift", "fieldname": "custom_pos_cashier_shift", "fieldtype": "Link", "options": "POS Cashier Shift", "width": 150},
		{"label": "Order Type", "fieldname": "custom_order_type", "fieldtype": "Data", "width": 100},
	]


def get_data(filters):
	rows = _get_invoices(filters) + _get_payment_entries(filters)
	# Newest first; Payment Entries have no posting_time, so fall back to an empty string.
	rows.sort(key=lambda r: (str(r.get("posting_date") or ""), str(r.get("posting_time") or "")), reverse=True)
	return rows


def _get_invoices(filters):
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
			'Sales Invoice' AS voucher_type,
			name, customer_name, posting_date, posting_time, grand_total,
			NULL AS mode_of_payment, branch, pos_profile, posa_pos_opening_shift,
			custom_pos_business_day, custom_pos_cashier_shift, custom_order_type
		FROM `tabSales Invoice`
		WHERE {where_clause}
		""",
		values=values,
		as_dict=True,
	)


def _get_payment_entries(filters):
	"""COD / Call Center / All-Orders collections are Payment Entries stamped with
	`custom_pos_business_day` / `custom_pos_cashier_shift`. Show them alongside the
	invoices for the same shift, enriched with the shift's POS Profile / branch."""
	conditions = [
		"pe.docstatus = 1",
		"pe.payment_type = 'Receive'",
		"IFNULL(pe.custom_pos_cashier_shift, '') != ''",
	]
	values = {}

	if filters.get("from_date"):
		conditions.append("pe.posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("pe.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	if filters.get("branch"):
		conditions.append("prof.branch = %(branch)s")
		values["branch"] = filters["branch"]
	if filters.get("pos_profile"):
		conditions.append("cs.pos_profile = %(pos_profile)s")
		values["pos_profile"] = filters["pos_profile"]
	if filters.get("pos_shift"):
		conditions.append("cs.pos_opening_shift = %(pos_shift)s")
		values["pos_shift"] = filters["pos_shift"]
	if filters.get("pos_business_day"):
		conditions.append("pe.custom_pos_business_day = %(pos_business_day)s")
		values["pos_business_day"] = filters["pos_business_day"]
	if filters.get("pos_cashier_shift"):
		conditions.append("pe.custom_pos_cashier_shift = %(pos_cashier_shift)s")
		values["pos_cashier_shift"] = filters["pos_cashier_shift"]

	where_clause = " AND ".join(conditions)
	return frappe.db.sql(
		f"""
		SELECT
			'Payment Entry' AS voucher_type,
			pe.name AS name,
			pe.party_name AS customer_name,
			pe.posting_date AS posting_date,
			NULL AS posting_time,
			pe.paid_amount AS grand_total,
			pe.mode_of_payment AS mode_of_payment,
			prof.branch AS branch,
			cs.pos_profile AS pos_profile,
			cs.pos_opening_shift AS posa_pos_opening_shift,
			pe.custom_pos_business_day AS custom_pos_business_day,
			pe.custom_pos_cashier_shift AS custom_pos_cashier_shift,
			'COD Collection' AS custom_order_type
		FROM `tabPayment Entry` pe
		LEFT JOIN `tabPOS Cashier Shift` cs ON cs.name = pe.custom_pos_cashier_shift
		LEFT JOIN `tabPOS Profile` prof ON prof.name = cs.pos_profile
		WHERE {where_clause}
		""",
		values=values,
		as_dict=True,
	)
