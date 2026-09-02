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
	following day, so its window cannot be expressed as a calendar date.

	The window is the shift's own start and end only. HRMS widens the equivalent
	window by begin_check_in_before_shift_start_time / allow_check_out_after_shift_
	end_time, but those are check-in margins: a sales person should be selectable
	for the shift itself, not for an hour past its end.

	Unlike HRMS's ``get_shift_timings``, the start day is already known here (it is
	the attendance date), so no day resolution is needed. Returns None when the
	Shift Type is unusable.
	"""
	if not shift_type:
		return None

	shift = frappe.get_cached_value(
		"Shift Type", shift_type, ["start_time", "end_time"], as_dict=True
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
			# name/late_entry/early_exit let the POS decide whether a marked row can
			# still be converted to Half Day, and which direction it came from
			fields=[
				"name",
				"employee",
				"employee_name",
				"status",
				"shift",
				"late_entry",
				"early_exit",
			],
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


# Correcting an already-marked day cancels a submitted Attendance record, so
# unlike plain marking it is restricted. Cashiers do it from the POS; System
# Manager is kept so the same correction is available from the desk.
HALF_DAY_ROLES = ("POSNext Cashier", "System Manager")


def _check_half_day_permitted():
	"""Whitelisted methods bypass DocType permissions, so check the role explicitly."""
	if not set(HALF_DAY_ROLES) & set(frappe.get_roles()):
		frappe.throw(
			_("Only {0} can change a marked attendance to Half Day.").format(
				_(HALF_DAY_ROLES[0])
			),
			frappe.PermissionError,
		)


# Why an already-marked day turns into a Half Day, mapped to the status the
# existing Attendance record must currently hold for that reason to make sense.
HALF_DAY_REASONS = {
	# Marked Present, then left before the shift ended: a full day is no longer true
	"early_exit": "Present",
	# Marked Absent, then turned up after the shift started: not a full absence after all
	"late_entry": "Absent",
}


def _find_submitted_attendance(employee: str, attendance_date, company: str | None = None) -> str | None:
	"""Name of the submitted Attendance for ``employee`` on ``attendance_date``.

	Newest first, because an amend chain leaves the live record as the most
	recently created one.
	"""
	filters = {
		"employee": employee,
		"attendance_date": attendance_date,
		"docstatus": 1,
	}
	if company:
		filters["company"] = company

	rows = frappe.get_list(
		"Attendance",
		filters=filters,
		fields=["name"],
		order_by="creation desc",
		limit=1,
	)
	return rows[0].name if rows else None


@frappe.whitelist()
def convert_attendance_to_half_day(
	employee_list: list | str,
	date: str | datetime.date,
	reason: str,
	company: str | None = None,
	branch: str | None = None,
	op_id: str | None = None,
) -> dict:
	"""Turn an already-marked Present/Absent day into a Half Day.

	Two cases, both of which surface only once attendance exists for the day:

	* ``early_exit``  - the sales person was marked Present and then left early.
	* ``late_entry``  - the sales person was marked Absent and then turned up late.

	Attendance.status is not ``allow_on_submit``, so a submitted record cannot be
	edited in place. The record is therefore cancelled and re-created as an
	amendment: the Half Day row links back to the original through
	``amended_from``, so the correction keeps an audit trail instead of silently
	overwriting HR data. ``late_entry`` / ``early_exit`` are stamped on the new
	row - they are what tells the POS craftsman gate apart a sales person who has
	just arrived from one who has already gone home, since both read "Half Day".

	Employees whose record does not match ``reason`` are skipped and reported
	rather than throwing, so one stale row cannot abort the whole batch.

	Offline-safe: a re-synced ``op_id`` is a no-op, and an employee already on the
	expected Half Day is skipped, making the operation idempotent per
	(employee, date, reason).

	Restricted to HALF_DAY_ROLES: cancelling a submitted HR record is a bigger
	step than marking an unmarked day, which stays open to any POS user.
	"""
	import json

	from ecs_posnext.api.offline_ops import create_op_sync_record, ensure_op_once

	_check_half_day_permitted()

	if reason not in HALF_DAY_REASONS:
		frappe.throw(
			_("Reason must be one of {0}").format(", ".join(sorted(HALF_DAY_REASONS)))
		)

	if isinstance(employee_list, str):
		employee_list = json.loads(employee_list)

	if not employee_list:
		frappe.throw(_("Please select at least one employee."))

	# Idempotency: this offline op already ran
	if op_id and ensure_op_once(op_id, "attendance_half_day"):
		return {"updated": [], "skipped": [], "already_synced": True}

	expected_status = HALF_DAY_REASONS[reason]
	attendance_date = frappe.utils.getdate(date)
	branch_field = BRANCH_FIELD if frappe.get_meta("Attendance").has_field(BRANCH_FIELD) else None

	updated, skipped = [], []

	for employee in employee_list:
		name = _find_submitted_attendance(employee, attendance_date, company)
		if not name:
			skipped.append({"employee": employee, "message": _("No submitted attendance for this date")})
			continue

		old = frappe.get_doc("Attendance", name)

		if old.status == "Half Day":
			# Already converted - most likely a re-sync or a double tap
			skipped.append({"employee": employee, "message": _("Already marked Half Day")})
			continue

		if old.status != expected_status:
			skipped.append(
				{
					"employee": employee,
					"message": _("Status is {0}, expected {1}").format(
						_(old.status), _(expected_status)
					),
				}
			)
			continue

		old.flags.ignore_permissions = True
		old.cancel()

		# Amendment rather than a fresh insert: carries in/out times, working hours
		# and site custom fields over, and links back to the cancelled original
		new = frappe.copy_doc(old)
		new.amended_from = old.name
		new.status = "Half Day"
		# Only the flag for this correction is set; the other is cleared so a
		# record cannot end up looking like both a late arrival and an early exit
		new.late_entry = 1 if reason == "late_entry" else 0
		new.early_exit = 1 if reason == "early_exit" else 0
		if branch_field and not new.get(branch_field):
			new.set(
				branch_field,
				branch or frappe.db.get_value("Employee", employee, "branch"),
			)

		new.flags.ignore_permissions = True
		new.insert(ignore_permissions=True)
		new.submit()
		new.add_comment(
			"Comment",
			text=_("Marked Half Day from POS ({0}). Amended from {1}, which was {2}.").format(
				_("left early") if reason == "early_exit" else _("arrived late"),
				old.name,
				_(expected_status),
			),
		)

		updated.append(
			{
				"employee": employee,
				"employee_name": new.employee_name,
				"attendance": new.name,
				"cancelled": old.name,
				"status": new.status,
			}
		)

	# Record the offline op so re-syncs short-circuit above
	if op_id:
		create_op_sync_record(
			op_id, "attendance_half_day", "Attendance", f"{len(updated)} converted"
		)

	frappe.db.commit()

	return {"updated": updated, "skipped": skipped}
