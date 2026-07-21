"""
Item Manager API — Backend endpoints for the Desk Item Manager page.

Provides APIs for:
- Creating simple (quick-sell) items
- Creating template items with variants
- Creating combo/Product Bundle items
- Fetching item groups, attributes, and UOMs
"""

import json
import frappe
from frappe import _
from frappe.utils import flt


# =============================================================================
# READ helpers
# =============================================================================

@frappe.whitelist()
def get_item_groups():
	"""Return all non-disabled Item Groups for the group selector."""
	return frappe.get_all(
		"Item Group",
		filters={"is_group": 0},
		fields=["name", "parent_item_group", "image"],
		order_by="name asc",
		limit_page_length=0,
	)


@frappe.whitelist()
def get_uoms():
	"""Return all enabled UOMs."""
	return frappe.get_all(
		"UOM",
		filters={"enabled": 1},
		fields=["name"],
		order_by="name asc",
		limit_page_length=0,
	)


@frappe.whitelist()
def get_item_attributes():
	"""Return all Item Attributes with their values in 2 queries (no N+1)."""
	attributes = frappe.get_all(
		"Item Attribute",
		fields=["name", "attribute_name"],
		order_by="attribute_name asc",
		limit_page_length=0,
	)
	if not attributes:
		return attributes

	attr_names = [a["name"] for a in attributes]
	all_values = frappe.get_all(
		"Item Attribute Value",
		filters=[["parent", "in", attr_names]],
		fields=["parent", "attribute_value", "abbr"],
		order_by="parent asc, idx asc",
		limit_page_length=0,
	)
	values_map = {}
	for v in all_values:
		values_map.setdefault(v["parent"], []).append(v)

	for attr in attributes:
		attr["values"] = values_map.get(attr["name"], [])

	return attributes


# =============================================================================
# WRITE bulk helpers
# =============================================================================

@frappe.whitelist()
def bulk_create_variants(template_code, variants, template_name="", template_name_arabic="", item_group=""):
	"""
	Enqueue creation of variant Items in a background job.
	Returns immediately with {queued: true}.
	Sends realtime event 'variants_save_done' to the requesting user when complete.

	Each entry in `variants` may carry a `prices` list of {price_list, price} —
	that variant's own rates. There is no template-level price list.
	"""
	if isinstance(variants, str):
		variants = json.loads(variants)

	user = frappe.session.user
	frappe.enqueue(
		"ecs_posnext.api.item_manager._do_create_variants_job",
		queue="long",
		timeout=600,
		user=user,
		template_code=template_code,
		variants=variants,
		template_name=template_name,
		template_name_arabic=template_name_arabic,
		item_group=item_group,
	)
	return {"queued": True}


