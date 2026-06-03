# -*- coding: utf-8 -*-
# Copyright (c) 2025, ecs_posnext and contributors
# For license information, please see license.txt

import json
from datetime import datetime, timedelta

import frappe
from frappe import _


@frappe.whitelist()
def get_orders(status=None, fromDelivery=False):
    """
    Fetch Sales Invoices grouped by kitchen status.
    Replaces posawesome get_sales_order3 but reads from Sales Invoice.
    """
    if isinstance(fromDelivery, str):
        fromDelivery = fromDelivery.lower() in ("true", "1")

    if fromDelivery:
        status_list = ["Delivery", "Completed"]
    elif status:
        status_list = [s.strip() for s in status.split(",")]
    else:
        status_list = ["Pending", "Preparing", "Dining", "Packing", "Delivery", "Completed"]

    grouped_result = {st: [] for st in status_list}

    so_type_filter = "AND t.custom_so_type = 'Delivery'" if fromDelivery else ""

    # Get user's permitted item classes
    items_class = frappe.get_list("item Class", fields=["name"])
    items_class_names = [row.name for row in items_class]

    # Hide Pickup orders from the fridge screen ONLY.
    # The fridge screen is identified by the user being scoped to the "ثلاجة"
    # item class alone. General screens (pending/prep) whose users also have
    # other classes (مطبخ/بار) must still show Pickup orders.
    hide_pickup = set(items_class_names) == {"ثلاجة"}
    if hide_pickup:
        so_type_filter += " AND t.custom_so_type NOT IN ('Pickup', 'Pick Up')"

    items_class_str = "', '".join(items_class_names)
    status_placeholders = "', '".join(status_list)

    query = f"""
        SELECT
            IFNULL(NULLIF(t1.custom_item_status, ''), 'Pending') AS status_name,
            t.custom_order_in_kitchen_ AS order_status,
            t.customer_name,
            t.branch,
            t.custom_number_order,
            t.name AS invoice_id,
            t.custom_so_type,
            t.custom_table_no,
            t.driver,
            D.cell_number,
            D.full_name AS driver_name,
            t.selling_price_list,
            t.creation,
            t.grand_total,
            t.posting_date,
            TIME(t.creation) AS creation_time,
            t.posa_notes,
            t.custom_time,
            t1.name AS item_row_name,
            t1.item_name AS item,
            t1.posa_notes AS item_notes,
            t1.qty AS item_qty
        FROM
            `tabSales Invoice` t
            JOIN `tabSales Invoice Item` t1 ON t.name = t1.parent
            LEFT JOIN `tabDriver` D ON D.name = t.driver
        WHERE
            IFNULL(NULLIF(t1.custom_item_status, ''), 'Pending') IN ('{status_placeholders}')
            AND t1.custom_item_class IN ('{items_class_str}')
            AND t.docstatus != 2
            AND t.is_return = 0
            AND IFNULL(t.custom_skip_kitchen, 0) = 0
            {so_type_filter}
        ORDER BY
            t.creation DESC,
            t.name DESC
    """

    rows = frappe.db.sql(query, as_dict=True)

    # Batch-fetch table numbers
    invoice_ids = list(set([row["invoice_id"] for row in rows]))
    tables_cache = {}
    if invoice_ids:
        tables_data = frappe.db.sql("""
            SELECT parent, table_no
            FROM `tabnumber of tables`
            WHERE parent IN %s
        """, (invoice_ids,), as_dict=True)
        for td in tables_data:
            if td.parent not in tables_cache:
                tables_cache[td.parent] = []
            tables_cache[td.parent].append(td.table_no)

    # Group results
    for row in rows:
        status_name = row["status_name"]
        invoice_id = row["invoice_id"]
        tables_number = " & ".join(tables_cache.get(invoice_id, []))
        existing_order = next(
            (o for o in grouped_result.get(status_name, []) if o["id"] == invoice_id),
            None,
        )
        if existing_order:
            existing_order["items"].append({
                "item": row["item"],
                "posa_notes": row["item_notes"],
                "item_qty": row["item_qty"],
                "item_row_name": row["item_row_name"],
            })
        else:
            if status_name not in grouped_result:
                grouped_result[status_name] = []
            grouped_result[status_name].append({
                "id": invoice_id,
                "name": invoice_id,
                "driver": row["driver"],
                "customer_name": row["customer_name"],
                "driver_cell_number": row["cell_number"],
                "driver_name": row["driver_name"],
                "selling_price_list": row["selling_price_list"],
                "branch": row["branch"],
                "status_name": status_name,
                "order_status": row["order_status"],
                "custom_number_order": row["custom_number_order"],
                "custom_so_type": row["custom_so_type"],
                "custom_table_no": tables_number,
                "time": row["custom_time"],
                "creation": row["creation"],
                "items": [{
                    "item": row["item"],
                    "posa_notes": row["item_notes"],
                    "item_qty": row["item_qty"],
                    "item_row_name": row["item_row_name"],
                }],
                "posa_notes": row["posa_notes"],
                "grand_total": row["grand_total"],
            })

    return [{"name": sn, "tasks": tasks} for sn, tasks in grouped_result.items()]


