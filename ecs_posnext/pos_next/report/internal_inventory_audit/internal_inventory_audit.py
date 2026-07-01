# Copyright (c) 2024, POSAwesome and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days, get_first_day, get_last_day
from collections import defaultdict

def execute(filters=None):
    """Main entry point for Script Report."""
    filters = validate_filters(filters)
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def validate_filters(filters):
    """Validate and normalize filters."""
    if not filters:
        filters = frappe._dict()
    
    # Convert month/year to date range if provided
    if filters.get("month") and filters.get("year"):
        month = int(filters.get("month"))
        year = int(filters.get("year"))
        filters["from_date"] = get_first_day(f"{year}-{month:02d}-01")
        filters["to_date"] = get_last_day(f"{year}-{month:02d}-01")
    
    # Validate required filters
    if not filters.get("warehouse"):
        frappe.throw(_("Warehouse (Branch) is required"))
    
    if not filters.get("from_date"):
        frappe.throw(_("From Date is required"))
    
    if not filters.get("to_date"):
        frappe.throw(_("To Date is required"))
    
    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be after To Date"))
    
    # Set company from warehouse if not provided
    if not filters.get("company"):
        filters["company"] = frappe.db.get_value("Warehouse", filters.get("warehouse"), "company")
    
    return filters


def get_columns():
    """Define report columns with Arabic labels."""
    return [
        {
            "fieldname": "item_code",
            "label": _("الصنف"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 180
        },
        {
            "fieldname": "stock_uom",
            "label": _("الوحدة"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "opening_qty",
            "label": _("رصيد أول"),
            "fieldtype": "Float",
            "width": 100
        },
        # {
        #     "fieldname": "incoming_store_qty",
        #     "label": _("محول من المخزن"),
        #     "fieldtype": "Float",
        #     "width": 120
        # },
        {
            "fieldname": "material_request_qty",
            "label": _("طلبيات"),
            "fieldtype": "Float",
            "width": 110
        },
        {
            "fieldname": "incoming_branch_qty",
            "label": _("محول إلى فرع"),
            "fieldtype": "Float",
            "width": 110
        },
        
        {
            "fieldname": "total_in_qty",
            "label": _("إجمالي الداخل"),
            "fieldtype": "Float",
            "width": 110
        },

         {
            "fieldname": "outgoing_branch_qty",
            "label": _("محول من فرع"),
            "fieldtype": "Float",
            "width": 110
        },
        {
            "fieldname": "waste_qty",
            "label": _("هالك"),
            "fieldtype": "Float",
            "width": 90
        },
        {
            "fieldname": "load_qty",
            "label": _("تحميل"),
            "fieldtype": "Float",
            "width": 90
        },
        {
            "fieldname": "sales_qty",
            "label": _("المبيعات"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "total_out_qty",
            "label": _("إجمالي الخارج"),
            "fieldtype": "Float",
            "width": 110
        },
        {
            "fieldname": "closing_count_qty",
            "label": _("الجرد الدفترى"),
            "fieldtype": "Float",
            "width": 110
        },
        {
            "fieldname": "actual_inventory_qty",
            "label": _("الجرد الفعلي"),
            "fieldtype": "Float",
            "width": 110
        },
        # {
        #     "fieldname": "actual_used_qty",
        #     "label": _("المستخدم الفعلي"),
        #     "fieldtype": "Float",
        #     "width": 110
        # },
        {
            "fieldname": "variance_qty",
            "label": _("العجز والزيادة"),
            "fieldtype": "Float",
            "width": 110
        },
        {
            "fieldname": "variance_percent",
            "label": _("النسبة التراكمية %"),
            "fieldtype": "Percent",
            "width": 110
        },
        {
            "fieldname": "avg_replenishment_days",
            "label": _("متوسط التأخير (يوم)"),
            "fieldtype": "Float",
            "width": 130
        }
    ]


def get_data(filters):
    """Build report data."""
    warehouse = filters.get("warehouse")
    central_warehouse = filters.get("central_warehouse")
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    # Get items to include
    items = get_items(filters)
    if not items:
        return []
    
    item_codes = [d.item_code for d in items]
    item_map = {d.item_code: d for d in items}
    
    # Get all data in bulk queries for performance
    opening_map = get_opening_balances(item_codes, warehouse, from_date)
    transfer_in_store, transfer_in_branch, transfer_out = get_transfer_movements(
        item_codes, warehouse, central_warehouse, from_date, to_date
    )
    material_request_map = get_material_request_quantities(
        item_codes, warehouse, central_warehouse, from_date, to_date
    )
    waste_map, load_map = get_stock_entry_type_movements(item_codes, warehouse, from_date, to_date)
    shortage_map = get_shortages(item_codes, warehouse, from_date, to_date)
    sales_map = get_sales_quantities(item_codes, warehouse, from_date, to_date, filters.get("company"))
    actual_inventory_map = get_actual_inventory(item_codes, warehouse, from_date, to_date)
    avg_replenishment_map = get_avg_replenishment_days(item_codes, warehouse, from_date, to_date)
    
    # Build rows
    data = []
    totals = defaultdict(float)
    
    for item_code in item_codes:
        item = item_map.get(item_code, {})
        
        # Get values from maps
        opening_qty = flt(opening_map.get(item_code, 0), 3)
        incoming_store_qty = flt(transfer_in_store.get(item_code, 0), 3)
        incoming_branch_qty = flt(transfer_in_branch.get(item_code, 0), 3)
        material_request_qty = flt(material_request_map.get(item_code, 0), 3)
        outgoing_branch_qty = flt(transfer_out.get(item_code, 0), 3)
        waste_qty = flt(waste_map.get(item_code, 0), 3)
        load_qty = flt(load_map.get(item_code, 0), 3)
        shortage_qty = flt(shortage_map.get(item_code, 0), 3)
        sales_qty = flt(sales_map.get(item_code, 0), 3)
        
        # Calculate derived fields
        # Add material_request_qty to total incoming
        total_in_qty = flt(opening_qty + incoming_store_qty + incoming_branch_qty + material_request_qty, 3)
        total_out_qty = flt(sales_qty+ outgoing_branch_qty + waste_qty + load_qty + shortage_qty, 3)
        # الجرد الدفتري = إجمالي الداخل - إجمالي الخارج
        closing_count_qty = flt(total_in_qty - total_out_qty, 3)
        # الجرد الفعلي من Inventory doctype
        actual_inventory_qty = flt(actual_inventory_map.get(item_code, 0), 3)
        actual_used_qty = flt(total_in_qty - total_out_qty, 3)
        variance_qty = flt(closing_count_qty - actual_inventory_qty, 3)
        # النسبة التراكمية = (العجز والزيادة / إجمالي الخارج) * 100
        variance_percent = flt((variance_qty / total_out_qty) * 100, 2) if total_out_qty else 0
        
        # Skip zero rows if not requested
        if not filters.get("include_zero_rows"):
            if all(v == 0 for v in [opening_qty, incoming_store_qty, incoming_branch_qty,
                                     material_request_qty, outgoing_branch_qty, waste_qty, load_qty, shortage_qty,
                                     closing_count_qty, sales_qty]):
                continue
        
        row = {
            "item_code": item_code,
            "stock_uom": item.get("stock_uom", ""),
            "opening_qty": opening_qty,
            "incoming_store_qty": incoming_store_qty,
            "incoming_branch_qty": incoming_branch_qty,
            "material_request_qty": material_request_qty,
            "total_in_qty": total_in_qty,
            "outgoing_branch_qty": outgoing_branch_qty,
            "waste_qty": waste_qty,
            "load_qty": load_qty,
            "shortage_qty": shortage_qty,
            "total_out_qty": total_out_qty,
            "closing_count_qty": closing_count_qty,
            "actual_inventory_qty": actual_inventory_qty,
            "actual_used_qty": actual_used_qty,
            "sales_qty": sales_qty,
            "variance_qty": variance_qty,
            "variance_percent": variance_percent,
            "avg_replenishment_days": flt(avg_replenishment_map.get(item_code, 0), 1),
        }
        data.append(row)
        
        # Accumulate totals
        for key in ["opening_qty", "incoming_store_qty", "incoming_branch_qty", "material_request_qty", "total_in_qty",
                    "outgoing_branch_qty", "waste_qty", "load_qty", "shortage_qty", "total_out_qty",
                    "closing_count_qty", "actual_inventory_qty", "actual_used_qty", "sales_qty", "variance_qty",
                    "variance_percent", "avg_replenishment_days"]:
            totals[key] += row[key]
    
    # Add totals row
    if data:
        totals_row = {
            "item_code": _("الإجمالي"),
            "stock_uom": "",
            "opening_qty": flt(totals["opening_qty"], 3),
            "incoming_store_qty": flt(totals["incoming_store_qty"], 3),
            "incoming_branch_qty": flt(totals["incoming_branch_qty"], 3),
            "material_request_qty": flt(totals["material_request_qty"], 3),
            "total_in_qty": flt(totals["total_in_qty"], 3),
            "outgoing_branch_qty": flt(totals["outgoing_branch_qty"], 3),
            "waste_qty": flt(totals["waste_qty"], 3),
            "load_qty": flt(totals["load_qty"], 3),
            "shortage_qty": flt(totals["shortage_qty"], 3),
            "total_out_qty": flt(totals["total_out_qty"], 3),
            "closing_count_qty": flt(totals["closing_count_qty"], 3),
            "actual_inventory_qty": flt(totals["actual_inventory_qty"], 3),
            "actual_used_qty": flt(totals["actual_used_qty"], 3),
            "sales_qty": flt(totals["sales_qty"], 3),
            "variance_qty": flt(totals["variance_qty"], 3),
            "variance_percent": flt((totals["variance_qty"] / totals["total_out_qty"]) * 100, 2) if totals["total_out_qty"] else 0,
            "avg_replenishment_days": flt(totals["avg_replenishment_days"] / len(data), 1) if data else 0,
        }
        data.append(totals_row)
    
    return data


def get_items(filters):
    """Get list of items to include in report."""
    conditions = ["i.disabled = 0", "i.is_stock_item = 1"]
    
    if filters.get("item_code"):
        conditions.append(f"i.item_code = %(item_code)s")
    
    if filters.get("item_group"):
        # Include child item groups
        item_groups = get_child_item_groups(filters.get("item_group"))
        conditions.append(f"i.item_group IN ({','.join(['%s'] * len(item_groups))})")
    
    query = f"""
        SELECT DISTINCT
            i.item_code,
            i.item_name,
            i.stock_uom,
            i.item_group
        FROM `tabItem` i
        WHERE {' AND '.join(conditions)}
        ORDER BY i.item_code
    """
    
    if filters.get("item_group"):
        return frappe.db.sql(query, tuple(item_groups) if item_groups else (), as_dict=True)
    
    return frappe.db.sql(query, filters, as_dict=True)


def get_child_item_groups(item_group):
    """Get item group and all its children."""
    item_groups = [item_group]
    
    children = frappe.db.sql("""
        SELECT name FROM `tabItem Group`
        WHERE parent_item_group = %s
    """, item_group, as_dict=True)
    
    for child in children:
        item_groups.extend(get_child_item_groups(child.name))
    
    return item_groups


def get_opening_balances(item_codes, warehouse, from_date):
    """
    Get opening balance (qty before from_date) for each item at the warehouse.
    Uses Stock Ledger Entry to get cumulative balance up to day before from_date.
    """
    if not item_codes:
        return {}
    
    opening_date = add_days(from_date, -1)
    
    # Get the last SLE before from_date for each item
    # This gives us the closing balance of the previous period = opening of current period
    query = """
        SELECT 
            sle.item_code,
            SUM(sle.actual_qty) as qty_after_transaction
        FROM `tabStock Ledger Entry` sle
        WHERE sle.item_code IN %(item_codes)s
            AND sle.warehouse = %(warehouse)s
            AND sle.posting_date <= %(from_date)s
            AND sle.is_cancelled = 0
        GROUP BY sle.item_code
    """
    
    result = frappe.db.sql(query, {
        "item_codes": item_codes,
        "warehouse": warehouse,
        "from_date": from_date
    }, as_dict=True)
    
    return {d.item_code: flt(d.qty_after_transaction) for d in result}


def get_transfer_movements(item_codes, warehouse, central_warehouse, from_date, to_date):
    """
    Get transfer movements (Material Transfer) for the warehouse.
    
    Returns:
        - transfer_in_store: inbound from central warehouse
        - transfer_in_branch: inbound from other warehouses (branches)
        - transfer_out: outbound to other warehouses
    
    Logic:
        - Material Transfer where t_warehouse = our warehouse -> incoming
        - Material Transfer where s_warehouse = our warehouse -> outgoing
        - Classify incoming based on source (central vs other)
    """
    if not item_codes:
        return {}, {}, {}
    
    transfer_in_store = defaultdict(float)
    transfer_in_branch = defaultdict(float)
    transfer_out = defaultdict(float)
    
    # Get incoming transfers (t_warehouse = our warehouse)
    incoming_query = """
        SELECT 
            sed.item_code,
            sed.qty,
            sed.s_warehouse
        FROM `tabStock Entry Detail` sed
        INNER JOIN `tabStock Entry` se ON se.name = sed.parent
        WHERE sed.item_code IN %(item_codes)s
            AND sed.t_warehouse = %(warehouse)s
            AND se.stock_entry_type = 'Material Transfer'
            AND se.docstatus = 1
            AND se.posting_date BETWEEN %(from_date)s AND %(to_date)s
    """
    
    incoming = frappe.db.sql(incoming_query, {
        "item_codes": item_codes,
        "warehouse": warehouse,
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=True)
    
    for row in incoming:
        item_code = row.item_code
        qty = flt(row.qty)
        source = row.s_warehouse
        
        # Classify based on source warehouse
        if central_warehouse and source == central_warehouse:
            # From central warehouse = "محول من المخزن"
            transfer_in_store[item_code] += qty
        else:
            # From other warehouse = "محول من فرع"
            transfer_in_branch[item_code] += qty
    
    # Get outgoing transfers (s_warehouse = our warehouse)
    outgoing_query = """
        SELECT 
            sed.item_code,
            SUM(sed.qty) as qty
        FROM `tabStock Entry Detail` sed
        INNER JOIN `tabStock Entry` se ON se.name = sed.parent
        WHERE sed.item_code IN %(item_codes)s
            AND sed.s_warehouse = %(warehouse)s
            AND se.stock_entry_type = 'Material Transfer'
            AND se.docstatus = 1
            AND se.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY sed.item_code
    """
    
    outgoing = frappe.db.sql(outgoing_query, {
        "item_codes": item_codes,
        "warehouse": warehouse,
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=True)
    
    for row in outgoing:
        transfer_out[row.item_code] = flt(row.qty)
    
    return dict(transfer_in_store), dict(transfer_in_branch), dict(transfer_out)


def get_stock_entry_type_movements(item_codes, warehouse, from_date, to_date):
    """
    Get movements classified by Stock Entry Type.
    
    - Consumptions -> waste_qty (هالك)
    - Loaded -> load_qty (تحميل)
    
    These are typically Material Issue entries where items leave the warehouse.
    """
    if not item_codes:
        return {}, {}
    
    waste_map = defaultdict(float)
    load_map = defaultdict(float)
    
    # Query for both types in one go
    query = """
        SELECT 
            sed.item_code,
            se.stock_entry_type,
            SUM(sed.qty) as qty
        FROM `tabStock Entry Detail` sed
        INNER JOIN `tabStock Entry` se ON se.name = sed.parent
        WHERE sed.item_code IN %(item_codes)s
            AND sed.s_warehouse = %(warehouse)s
            AND se.stock_entry_type IN ('Consumptions', 'Loaded')
            AND se.docstatus = 1
            AND se.posting_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY sed.item_code, se.stock_entry_type
    """
    
    result = frappe.db.sql(query, {
        "item_codes": item_codes,
        "warehouse": warehouse,
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=True)
    
    for row in result:
        if row.stock_entry_type == "Consumptions":
            waste_map[row.item_code] = flt(row.qty)
        elif row.stock_entry_type == "Loaded":
            load_map[row.item_code] = flt(row.qty)
    
    return dict(waste_map), dict(load_map)


def get_shortages(item_codes, warehouse, from_date, to_date):
    """
    Get shortages/negative adjustments from Stock Reconciliation.
    
    Shortages are calculated as negative quantity differences in Stock Reconciliation.
    Only considers adjustments where the difference is negative (actual < expected).
    
    TODO: Customize this function if your company tracks shortages differently.
    Current implementation: Uses Stock Reconciliation negative adjustments.
    Alternative approaches:
        - Custom Stock Entry Type for shortages
        - Custom field on Stock Entry
        - Separate Doctype for shortage tracking
    """
    if not item_codes:
        return {}
    
    shortage_map = defaultdict(float)
    
    # Get negative adjustments from Stock Reconciliation
    # Negative adjustment = current_qty < quantity_difference (loss)
    query = """
        SELECT 
            sri.item_code,
            SUM(ABS(sri.quantity_difference)) as shortage_qty
        FROM `tabStock Reconciliation Item` sri
        INNER JOIN `tabStock Reconciliation` sr ON sr.name = sri.parent
        WHERE sri.item_code IN %(item_codes)s
            AND sri.warehouse = %(warehouse)s
            AND sr.docstatus = 1
            AND sr.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND sri.quantity_difference < 0
        GROUP BY sri.item_code
    """
    
    result = frappe.db.sql(query, {
        "item_codes": item_codes,
        "warehouse": warehouse,
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=True)
    
    for row in result:
        shortage_map[row.item_code] = flt(row.shortage_qty)
    
    return dict(shortage_map)


def get_closing_counts(item_codes, warehouse, to_date):
    """
    Get closing inventory count (جرد آخر اليوم).
    
    Priority:
    1. Physical count from Stock Reconciliation on to_date (if exists)
    2. Fallback: Calculated closing balance from SLE
    
    Returns:
        - closing_map: {item_code: qty}
        - source_map: {item_code: 'physical' or 'ledger'} for reference
    """
    if not item_codes:
        return {}, {}
    
    closing_map = {}
    source_map = {}
    
    # First, try to get physical counts from Stock Reconciliation on to_date
    physical_query = """
        SELECT 
            sri.item_code,
            sri.qty as physical_qty
        FROM `tabStock Reconciliation Item` sri
        INNER JOIN `tabStock Reconciliation` sr ON sr.name = sri.parent
        WHERE sri.item_code IN %(item_codes)s
            AND sri.warehouse = %(warehouse)s
            AND sr.docstatus = 1
            AND sr.posting_date = %(to_date)s
    """
    
    physical_counts = frappe.db.sql(physical_query, {
        "item_codes": item_codes,
        "warehouse": warehouse,
        "to_date": to_date
    }, as_dict=True)
    
    physical_map = {d.item_code: flt(d.physical_qty) for d in physical_counts}
    
    # Get ledger closing balance for all items
    ledger_query = """
        SELECT 
            sle.item_code,
            SUM(sle.actual_qty) as closing_qty
        FROM `tabStock Ledger Entry` sle
        WHERE sle.item_code IN %(item_codes)s
            AND sle.warehouse = %(warehouse)s
            AND sle.posting_date <= %(to_date)s
            AND sle.is_cancelled = 0
        GROUP BY sle.item_code
    """
    
    ledger_result = frappe.db.sql(ledger_query, {
        "item_codes": item_codes,
        "warehouse": warehouse,
        "to_date": to_date
    }, as_dict=True)
    
    ledger_map = {d.item_code: flt(d.closing_qty) for d in ledger_result}
    
    # Build final map with priority: physical > ledger
    for item_code in item_codes:
        if item_code in physical_map:
            closing_map[item_code] = physical_map[item_code]
            source_map[item_code] = "physical"
        else:
            closing_map[item_code] = ledger_map.get(item_code, 0)
            source_map[item_code] = "ledger"
    
    return closing_map, source_map


def get_sales_quantities(item_codes, warehouse, from_date, to_date, company=None):
    """
    Get sales quantities from Sales Invoice (not POS Invoice).
    
    - Only submitted invoices (docstatus = 1)
    - Linked to the branch warehouse
    - Excludes returns (is_return = 1 or qty < 0)
    - Handles returns by subtracting returned quantities
    
    Returns logic:
        - Normal sale: qty > 0, is_return = 0 -> ADD to sales
        - Return: is_return = 1 OR qty < 0 -> SUBTRACT from sales
    """
    if not item_codes:
        return {}
    
    sales_map = defaultdict(float)
    
    # Query for sales (positive qty, not return)
    sales_query = """
        SELECT 
            sii.item_code,
            SUM(sii.qty) as qty
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE sii.item_code IN %(item_codes)s
            AND sii.warehouse = %(warehouse)s
            AND si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND IFNULL(si.is_return, 0) = 0
            AND sii.qty > 0
    """
    
    params = {
        "item_codes": item_codes,
        "warehouse": warehouse,
        "from_date": from_date,
        "to_date": to_date
    }
    
    if company:
        sales_query += " AND si.company = %(company)s"
        params["company"] = company
    
    sales_query += " GROUP BY sii.item_code"
    
    sales_result = frappe.db.sql(sales_query, params, as_dict=True)
    
    for row in sales_result:
        sales_map[row.item_code] = flt(row.qty)
    
    # Handle returns (subtract from sales)
    returns_query = """
        SELECT 
            sii.item_code,
            SUM(ABS(sii.qty)) as qty
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE sii.item_code IN %(item_codes)s
            AND sii.warehouse = %(warehouse)s
            AND si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            AND (si.is_return = 1 OR sii.qty < 0)
    """
    
    if company:
        returns_query += " AND si.company = %(company)s"
    
    returns_query += " GROUP BY sii.item_code"
    
    returns_result = frappe.db.sql(returns_query, params, as_dict=True)
    
    for row in returns_result:
        sales_map[row.item_code] -= flt(row.qty)
    
    return dict(sales_map)


def get_material_request_quantities(item_codes, warehouse, central_warehouse, from_date, to_date):
    """
    Get Material Request quantities for Material Transfer purpose.
    
    - Purpose: Material Transfer
    - Source Warehouse: المخزن الرئيسي - M (central_warehouse)
    - Target Warehouse: filter warehouse
    - Only submitted Material Requests (docstatus = 1)
    
    These quantities are added to total incoming.
    """
    if not item_codes:
        return {}
    
    if not central_warehouse:
        # If no central warehouse specified, use default "المخزن الرئيسي - M"
        central_warehouse = "المخزن الرئيسي - M"
    
    material_request_map = defaultdict(float)
    
    query = """
        SELECT 
            mri.item_code,
            SUM(mri.qty) as qty
        FROM `tabMaterial Request Item` mri
        INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
        WHERE mri.item_code IN %(item_codes)s
            AND mr.material_request_type = 'Material Transfer'
            AND mr.docstatus = 1
            AND mri.warehouse = %(target_warehouse)s
            AND mri.from_warehouse = %(source_warehouse)s
            AND mr.transaction_date BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY mri.item_code
    """
    
    result = frappe.db.sql(query, {
        "item_codes": item_codes,
        "target_warehouse": warehouse,
        "source_warehouse": central_warehouse,
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=True)
    
    for row in result:
        material_request_map[row.item_code] = flt(row.qty)
    
    return dict(material_request_map)


def get_actual_inventory(item_codes, warehouse, from_date, to_date):
    """
    Get actual inventory count from Inventory doctype.

    - Fetches from Inventory doctype where warehouse matches
    - Date is within the filter range
    - Only submitted documents (docstatus = 1)

    Returns the most recent inventory count for each item.
    """
    if not item_codes:
        return {}

    actual_inventory_map = defaultdict(float)

    # Get the latest inventory record for the warehouse within the date range
    query = """
        SELECT
            it.item as item_code,
            it.qty
        FROM `tabItems` it
        INNER JOIN `tabInventory` inv ON inv.name = it.parent
        WHERE it.item IN %(item_codes)s
            AND inv.warehouse = %(warehouse)s
            AND inv.docstatus = 1
            AND inv.date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY inv.date DESC
    """

    result = frappe.db.sql(query, {
        "item_codes": item_codes,
        "warehouse": warehouse,
        "from_date": from_date,
        "to_date": to_date
    }, as_dict=True)

    # Take the first (most recent) entry for each item
    for row in result:
        if row.item_code not in actual_inventory_map:
            actual_inventory_map[row.item_code] = flt(row.qty)

    return dict(actual_inventory_map)


def get_avg_replenishment_days(item_codes, warehouse, from_date, to_date):
    """
    حساب متوسط عدد الأيام من تاريخ Material Request حتى تاريخ Stock Entry المقابل.
    يُعبّر عن متوسط وقت الاستجابة لتجديد المخزون (Lead Time).
    """
    if not item_codes:
        return {}

    result = frappe.db.sql(
        """
        SELECT
            mri.item_code,
            AVG(DATEDIFF(se.posting_date, mr.transaction_date)) AS avg_days
        FROM `tabMaterial Request Item` mri
        INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
            AND mr.docstatus = 1
            AND mr.material_request_type = 'Material Transfer'
            AND mr.transaction_date BETWEEN %(from_date)s AND %(to_date)s
        INNER JOIN `tabStock Entry Detail` sed ON sed.item_code = mri.item_code
            AND sed.t_warehouse = %(warehouse)s
        INNER JOIN `tabStock Entry` se ON se.name = sed.parent
            AND se.stock_entry_type = 'Material Transfer'
            AND se.docstatus = 1
            AND se.posting_date BETWEEN mr.transaction_date AND DATE_ADD(mr.transaction_date, INTERVAL 60 DAY)
        WHERE mri.item_code IN %(item_codes)s
            AND mri.warehouse = %(warehouse)s
        GROUP BY mri.item_code
        """,
        {
            "item_codes": item_codes,
            "warehouse": warehouse,
            "from_date": from_date,
            "to_date": to_date,
        },
        as_dict=True,
    )

    return {r.item_code: flt(r.avg_days, 1) for r in result}
