# -*- coding: utf-8 -*-
# Copyright (c) 2024, POS Next and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def validate_item(doc, method):
	"""
	Validate Item doctype
	- Allow items with or without company
	- Items without company are treated as global items (available to all companies)
	- Explicitly set custom_company to empty string for new global items
	"""
	# Only set custom_company for new items, don't modify existing items
	if doc.is_new():
		if not doc.get("custom_company"):
			doc.custom_company = ""

	sync_expense_account_from_custom_set_account(doc)


def sync_expense_account_from_custom_set_account(doc):
	"""
	Keep Item Defaults > Expense Account in sync with the custom_set_account field.
	Whenever custom_set_account is set/changed, push its value into expense_account
	on the matching (or first available) Item Defaults row, creating a row if none exists.
	"""
	if not doc.has_value_changed("custom_set_account"):
		return

	company = frappe.defaults.get_global_default("company")
	row = None
	for item_default in doc.item_defaults:
		if company and item_default.company == company:
			row = item_default
			break

	if not row:
		row = doc.item_defaults[0] if doc.item_defaults else doc.append("item_defaults", {})

	if not row.company:
		row.company = company

	row.expense_account = doc.custom_set_account


@frappe.whitelist()
def item_query(doctype, txt, searchfield, start, page_len, filters):
	"""
	Custom query to filter items by company
	- If company is specified in filters, show:
	  1. Items belonging to that company
	  2. Global items (where custom_company is empty)
	- If no company specified, show all items
	"""
	import json

	# Parse filters if it's a string (when called from frontend)
	if isinstance(filters, str):
		filters = json.loads(filters)

	conditions = ["disabled = 0"]
	values = []

	if txt:
		conditions.append(f"({searchfield} LIKE %s OR item_name LIKE %s)")
		values.extend([f"%{txt}%", f"%{txt}%"])

	company = filters.get("company") if filters else None

	if company:
		# Show items for specific company + global items
		conditions.append("(custom_company = %s OR custom_company IS NULL OR custom_company = '')")
		values.append(company)

	query = f"""
		SELECT name, item_name, item_group
		FROM `tabItem`
		WHERE {' AND '.join(conditions)}
		ORDER BY
			CASE WHEN name LIKE %s THEN 0 ELSE 1 END,
			item_name
		LIMIT %s, %s
	"""

	values.extend([f"{txt}%", start, page_len])

	return frappe.db.sql(query, values)
