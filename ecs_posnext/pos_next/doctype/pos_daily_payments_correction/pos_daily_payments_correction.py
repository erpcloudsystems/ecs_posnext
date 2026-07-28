# Copyright (c) 2026, erpcloud.systems and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift import (
	_get_opening_shift_totals,
)

# Amounts are compared at currency display precision so float noise is not read as drift.
PRECISION = 2

# Mirrors the mode of payment hardcoded in the Actual Amount formula in pos_closing_shift.py.
VISA_MODE_OF_PAYMENT = "بنك CIB فيزا"

FIELD_LABELS = {
	"total_daily_payments": "Total Daily Payments",
	"total_tip": "Total Tip",
	"actual_amount": "Actual Amount",
}


class POSDailyPaymentsCorrection(Document):
	pass


def _guard():
	"""Whitelisted methods bypass DocType permissions, so check the role explicitly."""
	frappe.only_for("System Manager")


def _get_candidates(branch=None, pos_closing_shift=None):
	"""Every submitted closing shift in scope, with Branch resolved via its POS Profile."""
	conditions = ["cs.docstatus = 1"]
	values = {}

	if branch:
		conditions.append("pp.branch = %(branch)s")
		values["branch"] = branch

	if pos_closing_shift:
		conditions.append("cs.name = %(pos_closing_shift)s")
		values["pos_closing_shift"] = pos_closing_shift

	return frappe.db.sql(
		"""
		SELECT cs.name, cs.pos_profile, cs.pos_opening_shift, cs.period_start_date,
		       pp.branch, cs.grand_total,
		       cs.total_daily_payments, cs.total_tip, cs.actual_amount
		FROM `tabPOS Closing Shift` cs
		LEFT JOIN `tabPOS Profile` pp ON pp.name = cs.pos_profile
		WHERE {conditions}
		ORDER BY cs.period_start_date DESC
		""".format(conditions=" AND ".join(conditions)),
		values,
		as_dict=True,
	)


def _get_visa_amounts(names):
	"""Visa portion per closing shift, on the same basis as the Actual Amount formula."""
	if not names:
		return {}

	rows = frappe.db.sql(
		"""
		SELECT parent, COALESCE(SUM(COALESCE(expected_amount, 0) - COALESCE(opening_amount, 0)), 0) AS visa
		FROM `tabPOS Closing Shift Detail`
		WHERE parenttype = 'POS Closing Shift'
		  AND mode_of_payment = %(mop)s
		  AND parent IN %(names)s
		GROUP BY parent
		""",
		{"mop": VISA_MODE_OF_PAYMENT, "names": names},
		as_dict=True,
	)

	return {r.parent: flt(r.visa) for r in rows}


def _evaluate(candidate, visa):
	"""Return a correction row for `candidate`, or None if it needs no correction.

	A shift qualifies on a wrong Total Daily Payments or a wrong Total Tip only.
	Actual Amount is derived from those two, so it is always recalculated from the
	corrected values rather than being a reason to correct a shift on its own.
	"""
	totals = _get_opening_shift_totals(candidate.pos_opening_shift)

	stored_daily = flt(candidate.total_daily_payments, PRECISION)
	correct_daily = flt(totals["total_daily_payments"], PRECISION)
	stored_tip = flt(candidate.total_tip, PRECISION)
	correct_tip = flt(totals["total_tip"], PRECISION)
	stored_actual = flt(candidate.actual_amount, PRECISION)

	changes = []
	if correct_daily != stored_daily:
		changes.append("total_daily_payments")
	if correct_tip != stored_tip:
		changes.append("total_tip")

	if not changes:
		return None

	correct_actual = flt(
		flt(candidate.grand_total) - flt(visa) - correct_daily - correct_tip, PRECISION
	)

	if correct_actual != stored_actual:
		changes.append("actual_amount")

	return {
		"pos_closing_shift": candidate.name,
		"branch": candidate.branch,
		"pos_profile": candidate.pos_profile,
		"period_start_date": candidate.period_start_date,
		"fields_to_update": ", ".join(_(FIELD_LABELS[f]) for f in changes),
		"changes": changes,
		"stored_total_daily_payments": stored_daily,
		"correct_total_daily_payments": correct_daily,
		"difference": flt(correct_daily - stored_daily, PRECISION),
		"stored_total_tip": stored_tip,
		"correct_total_tip": correct_tip,
		"tip_difference": flt(correct_tip - stored_tip, PRECISION),
		"stored_actual_amount": stored_actual,
		"correct_actual_amount": correct_actual,
	}


