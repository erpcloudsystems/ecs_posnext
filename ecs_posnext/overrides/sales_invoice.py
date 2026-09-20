# Copyright (c) 2025, BrainWise and contributors
# For license information, please see license.txt

"""
Sales Invoice Override
Handles wallet payments that require party information for Receivable accounts.

"""

import frappe
from frappe.utils import cint, flt
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.accounts.utils import get_account_currency

from ecs_posnext.api.utilities import is_wallet_payment_mode

def _get_post_change_gl_entries_setting():
	"""
	Get post_change_gl_entries setting compatible with ERPNext v15 and v16.

	- ERPNext v15: Field is in 'Accounts Settings'
	- ERPNext v16: Field moved to ERPNext's 'POS Settings' (singleton)

	Since ecs_posnext has its own 'POS Settings' doctype (non-singleton) that overrides
	ERPNext's, we read directly from the Singles table for v16 compatibility.

	Returns:
		int: 1 if post_change_gl_entries is enabled, 0 otherwise (default: 0)
	"""
	# Resolved once per request. Which doctype holds the field is fixed by the
	# installed ERPNext version, and the setting itself is a rarely-touched
	# singleton, so re-running the schema probe and the Singles query on each of
	# the three validate passes a POS submit makes only cost round trips.
	#
	# `frappe.local` is a werkzeug Local, whose __getattr__ raises AttributeError
	# for anything it is not holding - including dunders like __dict__. getattr
	# with a default is the only safe way to probe it.
	cached = getattr(frappe.local, "_ecs_posnext_post_change_gl_entries", None)
	if cached is not None:
		return cached

	value = _read_post_change_gl_entries_setting()
	frappe.local._ecs_posnext_post_change_gl_entries = value
	return value


def _read_post_change_gl_entries_setting():
	"""Uncached read behind `_get_post_change_gl_entries_setting`."""
	# Check if field exists in Accounts Settings schema (v15)
	meta = frappe.get_meta("Accounts Settings")
	if meta.has_field("post_change_gl_entries"):
		value = frappe.db.get_single_value("Accounts Settings", "post_change_gl_entries")
		return cint(value) if value is not None else 0

	# For v16, read directly from Singles table using Query Builder to avoid ORM issues
	# ERPNext's POS Settings is a singleton, data stored in Singles table
	Singles = frappe.qb.DocType("Singles")
	result = (
		frappe.qb.from_(Singles)
		.select(Singles.value)
		.where(Singles.doctype == "POS Settings")
		.where(Singles.field == "post_change_gl_entries")
		.limit(1)
		.run()
	)
	return cint(result[0][0]) if result else 0


def _get_cash_account_of_pos_profile(pos_profile, company):
	"""Account behind the POS Profile's own Cash mode of payment.

	Returns None when the profile has no cash mode for this company, or has
	several that point at different accounts - the change account is then left
	to whatever ERPNext resolved, since there is nothing unambiguous to pick.
	"""
	# Resolved once per request: set_pos_fields runs on every validate pass of a
	# POS submit, and a profile's payment methods do not move under it mid-request.
	memo = getattr(frappe.local, "_ecs_posnext_profile_cash_account", None)
	if memo is None:
		memo = frappe.local._ecs_posnext_profile_cash_account = {}

	key = (pos_profile, company)
	if key in memo:
		return memo[key]

	PaymentMethod = frappe.qb.DocType("POS Payment Method")
	ModeOfPayment = frappe.qb.DocType("Mode of Payment")
	ModeOfPaymentAccount = frappe.qb.DocType("Mode of Payment Account")

	rows = (
		frappe.qb.from_(PaymentMethod)
		.join(ModeOfPayment)
		.on(ModeOfPayment.name == PaymentMethod.mode_of_payment)
		.join(ModeOfPaymentAccount)
		.on(ModeOfPaymentAccount.parent == ModeOfPayment.name)
		.select(ModeOfPaymentAccount.default_account)
		.distinct()
		.where(PaymentMethod.parent == pos_profile)
		.where(PaymentMethod.parenttype == "POS Profile")
		.where(ModeOfPayment.type == "Cash")
		.where(ModeOfPaymentAccount.company == company)
		.where(ModeOfPaymentAccount.default_account.notnull())
		.run()
	)

	accounts = [row[0] for row in rows if row[0]]
	account = accounts[0] if len(accounts) == 1 else None
	memo[key] = account
	return account


