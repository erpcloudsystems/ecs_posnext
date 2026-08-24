"""Business Day Closing Report.

Per POS Business Day: expected (from the day's orders) vs actual (from the shift
closings' per-mode reconciliation), broken down by Branch / Call Center and payment
mode, plus paid/returned/void order counts and a shift-status summary. Each metric row
links to the underlying Sales Invoices for review.

Expected/Actual come from the closing snapshot, which is frozen when the cashier
submits their count. Three kinds of collection can therefore land outside it, and all
are reported separately at the bottom so the day still ties out:
  * post-close COD — a Payment Entry tagged to the shift but created after the count;
  * post-close invoice payment — a Sales Invoice Payment on an invoice tied to the
    shift but created after the count (e.g. a POS invoice keyed in / synced late);
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
		{"label": "Change Given", "fieldname": "change", "fieldtype": "Currency", "width": 110},
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
	("Talabat Credit (Card)", "talabat", "credit", "&custom_order_type=Talabat"),
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


def _post_close_sip_payments(shift):
	"""Sales Invoice Payment rows on invoices tied to this shift but recorded after its
	count was submitted (e.g. a POS invoice keyed in / synced late).

	`_post_close_payments` catches this for Payment Entries; a payment entered directly
	on a Sales Invoice needs the same catch-up, or it silently drops out of the closing
	snapshot even though the money is real (see Sales by Working Day, which always sums
	Sales Invoice Payment live and so never misses it).
	"""
	if not shift.cashier_shift_closing or not shift.pos_opening_shift:
		return []
	closed_at = frappe.db.get_value("POS Cashier Shift Closing", shift.cashier_shift_closing, "modified")
	if not closed_at:
		return []
	return frappe.db.sql(
		"""
		SELECT sip.mode_of_payment, sip.amount AS paid_amount, si.name AS invoice, si.creation
		FROM `tabSales Invoice Payment` sip
		JOIN `tabSales Invoice` si ON si.name = sip.parent
		WHERE si.docstatus = 1
		  AND si.posa_pos_opening_shift = %(shift)s
		  AND si.creation > %(closed_at)s
		""",
		{"shift": shift.pos_opening_shift, "closed_at": closed_at},
		as_dict=True,
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

	# Per-mode Expected vs Actual — shown exactly as each Mode of Payment, no grouping.
	exp = {}   # mode -> expected
	act = {}   # mode -> actual (counted)

	def add(store, mode, amount):
		if not mode:
			return
		store[mode] = flt(store.get(mode, 0)) + flt(amount)

	# 1) Shift reconciliation (branch shifts; also any Call Center shift on this day).
	for s in shifts:
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
			add(exp, mode, row["expected_amount"] if isinstance(row, dict) else row.expected_amount)
			add(act, mode, row["closing_amount"] if isinstance(row, dict) else row.closing_amount)

	# 2) Call Center invoices route to this branch's day but have NO cashier shift, so
	# their payments never appear in a reconciliation — add them directly (Expected =
	# Actual, a Call Center shift has no drawer to count). Returns are included (their
	# Sales Invoice Payment amount is already negative) so a refunded CC order nets out
	# against its original sale instead of being counted as a shortage-free overage.
	cc_pay = frappe.db.sql(
		"""
		SELECT sip.mode_of_payment AS mop, SUM(sip.amount) AS amt
		FROM `tabSales Invoice Payment` sip
		JOIN `tabSales Invoice` si ON si.name = sip.parent
		WHERE si.custom_pos_business_day = %(bd)s AND si.docstatus = 1
		  AND LOWER(IFNULL(si.pos_profile, '')) LIKE %(cc)s
		GROUP BY sip.mode_of_payment
		""",
		{"bd": business_day, "cc": "%call center%"},
		as_dict=True,
	)
	for r in cc_pay:
		add(exp, r.mop, r.amt)
		add(act, r.mop, r.amt)

	# A Call Center Payment Entry can carry a *branch* shift's opening-shift reference
	# (e.g. the drawer that delivered/collected a call-center COD order) — that money is
	# already inside that shift's own snapshot or `_post_close_payments`, so re-adding it
	# here by pos_profile alone double-counts it. Only a reference_no that matches NO
	# branch shift at all (a pure Call Center opening shift, never tracked as a POS
	# Cashier Shift) is genuinely invisible everywhere else and belongs here.
	branch_opening_shifts = {s.pos_opening_shift for s in shifts if s.pos_opening_shift}
	cc_conditions = "IFNULL(pe.reference_no, '') != ''"
	cc_params = {"bd": business_day, "cc": "%call center%"}
	if branch_opening_shifts:
		cc_conditions += " AND pe.reference_no NOT IN %(branch_shifts)s"
		cc_params["branch_shifts"] = tuple(branch_opening_shifts)
	cc_payment_entries = frappe.db.sql(
		f"""
		SELECT pe.name, pe.mode_of_payment, per.allocated_amount AS paid_amount, pe.creation
		FROM `tabPayment Entry Reference` per
		JOIN `tabPayment Entry` pe ON pe.name = per.parent
		JOIN `tabSales Invoice` si ON si.name = per.reference_name
		WHERE pe.docstatus = 1
		  AND pe.payment_type = 'Receive'
		  AND per.reference_doctype = 'Sales Invoice'
		  AND si.docstatus = 1
		  AND si.custom_pos_business_day = %(bd)s
		  AND IFNULL(si.is_return, 0) = 0
		  AND LOWER(IFNULL(si.pos_profile, '')) LIKE %(cc)s
		  AND {cc_conditions}
		""",
		cc_params,
		as_dict=True,
	)
	for p in cc_payment_entries:
		add(exp, p.mode_of_payment, p.paid_amount)
		add(act, p.mode_of_payment, p.paid_amount)

	# 3) Collections outside the closing snapshot (post-close + unassigned Payment
	# Entries, and post-close Sales Invoice Payments) — real money; add to both sides so
	# they aren't shown as a false shortage.
	post_close = [(s, p) for s in shifts for p in _post_close_payments(s)]
	post_close_sip = [(s, p) for s in shifts for p in _post_close_sip_payments(s)]
	unassigned = _unassigned_payments(business_day)
	for _s, p in post_close:
		add(exp, p.mode_of_payment, p.paid_amount)
		add(act, p.mode_of_payment, p.paid_amount)
	for _s, p in post_close_sip:
		add(exp, p.mode_of_payment, p.paid_amount)
		add(act, p.mode_of_payment, p.paid_amount)
	for p in unassigned:
		add(exp, p.mode_of_payment, p.paid_amount)
		add(act, p.mode_of_payment, p.paid_amount)

	# ---- Order counts ----
	paid = frappe.db.count("Sales Invoice", {"custom_pos_business_day": business_day, "docstatus": 1, "is_return": 0, "outstanding_amount": ["<=", 0]})
	unpaid = frappe.db.count("Sales Invoice", {"custom_pos_business_day": business_day, "docstatus": 1, "is_return": 0, "outstanding_amount": [">", 0]})
	returned = frappe.db.count("Sales Invoice", {"custom_pos_business_day": business_day, "docstatus": 1, "is_return": 1})
	void = frappe.db.count("Sales Invoice", {"custom_pos_business_day": business_day, "docstatus": 2})

	# ---- Shifts (already fetched above) ----
	closed_shifts = [s for s in shifts if s.status == "Closed" and s.cashier_shift_closing]

	# Cash change handed back to customers, per Mode of Payment — Expected above is
	# already net of this (compute_cash_figures subtracts it), so it's shown here only
	# for visibility/reconciliation against reports that use the raw tendered amount.
	change_map = {
		r.mode_of_payment: flt(r.change_amount)
		for r in frappe.db.sql(
			"""
			SELECT sip.mode_of_payment, SUM(si.change_amount) AS change_amount
			FROM `tabSales Invoice` si
			JOIN `tabSales Invoice Payment` sip ON sip.parent = si.name
			JOIN `tabMode of Payment` mop ON mop.name = sip.mode_of_payment
			WHERE si.custom_pos_business_day = %(bd)s AND si.docstatus = 1
			  AND mop.type = 'Cash' AND IFNULL(si.change_amount, 0) != 0
			GROUP BY sip.mode_of_payment
			""",
			{"bd": business_day},
			as_dict=True,
		)
	}

	def mrow(item, e=None, a=None, count=None, note=None, link_extra="", chg=None):
		row = {"item": item}
		if e is not None or a is not None:
			row["expected"] = flt(e)
			row["actual"] = flt(a)
			row["difference"] = flt(a) - flt(e)
		if chg is not None:
			row["change"] = flt(chg)
		if count is not None:
			row["count"] = count
		if note:
			row["note"] = note
		row["invoices"] = _link(business_day, link_extra)
		return row

	data = []
	data.append({"item": f"Business Day {business_day} ({bd.get('business_date')})", "note": bd.get("status")})
	data.append({"item": f"Shifts: {len(shifts)}  |  Closed: {len(closed_shifts)}", "count": len(shifts)})

	# ---- Payments by Mode (each mode shown as-is, no grouping) ----
	data.append({"item": "— Payments by Mode of Payment —"})
	total_e = total_a = total_chg = 0
	for mode in sorted(set(exp) | set(act), key=lambda m: (m or "").lower()):
		e = flt(exp.get(mode, 0))
		a = flt(act.get(mode, 0))
		if not e and not a:
			continue
		chg = flt(change_map.get(mode, 0))
		data.append(mrow(mode, e, a, chg=chg))
		total_e += e
		total_a += a
		total_chg += chg
	data.append(mrow("Grand Total", total_e, total_a, chg=total_chg))

	# ---- Payment Entries recorded outside the closing snapshot (already folded into
	# the mode totals above; listed here so the day's collections are traceable) ----
	outside = [
		(p.mode_of_payment, flt(p.paid_amount), f"Post-Close · {s.name}", "payment-entry", p.name)
		for s, p in post_close
	] + [
		(p.mode_of_payment, flt(p.paid_amount), f"Post-Close Invoice · {s.name}", "sales-invoice", p.invoice)
		for s, p in post_close_sip
	] + [
		(p.mode_of_payment, flt(p.paid_amount), "Call Center Payment Entry", "payment-entry", p.name)
		for p in cc_payment_entries
	] + [
		(p.mode_of_payment, flt(p.paid_amount), f"Unassigned · {p.pos_profile or ''}", "payment-entry", p.name)
		for p in unassigned
	]
	if outside:
		data.append({"item": "— Collections Outside Closing Snapshot (included in totals above) —"})
		total_outside = 0
		for mode, amount, note, doctype_route, doc_name in outside:
			data.append({
				"item": mode,
				"actual": amount,
				"note": note,
				"invoices": f'<a href="/app/{doctype_route}/{doc_name}" target="_blank">{doc_name}</a>',
			})
			total_outside += amount
		data.append({"item": "Total Outside Snapshot", "actual": flt(total_outside)})

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
