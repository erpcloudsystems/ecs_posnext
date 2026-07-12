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
	validate_delivery_address(doc)


def validate_delivery_address(doc):
	"""Require a delivery address on POS Delivery orders.

	Frontend enforces this at checkout; this is a defense-in-depth guard for any
	other path (offline sync, imports) so a Delivery invoice can never be saved
	without an address.
	"""
	if not doc.get("is_pos"):
		return
	if (doc.get("custom_order_type") or "") != "Delivery":
		return
	if not (doc.get("customer_address") or doc.get("shipping_address_name")):
		frappe.throw(_("Delivery address is required for delivery orders."))


def _get_cached_pos_settings(pos_profile):
	"""Get POS Settings with per-request cache to avoid repeated DB queries."""
	if not pos_profile:
		return None
	cache_attr = "_pos_settings_hook_cache"
	if not hasattr(frappe.local, cache_attr):
		frappe.local._pos_settings_hook_cache = {}
	if pos_profile in frappe.local._pos_settings_hook_cache:
		return frappe.local._pos_settings_hook_cache[pos_profile]
	try:
		result = frappe.db.get_value(
			"POS Settings",
			{"pos_profile": pos_profile},
			["tax_inclusive", "enable_loyalty_program", "default_loyalty_program"],
			as_dict=True
		)
		frappe.local._pos_settings_hook_cache[pos_profile] = result
		return result
	except Exception:
		return None


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

	pos_settings = _get_cached_pos_settings(doc.pos_profile)
	tax_inclusive = cint(pos_settings.get("tax_inclusive", 0)) if pos_settings else 0

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

	# Get POS Settings (cached per-request)
	pos_settings = _get_cached_pos_settings(doc.pos_profile)

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
	Enqueued as a background job to avoid blocking the POS response (~3-5s savings).
	Skips silently if Payment Entries already exist for this invoice + mode of payment
	(guards against duplicate execution when multiple apps handle the same hook).

	Args:
		doc: Sales Invoice document
		method: Hook method name (unused)
	"""
	if not doc.is_pos:
		return

	if not doc.payments:
		return

	# Collect payment data for background job
	payments_data = []
	for payment in doc.payments:
		if not payment.amount or payment.amount <= 0:
			continue
		payments_data.append({
			"mode_of_payment": payment.mode_of_payment,
			"amount": payment.amount,
		})

	if not payments_data:
		return

	# Enqueue to background job - POS user gets response immediately
	frappe.enqueue(
		_create_payment_entries_background,
		queue="short",
		timeout=120,
		invoice_name=doc.name,
		customer=doc.customer,
		company=doc.company,
		debit_to=doc.debit_to,
		posting_date=str(doc.posting_date),
		payments_data=payments_data,
	)


def _create_payment_entries_background(
	invoice_name, customer, company, debit_to, posting_date, payments_data
):
	"""Background job: create and submit Payment Entries for a POS invoice."""
	try:
		for payment in payments_data:
			mode_of_payment = payment["mode_of_payment"]
			amount = payment["amount"]

			# Guard: skip if a Payment Entry already exists for this invoice + mode of payment
			existing = frappe.db.exists("Payment Entry", {
				"reference_no": invoice_name,
				"mode_of_payment": mode_of_payment,
				"party": customer,
				"docstatus": ["!=", 2]
			})
			if existing:
				continue

			# Resolve the cash/bank account linked to this mode of payment for this company
			paid_to_account = frappe.db.get_value(
				"Mode of Payment Account",
				{"parent": mode_of_payment, "company": company},
				"default_account"
			)

			if not paid_to_account:
				frappe.log_error(
					title="Error : Missing Mode of Payment Account",
					message="No account found for Mode of Payment {} in company {}".format(
						mode_of_payment, company
					)
				)
				continue

			pe = frappe.new_doc("Payment Entry")
			pe.payment_type = "Receive"
			pe.party_type = "Customer"
			pe.party = customer
			pe.company = company
			pe.posting_date = posting_date
			pe.mode_of_payment = mode_of_payment
			pe.paid_from = debit_to
			pe.paid_to = paid_to_account
			pe.paid_amount = amount
			pe.received_amount = amount
			pe.reference_no = invoice_name
			pe.reference_date = posting_date

			pe.insert(ignore_permissions=True)
			pe.submit()

		frappe.db.commit()
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(
			title="Error creating Payment Entry for Sales Invoice {}".format(invoice_name),
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
