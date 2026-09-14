# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class GeideaTerminal(Document):
	def validate(self):
		self.validate_connection_fields()
		self.validate_single_active_per_profile()

	def validate_connection_fields(self):
		"""A TCP terminal needs an IP + port; a COM terminal needs a port name."""
		if self.connection_mode == "TCP":
			if not self.ip_address:
				frappe.throw(_("Terminal IP Address is required for a TCP connection."))
			if not cint(self.port):
				frappe.throw(_("Terminal Port is required for a TCP connection."))
		elif not self.com_name:
			frappe.throw(_("COM Port is required for a COM connection."))

	def validate_single_active_per_profile(self):
		"""Only one active terminal per POS Profile — the cashier PC talks to one
		terminal, so a second active row would make the choice ambiguous."""
		if not cint(self.is_active):
			return
		other = frappe.db.get_value(
			"Geidea Terminal",
			{"pos_profile": self.pos_profile, "is_active": 1, "name": ("!=", self.name)},
			"name",
		)
		if other:
			frappe.throw(
				_("{0} is already the active Geidea terminal for POS Profile {1}.").format(
					other, self.pos_profile
				)
			)
