# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import getdate, add_days, flt
from datetime import timedelta


# Day of week mapping (Python weekday: 0=Monday, we want 0=Saturday)
DAY_NAMES = {
    0: "السبت",
    1: "الأحد",
    2: "الإثنين",
    3: "الثلاثاء",
    4: "الأربعاء",
    5: "الخميس",
    6: "الجمعة",
}


def get_increase_rate_from_doctype(target_dates=None, day_name=None):
    """
    Get increase rate (percent) from Operating Rate doctype.
    If target_dates AND day_name are provided, look for rows matching both date AND day.
    Returns percent as decimal (e.g., 130% = 1.3), defaults to 1.3 if not found.
    """
    try:
        # Get the first Operating Rate document
        operating_rate = frappe.get_all("Operating Rate", limit=1)
        if not operating_rate:
            return 1.3
        
        doc = frappe.get_doc("Operating Rate", operating_rate[0].name)
        
        if not doc.operating_rate_table:
            return 1.3
        
        total_percent = 0
        count = 0
        
        # Search for matching rows - combine date AND day criteria
        for row in doc.operating_rate_table:
            date_match = False
            day_match = False
            
            # Check date match
            if target_dates and row.date:
                if getdate(row.date) in [getdate(d) for d in target_dates]:
                    date_match = True
            
            # Check day match
            if day_name and row.day:
                if row.day == day_name:
                    day_match = True
            
            # If both criteria provided, both must match
            # If only one provided, that one must match
            if target_dates and day_name:
                if date_match and day_match:
                    total_percent += flt(row.percent)
                    count += 1
            elif target_dates and date_match:
                total_percent += flt(row.percent)
                count += 1
            elif day_name and day_match:
                total_percent += flt(row.percent)
                count += 1
        
        if count > 0:
            # percent is stored as 130 for 130%, convert to 1.3
            return total_percent / count / 100
        
        # Default
        return 1.3
    except Exception:
        return 1.3


def get_dates_for_day_of_week(day_of_week, num_weeks=4):
    """
    Get dates for a specific day of week for the last N weeks.
    day_of_week: 0=Saturday, 1=Sunday, ..., 6=Friday
    Returns list of dates, most recent first (week4, week3, week2, week1)
    """
    today = getdate()
    # Convert our day format (0=Sat) to Python weekday (0=Mon)
    # Saturday=5 in Python, Sunday=6, Monday=0, etc.
    python_weekday = (day_of_week + 5) % 7
    
    # Find the most recent occurrence of this day
    days_since = (today.weekday() - python_weekday) % 7
    if days_since == 0 and today.weekday() != python_weekday:
        days_since = 7
    
    most_recent = add_days(today, -days_since)
    
    # Get dates for last 4 weeks (most recent = week4)
    dates = []
    for i in range(num_weeks):
        dates.append(add_days(most_recent, -7 * i))
    
    # Reverse so week1 is oldest, week4 is newest
    dates.reverse()
    return dates


