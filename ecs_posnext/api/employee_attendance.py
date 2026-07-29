# -*- coding: utf-8 -*-
# Copyright (c) 2024, POS Next and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime

import frappe
from frappe import _

ALLOWED_STATUSES = ("Present", "Absent", "Half Day")

# Attendance has no core Branch field; sites carry it as this custom field
BRANCH_FIELD = "custom_branch"

# Shift Type carries the POS default on a custom field (owned by ecs_heshamrabea),
# so only rely on it where it is actually installed
DEFAULT_SHIFT_FIELD = "custom_default"


def get_shift_window(shift_type: str, on_date: str | datetime.date) -> tuple | None:
	"""Start/end datetimes of ``shift_type`` for a shift that STARTED on ``on_date``.

	An overnight shift (end_time <= start_time, e.g. 09:00 -> 03:00) ends on the
	following day, so its window cannot be expressed as a calendar date. The
	window is widened by the check-in/check-out grace margins, matching HRMS.

	Unlike HRMS's ``get_shift_timings``, the start day is already known here (it is
	the attendance date), so no day resolution is needed. Returns None when the
	Shift Type is unusable.
	"""
	if not shift_type:
		return None

	shift = frappe.get_cached_value(
		"Shift Type",
		shift_type,
		[
			"start_time",
			"end_time",
			"begin_check_in_before_shift_start_time",
			"allow_check_out_after_shift_end_time",
		],
		as_dict=True,
	)
	if not shift or shift.start_time is None or shift.end_time is None:
		return None

	# Time fields come back as timedeltas, so they add straight onto midnight
	day_start = datetime.datetime.combine(frappe.utils.getdate(on_date), datetime.time.min)
	start = day_start + shift.start_time
	end = day_start + shift.end_time
	if shift.end_time <= shift.start_time:
		# Shift spans midnight: it ends on the day after it started
		end += datetime.timedelta(days=1)

	start -= datetime.timedelta(minutes=shift.begin_check_in_before_shift_start_time or 0)
	end += datetime.timedelta(minutes=shift.allow_check_out_after_shift_end_time or 0)

	return start, end


def get_default_shift() -> str | None:
	"""The Shift Type attendance is recorded against.

	Cashiers do not choose a shift: it is whichever Shift Type is flagged with
	DEFAULT_SHIFT_FIELD. That field belongs to another app, so fall back to the
	shift that is running right now, then to the most recently created one.
	"""
	if frappe.get_meta("Shift Type").has_field(DEFAULT_SHIFT_FIELD):
		flagged = frappe.get_all(
			"Shift Type",
			filters={DEFAULT_SHIFT_FIELD: 1},
			pluck="name",
			order_by="creation asc",
		)
		if flagged:
			if len(flagged) > 1:
				frappe.log_error(
					f"Multiple Shift Types are flagged {DEFAULT_SHIFT_FIELD}: "
					f"{', '.join(flagged)}. Using {flagged[0]}.",
					"POS Default Shift Type",
				)
			return flagged[0]

	shift_types = frappe.get_all("Shift Type", pluck="name", order_by="creation desc")
	if not shift_types:
		return None

	# No shift flagged: prefer the one whose window covers now
	now = frappe.utils.now_datetime()
	today = frappe.utils.getdate(now)
	for shift_type in shift_types:
		for on_date in (today, frappe.utils.add_days(today, -1)):
			window = get_shift_window(shift_type, on_date)
			if window and window[0] <= now <= window[1]:
				return shift_type

	return shift_types[0]


@frappe.whitelist()
def get_attendance_date(shift: str | None = None, for_timestamp=None) -> str:
	"""The business date attendance should be stamped with at ``for_timestamp`` (default now).

	An overnight shift's attendance belongs to the day the shift STARTED (the HRMS
	convention), so between midnight and the shift's end this is yesterday - not
	today. Shares get_shift_window with the POS craftsman gate so the two can
	never disagree.
	"""
	moment = frappe.utils.get_datetime(for_timestamp) if for_timestamp else frappe.utils.now_datetime()
	on_date = frappe.utils.getdate(moment)

	previous_day = frappe.utils.add_days(on_date, -1)
	window = get_shift_window(shift, previous_day)
	if window and window[0] <= moment <= window[1]:
		return str(previous_day)

	return str(on_date)


