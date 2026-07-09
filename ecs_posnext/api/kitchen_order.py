# -*- coding: utf-8 -*-
# Copyright (c) 2024, POS Next and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.utils import flt, nowdate, get_datetime, add_days, now_datetime, get_time
from datetime import datetime, date, timedelta

@frappe.whitelist()
def get_stock_items_for_wastage(sales_invoice):
    """Get stock items from Sales Invoice items and packed items for wastage selection."""
    stock_items = []
    
    # Get items from Sales Invoice Item where is_stock_item = 1
    si_items = frappe.db.sql("""
        SELECT sii.item_code, sii.item_name, sii.qty, sii.uom, sii.warehouse
        FROM `tabSales Invoice Item` sii
        JOIN `tabItem` i ON i.name = sii.item_code
        WHERE sii.parent = %s AND i.is_stock_item = 1
    """, sales_invoice, as_dict=True)
    
    for item in si_items:
        stock_items.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": abs(item.qty),
            "original_qty": abs(item.qty),
            "uom": item.uom or "Nos",
            "warehouse": item.warehouse,
            "source": "items"
        })
    
    # Get items from Packed Item in Sales Invoice where is_stock_item = 1
    packed_items = frappe.db.sql("""
        SELECT pi.item_code, i.item_name, pi.qty, pi.warehouse
        FROM `tabPacked Item` pi
        JOIN `tabItem` i ON i.name = pi.item_code
        WHERE pi.parent = %s AND i.is_stock_item = 1
    """, sales_invoice, as_dict=True)
    
    for item in packed_items:
        stock_items.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": abs(item.qty),
            "original_qty": abs(item.qty),
            "uom": "Nos",
            "warehouse": item.warehouse,
            "source": "packed_items"
        })
    
    return stock_items

@frappe.whitelist()
def verify_cancel_manager(pos_profile=None, password=None):
    """Verify a manager password for authorizing an order cancellation.

    Passwords are stored (encrypted) on the ``POS Manager`` doctype and are
    never shipped to the browser. A manager is valid for the given POS Profile
    when it has no allowed profiles configured (valid for all) or the profile is
    listed. Returns the matched manager name so it can be recorded for audit.
    """
    from frappe.utils.password import get_decrypted_password

    password = (password or "").strip()
    if not password:
        return {"valid": False}

    managers = frappe.get_all("POS Manager", filters={"enabled": 1}, fields=["name", "manager_name"])
    for m in managers:
        allowed_profiles = frappe.get_all(
            "POS Manager POS Profile",
            filters={"parent": m.name},
            pluck="pos_profile",
        )
        # Empty list => manager may authorize on all profiles.
        if allowed_profiles and pos_profile and pos_profile not in allowed_profiles:
            continue

        stored = get_decrypted_password("POS Manager", m.name, "password", raise_exception=False)
        if stored and stored == password:
            return {"valid": True, "manager": m.manager_name or m.name}

    return {"valid": False}


