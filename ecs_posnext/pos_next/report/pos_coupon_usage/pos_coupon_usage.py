# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	return get_columns(), data, None, get_chart(data), get_report_summary(data)


def get_columns():
	return [
		{
			"label": _("Invoice"),
			"fieldname": "invoice",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 150,
		},
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 85},
		{
			"label": _("Coupon Code"),
			"fieldname": "coupon_code",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Coupon"),
			"fieldname": "coupon",
			"fieldtype": "Link",
			"options": "POS Coupon",
			"width": 160,
		},
		{"label": _("Coupon Type"), "fieldname": "coupon_type", "fieldtype": "Data", "width": 105},
		{
			"label": _("Discount Type"),
			"fieldname": "discount_type",
			"fieldtype": "Data",
			"width": 175,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 130,
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": _("POS Profile"),
			"fieldname": "pos_profile",
			"fieldtype": "Link",
			"options": "POS Profile",
			"width": 130,
		},
		{
			"label": _("Cashier"),
			"fieldname": "cashier",
			"fieldtype": "Link",
			"options": "User",
			"width": 150,
		},
		{
			"label": _("Grand Total"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 110,
		},
		{
			"label": _("Invoice Discount"),
			"fieldname": "discount_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130,
		},
		{
			"label": _("Points Earned"),
			"fieldname": "points_earned",
			"fieldtype": "Float",
			"precision": 2,
			"width": 115,
		},
		{
			"label": _("Points from Coupon"),
			"fieldname": "coupon_points",
			"fieldtype": "Float",
			"precision": 2,
			"width": 145,
		},
		{
			"label": _("Cashback Earned"),
			"fieldname": "cashback_earned",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 135,
		},
		{
			"label": _("Cashback from Coupon"),
			"fieldname": "coupon_cashback",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 165,
		},
		{
			"label": _("Reward Status"),
			"fieldname": "reward_status",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Bonus Points %"),
			"fieldname": "bonus_points_percentage",
			"fieldtype": "Percent",
			"width": 120,
		},
		{
			"label": _("Bonus Cashback %"),
			"fieldname": "bonus_cashback_percentage",
			"fieldtype": "Percent",
			"width": 135,
		},
		{
			"label": _("Coupon Uses"),
			"fieldname": "used",
			"fieldtype": "Int",
			"width": 105,
		},
		{
			"label": _("Max Uses"),
			"fieldname": "maximum_use",
			"fieldtype": "Int",
			"width": 95,
		},
		{
			"label": _("Gift Card Balance"),
			"fieldname": "balance_amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 145,
		},
		{
			"label": _("Campaign"),
			"fieldname": "campaign",
			"fieldtype": "Link",
			"options": "Campaign",
			"width": 130,
		},
	]


def get_conditions(filters):
	conditions = []
	if filters.get("company"):
		conditions.append("si.company = %(company)s")
	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
	if filters.get("pos_profile"):
		conditions.append("si.pos_profile = %(pos_profile)s")
	if filters.get("cashier"):
		conditions.append("si.owner = %(cashier)s")
	if filters.get("coupon_code"):
		conditions.append("si.coupon_code = %(coupon_code)s")
	if filters.get("coupon_type"):
		conditions.append("c.coupon_type = %(coupon_type)s")
	if filters.get("discount_type"):
		conditions.append("c.discount_type = %(discount_type)s")

	# Cancelled invoices give back their coupon use, so they are off by default;
	# they stay available for auditing a coupon whose counter looks wrong.
	if filters.get("include_cancelled"):
		conditions.append("si.docstatus < 3")
	else:
		conditions.append("si.docstatus = 1")

	return " AND ".join(conditions)


