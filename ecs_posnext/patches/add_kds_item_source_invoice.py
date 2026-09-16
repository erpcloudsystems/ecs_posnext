# Copyright (c) 2026, ECS and contributors
"""KDS Order Item.source_invoice — which invoice each ticket row came from.

Needed so a supplement invoice's rows can be recognised on the original order's ticket:
merging is skipped when its rows are already there (no duplicated items), and cancelling
the supplement pulls exactly its rows back off the ticket.

Existing rows are backfilled with their ticket's own invoice; rows flagged `is_addition`
predate the tracking and are left blank (their source invoice is not recoverable).
"""

import frappe


def execute():
	frappe.reload_doc("pos_next", "doctype", "kds_order_item")
	frappe.db.sql(
		"""
		UPDATE `tabKDS Order Item` koi
		JOIN `tabKDS Order` ko ON ko.name = koi.parent
		SET koi.source_invoice = ko.sales_invoice
		WHERE (koi.source_invoice IS NULL OR koi.source_invoice = '')
		  AND IFNULL(koi.is_addition, 0) = 0
		"""
	)
	frappe.db.commit()
