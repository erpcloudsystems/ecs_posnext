# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Create the POS Business Day roles and grant permissions on the new doctypes.

Idempotent — safe to re-run.
"""

import frappe
from frappe.permissions import add_permission, update_permission_property

ROLES = ["POSNext Supervisor", "POSNext Branch Manager", "POSNext Operations Manager"]


def execute():
	_ensure_roles()
	_grant_permissions()
	frappe.db.commit()


def _ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def _perm(doctype, role, permlevel=0, rights=None):
	add_permission(doctype, role, permlevel)
	for right in rights or []:
		update_permission_property(doctype, role, permlevel, right, 1)


def _grant_permissions():
	# Supervisor — opens/closes cashier shifts, enters actual cash, sees differences
	_perm("POS Cashier Shift", "POSNext Supervisor", 0, ["read", "write", "create"])
	_perm("POS Cashier Shift Closing", "POSNext Supervisor", 0, ["read", "write", "create", "submit"])
	_perm("POS Cashier Shift Closing", "POSNext Supervisor", 1, ["read", "write"])
	_perm("POS Business Day", "POSNext Supervisor", 0, ["read"])
	_perm("POS Audit Log", "POSNext Supervisor", 0, ["read"])

	# Branch Manager — reviews closings, approves differences, closes Business Day
	for dt in ("POS Cashier Shift", "POS Cashier Shift Closing", "POS Business Day"):
		_perm(dt, "POSNext Branch Manager", 0, ["read", "write", "create", "submit", "cancel"])
	_perm("POS Cashier Shift Closing", "POSNext Branch Manager", 1, ["read", "write"])
	_perm("POS Audit Log", "POSNext Branch Manager", 0, ["read"])

	# Operations Manager — all branches, override
	for dt in ("POS Cashier Shift", "POS Cashier Shift Closing", "POS Business Day", "POS Audit Log"):
		_perm(dt, "POSNext Operations Manager", 0, ["read", "write", "create", "submit", "cancel", "delete"])
	_perm("POS Cashier Shift Closing", "POSNext Operations Manager", 1, ["read", "write"])
