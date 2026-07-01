# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

"""
Daily Operation Planning Report (معدل التشغيل اليومي)

This report calculates daily required preparation quantities for raw items
based on historical consumption from Packed Items linked to Sales Invoices.

Data Source: tabPacked Item -> tabSales Invoice
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_days, flt, cint


def execute(filters=None):
    """Main entry point for the script report."""
    if not filters:
        filters = {}
    
    validate_filters(filters)
    
    columns = get_columns(filters)
    data = get_data(filters)
    
    return columns, data


def validate_filters(filters):
    """Validate required filters."""
    if not filters.get("warehouse"):
        frappe.throw(_("Warehouse is required"))
    
    if not filters.get("posting_date"):
        frappe.throw(_("Posting Date is required"))


def get_columns(filters):
    """Define report columns."""
    weeks_count = cint(filters.get("weeks_count")) or 4
    
    columns = [
        {
            "fieldname": "item_code",
            "label": _("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 120,
        },
        {
            "fieldname": "item_name",
            "label": _("Item Name"),
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "fieldname": "stock_uom",
            "label": _("UOM"),
            "fieldtype": "Data",
            "width": 60,
        },
    ]
    
    # Add week columns dynamically (up to 4 or weeks_count)
    display_weeks = min(weeks_count, 4)
    for i in range(1, display_weeks + 1):
        columns.append({
            "fieldname": f"week_{i}_qty",
            "label": _("Week {0}").format(i),
            "fieldtype": "Float",
            "precision": 2,
            "width": 80,
        })
    
    columns.extend([
        {
            "fieldname": "daily_avg_qty",
            "label": _("معدل يوم "),
            "fieldtype": "Float",
            "precision": 2,
            "width": 90,
        },
        {
            "fieldname": "growth_factor",
            "label": _("نسبة الزياده المتوقعه"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 80,
        },
        {
            "fieldname": "gross_required_qty",
            "label": _("اجمالي المطلوب"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 100,
        },
        {
            "fieldname": "current_stock_qty",
            "label": _("جرد اليوم"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 100,
        },
        {
            "fieldname": "net_required_qty",
            "label": _("المطلوب"),
            "fieldtype": "Float",
            "precision": 2,
            "width": 100,
        },
        # {
        #     "fieldname": "pack_size",
        #     "label": _("Pack Size"),
        #     "fieldtype": "Float",
        #     "precision": 2,
        #     "width": 80,
        # },
        # {
        #     "fieldname": "required_packs",
        #     "label": _("Required Packs"),
        #     "fieldtype": "Float",
        #     "precision": 2,
        #     "width": 100,
        # },
    ])
    
    return columns


def get_data(filters):
    """Fetch and process report data."""
    posting_date = getdate(filters.get("posting_date"))
    weeks_count = cint(filters.get("weeks_count")) or 4
    warehouse = filters.get("warehouse")
    
    # Get target weekday dates
    target_dates = get_target_weekday_dates(posting_date, weeks_count)
    
    if not target_dates:
        return []
    
    # Get packed item consumption data
    consumption_data = get_packed_item_consumption(filters, target_dates)
    
    # Get item metadata
    item_metadata = get_item_metadata(filters)
    
    # Get current stock
    stock_data = get_current_stock(warehouse)
    
    # Build result rows
    result = build_result_rows(
        consumption_data,
        item_metadata,
        stock_data,
        target_dates,
        weeks_count
    )
    
    return result


def get_target_weekday_dates(posting_date, weeks_count):
    """
    Get target dates for the same weekday over the last N weeks.
    
    Example: If posting_date is Tuesday 2024-01-16, and weeks_count=4,
    returns [2024-01-16, 2024-01-09, 2024-01-02, 2023-12-26]
    (most recent first, then reversed for week_1 = oldest)
    """
    dates = [posting_date]
    
    for i in range(1, weeks_count):
        prev_date = add_days(posting_date, -7 * i)
        dates.append(prev_date)
    
    # Reverse so week_1 is oldest, week_N is most recent (posting_date)
    dates.reverse()
    
    return dates


def get_packed_item_consumption(filters, target_dates):
    """
    Query packed item quantities from Sales Invoices for target dates.
    Returns dict: {item_code: {date: qty, ...}, ...}
    """
    conditions = ["si.docstatus = 1"]
    params = {}
    
    # Date filter - use IN clause for target dates
    date_list = ", ".join([f"'{d}'" for d in target_dates])
    conditions.append(f"si.posting_date IN ({date_list})")
    
    # Include returns filter
    include_returns = cint(filters.get("include_returns"))
    if not include_returns:
        conditions.append("si.is_return = 0")
    
    # Company filter
    if filters.get("company"):
        conditions.append("si.company = %(company)s")
        params["company"] = filters.get("company")
    
    # Branch filter (handle gracefully if field doesn't exist)
    if filters.get("branch"):
        if has_field("Sales Invoice", "branch"):
            conditions.append("si.branch = %(branch)s")
            params["branch"] = filters.get("branch")
    
    # Item group filter
    if filters.get("item_group"):
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = filters.get("item_group")
    
    # Only operation items filter
    only_operation_items = cint(filters.get("only_operation_items", 1))
    if only_operation_items:
        if has_field("Item", "include_in_operation_report"):
            conditions.append("i.include_in_operation_report = 1")
    
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
    
    # Build nested dict: {item_code: {date: qty}}
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
    """
    Get item metadata including custom fields for operation planning.
    Returns dict: {item_code: {item_name, stock_uom, growth_factor, pack_size}}
    """
    conditions = ["i.disabled = 0"]
    params = {}
    
    # Item group filter
    if filters.get("item_group"):
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = filters.get("item_group")
    
    # Only operation items filter
    only_operation_items = cint(filters.get("only_operation_items", 1))
    if only_operation_items and has_field("Item", "include_in_operation_report"):
        conditions.append("i.include_in_operation_report = 1")
    
    where_clause = " AND ".join(conditions)
    
    # Build SELECT fields based on available custom fields
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


def get_current_stock(warehouse):
    """
    Get current stock quantities from Bin for selected warehouse.
    Returns dict: {item_code: actual_qty}
    """
    query = """
        SELECT item_code, actual_qty
        FROM `tabBin`
        WHERE warehouse = %(warehouse)s
        AND actual_qty != 0
    """
    
    data = frappe.db.sql(query, {"warehouse": warehouse}, as_dict=True)
    
    return {row["item_code"]: flt(row["actual_qty"], 3) for row in data}


def build_result_rows(consumption_data, item_metadata, stock_data, target_dates, weeks_count):
    """
    Build final result rows combining all data sources.
    """
    result = []
    
    # Get all unique item codes from consumption data
    all_items = set(consumption_data.keys())
    
    # Also include items from metadata if they have include_in_operation_report
    # (they might have zero consumption but still need to be shown)
    all_items.update(item_metadata.keys())
    
    display_weeks = min(weeks_count, 4)
    
    for item_code in sorted(all_items):
        # Get item metadata (with defaults)
        meta = item_metadata.get(item_code, {})
        if not meta:
            # Item not in metadata, skip or fetch basic info
            item_doc = frappe.db.get_value(
                "Item",
                item_code,
                ["item_name", "stock_uom"],
                as_dict=True
            )
            if not item_doc:
                continue
            meta = {
                "item_name": item_doc.get("item_name", ""),
                "stock_uom": item_doc.get("stock_uom", ""),
                "growth_factor": 1.3,
                "pack_size": 0,
            }
        
        # Get consumption data for this item
        item_consumption = consumption_data.get(item_code, {})
        
        # Build week quantities
        week_qtys = []
        total_qty = 0
        
        for i, target_date in enumerate(target_dates):
            qty = flt(item_consumption.get(target_date, 0), 3)
            week_qtys.append(qty)
            total_qty += qty
        
        # Skip items with zero consumption unless they have stock
        current_stock = flt(stock_data.get(item_code, 0), 3)
        if total_qty == 0 and current_stock == 0:
            continue
        
        # Calculate daily average (average across all weeks, missing weeks = 0)
        daily_avg = flt(total_qty / weeks_count, 3) if weeks_count > 0 else 0
        
        # Growth factor
        growth_factor = flt(meta.get("growth_factor", 1.3), 2)
        
        # Gross required
        gross_required = flt(daily_avg * growth_factor, 3)
        
        # Net required (max 0)
        net_required = max(0, flt(gross_required - current_stock, 3))
        
        # Pack size and required packs
        pack_size = flt(meta.get("pack_size", 0), 2)
        required_packs = None
        if pack_size > 0:
            required_packs = flt(net_required / pack_size, 2)
        
        # Build row
        row = {
            "item_code": item_code,
            "item_name": meta.get("item_name", ""),
            "stock_uom": meta.get("stock_uom", ""),
            "daily_avg_qty": daily_avg,
            "growth_factor": growth_factor,
            "gross_required_qty": gross_required,
            "current_stock_qty": current_stock,
            "net_required_qty": net_required,
            "pack_size": pack_size if pack_size > 0 else None,
            "required_packs": required_packs,
        }
        
        # Add week columns (up to display_weeks)
        for i in range(display_weeks):
            if i < len(week_qtys):
                row[f"week_{i + 1}_qty"] = week_qtys[i]
            else:
                row[f"week_{i + 1}_qty"] = 0
        
        result.append(row)
    
    # Sort by net_required_qty descending (most needed first)
    result.sort(key=lambda x: x.get("net_required_qty", 0), reverse=True)
    
    return result


def has_field(doctype, fieldname):
    """
    Check if a field exists on a doctype.
    Caches the result to avoid repeated DB calls.
    """
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
