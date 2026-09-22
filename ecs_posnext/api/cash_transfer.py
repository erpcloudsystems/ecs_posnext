# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Cash custody chain for a POS Business Day.

Physical cash moves in two hops once the day is closed:

    cashier drawer  ->  branch safe  ->  master cash

Each hop is a `POS Cash Transfer` document that posts an Internal Transfer Payment
Entry. The first hop also books the counted-vs-expected difference to a shortage /
overage account, so the drawer account ends the day flat: what the books say left the
drawer is exactly what the branch manager physically received.
"""

import frappe
from frappe import _
from frappe.utils import flt, today

from ecs_posnext.pos_next.doctype.pos_cash_transfer.pos_cash_transfer import (
	DRAWER_TO_SAFE,
	SAFE_TO_MASTER,
)

TRANSFER_ROLES = (
	"System Manager",
	"POSNext Branch Manager",
	"POSNext Operations Manager",
	# Legacy role name kept in sync with ecs_posnext.api.cash_management.
	"Bransh Manager",
)


def _require_transfer_access():
	user = frappe.session.user
	if user == "Administrator":
		return
	if not set(TRANSFER_ROLES) & set(frappe.get_roles(user)):
		frappe.throw(
			_("Only a Branch Manager may transfer cash between treasuries."),
			frappe.PermissionError,
		)


# ----------------------------------------------------------------------
# Account resolution
# ----------------------------------------------------------------------
def _settings_accounts(pos_profile):
	"""Configured accounts from POS Settings, if a row exists for this profile."""
	if not frappe.db.exists("POS Settings", pos_profile):
		return {}
	return (
		frappe.db.get_value(
			"POS Settings",
			pos_profile,
			[
				"cashier_drawer_account",
				"branch_safe_account",
				"master_cash_account",
				"cash_shortage_account",
				"cash_overage_account",
			],
			as_dict=True,
		)
		or {}
	)


def _drawer_from_payment_methods(pos_profile, company):
	"""The account POS cash sales actually land in — the cashier's drawer.

	Taken from the profile's own Cash mode of payment rather than from a naming
	convention, because that is the account the Sales Invoice posts to; any other
	choice would leave the transfer moving money the drawer never received.
	"""
	methods = frappe.get_all(
		"POS Payment Method",
		filters={"parent": pos_profile, "parenttype": "POS Profile"},
		fields=["mode_of_payment"],
		order_by="idx asc",
	)
	for method in methods:
		if frappe.get_cached_value("Mode of Payment", method.mode_of_payment, "type") != "Cash":
			continue
		account = frappe.db.get_value(
			"Mode of Payment Account",
			{"parent": method.mode_of_payment, "company": company},
			"default_account",
		)
		if account:
			return account
	return None


def _find_account(company, names, account_type=None):
	for name in names:
		filters = {"company": company, "is_group": 0}
		if account_type:
			filters["account_type"] = account_type
		if frappe.db.exists("Account", dict(filters, name=name)):
			return name
		match = frappe.db.get_value(
			"Account", dict(filters, account_name=name), "name"
		)
		if match:
			return match
	return None


def resolve_accounts(pos_profile, company):
	"""Resolve the four accounts the custody chain needs.

	POS Settings wins; anything left blank falls back to the site's naming
	conventions so an unconfigured branch still works out of the box.
	"""
	configured = _settings_accounts(pos_profile)

	drawer = configured.get("cashier_drawer_account") or _drawer_from_payment_methods(
		pos_profile, company
	)
	branch_safe = configured.get("branch_safe_account") or _find_account(
		company,
		[f"Branch Safe {pos_profile}", f"خزنة فرع {pos_profile}", f"خزينة مدير فرع {pos_profile}"],
		"Cash",
	)
	master = configured.get("master_cash_account") or _find_account(
		company, ["Master Treasury", "الخزنة الرئيسية"], "Cash"
	)
	shortage = configured.get("cash_shortage_account") or _find_account(
		company, ["Cash Shortage", "عجز خزينة"]
	)
	overage = configured.get("cash_overage_account") or _find_account(
		company, ["Cash Overage", "زيادة خزينة"]
	)

	return {
		"drawer": drawer,
		"branch_safe": branch_safe,
		"master": master,
		"shortage": shortage,
		"overage": overage,
	}


def _account_balance(account, company):
	if not account:
		return 0.0
	balance = frappe.db.sql(
		"""
		select sum(debit) - sum(credit)
		from `tabGL Entry`
		where account = %s and company = %s and is_cancelled = 0
		""",
		(account, company),
	)
	return flt(balance[0][0]) if balance and balance[0][0] else 0.0


# ----------------------------------------------------------------------
# Day figures
# ----------------------------------------------------------------------
def get_day_cash_figures(business_day):
	"""Counted vs expected cash for a business day, from its submitted shift closings.

	Only submitted closings count: a draft closing has not been signed off by a
	supervisor, so its count is not yet a statement of what the branch holds.
	"""
	rows = frappe.get_all(
		"POS Cashier Shift Closing",
		filters={"pos_business_day": business_day, "docstatus": 1},
		fields=["name", "actual_counted_cash", "expected_cash"],
	)
	counted = sum(flt(r.actual_counted_cash) for r in rows)
	expected = sum(flt(r.expected_cash) for r in rows)
	return {
		"counted": counted,
		"expected": expected,
		"variance": counted - expected,
		"closings": len(rows),
	}


def _existing_transfer(business_day, transfer_type):
	return frappe.db.get_value(
		"POS Cash Transfer",
		{"pos_business_day": business_day, "transfer_type": transfer_type, "docstatus": 1},
		"name",
	)


@frappe.whitelist()
def get_cash_custody_state(business_day):
	"""Everything the Business Day form needs to render the two transfer buttons."""
	day = frappe.get_doc("POS Business Day", business_day)
	accounts = resolve_accounts(day.pos_profile, day.company)
	figures = get_day_cash_figures(business_day)

	drawer_transfer = _existing_transfer(business_day, DRAWER_TO_SAFE)
	safe_transfer = _existing_transfer(business_day, SAFE_TO_MASTER)

	return {
		"business_day": business_day,
		"status": day.status,
		"can_transfer": bool(set(TRANSFER_ROLES) & set(frappe.get_roles()))
		or frappe.session.user == "Administrator",
		"accounts": accounts,
		"figures": figures,
		"drawer_transfer": drawer_transfer,
		"safe_transfer": safe_transfer,
		"drawer_balance": _account_balance(accounts["drawer"], day.company),
		"branch_safe_balance": _account_balance(accounts["branch_safe"], day.company),
		"currency": frappe.get_cached_value("Company", day.company, "default_currency"),
	}


# ----------------------------------------------------------------------
# The two hops
# ----------------------------------------------------------------------
def _assert_closed(day):
	if day.status != "Closed":
		frappe.throw(
			_("Cash can only be handed over after the Business Day is closed (current status: {0}).").format(
				day.status
			)
		)


def _make_transfer(day, transfer_type, from_account, to_account, amount, **extra):
	doc = frappe.get_doc(
		{
			"doctype": "POS Cash Transfer",
			"transfer_type": transfer_type,
			"company": day.company,
			"pos_profile": day.pos_profile,
			"pos_business_day": day.name,
			"posting_date": today(),
			"transferred_by": frappe.session.user,
			"from_account": from_account,
			"to_account": to_account,
			"amount": flt(amount),
			**extra,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc


@frappe.whitelist()
def transfer_drawer_to_safe(business_day, remarks=None):
	"""Hand the day's physically counted cash from the cashier drawer to the branch safe."""
	_require_transfer_access()
	day = frappe.get_doc("POS Business Day", business_day)
	_assert_closed(day)

	existing = _existing_transfer(business_day, DRAWER_TO_SAFE)
	if existing:
		frappe.throw(
			_("The drawer for this Business Day was already handed over ({0}). Cancel it first to redo the transfer.").format(
				existing
			)
		)

	accounts = resolve_accounts(day.pos_profile, day.company)
	if not accounts["drawer"]:
		frappe.throw(_("No cashier drawer account found for POS Profile {0}.").format(day.pos_profile))
	if not accounts["branch_safe"]:
		frappe.throw(
			_("No branch safe account configured for POS Profile {0}. Set it in POS Settings.").format(
				day.pos_profile
			)
		)

	figures = get_day_cash_figures(business_day)
	if not figures["closings"]:
		frappe.throw(_("This Business Day has no submitted cashier shift closings to hand over."))
	if flt(figures["counted"]) <= 0:
		frappe.throw(_("The counted cash for this Business Day is zero — nothing to transfer."))

	variance = flt(figures["variance"])
	variance_account = accounts["shortage"] if variance < 0 else accounts["overage"]
	if variance and not variance_account:
		frappe.throw(
			_("The day has a cash {0} of {1} but no {2} account is configured in POS Settings.").format(
				_("shortage") if variance < 0 else _("overage"),
				abs(variance),
				_("Cash Shortage") if variance < 0 else _("Cash Overage"),
			)
		)

	doc = _make_transfer(
		day,
		DRAWER_TO_SAFE,
		accounts["drawer"],
		accounts["branch_safe"],
		figures["counted"],
		expected_amount=figures["expected"],
		variance=variance,
		variance_account=variance_account if variance else None,
		remarks=remarks,
	)
	return {"name": doc.name, "amount": doc.amount, "variance": doc.variance}