def _get_drifted_shifts(branch=None, pos_closing_shift=None):
	candidates = _get_candidates(branch=branch, pos_closing_shift=pos_closing_shift)
	visa_amounts = _get_visa_amounts([c.name for c in candidates])

	rows = []
	for candidate in candidates:
		row = _evaluate(candidate, visa_amounts.get(candidate.name, 0.0))
		if row:
			rows.append(row)
	return rows


@frappe.whitelist()
def get_problem_shifts(branch=None, pos_closing_shift=None):
	"""Closing shifts with a wrong stored Total Daily Payments or Total Tip."""
	_guard()
	return _get_drifted_shifts(branch=branch, pos_closing_shift=pos_closing_shift)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def problem_shift_query(doctype, txt, searchfield, start, page_len, filters):
	"""Link field query that only offers closing shifts needing a correction."""
	_guard()

	rows = _get_drifted_shifts(branch=(filters or {}).get("branch"))

	if txt:
		needle = txt.lower()
		rows = [r for r in rows if needle in (r["pos_closing_shift"] or "").lower()]

	start, page_len = cint(start), cint(page_len) or 20

	return [
		[
			r["pos_closing_shift"],
			"{branch} | {fields}".format(
				branch=r["branch"] or _("No Branch"), fields=r["fields_to_update"]
			),
		]
		for r in rows[start : start + page_len]
	]


@frappe.whitelist()
def apply_corrections(shifts):
	"""Write the corrected totals onto the given closing shifts.

	`shifts` carries only the selection; every amount is recomputed here so a
	tampered or stale client payload can never decide what gets written.
	"""
	_guard()

	if isinstance(shifts, str):
		shifts = json.loads(shifts)

	names = [
		row.get("pos_closing_shift")
		for row in (shifts or [])
		if cint(row.get("apply")) and row.get("pos_closing_shift")
	]

	if not names:
		frappe.throw(_("Select at least one POS Closing Shift to correct."))

	updated, skipped = [], []

	for name in names:
		candidates = _get_candidates(pos_closing_shift=name)

		if not candidates:
			skipped.append(name)
			continue

		row = _evaluate(candidates[0], _get_visa_amounts([name]).get(name, 0.0))

		if not row:
			skipped.append(name)
			continue

		doc = frappe.get_doc("POS Closing Shift", name)
		messages = []

		for field in row["changes"]:
			stored, correct = _values_for(row, field)
			# db_set keeps `modified` untouched so the original submission trail
			# survives; the change is recorded as a comment instead.
			doc.db_set(field, correct, update_modified=False)
			messages.append(
				_("{0} corrected from {1} to {2}").format(_(FIELD_LABELS[field]), stored, correct)
			)

		doc.add_comment(
			"Comment",
			text=_("Applied via POS Daily Payments Correction") + ": " + "; ".join(messages) + ".",
		)
		updated.append(row)

	return {"updated": updated, "skipped": skipped}


def _values_for(row, field):
	if field == "total_daily_payments":
		return row["stored_total_daily_payments"], row["correct_total_daily_payments"]
	if field == "total_tip":
		return row["stored_total_tip"], row["correct_total_tip"]
	return row["stored_actual_amount"], row["correct_actual_amount"]
