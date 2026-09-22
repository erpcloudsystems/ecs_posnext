# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Map branch petty-cash expense types to their accounts.

The Branch Expenses page only offers an Expense Claim Type that already has an
account for the company — an unmapped type could never post. This seeds the common
branch spends so the page is usable on day one; the accountant adds, renames or
removes types from the standard Expense Claim Type list afterwards.

Only missing mappings are added, so a type an accountant has already pointed
somewhere else is never re-pointed. Idempotent.
"""

import frappe

# Expense Claim Type name -> the account it should post to, by account_name.
BRANCH_EXPENSE_TYPES = {
	"Utility Expenses": "Utility Expenses",
	"Office Maintenance Expenses": "Office Maintenance Expenses",
	"Print and Stationery": "Print and Stationery",
	"Telephone Expenses": "Telephone Expenses",
	"Marketing Expenses": "Marketing Expenses",
	"Travel Expenses": "Travel Expenses",
	"Entertainment Expenses": "Entertainment Expenses",
	"Miscellaneous Expenses": "Miscellaneous Expenses",
}


def execute():
	companies = frappe.get_all("Company", pluck="name")
	for type_name, account_name in BRANCH_EXPENSE_TYPES.items():
		mapped = {
			company: account
			for company in companies
			if (account := _expense_account(company, account_name))
		}
		if mapped:
			_ensure_type(type_name, mapped)
	frappe.db.commit()


def _expense_account(company, account_name):
	return frappe.db.get_value(
		"Account",
		{"company": company, "account_name": account_name, "root_type": "Expense", "is_group": 0},
		"name",
	)


def _ensure_type(type_name, accounts_by_company):
	is_new = not frappe.db.exists("Expense Claim Type", type_name)
	doc = (
		frappe.get_doc({"doctype": "Expense Claim Type", "expense_type": type_name})
		if is_new
		else frappe.get_doc("Expense Claim Type", type_name)
	)

	mapped_companies = {row.company for row in doc.get("accounts") or []}
	added = False
	for company, account in accounts_by_company.items():
		if company in mapped_companies:
			continue
		doc.append("accounts", {"company": company, "default_account": account})
		added = True

	if not (is_new or added):
		return

	doc.flags.ignore_permissions = True
	if is_new:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