def _do_create_variants_job(user, template_code, variants, template_name="", template_name_arabic="", item_group=""):
	"""
	Background worker: create variant Items + upsert prices, then notify frontend.
	"""
	try:
		# --- 1. Create new variant Items ---
		requested_codes = [v["item_code"] for v in variants if v.get("item_code")]
		# Codes that already exist in the DB *before* this batch — genuine
		# re-saves that we skip.
		db_existing = set()
		if requested_codes:
			rows = frappe.get_all(
				"Item",
				filters=[["item_code", "in", requested_codes]],
				fields=["item_code", "variant_of"],
				limit_page_length=0,
			)
			for r in rows:
				db_existing.add(r["item_code"])

		created = []
		skipped = []
		used = set()  # codes already consumed within this batch
		seen_attr_sigs = set()  # attribute combinations already handled this batch

		def _attr_sig(attr_list):
			# A stable signature for an attribute combination. ERPNext forbids
			# two variants of one template having the same attribute values.
			return tuple(sorted(
				(str(a.get("attribute")), str(a.get("value"))) for a in attr_list
			))

		for v in variants:
			code = (v.get("item_code") or "").strip()
			if not code:
				continue

			attrs = v.get("attributes") or []
			# Skip combinations that repeat within this batch — they would be
			# rejected by ERPNext as duplicate variants anyway.
			sig = _attr_sig(attrs)
			if sig in seen_attr_sigs:
				skipped.append(code)
				continue
			seen_attr_sigs.add(sig)

			# Already in the DB by code → genuine duplicate variant, skip it.
			if code in db_existing:
				skipped.append(code)
				continue
			# Disambiguate code collisions *within this batch*. Arabic attribute
			# values often truncate to the same client-generated code, which
			# previously caused all-but-one of them to be silently dropped.
			# Append a numeric suffix so every distinct variant is created.
			base_code = code
			suffix = 1
			while code in used or code in db_existing:
				code = f"{base_code}-{suffix}"
				suffix += 1
			used.add(code)

			v_name = v.get("name", code)
			doc = frappe.get_doc({
				"doctype": "Item",
				"item_code": code,
				"item_name": f"{template_name} - {v_name}" if template_name else code,
				"custom_item_name_arabic": f"{template_name_arabic} - {v_name}" if template_name_arabic else "",
				"item_group": item_group,
				"variant_of": template_code,
				"standard_rate": flt(v.get("price", 0)),
				"is_stock_item": 0,
				"stock_uom": "Unit",
				"attributes": [
					{"attribute": a["attribute"], "attribute_value": a["value"]}
					for a in attrs
				],
			})
			# A variant with this attribute combination may already exist in the
			# DB under a different code (ItemVariantExistsError), or be otherwise
			# invalid. Isolate each insert with a savepoint so a single failure
			# skips just that variant instead of aborting the whole batch.
			frappe.db.savepoint("variant_insert")
			try:
				doc.insert(ignore_permissions=True)
			except frappe.ValidationError:
				frappe.db.rollback(save_point="variant_insert")
				used.discard(code)
				skipped.append(code)
				continue
			created.append({"original": v["item_code"], "created": code})

		frappe.db.commit()

		# --- 2. Upsert Item Prices for newly created variants ---
		# Each variant carries its OWN per-price-list rates (set in the editor's
		# per-variant prices dialog). A variant is only priced on the lists it
		# was actually given — no list is filled in by default.
		if created:
			code_map = {c["original"]: c["created"] for c in created}
			created_originals = {c["original"] for c in created}
			price_entries = []
			for v in variants:
				if v["item_code"] not in created_originals:
					continue
				final_code = code_map[v["item_code"]]
				for p in (v.get("prices") or []):
					if not p.get("price_list"):
						continue
					price_entries.append({
						"item_code": final_code,
						"price_list": p["price_list"],
						"price": flt(p.get("price") or 0),
					})

			if price_entries:
				item_codes = list({e["item_code"] for e in price_entries})
				existing_prices = frappe.get_all(
					"Item Price",
					filters=[["item_code", "in", item_codes], ["selling", "=", 1]],
					fields=["name", "item_code", "price_list", "price_list_rate"],
					limit_page_length=0,
				)
				ep_map = {(r["item_code"], r["price_list"]): r for r in existing_prices}
				now_dt = frappe.utils.now()
				for entry in price_entries:
					key = (entry["item_code"], entry["price_list"])
					if key in ep_map:
						frappe.db.sql(
							"UPDATE `tabItem Price` SET price_list_rate=%s, modified=%s WHERE name=%s",
							(entry["price"], now_dt, ep_map[key]["name"]),
						)
					else:
						ip = frappe.get_doc({
							"doctype": "Item Price",
							"item_code": entry["item_code"],
							"price_list": entry["price_list"],
							"price_list_rate": entry["price"],
							"selling": 1,
						})
						ip.insert(ignore_permissions=True)
				frappe.db.commit()

		frappe.publish_realtime(
			event="variants_save_done",
			message={"success": True, "created": len(created), "skipped": len(skipped), "template_code": template_code},
			user=user,
			after_commit=True,
		)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "bulk_create_variants job failed")
		frappe.publish_realtime(
			event="variants_save_done",
			message={"success": False, "error": str(e), "template_code": template_code},
			user=user,
			after_commit=True,
		)


@frappe.whitelist()
def bulk_update_variant_rates(variants):
	"""
	Bulk-update standard_rate for existing variant Items.
	variants: JSON list of {item_code, price}
	Returns {updated: N}
	"""
	if isinstance(variants, str):
		variants = json.loads(variants)
	if not variants:
		return {"updated": 0}

	user = frappe.session.user
	now = frappe.utils.now()
	for v in variants:
		disabled = 1 if v.get("disabled") else 0
		frappe.db.sql(
			"UPDATE `tabItem` SET standard_rate=%s, disabled=%s, modified=%s, modified_by=%s WHERE name=%s",
			(float(v["price"]), disabled, now, user, v["item_code"]),
		)

	frappe.db.commit()
	return {"updated": len(variants)}


