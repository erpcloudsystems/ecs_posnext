# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

"""
Daily Operation Planning Page API

This page provides an interactive interface for daily operation planning
with editable growth factor from user input.
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_days, flt, cint
import json


@frappe.whitelist()
def get_planning_data(filters):
    """Get planning data for the page."""
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    validate_filters(filters)
    
    columns = get_columns(filters)
    data = get_data(filters)
    
    return {
        "columns": columns,
        "data": data
    }


def validate_filters(filters):
    """Validate required filters."""
    if not filters.get("warehouse"):
        frappe.throw(_("Warehouse is required"))
    
    if not filters.get("posting_date"):
        frappe.throw(_("Posting Date is required"))


def get_columns(filters):
    """Define columns."""
    weeks_count = cint(filters.get("weeks_count")) or 4
    
    columns = [
        {"fieldname": "item_code", "label": _("Item Code"), "fieldtype": "Link", "options": "Item"},
        {"fieldname": "item_name", "label": _("Item Name"), "fieldtype": "Data"},
        {"fieldname": "stock_uom", "label": _("UOM"), "fieldtype": "Data"},
    ]
    
    display_weeks = min(weeks_count, 4)
    for i in range(1, display_weeks + 1):
        columns.append({
            "fieldname": f"week_{i}_qty",
            "label": _("Week {0}").format(i),
            "fieldtype": "Float",
        })
    
    columns.extend([
        {"fieldname": "daily_avg_qty", "label": _("معدل يوم"), "fieldtype": "Float"},
        {"fieldname": "growth_factor", "label": _("نسبة الزيادة"), "fieldtype": "Float", "editable": True},
        {"fieldname": "gross_required_qty", "label": _("إجمالي المطلوب"), "fieldtype": "Float"},
        {"fieldname": "current_stock_qty", "label": _("جرد اليوم"), "fieldtype": "Float"},
        {"fieldname": "net_required_qty", "label": _("المطلوب"), "fieldtype": "Float"},
    ])
    
    return columns


def get_data(filters):
    """Fetch and process data."""
    posting_date = getdate(filters.get("posting_date"))
    weeks_count = cint(filters.get("weeks_count")) or 4
    warehouse = filters.get("warehouse")
    
    target_dates = get_target_weekday_dates(posting_date, weeks_count)
    
    if not target_dates:
        return []
    
    consumption_data = get_packed_item_consumption(filters, target_dates)
    item_metadata = get_item_metadata(filters)
    stock_data = get_current_stock(warehouse, posting_date)

    result = build_result_rows(
        consumption_data,
        item_metadata,
        stock_data,
        target_dates,
        weeks_count
    )
    
    return result


def get_target_weekday_dates(posting_date, weeks_count):
    """Get target dates for the same weekday over the last N weeks."""
    dates = [posting_date]
    
    for i in range(1, weeks_count):
        prev_date = add_days(posting_date, -7 * i)
        dates.append(prev_date)
    
    dates.reverse()
    return dates


def get_packed_item_consumption(filters, target_dates):
    """Query packed item quantities from Sales Invoices for target dates."""
    conditions = ["si.docstatus = 1"]
    params = {}
    
    date_list = ", ".join([f"'{d}'" for d in target_dates])
    conditions.append(f"si.posting_date IN ({date_list})")
    
    include_returns = cint(filters.get("include_returns"))
    if not include_returns:
        conditions.append("si.is_return = 0")
    
    if filters.get("company"):
        conditions.append("si.company = %(company)s")
        params["company"] = filters.get("company")
    
    if filters.get("branch"):
        if has_field("Sales Invoice", "branch"):
            conditions.append("si.branch = %(branch)s")
            params["branch"] = filters.get("branch")
    
    if filters.get("item_group"):
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = filters.get("item_group")
    
    only_operation_items = cint(filters.get("only_operation_items", 1))
    if only_operation_items:
        conditions.append("i.custom_daily = 1")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
        SELECT 
            pi.item_code,
            si.posting_date,
            SUM(pi.qty) as total_qty
        FROM `tabPacked Item` pi
        INNER JOIN `tabSales Invoice` si ON si.name = pi.parent
        LEFT JOIN `tabItem` i ON i.name = pi.item_code
        WHERE pi.parenttype = 'Sales Invoice'
        AND {where_clause}
        GROUP BY pi.item_code, si.posting_date
        ORDER BY pi.item_code, si.posting_date
    """
    
    data = frappe.db.sql(query, params, as_dict=True)
    
    result = {}
    for row in data:
        item_code = row["item_code"]
        posting_date = getdate(row["posting_date"])
        qty = flt(row["total_qty"], 3)
        
        if item_code not in result:
            result[item_code] = {}
        
        result[item_code][posting_date] = qty
    
    return result


def get_item_metadata(filters):
    """Get item metadata including custom fields."""
    conditions = ["i.disabled = 0"]
    params = {}
    
    if filters.get("item_group"):
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = filters.get("item_group")
    
    only_operation_items = cint(filters.get("only_operation_items", 1))
    if only_operation_items:
        conditions.append("i.is_stock_item = 1")
    
    where_clause = " AND ".join(conditions)
    
    select_fields = ["i.name as item_code", "i.item_name", "i.stock_uom"]
    
    if has_field("Item", "operation_growth_factor"):
        select_fields.append("i.operation_growth_factor")
    
    if has_field("Item", "operation_pack_size"):
        select_fields.append("i.operation_pack_size")
    
    select_clause = ", ".join(select_fields)
    
    query = f"""
        SELECT {select_clause}
        FROM `tabItem` i
        WHERE {where_clause}
    """
    
    data = frappe.db.sql(query, params, as_dict=True)
    
    result = {}
    for row in data:
        item_code = row["item_code"]
        result[item_code] = {
            "item_name": row.get("item_name", ""),
            "stock_uom": row.get("stock_uom", ""),
            "growth_factor": flt(row.get("operation_growth_factor")) or 1.3,
            "pack_size": flt(row.get("operation_pack_size")) or 0,
        }
    
    return result


