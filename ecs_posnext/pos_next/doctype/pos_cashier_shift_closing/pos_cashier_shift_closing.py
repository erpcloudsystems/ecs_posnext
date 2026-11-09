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
		# Call Center shifts have no physical drawer to count — treat them as auto-counted
		# so they compute + auto-balance (Actual = Expected) without a manual count step.
		if self._is_call_center():
			self.cash_counted = 1
		# Blind close: the shift figures + expected cash are computed ONLY after the
		# drawer has been counted. "Counted" is an explicit flag, NOT "amount > 0" — an
		# empty drawer is a legitimate count of 0 and must be closeable.
		self._ensure_credit_rows()
		if self.cash_counted:
			self._populate_from_shift()
			self._ensure_credit_rows()
			self.calculate_reconciliation()
		self.set_status()

	def _ensure_credit_rows(self):
		"""One Actual Non-Cash row per non-cash mode (card, wallet, …), entered separately.

		Card and wallet settle into different bank accounts, so each mode is reconciled on
		its own. Before the count only the profile's modes are listed (no amounts — the
		close stays blind); after the count any other non-cash mode the shift took is added.
		"""
		modes = []
		profile = self.pos_profile or (
			self.pos_cashier_shift and frappe.db.get_value("POS Cashier Shift", self.pos_cashier_shift, "pos_profile")
		)
		if profile:
			modes += frappe.get_all(
				"POS Payment Method",
				filters={"parent": profile, "parenttype": "POS Profile"},
				pluck="mode_of_payment",
				order_by="idx",
			)
		modes += [row.mode_of_payment for row in self.get("payment_reconciliation") or []]

		existing = {row.mode_of_payment for row in self.get("credit_counts") or []}
		for mode in modes:
			if mode and mode not in existing and not self._is_cash_mode(mode):
				self.append("credit_counts", {"mode_of_payment": mode, "amount": 0})
				existing.add(mode)

		# Legacy entry (API / drafts from before the split): a single total can only be
		# attributed when there is exactly one non-cash mode.
		rows = self.get("credit_counts") or []
		if flt(self.actual_credit) and not any(flt(r.amount) for r in rows):
			if len(rows) == 1:
				rows[0].amount = flt(self.actual_credit)
			elif rows and not self._is_call_center():
				frappe.throw(
					_("Enter the actual amount for each non-cash payment method ({0}) separately.").format(
						", ".join(r.mode_of_payment for r in rows)
					),
					title=_("Actual Non-Cash per Payment Method"),
				)
		if rows:
			self.actual_credit = sum(flt(r.amount) for r in rows)

	@staticmethod
	def _is_cash_mode(mode):
		return frappe.get_cached_value("Mode of Payment", mode, "type") == "Cash"

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
		# Supervisor = whoever actually closes (counts) the shift. Set authoritatively
		# here (not "only if empty"), so it reflects the closer even if a different
		# person prepared the closing.
		closer_employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
		if closer_employee:
			self.supervisor_employee = closer_employee
		self.set("payment_reconciliation", fig.payment_reconciliation)
		self.set("pos_transactions", fig.pos_transactions)
		# Payment Entries (COD / Call Center collections) settled on this shift — the
		# line-by-line breakdown behind call_center_cash_collected, which is otherwise a
		# single unexplained figure on the reveal screen.
		self.set("pos_payment_entries", fig.pos_payment_entries)

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

	def _is_call_center(self):
		profile = self.pos_profile
		if not profile and self.pos_cashier_shift:
			profile = frappe.db.get_value("POS Cashier Shift", self.pos_cashier_shift, "pos_profile")
		return "call center" in (profile or "").lower()

	def calculate_reconciliation(self):
		# Expected Cash =
		#   Opening Cash + POS Cash Sales + Call Center Cash Collected - Cash Refunds
		self.expected_cash = (
			flt(self.opening_cash)
			+ flt(self.cash_sales)
			+ flt(self.call_center_cash_collected)
			- flt(self.cash_refunds)
		)

		# Call Center agents never hold a physical drawer — the money is collected by the
		# branch / driver. So a Call Center shift closing is auto-balanced: for every mode
		# of payment Actual = Expected (no counting, no difference).
		is_cc = self._is_call_center()
		if is_cc:
			self.actual_counted_cash = flt(self.expected_cash)

		self.difference = flt(self.actual_counted_cash) - flt(self.expected_cash)
		self.shortage = abs(self.difference) if self.difference < 0 else 0
		self.overage = self.difference if self.difference > 0 else 0

		# Expected Credit = everything the shift took on non-cash (card / bank / wallet)
		# modes. The supervisor enters the actual amount of EACH non-cash mode (card from
		# the card machine report, wallet from the bank app); each row is reconciled
		# against its own amount, and Actual Credit is their sum.
		expected_by_mode = {}
		for row in self.get("payment_reconciliation") or []:
			if not self._is_cash_mode(row.mode_of_payment):
				expected_by_mode[row.mode_of_payment] = flt(row.expected_amount)
		if is_cc:
			# Actual = Expected for every mode on a Call Center shift.
			for credit in self.get("credit_counts") or []:
				credit.amount = expected_by_mode.get(credit.mode_of_payment, 0)
		actual_by_mode = {}
		for credit in self.get("credit_counts") or []:
			actual_by_mode[credit.mode_of_payment] = actual_by_mode.get(credit.mode_of_payment, 0) + flt(credit.amount)

		for row in self.get("payment_reconciliation") or []:
			if is_cc:
				row.closing_amount = flt(row.expected_amount)
			elif self._is_cash_mode(row.mode_of_payment):
				row.closing_amount = flt(self.actual_counted_cash)
			else:
				row.closing_amount = actual_by_mode.get(row.mode_of_payment, 0)
			row.difference = flt(row.closing_amount) - flt(row.expected_amount)

		self.expected_credit = sum(expected_by_mode.values())
		self.actual_credit = sum(actual_by_mode.values())
		if is_cc:
			self.actual_credit = flt(self.expected_credit)
		self.credit_difference = flt(self.actual_credit) - flt(self.expected_credit)

		# Auto-balanced Call Center shift never needs approval; otherwise any unexplained
		# cash / credit difference does.
		if is_cc:
			self.difference_requires_approval = 0
		else:
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
