import frappe


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "Driver", "fieldname": "driver", "fieldtype": "Link", "options": "Driver", "width": 160},
		{"label": "Driver Name", "fieldname": "driver_name", "fieldtype": "Data", "width": 180},
		{"label": "Channel", "fieldname": "delivery_channel", "fieldtype": "Data", "width": 100},
		{"label": "Assigned", "fieldname": "assigned", "fieldtype": "Int", "width": 100},
		{"label": "Delivered", "fieldname": "delivered", "fieldtype": "Int", "width": 100},
		{"label": "Returned", "fieldname": "returned", "fieldtype": "Int", "width": 100},
		{"label": "Failed", "fieldname": "failed", "fieldtype": "Int", "width": 100},
		{"label": "Cash Collected", "fieldname": "cash_collected", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	conds = ["da.docstatus != 2"]
	vals = {}
	if filters.get("from_date"):
		conds.append("da.assigned_time >= %(from_date)s")
		vals["from_date"] = str(filters["from_date"]) + " 00:00:00"
	if filters.get("to_date"):
		conds.append("da.assigned_time <= %(to_date)s")
		vals["to_date"] = str(filters["to_date"]) + " 23:59:59"
	if filters.get("driver"):
		conds.append("da.driver = %(driver)s")
		vals["driver"] = filters["driver"]

	# Branch filter joins the linked Sales Invoice.
	join = ""
	if filters.get("branch"):
		join = "INNER JOIN `tabSales Invoice` si ON si.name = da.order_reference AND da.order_doctype = 'Sales Invoice'"
		conds.append("si.branch = %(branch)s")
		vals["branch"] = filters["branch"]

	rows = frappe.db.sql(
		f"""
		SELECT
			da.driver AS driver,
			da.delivery_channel AS delivery_channel,
			COUNT(*) AS assigned,
			SUM(CASE WHEN da.status = 'Delivered' THEN 1 ELSE 0 END) AS delivered,
			SUM(CASE WHEN da.status = 'Returned' THEN 1 ELSE 0 END) AS returned,
			SUM(CASE WHEN da.status = 'Failed' THEN 1 ELSE 0 END) AS failed,
			SUM(CASE WHEN da.status = 'Delivered' THEN IFNULL(da.amount_collected, 0) ELSE 0 END) AS cash_collected
		FROM `tabDelivery Assignment` da
		{join}
		WHERE {' AND '.join(conds)}
		GROUP BY da.driver, da.delivery_channel
		ORDER BY assigned DESC
		""",
		vals,
		as_dict=True,
	)

	driver_names = {}
	ids = [r.driver for r in rows if r.driver]
	if ids:
		driver_names = {d.name: d.full_name for d in frappe.get_all("Driver", filters={"name": ["in", ids]}, fields=["name", "full_name"])}
	for r in rows:
		r["driver_name"] = driver_names.get(r.driver) or (r.delivery_channel if not r.driver else r.driver)
	return rows
