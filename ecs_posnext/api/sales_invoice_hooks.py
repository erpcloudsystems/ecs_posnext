# Copyright (c) 2025, BrainWise and contributors
# For license information, please see license.txt

"""
Sales Invoice Hooks
Event handlers for Sales Invoice document events
"""

import frappe
from frappe import _
from frappe.utils import cint


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


def create_payment_entry_on_submit(doc, method=None):
	"""
	Create and submit a Payment Entry for each payment row on POS Sales Invoice submit.
	Skips silently if Payment Entries already exist for this invoice + mode of payment
	(guards against duplicate execution when multiple apps handle the same hook).

	Args:
		doc: Sales Invoice document
		method: Hook method name (unused)
	"""
	try:
		if not doc.is_pos:
			return

		if not doc.payments:
			return

		for payment in doc.payments:
			if not payment.amount or payment.amount <= 0:
				continue

			# Guard: skip if a Payment Entry already exists for this invoice + mode of payment
			existing = frappe.db.exists("Payment Entry", {
				"reference_no": doc.name,
				"mode_of_payment": payment.mode_of_payment,
				"party": doc.customer,
				"docstatus": ["!=", 2]
			})
			if existing:
				continue

			# Resolve the cash/bank account linked to this mode of payment for this company
			paid_to_account = frappe.db.get_value(
				"Mode of Payment Account",
				{"parent": payment.mode_of_payment, "company": doc.company},
				"default_account"
			)

			if not paid_to_account:
				frappe.log_error(
					title="Error : Missing Mode of Payment Account",
					message="No account found for Mode of Payment {} in company {}".format(
						payment.mode_of_payment, doc.company
					)
				)
				continue

			pe = frappe.new_doc("Payment Entry")
			pe.payment_type = "Receive"
			pe.party_type = "Customer"
			pe.party = doc.customer
			pe.company = doc.company
			pe.posting_date = doc.posting_date
			pe.mode_of_payment = payment.mode_of_payment
			pe.paid_from = doc.debit_to
			pe.paid_to = paid_to_account
			pe.paid_amount = payment.amount
			pe.received_amount = payment.amount
			pe.reference_no = doc.name
			pe.reference_date = doc.posting_date

			pe.insert(ignore_permissions=True)
			pe.submit()

	except Exception as e:
		frappe.log_error(
			title="Error creating Payment Entry for Sales Invoice {}".format(doc.name),
			message="{}\n{}".format(str(e), frappe.get_traceback())
		)


def cancel_payment_entries_on_cancel(doc, method=None):
	"""
	Cancel all submitted Payment Entries linked to this POS Sales Invoice.

	Args:
		doc: Sales Invoice document
		method: Hook method name (unused)
	"""
	try:
		if not doc.is_pos:
			return

		pe_list = frappe.get_all(
			"Payment Entry",
			filters={
				"reference_no": doc.name,
				"party": doc.customer,
				"docstatus": 1
			},
			fields=["name"]
		)

		for pe_row in pe_list:
			pe_doc = frappe.get_doc("Payment Entry", pe_row.name)
			pe_doc.cancel()

	except Exception as e:
		frappe.log_error(
			title="Error cancelling Payment Entry for Sales Invoice {}".format(doc.name),
			message="{}\n{}".format(str(e), frappe.get_traceback())
		)
