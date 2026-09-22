# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class POSBranchExpense(Document):
	"""Cash paid out of a branch safe against an expense account.

	The counterpart to the cash custody chain: money that arrives in the branch safe
	from the cashier drawers either goes on to the master treasury, or leaves here as
	a branch expense. Submitting posts the Journal Entry, cancelling reverses it.
	"""

	def validate(self):
		self._set_accounts()
		if flt(self.amount) <= 0:
			frappe.throw(_("Expense amount must be greater than zero."))
		if not self.recorded_by:
			self.recorded_by = frappe.session.user

	def _set_accounts(self):
		"""Resolve both sides of the entry server-side.

		Neither account is taken from the client: the expense account comes from the
		Expense Claim Type's mapping for this company, and the credit side is always the
		branch's own safe — so a branch can only ever spend its own custody.
		"""
		from ecs_posnext.api.cash_transfer import resolve_accounts

		self.expense_account = get_expense_account(self.expense_claim_type, self.company)
		if not self.expense_account:
			frappe.throw(
				_("Expense Type {0} has no account set for {1}. Add one in the Expense Claim Type.").format(
					frappe.bold(self.expense_claim_type), self.company
				)
			)

		self.paid_from = resolve_accounts(self.pos_profile, self.company)["branch_safe"]
		if not self.paid_from:
			frappe.throw(
				_("No branch safe account configured for {0}. Set it in POS Settings.").format(
					frappe.bold(self.pos_profile)
				)
			)

	def before_submit(self):
		if not self.receipt:
			frappe.throw(_("Attach the receipt before submitting the expense."))
		self._assert_funds()

	def _assert_funds(self):
		from ecs_posnext.api.cash_transfer import _account_balance

		available = _account_balance(self.paid_from, self.company)
		if flt(self.amount) > available:
			frappe.throw(
				_("Cannot pay {0}. The branch safe ({1}) only holds {2}.").format(
					frappe.format_value(flt(self.amount), {"fieldtype": "Currency"}),
					self.paid_from,
					frappe.format_value(available, {"fieldtype": "Currency"}),
				)
			)

	def on_submit(self):
		self._post_journal_entry()
		self.db_set("status", "Paid")
		self._log("Branch Expense")

	def on_cancel(self):
		self.flags.ignore_links = True
		if self.journal_entry and frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus") == 1:
			frappe.get_doc("Journal Entry", self.journal_entry).cancel()
		self.db_set("status", "Cancelled")
		self._log("Branch Expense Cancelled")

	def _post_journal_entry(self):
		company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Cash Entry"
		je.company = self.company
		je.posting_date = self.posting_date
		je.user_remark = _("{0} — {1} ({2})").format(
			self.expense_claim_type, self.description, self.pos_profile
		)
		for account, debit, credit in (
			(self.expense_account, flt(self.amount), 0),
			(self.paid_from, 0, flt(self.amount)),
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
		self.db_set("journal_entry", je.name)

	def _log(self, action):
		from ecs_posnext.api.business_day import log_pos_event

		log_pos_event(
			action=action,
			reference_doctype=self.doctype,
			reference_name=self.name,
			pos_profile=self.pos_profile,
			new_value="{0} -> {1}".format(flt(self.amount), self.expense_account),
			reason=self.description,
		)


def get_expense_account(expense_claim_type, company):
	"""The account an Expense Claim Type posts to for a given company."""
	if not expense_claim_type or not company:
		return None
	return frappe.db.get_value(
		"Expense Claim Account",
		{"parent": expense_claim_type, "parenttype": "Expense Claim Type", "company": company},
		"default_account",
	)
