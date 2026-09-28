# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import strip


class POSWristband(Document):
	def validate(self):
		self.serial_no = strip(self.serial_no or "")
		if not self.serial_no:
			frappe.throw(_("Wristband Serial No is required"))

		# The unique index is case-sensitive, so "ab12" and "AB12" would both be
		# accepted while the cashier reads them as the same band. Check explicitly.
		duplicate = frappe.db.sql(
			"""
			SELECT name, ticket FROM `tabPOS Wristband`
			WHERE LOWER(serial_no) = LOWER(%(serial_no)s) AND name != %(name)s
			LIMIT 1
			""",
			{"serial_no": self.serial_no, "name": self.name or ""},
			as_dict=True,
		)
		if duplicate:
			frappe.throw(
				_("Wristband serial {0} is already used on ticket {1}").format(
					self.serial_no, duplicate[0].ticket
				)
			)