def get_data(filters):
	rows = frappe.db.sql(
		"""
		SELECT
			si.name AS invoice,
			si.posting_date,
			si.docstatus,
			si.coupon_code,
			si.customer,
			si.customer_name,
			si.pos_profile,
			si.owner AS cashier,
			si.currency,
			si.grand_total,
			si.discount_amount,
			si.custom_bonus_points_percentage AS bonus_points_percentage,
			si.custom_bonus_cashback_percentage AS bonus_cashback_percentage,
			c.name AS coupon,
			c.coupon_type,
			c.discount_type,
			c.campaign,
			c.used,
			c.maximum_use,
			c.balance_amount
		FROM `tabSales Invoice` si
		LEFT JOIN `tabPOS Coupon` c ON c.coupon_code = si.coupon_code
		WHERE IFNULL(si.coupon_code, '') != '' AND {conditions}
		ORDER BY si.posting_date DESC, si.name DESC
	""".format(conditions=get_conditions(filters)),
		filters,
		as_dict=True,
	)

	if not rows:
		return []

	rewards = get_rewards({row.invoice for row in rows})

	for row in rows:
		row.status = {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(row.docstatus, "")
		# Invoices with nothing staged still need zeros, so the total row and the
		# formatter have numbers to work with instead of blanks.
		row.update({"points_earned": 0.0, "cashback_earned": 0.0, "coupon_points": 0.0, "coupon_cashback": 0.0})
		row.update(rewards.get(row.invoice) or {})

	return rows


def get_rewards(invoices):
	"""Staged loyalty rewards per invoice, split into the coupon's own share.

	loyalty_engine stages a "Cashback and Point Loyalty" coupon as its own
	Pending Loyalty Reward rows flagged is_bonus, so the coupon-granted part can
	be reported apart from the tier/POS Offer part. Cancelled stagings are left
	out - they were reversed and never reached the wallet.
	"""
	rewards = {}
	if not invoices:
		return rewards

	for row in frappe.db.sql(
		"""
		SELECT
			reference_name,
			reward_type,
			is_bonus,
			SUM(points) AS points,
			SUM(cashback_amount) AS cashback_amount,
			GROUP_CONCAT(DISTINCT status ORDER BY status) AS statuses
		FROM `tabPending Loyalty Reward`
		WHERE reference_doctype = 'Sales Invoice'
			AND reference_name IN %(invoices)s
			AND status != 'Cancelled'
		GROUP BY reference_name, reward_type, is_bonus
	""",
		{"invoices": tuple(invoices)},
		as_dict=True,
	):
		entry = rewards.setdefault(
			row.reference_name,
			{
				"points_earned": 0.0,
				"cashback_earned": 0.0,
				"coupon_points": 0.0,
				"coupon_cashback": 0.0,
				"reward_status": set(),
			},
		)

		# Reversals are staged as their own reward type with a positive amount.
		sign = -1 if row.reward_type in ("Points Reversal", "Cashback Reversal") else 1
		points = sign * flt(row.points)
		cashback = sign * flt(row.cashback_amount)

		entry["points_earned"] += points
		entry["cashback_earned"] += cashback
		if row.is_bonus:
			entry["coupon_points"] += points
			entry["coupon_cashback"] += cashback

		entry["reward_status"].update((row.statuses or "").split(","))

	for entry in rewards.values():
		entry["reward_status"] = ", ".join(sorted(s for s in entry["reward_status"] if s))

	return rewards


def get_report_summary(data):
	if not data:
		return None

	# Every row is filtered to one company, so the first row's currency covers them all.
	currency = data[0].get("currency")

	return [
		{"label": _("Redemptions"), "value": len(data), "datatype": "Int"},
		{
			"label": _("Distinct Coupons"),
			"value": len({row.coupon_code for row in data}),
			"datatype": "Int",
		},
		{
			"label": _("Customers"),
			"value": len({row.customer for row in data}),
			"datatype": "Int",
		},
		{
			"label": _("Discount Given"),
			"value": sum(flt(row.discount_amount) for row in data),
			"datatype": "Currency",
			"options": currency,
		},
		{
			"label": _("Points Earned"),
			"value": flt(sum(flt(row.get("points_earned")) for row in data), 2),
			"datatype": "Float",
		},
		{
			"label": _("Cashback Earned"),
			"value": sum(flt(row.get("cashback_earned")) for row in data),
			"datatype": "Currency",
			"options": currency,
		},
	]


def get_chart(data):
	if not data:
		return None

	totals = {}
	for row in data:
		bucket = totals.setdefault(row.coupon_code, {"discount": 0.0, "cashback": 0.0})
		bucket["discount"] += flt(row.discount_amount)
		bucket["cashback"] += flt(row.get("cashback_earned"))

	top = sorted(totals.items(), key=lambda item: item[1]["discount"] + item[1]["cashback"], reverse=True)[:10]

	return {
		"data": {
			"labels": [code for code, _totals in top],
			"datasets": [
				{"name": _("Discount Given"), "values": [flt(t["discount"], 2) for _code, t in top]},
				{"name": _("Cashback Earned"), "values": [flt(t["cashback"], 2) for _code, t in top]},
			],
		},
		"type": "bar",
		"barOptions": {"stacked": 1},
	}
