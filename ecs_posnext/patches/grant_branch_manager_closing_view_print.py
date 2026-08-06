# Copyright (c) 2026, ECS and contributors
"""Let Branch Managers VIEW + PRINT closing records (POS Cashier Shift Closing and POS
Business Day) from the desk. Printing is further restricted to within the record's own
business day by the before_print guard (ecs_posnext.api.closing_print_guard)."""

import frappe
from frappe.permissions import add_permission, update_permission_property

ROLES = ("Bransh Manager", "POSNext Branch Manager")
DOCTYPES = ("POS Cashier Shift Closing", "POS Business Day")


def execute():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			continue
		for dt in DOCTYPES:
			if not frappe.db.exists("DocType", dt):
				continue
			add_permission(dt, role, 0)
			for right in ("read", "print"):
				update_permission_property(dt, role, 0, right, 1)
	frappe.db.commit()
