# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
POS Table Session

Records which table an order belongs to and how many guests are seated there.

This lives in its own doctype rather than as custom fields on Sales Invoice
because the sale itself is not necessarily persisted in ERPNext - it may be
posted to an external system (e.g. Protel) instead. The session is therefore
the record of the table/guest context, independent of any Sales Invoice.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now


class POSTableSession(Document):
	def validate(self):
		self.validate_guest_count()
		self.validate_table_enabled()
		self.validate_single_open_session()

	def before_insert(self):
		if not self.opened_at:
			self.opened_at = now()
		if not self.cashier:
			self.cashier = frappe.session.user

	def validate_guest_count(self):
		"""A session without guests is meaningless - it's the reason the record exists."""
		if cint(self.guest_count) < 1:
			frappe.throw(_("Guest Count must be at least 1"))

	def validate_table_enabled(self):
		"""Don't let a disabled table be seated."""
		if not self.table:
			return

		if frappe.db.get_value("Table", self.table, "disabled"):
			frappe.throw(_("Table {0} is disabled").format(self.table))

	def validate_single_open_session(self):
		"""
		Only one Open session per table at a time.

		Without this two cashiers can seat the same table and each would build a
		separate order for it, which is exactly the duplicate the table number is
		supposed to prevent.
		"""
		if self.status != "Open" or not self.table:
			return

		existing = frappe.db.get_value(
			"POS Table Session",
			{
				"table": self.table,
				"status": "Open",
				"name": ["!=", self.name or ""],
			},
			"name",
		)

		if existing:
			frappe.throw(
				_("Table {0} already has an open session ({1}). Close it before seating the table again.").format(
					self.table, existing
				),
				title=_("Table Already Occupied"),
			)

	def close_session(self, sales_invoice=None, external_reference=None):
		"""Mark this session closed, optionally linking what it was posted to."""
		self.status = "Closed"
		self.closed_at = now()

		if sales_invoice:
			self.sales_invoice = sales_invoice
		if external_reference:
			self.external_reference = external_reference

		self.save(ignore_permissions=True)
		return self
