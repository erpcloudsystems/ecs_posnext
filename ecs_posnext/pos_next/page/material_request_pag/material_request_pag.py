import json
import math
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import cint, flt, nowdate


def _sanitize(value, precision=2):
	"""Convert value to a finite float rounded to the desired precision."""
	value = flt(value)
	if not math.isfinite(value):
		return 0.0
	return flt(value, precision)


@frappe.whitelist()
def get_items(item_type=None, page_len=50, page_start=0):
	"""Return reorder suggestions for items in the given POS Item Type."""
	if not item_type:
		frappe.throw(_("Item Type is required"), title=_("Missing Filter"))

	page_len = cint(page_len or 50)
	page_start = cint(page_start or 0)

	page_len = max(10, min(page_len, 200))
	page_start = max(page_start, 0)
	limit = page_len + 1  # fetch one extra row to detect more results

	query = """
		SELECT
			item.name AS item_code,
			item.item_name,
			item.item_group,
			reorder.warehouse,
			COALESCE(bin.actual_qty, 0) AS actual_qty,
			COALESCE(reorder.warehouse_reorder_level, 0) AS reorder_level,
			COALESCE(reorder.warehouse_reorder_qty, 0) AS reorder_qty,
			GREATEST(
				COALESCE(reorder.warehouse_reorder_qty, 0),
				GREATEST(
					COALESCE(reorder.warehouse_reorder_level, 0) - COALESCE(bin.actual_qty, 0),
					0
				)
			) AS suggested_qty
		FROM `tabItem` item
		INNER JOIN `tabItem Reorder` reorder
			ON reorder.parent = item.name
			AND reorder.parenttype = 'Item'
			AND reorder.parentfield = 'reorder_levels'
		LEFT JOIN `tabBin` bin
			ON bin.item_code = item.name
			AND bin.warehouse = reorder.warehouse
		WHERE item.disabled = 0
			AND item.is_stock_item = 1
			AND item.posa_item_type = %(item_type)s
		HAVING suggested_qty > 0
		ORDER BY item.item_name
		LIMIT %(fetch_limit)s OFFSET %(page_start)s
	"""

	records = frappe.db.sql(
		query,
		{
			"item_type": item_type,
			"fetch_limit": limit,
			"page_start": page_start,
		},
		as_dict=True,
	)

	has_more = len(records) > page_len
	if has_more:
		records = records[:page_len]

	results = []
	for row in records:
		suggested_qty = _sanitize(row.suggested_qty)
		if suggested_qty <= 0:
			continue

		actual_qty = _sanitize(row.actual_qty)
		reorder_level = _sanitize(row.reorder_level)
		reorder_qty = _sanitize(row.reorder_qty)

		results.append(
			{
				"item_code": row.item_code,
				"item_name": row.item_name,
				"item_group": row.item_group,
				"warehouse": row.warehouse,
				"actual_qty": actual_qty,
				"reorder_level": reorder_level,
				"reorder_qty": reorder_qty,
				"suggested_qty": suggested_qty,
				"request_qty": suggested_qty,
			}
		)

	return {
		"items": results,
		"start": page_start,
		"page_len": page_len,
		"has_more": has_more,
	}


@frappe.whitelist()
def create_material_request(items, target_warehouse=None):
	"""Create a Material Request document for the provided items."""
	if isinstance(items, str):
		items = json.loads(items)

	if not items:
		frappe.throw(_("Select at least one item to create a Material Request."), title=_("Nothing Selected"))

	aggregated = defaultdict(float)
	target_warehouse = (target_warehouse or "").strip()

	for raw in items:
		row = frappe._dict(raw or {})
		item_code = (row.get("item_code") or "").strip()
		warehouse = target_warehouse or (row.get("warehouse") or "").strip()
		qty = _sanitize(row.get("qty") or row.get("request_qty"), precision=4)

		if not item_code or not warehouse:
			frappe.throw(_("Item code and warehouse are required for every row."))

		if qty <= 0:
			frappe.throw(_("Quantity for {0} must be greater than zero.").format(frappe.bold(item_code)))

		key = (item_code, warehouse)
		aggregated[key] += qty

	if not aggregated:
		frappe.throw(_("Select at least one item with a quantity greater than zero."))

	doc = frappe.new_doc("Material Request")
	doc.company = frappe.defaults.get_user_default("Company")
	doc.schedule_date = nowdate()
	doc.material_request_type = "Purchase"

	response_items = []
	for (item_code, warehouse), qty in aggregated.items():
		qty = _sanitize(qty, precision=4)
		if qty <= 0:
			continue

		doc.append(
			"items",
			{
				"item_code": item_code,
				"warehouse": warehouse,
				"qty": qty,
				"schedule_date": doc.schedule_date,
			},
		)
		response_items.append({"item_code": item_code, "warehouse": warehouse, "qty": qty})

	if not doc.items:
		frappe.throw(_("Select at least one item with a quantity greater than zero."))

	doc.insert()
	doc.submit()

	return {
		"material_request": doc.name,
		"items": response_items,
		"processed_items": response_items,
		"target_warehouse": target_warehouse,
	}
