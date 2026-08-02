"""Business Day Closing Report.

Per POS Business Day: expected (from the day's orders) vs actual (from the shift
closings' per-mode reconciliation), broken down by Branch / Call Center and payment
mode, plus paid/returned/void order counts and a shift-status summary. Each metric row
links to the underlying Sales Invoices for review.
"""

import frappe
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}
	business_day = filters.get("business_day")
	if not business_day:
		frappe.throw("Please select a POS Business Day.")
	return get_columns(), get_data(business_day)


def get_columns():
	return [
		{"label": "Item", "fieldname": "item", "fieldtype": "Data", "width": 260},
		{"label": "Expected", "fieldname": "expected", "fieldtype": "Currency", "width": 130},
		{"label": "Actual", "fieldname": "actual", "fieldtype": "Currency", "width": 130},
		{"label": "Difference", "fieldname": "difference", "fieldtype": "Currency", "width": 120},
		{"label": "Count", "fieldname": "count", "fieldtype": "Int", "width": 80},
		{"label": "Note", "fieldname": "note", "fieldtype": "Data", "width": 140},
		{"label": "Invoices", "fieldname": "invoices", "fieldtype": "Data", "width": 110},
	]


def _is_cc(profile):
	return "call center" in (profile or "").lower()


def _category(mode_name, mode_type):
	"""Classify a payment mode into a report bucket."""
	n = (mode_name or "").lower()
	if "vodafone" in n:
		return "vodafone"
	if "insta" in n:
		return "instapay"
	if "hospitality" in n:
		return "hospitality"
	if (mode_type or "") == "Cash":
		return "cash"
	return "credit"


def _link(business_day, extra=""):
	"""HTML anchor to the Sales Invoice list filtered for review (rendered by the report JS)."""
	url = f"/app/sales-invoice/view/list?custom_pos_business_day={business_day}{extra}"
	return f'<a href="{url}" target="_blank">Review</a>'