@frappe.whitelist()
def cancel_sales_invoice_with_wastage(sales_invoice, is_wastage=False, items_to_return="[]", wastage_items="[]", stock_entry_type="Consumptions", employee=None, cancelled_by_manager=None):
    """Cancel Sales Invoice with wastage handling - create stock entry for wastage items."""
    
    is_wastage = is_wastage if isinstance(is_wastage, bool) else is_wastage == "true" or is_wastage == True
    items_to_return = json.loads(items_to_return) if isinstance(items_to_return, str) else items_to_return
    wastage_items = json.loads(wastage_items) if isinstance(wastage_items, str) else wastage_items

    # Get Sales Invoice details
    si_doc = frappe.get_doc("Sales Invoice", sales_invoice)
    company = si_doc.company
    
    # Get default warehouse
    default_warehouse = None
    if si_doc.items:
        default_warehouse = si_doc.items[0].warehouse
    if not default_warehouse:
        default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
    
    wastage_stock_entry_name = None

    has_wastage_items = bool(is_wastage and wastage_items and len(wastage_items) > 0)

    # Employee is only required for a "Loaded" wastage stock entry — i.e. when a
    # wastage stock entry is actually going to be created. A plain cancellation
    # (No wastage) must never demand an employee.
    if has_wastage_items and stock_entry_type == "Loaded" and not employee:
        frappe.throw(_("Please select an employee"))

    # Create Stock Entry for wastage items
    if has_wastage_items:
        try:
            stock_entry = frappe.new_doc("Stock Entry")
            stock_entry.stock_entry_type = stock_entry_type  # Consumptions or Loaded
            stock_entry.posting_date = nowdate()
            stock_entry.set_posting_time = 1
            stock_entry.company = company
            
            # Add custom field for wastage type if exists
            if hasattr(stock_entry, 'custom_wastedge_type'):
                stock_entry.custom_wastedge_type = stock_entry_type
            
            # Add reference to sales invoice
            if hasattr(stock_entry, 'custom_wastedge_reference'):
                stock_entry.custom_wastedge_reference = sales_invoice

            # add employee
            if employee:
                stock_entry.custom_empolyee = employee
            
            # Add wastage items
            for item in wastage_items:
                if flt(item.get("qty", 0)) > 0:
                    stock_entry.append("items", {
                        "item_code": item.get("item_code"),
                        "qty": item.get("qty"),
                        "uom": item.get("uom", "Nos"),
                        "s_warehouse": item.get("warehouse") or default_warehouse,
                    })
            
            if stock_entry.items:
                stock_entry.insert()
                stock_entry.submit()
                wastage_stock_entry_name = stock_entry.name

        except Exception as e:
            frappe.log_error(title="Wastage Stock Entry Error", message=str(e))
    
    # Identify linked Sales Orders
    sales_orders = set()
    for item in si_doc.items:
        if item.sales_order:
            sales_orders.add(item.sales_order)

    # Cancel the Sales Invoice
    try:
        if si_doc.docstatus == 1:
            si_doc.ignore_permissions = True
            si_doc.flags.ignore_validate_update_after_submit = True
            si_doc.flags.ignore_links = True
            si_doc.cancel()
    except Exception as e:
        frappe.log_error(title="Cancel Invoice Error", message=f"Error cancelling Sales Invoice {sales_invoice}: {str(e)}")
        return {"status": "error", "message": str(e)}

    # Record which manager authorized the cancellation (audit trail)
    if cancelled_by_manager:
        try:
            frappe.db.set_value(
                "Sales Invoice", sales_invoice,
                "custom_cancelled_by_manager", cancelled_by_manager,
                update_modified=False,
            )
        except Exception:
            frappe.log_error(title="Record Cancel Manager Error", message=frappe.get_traceback())

    # Cancel linked Sales Orders
    for so_name in sales_orders:
        try:
            so_doc = frappe.get_doc("Sales Order", so_name)
            if so_doc.docstatus == 1:
                # Check if all invoices for this SO are cancelled
                invoices = frappe.get_all("Sales Invoice Item", filters={"sales_order": so_name}, fields=["parent"])
                all_cancelled = True
                for inv in invoices:
                    if frappe.db.get_value("Sales Invoice", inv.parent, "docstatus") == 1:
                        all_cancelled = False
                        break
                
                if all_cancelled:
                    so_doc.ignore_permissions = True
                    so_doc.flags.ignore_validate_update_after_submit = True
                    so_doc.flags.ignore_links = True
                    so_doc.cancel()
        except Exception as e:
            frappe.log_error(title="Cancel Sales Order Error", message=str(e))

    frappe.db.commit()

    return {
        "status": "success",
        "message": _("Invoice {0} cancelled successfully.").format(sales_invoice),
        "wastage_stock_entry": wastage_stock_entry_name,
        "is_wastage": is_wastage
    }


