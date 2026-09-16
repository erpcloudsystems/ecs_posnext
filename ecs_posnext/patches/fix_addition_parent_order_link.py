# Copyright (c) 2026, ECS and contributors
"""Re-point supplement invoices that were linked to the wrong original order.

`custom_parent_order` used to be resolved from the human order label (M-50). Those
labels cycle per branch, so the same label exists in several branches on the same day
and the lookup picked an arbitrary match — additions were linked to another branch's
order, and the KDS merged their items onto that kitchen's ticket.

`custom_parent_invoice` always holds the docname the cashier actually pressed "+" on,
so it is authoritative. This repoints every disagreeing row to the root of that chain.

Kitchen tickets are not rewritten: the affected orders are long finished, and moving
rows between historical tickets would only rewrite the record of what was cooked.
"""

import frappe


def execute():
	broken = frappe.db.sql(
		"""
		SELECT sup.name, sup.custom_parent_invoice, sup.custom_parent_order
		FROM `tabSales Invoice` sup
		WHERE sup.custom_parent_invoice IS NOT NULL
		  AND sup.custom_parent_invoice != ''
		  AND IFNULL(sup.custom_parent_order, '') != sup.custom_parent_invoice
		""",
		as_dict=True,
	)
	fixed = 0
	for row in broken:
		root = (
			frappe.db.get_value("Sales Invoice", row.custom_parent_invoice, "custom_parent_order")
			or row.custom_parent_invoice
		)
		if root == row.custom_parent_order:
			continue
		frappe.db.set_value(
			"Sales Invoice", row.name, "custom_parent_order", root, update_modified=False
		)
		fixed += 1

	if fixed:
		frappe.db.commit()
