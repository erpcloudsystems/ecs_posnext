# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
Add the Reports card, holding POS Sales Detail, to the POSNext workspace.

Appends rather than reinstalling the workspace, for the same reason
`v1_16_0.add_table_service_workspace_links` does: a reinstall deletes the
document first and would discard anything a site added itself.
"""

import frappe

WORKSPACE = "POSNext"
CARD_LABEL = "Reports"

# (label, link_to, link_type, is_query_report)
REPORT_LINKS = [
	("POS Sales Detail", "POS Sales Detail", "Report", 1),
]


def execute():
	if not frappe.db.exists("Workspace", WORKSPACE):
		# Nothing to patch - a fresh install picks the links up from the JSON
		return

	doc = frappe.get_doc("Workspace", WORKSPACE)
	existing = {row.label for row in doc.links}

	if CARD_LABEL not in existing:
		doc.append("links", {
			"type": "Card Break",
			"label": CARD_LABEL,
			"hidden": 0,
			"onboard": 0,
			"link_count": 0,
		})

	for label, link_to, link_type, is_query_report in REPORT_LINKS:
		if label in existing:
			continue
		doc.append("links", {
			"type": "Link",
			"label": label,
			"link_to": link_to,
			"link_type": link_type,
			"is_query_report": is_query_report,
			"hidden": 0,
			"onboard": 0,
			"link_count": 0,
		})

	# Renumbering keeps the appended card whole: Frappe derives a new row's `idx`
	# from the row count, which collides with the gaps this workspace's older
	# rows carry, scattering the new links through another card.
	for position, row in enumerate(doc.links, start=1):
		row.idx = position

	doc.save(ignore_permissions=True)
	frappe.clear_cache()