@frappe.whitelist()
def bulk_upsert_item_prices(entries):
	"""
	Bulk upsert Item Price records.
	entries: JSON list of {item_code, price_list, price}
	Loads all existing prices in ONE query, then updates/inserts with minimal round trips.
	Returns {updated: N, inserted: N}
	"""
	if isinstance(entries, str):
		entries = json.loads(entries)
	if not entries:
		return {"updated": 0, "inserted": 0}

	item_codes = list({e["item_code"] for e in entries})
	# Load ALL existing prices for these items (any selling/buying flag) so we
	# update instead of inserting a duplicate.
	existing = frappe.get_all(
		"Item Price",
		filters=[["item_code", "in", item_codes]],
		fields=["name", "item_code", "price_list", "price_list_rate", "selling"],
		limit_page_length=0,
	)
	existing_map = {}
	for r in existing:
		key = (r["item_code"], r["price_list"])
		# Prefer a selling price for the key when one exists.
		if key not in existing_map or r.get("selling"):
			existing_map[key] = r

	user = frappe.session.user
	now = frappe.utils.now()

	def _update_rate(name, price):
		frappe.db.sql(
			"UPDATE `tabItem Price` SET price_list_rate=%s, selling=1, modified=%s, modified_by=%s WHERE name=%s",
			(price, now, user, name),
		)

	updated = 0
	inserted = 0
	for entry in entries:
		key = (entry["item_code"], entry["price_list"])
		price = float(entry.get("price") or 0)
		rec = existing_map.get(key)
		if rec:
			if float(rec.get("price_list_rate") or 0) != price:
				_update_rate(rec["name"], price)
				updated += 1
			continue

		# Insert, guarding against ERPNext's duplicate-price validation.
		frappe.db.savepoint("ip_insert")
		try:
			doc = frappe.get_doc({
				"doctype": "Item Price",
				"item_code": entry["item_code"],
				"price_list": entry["price_list"],
				"price_list_rate": price,
				"selling": 1,
			})
			doc.insert(ignore_permissions=True)
			existing_map[key] = {"name": doc.name, "price_list_rate": price}
			inserted += 1
		except Exception:
			frappe.db.rollback(save_point="ip_insert")
			dup = frappe.get_all(
				"Item Price",
				filters={"item_code": entry["item_code"], "price_list": entry["price_list"]},
				fields=["name"],
				limit_page_length=1,
			)
			if dup:
				_update_rate(dup[0]["name"], price)
				existing_map[key] = {"name": dup[0]["name"], "price_list_rate": price}
				updated += 1

	frappe.db.commit()
	return {"updated": updated, "inserted": inserted}


@frappe.whitelist()
def get_price_lists():
	"""Return selling price lists for price entry."""
	return frappe.get_all(
		"Price List",
		filters={"selling": 1, "enabled": 1},
		fields=["name", "currency"],
		order_by="name asc",
		limit_page_length=0,
	)


@frappe.whitelist()
def get_item_classifications():
	"""Return Item Classifications when the custom DocType exists."""
	if not frappe.db.exists("DocType", "Item Classification"):
		return []
	return frappe.get_all(
		"Item Classification",
		fields=["name"],
		order_by="name asc",
		limit_page_length=0,
	)


