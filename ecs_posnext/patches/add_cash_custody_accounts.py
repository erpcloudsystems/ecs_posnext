# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Create the accounts the POS cash custody chain needs.

Per company: a Cash Shortage expense account and a Cash Overage income account.
Per POS Profile: a "Branch Safe <profile>" cash account, the branch manager's safe
sitting between the cashier drawer and the master treasury.

Existing POS Settings rows get their blank custody fields filled in; rows are never
created, so a profile that has no settings today keeps resolving its accounts by name.

Idempotent — safe to re-run.
"""

import frappe

CUSTODY_FIELDS = (
	"cashier_drawer_account",
	"branch_safe_account",
	"master_cash_account",
	"cash_shortage_account",
	"cash_overage_account",
)


def execute():
	for company in frappe.get_all("Company", pluck="name"):
		shortage = _ensure_account(company, "Cash Shortage", "Expense", ["Indirect Expenses", "Expenses"])
		overage = _ensure_account(company, "Cash Overage", "Income", ["Indirect Income", "Income"])
		master = _find_leaf(company, "Master Treasury")

		for profile in frappe.get_all(
			"POS Profile", filters={"company": company, "disabled": 0}, pluck="name"
		):
			safe = _ensure_account(
				company, f"Branch Safe {profile}", "Asset", ["Cash In Hand"], account_type="Cash"
			)
			_fill_settings(profile, safe, master, shortage, overage)

	frappe.db.commit()


def _find_leaf(company, account_name):
	return frappe.db.get_value(
		"Account", {"company": company, "account_name": account_name, "is_group": 0}, "name"
	)


def _find_group(company, candidates, root_type):
	"""First matching group account, else any group of the right root type."""
	for name in candidates:
		match = frappe.db.get_value(
			"Account", {"company": company, "account_name": name, "is_group": 1}, "name"
		)
		if match:
			return match
	return frappe.db.get_value(
		"Account", {"company": company, "root_type": root_type, "is_group": 1}, "name"
	)


def _ensure_account(company, account_name, root_type, parent_candidates, account_type=None):
	existing = _find_leaf(company, account_name)
	if existing:
		return existing

	parent = _find_group(company, parent_candidates, root_type)
	if not parent:
		frappe.log_error(
			f"Could not place '{account_name}' for {company}: no {root_type} group account found.",
			"POS Cash Custody Accounts",
		)
		return None

	doc = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": account_name,
			"company": company,
			"parent_account": parent,
			"root_type": root_type,
			"is_group": 0,
			"account_type": account_type,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _fill_settings(profile, safe, master, shortage, overage):
	"""Populate blank custody fields on an existing POS Settings row.

	Only blanks are touched — a branch that was pointed at a different safe by hand
	keeps its own configuration.
	"""
	if not frappe.db.exists("POS Settings", profile):
		return
	current = frappe.db.get_value("POS Settings", profile, CUSTODY_FIELDS, as_dict=True) or {}
	updates = {}
	for fieldname, value in (
		("branch_safe_account", safe),
		("master_cash_account", master),
		("cash_shortage_account", shortage),
		("cash_overage_account", overage),
	):
		if value and not current.get(fieldname):
			updates[fieldname] = value
	if updates:
		frappe.db.set_value("POS Settings", profile, updates)