def _is_now_in_shift(now, start_str, end_str):
    """Check if current time falls within a shift window.
    Handles both same-day and overnight shifts.
    Returns (matched, time_condition_sql, date_params).
    """
    today = now.date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    shift_start = datetime.strptime(start_str, "%H:%M:%S").time()
    shift_end = datetime.strptime(end_str, "%H:%M:%S").time()

    if shift_start <= shift_end:
        # Same-day shift (e.g. 08:00 to 17:00)
        if shift_start <= now.time() <= shift_end:
            cond = "AND t.transaction_date = %s AND TIME(t.creation) BETWEEN %s AND %s"
            params = [today, start_str, end_str]
            return True, cond, params
    else:
        # Overnight shift (e.g. 22:00 to 06:00)
        if now.time() >= shift_start:
            cond = "AND ((t.transaction_date = %s AND TIME(t.creation) >= %s) OR (t.transaction_date = %s AND TIME(t.creation) <= %s))"
            params = [today, start_str, tomorrow, end_str]
            return True, cond, params
        elif now.time() <= shift_end:
            cond = "AND ((t.transaction_date = %s AND TIME(t.creation) >= %s) OR (t.transaction_date = %s AND TIME(t.creation) <= %s))"
            params = [yesterday, start_str, today, end_str]
            return True, cond, params

    return False, "", []


def _parse_time_parts(val):
    if not val:
        return None
    try:
        h, m, s = val.hour, val.minute, val.second
        return h, m
    except Exception:
        pass
    if isinstance(val, str):
        parts = val.strip().split(":")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])
    return None


def _get_shift_times(pos_profiles=None, explicit_profile=None):
    if explicit_profile:
        candidates = [explicit_profile]
    else:
        candidates = list(pos_profiles or [])
    if not candidates:
        candidates = frappe.get_all("POS Profile", filters={"disabled": 0}, pluck="name") or []
    if not candidates:
        candidates = frappe.get_all("POS Profile", pluck="name") or []
    fields = ["posa_shift_1_start", "posa_shift_1_end", "posa_shift_2_start", "posa_shift_2_end"]
    for profile in candidates:
        data = frappe.db.get_value("POS Profile", profile, fields, as_dict=True) or {}
        parsed = {
            "s1_start": _parse_time_parts(data.get("posa_shift_1_start")),
            "s1_end": _parse_time_parts(data.get("posa_shift_1_end")),
            "s2_start": _parse_time_parts(data.get("posa_shift_2_start")),
            "s2_end": _parse_time_parts(data.get("posa_shift_2_end")),
        }
        if any(parsed.values()):
            return parsed
    return {}