@frappe.whitelist()
def get_editor_variants(template_item):
	"""Return all variants for a template item with ALL price list prices — for the product editor."""
	if not frappe.db.exists("Item", template_item):
		frappe.throw(_("Item {0} not found").format(template_item))

	variants = frappe.db.sql("""
		SELECT
			i.name AS item_code,
			i.item_name,
			i.standard_rate,
			i.enabled_item_bundle,
			i.disabled
		FROM `tabItem` i
		WHERE i.variant_of = %(template)s
		ORDER BY i.name ASC
	""", {"template": template_item}, as_dict=True)

	if not variants:
		return {"variants": [], "attributes": []}

	variant_codes = [v.item_code for v in variants]

	# All attributes for all variants in one query
	attrs = frappe.get_all(
		"Item Variant Attribute",
		filters={"parent": ["in", variant_codes]},
		fields=["parent", "attribute", "attribute_value"],
		order_by="parent asc, idx asc",
	)
	attr_map = {}
	for a in attrs:
		attr_map.setdefault(a.parent, {})[a.attribute] = a.attribute_value

	# All selling prices for all variants in one query
	prices = frappe.get_all(
		"Item Price",
		filters={"item_code": ["in", variant_codes], "selling": 1},
		fields=["item_code", "name", "price_list", "price_list_rate"],
		order_by="item_code asc, price_list asc",
	)
	price_map = {}
	for p in prices:
		price_map.setdefault(p.item_code, []).append({
			"name": p.name,
			"price_list": p.price_list,
			"price": p.price_list_rate,
		})

	# Build attribute summary for the editor (unique values per attribute)
	attr_summary = {}
	for v in variants:
		for attr, val in attr_map.get(v.item_code, {}).items():
			attr_summary.setdefault(attr, [])
			if val not in attr_summary[attr]:
				attr_summary[attr].append(val)

	result_variants = []
	for v in variants:
		result_variants.append({
			"item_code": v.item_code,
			"item_name": v.item_name,
			"standard_rate": v.standard_rate or 0,
			# Every price list this variant is priced on. This is the only source
			# of truth for variant pricing — there is no single "display price",
			# because collapsing the lists to one number is what silently
			# overwrote per-list rates on save.
			"prices": price_map.get(v.item_code, []),
			"attributes": attr_map.get(v.item_code, {}),
			"enabled_item_bundle": v.enabled_item_bundle,
			"disabled": v.disabled,
		})

	attributes = [{"attribute": attr, "values": vals} for attr, vals in attr_summary.items()]

	return {"variants": result_variants, "attributes": attributes}


@frappe.whitelist()
def get_item_manager_items(search_term="", start=0, page_length=20, item_group=None, item_classification=None, item_type=None):
	"""Return a paginated item list for the Desk Item Manager page."""
	start = frappe.utils.cint(start)
	page_length = frappe.utils.cint(page_length) or 20

	has_arabic = _has_field("Item", "custom_item_name_arabic")
	has_classification = _has_field("Item", "custom_item_classification")
	has_bundle = _has_field("Item", "enabled_item_bundle")
	has_fast_sell = _has_field("Item", "custom_fast_sell")

	extra_fields = ""
	if has_arabic:
		extra_fields += ", custom_item_name_arabic"
	if has_classification:
		extra_fields += ", custom_item_classification"
	if has_bundle:
		extra_fields += ", enabled_item_bundle"
	if has_fast_sell:
		extra_fields += ", custom_fast_sell"

	conditions = ["disabled = 0"]
	params = {}

	if item_group:
		conditions.append("item_group = %(item_group)s")
		params["item_group"] = item_group

	if item_classification and has_classification:
		conditions.append("custom_item_classification = %(item_classification)s")
		params["item_classification"] = item_classification

	if item_type:
		if item_type == "template":
			conditions.append("has_variants = 1")
		elif item_type == "variant":
			conditions.append("variant_of IS NOT NULL AND variant_of != ''")
		elif item_type == "bundle" and has_bundle:
			conditions.append("enabled_item_bundle = 1")
		elif item_type == "normal":
			normal_conds = ["has_variants = 0", "(variant_of IS NULL OR variant_of = '')"]
			if has_bundle:
				normal_conds.append("(enabled_item_bundle IS NULL OR enabled_item_bundle = 0)")
			conditions.append("(" + " AND ".join(normal_conds) + ")")

	if search_term:
		conditions.append("(item_code LIKE %(search)s OR item_name LIKE %(search)s)")
		params["search"] = f"%{search_term}%"

	where_clause = " AND ".join(conditions)

	items = frappe.db.sql(f"""
		SELECT
			name, item_code, item_name, item_group,
			has_variants, variant_of, standard_rate,
			image, disabled, modified
			{extra_fields}
		FROM `tabItem`
		WHERE {where_clause}
		ORDER BY modified DESC, name ASC
		LIMIT %(limit)s OFFSET %(offset)s
	""", {**params, "limit": page_length, "offset": start}, as_dict=1)

	total = frappe.db.sql(
		f"SELECT COUNT(*) FROM `tabItem` WHERE {where_clause}", params
	)[0][0]

	return {"items": items, "total": total}