@frappe.whitelist()
def get_shift_types() -> dict:
	"""Return the shift attendance is recorded against, plus its business date.

	The shift is system-determined (see get_default_shift), so the POS shows it
	read-only instead of offering a choice. ``shift_types`` is still returned for
	display and offline caching. ``last_shift`` is kept as an alias of
	``default_shift`` so an older cached POS bundle keeps working.
	"""
	shift_types = frappe.get_list(
		"Shift Type",
		fields=["name", "start_time", "end_time"],
		order_by="creation desc",
	)
	default_shift = get_default_shift()

	return {
		"shift_types": shift_types,
		"default_shift": default_shift,
		"last_shift": default_shift,
		"business_date": get_attendance_date(default_shift),
		"server_date": frappe.utils.today(),
	}


@frappe.whitelist()
def get_employees(date: str | datetime.date, company: str | None = None, branch: str | None = None) -> dict[str, list]:
	"""Fetch active employees for a company/branch and split them into marked/unmarked for the given date."""
	filters = {"status": "Active", "date_of_joining": ["<=", date]}
	if company:
		filters["company"] = company
	if branch:
		filters["branch"] = branch

	employee_list = frappe.get_list(
		"Employee",
		fields=["name as employee", "employee_name"],
		filters=filters,
		order_by="employee_name",
	)
	employee_names = [entry.employee for entry in employee_list]

	attendance_list = []
	if employee_names:
		attendance_filters = {
			"attendance_date": date,
			"docstatus": 1,
			"employee": ["in", employee_names],
		}
		if company:
			attendance_filters["company"] = company

		attendance_list = frappe.get_list(
			"Attendance",
			fields=["employee", "employee_name", "status", "shift"],
			filters=attendance_filters,
			order_by="employee_name",
		)

	marked_employees = {entry.employee for entry in attendance_list}
	unmarked = [entry for entry in employee_list if entry.employee not in marked_employees]

	return {"marked": attendance_list, "unmarked": unmarked}


@frappe.whitelist()
def mark_employee_attendance(
	employee_list: list | str,
	status: str,
	date: str | datetime.date,
	company: str | None = None,
	shift: str | None = None,
	branch: str | None = None,
	op_id: str | None = None,
) -> None:
	"""Mark Present/Absent attendance for the given employees on the given date.

	The shift is not a user choice: whatever the client sends in ``shift`` is
	ignored and the default Shift Type is resolved here, so the window the POS
	craftsman gate derives from the row is always the real one. The parameter is
	kept only so queued offline ops and older POS bundles still post successfully.

	Offline-safe: with an ``op_id`` (from the offline operation queue) a re-sync
	is a no-op, and employees who already have attendance for the date are
	skipped so the operation is idempotent per (employee, date).
	"""
	import json

	from ecs_posnext.api.offline_ops import create_op_sync_record, ensure_op_once

	if status not in ALLOWED_STATUSES:
		frappe.throw(_("Status must be one of {0}").format(", ".join(ALLOWED_STATUSES)))

	if isinstance(employee_list, str):
		employee_list = json.loads(employee_list)

	if not employee_list:
		frappe.throw(_("Please select at least one employee."))

	# Idempotency: this offline op already ran
	if op_id and ensure_op_once(op_id, "attendance"):
		return

	# System-determined, never the value the client sent
	shift = get_default_shift()
	if shift and not frappe.db.exists("Shift Type", shift):
		frappe.throw(_("Shift Type {0} does not exist").format(shift))

	if branch and not frappe.db.exists("Branch", branch):
		frappe.throw(_("Branch {0} does not exist").format(branch))

	attendance_date = frappe.utils.getdate(date)
	# Branch lives on a custom field, so only write it where the field is installed
	branch_field = BRANCH_FIELD if frappe.get_meta("Attendance").has_field(BRANCH_FIELD) else None
	marked_count = 0

	for employee in employee_list:
		# Skip if attendance already exists for this employee/date (dedup on re-sync)
		if frappe.db.exists(
			"Attendance",
			{
				"employee": employee,
				"attendance_date": attendance_date,
				"docstatus": ["<", 2],
			},
		):
			continue

		attendance = frappe.get_doc(
			{
				"doctype": "Attendance",
				"employee": employee,
				"attendance_date": attendance_date,
				"status": status,
				"company": company,
				"shift": shift,
			}
		)
		if branch_field:
			# Prefer the POS profile's branch; fall back to the employee's own branch
			attendance.set(
				branch_field,
				branch or frappe.db.get_value("Employee", employee, "branch"),
			)
		attendance.insert(ignore_permissions=True)
		attendance.submit()
		marked_count += 1

	# Record the offline op so re-syncs short-circuit above
	if op_id:
		create_op_sync_record(op_id, "attendance", "Attendance", f"{marked_count} marked")

	frappe.db.commit()