@frappe.whitelist()
def get_sales_order2(status=None):
    if status:
        status_list = [s.strip() for s in status.split(",")]
    else:
        status_list = ["Pending", "Preparing", "Dining", "Packing", "Delivery", "Completed"]

    # Separate status into SO and SI
    so_statuses = [s for s in status_list if s != "Completed"]
    include_completed = "Completed" in status_list

    # Get the user's currently open POS shift
    shift = frappe.db.sql("""
        SELECT pos_profile
        FROM `tabPOS Opening Shift`
        WHERE status = 'Open' AND user = %s AND docstatus != 2
        ORDER BY creation DESC
        LIMIT 1
    """, (frappe.session.user,), as_dict=True)

    branch_filter_sql_so = ""
    branch_filter_sql_si = ""
    branch_filter_param = None
    time_condition_so = ""
    time_condition_si = ""
    date_params = []

    if shift:
        pos_profile_name = shift[0].pos_profile
        profile_data = frappe.db.get_value(
            "POS Profile",
            pos_profile_name,
            ["custom_shift_start_time", "custom_shift_end_time"],
            as_dict=True,
        )

        start_time = profile_data.get("custom_shift_start_time") if profile_data else None
        end_time = profile_data.get("custom_shift_end_time") if profile_data else None

        now = now_datetime()
        today = now.date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        start_t = get_time(start_time) if start_time else None
        end_t = get_time(end_time) if end_time else None

        # A zero-width window (start == end) is invalid configuration and would
        # filter out every order; treat it as "no window" (whole day) instead.
        if start_t and end_t and start_t != end_t:
            current_time = now.time()

            if start_t <= end_t:
                # Same-day range (e.g. 06:00 - 23:00)
                if current_time >= start_t:
                    range_start = datetime.combine(today, start_t)
                    range_end = datetime.combine(today, end_t)
                else:
                    range_start = datetime.combine(yesterday, start_t)
                    range_end = datetime.combine(yesterday, end_t)
            else:
                # Overnight range (e.g. 13:00 - 05:00)
                if current_time >= start_t:
                    range_start = datetime.combine(today, start_t)
                    range_end = datetime.combine(tomorrow, end_t)
                else:
                    range_start = datetime.combine(yesterday, start_t)
                    range_end = datetime.combine(today, end_t)

            time_condition_so = "AND t.creation BETWEEN %s AND %s"
            time_condition_si = "AND TIMESTAMP(t.posting_date, t.posting_time) BETWEEN %s AND %s"
            date_params = [range_start, range_end]
        else:
            time_condition_so = "AND t.transaction_date = %s"
            time_condition_si = "AND t.posting_date = %s"
            date_params = [today]

        if pos_profile_name.lower() != "call center":
            branch_filter_sql_so = " AND t.branch = %s "
            branch_filter_sql_si = " AND t.branch = %s "
            branch_filter_param = pos_profile_name
    else:
        now = now_datetime()
        today = now.date()
        time_condition_so = "AND t.transaction_date = %s"
        time_condition_si = "AND t.posting_date = %s"
        date_params = [today]

    # Check which table to use for kitchen status
    # User says "in new version no Sales Order", so we prioritize Sales Invoice
    use_si_exclusively = not frappe.db.exists("DocType", "Sales Order") or True # Force True as per user request
    
    kitchen_status_col = "custom_order_in_kitchen_"
    has_kitchen_col_si = frappe.db.has_column("Sales Invoice", kitchen_status_col)
    
    table_no_col_si = "custom_table_number" if frappe.db.has_column("Sales Invoice", "custom_table_number") else "NULL"
    order_type_col_si = "custom_order_type" if frappe.db.has_column("Sales Invoice", "custom_order_type") else "NULL"

    queries = []
    # frappe.throw(f"{branch_filter_sql_si}")
    # Query for Sales Invoices (All requested statuses)
    if include_completed or so_statuses:
        status_cond = ""
        if has_kitchen_col_si:
            # If status_list includes 'Completed', we might need to handle it specially 
            # if 'Completed' is not a value in custom_order_in_kitchen_ but implied by docstatus
            placeholders = ', '.join(['%s'] * len(status_list))
            status_cond = f"AND (t.{kitchen_status_col} IN ({placeholders}) OR (t.docstatus = 1 AND 'Completed' IN ({placeholders})))"
        else:
            # Fallback: if no kitchen col, use docstatus
            if "Completed" in status_list:
                status_cond = "AND (t.docstatus = 1)"
            else:
                status_cond = "AND (t.docstatus = 0)"

        queries.append(f"""
            SELECT
                IF(t.docstatus=1, 'Completed', COALESCE(t.{kitchen_status_col if has_kitchen_col_si else "status"}, 'Pending')) AS status_name,
                t.customer_name,
                t.branch,
                t.custom_number_order,
                t.name,
                t1.item_code,
                t1.qty,
                t.{order_type_col_si} AS order_type,
                t.{table_no_col_si} AS table_no,
                t.posting_date AS transaction_date,
                t.custom_unique_talbat_number,
                t.driver,
                t.grand_total,
                COALESCE(cust.mobile_no, '') AS contact_mobile,
                COALESCE(cust.custom_other_mobile_no, '') AS other_mobile_no,
                D.full_name AS driver_name,
                t.creation,
                ko.status AS kds_status
            FROM
                `tabSales Invoice` t
                JOIN `tabSales Invoice Item` t1 ON t.name = t1.parent
                LEFT JOIN `tabDriver` D ON D.name = t.driver
                LEFT JOIN `tabCustomer` cust ON cust.name = t.customer
                LEFT JOIN `tabKDS Order` ko ON ko.sales_invoice = t.name
            WHERE
                t.docstatus != 2
                {status_cond}
                {time_condition_si}
                {branch_filter_sql_si}
        """)
    # frappe.throw(f"{queries}")
    if not queries:
        return []

    full_query = " UNION ALL ".join(queries) + " ORDER BY creation DESC, name DESC"
    
    # Collect all parameters
    all_params = []
    if has_kitchen_col_si:
        all_params.extend(status_list)
        all_params.extend(status_list)
    all_params.extend(date_params)
    if branch_filter_param:
        all_params.append(branch_filter_param)

    rows = frappe.db.sql(full_query, tuple(all_params), as_dict=True)
    # frappe.throw(f"{all_params}")
    # Group flat rows into orders with nested items
    orders = {}
    for row in rows:
        order_name = row["name"]
        if order_name not in orders:
            orders[order_name] = {
                "name": order_name,
                "custom_number_order": row["custom_number_order"],
                "customer_name": row["customer_name"],
                "contact_mobile": row.get("contact_mobile") or "",
                "other_mobile_no": row.get("other_mobile_no") or "",
                "branch": row["branch"],
                "status_name": row["status_name"],
                "custom_unique_talbat_number": row["custom_unique_talbat_number"],
                "items": [],
                "transaction_date": row["transaction_date"],
                "custom_so_type": row["order_type"],
                "custom_table_no": row["table_no"],
                "driver": row["driver"],
                "grand_total": row["grand_total"],
                "driver_name": row["driver_name"],
                "kds_status": row.get("kds_status"),
                "order_time": str(row["creation"]) if row.get("creation") else None,
            }
        orders[order_name]["items"].append({
            "item_code": row["item_code"],
            "qty": row["qty"]
        })

    return list(orders.values())