@frappe.whitelist()
def get_item_with_details(item_code):
	"""Return an editable Item payload with prices and Product Bundle rows."""
	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item {0} not found").format(item_code))

	item = frappe.get_doc("Item", item_code)
	prices = frappe.get_all(
		"Item Price",
		filters={"item_code": item.name, "selling": 1},
		fields=["name", "price_list", "price_list_rate", "uom"],
		order_by="price_list asc",
		limit_page_length=0,
	)
	bundle = get_product_bundle(item.name)

	return {
		"item": {
			"name": item.name,
			"item_code": item.item_code,
			"item_name": item.item_name,
			"item_name_arabic": getattr(item, "custom_item_name_arabic", None),
			"item_group": item.item_group,
			"item_classification": getattr(item, "custom_item_classification", None),
			"stock_uom": item.stock_uom,
			"is_stock_item": item.is_stock_item,
			"standard_rate": item.standard_rate,
			"has_variants": item.has_variants,
			"variant_of": item.variant_of,
			"image": item.image,
			"description": item.description,
			"enabled_item_bundle": getattr(item, "enabled_item_bundle", 0),
			"custom_fast_sell": getattr(item, "custom_fast_sell", 0),
		},
		"prices": prices,
		"bundle": bundle,
	}


@frappe.whitelist()
def search_items_for_bundle(search_term=""):
	"""Search items that can be added to a Product Bundle (non-template, non-bundle)."""
	filters = {
		"disabled": 0,
		"has_variants": 0,
		"is_stock_item": 1,
	}
	or_filters = {}
	if search_term:
		or_filters = {
			"item_code": ["like", f"%{search_term}%"],
			"item_name": ["like", f"%{search_term}%"],
		}
	return frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "item_code", "item_name", "image", "stock_uom"],
		order_by="item_name asc",
		limit_page_length=20,
	)


@frappe.whitelist()
def get_product_bundle(item_code):
	"""Return Product Bundle rows for an item."""
	bundle_name = frappe.db.get_value("Product Bundle", {"new_item_code": item_code}, "name")
	if not bundle_name:
		return {"exists": False, "items": []}

	bundle = frappe.get_doc("Product Bundle", bundle_name)
	return {
		"exists": True,
		"name": bundle.name,
		"items": [
			{
				"item_code": row.item_code,
				"item_name": frappe.db.get_value("Item", row.item_code, "item_name") or row.description or row.item_code,
				"qty": row.qty,
				"uom": getattr(row, "uom", None),
				"description": row.description,
			}
			for row in bundle.items
		],
	}


# =============================================================================
# CREATE helpers
# =============================================================================

@frappe.whitelist()
def create_simple_item(item_data):
	"""
	Create a simple (quick-sell) item — no variants.

	Args:
		item_data (str|dict): JSON with keys:
			- item_code (str)
			- item_name (str)
			- item_group (str)
			- uom (str) — stock UOM
			- rate (float) — selling rate
			- price_list (str) — price list to set the rate in
			- image (str, optional)
			- description (str, optional)
			- is_stock_item (bool, optional, default 1)
	"""
	if isinstance(item_data, str):
		item_data = json.loads(item_data)

	_validate_required(item_data, ["item_code", "item_name", "item_group", "uom"])

	item = frappe.get_doc({
		"doctype": "Item",
		"item_code": item_data["item_code"],
		"item_name": item_data["item_name"],
		"item_group": item_data["item_group"],
		"stock_uom": item_data["uom"],
		"is_stock_item": item_data.get("is_stock_item", 1),
		"standard_rate": item_data.get("standard_rate") or 0,
		"has_variants": 0,
		"image": item_data.get("image"),
		"description": item_data.get("description", item_data["item_name"]),
	})
	_set_optional_item_fields(item, item_data)
	item.insert()

	_create_item_prices(
		item.name,
		item_data.get("price_lists"),
		item_data.get("price_list"),
		item_data.get("rate"),
		item_data["uom"],
	)

	frappe.db.commit()
	return {"item_code": item.name, "item_name": item.item_name}


