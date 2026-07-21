# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

DENOMINATIONS = {
	"cash_200_egp": 200,
	"cash_100_egp": 100,
	"cash_50_egp": 50,
	"cash_20_egp": 20,
	"cash_10_egp": 10,
	"cash_5_egp": 5,
	"cash_1_egp": 1,
}


class POSCashierShiftClosing(Document):
	def validate(self):
		self._validate_single_closing()
		self._set_business_day()
		self.calculate_actual_counted_cash()
		# Blind close: the shift figures + expected cash are computed ONLY after the
		# drawer has been counted. "Counted" is an explicit flag, NOT "amount > 0" — an
		# empty drawer is a legitimate count of 0 and must be closeable.
		if self.cash_counted:
			self._populate_from_shift()
			self.calculate_reconciliation()
		self.set_status()

	def _populate_from_shift(self):
		"""Pull opening cash, POS cash sales, call-center cash, refunds and the linked
		invoices/reconciliation from the cashier's shift. Idempotent."""
		from ecs_posnext.api.cashier_shift import compute_cash_figures

		shift = frappe.get_doc("POS Cashier Shift", self.pos_cashier_shift)
		fig = compute_cash_figures(shift.pos_opening_shift)
		self.opening_cash = fig.opening_cash
		self.cash_sales = fig.cash_sales
		self.cash_refunds = fig.cash_refunds
		self.call_center_cash_collected = fig.call_center_cash_collected
		if not self.shift_start:
			self.shift_start = fig.shift_start
		if not self.shift_end:
			self.shift_end = now_datetime()
		if not self.supervisor_employee:
			self.supervisor_employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
		self.set("payment_reconciliation", fig.payment_reconciliation)
		self.set("pos_transactions", fig.pos_transactions)

	def _set_business_day(self):
		"""Always link the closing to its Business Day.

		Set server-side rather than relying on a fetch_from, so the link can't go missing:
		the day's closing validations (uncounted cash, unapproved differences) query
		closings BY pos_business_day and would silently skip an unlinked one.
		"""
		if self.pos_cashier_shift and not self.pos_business_day:
			self.pos_business_day = frappe.db.get_value(
				"POS Cashier Shift", self.pos_cashier_shift, "pos_business_day"
			)

	def _validate_single_closing(self):
		dup = frappe.db.exists(
			"POS Cashier Shift Closing",
			{
				"pos_cashier_shift": self.pos_cashier_shift,
				"docstatus": ["<", 2],
				"name": ["!=", self.name or ""],
			},
		)
		if dup:
			frappe.throw(
				_("A closing ({0}) already exists for this cashier shift.").format(dup),
				title=_("Duplicate Closing"),
			)

	def calculate_actual_counted_cash(self):
		self.actual_counted_cash = sum(flt(self.get(f)) * mult for f, mult in DENOMINATIONS.items())

	def calculate_reconciliation(self):
		# Expected Cash =
		#   Opening Cash + POS Cash Sales + Call Center Cash Collected - Cash Refunds
		self.expected_cash = (
			flt(self.opening_cash)
			+ flt(self.cash_sales)
			+ flt(self.call_center_cash_collected)
			- flt(self.cash_refunds)
		)
		self.difference = flt(self.actual_counted_cash) - flt(self.expected_cash)
		self.shortage = abs(self.difference) if self.difference < 0 else 0
		self.overage = self.difference if self.difference > 0 else 0

		# Expected Credit = everything the shift took on non-cash (card / bank / wallet)
		# modes. The supervisor enters Actual Credit (from the card terminal / bank) and
		# we reconcile it as a single figure, mirroring the cash side.
		expected_credit = 0
		for row in self.get("payment_reconciliation") or []:
			mtype = frappe.get_cached_value("Mode of Payment", row.mode_of_payment, "type")
			if mtype == "Cash":
				row.closing_amount = flt(self.actual_counted_cash)
			else:
				expected_credit += flt(row.expected_amount)
				if not row.closing_amount:
					row.closing_amount = flt(row.expected_amount)
			row.difference = flt(row.closing_amount) - flt(row.expected_amount)

		self.expected_credit = expected_credit
		self.credit_difference = flt(self.actual_credit) - flt(self.expected_credit)

		# Any unexplained difference — cash OR credit — needs manager approval.
		self.difference_requires_approval = 1 if (flt(self.difference) or flt(self.credit_difference)) else 0

	def set_status(self):
		if self.docstatus == 2:
			self.status = "Cancelled"
		elif self.docstatus == 1:
			self.status = "Closed"
		elif not self.cash_counted:
			self.status = "Awaiting Count"
		elif self.difference_requires_approval and not self.approved_by:
			self.status = "Difference Pending Approval"
		else:
			self.status = "Counted"

	def before_submit(self):
		if not self.cash_counted:
			frappe.throw(_("Count the drawer and confirm 'Cash Counted' before closing the shift."))
		if self.difference_requires_approval and not self.approved_by:
			frappe.throw(
				_("This shift has a cash/credit difference and needs Manager Approval before closing.")
			)
		if (flt(self.difference) or flt(self.credit_difference)) and not self.difference_reason:
			frappe.throw(_("Please enter a Difference Reason."))

	def on_submit(self):
		from ecs_posnext.api.business_day import log_pos_event

		shift = frappe.get_doc("POS Cashier Shift", self.pos_cashier_shift)
		shift.db_set("status", "Closed")
		shift.db_set("cashier_shift_closing", self.name)

		# Also close the UNDERLYING legacy POS Opening Shift. Without this the POS still
		# reports the cashier as on-shift (check_opening_shift looks for status "Open"
		# with pos_closing_shift unset), so new sales/returns would keep attaching to a
		# shift that has already been counted and reconciled — silently invalidating
		# this closing's figures.
		if shift.pos_opening_shift and frappe.db.exists("POS Opening Shift", shift.pos_opening_shift):
			frappe.db.set_value(
				"POS Opening Shift",
				shift.pos_opening_shift,
				{"pos_closing_shift": self.name, "status": "Closed"},
				update_modified=False,
			)

		if self.pos_business_day and frappe.db.exists("POS Business Day", self.pos_business_day):
			frappe.get_doc("POS Business Day", self.pos_business_day).refresh_summary(save=True)

		action = "Overage" if flt(self.overage) else ("Shortage" if flt(self.shortage) else "Closing Shift")
		log_pos_event(
			action=action,
			reference_doctype=self.doctype,
			reference_name=self.name,
			pos_profile=self.pos_profile,
			pos_business_day=self.pos_business_day,
			new_value=self.actual_counted_cash,
			old_value=self.expected_cash,
			reason=self.difference_reason,
		)

	def on_cancel(self):
		shift = frappe.db.exists("POS Cashier Shift", self.pos_cashier_shift)
		if shift:
			frappe.db.set_value("POS Cashier Shift", self.pos_cashier_shift, {"status": "Open", "cashier_shift_closing": None})
			# Re-open the underlying legacy opening shift (mirror of on_submit).
			opening = frappe.db.get_value("POS Cashier Shift", self.pos_cashier_shift, "pos_opening_shift")
			if opening and frappe.db.get_value("POS Opening Shift", opening, "pos_closing_shift") == self.name:
				frappe.db.set_value(
					"POS Opening Shift",
					opening,
					{"pos_closing_shift": "", "status": "Open"},
					update_modified=False,
				)
		if self.pos_business_day and frappe.db.exists("POS Business Day", self.pos_business_day):
			frappe.get_doc("POS Business Day", self.pos_business_day).refresh_summary(save=True)


@frappe.whitelist()
def approve_difference(pos_cashier_shift_closing, reason=None):
	"""Manager approval for a cashier cash difference."""
	doc = frappe.get_doc("POS Cashier Shift Closing", pos_cashier_shift_closing)
	doc.approved_by = frappe.session.user
	doc.approval_datetime = now_datetime()
	if reason:
		doc.difference_reason = reason
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)

	from ecs_posnext.api.business_day import log_pos_event

	log_pos_event(
		action="Manager Approval",
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		pos_profile=doc.pos_profile,
		pos_business_day=doc.pos_business_day,
		new_value=doc.difference,
		reason=reason,
	)
	return doc.as_dict()
