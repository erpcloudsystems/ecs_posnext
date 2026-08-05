# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class POSReportSettings(Document):
	def validate(self):
		self.validate_duplicates()
		self.validate_reports()

	def validate_duplicates(self):
		"""The POS lists one entry per (report, profile), so a repeat would render twice.

		A blank profile means "every profile", so it collides with a profile-specific
		row for the same report too — the cashier would see the report listed twice.
		"""
		seen = {}
		for row in self.reports:
			key = (row.report, row.pos_profile or None)
			if key in seen:
				frappe.throw(
					_("Row #{0}: Report {1} is already listed in row #{2}.").format(
						row.idx, frappe.bold(row.report), seen[key]
					)
				)
			seen[key] = row.idx

			if row.pos_profile and (row.report, None) in seen:
				frappe.throw(
					_(
						"Row #{0}: Report {1} is already listed for all POS Profiles in row #{2}."
					).format(row.idx, frappe.bold(row.report), seen[(row.report, None)])
				)

	def validate_reports(self):
		"""A disabled report cannot be run, so listing it would only dead-end the cashier."""
		for row in self.reports:
			if not row.report:
				continue
			if frappe.db.get_value("Report", row.report, "disabled"):
				frappe.throw(
					_("Row #{0}: Report {1} is disabled and cannot be shown in the POS.").format(
						row.idx, frappe.bold(row.report)
					)
				)
			if not row.icon:
				row.icon = "bar-chart-2"


def get_pos_report_rows(pos_profile: str | None = None) -> list[frappe._dict]:
	"""Enabled rows for ``pos_profile``, in the order the settings list them.

	Rows without a profile apply everywhere. Returns [] when reports are switched
	off globally so callers do not have to special-case the master toggle.
	"""
	settings = frappe.get_cached_doc("POS Report Settings")
	if not cint(settings.enable_reports_in_pos):
		return []

	rows = []
	for row in settings.reports:
		if not cint(row.enabled) or not row.report:
			continue
		if row.pos_profile and pos_profile and row.pos_profile != pos_profile:
			continue
		if row.pos_profile and not pos_profile:
			# Caller did not say which profile it is running for, so a
			# profile-scoped report cannot be shown safely
			continue
		rows.append(
			frappe._dict(
				report=row.report,
				label=row.label or row.report,
				icon=row.icon or "bar-chart-2",
				report_type=row.report_type,
				ref_doctype=row.ref_doctype,
				pos_profile=row.pos_profile,
			)
		)

	return rows