@frappe.whitelist()
def create_template_item(item_data):
	"""
	Create a template item with variants.

	Args:
		item_data (str|dict): JSON with keys:
			- item_code (str)
			- item_name (str)
			- item_group (str)
			- uom (str) — stock UOM
			- image (str, optional)
			- description (str, optional)
			- attributes (list): [{"attribute": "Size", "values": ["S", "M", "L"]}, ...]
			- variants (list): [{"attributes": {"Size": "S", "Color": "Red"}, "rate": 50}, ...]
			- price_list (str) — price list to set variant rates in
	"""
	if isinstance(item_data, str):
		item_data = json.loads(item_data)

	_validate_required(item_data, ["item_code", "item_name", "item_group", "uom", "attributes"])

	attributes = item_data.get("attributes", [])
	if not attributes:
		frappe.throw(_("At least one attribute is required for template items"))

	# Create template item
	item = frappe.get_doc({
		"doctype": "Item",
		"item_code": item_data["item_code"],
		"item_name": item_data["item_name"],
		"item_group": item_data["item_group"],
		"stock_uom": item_data["uom"],
		"standard_rate": item_data.get("standard_rate") or 0,
		"has_variants": 1,
		"image": item_data.get("image"),
		"description": item_data.get("description", item_data["item_name"]),
		"attributes": [
			{"attribute": attr["attribute"]} for attr in attributes
		],
	})
	_set_optional_item_fields(item, item_data)
	item.insert()

	# Create variants
	created_variants = []
	variants = item_data.get("variants", [])

	for variant_def in variants:
		variant_attrs = variant_def.get("attributes", {})
		variant = frappe.get_doc({
			"doctype": "Item",
			"item_code": _generate_variant_code(item_data["item_code"], variant_attrs),
			"item_name": _generate_variant_name(item_data["item_name"], variant_attrs),
			"item_group": item_data["item_group"],
			"stock_uom": item_data["uom"],
			"has_variants": 0,
			"variant_of": item.name,
			"image": item_data.get("image"),
			"description": item_data.get("description", item_data["item_name"]),
			"attributes": [
				{"attribute": attr, "attribute_value": val}
				for attr, val in variant_attrs.items()
			],
		})
		variant.insert()

		_create_item_prices(
			variant.name,
			variant_def.get("price_lists"),
			item_data.get("price_list"),
			variant_def.get("rate"),
			item_data["uom"],
		)

		created_variants.append({
			"item_code": variant.name,
			"item_name": variant.item_name,
			"attributes": variant_attrs,
		})

	frappe.db.commit()
	return {
		"template": {"item_code": item.name, "item_name": item.item_name},
		"variants": created_variants,
	}


@frappe.whitelist()
def create_combo_item(item_data):
	"""
	Create a combo item (Product Bundle).

	Args:
		item_data (str|dict): JSON with keys:
			- item_code (str)
			- item_name (str)
			- item_group (str)
			- uom (str)
			- rate (float) — combo selling rate
			- price_list (str) — price list
			- image (str, optional)
			- description (str, optional)
			- components (list): [{"item_code": "ITEM-001", "qty": 2}, ...]
	"""
	if isinstance(item_data, str):
		item_data = json.loads(item_data)

	_validate_required(item_data, ["item_code", "item_name", "item_group", "uom", "components"])

	components = item_data.get("components", [])
	if not components:
		frappe.throw(_("At least one component is required for combo items"))

	# Create the parent item (non-stock, since it's a bundle)
	item = frappe.get_doc({
		"doctype": "Item",
		"item_code": item_data["item_code"],
		"item_name": item_data["item_name"],
		"item_group": item_data["item_group"],
		"stock_uom": item_data["uom"],
		"is_stock_item": 0,
		"standard_rate": item_data.get("standard_rate") or 0,
		"image": item_data.get("image"),
		"description": item_data.get("description", item_data["item_name"]),
	})
	_set_optional_item_fields(item, item_data)
	item.insert()

	# Create Product Bundle
	bundle = frappe.get_doc({
		"doctype": "Product Bundle",
		"new_item_code": item.name,
		"description": item_data.get("description", item_data["item_name"]),
		"items": [
			{
				"item_code": comp["item_code"],
				"qty": comp.get("qty", 1),
				"description": frappe.db.get_value("Item", comp["item_code"], "item_name") or comp["item_code"],
			}
			for comp in components
		],
	})
	bundle.insert()

	_create_item_prices(
		item.name,
		item_data.get("price_lists"),
		item_data.get("price_list"),
		item_data.get("rate"),
		item_data["uom"],
	)

	frappe.db.commit()
	return {
		"item_code": item.name,
		"item_name": item.item_name,
		"bundle": bundle.name,
	}


