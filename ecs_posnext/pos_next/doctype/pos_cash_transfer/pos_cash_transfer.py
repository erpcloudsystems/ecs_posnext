# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

DRAWER_TO_SAFE = "Drawer to Branch Safe"
SAFE_TO_MASTER = "Branch Safe to Master Cash"

BUSINESS_DAY_LINK_FIELD = {
	DRAWER_TO_SAFE: "drawer_to_safe_transfer",
	SAFE_TO_MASTER: "safe_to_master_transfer",
}


class POSCashTransfer(Document):
	"""One custody hand-over of physical cash, with its accounting vouchers.

	The figures are always computed server-side by `ecs_posnext.api.cash_transfer`;
	every field here is read-only in the form. Submitting posts the money, cancelling
	un-posts it — so a mistaken hand-over is reversed by cancelling this one document
	instead of hunting down its Payment Entry and Journal Entry separately.
	"""

	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Transfer amount must be greater than zero."))
		if self.from_account == self.to_account:
			frappe.throw(_("From and To accounts must be different."))
		if flt(self.variance) and not self.variance_account:
			frappe.throw(_("A variance of {0} needs a Variance Account.").format(self.variance))

	def on_submit(self):
		# The variance is posted BEFORE the hand-over: it writes the drawer down (or up)
		# to the cash that physically exists, so the transfer that follows can move the
		# counted amount without driving the drawer account negative.
		self._post_variance()
		self._post_transfer()
		self.db_set("status", "Transferred")
		self._link_to_business_day(self.name)
		self._log("Cash Transfer")

	def on_cancel(self):
		self.flags.ignore_links = True
		# Cancel in the reverse order of posting so the drawer is never momentarily
		# short of the money the variance entry accounted for.
		for fieldname, doctype in (
			("payment_entry", "Payment Entry"),
			("variance_journal_entry", "Journal Entry"),
		):
			voucher = self.get(fieldname)
			if voucher and frappe.db.get_value(doctype, voucher, "docstatus") == 1:
				frappe.get_doc(doctype, voucher).cancel()
		self.db_set("status", "Cancelled")
		self._link_to_business_day(None)
		self._log("Cash Transfer Cancelled")

	# ------------------------------------------------------------------
	# Posting
	# ------------------------------------------------------------------
	def _post_variance(self):
		"""Book the counted-vs-expected difference to the shortage / overage account."""
		variance = flt(self.variance)
		if not variance:
			return

		company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.company = self.company
		je.posting_date = self.posting_date
		je.user_remark = _("Cash {0} on POS Business Day {1} ({2})").format(
			_("overage") if variance > 0 else _("shortage"), self.pos_business_day, self.pos_profile
		)

		if variance < 0:
			# Shortage: money the books expected is missing — charge it to expense.
			debit_account, credit_account = self.variance_account, self.from_account
		else:
			# Overage: more cash in the drawer than the books expected — book it as income.
			debit_account, credit_account = self.from_account, self.variance_account

		amount = abs(variance)
		for account, debit, credit in (
			(debit_account, amount, 0),
			(credit_account, 0, amount),
		):
			je.append(
				"accounts",
				{
					"account": account,
					"debit_in_account_currency": debit,
					"credit_in_account_currency": credit,
					"account_currency": company_currency,
				},
			)

		je.flags.ignore_permissions = True
		je.insert(ignore_permissions=True)
		je.submit()
		self.db_set("variance_journal_entry", je.name)

	def _post_transfer(self):
		company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Internal Transfer"
		pe.company = self.company
		pe.posting_date = self.posting_date
		pe.reference_date = self.posting_date
		pe.paid_from = self.from_account
		pe.paid_to = self.to_account
		pe.paid_amount = flt(self.amount)
		pe.received_amount = flt(self.amount)
		pe.paid_from_account_currency = company_currency
		pe.paid_to_account_currency = company_currency
		pe.remarks = self.remarks or _("{0} for POS Business Day {1} ({2})").format(
			self.transfer_type, self.pos_business_day, self.pos_profile
		)
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		pe.submit()
		self.db_set("payment_entry", pe.name)

	# ------------------------------------------------------------------
	# Bookkeeping around the transfer
	# ------------------------------------------------------------------
	def _link_to_business_day(self, value):
		"""Stamp (or clear) this transfer on its Business Day.

		The link is what stops a second hand-over of the same money: the API refuses to
		build a transfer while the day already points at a submitted one.
		"""
		fieldname = BUSINESS_DAY_LINK_FIELD.get(self.transfer_type)
		if not fieldname or not self.pos_business_day:
			return
		if not frappe.db.exists("POS Business Day", self.pos_business_day):
			return
		frappe.db.set_value(
			"POS Business Day", self.pos_business_day, fieldname, value, update_modified=False
		)

	def _log(self, action):
		from ecs_posnext.api.business_day import log_pos_event

		log_pos_event(
			action=action,
			reference_doctype=self.doctype,
			reference_name=self.name,
			pos_profile=self.pos_profile,
			pos_business_day=self.pos_business_day,
			old_value=self.from_account,
			new_value="{0} -> {1}".format(flt(self.amount), self.to_account),
			reason=self.remarks,
		)
