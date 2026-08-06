# -*- coding: utf-8 -*-
# Booking creation for the POS 'Build' product catalog page.
#
# Mirrors the fields captured by ecs_vim's website booking flow (branch, room,
# visit date, phone, weekday/weekend UOM pricing, slot) but creates the
# reservation Sales Order directly instead of going through the website's
# session-scoped Quotation cart (erpnext.e_commerce's _get_cart_quotation only
# returns an EXISTING draft cart or None - it does not auto-create one, so it
# isn't safe to reuse for a POS session that isn't a single customer's browsing
# session).
#
# Branch/Room: ecs_vim books against a "Dimension Branch" (the actual bookable
# unit - a room, or a whole-branch catch-all), each tagged with a standard
# "Branch" (the physical location) via its own `branch` field. The POS shows a
# Branch -> Room cascade (ecs_vim.get_branch_list_based) and submits the
# selected Room's Dimension Branch name as the reservation's branch.
#
# The resulting Sales Order carries the same fields ecs_vim's place_order() sets
# (branch/custom_branch, delivery_date, select_event/select_slot, no_of_entries -
# the latter three derived by ecs_vim's own Sales Order validate() hook from the
# first item row) and defaults pos_status to "Open", so
# ecs_posnext.api.reservations can find and close it at the register exactly
# like a web-booked reservation.

import json

import frappe
from frappe import _
from frappe.utils import flt, nowdate

from ecs_posnext.api.items import BUILD_CATALOG_ROLE


def _ensure_build_access():
	if BUILD_CATALOG_ROLE not in frappe.get_roles():
		frappe.throw(_("Not permitted to access the product catalog"), frappe.PermissionError)


def _resolve_company():
	company = frappe.defaults.get_global_default("company")
	if company:
		return company
	return frappe.db.get_value("Company", {}, "name")


def _default_price_list():
	return frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"


def _resolve_rate_for_uom(item_code, uom, price_list):
	"""Numeric price for (item_code, uom), mirroring ecs_vim.api.get_price's logic
	(exact per-uom Item Price row, else the item's base rate * UOM conversion
	factor) but returning a plain number instead of a formatted HTML string."""
	if not uom:
		return frappe.db.get_value(
			"Item Price", {"item_code": item_code, "price_list": price_list, "selling": 1}, "price_list_rate"
		) or 0

	exact = frappe.db.get_value(
		"Item Price",
		{"item_code": item_code, "uom": uom, "price_list": price_list, "selling": 1},
		"price_list_rate",
	)
	if exact:
		return exact

	base_rate = (
		frappe.db.get_value(
			"Item Price", {"item_code": item_code, "price_list": price_list, "selling": 1}, "price_list_rate"
		)
		or 0
	)
	conversion_factor = (
		frappe.db.get_value("UOM Conversion Detail", {"parent": item_code, "uom": uom}, "conversion_factor") or 1
	)
	return base_rate * conversion_factor


@frappe.whitelist()
def get_booking_options(item_code):
	"""Branch/UOM options + included items needed to book item_code."""
	_ensure_build_access()

	item = frappe.db.get_value(
		"Item",
		item_code,
		[
			"item_name",
			"non_sharable_slot",
			"applicable_for",
			"sales_uom",
			"stock_uom",
			"dimension_brand",
			"minimum_sales_quantity",
		],
		as_dict=True,
	)
	if not item:
		frappe.throw(_("Item not found"), frappe.DoesNotExistError)

	# Simple add-ons (e.g. "Party Additions" like Additional Backdrop) have no
	# dimension_brand and aren't tied to a specific branch/room/visit date - they
	# just attach to whatever reservation is already being built, so skip the
	# branch/room selection for them entirely rather than showing every branch
	# across every brand unfiltered.
	requires_booking = bool(item.dimension_brand)
	parent_branches = []
	if requires_booking:
		parent_branches = frappe.get_all(
			"Dimension Branch", filters={"brand": item.dimension_brand}, pluck="branch", distinct=True
		)
		parent_branches = sorted({b for b in parent_branches if b})

	price_list = _default_price_list()
	currency = frappe.db.get_value("Price List", price_list, "currency") or "SAR"

	item_doc = frappe.get_cached_doc("Item", item_code)
	uoms = []
	seen_uoms = set()
	for row in item_doc.uoms:
		if row.uom in seen_uoms:
			continue
		seen_uoms.add(row.uom)
		uoms.append({"uom": row.uom, "rate": _resolve_rate_for_uom(item_code, row.uom, price_list)})
	if not uoms:
		base_uom = item.sales_uom or item.stock_uom
		uoms = [{"uom": base_uom, "rate": _resolve_rate_for_uom(item_code, base_uom, price_list)}]

	bundle_name = frappe.db.get_value("Product Bundle", {"new_item_code": item_code}, "name")
	bundle_items = []
	if bundle_name:
		bundle_items = frappe.get_all(
			"Product Bundle Item",
			filters={"parent": bundle_name},
			fields=["item_code", "qty", "uom"],
			order_by="idx",
		)
		item_names = frappe.get_all(
			"Item",
			filters={"name": ["in", [row["item_code"] for row in bundle_items]]},
			fields=["name", "item_name"],
		)
		item_name_map = {row["name"]: row["item_name"] for row in item_names}
		for row in bundle_items:
			row["item_name"] = item_name_map.get(row["item_code"])

	return {
		"item_name": item.item_name,
		"requires_booking": requires_booking,
		"parent_branches": parent_branches,
		"non_sharable_slot": bool(item.non_sharable_slot),
		"applicable_for": item.applicable_for,
		"uoms": uoms,
		"currency": currency,
		"bundle_items": bundle_items,
		"minimum_sales_quantity": flt(item.minimum_sales_quantity) or 1,
	}


