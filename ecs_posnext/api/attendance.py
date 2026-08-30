# -*- coding: utf-8 -*-
# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, nowdate


@frappe.whitelist()
def get_attendance(pos_shift):
	"""Get the Pos Attendance entry count for a given POS Opening Shift"""
	if not pos_shift:
		return {"name": None, "number_of_entries": 0}

	name = frappe.db.get_value("Pos Attendance", {"pos_shift": pos_shift})
	if not name:
		return {"name": None, "number_of_entries": 0}

	number_of_entries = frappe.db.get_value("Pos Attendance", name, "number_of_entries")
	return {"name": name, "number_of_entries": cint(number_of_entries)}


@frappe.whitelist()
def save_attendance(pos_shift, number_of_entries):
	"""Create or update the Pos Attendance entry for a given POS Opening Shift"""
	number_of_entries = cint(number_of_entries)

	existing_name = frappe.db.get_value("Pos Attendance", {"pos_shift": pos_shift})

	if existing_name:
		doc = frappe.get_doc("Pos Attendance", existing_name)
		doc.number_of_entries = number_of_entries
		doc.save(ignore_permissions=True)
	else:
		shift = frappe.get_doc("POS Opening Shift", pos_shift)
		doc = frappe.get_doc(
			{
				"doctype": "Pos Attendance",
				"pos_shift": pos_shift,
				"pos_profile": shift.pos_profile,
				"branch": frappe.db.get_value("POS Profile", shift.pos_profile, "dimension_branch"),
				"date": nowdate(),
				"number_of_entries": number_of_entries,
			}
		)
		doc.insert(ignore_permissions=True)

	return {"name": doc.name, "number_of_entries": doc.number_of_entries}