@frappe.whitelist()
def update_sales_order(name, status, driver=None, time=None):
    doctype = "Sales Order" if frappe.db.exists("Sales Order", name) else "Sales Invoice"
    doc = frappe.get_doc(doctype, name)
    
    if status == 'Delivery':
        doc.driver = driver
        if doctype == "Sales Order":
            sales_invoice = frappe.db.sql("""SELECT parent from `tabSales Invoice Item` where sales_order = %s """, (name,), as_dict=True)
            if sales_invoice:
                frappe.db.set_value('Sales Invoice', sales_invoice[0].parent, {'driver': driver})

    if hasattr(doc, 'custom_order_in_kitchen_'):
        doc.custom_order_in_kitchen_ = status
    doc.custom_time = time
    doc.save('Update')
    
    frappe.publish_realtime(
        event="sales_order_updated",
        message={"so": name, "status": status},
        after_commit=True
    )
    return


@frappe.whitelist()
def update_sales_order_driver(name, status, driver=None, time=None):
    doctype = "Sales Order" if frappe.db.exists("Sales Order", name) else "Sales Invoice"
    doc = frappe.get_doc(doctype, name)
    
    if status == 'Delivery':
        doc.driver = driver
        if doctype == "Sales Order":
            sales_invoice = frappe.db.sql("""SELECT parent from `tabSales Invoice Item` where sales_order = %s """, (name,), as_dict=True)
            if sales_invoice:
                frappe.db.set_value('Sales Invoice', sales_invoice[0].parent, {'driver': driver})

    if hasattr(doc, 'custom_order_in_kitchen_'):
        doc.custom_order_in_kitchen_ = "Completed"
    doc.custom_time = time
    doc.save('Update')
    
    frappe.publish_realtime(
        event="sales_order_updated",
        message={"so": name, "status": status},
        after_commit=True
    )
    return


