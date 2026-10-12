# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
POS Table Order

The server-side held order for a table. Replaces the browser-only (IndexedDB)
hold for online use, so a manager or a second terminal can see what every open
table has actually ordered.

`items` is the readable/reportable projection; `cart_payload` is the full POS
cart, which is what gets restored on resume so offers, batches, serials and UOM
pricing come back exactly as they were.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now


class POSTableOrder(Document):
	def validate(self):
		self.set_totals()
		self.set_order_timestamps()

	def set_totals(self):
		"""Totals are derived, never trusted from the client."""
		self.total_qty = sum(flt(row.qty) for row in self.items)
		self.total_amount = sum(flt(row.amount) for row in self.items)

	def set_order_timestamps(self):
		"""
		Stamp the order clock.

		`last_order_at` is what the tables dashboard measures idle time against,
		so it only moves when the order actually changes - not on every unrelated
		save (a status change, an external reference being filled in).
		"""
		if not self.items:
			return

		if not self.ordered_at:
			self.ordered_at = now()

		if self.has_value_changed("total_qty") or self.has_value_changed("total_amount"):
			self.last_order_at = now()
		elif not self.last_order_at:
			self.last_order_at = now()

	def on_update(self):
		self.sync_session_last_order()

	def sync_session_last_order(self):
		"""
		Mirror the order clock onto the session.

		The dashboard reads sessions first (a seated table may have no order yet),
		so keeping the timestamp there too means idle time is one field lookup
		rather than a join per table.
		"""
		if not self.table_session or not self.last_order_at:
			return

		if not frappe.db.exists("POS Table Session", self.table_session):
			return

		current = frappe.db.get_value("POS Table Session", self.table_session, "last_order_at")
		if not current or str(current) < str(self.last_order_at):
			frappe.db.set_value(
				"POS Table Session",
				self.table_session,
				"last_order_at",
				self.last_order_at,
				update_modified=False,
			)

	def settle(self, sales_invoice=None, external_reference=None):
		"""Mark the order settled once its bill is paid."""
		self.status = "Settled"
		if sales_invoice:
			self.sales_invoice = sales_invoice
		if external_reference:
			self.external_reference = external_reference
		self.save(ignore_permissions=True)
		return self
