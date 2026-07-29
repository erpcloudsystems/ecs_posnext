# Copyright (c) 2026, erpcloud.systems and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from ecs_posnext.api.employee_attendance import get_attendance_date, get_default_shift


class POSAttendanceShiftCorrection(Document):
	pass


def _guard():
	"""Whitelisted methods bypass DocType permissions, so check the role explicitly."""
	frappe.only_for("System Manager")


def _get_candidates(from_date=None, to_date=None, only_missing_shift=1, attendance=None):
	"""Submitted Attendance records in scope, oldest first.

	Only submitted records are considered: drafts can be corrected by saving them
	normally, and cancelled records are history.
	"""
	conditions = ["docstatus = 1"]
	values = {}

	if cint(only_missing_shift):
		conditions.append("(shift is null or shift = '')")

	if from_date:
		conditions.append("attendance_date >= %(from_date)s")
		values["from_date"] = from_date

	if to_date:
		conditions.append("attendance_date <= %(to_date)s")
		values["to_date"] = to_date

	if attendance:
		conditions.append("name = %(attendance)s")
		values["attendance"] = attendance

	return frappe.db.sql(
		"""
		SELECT name, employee, employee_name, attendance_date, status, shift, creation
		FROM `tabAttendance`
		WHERE {conditions}
		ORDER BY attendance_date ASC, employee ASC
		""".format(conditions=" AND ".join(conditions)),
		values,
		as_dict=True,
	)


def _evaluate(candidate, target_shift):
	"""Return a correction row for `candidate`, or None if its shift is already right."""
	if not target_shift or candidate.shift == target_shift:
		return None

	return {
		"attendance": candidate.name,
		"employee": candidate.employee,
		"employee_name": candidate.employee_name,
		"attendance_date": candidate.attendance_date,
		"status": candidate.status,
		"current_shift": candidate.shift or _("No Shift"),
		"new_shift": target_shift,
		"created_on": candidate.creation,
		"date_note": _date_note(candidate, target_shift),
	}


def _date_note(candidate, target_shift):
	"""Flag records whose Attendance Date disagrees with when they were created.

	A record entered at 01:00 while a 09:00 -> 03:00 shift was still running belongs
	to the previous day. Those rows are only reported, never rewritten: changing
	Attendance Date could collide with another record for the same employee and day,
	and it would move the record in HR reporting.
	"""
	business_date = get_attendance_date(target_shift, candidate.creation)
	if str(candidate.attendance_date) == business_date:
		return ""

	return _("Created during the {0} shift").format(business_date)


def _get_correctable(from_date=None, to_date=None, only_missing_shift=1, attendance=None):
	target_shift = get_default_shift()
	candidates = _get_candidates(
		from_date=from_date,
		to_date=to_date,
		only_missing_shift=only_missing_shift,
		attendance=attendance,
	)

	rows = []
	for candidate in candidates:
		row = _evaluate(candidate, target_shift)
		if row:
			rows.append(row)
	return rows


@frappe.whitelist()
def get_target_shift():
	"""The Shift Type every corrected record will point at."""
	_guard()
	return get_default_shift()


@frappe.whitelist()
def get_attendance_to_correct(from_date=None, to_date=None, only_missing_shift=1):
	"""Submitted Attendance records that are not on the default Shift Type."""
	_guard()
	return _get_correctable(
		from_date=from_date, to_date=to_date, only_missing_shift=only_missing_shift
	)


@frappe.whitelist()
def apply_corrections(records):
	"""Write the default Shift Type onto the selected Attendance records.

	`records` carries only the selection; the target shift and every row is
	re-resolved here so a tampered or stale client payload can never decide what
	gets written. Attendance Date is never touched.
	"""
	_guard()

	if isinstance(records, str):
		records = json.loads(records)

	names = [
		row.get("attendance")
		for row in (records or [])
		if cint(row.get("apply")) and row.get("attendance")
	]

	if not names:
		frappe.throw(_("Select at least one Attendance record to correct."))

	updated, skipped = [], []

	for name in names:
		rows = _get_correctable(only_missing_shift=0, attendance=name)

		if not rows:
			# Already on the default shift, or no longer submitted
			skipped.append(name)
			continue

		row = rows[0]
		doc = frappe.get_doc("Attendance", name)

		# Shift is not allow_on_submit, so db_set is the only way to correct a
		# submitted record. update_modified=False keeps the original submission
		# trail intact; the change is recorded as a comment instead.
		doc.db_set("shift", row["new_shift"], update_modified=False)
		doc.add_comment(
			"Comment",
			text=_("Applied via POS Attendance Shift Correction: Shift set from {0} to {1}.").format(
				row["current_shift"], row["new_shift"]
			),
		)
		updated.append(row)

	return {"updated": updated, "skipped": skipped}
