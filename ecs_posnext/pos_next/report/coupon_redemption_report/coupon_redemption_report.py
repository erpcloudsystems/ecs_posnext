import frappe


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 130},
		{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
		{"label": "Coupon", "fieldname": "coupon", "fieldtype": "Link", "options": "POS Coupon", "width": 130},
		{"label": "Coupon Code", "fieldname": "coupon_code", "fieldtype": "Data", "width": 110},
		{"label": "Order", "fieldname": "invoice_name", "fieldtype": "Dynamic Link", "options": "invoice_doctype", "width": 160},
		{"label": "Order Type", "fieldname": "invoice_doctype", "fieldtype": "Link", "options": "DocType", "width": 100},
		{"label": "Discount Type", "fieldname": "discount_type", "fieldtype": "Data", "width": 100},
		{"label": "Discount Value", "fieldname": "discount_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Usage Date", "fieldname": "redeemed_on", "fieldtype": "Datetime", "width": 160},
	]


def get_data(filters):
	conds = {}
	if filters.get("customer"):
		conds["customer"] = filters["customer"]
	if filters.get("coupon"):
		conds["coupon"] = filters["coupon"]
	if filters.get("from_date") and filters.get("to_date"):
		conds["redeemed_on"] = [
			"between",
			[str(filters["from_date"]) + " 00:00:00", str(filters["to_date"]) + " 23:59:59"],
		]

	return frappe.get_all(
		"POS Coupon Redemption",
		filters=conds,
		fields=[
			"customer", "customer_name", "coupon", "coupon_code",
			"invoice_name", "invoice_doctype", "discount_type",
			"discount_amount", "redeemed_on",
		],
		order_by="redeemed_on desc",
	)
