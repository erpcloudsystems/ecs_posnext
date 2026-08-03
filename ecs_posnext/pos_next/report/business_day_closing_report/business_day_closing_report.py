"""Business Day Closing Report.

Per POS Business Day: expected (from the day's orders) vs actual (from the shift
closings' per-mode reconciliation), broken down by Branch / Call Center and payment
mode, plus paid/returned/void order counts and a shift-status summary. Each metric row
links to the underlying Sales Invoices for review.

Expected/Actual come from the closing snapshot, which is frozen when the cashier
submits their count. Two kinds of collection can therefore land outside it, and both
are reported separately at the bottom so the day still ties out:
  * post-close COD — a Payment Entry tagged to the shift but created after the count;
  * unassigned COD — a Payment Entry against one of the day's invoices carrying no
    shift reference at all (typically entered from the back office, not the POS).

A final "Total Collected (Snapshot + Outside)" section adds those back, so the day's
Expected reconciles with the Sales by Working Day page while each shift's Difference
stays a pure drawer shortage.
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


# (label, bucket, category, invoice-list filter) for the tie-out section — mirrors the
# metric rows above, emitted only for buckets that actually have collections outside
# the closing snapshot.
TIE_ROWS = [
	("Branch Cash", "branch", "cash", "&is_return=0"),
	("Branch Credit (Card)", "branch", "credit", "&is_return=0"),
	("Call Center Vodafone", "cc", "vodafone", "&pos_profile=Call Center"),
	("Call Center Instapay", "cc", "instapay", "&pos_profile=Call Center"),
	("Call Center Cash (Collected)", "cc", "cash", "&pos_profile=Call Center"),
	("Call Center Credit (Card)", "cc", "credit", "&pos_profile=Call Center"),
	("Talabat Cash", "talabat", "cash", "&custom_order_type=Talabat"),
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


def _post_close_payments(shift):
	"""Cash/card tagged to this shift but recorded after its count was submitted.

	The closing snapshot cannot contain these, so they read as a shortage on the
	drawer even though the money is accounted for. Uses `creation` (not posting_date)
	because that is when the collection was actually keyed in.
	"""
	if not shift.cashier_shift_closing or not shift.pos_opening_shift:
		return []
	closed_at = frappe.db.get_value("POS Cashier Shift Closing", shift.cashier_shift_closing, "modified")
	if not closed_at:
		return []
	return frappe.get_all(
		"Payment Entry",
		filters={
			"docstatus": 1,
			"payment_type": "Receive",
			"reference_no": shift.pos_opening_shift,
			"creation": [">", closed_at],
		},
		fields=["name", "mode_of_payment", "paid_amount", "creation"],
	)


def _unassigned_payments(business_day):
	"""Collections against this day's invoices that carry no shift reference.

	`get_payments_entries()` matches strictly on reference_no = opening shift, so a
	Payment Entry raised outside the POS never reaches any closing — on any day.
	"""
	return frappe.db.sql(
		"""
		SELECT pe.name, pe.mode_of_payment, per.allocated_amount AS paid_amount, pe.creation, si.pos_profile
		FROM `tabPayment Entry Reference` per
		JOIN `tabPayment Entry` pe ON pe.name = per.parent
		JOIN `tabSales Invoice` si ON si.name = per.reference_name
		WHERE pe.docstatus = 1
		  AND pe.payment_type = 'Receive'
		  AND per.reference_doctype = 'Sales Invoice'
		  AND si.docstatus = 1
		  AND si.custom_pos_business_day = %(bd)s
		  AND ifnull(pe.reference_no, '') = ''
		""",
		{"bd": business_day},
		as_dict=True,
	)


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

	# ---- Collections the closing snapshot could not contain ----
	# Reported as their own rows rather than folded into Expected: the cashier was
	# measured against the snapshot, so blending these in would hide a real shortage.
	post_close = [(s, p) for s in shifts for p in _post_close_payments(s)]
	unassigned = _unassigned_payments(business_day)
	out = _zero_buckets()
	for s, p in post_close:
		_bucket_payment(out, p, s.pos_profile)
	for p in unassigned:
		_bucket_payment(out, p, p.pos_profile)
	if post_close or unassigned:
		data.append({"item": "— Outside the Closing Snapshot —"})
		for s, p in sorted(post_close, key=lambda r: r[1].creation):
			data.append({
				"item": f"Post-Close: {p.mode_of_payment} · {s.name}",
				"actual": flt(p.paid_amount),
				"note": frappe.utils.format_datetime(p.creation, "HH:mm"),
				"invoices": f'<a href="/app/payment-entry/{p.name}" target="_blank">Review</a>',
			})
		for p in sorted(unassigned, key=lambda r: r.creation):
			data.append({
				"item": f"Unassigned (no shift): {p.mode_of_payment}",
				"actual": flt(p.paid_amount),
				"note": frappe.utils.format_datetime(p.creation, "HH:mm"),
				"invoices": f'<a href="/app/payment-entry/{p.name}" target="_blank">Review</a>',
			})
		outside = sum(flt(p.paid_amount) for _, p in post_close) + sum(flt(p.paid_amount) for p in unassigned)
		data.append({
			"item": "Total Outside Snapshot",
			"actual": outside,
			"count": len(post_close) + len(unassigned),
		})

		# ---- Tie-out: snapshot + outside ----
		# Expected here is every collection the system recorded for the day, so it
		# reconciles against Sales by Working Day. Difference is untouched — it is
		# still the snapshot shortage, so no cashier is charged for money that
		# reached the books after their count.
		data.append({"item": "— Total Collected (Snapshot + Outside) —"})
		for label, bucket, cat, link_extra in TIE_ROWS:
			o = out[bucket][cat]
			if not o:
				continue
			data.append(mrow(f"{label} (incl. Outside)", exp[bucket][cat] + o, act[bucket][cat] + o, link_extra=link_extra))
		data.append(mrow(
			"Grand Total Collected (incl. Outside)",
			sum(exp["all"].values()) + outside,
			sum(act["all"].values()) + outside,
		))

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


def _bucket_payment(buckets, payment, pos_profile):
	"""File a Payment Entry into the same buckets the reconciliation rows use."""
	mode = payment.mode_of_payment
	mtype = frappe.get_cached_value("Mode of Payment", mode, "type") if mode else None
	_add(
		buckets,
		_is_cc(pos_profile),
		"talabat" in (mode or "").lower(),
		_category(mode, mtype),
		flt(payment.paid_amount),
	)


def _add(buckets, is_cc, is_talabat, cat, amount):
	buckets["all"][cat] = flt(buckets["all"].get(cat, 0)) + amount
	if is_talabat:
		buckets["talabat"][cat] = flt(buckets["talabat"].get(cat, 0)) + amount
	elif is_cc:
		buckets["cc"][cat] = flt(buckets["cc"].get(cat, 0)) + amount
	else:
		buckets["branch"][cat] = flt(buckets["branch"].get(cat, 0)) + amount