@frappe.whitelist()
def get_item_statuses(invoice_name):
    """Return item_code, custom_item_status, uom for all items in a Sales Invoice."""
    items = frappe.get_all(
        "Sales Invoice Item",
        filters={"parent": invoice_name},
        fields=["item_code", "custom_item_status", "uom", "name", "idx"],
        order_by="idx asc",
    )
    for item in items:
        if not item.get("custom_item_status"):
            item["custom_item_status"] = "Pending"
    return items


@frappe.whitelist()
def update_item_status(name, status, item_row_names=None, driver=None, time=None):
    """
    Update status of specific items in a Sales Invoice.
    If all items reach the same status, update the invoice-level status too.
    """
    si = frappe.get_doc("Sales Invoice", name)

    # Get user's permitted item classes
    user_permissions = frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "item Class"},
        fields=["for_value"],
    )
    permitted_classes = [p.for_value for p in user_permissions] if user_permissions else None

    if item_row_names:
        if isinstance(item_row_names, str):
            item_row_names = json.loads(item_row_names)

    for item in si.items:
        should_update = False
        if item_row_names:
            should_update = item.name in item_row_names
        elif permitted_classes:
            should_update = item.custom_item_class in permitted_classes
        else:
            should_update = True

        if should_update:
            item.custom_item_status = status

    # Handle driver assignment for Delivery
    if status == "Delivery" and driver:
        si.driver = driver

    # Check if all items share the same status → update invoice-level status
    all_statuses = [item.custom_item_status or "Pending" for item in si.items]
    if all_statuses and len(set(all_statuses)) == 1:
        si.custom_order_in_kitchen_ = all_statuses[0]

    if time is not None:
        si.custom_time = time

    # Capture old status before save for realtime notifications
    old_status = si.get_db_value("custom_order_in_kitchen_") or "Pending"

    si.save("Update")

    # Publish realtime events so all open kitchen pages refresh automatically.
    # The new-status page needs to know an order arrived;
    # the old-status page needs to know an order left.
    status_event_map = {
        "Pending": "kitchen_order_pending",
        "Preparing": "kitchen_order_preparing",
        "Packing": "kitchen_order_packing",
        "Delivery": "kitchen_order_delivery",
        "Completed": "kitchen_order_completed",
    }

    msg = {"invoice": name, "status": status, "old_status": old_status}

    # Notify the destination page
    if status in status_event_map:
        frappe.publish_realtime(
            event=status_event_map[status], message=msg, user=None, after_commit=True
        )

    # Notify the source page so it removes the card
    if old_status != status and old_status in status_event_map:
        frappe.publish_realtime(
            event=status_event_map[old_status], message=msg, user=None, after_commit=True
        )

    return {"success": True, "order_status": si.custom_order_in_kitchen_}


@frappe.whitelist()
def get_items(name):
    """
    Get items of a Sales Invoice (packed items + invoice items).
    """
    spi = frappe.db.sql(
        "SELECT * FROM `tabSelected Packed Items` WHERE parent = %s",
        (name,),
        as_dict=1,
    )
    items = frappe.db.sql(
        "SELECT * FROM `tabSales Invoice Item` WHERE parent = %s",
        (name,),
        as_dict=1,
    )
    return [spi, items]


@frappe.whitelist()
def cancel_invoice(name):
    """Cancel a Sales Invoice."""
    try:
        doc = frappe.get_doc("Sales Invoice", name)
        if doc.docstatus == 1:
            doc.cancel()
        frappe.db.commit()
        return {"status": "success", "message": f"Cancelled Sales Invoice {name}"}
    except Exception as e:
        frappe.log_error(f"Error cancelling Sales Invoice {name}: {str(e)}")
        return {"status": "error", "message": str(e)}