@frappe.whitelist()
def get_rooms(item_code, parent_branch):
	"""Dimension Branch rooms (incl. the whole-branch catch-all) under a physical
	Branch, for the Branch -> Room cascade. Mirrors ecs_vim.get_branch_list_based."""
	_ensure_build_access()

	brand = frappe.db.get_value("Item", item_code, "dimension_brand")
	filters = {"branch": parent_branch}
	if brand:
		filters["brand"] = brand

	return frappe.get_all(
		"Dimension Branch",
		filters=filters,
		fields=["name", "is_group"],
		order_by="is_group desc, name asc",
	)


@frappe.whitelist()
def get_slots(item_code, visit_date, branch=None):
	"""Available booking slots for a slot-based (non_sharable_slot) item, reusing
	ecs_vim's own slot-availability logic so it stays consistent with the website."""
	_ensure_build_access()
	from ecs_vim.api import vim_get_slot_list

	return vim_get_slot_list(item_code=item_code, visit_date=visit_date, branch=branch)


@frappe.whitelist()
def lookup_customer_by_phone(phone):
	_ensure_build_access()
	return frappe.db.get_value(
		"Customer", {"mobile_no": phone, "disabled": 0}, ["name", "customer_name"], as_dict=True
	)


def _resolve_or_create_customer(phone, customer_name):
	customer = frappe.db.get_value("Customer", {"mobile_no": phone, "disabled": 0}, "name")
	if customer:
		return customer

	if not customer_name:
		frappe.throw(_("No customer found for {0}. Provide a name to create one.").format(phone))

	# Built directly (rather than via ecs_posnext.api.customers.create_customer)
	# since this site's Customer doctype has first_name/last_name as mandatory
	# custom fields, which that shared helper does not set.
	name_parts = customer_name.strip().split(" ", 1)
	customer_doc = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": customer_name,
			"customer_type": "Individual",
			"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "Individual",
			"territory": "All Territories",
			"mobile_no": phone,
			"first_name": name_parts[0],
			"last_name": name_parts[1] if len(name_parts) > 1 else name_parts[0],
		}
	)
	customer_doc.flags.ignore_permissions = True
	customer_doc.insert()
	return customer_doc.name


@frappe.whitelist()
def validate_build_coupon(coupon_code, phone=None):
	"""Validate a POS Coupon for the Build page's "Review & Book" checkout.

	Resolves the customer from `phone` (same lookup create_booking itself uses)
	so a coupon restricted to a specific customer validates correctly even
	though the actual Customer record may not exist yet for a new phone
	number - reuses ecs_posnext.api.offers.validate_coupon (the same endpoint
	the main POS cart's coupon dialog calls) so both surfaces enforce the same
	rules.
	"""
	_ensure_build_access()
	from ecs_posnext.api.offers import validate_coupon

	customer = None
	if phone:
		customer = frappe.db.get_value("Customer", {"mobile_no": phone, "disabled": 0}, "name")

	return validate_coupon(coupon_code=coupon_code, customer=customer, company=_resolve_company())


