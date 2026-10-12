# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
Add the Table Service card to the POSNext workspace.

Appends links rather than reinstalling the workspace: a reinstall (as
`v1_7_0.reinstall_workspace` does) deletes the document first, which would
discard any shortcuts or cards a site has added of its own.

Note that `v1_7_0.reinstall_workspace` expects the workspace JSON to be a list
and today's `posnext.json` is an object, so it no longer applies the file - one
more reason this patch does its own, narrower thing.
"""

import frappe

WORKSPACE = "POSNext"

# (label, link_to, link_type, is_query_report)
TABLE_SERVICE_LINKS = [
	("Open Tables", "Open Tables", "Report", 1),
	("Table", "Table", "DocType", 0),
	("POS Table Session", "POS Table Session", "DocType", 0),
	("POS Table Order", "POS Table Order", "DocType", 0),
]

CARD_LABEL = "Table Service"


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

	for label, link_to, link_type, is_query_report in TABLE_SERVICE_LINKS:
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

	_pin_order(doc)

	doc.save(ignore_permissions=True)
	frappe.clear_cache()


def _pin_order(doc):
	"""
	Force the Table Service card and its links to sit together at the end.

	Frappe derives a new row's `idx` from the row count, but this workspace's
	existing links have gaps in theirs (3, 4, 8, 9, 10), so appended rows collide
	with existing ones and the new card gets rendered in the middle of another
	card's links. Renumbering every row sequentially is also what repairs a site
	where that already happened.
	"""
	group_labels = {CARD_LABEL} | {label for label, _lt, _t, _q in TABLE_SERVICE_LINKS}

	others = [row for row in doc.links if row.label not in group_labels]
	group = [row for row in doc.links if row.label in group_labels]

	# Canonical order inside the card: the break first, then the links as listed
	wanted = [CARD_LABEL] + [label for label, _lt, _t, _q in TABLE_SERVICE_LINKS]
	group.sort(key=lambda row: wanted.index(row.label))

	doc.links = others + group
	for position, row in enumerate(doc.links, start=1):
		row.idx = position
