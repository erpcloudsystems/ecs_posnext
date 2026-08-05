import frappe


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Order #", "fieldname": "custom_number_order", "fieldtype": "Data", "width": 90},
		{"label": "Invoice", "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 150},
		{"label": "POS Profile", "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile", "width": 120},
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 170},
		{"label": "Customer Number", "fieldname": "customer_number", "fieldtype": "Data", "width": 130},
		{"label": "Order Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Order Time", "fieldname": "posting_time", "fieldtype": "Data", "width": 90},
		{"label": "Order Type", "fieldname": "order_type", "fieldtype": "Data", "width": 90},
		{"label": "Delivery Status", "fieldname": "delivery_status", "fieldtype": "Data", "width": 120},
		{"label": "KDS Status", "fieldname": "kds_status", "fieldtype": "Data", "width": 110},
	]


def get_data(filters):
	conds = [
		"si.docstatus = 1",
		"IFNULL(si.is_return, 0) = 0",
	]
	vals = {}
	# Datetime filters — compare the order's full timestamp (date + time), so a time-of-day
	# window works, not just whole days.
	if filters.get("from_date"):
		conds.append("timestamp(si.posting_date, IFNULL(si.posting_time, '00:00:00')) >= %(from_date)s")
		vals["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conds.append("timestamp(si.posting_date, IFNULL(si.posting_time, '00:00:00')) <= %(to_date)s")
		vals["to_date"] = filters["to_date"]
	if filters.get("pos_profile"):
		conds.append("si.pos_profile = %(pos_profile)s")
		vals["pos_profile"] = filters["pos_profile"]
	if filters.get("branch"):
		conds.append("si.branch = %(branch)s")
		vals["branch"] = filters["branch"]
	if filters.get("order_type"):
		conds.append("si.custom_order_type = %(order_type)s")
		vals["order_type"] = filters["order_type"]

	rows = frappe.db.sql(
		f"""
		SELECT
			si.name,
			si.custom_number_order,
			si.pos_profile,
			si.branch,
			si.customer_name,
			COALESCE(NULLIF(si.contact_mobile, ''), cust.mobile_no) AS customer_number,
			si.posting_date,
			si.posting_time,
			si.custom_order_type AS order_type,
			(
				SELECT da.status FROM `tabDelivery Assignment` da
				WHERE da.order_reference = si.name AND da.order_doctype = 'Sales Invoice'
				  AND da.docstatus != 2
				ORDER BY da.creation DESC LIMIT 1
			) AS delivery_status,
			(
				SELECT ko.status FROM `tabKDS Order` ko
				WHERE ko.sales_invoice = si.name AND ko.status != 'Cancelled'
				ORDER BY ko.creation DESC LIMIT 1
			) AS kds_status
		FROM `tabSales Invoice` si
		LEFT JOIN `tabCustomer` cust ON cust.name = si.customer
		WHERE {' AND '.join(conds)}
		ORDER BY si.posting_date DESC, si.posting_time DESC
		""",
		vals,
		as_dict=True,
	)

	for r in rows:
		# Delivery status only meaningful for delivery-type orders.
		if (r.get("order_type") or "").strip().lower() not in ("delivery", "talabat"):
			r["delivery_status"] = ""
		r["posting_time"] = str(r.get("posting_time") or "")[:8]
	return rows