@frappe.whitelist()
def create_booking(items, branch, visit_date, phone, customer_name=None, coupon_code=None, discount_amount=0):
	"""Create a party-reservation Sales Order directly from the POS Build page.

	`items` is a JSON list of {item_code, qty, uom, slot} - the main package plus
	any additional add-on items the cashier attached to the same reservation.
	`branch` is the selected Dimension Branch (room, or whole-branch catch-all).
	`coupon_code`/`discount_amount`: same trust model as invoices.py's
	update_invoice() - the frontend computes discount_amount from the coupon's
	discount_type/percentage/amount (via the same calculateDiscountAmount
	helper the main POS cart uses), and the server only re-validates the code
	itself before accepting the client-supplied amount.
	"""
	_ensure_build_access()
	from ecs_vim.api import check_available

	if isinstance(items, str):
		items = json.loads(items)
	if not items:
		frappe.throw(_("Add at least one item to the reservation"))
	if not phone:
		frappe.throw(_("Customer phone number is required"))
	if not branch:
		frappe.throw(_("Branch is required"))
	if not visit_date:
		frappe.throw(_("Visit date is required"))

	customer = _resolve_or_create_customer(phone, customer_name)

	coupon_doc = None
	if coupon_code:
		from ecs_posnext.api.offers import validate_coupon

		validation = validate_coupon(coupon_code=coupon_code, customer=customer, company=_resolve_company())
		if not validation.get("valid"):
			frappe.throw(validation.get("message") or _("Invalid coupon code"))
		coupon_doc = validation.get("coupon")

	price_list = _default_price_list()
	warehouse = frappe.db.get_value("Dimension Branch", branch, "default_warehouse")

	item_rows = []
	for entry in items:
		item_code = entry["item_code"]
		item_doc = frappe.db.get_value(
			"Item", item_code, ["item_name", "non_sharable_slot", "minimum_sales_quantity"], as_dict=True
		)
		if not item_doc:
			frappe.throw(_("Item {0} not found").format(item_code))

		# Same weekday/weekend + block-date validation the website applies before booking.
		check_available(item_code=item_code, visit_date=visit_date, branch=branch)

		qty = flt(entry.get("qty")) or 1
		min_qty = flt(item_doc.minimum_sales_quantity)
		if min_qty and qty < min_qty:
			qty = min_qty
		uom = entry.get("uom")
		row = {
			"item_code": item_code,
			"item_name": item_doc.item_name,
			"qty": qty,
			"rate": _resolve_rate_for_uom(item_code, uom, price_list),
			"delivery_date": visit_date,
			"warehouse": warehouse,
		}
		if uom:
			row["uom"] = uom
		if item_doc.non_sharable_slot and entry.get("slot"):
			row["slot_name"] = entry["slot"]
		item_rows.append(row)

	so_dict = {
		"doctype": "Sales Order",
		"customer": customer,
		"company": _resolve_company(),
		"transaction_date": nowdate(),
		"delivery_date": visit_date,
		"branch": branch,
		"custom_branch": branch,
		"set_warehouse": warehouse,
		"items": item_rows,
	}

	discount_amount = flt(discount_amount)
	if coupon_code and discount_amount > 0:
		so_dict["coupon_code"] = coupon_code
		so_dict["apply_discount_on"] = (coupon_doc or {}).get("apply_on") or "Grand Total"
		so_dict["discount_amount"] = discount_amount

	so = frappe.get_doc(so_dict)

	so.flags.ignore_permissions = True
	so.insert()

	if coupon_code and frappe.db.table_exists("POS Coupon"):
		try:
			from ecs_posnext.pos_next.doctype.pos_coupon.pos_coupon import increment_coupon_usage
			increment_coupon_usage(coupon_code)
		except Exception as e:
			frappe.log_error(
				title="Failed to increment coupon usage",
				message=f"Coupon: {coupon_code}, Error: {str(e)}"
			)

	# Whole-branch bookings of certain packages (see ecs_vim's
	# check_submit_permissions) may only be submitted by that branch's manager -
	# other users get blocked there and the manager is emailed for approval, exactly
	# like ecs_vim's own place_order(), which submits best-effort and swallows this.
	submitted = True
	try:
		so.submit()
	except Exception:
		frappe.clear_last_message()
		submitted = False

	return {"sales_order": so.name, "customer": customer, "submitted": submitted}
