# Copyright (c) 2025, BrainWise and contributors
# For license information, please see license.txt

"""
Sales Invoice Hooks
Event handlers for Sales Invoice document events
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, today


def before_insert(doc, method=None):
	"""
	Before Insert hook for Sales Invoice.
	Auto-enable "Update Stock" when the invoice is being created against a Sales Order,
	so stock is reduced directly on the invoice instead of requiring a separate Delivery Note.

	Args:
		doc: Sales Invoice document
		method: Hook method name (unused)
	"""
	if doc.get("is_return"):
		return

	if any(item.get("sales_order") for item in doc.get("items", [])):
		doc.update_stock = 1


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
	apply_bundle_selections(doc)


def apply_bundle_selections(doc):
	"""Honor per-bundle component choices made at the POS.

	ERPNext's make_packing_list() (run during core validate, before this hook) resets
	and rebuilds packed_items from the FULL Product Bundle. For configurable bundles the
	cashier may have chosen only a SUBSET of components; posa_bundle_selections holds
	{bundle_item_code: [chosen component item_codes]}. Here we drop the packed_items
	rows whose (parent_item, item_code) component was not chosen. Bundles with no entry
	are left untouched (full bundle / default behavior).
	"""
	if not doc.get("packed_items"):
		return

	import json

	selections = {}
	raw = doc.get("posa_bundle_selections")
	if raw:
		try:
			parsed = json.loads(raw) if isinstance(raw, str) else raw
			if isinstance(parsed, dict):
				selections = parsed
		except Exception:
			selections = {}

	# Drop packed rows whose component was NOT chosen (only for bundles with an
	# explicit selection list; bundles without an entry keep all their components).
	kept = []
	for row in doc.packed_items:
		chosen = selections.get(row.parent_item)
		if chosen is None or row.item_code in chosen:
			kept.append(row)
	doc.packed_items = kept

	# Mirror the packed components into the "Selected Packed Items" table(s) so they
	# are visible on the Sales Invoice (parity with posawesome's seleceted_packed_items).
	selected_rows = [
		{
			"parent_item": r.parent_item,
			"item_code": r.item_code,
			"qty": r.qty,
			"quantity": r.qty,
			"packed_quantity": r.qty,
		}
		for r in kept
	]
	for fieldname in ("seleceted_packed_items", "custom_selected_packed_items"):
		if doc.meta.has_field(fieldname):
			doc.set(fieldname, selected_rows)


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


def restore_coupon_usage_on_cancel(doc, method=None):
	"""
	Restore POS Coupon usage when a Sales Invoice that redeemed one is cancelled.
	For Gift Cards this puts the redeemed amount back into the card's remaining
	balance so it can be used again.

	Args:
		doc: Sales Invoice document
		method: Hook method name (unused)
	"""
	coupon_code = doc.get("coupon_code")
	if not coupon_code:
		return

	if not frappe.db.table_exists("POS Coupon"):
		return

	try:
		from ecs_posnext.pos_next.doctype.pos_coupon.pos_coupon import decrement_coupon_usage
		decrement_coupon_usage(coupon_code, doc.discount_amount)
	except Exception as e:
		frappe.log_error(
			title="Coupon Usage Restore Failed",
			message=f"Invoice: {doc.name}, Coupon: {coupon_code}, Error: {str(e)}"
		)


def create_gift_card_coupons(doc, method=None):
	"""
	Auto-create a Gift Card POS Coupon for each Gift Card item sold on this invoice.

	One coupon is created per invoice line whose Item belongs to the "Gift Card"
	Item Group, valued at the line's full amount (rate x qty) and assigned to the
	invoice's customer, so the customer can redeem it on a future purchase.

	Args:
		doc: Sales Invoice document
		method: Hook method name (unused)
	"""
	if not frappe.db.table_exists("POS Coupon"):
		return

	if not doc.customer:
		return

	for item in doc.get("items", []):
		item_group = frappe.db.get_value("Item", item.item_code, "item_group")
		if item_group != "Gift Card":
			continue

		amount = flt(item.amount)
		if amount <= 0:
			continue

		try:
			coupon = frappe.new_doc("POS Coupon")
			coupon.coupon_name = f"{item.item_name} Gift Card ({doc.name}/{item.idx})"
			coupon.coupon_type = "Gift Card"
			coupon.customer = doc.customer
			coupon.company = doc.company
			coupon.discount_type = "Amount"
			coupon.discount_amount = amount
			coupon.apply_on = "Grand Total"
			coupon.valid_from = today()
			coupon.insert(ignore_permissions=True)
			send_gift_card_coupon_sms(coupon, doc.customer)
		except Exception as e:
			frappe.log_error(
				title="Gift Card Coupon Creation Failed",
				message=f"Invoice: {doc.name}, Item: {item.item_code}, Error: {str(e)}\n{frappe.get_traceback()}"
			)


def send_gift_card_coupon_sms(coupon, customer):
	"""
	Text the newly issued Gift Card's redeem code to the customer.
	Failure to send doesn't affect coupon creation or invoice submission.

	Args:
		coupon: newly inserted POS Coupon document (type Gift Card)
		customer: Customer this coupon was issued to
	"""
	mobile = frappe.db.get_value("Customer", customer, "mobile_no")
	if not mobile:
		return

	try:
		from ecs_vim.sms.send_sms import send_sms

		send_sms(
			_("Your Gift Card code is {0}, worth {1}. Present it on your next visit to redeem it.").format(
				coupon.coupon_code, frappe.format_value(coupon.balance_amount, {"fieldtype": "Currency"})
			),
			mobile,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Gift Card Coupon SMS Send Error")


def disable_gift_card_coupons_on_cancel(doc, method=None):
	"""
	Disable any Gift Card POS Coupons that were auto-created from this invoice when
	it gets cancelled, so a reversed sale can no longer be redeemed. Coupons that
	were already partly or fully used are disabled too, but flagged with a warning
	since their redemption can't be undone here.

	Args:
		doc: Sales Invoice document
		method: Hook method name (unused)
	"""
	if not frappe.db.table_exists("POS Coupon"):
		return

	coupons = frappe.get_all(
		"POS Coupon",
		filters={"coupon_name": ["like", f"%({doc.name}/%"]},
		fields=["name", "used", "balance_amount", "discount_amount"]
	)

	for row in coupons:
		if row.used or flt(row.balance_amount) != flt(row.discount_amount):
			frappe.msgprint(
				_("Gift Card coupon {0} from this invoice was already used and has only been disabled, not removed.").format(row.name),
				alert=True,
				indicator="orange"
			)
		frappe.db.set_value("POS Coupon", row.name, "disabled", 1)


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