def get_data(business_day):
	bd = frappe.db.get_value(
		"POS Business Day", business_day,
		["business_date", "pos_profile", "status"], as_dict=True,
	) or {}

	# ---- Expected vs Actual: BOTH from each shift's per-mode reconciliation ----
	# Sourcing both sides from the same reconciliation (the closing, or a live recompute
	# for a not-yet-closed shift) makes Difference the true shortage/overage. Expected
	# already includes the opening float + COD collected — exactly like the counted
	# drawer — so it no longer looks like a discrepancy.
	from ecs_posnext.api.cashier_shift import compute_cash_figures

	shifts = frappe.get_all(
		"POS Cashier Shift",
		filters={"pos_business_day": business_day},
		fields=["name", "status", "cashier_user", "pos_profile", "cashier_shift_closing", "pos_opening_shift"],
	)

	exp = _zero_buckets()
	act = _zero_buckets()
	for s in shifts:
		cc = _is_cc(s.pos_profile)
		recon = []
		if s.cashier_shift_closing and frappe.db.exists("POS Cashier Shift Closing", s.cashier_shift_closing):
			recon = frappe.get_all(
				"POS Closing Shift Detail",
				filters={"parent": s.cashier_shift_closing},
				fields=["mode_of_payment", "expected_amount", "closing_amount"],
			)
		elif s.pos_opening_shift:
			# Shift not closed yet — recompute expected live; actual is still 0.
			try:
				fig = compute_cash_figures(s.pos_opening_shift)
				recon = [
					{"mode_of_payment": r["mode_of_payment"], "expected_amount": r.get("expected_amount"), "closing_amount": 0}
					for r in (fig.payment_reconciliation or [])
				]
			except Exception:
				recon = []
		for row in recon:
			mode = row["mode_of_payment"] if isinstance(row, dict) else row.mode_of_payment
			mtype = frappe.get_cached_value("Mode of Payment", mode, "type")
			cat = _category(mode, mtype)
			talabat = "talabat" in (mode or "").lower()
			exp_amt = row["expected_amount"] if isinstance(row, dict) else row.expected_amount
			act_amt = row["closing_amount"] if isinstance(row, dict) else row.closing_amount
			_add(exp, cc, talabat, cat, flt(exp_amt))
			_add(act, cc, talabat, cat, flt(act_amt))

	# ---- Order counts ----
	paid = frappe.db.count("Sales Invoice", {"custom_pos_business_day": business_day, "docstatus": 1, "is_return": 0, "outstanding_amount": ["<=", 0]})
	unpaid = frappe.db.count("Sales Invoice", {"custom_pos_business_day": business_day, "docstatus": 1, "is_return": 0, "outstanding_amount": [">", 0]})
	returned = frappe.db.count("Sales Invoice", {"custom_pos_business_day": business_day, "docstatus": 1, "is_return": 1})
	void = frappe.db.count("Sales Invoice", {"custom_pos_business_day": business_day, "docstatus": 2})

	# ---- Shifts (already fetched above) ----
	closed_shifts = [s for s in shifts if s.status == "Closed" and s.cashier_shift_closing]

	def mrow(item, e=None, a=None, count=None, note=None, link_extra=""):
		row = {"item": item}
		if e is not None or a is not None:
			row["expected"] = flt(e)
			row["actual"] = flt(a)
			row["difference"] = flt(a) - flt(e)
		if count is not None:
			row["count"] = count
		if note:
			row["note"] = note
		row["invoices"] = _link(business_day, link_extra)
		return row

	data = []
	data.append({"item": f"Business Day {business_day} ({bd.get('business_date')})", "note": bd.get("status")})
	data.append({"item": f"Shifts: {len(shifts)}  |  Closed: {len(closed_shifts)}", "count": len(shifts)})

	# Branch
	data.append(mrow("Branch Cash", exp["branch"]["cash"], act["branch"]["cash"], link_extra="&is_return=0"))
	data.append(mrow("Branch Credit (Card)", exp["branch"]["credit"], act["branch"]["credit"], link_extra="&is_return=0"))
	# Call Center
	data.append(mrow("Call Center Vodafone", exp["cc"]["vodafone"], act["cc"]["vodafone"], link_extra="&pos_profile=Call Center"))
	data.append(mrow("Call Center Instapay", exp["cc"]["instapay"], act["cc"]["instapay"], link_extra="&pos_profile=Call Center"))
	data.append(mrow("Call Center Cash (Collected)", exp["cc"]["cash"], act["cc"]["cash"], link_extra="&pos_profile=Call Center"))
	data.append(mrow("Call Center Credit (Card)", exp["cc"]["credit"], act["cc"]["credit"], link_extra="&pos_profile=Call Center"))
	# Detailed extras
	data.append(mrow("Talabat Cash", exp["talabat"]["cash"], act["talabat"].get("cash", 0), link_extra="&custom_order_type=Talabat"))
	data.append(mrow("Vodafone Cash (All)", exp["all"]["vodafone"], act["all"]["vodafone"]))
	data.append(mrow("Instapay (All)", exp["all"]["instapay"], act["all"]["instapay"]))
	data.append(mrow("Hospitality Orders", exp["all"]["hospitality"], act["all"]["hospitality"]))

	# Counts
	data.append(mrow("Total Paid Orders (Branch & Call Center)", count=paid, link_extra="&is_return=0&status=Paid"))
	data.append(mrow("Total Unpaid / Outstanding Orders", count=unpaid, link_extra="&is_return=0"))
	data.append(mrow("Total Returned Orders (Branch & Call Center)", count=returned, link_extra="&is_return=1"))
	data.append(mrow("Void / Cancelled Orders", count=void, link_extra="&docstatus=2"))

	# Shift status summary
	data.append({"item": "— Shift Status Summary —"})
	for s in shifts:
		status = "Closed" if (s.status == "Closed" and s.cashier_shift_closing) else "(Still Opened)"
		data.append({
			"item": f"{s.name} · {s.cashier_user or ''} · {s.pos_profile or ''}",
			"note": status,
		})

	return data


def _zero_buckets():
	def cats():
		return {"cash": 0.0, "credit": 0.0, "vodafone": 0.0, "instapay": 0.0, "hospitality": 0.0}
	return {"branch": cats(), "cc": cats(), "talabat": cats(), "all": cats()}


def _add(buckets, is_cc, is_talabat, cat, amount):
	buckets["all"][cat] = flt(buckets["all"].get(cat, 0)) + amount
	if is_talabat:
		buckets["talabat"][cat] = flt(buckets["talabat"].get(cat, 0)) + amount
	elif is_cc:
		buckets["cc"][cat] = flt(buckets["cc"].get(cat, 0)) + amount
	else:
		buckets["branch"][cat] = flt(buckets["branch"].get(cat, 0)) + amount