class CustomSalesInvoice(SalesInvoice):
	"""
	Custom Sales Invoice class that handles wallet payments correctly.

	When a wallet payment is made using a Receivable account, ERPNext requires
	party information in the GL entry. This override adds party_type and party
	for wallet payment methods marked with is_wallet_payment.
	"""

	def set_pos_fields(self, for_validate=False):
		"""
		Override to take the change account from the POS Profile's own cash till.

		ERPNext only reads `account_for_change_amount` off the POS Profile, and
		falls back to Company.default_cash_account when the profile leaves it
		empty. With one company and a profile per branch that means every branch
		hands change back out of the head office till, so the change lands in the
		wrong cost center and the branch's expected cash at shift closing is
		overstated by it. Fall back to the cash mode of payment configured on the
		profile itself instead.

		A value already configured on the POS Profile, or picked by hand on the
		invoice, is left untouched; the company default is treated as "nothing was
		chosen" so that held drafts get corrected too.
		"""
		result = super().set_pos_fields(for_validate=for_validate)

		if not cint(self.is_pos) or not self.pos_profile:
			return result

		if frappe.get_cached_value("POS Profile", self.pos_profile, "account_for_change_amount"):
			# Configured on the profile - ERPNext already applied it.
			return result

		company_default = frappe.get_cached_value("Company", self.company, "default_cash_account")
		if self.account_for_change_amount and self.account_for_change_amount != company_default:
			# Chosen deliberately on the invoice.
			return result

		account = _get_cash_account_of_pos_profile(self.pos_profile, self.company)
		if account:
			self.account_for_change_amount = account

		return result

	def make_pos_gl_entries(self, gl_entries):
		"""
		Override to add party information for wallet payment accounts.

		The standard ERPNext implementation doesn't set party_type/party for
		payment mode accounts, which causes validation errors for Receivable
		accounts (like wallet accounts).
		"""
		if cint(self.is_pos):
			skip_change_gl_entries = not _get_post_change_gl_entries_setting()

			for payment_mode in self.payments:
				if skip_change_gl_entries and payment_mode.account == self.account_for_change_amount:
					payment_mode.base_amount -= flt(self.change_amount)

				if payment_mode.amount:
					# POS, make payment entries
					# Credit entry to debit_to (customer receivable)
					gl_entries.append(
						self.get_gl_dict(
							{
								"account": self.debit_to,
								"party_type": "Customer",
								"party": self.customer,
								"against": payment_mode.account,
								"credit": payment_mode.base_amount,
								"credit_in_account_currency": payment_mode.base_amount
								if self.party_account_currency == self.company_currency
								else payment_mode.amount,
								"against_voucher": self.return_against
								if cint(self.is_return) and self.return_against
								else self.name,
								"against_voucher_type": self.doctype,
								"cost_center": self.cost_center,
							},
							self.party_account_currency,
							item=self,
						)
					)

					# Debit entry to payment mode account
					payment_mode_account_currency = get_account_currency(payment_mode.account)

					# Get party info for wallet payments
					party_type, party = self.get_party_and_party_type_for_pos_gl_entry(
						payment_mode.mode_of_payment, payment_mode.account
					)

					gl_entries.append(
						self.get_gl_dict(
							{
								"account": payment_mode.account,
								"party_type": party_type,
								"party": party,
								"against": self.customer,
								"debit": payment_mode.base_amount,
								"debit_in_account_currency": payment_mode.base_amount
								if payment_mode_account_currency == self.company_currency
								else payment_mode.amount,
								"cost_center": self.cost_center,
							},
							payment_mode_account_currency,
							item=self,
						)
					)

			if not skip_change_gl_entries:
				if hasattr(self, "get_gle_for_change_amount"):
					# ERPNext v16+: Method renamed and returns a list of GL entries
					# that needs to be extended to the main gl_entries list
					gl_entries.extend(self.get_gle_for_change_amount())
				else:
					# ERPNext v15: Method takes gl_entries as parameter
					# and appends change amount entries directly to it
					self.make_gle_for_change_amount(gl_entries)

	def get_party_and_party_type_for_pos_gl_entry(self, mode_of_payment, account):
		"""
		Get party type and party for wallet payment GL entries.

		For wallet payments (Mode of Payment with is_wallet_payment=1),
		returns Customer as party_type and the invoice customer as party.
		For regular payments, returns empty strings.
		"""
		party_type, party = "", ""
		if is_wallet_payment_mode(mode_of_payment):
			party_type, party = "Customer", self.customer

		return party_type, party
