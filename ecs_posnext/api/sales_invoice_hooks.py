# Copyright (c) 2025, BrainWise and contributors
# For license information, please see license.txt

"""
Sales Invoice Hooks
Event handlers for Sales Invoice document events
"""

import frappe
from frappe import _
from frappe.utils import cint

# Items in this class need no kitchen preparation; they are auto-completed.
FRIDGE_ITEM_CLASS = "ثلاجة"


def validate(doc, method=None):
	"""
	Validate hook for Sales Invoice.
	Apply tax inclusive settings based on POS Profile configuration.
	Auto-assign loyalty program to customer if enabled.

	Args:
		doc: Sales Invoice document
		method: Hook method name (unused)
	"""
	apply_tax_inclusive(doc)
	auto_assign_loyalty_program_on_invoice(doc)
	auto_complete_fridge_items(doc)


def auto_complete_fridge_items(doc):
	"""Mark fridge (ثلاجة) items as Completed automatically.

	Fridge items are simply retrieved, not prepared, so they should never sit
	in the kitchen queue. The authoritative class is the Item master's
	custom_item_class (Link field); the row-level Data field is used first and
	backfilled when empty so kitchen screens (which query the row) stay correct.
	"""
	items = doc.get("items") or []
	if not items:
		return

	# Resolve classes from the Item master only for rows missing the row value
	missing = list({
		i.item_code for i in items
		if i.get("item_code") and not i.get("custom_item_class")
	})
	class_map = {}
	if missing:
		for row in frappe.get_all(
			"Item",
			filters={"name": ["in", missing]},
			fields=["name", "custom_item_class"],
		):
			class_map[row.name] = row.custom_item_class

	for item in items:
		item_class = item.get("custom_item_class") or class_map.get(item.item_code)
		if item_class == FRIDGE_ITEM_CLASS:
			# Keep the row-level class in sync (kitchen screens query this field)
			if not item.get("custom_item_class"):
				item.custom_item_class = item_class
			item.custom_item_status = "Completed"


def apply_tax_inclusive(doc):
	"""
	Mark taxes as inclusive based on POS Profile setting.

	This function reads the tax_inclusive setting from POS Settings
	and applies it to all taxes in the invoice (except Actual charge type).

	Args:
		doc: Sales Invoice document
	"""
	if not doc.pos_profile:
		return

	try:
		# Get POS Settings for this profile
		pos_settings = frappe.db.get_value(
			"POS Settings",
			{"pos_profile": doc.pos_profile},
			["tax_inclusive"],
			as_dict=True
		)
		tax_inclusive = pos_settings.get("tax_inclusive", 0) if pos_settings else 0
	except Exception:
		tax_inclusive = 0

	has_changes = False
	for tax in doc.get("taxes", []):
		# Skip Actual charge type - these can't be inclusive
		if tax.charge_type == "Actual":
			if tax.included_in_print_rate:
				tax.included_in_print_rate = 0
				has_changes = True
			continue

		# Apply tax inclusive setting
		if tax_inclusive and not tax.included_in_print_rate:
			tax.included_in_print_rate = 1
			has_changes = True
		elif not tax_inclusive and tax.included_in_print_rate:
			tax.included_in_print_rate = 0
			has_changes = True

	# Recalculate if we made changes
	if has_changes:
		doc.calculate_taxes_and_totals()


def auto_assign_loyalty_program_on_invoice(doc):
	"""
	Auto-assign loyalty program to customer if loyalty is enabled in POS Settings
	but customer doesn't have a loyalty program yet.

	This ensures customers created before loyalty was enabled can still earn points.

	Args:
		doc: Sales Invoice document
	"""
	if not doc.is_pos or not doc.pos_profile or not doc.customer:
		return

	# Check if customer already has a loyalty program
	customer_loyalty = frappe.db.get_value("Customer", doc.customer, "loyalty_program")
	if customer_loyalty:
		return

	# Get POS Settings
	pos_settings = frappe.db.get_value(
		"POS Settings",
		{"pos_profile": doc.pos_profile},
		["enable_loyalty_program", "default_loyalty_program"],
		as_dict=True
	)

	if not pos_settings:
		return

	if not cint(pos_settings.get("enable_loyalty_program")):
		return

	loyalty_program = pos_settings.get("default_loyalty_program")
	if not loyalty_program:
		return

	# Assign loyalty program to customer
	frappe.db.set_value(
		"Customer",
		doc.customer,
		"loyalty_program",
		loyalty_program,
		update_modified=False
	)


def before_cancel(doc, method=None):
	"""
	Before Cancel hook for Sales Invoice.
	Cancel any credit redemption journal entries.

	Args:
		doc: Sales Invoice document
		method: Hook method name (unused)
	"""
	try:
		from ecs_posnext.api.credit_sales import cancel_credit_journal_entries
		cancel_credit_journal_entries(doc.name)
	except Exception as e:
		frappe.log_error(
			title="Credit Sale JE Cancellation Error",
			message=f"Invoice: {doc.name}, Error: {str(e)}\n{frappe.get_traceback()}"
		)
		# Don't block invoice cancellation if JE cancellation fails
		frappe.msgprint(
			_("Warning: Some credit journal entries may not have been cancelled. Please check manually."),
			alert=True,
			indicator="orange"
		)
