# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Make Branch an accounting dimension.

Branch expenses are posted from the branch safe, so every one of their ledger
entries belongs to a branch. ERPNext carries that on the voucher only if `Branch`
is registered as an Accounting Dimension — registering it creates the `branch`
field on Journal Entry Account (and the other dimension-aware doctypes), which is
what `POS Branch Expense` fills in when it posts.

Idempotent: an existing dimension — even one an accountant has disabled on
purpose — is left exactly as it is.
"""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Branch"):
		return
	if frappe.db.exists("Accounting Dimension", {"document_type": "Branch"}):
		return

	doc = frappe.get_doc({"doctype": "Accounting Dimension", "document_type": "Branch"})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