def get_current_stock(warehouse, posting_date=None):
    """
    Get today's inventory count from the Inventory doctype (physical count).
    Falls back to Bin (system stock) if no submitted Inventory document exists
    for the given warehouse on or before posting_date.
    """
    if posting_date is None:
        posting_date = frappe.utils.today()

    inventory_query = """
        SELECT it.item AS item_code, it.qty
        FROM `tabItems` it
        INNER JOIN `tabInventory` inv ON inv.name = it.parent
        WHERE inv.warehouse = %(warehouse)s
            AND inv.docstatus = 1
            AND inv.date <= %(posting_date)s
        ORDER BY inv.date DESC
    """
    rows = frappe.db.sql(inventory_query, {"warehouse": warehouse, "posting_date": posting_date}, as_dict=True)

    if rows:
        # Use the most recent Inventory document per item
        seen = {}
        for r in rows:
            if r.item_code not in seen:
                seen[r.item_code] = flt(r.qty, 3)
        return seen

    # Fallback: use Bin (system stock) when no Inventory document exists
    bin_query = """
        SELECT item_code, actual_qty
        FROM `tabBin`
        WHERE warehouse = %(warehouse)s
        AND actual_qty != 0
    """
    data = frappe.db.sql(bin_query, {"warehouse": warehouse}, as_dict=True)
    return {row["item_code"]: flt(row["actual_qty"], 3) for row in data}


def build_result_rows(consumption_data, item_metadata, stock_data, target_dates, weeks_count):
    """Build final result rows."""
    result = []
    
    all_items = set(consumption_data.keys())
    all_items.update(item_metadata.keys())
    
    display_weeks = min(weeks_count, 4)
    
    for item_code in sorted(all_items):
        meta = item_metadata.get(item_code, {})
        if not meta:
            item_doc = frappe.db.get_value(
                "Item", item_code, ["item_name", "stock_uom"], as_dict=True
            )
            if not item_doc:
                continue
            meta = {
                "item_name": item_doc.get("item_name", ""),
                "stock_uom": item_doc.get("stock_uom", ""),
                "growth_factor": 1.3,
                "pack_size": 0,
            }
        
        item_consumption = consumption_data.get(item_code, {})
        
        week_qtys = []
        total_qty = 0
        
        for i, target_date in enumerate(target_dates):
            qty = flt(item_consumption.get(target_date, 0), 3)
            week_qtys.append(qty)
            total_qty += qty
        
        current_stock = flt(stock_data.get(item_code, 0), 3)
        if total_qty == 0 and current_stock == 0:
            continue
        
        daily_avg = flt(total_qty / weeks_count, 3) if weeks_count > 0 else 0
        growth_factor = flt(meta.get("growth_factor", 1.3), 2)
        gross_required = flt(daily_avg * growth_factor, 3)
        net_required = max(0, flt(gross_required - current_stock, 3))
        
        row = {
            "item_code": item_code,
            "item_name": meta.get("item_name", ""),
            "stock_uom": meta.get("stock_uom", ""),
            "daily_avg_qty": daily_avg,
            "growth_factor": growth_factor,
            "gross_required_qty": gross_required,
            "current_stock_qty": current_stock,
            "net_required_qty": net_required,
        }
        
        for i in range(display_weeks):
            if i < len(week_qtys):
                row[f"week_{i + 1}_qty"] = week_qtys[i]
            else:
                row[f"week_{i + 1}_qty"] = 0
        
        result.append(row)
    
    result.sort(key=lambda x: x.get("net_required_qty", 0), reverse=True)
    return result


def has_field(doctype, fieldname):
    """Check if a field exists on a doctype."""
    cache_key = f"has_field_{doctype}_{fieldname}"
    cached = frappe.cache().get_value(cache_key)
    
    if cached is not None:
        return cached
    
    try:
        meta = frappe.get_meta(doctype)
        result = meta.has_field(fieldname)
    except Exception:
        result = False
    
    frappe.cache().set_value(cache_key, result, expires_in_sec=3600)
    return result


@frappe.whitelist()
def create_material_request(items, warehouse, company=None):
    """Create Material Request from planning data."""
    if isinstance(items, str):
        items = json.loads(items)
    
    if not items:
        frappe.throw(_("No items provided"))
    
    if not warehouse:
        frappe.throw(_("Warehouse is required"))
    
    if not company:
        company = frappe.defaults.get_user_default("company") or frappe.db.get_single_value("Global Defaults", "default_company")
    
    mr = frappe.new_doc("Material Request")
    mr.material_request_type = "Material Transfer"
    mr.company = company
    mr.schedule_date = frappe.utils.nowdate()
    mr.set_warehouse = warehouse
    mr.set_from_warehouse = 'المخزن الرئيسي - M'
    
    for item in items:
        if flt(item.get("qty")) <= 0:
            continue
        
        mr.append("items", {
            "item_code": item.get("item_code"),
            "qty": flt(item.get("qty")),
            "uom": item.get("uom") or frappe.db.get_value("Item", item.get("item_code"), "stock_uom"),
            "warehouse": warehouse,
            "schedule_date": frappe.utils.nowdate()
        })
    
    if not mr.items:
        frappe.throw(_("No valid items to create Material Request"))
    
    mr.insert()
    # mr.submit()
    
    return mr.name
