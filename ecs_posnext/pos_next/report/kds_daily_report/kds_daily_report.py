import frappe
from frappe.utils import flt, time_diff_in_seconds


def execute(filters=None):
	filters = filters or {}
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": "KDS Order", "fieldname": "name", "fieldtype": "Link", "options": "KDS Order", "width": 150},
		{"label": "Order #", "fieldname": "custom_number_order", "fieldtype": "Data", "width": 80},
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": "Type", "fieldname": "order_type", "fieldtype": "Data", "width": 90},
		{"label": "Order Time", "fieldname": "order_time", "fieldtype": "Datetime", "width": 155},
		{"label": "Done Time", "fieldname": "done_time", "fieldtype": "Datetime", "width": 155},
		{"label": "Preparing (min)", "fieldname": "prep_minutes", "fieldtype": "Float", "precision": 1, "width": 110},
		{"label": "Target (min)", "fieldname": "target_minutes", "fieldtype": "Int", "width": 90},
		{"label": "On Time", "fieldname": "on_time", "fieldtype": "Int", "width": 80},
		{"label": "Overdue", "fieldname": "overdue", "fieldtype": "Int", "width": 80},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
	]


def get_data(filters):
	conds = ["1=1"]
	vals = {}
	if filters.get("from_date"):
		conds.append("order_time >= %(from_date)s")
		vals["from_date"] = str(filters["from_date"]) + " 00:00:00"
	if filters.get("to_date"):
		conds.append("order_time <= %(to_date)s")
		vals["to_date"] = str(filters["to_date"]) + " 23:59:59"
	if filters.get("branch"):
		conds.append("branch = %(branch)s")
		vals["branch"] = filters["branch"]
	if filters.get("order_type"):
		conds.append("order_type = %(order_type)s")
		vals["order_type"] = filters["order_type"]

	rows = frappe.db.sql(
		f"""
		SELECT name, custom_number_order, branch, order_type, order_time,
		       completed_time, ready_time, target_minutes, status
		FROM `tabKDS Order`
		WHERE {' AND '.join(conds)}
		ORDER BY order_time DESC
		""",
		vals,
		as_dict=True,
	)

	out = []
	for r in rows:
		done = r.completed_time or r.ready_time
		prep = None
		if r.order_time and done:
			prep = flt(time_diff_in_seconds(done, r.order_time) / 60.0, 1)
		r["done_time"] = done
		r["prep_minutes"] = prep
		# On-time / overdue only meaningful once the order is done and has a target.
		r["on_time"] = 0
		r["overdue"] = 0
		if prep is not None and r.target_minutes:
			if prep <= r.target_minutes:
				r["on_time"] = 1
			else:
				r["overdue"] = 1
		out.append(r)
	return out
