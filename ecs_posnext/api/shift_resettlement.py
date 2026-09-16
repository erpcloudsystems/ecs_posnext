# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Re-settle a POS Business Day whose collections landed on already-counted shifts.

POS collection screens send the shift as `reference_no` from CLIENT state, so a terminal
whose page was loaded before a handover keeps sending the PREVIOUS cashier's shift. Cash
collected after that shift was counted gets booked onto it, and nothing ever recomputes
it: `compute_cash_figures` runs only at count time, and the drawer that physically holds
the cash filters strictly by `reference_no` and so never sees it. The money ends up in
no reconciliation at all.

`redirect_collection_from_closed_shift` (api/cashier_shift.py) closes the hole for NEW
collections. This module repairs the ones already booked, by re-pointing each collection
at the shift that was genuinely open when the money was taken and recomputing the day's
closings from the same helper the original closing used.

Nothing here touches accounting: `reference_no` and the `custom_pos_*` links are
descriptive fields with no GL effect, and a collection is only ever moved between shifts,
never between days.
"""

import frappe
from frappe import _
from frappe.utils import flt, fmt_money

from ecs_posnext.api.business_day import log_pos_event
from ecs_posnext.api.cashier_shift import compute_cash_figures

# Figures recomputed onto a closing. Mirrors POSCashierShiftClosing.calculate_reconciliation.
_RECOMPUTED_FIELDS = (
	"cash_sales",
	"call_center_cash_collected",
	"cash_refunds",
	"expected_cash",
	"difference",
	"shortage",
	"overage",
	"expected_credit",
	"credit_difference",
)


def shift_open_at(pos_profile, at_datetime):
	"""The POS Opening Shift that was taking money on a profile at a given moment.

	A shift qualifies if it started before that moment and was still uncounted then —
	either it has no closing at all, or its closing was submitted afterwards. The most
	recently started match wins, so a handover resolves to the incoming cashier.
	"""
	rows = frappe.db.sql(
		"""
		SELECT o.name
		FROM `tabPOS Opening Shift` o
		LEFT JOIN `tabPOS Cashier Shift Closing` c
		       ON c.pos_cashier_shift IN (
		              SELECT s.name FROM `tabPOS Cashier Shift` s WHERE s.pos_opening_shift = o.name
		          )
		      AND c.docstatus = 1
		WHERE o.pos_profile = %(profile)s
		  AND o.docstatus = 1
		  AND o.period_start_date <= %(at)s
		  AND (c.name IS NULL OR c.modified > %(at)s)
		ORDER BY o.period_start_date DESC
		LIMIT 1
		""",
		{"profile": pos_profile, "at": at_datetime},
		as_dict=True,
	)
	return rows[0].name if rows else None


def find_misallocated_collections(business_day):
	"""Collections booked onto a shift of this day after that shift's closing was submitted.

	Each row carries the shift it should have landed on, so the caller can both report and
	repair from one pass.
	"""
	found = []
	for s in frappe.get_all(
		"POS Cashier Shift",
		filters={"pos_business_day": business_day},
		fields=["name", "pos_opening_shift", "cashier_user", "cashier_shift_closing", "pos_profile"],
	):
		if not s.pos_opening_shift or not s.cashier_shift_closing:
			continue
		closing = frappe.db.get_value(
			"POS Cashier Shift Closing", s.cashier_shift_closing, ["name", "docstatus", "modified"], as_dict=True
		)
		if not closing or closing.docstatus != 1:
			continue

		for pe in frappe.get_all(
			"Payment Entry",
			filters={
				"reference_no": s.pos_opening_shift,
				"docstatus": 1,
				"payment_type": "Receive",
				"creation": [">", closing.modified],
			},
			fields=["name", "paid_amount", "mode_of_payment", "creation", "owner"],
			order_by="creation",
		):
			correct = shift_open_at(s.pos_profile, pe.creation)
			found.append(
				frappe._dict(
					{
						"payment_entry": pe.name,
						"amount": flt(pe.paid_amount),
						"mode_of_payment": pe.mode_of_payment,
						"collected_at": pe.creation,
						"collected_by": pe.owner,
						"booked_on": s.pos_opening_shift,
						"booked_closing": closing.name,
						"closed_at": closing.modified,
						"correct_shift": correct,
						"pos_profile": s.pos_profile,
					}
				)
			)
	return found


def _recompute_closing(closing_name):
	"""Recompute a submitted closing's figures from the shift as it stands now.

	Returns (current, recomputed) dicts of the fields in _RECOMPUTED_FIELDS. Reuses
	compute_cash_figures — the very helper the original closing was built from — so the
	repair cannot drift from the live calculation.
	"""
	c = frappe.get_doc("POS Cashier Shift Closing", closing_name)
	opening = frappe.db.get_value("POS Cashier Shift", c.pos_cashier_shift, "pos_opening_shift")
	fig = compute_cash_figures(opening)

	expected_cash = (
		flt(fig.opening_cash) + flt(fig.cash_sales) + flt(fig.call_center_cash_collected) - flt(fig.cash_refunds)
	)
	difference = flt(c.actual_counted_cash) - expected_cash

	expected_credit = 0.0
	for row in fig.payment_reconciliation:
		if frappe.get_cached_value("Mode of Payment", row["mode_of_payment"], "type") != "Cash":
			expected_credit += flt(row["expected_amount"])

	new = {
		"cash_sales": flt(fig.cash_sales),
		"call_center_cash_collected": flt(fig.call_center_cash_collected),
		"cash_refunds": flt(fig.cash_refunds),
		"expected_cash": expected_cash,
		"difference": difference,
		"shortage": abs(difference) if difference < 0 else 0,
		"overage": difference if difference > 0 else 0,
		"expected_credit": expected_credit,
		"credit_difference": flt(c.actual_credit) - expected_credit,
	}
	current = {f: flt(c.get(f)) for f in _RECOMPUTED_FIELDS}
	return c, current, new


def _apply_closing_figures(closing_doc, new, audit_note):
	"""Write recomputed figures onto a submitted closing.

	Direct db writes: the doctype declares no allow_on_submit fields, so the document
	layer would refuse. update_modified is left at its default here so the correction is
	visible in the document's timeline — unlike the Payment Entry re-pointing, where the
	original collection time is evidence and must be preserved.
	"""
	frappe.db.set_value("POS Cashier Shift Closing", closing_doc.name, new)

	# Keep the cash row of the per-mode reconciliation consistent with the new figures.
	for row in closing_doc.payment_reconciliation:
		if frappe.get_cached_value("Mode of Payment", row.mode_of_payment, "type") != "Cash":
			continue
		frappe.db.set_value(
			"POS Closing Shift Detail",
			row.name,
			{
				"expected_amount": new["expected_cash"],
				"closing_amount": flt(closing_doc.actual_counted_cash),
				"difference": new["difference"],
			},
			update_modified=False,
		)

	# approved_by / approval_datetime are deliberately left untouched: approve_difference
	# calls doc.save(), which cannot run on a submitted document here, so clearing them
	# would create a state no one can action from the UI. The note records that the
	# standing approval predates this correction.
	reason = (closing_doc.difference_reason or "").rstrip()
	frappe.db.set_value(
		"POS Cashier Shift Closing",
		closing_doc.name,
		"difference_reason",
		(reason + "\n" + audit_note).strip(),
		update_modified=False,
	)


def resettle_business_day(business_day, dry_run=True):
	"""Repair one POS Business Day. Prints a full before/after report.

	dry_run=True (the default) leaves the database untouched — run it first and check the
	report against the day's expected figures before applying.

	A dry run takes the SAME code path as a real one and rolls the transaction back at the
	end, rather than skipping the writes. Skipping them would recompute the closings from
	collections that had not been moved yet, so the preview would report the opposite of
	what applying does — a preview that cannot be trusted is worse than none.
	"""
	dry_run = frappe.parse_json(dry_run) if isinstance(dry_run, str) else dry_run
	bd = frappe.get_doc("POS Business Day", business_day)
	out = []
	mode = "DRY RUN — nothing will be written" if dry_run else "APPLYING CHANGES"
	out.append("=" * 78)
	out.append(f"Re-settle {business_day} | {bd.pos_profile} | {bd.business_date} | status={bd.status}")
	out.append(mode)
	out.append("=" * 78)

	misallocated = find_misallocated_collections(business_day)
	if not misallocated:
		out.append("\nNo misallocated collections on this day — nothing to re-settle.")
		print("\n".join(out))
		return {"misallocated": [], "closings": []}

	out.append(f"\n--- {len(misallocated)} misallocated collection(s), total {sum(m.amount for m in misallocated):,.2f} ---")
	for m in misallocated:
		out.append(f"  {m.payment_entry}  {m.amount:>10,.2f}  {m.mode_of_payment}")
		out.append(f"      collected {m.collected_at} by {m.collected_by}")
		out.append(f"      booked on {m.booked_on} (counted by {m.booked_closing} at {m.closed_at})")
		out.append(f"      belongs to {m.correct_shift or 'UNRESOLVED — skipped'}")

	# 1) Re-point each collection at the shift that was actually open when it was taken.
	moved = []
	for m in misallocated:
		if not m.correct_shift or m.correct_shift == m.booked_on:
			continue
		cs = frappe.db.get_value(
			"POS Cashier Shift", {"pos_opening_shift": m.correct_shift}, ["name", "pos_business_day"], as_dict=True
		)
		if not cs:
			out.append(f"\n  !! {m.payment_entry}: no POS Cashier Shift for {m.correct_shift} — skipped")
			continue
		m.target_cashier_shift = cs.name
		m.target_business_day = cs.pos_business_day
		moved.append(m)
		frappe.db.set_value(
			"Payment Entry",
			m.payment_entry,
			{
				"reference_no": m.correct_shift,
				"custom_pos_cashier_shift": cs.name,
				"custom_pos_business_day": cs.pos_business_day,
			},
			update_modified=False,  # the original collection time is evidence — preserve it
		)
		log_pos_event(
			action="Override",
			reference_doctype="Payment Entry",
			reference_name=m.payment_entry,
			pos_profile=m.pos_profile,
			pos_business_day=cs.pos_business_day,
			old_value=m.booked_on,
			new_value=m.correct_shift,
			reason=_(
				"Re-settlement: {0} was collected at {1} but booked on {2}, already counted by {3}. "
				"Re-pointed at the shift open at collection time."
			).format(fmt_money(m.amount), m.collected_at, m.booked_on, m.booked_closing),
		)

	# 2) Recompute every closing of the day — both the one that lost money and the one
	#    that gains it.
	closings = frappe.get_all(
		"POS Cashier Shift Closing",
		filters={"pos_business_day": business_day, "docstatus": 1},
		fields=["name"],
		order_by="creation",
	)
	out.append("\n--- closings ---")
	changed = []
	for row in closings:
		doc, current, new = _recompute_closing(row.name)
		deltas = {f: new[f] - current[f] for f in _RECOMPUTED_FIELDS if abs(new[f] - current[f]) >= 0.005}
		cashier = doc.cashier or ""
		if not deltas:
			out.append(f"\n  {row.name} ({cashier}): unchanged")
			continue
		out.append(f"\n  {row.name} ({cashier}):")
		for f in _RECOMPUTED_FIELDS:
			if f in deltas:
				out.append(f"      {f:<28} {current[f]:>12,.2f}  ->  {new[f]:>12,.2f}")
		changed.append((doc, current, new))

		note = _("[Re-settled {0}] expected cash {1} -> {2}, difference {3} -> {4}. Approval above predates this correction.").format(
			frappe.utils.now_datetime().strftime("%Y-%m-%d %H:%M"),
			fmt_money(current["expected_cash"]),
			fmt_money(new["expected_cash"]),
			fmt_money(current["difference"]),
			fmt_money(new["difference"]),
		)
		_apply_closing_figures(doc, new, note)
		log_pos_event(
			action="Overage" if new["overage"] else ("Shortage" if new["shortage"] else "Closing Shift"),
			reference_doctype="POS Cashier Shift Closing",
			reference_name=doc.name,
			pos_profile=doc.pos_profile,
			pos_business_day=business_day,
			old_value=current["difference"],
			new_value=new["difference"],
			reason=note,
		)

	# 3) Refresh the day summary so reports follow the corrected closings.
	bd.flags.ignore_permissions = True
	bd.refresh_summary(save=True)

	out.append("\n" + "-" * 78)
	out.append(
		f"{'Would move' if dry_run else 'Moved'} {len(moved)} collection(s) "
		f"totalling {sum(m.amount for m in moved):,.2f}; "
		f"{'would update' if dry_run else 'updated'} {len(changed)} closing(s)."
	)

	if dry_run:
		frappe.db.rollback()
		out.append("ROLLED BACK — nothing was written. Re-run with dry_run=False to apply.")
	else:
		frappe.db.commit()
		out.append("COMMITTED — Business Day summary refreshed.")
	print("\n".join(out))
	return {
		"misallocated": [dict(m) for m in misallocated],
		"moved": [m.payment_entry for m in moved],
		"closings_changed": [d.name for d, _c, _n in changed],
		"dry_run": bool(dry_run),
	}