@frappe.whitelist()
def update_item(item_code, item_data):
	"""Update an existing Item, its selling prices, and optional Product Bundle rows."""
	if isinstance(item_data, str):
		item_data = json.loads(item_data)

	if not frappe.db.exists("Item", item_code):
		frappe.throw(_("Item {0} not found").format(item_code))

	_validate_required(item_data, ["item_name", "item_group", "uom"])

	item = frappe.get_doc("Item", item_code)
	item.item_name = item_data["item_name"]
	item.item_group = item_data["item_group"]
	item.stock_uom = item_data["uom"]
	item.is_stock_item = item_data.get("is_stock_item", item.is_stock_item)
	item.standard_rate = item_data.get("standard_rate") or 0
	item.image = item_data.get("image")
	item.description = item_data.get("description") or item_data["item_name"]
	_set_optional_item_fields(item, item_data)
	item.save(ignore_permissions=True)

	_replace_item_prices(item.name, item_data.get("price_lists"), item.stock_uom)

	if item_data.get("components") is not None:
		_save_product_bundle(item.name, item_data.get("components") or [], item.description)

	frappe.db.commit()
	return {"item_code": item.name, "item_name": item.item_name}


# =============================================================================
# Private helpers
# =============================================================================

def _validate_required(data, fields):
	"""Raise if any required field is missing."""
	for f in fields:
		if not data.get(f):
			frappe.throw(_("{0} is required").format(f))


def _has_field(doctype, fieldname):
	return bool(frappe.get_meta(doctype).has_field(fieldname))


def _set_optional_item_fields(item, item_data):
	"""Set POSAwesome-style custom fields only when they exist on this site."""
	field_map = {
		"custom_item_name_arabic": item_data.get("item_name_arabic"),
		"custom_item_classification": item_data.get("item_classification"),
		"enabled_item_bundle": item_data.get("enabled_item_bundle"),
		"custom_fast_sell": item_data.get("custom_fast_sell"),
	}
	for fieldname, value in field_map.items():
		if value is not None and _has_field("Item", fieldname):
			setattr(item, fieldname, value)


def _create_item_price(item_code, price_list, rate, uom):
	"""Create an Item Price entry."""
	frappe.get_doc({
		"doctype": "Item Price",
		"item_code": item_code,
		"price_list": price_list,
		"price_list_rate": rate,
		"uom": uom,
	}).insert(ignore_permissions=True)


def _create_item_prices(item_code, price_entries=None, fallback_price_list=None, fallback_rate=None, uom=None):
	"""Create one or more Item Price entries, keeping old single-price payloads compatible."""
	entries = price_entries or []
	if not entries and fallback_price_list and fallback_rate is not None:
		entries = [{"price_list": fallback_price_list, "rate": fallback_rate, "uom": uom}]

	seen = set()
	for entry in entries:
		price_list = entry.get("price_list")
		rate = entry.get("rate")
		price_uom = entry.get("uom") or uom

		if not price_list or rate is None:
			continue

		key = (price_list, price_uom)
		if key in seen:
			continue
		seen.add(key)

		_create_item_price(item_code, price_list, rate, price_uom)


def _replace_item_prices(item_code, price_entries=None, uom=None):
	for name in frappe.get_all("Item Price", filters={"item_code": item_code, "selling": 1}, pluck="name"):
		frappe.delete_doc("Item Price", name, ignore_permissions=True)
	_create_item_prices(item_code, price_entries or [], uom=uom)


def _save_product_bundle(item_code, components, description=None):
	bundle_name = frappe.db.get_value("Product Bundle", {"new_item_code": item_code}, "name")
	if not components:
		if bundle_name:
			frappe.delete_doc("Product Bundle", bundle_name, ignore_permissions=True)
		return

	if bundle_name:
		bundle = frappe.get_doc("Product Bundle", bundle_name)
		bundle.items = []
	else:
		bundle = frappe.new_doc("Product Bundle")
		bundle.new_item_code = item_code

	bundle.description = description or item_code
	for comp in components:
		bundle.append("items", {
			"item_code": comp["item_code"],
			"qty": comp.get("qty", 1),
			"description": frappe.db.get_value("Item", comp["item_code"], "item_name") or comp["item_code"],
		})
	bundle.save(ignore_permissions=True)


def _generate_variant_code(template_code, attrs):
	"""Generate a variant item code like TEMPLATE-S-Red."""
	suffix = "-".join(str(v) for v in attrs.values())
	return f"{template_code}-{suffix}"


def _generate_variant_name(template_name, attrs):
	"""Generate a variant item name like 'Burger (Small, Red)'."""
	suffix = ", ".join(str(v) for v in attrs.values())
	return f"{template_name} ({suffix})"