@frappe.whitelist()
def get_operating_rate_report(warehouse=None, item_group=None, day_of_week=None, increase_rate=None, from_date=None, to_date=None):
    """
    Get operating rate report - consumption over date range
    Data source: Stock Ledger Entry (outgoing quantities)
    day_of_week: 0=Saturday, 1=Sunday, ..., 6=Friday (optional filter for specific day)
    from_date, to_date: Date range to analyze
    increase_rate: Expected increase rate (fetched from Operating Rate doctype if not provided)
    """
    today = getdate()
    
    # Use provided date range or default to last 4 weeks
    if from_date and to_date:
        date_from = getdate(from_date)
        date_to = getdate(to_date)
    else:
        # Last 4 weeks (28 days)
        date_from = add_days(today, -27)
        date_to = today
    
    # Calculate number of days and weeks in range
    num_days = (date_to - date_from).days + 1
    num_weeks = max(1, num_days // 7) or 1
    
    # If day_of_week specified, filter only those days within the date range
    target_dates = None
    if day_of_week is not None and day_of_week != "":
        day_of_week = int(day_of_week)
        # Get all dates matching day_of_week within the range
        target_dates = []
        current = date_from
        python_weekday = (day_of_week + 5) % 7
        while current <= date_to:
            if current.weekday() == python_weekday:
                target_dates.append(current)
            current = add_days(current, 1)
        num_weeks = len(target_dates) or 1
    
    # Get day name for fetching increase_rate from doctype
    day_name = DAY_NAMES.get(int(day_of_week) if day_of_week is not None and day_of_week != "" else -1, None)
    
    # Fetch increase_rate from Operating Rate doctype based on target_dates (date range)
    if increase_rate is None or increase_rate == "":
        increase_rate = get_increase_rate_from_doctype(target_dates=target_dates, day_name=day_name)
    else:
        increase_rate = flt(increase_rate) or 1.3
    
    # Build filters
    conditions = ["sle.actual_qty < 0"]  # Only outgoing (consumed)
    params = {"date_from": date_from, "date_to": date_to}
    
    if warehouse:
        conditions.append("sle.warehouse = %(warehouse)s")
        params["warehouse"] = warehouse
    
    if item_group:
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = item_group
    
    # If filtering by specific day, add IN clause for those dates
    if target_dates:
        date_list = ", ".join([f"'{d}'" for d in target_dates])
        conditions.append(f"sle.posting_date IN ({date_list})")
    
    where_clause = " AND ".join(conditions)
    
    # Get daily consumption per item
    query = f"""
        SELECT 
            sle.item_code,
            i.item_name,
            i.item_group,
            i.stock_uom,
            sle.posting_date,
            SUM(sle.actual_qty * -1) as consumed_qty
        FROM `tabStock Ledger Entry` sle
        LEFT JOIN `tabItem` i ON i.name = sle.item_code
        WHERE sle.posting_date BETWEEN %(date_from)s AND %(date_to)s
        AND {where_clause}
        GROUP BY sle.item_code, sle.posting_date
        ORDER BY sle.item_code, sle.posting_date
    """
    
    daily_data = frappe.db.sql(query, params, as_dict=True)
    
    # Aggregate by item and week
    items = {}
    for row in daily_data:
        item_code = row["item_code"]
        if item_code not in items:
            items[item_code] = {
                "item_code": item_code,
                "item_name": row["item_name"],
                "item_group": row["item_group"],
                "stock_uom": row["stock_uom"],
                "week1": 0,
                "week2": 0,
                "week3": 0,
                "week4": 0,
                "total_qty": 0,
            }
        
        posting_date = getdate(row["posting_date"])
        
        # Determine week number
        if target_dates:
            # Find which week this date belongs to
            try:
                week_num = target_dates.index(posting_date) + 1
            except ValueError:
                continue
        else:
            # Calculate week based on date range
            days_diff = (posting_date - date_from).days
            week_num = min((days_diff // 7) + 1, 4)
        
        week_key = f"week{week_num}"
        items[item_code][week_key] += flt(row["consumed_qty"], 3)
        items[item_code]["total_qty"] += flt(row["consumed_qty"], 3)
    
    # Get current stock for all items
    stock_query = """
        SELECT item_code, SUM(actual_qty) as current_stock
        FROM `tabBin`
        WHERE actual_qty != 0
        {warehouse_filter}
        GROUP BY item_code
    """.format(
        warehouse_filter=f"AND warehouse = '{warehouse}'" if warehouse else ""
    )
    stock_data = frappe.db.sql(stock_query, as_dict=True)
    stock_map = {row["item_code"]: flt(row["current_stock"], 3) for row in stock_data}
    
    # Calculate daily average and other fields
    num_days = len(target_dates) if target_dates else (date_to - date_from).days + 1
    result = []
    for item_code, data in items.items():
        data["daily_avg"] = flt(data["total_qty"] / num_days, 3)
        data["increase_rate"] = increase_rate
        data["total_required"] = flt(data["daily_avg"] * increase_rate, 3)
        data["current_stock"] = stock_map.get(item_code, 0)
        data["required_qty"] = flt(data["total_required"] - data["current_stock"], 3)
        if data["required_qty"] < 0:
            data["required_qty"] = 0
        result.append(data)
    
    # Sort by total quantity descending
    result.sort(key=lambda x: x["total_qty"], reverse=True)
    
    # Week date ranges for display
    weeks = []
    if target_dates:
        for i, d in enumerate(target_dates):
            weeks.append({
                "week": i + 1,
                "label": f"أسبوع {i + 1}",
                "date": str(d),
            })
    else:
        for i in range(4):
            week_start = add_days(date_from, i * 7)
            week_end = add_days(week_start, 6)
            weeks.append({
                "week": i + 1,
                "label": f"أسبوع {i + 1}",
                "start": str(week_start),
                "end": str(week_end),
            })
    
    day_name = DAY_NAMES.get(day_of_week, "") if day_of_week is not None else ""
    
    return {
        "items": result,
        "weeks": weeks,
        "summary": {
            "date_from": str(date_from),
            "date_to": str(date_to),
            "num_weeks": num_weeks,
            "num_days": num_days,
            "total_items": len(result),
            "day_filter": day_name,
        }
    }


@frappe.whitelist()
def get_hourly_consumption_report(warehouse=None, item_group=None, from_date=None, to_date=None):
    """
    Get hourly consumption report for a date range
    Hours: 13:00 to 06:00 (next day)
    Data source: Stock Ledger Entry (outgoing quantities)
    Aggregates data across all dates in range
    """
    from frappe.utils import get_datetime
    
    if not from_date:
        from_date = getdate()
    else:
        from_date = getdate(from_date)
    
    if not to_date:
        to_date = from_date
    else:
        to_date = getdate(to_date)
    
    # Define hours (13:00 to 06:00 next day)
    hours = list(range(13, 24)) + list(range(0, 7))  # [13,14,...,23,0,1,2,3,4,5,6]
    
    # Build filters
    conditions = ["sle.actual_qty < 0"]
    params = {}
    
    if warehouse:
        conditions.append("sle.warehouse = %(warehouse)s")
        params["warehouse"] = warehouse
    
    if item_group:
        conditions.append("i.item_group = %(item_group)s")
        params["item_group"] = item_group
    
    where_clause = " AND ".join(conditions)
    
    # Query with hour extraction - cover date range and next day after to_date (for hours 0-6)
    next_to_date = add_days(to_date, 1)
    query = f"""
        SELECT 
            sle.item_code,
            i.item_name,
            i.item_group,
            i.stock_uom,
            sle.posting_date,
            HOUR(sle.posting_time) as posting_hour,
            SUM(sle.actual_qty * -1) as consumed_qty
        FROM `tabStock Ledger Entry` sle
        LEFT JOIN `tabItem` i ON i.name = sle.item_code
        WHERE (
            (sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND HOUR(sle.posting_time) >= 13)
            OR
            (sle.posting_date BETWEEN %(from_date_next)s AND %(to_date_next)s AND HOUR(sle.posting_time) < 7)
        )
        AND {where_clause}
        GROUP BY sle.item_code, HOUR(sle.posting_time)
        ORDER BY sle.item_code, HOUR(sle.posting_time)
    """
    params["from_date"] = from_date
    params["to_date"] = to_date
    params["from_date_next"] = add_days(from_date, 1)
    params["to_date_next"] = next_to_date
    
    hourly_data = frappe.db.sql(query, params, as_dict=True)
    
    # Aggregate by item and hour
    items = {}
    for row in hourly_data:
        item_code = row["item_code"]
        if item_code not in items:
            items[item_code] = {
                "item_code": item_code,
                "item_name": row["item_name"],
                "item_group": row["item_group"],
                "stock_uom": row["stock_uom"],
                "hourly": {str(h): 0 for h in hours},
                "total_qty": 0,
            }
        
        hour = int(row["posting_hour"])
        hour_key = str(hour)
        if hour_key in items[item_code]["hourly"]:
            items[item_code]["hourly"][hour_key] += flt(row["consumed_qty"], 3)
            items[item_code]["total_qty"] += flt(row["consumed_qty"], 3)
    
    result = list(items.values())
    result.sort(key=lambda x: x["total_qty"], reverse=True)
    
    # Hour labels for display
    hour_labels = []
    for h in hours:
        hour_labels.append({
            "hour": h,
            "label": f"{h}:00",
        })
    
    return {
        "items": result,
        "hours": hours,
        "hour_labels": hour_labels,
        "summary": {
            "date_from": str(from_date),
            "date_to": str(to_date),
            "num_days": (to_date - from_date).days + 1,
            "total_items": len(result),
        }
    }


@frappe.whitelist()
def get_warehouses():
    """Get list of warehouses for filter"""
    return frappe.get_all(
        "Warehouse",
        filters={"is_group": 0, "disabled": 0},
        fields=["name"],
        order_by="name",
        pluck="name"
    )


@frappe.whitelist()
def get_item_groups():
    """Get list of item groups for filter"""
    return frappe.get_all(
        "Item Group",
        filters={"is_group": 0},
        fields=["name"],
        order_by="name",
        pluck="name"
    )
