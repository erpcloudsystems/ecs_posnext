# -*- coding: utf-8 -*-
# Copyright (c) 2024, POS Next and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime

import frappe
from frappe import _

ALLOWED_STATUSES = ("Present", "Absent", "Half Day")


@frappe.whitelist()
def get_shift_types() -> dict:
	"""Return the available Shift Types along with the last one created.

	Mirrors the shift selection of HR's Employee Attendance Tool so attendance
	marked from POS carries the same shift information. Shift Type is not
	company-scoped, so every shift is returned.
	"""
	shift_types = frappe.get_list(
		"Shift Type",
		fields=["name", "start_time", "end_time"],
		order_by="creation desc",
	)

	# "Last" shift type = the most recently created one, used as the default selection
	last_shift = shift_types[0].name if shift_types else None

	return {"shift_types": shift_types, "last_shift": last_shift}


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
	op_id: str | None = None,
) -> None:
	"""Mark Present/Absent attendance for the given employees on the given date.

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

	if shift and not frappe.db.exists("Shift Type", shift):
		frappe.throw(_("Shift Type {0} does not exist").format(shift))

	attendance_date = frappe.utils.getdate(date)
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
		attendance.insert(ignore_permissions=True)
		attendance.submit()
		marked_count += 1

	# Record the offline op so re-syncs short-circuit above
	if op_id:
		create_op_sync_record(op_id, "attendance", "Attendance", f"{marked_count} marked")

	frappe.db.commit()