@frappe.whitelist()
def get_items_sales_order(name):
    # Try Sales Order first
    if frappe.db.exists("Sales Order", name):
        spi = frappe.db.sql(f"""SELECT * FROM `tabSelected Packed Items` where parent = %s """, (name,), as_dict=1)
        items = frappe.db.sql(f"""SELECT * FROM `tabSales Order Item` where parent = %s """, (name,), as_dict=1)
        return [spi, items]
    # Try Sales Invoice
    elif frappe.db.exists("Sales Invoice", name):
        # Sales Invoice usually doesn't have Selected Packed Items in the same way, but let's check
        spi = frappe.db.sql(f"""SELECT * FROM `tabSelected Packed Items` where parent = %s """, (name,), as_dict=1)
        items = frappe.db.sql(f"""SELECT * FROM `tabSales Invoice Item` where parent = %s """, (name,), as_dict=1)
        return [spi, items]
    return [[], []]


@frappe.whitelist()
def get_sales_invoice_from_order(sales_order):
    # If it's already an invoice, return itself
    if frappe.db.exists("Sales Invoice", sales_order):
        return [{"parent": sales_order}]
        
    invoice = frappe.db.sql("""
        SELECT DISTINCT parent, outstanding_amount
        FROM `tabSales Invoice Item`
        Join `tabSales Invoice` ON `tabSales Invoice`.name = `tabSales Invoice Item`.parent
        WHERE sales_order = %s
        LIMIT 1
    """, sales_order, as_dict=True)
    return invoice


@frappe.whitelist()
def cancel_sales_order_and_invoices(sales_order, cancelled_by_manager=None):
    """Cancel all Sales Invoices linked to a Sales Order, then cancel the Sales Order.
       If an invoice name is passed, cancel it and its linked Sales Order.
    """
    so_name = sales_order
    invoices_to_cancel = []

    if frappe.db.exists("Sales Invoice", sales_order):
        invoices_to_cancel.append(sales_order)
        # Try to find linked Sales Order
        so_name = frappe.db.get_value("Sales Invoice Item", {"parent": sales_order}, "sales_order")
    else:
        # It's a Sales Order, find all linked invoices
        linked_invoices = frappe.get_all(
            "Sales Invoice Item",
            filters={"sales_order": sales_order},
            fields=["parent"]
        )
        invoices_to_cancel = [inv.parent for inv in linked_invoices]

    cancelled_invoices = 0
    for inv_name in invoices_to_cancel:
        try:
            doc_inv = frappe.get_doc("Sales Invoice", inv_name)
            if doc_inv.docstatus == 1:  # Submitted
                doc_inv.ignore_permissions = True
                doc_inv.flags.ignore_validate_update_after_submit = True
                doc_inv.flags.ignore_links = True
                doc_inv.cancel()
                cancelled_invoices += 1
                if cancelled_by_manager:
                    try:
                        frappe.db.set_value(
                            "Sales Invoice", inv_name,
                            "custom_cancelled_by_manager", cancelled_by_manager,
                            update_modified=False,
                        )
                    except Exception:
                        frappe.log_error(title="Record Cancel Manager Error", message=frappe.get_traceback())
        except Exception as e:
            frappe.log_error(f"Error cancelling Sales Invoice {inv_name}: {str(e)}")
    
    # 2. Cancel the Sales Order
    if so_name and frappe.db.exists("Sales Order", so_name):
        try:
            so_doc = frappe.get_doc("Sales Order", so_name)
            if so_doc.docstatus == 1:
                so_doc.ignore_permissions = True
                so_doc.flags.ignore_validate_update_after_submit = True
                so_doc.flags.ignore_links = True
                so_doc.cancel()
        except Exception as e:
            frappe.log_error(f"Error cancelling Sales Order {so_name}: {str(e)}")
            # Even if SO fails, we might have cancelled invoices
    
    frappe.db.commit()

    return {
        "status": "success",
        "message": f"Cancelled {cancelled_invoices} invoices and Sales Order {so_name}."
    }

@frappe.whitelist()
def get_drivers_by_branch(branch=None):
    """Get drivers by branch without permission check."""
    filters = {}
    if branch:
        filters["custom_branch"] = branch
    
    drivers = frappe.get_all(
        "Driver",
        filters=filters,
        fields=["name", "full_name", "cell_number"],
        ignore_permissions=True,
        limit=1000
    )
    return drivers
