# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Branch expenses paid out of the branch safe.

The spending end of the cash custody chain: cash the branch manager received from
the cashier drawers leaves either upward (to the master treasury, see
`ecs_posnext.api.cash_transfer`) or outward as an expense recorded here.

Expense types come from the standard `Expense Claim Type`, whose per-company account
mapping decides which account is debited — so the chart of accounts stays under the
accountant's control while the branch manager only ever picks a readable name.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

from ecs_posnext.api.cash_management import _get_user_branch_scope
from ecs_posnext.api.cash_transfer import TRANSFER_ROLES, _account_balance, resolve_accounts
from ecs_posnext.pos_next.doctype.pos_branch_expense.pos_branch_expense import get_expense_account


def _require_expense_access():
	user = frappe.session.user
	if user == "Administrator":
		return
	if not set(TRANSFER_ROLES) & set(frappe.get_roles(user)):
		frappe.throw(
			_("Only a Branch Manager may record branch expenses."), frappe.PermissionError
		)


def _assert_branch_allowed(pos_profile):
	"""A restricted user may only spend from a branch they are permitted to see."""
	restricted, allowed_profiles, allowed_branches = _get_user_branch_scope()
	if not restricted:
		return
	if pos_profile in (allowed_profiles or []):
		return
	if allowed_branches:
		branch = frappe.db.get_value("POS Profile", pos_profile, "branch")
		if branch in allowed_branches:
			return
	frappe.throw(_("You are not permitted to record expenses for this branch."))


@frappe.whitelist()
def get_allowed_branches():
	"""POS Profiles the current user may spend from, newest configuration first."""
	_require_expense_access()
	filters = {"disabled": 0}
	restricted, allowed_profiles, allowed_branches = _get_user_branch_scope()
	if restricted:
		if allowed_profiles:
			filters["name"] = ["in", allowed_profiles]
		if allowed_branches:
			filters["branch"] = ["in", allowed_branches]
	return frappe.get_all("POS Profile", filters=filters, fields=["name", "company"], order_by="name")


@frappe.whitelist()
def get_expense_types(company):
	"""Expense Claim Types that actually have an account for this company.

	Types without a mapping are hidden rather than shown and rejected on save: an
	unmapped type cannot produce a posting, so offering it would only ever be a dead end.
	"""
	rows = frappe.get_all(
		"Expense Claim Account",
		filters={"parenttype": "Expense Claim Type", "company": company},
		fields=["parent as expense_type", "default_account"],
		order_by="parent",
	)
	return [r for r in rows if r.default_account]


@frappe.whitelist()
def get_branch_expense_state(pos_profile):
	"""Everything the Branch Expenses page needs for one branch."""
	_require_expense_access()
	_assert_branch_allowed(pos_profile)

	company = frappe.db.get_value("POS Profile", pos_profile, "company")
	accounts = resolve_accounts(pos_profile, company)
	safe = accounts["branch_safe"]

	return {
		"pos_profile": pos_profile,
		"company": company,
		"branch_safe_account": safe,
		"branch_safe_balance": _account_balance(safe, company),
		"currency": frappe.get_cached_value("Company", company, "default_currency"),
		"expense_types": get_expense_types(company),
		"spent_today": _spent_between(pos_profile, today(), today()),
	}


def _spent_between(pos_profile, from_date, to_date):
	total = frappe.db.sql(
		"""
		select sum(amount) from `tabPOS Branch Expense`
		where pos_profile = %s and docstatus = 1 and posting_date between %s and %s
		""",
		(pos_profile, from_date, to_date),
	)
	return flt(total[0][0]) if total and total[0][0] else 0.0


@frappe.whitelist()
def list_expenses(pos_profile, from_date=None, to_date=None, limit=100):
	"""Submitted and draft expenses for a branch in a date range, newest first."""
	_require_expense_access()
	_assert_branch_allowed(pos_profile)

	filters = {"pos_profile": pos_profile, "docstatus": ["<", 2]}
	if from_date and to_date:
		filters["posting_date"] = ["between", [getdate(from_date), getdate(to_date)]]

	rows = frappe.get_all(
		"POS Branch Expense",
		filters=filters,
		fields=[
			"name", "posting_date", "expense_claim_type", "expense_account", "amount",
			"description", "receipt", "status", "journal_entry", "recorded_by", "docstatus",
		],
		order_by="posting_date desc, creation desc",
		limit=limit,
	)
	return {
		"expenses": rows,
		"total": sum(flt(r.amount) for r in rows if r.docstatus == 1),
	}


@frappe.whitelist()
def record_expense(
	pos_profile, expense_claim_type, amount, description, receipt, posting_date=None
):
	"""Record and immediately post a branch expense.

	Submitted in the same call: the branch manager spends on their own authority, so a
	draft left behind would only be an expense that happened in the safe but not in the
	books.
	"""
	_require_expense_access()
	_assert_branch_allowed(pos_profile)

	if not receipt:
		frappe.throw(_("Attach the receipt or invoice for this expense."))

	company = frappe.db.get_value("POS Profile", pos_profile, "company")
	if not get_expense_account(expense_claim_type, company):
		frappe.throw(
			_("Expense Type {0} has no account set for {1}.").format(
				frappe.bold(expense_claim_type), company
			)
		)

	# Check the funds before building anything. The document re-checks on submit — that
	# is the guarantee — but refusing here keeps a rejected attempt from leaving a draft
	# expense behind in contexts that do not roll back the whole request.
	safe = resolve_accounts(pos_profile, company)["branch_safe"]
	available = _account_balance(safe, company)
	if flt(amount) > available:
		frappe.throw(
			_("Cannot pay {0}. The branch safe ({1}) only holds {2}.").format(
				frappe.format_value(flt(amount), {"fieldtype": "Currency"}),
				safe,
				frappe.format_value(available, {"fieldtype": "Currency"}),
			)
		)

	doc = frappe.get_doc(
		{
			"doctype": "POS Branch Expense",
			"pos_profile": pos_profile,
			"company": company,
			"posting_date": posting_date or today(),
			"expense_claim_type": expense_claim_type,
			"amount": flt(amount),
			"description": description,
			"receipt": receipt,
			"recorded_by": frappe.session.user,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()

	return {
		"name": doc.name,
		"amount": doc.amount,
		"journal_entry": doc.journal_entry,
		"balance": _account_balance(doc.paid_from, company),
	}


@frappe.whitelist()
def cancel_expense(name):
	"""Reverse a posted expense — cancels its Journal Entry too."""
	_require_expense_access()
	doc = frappe.get_doc("POS Branch Expense", name)
	_assert_branch_allowed(doc.pos_profile)
	doc.flags.ignore_permissions = True
	doc.cancel()
	return {"name": doc.name, "status": doc.status}
