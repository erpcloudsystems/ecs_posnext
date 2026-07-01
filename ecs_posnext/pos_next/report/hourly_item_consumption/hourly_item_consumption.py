# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

"""
Hourly Item Consumption Report (استهلاك الأصناف بالساعة)

This report shows item consumption (outgoing stock) broken down by hour
for a selected date or date range.

Data Source: Stock Ledger Entry (actual_qty < 0 = outgoing)
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
    if not filters.get("posting_date"):
        frappe.throw(_("التاريخ مطلوب"))
    
    if not filters.get("warehouse"):
        frappe.throw(_("المخزن مطلوب"))


def get_columns(filters):
    """Define report columns with hourly breakdown per week."""
    
    # Define operating hours (13:00 to 06:00 next day)
    hours = get_operating_hours()
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
    
    # Add hour columns - each hour has columns for each week + total + avg
    for hour in hours:
        # Total for this hour across weeks
        columns.append({
            "fieldname": f"hour_{hour}_total",
            "label": f"{hour}:00",
            "fieldtype": "Float",
            "precision": 2,
            "width": 60,
        })
        # Average for this hour
        # columns.append({
        #     "fieldname": f"hour_{hour}_avg",
        #     "label": f"{hour}:00 م",
        #     "fieldtype": "Float",
        #     "precision": 2,
        #     "width": 55,
        # })
    
    # Grand total column
    columns.append({
        "fieldname": "grand_total",
        "label": _("الإجمالي"),
        "fieldtype": "Float",
        "precision": 2,
        "width": 90,
    })
    
    return columns


def get_operating_hours():
    """
    Return list of operating hours.
    Default: 13:00 to 06:00 (next day)
    """
    return list(range(13, 24)) + list(range(0, 7))


def get_data(filters):
    """Fetch and process hourly consumption data per week."""
    posting_date = getdate(filters.get("posting_date"))
    weeks_count = cint(filters.get("weeks_count")) or 4
    
    hours = get_operating_hours()
    
    # Get target weekday dates (same day of week over past N weeks)
    target_dates = get_target_weekday_dates(posting_date, weeks_count)
    
    # Get hourly consumption for each target date
    hourly_weekly_data = get_hourly_weekly_consumption(filters, target_dates)
    
    # Aggregate by item
    items = {}
    for item_code, item_data in hourly_weekly_data.items():
        items[item_code] = {
            "item_code": item_code,
            "item_name": item_data.get("item_name", ""),
            "stock_uom": item_data.get("stock_uom", ""),
            "grand_total": 0,
        }
        
        # Initialize all hour/week columns
        for h in hours:
            for w in range(1, weeks_count + 1):
                items[item_code][f"hour_{h}_w{w}"] = 0
            items[item_code][f"hour_{h}_total"] = 0
            items[item_code][f"hour_{h}_avg"] = 0
        
        # Fill in weekly data for each hour
        for h in hours:
            hour_total = 0
            for w_idx, target_date in enumerate(target_dates):
                week_num = w_idx + 1
                qty = flt(item_data.get("hours", {}).get(target_date, {}).get(h, 0), 2)
                items[item_code][f"hour_{h}_w{week_num}"] = qty
                hour_total += qty
            
            items[item_code][f"hour_{h}_total"] = flt(hour_total, 2)
            items[item_code][f"hour_{h}_avg"] = flt(hour_total / weeks_count, 2) if weeks_count > 0 else 0
            items[item_code]["grand_total"] += hour_total
    
    # Convert to list and sort by grand_total descending
    result = list(items.values())
    result.sort(key=lambda x: x.get("grand_total", 0), reverse=True)
    
    # Add totals row
    if result:
        totals_row = {
            "item_code": "",
            "item_name": _("الإجمالي"),
            "stock_uom": "",
            "grand_total": 0,
        }
        for h in hours:
            for w in range(1, weeks_count + 1):
                totals_row[f"hour_{h}_w{w}"] = sum(flt(r.get(f"hour_{h}_w{w}", 0)) for r in result)
            totals_row[f"hour_{h}_total"] = sum(flt(r.get(f"hour_{h}_total", 0)) for r in result)
            totals_row[f"hour_{h}_avg"] = sum(flt(r.get(f"hour_{h}_avg", 0)) for r in result)
        totals_row["grand_total"] = sum(flt(r.get("grand_total", 0)) for r in result)
        result.append(totals_row)
    
    return result


def get_target_weekday_dates(posting_date, weeks_count):
    """Get target dates for the same weekday over the last N weeks."""
    dates = []
    
    for i in range(weeks_count - 1, -1, -1):
        prev_date = add_days(posting_date, -7 * i)
        dates.append(prev_date)
    
    return dates


def get_hourly_weekly_consumption(filters, target_dates):
    """Get hourly consumption for each target date (same weekday over past weeks)."""
    conditions = ["sle.actual_qty < 0"]
    params = {}
    
    # Build date conditions
    date_conditions = []
    for d in target_dates:
        next_d = add_days(d, 1)
        date_conditions.append(f"(sle.posting_date = '{d}' AND HOUR(sle.posting_time) >= 13)")
        date_conditions.append(f"(sle.posting_date = '{next_d}' AND HOUR(sle.posting_time) < 7)")
    
    # Warehouse filter
    if filters.get("warehouse"):
        conditions.append("sle.warehouse = %(warehouse)s")
        params["warehouse"] = filters.get("warehouse")
    
    # Item group filter
    if filters.get("item_group"):
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = filters.get("item_group")
    
    # Item code filter
    if filters.get("item_code"):
        conditions.append("sle.item_code = %(item_code)s")
        params["item_code"] = filters.get("item_code")
    
    where_clause = " AND ".join(conditions)
    date_clause = " OR ".join(date_conditions)
    
    query = f"""
        SELECT 
            sle.item_code,
            i.item_name,
            i.stock_uom,
            sle.posting_date,
            HOUR(sle.posting_time) as posting_hour,
            SUM(sle.actual_qty * -1) as consumed_qty
        FROM `tabStock Ledger Entry` sle
        LEFT JOIN `tabItem` i ON i.name = sle.item_code
        WHERE ({date_clause})
        AND i.custom_hourly = 1
        AND {where_clause}
        GROUP BY sle.item_code, sle.posting_date, HOUR(sle.posting_time)
        ORDER BY sle.item_code, sle.posting_date, HOUR(sle.posting_time)
    """
    
    data = frappe.db.sql(query, params, as_dict=True)
    
    # Build nested dict: {item_code: {item_name, stock_uom, hours: {date: {hour: qty}}}}
    result = {}
    for row in data:
        item_code = row["item_code"]
        posting_date = getdate(row["posting_date"])
        posting_hour = int(row.get("posting_hour", 13))
        
        # Adjust date for early morning hours (0-6) - belongs to previous day's shift
        if posting_hour < 7:
            posting_date = add_days(posting_date, -1)
        
        if item_code not in result:
            result[item_code] = {
                "item_name": row["item_name"],
                "stock_uom": row["stock_uom"],
                "hours": {},
            }
        
        if posting_date not in result[item_code]["hours"]:
            result[item_code]["hours"][posting_date] = {}
        
        if posting_hour not in result[item_code]["hours"][posting_date]:
            result[item_code]["hours"][posting_date][posting_hour] = 0
        
        result[item_code]["hours"][posting_date][posting_hour] += flt(row["consumed_qty"], 2)
    
    return result
