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


class POSDailyPaymentsCorrection(Document):
	pass


def _guard():
	"""Whitelisted methods bypass DocType permissions, so check the role explicitly."""
	frappe.only_for("System Manager")


def _get_candidates(branch=None, pos_closing_shift=None):
	"""Submitted closing shifts that could possibly be wrong.

	A shift can only drift if its opening shift has Daily Payments, or if it
	already stores a non-zero total. Everything else is 0 == 0 and is skipped
	before the per-shift recomputation.
	"""
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
		       pp.branch,
		       cs.total_daily_payments AS stored_total_daily_payments,
		       cs.actual_amount AS stored_actual_amount
		FROM `tabPOS Closing Shift` cs
		LEFT JOIN `tabPOS Profile` pp ON pp.name = cs.pos_profile
		WHERE {conditions}
		  AND (
		    IFNULL(cs.total_daily_payments, 0) != 0
		    OR EXISTS (
		      SELECT 1 FROM `tabDaily Payment` dp
		      WHERE dp.pos_opening_shift = cs.pos_opening_shift AND dp.docstatus = 1
		    )
		  )
		ORDER BY cs.period_start_date DESC
		""".format(conditions=" AND ".join(conditions)),
		values,
		as_dict=True,
	)


def _get_drift(candidate):
	"""Return a correction row for `candidate`, or None if it is already correct."""
	correct = flt(
		_get_opening_shift_totals(candidate.pos_opening_shift)["total_daily_payments"],
		PRECISION,
	)
	stored = flt(candidate.stored_total_daily_payments, PRECISION)

	if correct == stored:
		return None

	difference = flt(correct - stored, PRECISION)

	return {
		"pos_closing_shift": candidate.name,
		"branch": candidate.branch,
		"pos_profile": candidate.pos_profile,
		"period_start_date": candidate.period_start_date,
		"stored_total_daily_payments": stored,
		"correct_total_daily_payments": correct,
		"difference": difference,
		"stored_actual_amount": flt(candidate.stored_actual_amount, PRECISION),
		# Actual Amount is only moved by the Daily Payments difference. Recomputing it
		# from scratch would silently absorb any drift in grand total, visa or tip too.
		"correct_actual_amount": flt(
			flt(candidate.stored_actual_amount, PRECISION) - difference, PRECISION
		),
	}


def _get_drifted_shifts(branch=None, pos_closing_shift=None):
	rows = []
	for candidate in _get_candidates(branch=branch, pos_closing_shift=pos_closing_shift):
		drift = _get_drift(candidate)
		if drift:
			rows.append(drift)
	return rows


@frappe.whitelist()
def get_problem_shifts(branch=None, pos_closing_shift=None):
	"""Closing shifts whose stored Total Daily Payments does not match the recomputed value."""
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
			"{branch} | {stored} → {correct}".format(
				branch=r["branch"] or _("No Branch"),
				stored=r["stored_total_daily_payments"],
				correct=r["correct_total_daily_payments"],
			),
		]
		for r in rows[start : start + page_len]
	]


@frappe.whitelist()
def apply_corrections(shifts, update_actual_amount=1):
	"""Write the corrected totals onto the given closing shifts.

	`shifts` carries only the selection; every amount is recomputed here so a
	tampered or stale client payload can never decide what gets written.
	"""
	_guard()

	if isinstance(shifts, str):
		shifts = json.loads(shifts)

	update_actual_amount = cint(update_actual_amount)

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
		drift = _get_drift(candidates[0]) if candidates else None

		if not drift:
			skipped.append(name)
			continue

		doc = frappe.get_doc("POS Closing Shift", name)
		# db_set keeps `modified` untouched so the original submission trail survives;
		# the change is recorded as a comment on the document instead.
		doc.db_set(
			"total_daily_payments",
			drift["correct_total_daily_payments"],
			update_modified=False,
		)

		message = _("Total Daily Payments corrected from {0} to {1}").format(
			drift["stored_total_daily_payments"], drift["correct_total_daily_payments"]
		)

		if update_actual_amount:
			doc.db_set(
				"actual_amount", drift["correct_actual_amount"], update_modified=False
			)
			message += ". " + _("Actual Amount corrected from {0} to {1}").format(
				drift["stored_actual_amount"], drift["correct_actual_amount"]
			)

		doc.add_comment(
			"Comment",
			text=message + ". " + _("Applied via POS Daily Payments Correction."),
		)
		updated.append(drift)

	return {"updated": updated, "skipped": skipped}