@frappe.whitelist()
def transfer_safe_to_master(business_day, amount=None, remarks=None):
	"""Move cash on from the branch safe to the master treasury."""
	_require_transfer_access()
	day = frappe.get_doc("POS Business Day", business_day)
	_assert_closed(day)

	drawer_transfer = _existing_transfer(business_day, DRAWER_TO_SAFE)
	if not drawer_transfer:
		frappe.throw(_("Hand the cashier drawer over to the branch safe first."))

	existing = _existing_transfer(business_day, SAFE_TO_MASTER)
	if existing:
		frappe.throw(
			_("This Business Day's deposit was already sent to the master cash ({0}).").format(existing)
		)

	accounts = resolve_accounts(day.pos_profile, day.company)
	if not accounts["branch_safe"] or not accounts["master"]:
		frappe.throw(_("Branch safe and master cash accounts must both be configured in POS Settings."))

	deposited = flt(frappe.db.get_value("POS Cash Transfer", drawer_transfer, "amount"))
	amount = flt(amount) if amount else deposited
	if amount <= 0:
		frappe.throw(_("Amount to send to the master cash must be greater than zero."))

	available = _account_balance(accounts["branch_safe"], day.company)
	if amount > available:
		frappe.throw(
			_("Cannot send {0}. The branch safe only holds {1}.").format(
				frappe.format_value(amount, {"fieldtype": "Currency"}),
				frappe.format_value(available, {"fieldtype": "Currency"}),
			)
		)

	doc = _make_transfer(
		day,
		SAFE_TO_MASTER,
		accounts["branch_safe"],
		accounts["master"],
		amount,
		remarks=remarks,
	)
	return {"name": doc.name, "amount": doc.amount}
