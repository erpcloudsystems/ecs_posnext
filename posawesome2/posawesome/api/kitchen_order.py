# -*- coding: utf-8 -*-
# Copyright (c) 2021, Youssef Restom and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, add_days
from posawesome.posawesome.doctype.pos_coupon.pos_coupon import update_coupon_code_count
from posawesome.posawesome.api.posapp import get_company_domain
from posawesome.posawesome.doctype.delivery_charges.delivery_charges import (
    get_applicable_delivery_charges,
)
from datetime import datetime, date
from datetime import date

def is_time_in_shift(transaction_time_str, start_time_str, end_time_str):
    """
    Check if transaction_time_str ('HH:MM:SS') is within the shift defined by start_time_str and end_time_str.
    Handles cross-midnight shifts.
    """
    def time_to_minutes(t_str):
        h, m, s = map(int, t_str.split(":"))
        return h * 60 + m + s / 60

    transaction_minutes = time_to_minutes(transaction_time_str)
    start_minutes = time_to_minutes(start_time_str)
    end_minutes = time_to_minutes(end_time_str)

    if start_minutes < end_minutes:
        return start_minutes <= transaction_minutes <= end_minutes
    else:
        # Cross midnight shift
        return transaction_minutes >= start_minutes or transaction_minutes <= end_minutes


from datetime import datetime, date, timedelta
import frappe

def is_time_in_shift(transaction_time, start_time, end_time):
    """Check if a given time is within the shift time range (handles midnight wrap)."""
    start_minutes = int(start_time[:2]) * 60 + int(start_time[3:5])
    end_minutes = int(end_time[:2]) * 60 + int(end_time[3:5])
    trans_minutes = int(transaction_time[:2]) * 60 + int(transaction_time[3:5])

    if start_minutes <= end_minutes:
        return start_minutes <= trans_minutes <= end_minutes
    else:
        # Shift passes midnight
        return trans_minutes >= start_minutes or trans_minutes <= end_minutes

from datetime import date, datetime, timedelta
import frappe

def is_time_in_shift(order_time_str, start_time_str, end_time_str):
    """Check if a time is inside the shift, handling overnight shifts."""
    order_time = datetime.strptime(order_time_str, "%H:%M:%S").time()
    start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

    if start_time < end_time:
        # Normal same-day shift
        return start_time <= order_time <= end_time
    else:
        # Overnight shift (e.g., 13:00 to 04:00)
        return order_time >= start_time or order_time <= end_time


import frappe
from datetime import date, datetime, timedelta

from datetime import datetime, date, timedelta
import frappe

def get_shift_date_range(start_time_str, end_time_str):
    """Return the datetime range for the current shift based on start/end times."""
    now = datetime.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

    if start_time > end_time:  # Overnight shift case: e.g., 13:00 → 04:00
        if now.time() < end_time:
            # Before 04:00 → still yesterday’s shift
            start_dt = datetime.combine(yesterday, start_time)
            end_dt = datetime.combine(today, end_time)
        elif now.time() < start_time:
            # Between 04:00 and 13:00 → no active shift
            return None, None
        else:
            # After 13:00 today → today’s shift
            start_dt = datetime.combine(today, start_time)
            end_dt = datetime.combine(tomorrow, end_time)
    else:
        # Same-day shift (not overnight)
        if not (start_time <= now.time() <= end_time):
            return None, None
        start_dt = datetime.combine(today, start_time)
        end_dt = datetime.combine(today, end_time)

    return start_dt, end_dt


from datetime import datetime, date, timedelta
import frappe

def get_shift_date_range(start_time_str, end_time_str):
    """Return the datetime range for the current shift based on start/end times."""
    now = datetime.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

    if start_time > end_time:  # Overnight shift case: e.g., 13:00 → 04:00
        if now.time() < end_time:
            start_dt = datetime.combine(yesterday, start_time)
            end_dt = datetime.combine(today, end_time)
        elif now.time() < start_time:
            return None, None
        else:
            start_dt = datetime.combine(today, start_time)
            end_dt = datetime.combine(tomorrow, end_time)
    else:
        if not (start_time <= now.time() <= end_time):
            return None, None
        start_dt = datetime.combine(today, start_time)
        end_dt = datetime.combine(today, end_time)

    return start_dt, end_dt
@frappe.whitelist()
def get_sales_order3(status=None, fromDelivery=False, item_group=None):
    from datetime import datetime, timedelta

    # Step 1: Decide status list
    if fromDelivery:
        status_list = ["Delivery","Completed"] # Edit By Wael ELsafty
    elif status:
        status_list = [s.strip() for s in status.split(",")]
    else:
        status_list = ["Pending", "Preparing", "Dining", "Packing", "Delivery", "Completed"]

    grouped_result = {st: [] for st in status_list}
    # return grouped_result
    # Step 2: Get POS profile shift
    # shift = frappe.db.sql("""
    #     SELECT pos_profile
    #     FROM `tabPOS Opening Shift`
    #     WHERE status = 'Open' AND user = %s
    #     ORDER BY creation DESC
    #     LIMIT 1
    # """, (frappe.session.user,), as_dict=True)

    # branch_filter_sql = ""
    # branch_filter_param = None
    # start_time_str = "00:00:00"
    # end_time_str = "23:59:59"

    # if shift:
    #     pos_profile_name = shift[0].pos_profile
    #     pos_profile_times = frappe.db.get_value(
    #         "POS Profile",
    #         pos_profile_name,
    #         ["custom_start_time", "custom_end_time"],
    #         as_dict=True
    #     )

    #     for key in ["custom_start_time", "custom_end_time"]:
    #         val = pos_profile_times.get(key)
    #         if val and not isinstance(val, str):
    #             total_seconds = int(val.total_seconds())
    #             hours = total_seconds // 3600
    #             minutes = (total_seconds % 3600) // 60
    #             seconds = total_seconds % 60
    #             pos_profile_times[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    #     start_time_str = pos_profile_times.get("custom_start_time") or start_time_str
    #     end_time_str = pos_profile_times.get("custom_end_time") or end_time_str

    #     if pos_profile_name.lower() != "call center":
    #         branch_filter_sql = " AND t.branch = %s"
    #         branch_filter_param = pos_profile_name

    # now = frappe.utils.now_datetime()
    # today = now.date()
    # yesterday = today - timedelta(days=1)
    # tomorrow = today + timedelta(days=1)

    # shift_start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    # shift_end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

    # # Step 3: Build time condition + params
    # time_condition = ""
    # params = list(status_list)  # Start with status params

    # if shift_start_time < shift_end_time:
    #     if shift_start_time <= now.time() <= shift_end_time:
    #         time_condition = "AND t.transaction_date = %s AND TIME(t.creation) BETWEEN %s AND %s"
    #         params += [today, start_time_str, now.strftime("%H:%M:%S")]
    #     # else:
    #     #     return [{"name": st, "tasks": []} for st in status_list] # Edit By Wael ELsafty
    # else:
    #     if now.time() >= shift_start_time:
    #         time_condition = """AND (
    #             (t.transaction_date = %s AND TIME(t.creation) >= %s)
    #             OR
    #             (t.transaction_date = %s AND TIME(t.creation) <= %s)
    #         )"""
    #         params += [today, start_time_str, tomorrow, end_time_str]
    #     elif now.time() <= shift_end_time:
    #         time_condition = """AND (
    #             (t.transaction_date = %s AND TIME(t.creation) >= %s)
    #             OR
    #             (t.transaction_date = %s AND TIME(t.creation) <= %s)
    #         )"""
    #         params += [yesterday, start_time_str, today, end_time_str]
    #     # else:
    #     #     return [{"name": st, "tasks": []} for st in status_list] # Edit By Wael ELsafty

    # if branch_filter_param:
    #     time_condition += branch_filter_sql
    #     params.append(branch_filter_param)

    so_type_placeholders = "AND t.custom_so_type = 'Delivery'" if fromDelivery else ""
    # return status_list
    # Step 4: Build query
    status_placeholders = "', '".join(status_list)
    items_class = frappe.get_list(
        "item Class",
        fields=["name"]
        
    )
    items_class = [row.name for row in items_class]
    items_class = "', '".join(items_class)
    
    query = f"""
        SELECT
            t.custom_order_in_kitchen_ AS status_name,
            t.customer_name,
            t.branch,
            t.custom_number_order,
            t.name AS order_id,
            t.custom_so_type,
            t.custom_table_no,
            t.driver,
            D.cell_number,
            D.full_name AS driver_name,
            t.selling_price_list,
            t.creation,
            t.grand_total ,
            t.transaction_date,
            TIME(t.creation) AS creation_time,
            t.posa_notes,
            t.custom_time,
            t1.item_name AS item,
            t1.qty AS item_qty
        FROM
            `tabSales Order` t
            JOIN `tabSales Order Item` t1 ON t.name = t1.parent
            LEFT JOIN `tabDriver` D ON D.name = t.driver
        WHERE
            t.custom_order_in_kitchen_ IN ('{status_placeholders}')
            AND t1.custom_item_class IN('{items_class}')
            AND t.docstatus = 1
            {so_type_placeholders}
        ORDER BY
            t.creation DESC,
            t.name DESC
    """

    # Step 5: Run query
    rows = frappe.db.sql(query,  as_dict=True)
    # return rows
    # return rows
    # Step 6: Group results
    for row in rows:
        status_name = row["status_name"]
        order_id = row["order_id"]
        so = frappe.get_doc("Sales Order", order_id)
        tables_number = [d.table_no for d in so.custom_numbers_of_table]
        tables_number = " & ".join(tables_number)
        existing_order = next((o for o in grouped_result[status_name] if o["id"] == order_id), None)
        if existing_order:
            existing_order["items"].append({"item":row["item"], "item_qty":row["item_qty"]})
        else:
            grouped_result[status_name].append({
                "id": order_id,
                "name": order_id,
                "driver": row["driver"],
                "customer_name": row["customer_name"],
                "driver_cell_number": row["cell_number"],
                "driver_name": row["driver_name"],
                "selling_price_list": row["selling_price_list"],
                "branch": row["branch"],
                "status_name": status_name,
                "custom_number_order": row["custom_number_order"],
                "custom_so_type": row["custom_so_type"],
                "custom_table_no": tables_number,
                "time": row["custom_time"],
                "items": [{"item":row["item"], "item_qty":row["item_qty"]}],
                "posa_notes": row["posa_notes"],
                "grand_total": row["grand_total"],
            })

    return [{"name": status_name, "tasks": tasks} for status_name, tasks in grouped_result.items()]
@frappe.whitelist()
def get_sales_order(status=None, fromDelivery=False):
    from datetime import datetime, timedelta

    # Step 1: Decide status list
    if fromDelivery:
        status_list = ["Delivery","Completed"] # Edit By Wael ELsafty
    elif status:
        status_list = [s.strip() for s in status.split(",")]
    else:
        status_list = ["Pending", "Preparing", "Dining", "Packing", "Delivery", "Completed"]

    grouped_result = {st: [] for st in status_list}

    # Step 2: Get POS profile shift
    shift = frappe.db.sql("""
        SELECT pos_profile
        FROM `tabPOS Opening Shift`
        WHERE status = 'Open' AND user = %s
        ORDER BY creation DESC
        LIMIT 1
    """, (frappe.session.user,), as_dict=True)

    branch_filter_sql = ""
    branch_filter_param = None
    start_time_str = "00:00:00"
    end_time_str = "23:59:59"

    if shift:
        pos_profile_name = shift[0].pos_profile
        pos_profile_times = frappe.db.get_value(
            "POS Profile",
            pos_profile_name,
            ["custom_start_time", "custom_end_time"],
            as_dict=True
        )

        for key in ["custom_start_time", "custom_end_time"]:
            val = pos_profile_times.get(key)
            if val and not isinstance(val, str):
                total_seconds = int(val.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                pos_profile_times[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        start_time_str = pos_profile_times.get("custom_start_time") or start_time_str
        end_time_str = pos_profile_times.get("custom_end_time") or end_time_str

        if pos_profile_name.lower() != "call center":
            branch_filter_sql = " AND t.branch = %s"
            branch_filter_param = pos_profile_name

    now = frappe.utils.now_datetime()
    today = now.date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    shift_start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    shift_end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

    # Step 3: Build time condition + params
    time_condition = ""
    params = list(status_list)  # Start with status params

    if shift_start_time < shift_end_time:
        if shift_start_time <= now.time() <= shift_end_time:
            time_condition = "AND t.transaction_date = %s AND TIME(t.creation) BETWEEN %s AND %s"
            params += [today, start_time_str, now.strftime("%H:%M:%S")]
        # else:
        #     return [{"name": st, "tasks": []} for st in status_list] # Edit By Wael ELsafty
    else:
        if now.time() >= shift_start_time:
            time_condition = """AND (
                (t.transaction_date = %s AND TIME(t.creation) >= %s)
                OR
                (t.transaction_date = %s AND TIME(t.creation) <= %s)
            )"""
            params += [today, start_time_str, tomorrow, end_time_str]
        elif now.time() <= shift_end_time:
            time_condition = """AND (
                (t.transaction_date = %s AND TIME(t.creation) >= %s)
                OR
                (t.transaction_date = %s AND TIME(t.creation) <= %s)
            )"""
            params += [yesterday, start_time_str, today, end_time_str]
        # else:
        #     return [{"name": st, "tasks": []} for st in status_list] # Edit By Wael ELsafty

    if branch_filter_param:
        time_condition += branch_filter_sql
        params.append(branch_filter_param)

    so_type_placeholders = "AND t.custom_so_type = 'Delivery'" if fromDelivery else ""

    # Step 4: Build query
    status_placeholders = ', '.join(['%s'] * len(status_list))
    query = f"""
        SELECT
            t.custom_order_in_kitchen_ AS status_name,
            t.customer_name,
            t.branch,
            t.custom_number_order,
            t.name AS order_id,
            t.custom_so_type,
            t.custom_table_no,
            t.driver,
            D.cell_number,
            D.full_name AS driver_name,
            t.selling_price_list,
            t.creation,
            t.grand_total ,
            t.transaction_date,
            TIME(t.creation) AS creation_time,
            t.posa_notes,
            t.custom_time,
            t1.item_code AS item
        FROM
            `tabSales Order` t
            JOIN `tabSales Order Item` t1 ON t.name = t1.parent
            LEFT JOIN `tabDriver` D ON D.name = t.driver
        WHERE
            t.custom_order_in_kitchen_ IN ({status_placeholders})
            AND t.docstatus = 1
            {time_condition}
            {so_type_placeholders}
        ORDER BY
            t.creation DESC,
            t.name DESC
    """

    # Step 5: Run query
    rows = frappe.db.sql(query, tuple(params), as_dict=True)

    # Step 6: Group results
    for row in rows:
        status_name = row["status_name"]
        order_id = row["order_id"]
        existing_order = next((o for o in grouped_result[status_name] if o["id"] == order_id), None)
        if existing_order:
            existing_order["items"].append(row["item"])
        else:
            grouped_result[status_name].append({
                "id": order_id,
                "name": order_id,
                "driver": row["driver"],
                "customer_name": row["customer_name"],
                "driver_cell_number": row["cell_number"],
                "driver_name": row["driver_name"],
                "selling_price_list": row["selling_price_list"],
                "branch": row["branch"],
                "status_name": status_name,
                "custom_number_order": row["custom_number_order"],
                "custom_so_type": row["custom_so_type"],
                "custom_table_no": row["custom_table_no"],
                "time": row["custom_time"],
                "items": [row["item"]],
                "posa_notes": row["posa_notes"],
                "grand_total": row["grand_total"],
            })

    return [{"name": status_name, "tasks": tasks} for status_name, tasks in grouped_result.items()]

# @frappe.whitelist()
# def get_sales_order_test(status=None):
#     from datetime import datetime, timedelta

#     if status:
#         status_list = [s.strip() for s in status.split(",")]
#     else:
#         status_list = ["Pending", "Preparing", "Dining", "Packing", "Delivery", "Completed"]

#     grouped_result = {st: [] for st in status_list}

#     # Get open shift for current user
#     shift = frappe.db.sql("""
#         SELECT pos_profile
#         FROM `tabPOS Opening Shift`
#         WHERE status = 'Open' AND user = %s
#         ORDER BY creation DESC
#         LIMIT 1
#     """, (frappe.session.user,), as_dict=True)

#     branch_filter_sql = ""
#     branch_filter_param = None
#     start_time_str = "00:00:00"
#     end_time_str = "23:59:59"

#     if shift:
#         pos_profile_name = shift[0].pos_profile

#         pos_profile_times = frappe.db.get_value(
#             "POS Profile",
#             pos_profile_name,
#             ["custom_start_time", "custom_end_time"],
#             as_dict=True
#         )

#         for key in ["custom_start_time", "custom_end_time"]:
#             val = pos_profile_times.get(key)
#             if val and not isinstance(val, str):
#                 total_seconds = int(val.total_seconds())
#                 hours = total_seconds // 3600
#                 minutes = (total_seconds % 3600) // 60
#                 seconds = total_seconds % 60
#                 pos_profile_times[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

#         start_time_str = pos_profile_times.get("custom_start_time") or start_time_str
#         end_time_str = pos_profile_times.get("custom_end_time") or end_time_str

#         if pos_profile_name.lower() != "call center":
#             branch_filter_sql = " AND t.branch = %s "
#             branch_filter_param = pos_profile_name

#     # --------------------------
#     # Hardcode date/time for test
#     now = datetime(2025, 8, 13, 13, 30, 0)  # Simulate 14/8 at 2 AM
#     # --------------------------

#     today = now.date()
#     yesterday = today - timedelta(days=1)
#     tomorrow = today + timedelta(days=1)

#     shift_start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
#     shift_end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

#     # Build conditions
#     status_placeholders = ', '.join(['%s'] * len(status_list))
#     time_condition = ""
#     date_params = []

#     if shift_start_time < shift_end_time:
#         # Same-day shift
#         if shift_start_time <= now.time() <= shift_end_time:
#             time_condition = "AND t.transaction_date = %s AND TIME(t.creation) BETWEEN %s AND %s"
#             date_params = [today, start_time_str, now.strftime("%H:%M:%S")]
#         else:
#             return [{"name": st, "tasks": []} for st in status_list]
#     else:
#         # Overnight shift
#         if now.time() >= shift_start_time:
#             time_condition = """AND (
#                 (t.transaction_date = %s AND TIME(t.creation) >= %s)
#                 OR
#                 (t.transaction_date = %s AND TIME(t.creation) <= %s)
#             )"""
#             date_params = [today, start_time_str, tomorrow, end_time_str]

#         elif now.time() <= shift_end_time:
#             time_condition = """AND (
#                 (t.transaction_date = %s AND TIME(t.creation) >= %s)
#                 OR
#                 (t.transaction_date = %s AND TIME(t.creation) <= %s)
#             )"""
#             date_params = [yesterday, start_time_str, today, end_time_str]
#         else:
#             return [{"name": st, "tasks": []} for st in status_list]

#     query = f"""
#         SELECT
#             t.custom_order_in_kitchen_ AS status_name,
#             t.customer_name,
#             t.branch,
#             t.custom_number_order,
#             t.name AS order_id,
#             t.custom_so_type,
#             t.driver,
#             t.selling_price_list,
#             t.creation,
#             t.transaction_date,
#             TIME(t.creation) AS creation_time,
#             t.posa_notes,
#             t.custom_time,
#             t1.item_code AS item
#         FROM
#             `tabSales Order` t
#             JOIN `tabSales Order Item` t1 ON t.name = t1.parent
#         WHERE
#             t.custom_order_in_kitchen_ IN ({status_placeholders})
#             AND t.docstatus = 1
#             {time_condition}
#             {branch_filter_sql}
#         ORDER BY
#             t.creation DESC,
#             t.name DESC
#     """

#     params = tuple(status_list) + tuple(date_params)
#     if branch_filter_param:
#         params += (branch_filter_param,)

#     rows = frappe.db.sql(query, params, as_dict=True)

#     for row in rows:
#         status_name = row["status_name"]
#         order_id = row["order_id"]
#         existing_order = next((o for o in grouped_result[status_name] if o["id"] == order_id), None)
#         if existing_order:
#             existing_order["items"].append(row["item"])
#         else:
#             grouped_result[status_name].append({
#                 "id": order_id,
#                 "name": order_id,
#                 "driver": row["driver"],
#                 "customer_name": row["customer_name"],
#                 "selling_price_list": row["selling_price_list"],
#                 "branch": row["branch"],
#                 "status_name": status_name,
#                 "custom_number_order": row["custom_number_order"],
#                 "custom_so_type": row["custom_so_type"],
#                 "time": (row["custom_time"]),
#                 "items": [row["item"]],
#                 "posa_notes": row["posa_notes"],
#             })

#     return [{"name": status_name, "tasks": tasks} for status_name, tasks in grouped_result.items()]




from datetime import datetime, timedelta
import frappe

# @frappe.whitelist()
# def get_sales_order2(status=None):
#     from datetime import datetime, timedelta
#
#     if status:
#         status_list = [s.strip() for s in status.split(",")]
#     else:
#         status_list = ["Pending", "Preparing", "Dining", "Packing", "Delivery", "Completed"]
#
#     shift = frappe.db.sql("""
#         SELECT pos_profile
#         FROM `tabPOS Opening Shift`
#         WHERE status = 'Open' AND user = %s AND docstatus != 2
#         ORDER BY creation DESC
#         LIMIT 1
#     """, (frappe.session.user,), as_dict=True)
#
#     branch_filter_sql = ""
#     branch_filter_param = None
#     start_time_str = "00:00:00"
#     end_time_str = "23:59:59"
#
#     if shift:
#         pos_profile_name = shift[0].pos_profile
#         pos_profile_times = frappe.db.get_value(
#             "POS Profile",
#             pos_profile_name,
#             ["custom_start_time", "custom_end_time"],
#             as_dict=True
#         )
#
#         for key in ["custom_start_time", "custom_end_time"]:
#             val = pos_profile_times.get(key)
#             if val and not isinstance(val, str):
#                 total_seconds = int(val.total_seconds())
#                 hours = total_seconds // 3600
#                 minutes = (total_seconds % 3600) // 60
#                 seconds = total_seconds % 60
#                 pos_profile_times[key] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
#
#         start_time_str = pos_profile_times.get("custom_start_time") or start_time_str
#         end_time_str = pos_profile_times.get("custom_end_time") or end_time_str
#
#         if pos_profile_name.lower() != "call center":
#             branch_filter_sql = " AND t.branch = %s "
#             branch_filter_param = pos_profile_name
#
#     now = frappe.utils.now_datetime()
#     today = now.date()
#     yesterday = today - timedelta(days=1)
#     tomorrow = today + timedelta(days=1)
#
#     shift_start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
#     shift_end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()
#
#     time_condition = ""
#     date_params = []
#
#     if shift_start_time < shift_end_time:
#         if shift_start_time <= now.time() <= shift_end_time:
#             time_condition = "AND t.transaction_date = %s AND TIME(t.creation) BETWEEN %s AND %s"
#             date_params = [today, start_time_str, now.strftime("%H:%M:%S")]
#         else:
#             return []
#     else:
#         if now.time() >= shift_start_time:
#             time_condition = """AND (
#                 (t.transaction_date = %s AND TIME(t.creation) >= %s)
#                 OR
#                 (t.transaction_date = %s AND TIME(t.creation) <= %s)
#             )"""
#             date_params = [today, start_time_str, tomorrow, end_time_str]
#         elif now.time() <= shift_end_time:
#             time_condition = """AND (
#                 (t.transaction_date = %s AND TIME(t.creation) >= %s)
#                 OR
#                 (t.transaction_date = %s AND TIME(t.creation) <= %s)
#             )"""
#             date_params = [yesterday, start_time_str, today, end_time_str]
#         else:
#             return []
#
#     table_no_select = (
#         "t.custom_table_no"
#         if frappe.db.has_column("Sales Order", "custom_table_no")
#         else "NULL as custom_table_no"
#     )
#
#     status_placeholders = ', '.join(['%s'] * len(status_list))
#     query = f"""
#         SELECT
#             t.custom_order_in_kitchen_ AS status_name,
#             t.customer_name, t.branch, t.custom_number_order, t.name,
#             t1.item_code, t1.qty, t.custom_so_type, {table_no_select},
#             t.transaction_date, t.custom_unique_talbat_number, t.driver,
#             t.grand_total, t.contact_mobile,
#             D.cell_number, D.full_name AS driver_name
#         FROM `tabSales Order` t
#             JOIN `tabSales Order Item` t1 ON t.name = t1.parent
#             LEFT JOIN `tabDriver` D ON D.name = t.driver
#         WHERE t.custom_order_in_kitchen_ IN ({status_placeholders})
#             AND t.docstatus = 1
#             {time_condition}
#             {branch_filter_sql}
#         ORDER BY t.creation DESC, t.name DESC
#     """
#
#     params = tuple(status_list) + tuple(date_params)
#     if branch_filter_param:
#         params += (branch_filter_param,)
#
#     rows = frappe.db.sql(query, params, as_dict=True)
#
#     orders = {}
#     for row in rows:
#         order_name = row["name"]
#         if order_name not in orders:
#             orders[order_name] = {
#                 "name": order_name,
#                 "custom_number_order": row["custom_number_order"],
#                 "customer_name": row["customer_name"],
#                 "contact_mobile": row["contact_mobile"],
#                 "branch": row["branch"],
#                 "status_name": row["status_name"],
#                 "custom_unique_talbat_number": row["custom_unique_talbat_number"],
#                 "items": [],
#                 "transaction_date": row["transaction_date"],
#                 "custom_so_type": row["custom_so_type"],
#                 "custom_table_no": row["custom_table_no"],
#                 "driver": row["driver"],
#                 "cell_number": row["cell_number"],
#                 "grand_total": row["grand_total"],
#                 "driver_name": row["driver_name"],
#             }
#         orders[order_name]["items"].append({
#             "item_code": row["item_code"],
#             "qty": row["qty"]
#         })
#
#     return list(orders.values())


def _time_val_to_str(val):
    """Convert a timedelta or string time value to HH:MM:SS string."""
    if not val:
        return None
    if isinstance(val, str):
        return val
    total_seconds = int(val.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


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

    if shift_start < shift_end:
        # Same-day shift (e.g. 08:00 - 16:00)
        if shift_start <= now.time() <= shift_end:
            time_condition = "AND t.transaction_date = %s AND TIME(t.creation) BETWEEN %s AND %s"
            date_params = [today, start_str, end_str]
            return True, time_condition, date_params
    else:
        # Overnight shift (e.g. 22:00 - 06:00)
        if now.time() >= shift_start:
            time_condition = """AND (
                (t.transaction_date = %s AND TIME(t.creation) >= %s)
                OR
                (t.transaction_date = %s AND TIME(t.creation) <= %s)
            )"""
            date_params = [today, start_str, tomorrow, end_str]
            return True, time_condition, date_params
        elif now.time() <= shift_end:
            time_condition = """AND (
                (t.transaction_date = %s AND TIME(t.creation) >= %s)
                OR
                (t.transaction_date = %s AND TIME(t.creation) <= %s)
            )"""
            date_params = [yesterday, start_str, today, end_str]
            return True, time_condition, date_params

    return False, None, None


@frappe.whitelist()
def get_sales_order2(status=None):
    from datetime import datetime, timedelta

    if status:
        status_list = [s.strip() for s in status.split(",")]
    else:
        status_list = ["Pending", "Preparing", "Dining", "Packing", "Delivery", "Completed"]

    # Get the user's currently open POS shift
    shift = frappe.db.sql("""
        SELECT pos_profile
        FROM `tabPOS Opening Shift`
        WHERE status = 'Open' AND user = %s AND docstatus != 2
        ORDER BY creation DESC
        LIMIT 1
    """, (frappe.session.user,), as_dict=True)

    branch_filter_sql = ""
    branch_filter_param = None
    time_condition = ""
    date_params = []

    if shift:
        pos_profile_name = shift[0].pos_profile

        # Read shift fields from POS Profile
        profile_data = frappe.db.get_value(
            "POS Profile",
            pos_profile_name,
            [
                "posa_shift_1_start", "posa_shift_1_end",
                "posa_shift_2_start", "posa_shift_2_end",
                "posa_allow_sales_whole_day",
            ],
            as_dict=True,
        )

        # Always use shift_1_start → shift_2_end as the full day range
        now = frappe.utils.now_datetime()
        today = now.date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        day_start_str = _time_val_to_str(profile_data.get("posa_shift_1_start"))
        day_end_str = _time_val_to_str(profile_data.get("posa_shift_2_end"))

        if day_start_str and day_end_str:
            day_start = datetime.strptime(day_start_str, "%H:%M:%S").time()
            day_end = datetime.strptime(day_end_str, "%H:%M:%S").time()

            if day_start <= day_end:
                # Same-day range (e.g. 06:00 - 23:00)
                range_start = datetime.combine(today, day_start)
                range_end = datetime.combine(today, day_end)
            else:
                # Overnight range (e.g. 11:00 - 05:00 next day)
                if now.time() >= day_start:
                    range_start = datetime.combine(today, day_start)
                    range_end = datetime.combine(tomorrow, day_end)
                else:
                    range_start = datetime.combine(yesterday, day_start)
                    range_end = datetime.combine(today, day_end)

            time_condition = "AND t.creation BETWEEN %s AND %s"
            date_params = [range_start, range_end]
        else:
            # Fallback: no shift times configured, use today
            time_condition = "AND t.transaction_date = %s"
            date_params = [today]

        # Branch filter: call center sees all branches, others see only their own
        if pos_profile_name.lower() != "call center":
            branch_filter_sql = " AND t.branch = %s "
            branch_filter_param = pos_profile_name
    else:
        # No open shift: default to whole day today
        now = frappe.utils.now_datetime()
        today = now.date()
        time_condition = "AND t.transaction_date = %s"
        date_params = [today]

    # Handle optional custom fields
    table_no_select = (
        "t.custom_table_no"
        if frappe.db.has_column("Sales Order", "custom_table_no")
        else "NULL as custom_table_no"
    )

    # Build and execute query
    status_placeholders = ', '.join(['%s'] * len(status_list))

    query = f"""
        SELECT
            t.custom_order_in_kitchen_ AS status_name,
            t.customer_name,
            t.branch,
            t.custom_number_order,
            t.name,
            t1.item_code,
            t1.qty,
            t.custom_so_type,
            {table_no_select},
            t.transaction_date,
            t.custom_unique_talbat_number,
            t.driver,
            t.grand_total,
            t.contact_mobile,
            D.cell_number,
            D.full_name AS driver_name
        FROM
            `tabSales Order` t
            JOIN `tabSales Order Item` t1 ON t.name = t1.parent
            LEFT JOIN `tabDriver` D ON D.name = t.driver
        WHERE
            t.custom_order_in_kitchen_ IN ({status_placeholders})
            AND t.docstatus = 1
            {time_condition}
            {branch_filter_sql}
        ORDER BY
            t.creation DESC,
            t.name DESC
    """

    params = tuple(status_list) + tuple(date_params)
    if branch_filter_param:
        params += (branch_filter_param,)

    rows = frappe.db.sql(query, params, as_dict=True)

    # Group flat rows into orders with nested items
    orders = {}
    for row in rows:
        order_name = row["name"]
        if order_name not in orders:
            orders[order_name] = {
                "name": order_name,
                "custom_number_order": row["custom_number_order"],
                "customer_name": row["customer_name"],
                "contact_mobile": row["contact_mobile"],
                "branch": row["branch"],
                "status_name": row["status_name"],
                "custom_unique_talbat_number": row["custom_unique_talbat_number"],
                "items": [],
                "transaction_date": row["transaction_date"],
                "custom_so_type": row["custom_so_type"],
                "custom_table_no": row["custom_table_no"],
                "driver": row["driver"],
                "cell_number": row["cell_number"],
                "grand_total": row["grand_total"],
                "driver_name": row["driver_name"],
            }
        orders[order_name]["items"].append({
            "item_code": row["item_code"],
            "qty": row["qty"]
        })

    return list(orders.values())

# Shift windows for working day
SHIFT_WINDOWS = {
    "Morning": (13, 0, 22, 0),
    "Evening": (22, 0, 6, 0),
    "Whole Day": (13, 0, 6, 0),
}


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
def _compute_window(working_day, shift, pos_profiles=None, explicit_profile=None, shift_overrides=None):
    from frappe.utils import get_datetime
    shift_overrides = shift_overrides or {}
    # Resolve shift times: prefer POS Profile custom fields, fallback to static defaults
    custom = _get_shift_times(pos_profiles, explicit_profile)
    default = SHIFT_WINDOWS.get(shift, SHIFT_WINDOWS["Morning"])
    def pick(key, fallback):
        # order: override -> custom -> fallback
        override_val = _parse_time_parts(shift_overrides.get(key))
        if override_val:
            return override_val
        if custom.get(key):
            return custom[key]
        return fallback

    if shift == "Morning":
        start_h, start_m = pick("s1_start", default[:2])
        end_h, end_m = pick("s1_end", default[2:])
    elif shift == "Evening":
        start_h, start_m = pick("s2_start", default[:2])
        end_h, end_m = pick("s2_end", default[2:])
    else:  # Whole Day
        start_h, start_m = pick("s1_start", SHIFT_WINDOWS["Morning"][:2])
        end_h, end_m = pick("s2_end", SHIFT_WINDOWS["Evening"][2:])

    base = get_datetime(f"{working_day} 00:00:00")
    start_dt = base.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end_dt = base.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
    if (end_h, end_m) <= (start_h, start_m):
        end_dt = add_days(end_dt, 1)
    return start_dt, end_dt



# Used working_day / shift window logic with _get_shift_times / _compute_window.
# Replaced by new version that uses posa_shift_1/2 fields and posa_allow_sales_whole_day.
#
# @frappe.whitelist()
# def get_all_sales_order_in_all_branchs(status=None, branch=None, working_day=None, shift="Whole Day", date_from=None, date_to=None):
#     from frappe.utils import get_datetime, getdate
#
#     if status:
#         status_list = [s.strip() for s in status.split(",")]
#     else:
#         status_list = ["Pending", "Preparing", "Dining", "Packing", "Delivery", "Completed", "Cancelled"]
#
#     table_no_select = (
#         "t.custom_table_no"
#         if frappe.db.has_column("Sales Order", "custom_table_no")
#         else "NULL as custom_table_no"
#     )
#     branch_list = frappe.get_list("Branch", fields=["name"], pluck="name")
#
#     if date_from and date_to:
#         start_dt = get_datetime(f"{date_from} 00:00:00")
#         end_dt = get_datetime(f"{date_to} 23:59:59")
#     elif date_from:
#         start_dt = get_datetime(f"{date_from} 00:00:00")
#         end_dt = get_datetime(f"{date_from} 23:59:59")
#     else:
#         if not working_day:
#             working_day = getdate()
#             now = get_datetime()
#             current_time = (now.hour, now.minute)
#             shift_times = _get_shift_times()
#             start_h, start_m = shift_times.get("s1_start") or (13, 0)
#             end_h, end_m = shift_times.get("s2_end") or (6, 0)
#             if (end_h, end_m) <= (start_h, start_m):
#                 if current_time < (start_h, start_m):
#                     working_day = add_days(working_day, -1)
#         start_dt, end_dt = _compute_window(working_day, shift)
#
#     status_placeholders = ', '.join(['%s'] * len(status_list))
#     branch_placeholders = ', '.join(['%s'] * len(branch_list))
#     query = f"""
#         SELECT
#             t.custom_order_in_kitchen_ AS status_name,
#             si.docstatus as docstatus,
#             t.customer_name, t.branch, t.custom_number_order, t.name,
#             t1.item_code, t1.qty, t.custom_so_type, {table_no_select},
#             t.transaction_date, t.driver, t.contact_mobile,
#             t.custom_unique_talbat_number, t.grand_total,
#             D.cell_number, si.outstanding_amount as outstanding_amount,
#             D.full_name AS driver_name
#         FROM `tabSales Order` t
#             JOIN `tabSales Order Item` t1 ON t.name = t1.parent
#             JOIN `tabSales Invoice Item` sii ON sii.sales_order = t.name
#             JOIN `tabSales Invoice` si ON si.name = sii.parent
#             LEFT JOIN `tabDriver` D ON D.name = t.driver
#         WHERE t.custom_order_in_kitchen_ IN ({status_placeholders})
#             AND t.branch IN ({branch_placeholders})
#             AND TIMESTAMP(si.posting_date, IFNULL(si.posting_time, '00:00:00')) BETWEEN %s AND %s
#         ORDER BY t.creation DESC, t.name DESC
#     """
#
#     params = tuple(status_list) + tuple(branch_list) + (start_dt, end_dt)
#     rows = frappe.db.sql(query, params, as_dict=True)
#
#     orders = {}
#     for row in rows:
#         order_name = row["name"]
#         if order_name not in orders:
#             orders[order_name] = {
#                 "name": order_name,
#                 "custom_number_order": row["custom_number_order"],
#                 "customer_name": row["customer_name"],
#                 "branch": row["branch"],
#                 "status_name": row["status_name"],
#                 "items": [],
#                 "transaction_date": row["transaction_date"],
#                 "custom_so_type": row["custom_so_type"],
#                 "custom_table_no": row["custom_table_no"],
#                 "driver": row["driver"],
#                 "cell_number": row["cell_number"],
#                 "contact_mobile": row["contact_mobile"],
#                 "custom_unique_talbat_number": row["custom_unique_talbat_number"],
#                 "grand_total": row["grand_total"],
#                 "driver_name": row["driver_name"],
#                 "outstanding_amount": row["outstanding_amount"],
#             }
#         orders[order_name]["items"].append({
#             "item_code": row["item_code"],
#             "qty": row["qty"]
#         })
#
#     return list(orders.values())


@frappe.whitelist()
def get_all_sales_order_in_all_branchs(status=None, branch=None, date_from=None, date_to=None):
    from frappe.utils import get_datetime, getdate

    if status:
        status_list = [s.strip() for s in status.split(",")]
    else:
        status_list = ["Pending", "Preparing", "Dining", "Packing", "Delivery", "Completed", "Cancelled"]

    # Handle optional custom fields
    table_no_select = (
        "t.custom_table_no"
        if frappe.db.has_column("Sales Order", "custom_table_no")
        else "NULL as custom_table_no"
    )

    branch_list = frappe.get_list("Branch", fields=["name"], pluck="name")

    # Get the user's currently open POS shift to read shift config
    shift = frappe.db.sql("""
        SELECT pos_profile
        FROM `tabPOS Opening Shift`
        WHERE status = 'Open' AND user = %s AND docstatus != 2
        ORDER BY creation DESC
        LIMIT 1
    """, (frappe.session.user,), as_dict=True)

    # Compute date/time range
    if date_from and date_to:
        # Explicit date range provided
        start_dt = get_datetime(f"{date_from} 00:00:00")
        end_dt = get_datetime(f"{date_to} 23:59:59")
    elif date_from:
        # Only date_from — use that single day
        start_dt = get_datetime(f"{date_from} 00:00:00")
        end_dt = get_datetime(f"{date_from} 23:59:59")
    else:
        # No date range — use POS Profile shift config
        now = frappe.utils.now_datetime()
        today = now.date()

        if shift:
            pos_profile_name = shift[0].pos_profile
            profile_data = frappe.db.get_value(
                "POS Profile",
                pos_profile_name,
                [
                    "posa_shift_1_start", "posa_shift_1_end",
                    "posa_shift_2_start", "posa_shift_2_end",
                    "posa_allow_sales_whole_day",
                ],
                as_dict=True,
            )

            allow_whole_day = profile_data.get("posa_allow_sales_whole_day")

            frappe.msgprint(f"allow_whole_day: {allow_whole_day}")

            if allow_whole_day:
                # Whole day: today 00:00 to 23:59
                start_dt = get_datetime(f"{today} 00:00:00")
                end_dt = get_datetime(f"{today} 23:59:59")
            else:
                # Check which shift we're currently in
                shift_1_start = _time_val_to_str(profile_data.get("posa_shift_1_start"))
                shift_1_end = _time_val_to_str(profile_data.get("posa_shift_1_end"))
                shift_2_start = _time_val_to_str(profile_data.get("posa_shift_2_start"))
                shift_2_end = _time_val_to_str(profile_data.get("posa_shift_2_end"))

                matched = False
                time_start_str = None
                time_end_str = None

                # Try shift 1
                if shift_1_start and shift_1_end:
                    matched, _, _ = _is_now_in_shift(now, shift_1_start, shift_1_end)
                    if matched:
                        time_start_str = shift_1_start
                        time_end_str = shift_1_end

                # Try shift 2 if shift 1 didn't match
                if not matched and shift_2_start and shift_2_end:
                    matched, _, _ = _is_now_in_shift(now, shift_2_start, shift_2_end)
                    if matched:
                        time_start_str = shift_2_start
                        time_end_str = shift_2_end

                if not matched:
                    return []

                # Build datetime range from matched shift
                shift_start_time = datetime.strptime(time_start_str, "%H:%M:%S").time()
                shift_end_time = datetime.strptime(time_end_str, "%H:%M:%S").time()

                if shift_start_time < shift_end_time:
                    # Same-day shift
                    start_dt = get_datetime(f"{today} {time_start_str}")
                    end_dt = get_datetime(f"{today} {time_end_str}")
                else:
                    # Overnight shift
                    yesterday = today - timedelta(days=1)
                    tomorrow = today + timedelta(days=1)
                    if now.time() >= shift_start_time:
                        start_dt = get_datetime(f"{today} {time_start_str}")
                        end_dt = get_datetime(f"{tomorrow} {time_end_str}")
                    else:
                        start_dt = get_datetime(f"{yesterday} {time_start_str}")
                        end_dt = get_datetime(f"{today} {time_end_str}")
        else:
            # No open shift: default to whole day today
            start_dt = get_datetime(f"{today} 00:00:00")
            end_dt = get_datetime(f"{today} 23:59:59")

    # Build and execute query
    status_placeholders = ', '.join(['%s'] * len(status_list))
    branch_placeholders = ', '.join(['%s'] * len(branch_list))
    query = f"""
        SELECT
            t.custom_order_in_kitchen_ AS status_name,
            si.docstatus as docstatus,
            t.customer_name,
            t.branch,
            t.custom_number_order,
            t.name,
            t1.item_code,
            t1.qty,
            t.custom_so_type,
            {table_no_select},
            t.transaction_date,
            t.driver,
            t.contact_mobile,
            t.custom_unique_talbat_number,
            t.grand_total,
            D.cell_number,
            si.outstanding_amount as outstanding_amount,
            D.full_name AS driver_name
        FROM
            `tabSales Order` t
            JOIN `tabSales Order Item` t1 ON t.name = t1.parent
            JOIN `tabSales Invoice Item` sii ON sii.sales_order = t.name
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            LEFT JOIN `tabDriver` D ON D.name = t.driver
        WHERE
            t.custom_order_in_kitchen_ IN ({status_placeholders})
            AND t.branch IN ({branch_placeholders})
            AND TIMESTAMP(si.posting_date, IFNULL(si.posting_time, '00:00:00')) BETWEEN %s AND %s
        ORDER BY
            t.creation DESC,
            t.name DESC
    """

    params = tuple(status_list) + tuple(branch_list) + (start_dt, end_dt)
    rows = frappe.db.sql(query, params, as_dict=True)

    # Group flat rows into orders with nested items
    orders = {}
    for row in rows:
        order_name = row["name"]
        if order_name not in orders:
            orders[order_name] = {
                "name": order_name,
                "custom_number_order": row["custom_number_order"],
                "customer_name": row["customer_name"],
                "branch": row["branch"],
                "status_name": row["status_name"],
                "items": [],
                "transaction_date": row["transaction_date"],
                "custom_so_type": row["custom_so_type"],
                "custom_table_no": row["custom_table_no"],
                "driver": row["driver"],
                "cell_number": row["cell_number"],
                "contact_mobile": row["contact_mobile"],
                "custom_unique_talbat_number": row["custom_unique_talbat_number"],
                "grand_total": row["grand_total"],
                "driver_name": row["driver_name"],
                "outstanding_amount": row["outstanding_amount"],
            }
        orders[order_name]["items"].append({
            "item_code": row["item_code"],
            "qty": row["qty"]
        })

    return list(orders.values())

@frappe.whitelist()
def update_sales_order(name, status, driver=None, time = None):

    # frappe.db.set_value('Sales Order', name, {
    # 'custom_order_in_kitchen_': status
    # })
    so= frappe.get_doc('Sales Order', name)
    if status== 'Delivery':
        so.driver = driver
        sales_invoice = frappe.db.sql("""SELECT parent from `tabSales Invoice Item` where sales_order = %s """, (name,), as_dict=True)
        if sales_invoice:
            # Update the driver in the Sales Invoice
            frappe.db.set_value('Sales Invoice', sales_invoice[0].parent, {
                'driver': driver
            })

    so.custom_order_in_kitchen_ = status
    so.custom_time = time
    so.save('Update')
    frappe.publish_realtime(
        event="sales_order_updated",
        message={"so": name, "status": status},
        after_commit=True
    )
    
    return
@frappe.whitelist()
def update_sales_order_driver(name, status, driver=None, time = None):

    # frappe.db.set_value('Sales Order', name, {
    # 'custom_order_in_kitchen_': status
    # })
    so= frappe.get_doc('Sales Order', name)
    if status== 'Delivery':
        so.driver = driver
        sales_invoice = frappe.db.sql("""SELECT parent from `tabSales Invoice Item` where sales_order = %s """, (name,), as_dict=True)
        if sales_invoice:
            # Update the driver in the Sales Invoice
            frappe.db.set_value('Sales Invoice', sales_invoice[0].parent, {
                'driver': driver
            })

    so.custom_order_in_kitchen_ = "Completed"
    so.custom_time = time
    so.save('Update')
    frappe.publish_realtime(
        event="sales_order_updated",
        message={"so": name, "status": status},
        after_commit=True
    )
    
    return

@frappe.whitelist()
def get_items_sales_order(name):

    spi= frappe.db.sql(f"""SELECT * FROM `tabSelected Packed Items` where parent = '{name}' """, as_dict =1 )
    items= frappe.db.sql(f"""SELECT * FROM `tabSales Order Item` where parent = '{name}' """, as_dict =1 )
    
    return [spi, items]

@frappe.whitelist()
def get_sales_invoice_from_order(sales_order):
    invoice = frappe.db.sql("""
        SELECT DISTINCT parent, outstanding_amount
        FROM `tabSales Invoice Item`
        Join `tabSales Invoice` ON `tabSales Invoice`.name = `tabSales Invoice Item`.parent
        WHERE sales_order = %s
        LIMIT 1
    """, sales_order, as_dict=True)
    return invoice

@frappe.whitelist()
def cancel_sales_order_and_invoices(sales_order):
    """Cancel all Sales Invoices linked to a Sales Order, then cancel the Sales Order."""
    
    # 1. Cancel linked Sales Invoices
    invoices = frappe.get_all(
        "Sales Invoice Item",
        filters={"sales_order": sales_order},
        fields=["parent"]
    )

    cancelled_invoices = 0
    for inv in invoices:
        try:
            doc_inv = frappe.get_doc("Sales Invoice", inv.parent)
            if doc_inv.docstatus == 1:  # Submitted
                doc_inv.ignore_permissions = True
                doc_inv.flags.ignore_validate_update_after_submit = True
                doc_inv.flags.ignore_links = True  # Ignore links for cancel
                doc_inv.cancel()
                cancelled_invoices += 1
        except Exception as e:
            frappe.log_error(f"Error cancelling Sales Invoice {inv.parent}: {str(e)}")
    
    # 2. Cancel the Sales Order
    try:
        so_doc = frappe.get_doc("Sales Order", sales_order)
        if so_doc.docstatus == 1:
            so_doc.ignore_permissions = True
            so_doc.flags.ignore_validate_update_after_submit = True
            so_doc.flags.ignore_links = True
            so_doc.cancel()
    except Exception as e:
        frappe.log_error(f"Error cancelling Sales Order {sales_order}: {str(e)}")
        return {"status": "error", "message": str(e)}

    frappe.db.commit()

    return {
        "status": "success",
        "message": f"Cancelled {cancelled_invoices} invoices and Sales Order {sales_order}."
    }

@frappe.whitelist()
def get_stock_items_for_wastage(sales_order):
    """Get stock items from Sales Order items and packed items for wastage selection."""
    stock_items = []
    
    # Get items from Sales Order Item where is_stock_item = 1
    so_items = frappe.db.sql("""
        SELECT soi.item_code, soi.item_name, soi.qty, soi.uom, soi.warehouse
        FROM `tabSales Order Item` soi
        JOIN `tabItem` i ON i.name = soi.item_code
        WHERE soi.parent = %s AND i.is_stock_item = 1
    """, sales_order, as_dict=True)
    
    for item in so_items:
        stock_items.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": item.qty,
            "original_qty": item.qty,
            "uom": item.uom or "Nos",
            "warehouse": item.warehouse,
            "source": "items"
        })
    
    # Get Sales Invoice linked to this Sales Order
    invoice = frappe.db.sql("""
        SELECT DISTINCT sii.parent
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE sii.sales_order = %s AND si.docstatus = 1
        LIMIT 1
    """, sales_order, as_dict=True)
    
    # Get items from Packed Item in Sales Invoice where is_stock_item = 1
    if invoice:
        invoice_name = invoice[0].parent
        packed_items = frappe.db.sql("""
            SELECT pi.item_code, i.item_name, pi.qty
            FROM `tabPacked Item` pi
            JOIN `tabItem` i ON i.name = pi.item_code
            WHERE pi.parent = %s AND i.is_stock_item = 1
        """, invoice_name, as_dict=True)
        
        for item in packed_items:
            stock_items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "original_qty": item.qty,
                "uom": "Nos",
                "warehouse": default_warehouse if 'default_warehouse' in dir() else None,
                "source": "packed_items"
            })
    
    return stock_items
from frappe.utils import flt, nowdate

@frappe.whitelist()
def cancel_sales_order_with_wastage(sales_order, is_wastage=False, items_to_return="[]", wastage_items="[]", stock_entry_type="Consumptions",employee=None):
    """Cancel Sales Order with wastage handling - create stock entry for wastage items only."""
    import json
    
    is_wastage = is_wastage if isinstance(is_wastage, bool) else is_wastage == "true" or is_wastage == True
    items_to_return = json.loads(items_to_return) if isinstance(items_to_return, str) else items_to_return
    wastage_items = json.loads(wastage_items) if isinstance(wastage_items, str) else wastage_items


    # Get Sales Order details for warehouse info
    so_doc = frappe.get_doc("Sales Order", sales_order)
    company = so_doc.company
    
    # Get default warehouse from first item or company default
    default_warehouse = None
    if so_doc.items:
        default_warehouse = so_doc.items[0].warehouse
    if not default_warehouse:
        default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
    
    wastage_stock_entry_name = None

    if stock_entry_type == "Loaded" and not employee:
        frappe.throw("يجب اختيار موظف")
    
    # Create Stock Entry for wastage items - items NOT selected for return
    # Items selected for return will be returned automatically when invoice is cancelled
    if is_wastage and wastage_items and len(wastage_items) > 0:
        try:
            stock_entry = frappe.new_doc("Stock Entry")
            stock_entry.stock_entry_type = stock_entry_type  # Consumptions or Loaded
            stock_entry.posting_date = nowdate()
            stock_entry.set_posting_time = 1
            
            # Add custom field for wastage type if exists
            if hasattr(stock_entry, 'custom_wastedge_type'):
                stock_entry.custom_wastedge_type = stock_entry_type
            
            # Add reference to sales order
            if hasattr(stock_entry, 'custom_wastedge_reference'):
                stock_entry.custom_wastedge_reference = sales_order

            # add employee
            if employee:
                stock_entry.custom_empolyee = employee
            
            # Add wastage items
            for item in wastage_items:
                if item.get("qty", 0) > 0:
                    stock_entry.append("items", {
                        "item_code": item.get("item_code"),
                        "qty": item.get("qty"),
                        "uom": item.get("uom", "Nos"),
                        "s_warehouse": default_warehouse,
                    })
            
            if stock_entry.items:
                stock_entry.insert()
                stock_entry.submit()
                wastage_stock_entry_name = stock_entry.name

        except Exception as e:
            frappe.log_error(title="Wastage Stock Entry Error", message=str(e))
    
    # Cancel linked Sales Invoices
    invoices = frappe.get_all(
        "Sales Invoice Item",
        filters={"sales_order": sales_order},
        fields=["parent"]
    )

    cancelled_invoices = 0
    for inv in invoices:
        try:
            doc_inv = frappe.get_doc("Sales Invoice", inv.parent)
            if doc_inv.docstatus == 1:
                doc_inv.ignore_permissions = True
                doc_inv.flags.ignore_validate_update_after_submit = True
                doc_inv.flags.ignore_links = True
                doc_inv.cancel()
                cancelled_invoices += 1
        except Exception as e:
            frappe.log_error(title="Cancel Invoice Error", message=str(e))
    
    # Cancel the Sales Order - reload to get latest version
    try:
        so_doc = frappe.get_doc("Sales Order", sales_order)
        if so_doc.docstatus == 1:
            so_doc.ignore_permissions = True
            so_doc.flags.ignore_validate_update_after_submit = True
            so_doc.flags.ignore_links = True
            so_doc.cancel()
    except Exception as e:
        frappe.log_error(title="Cancel Sales Order Error", message=f"Error cancelling Sales Order {sales_order}: {str(e)}")
        return {"status": "error", "message": str(e)}

    frappe.db.commit()

    return {
        "status": "success",
        "message": f"Cancelled {cancelled_invoices} invoices and Sales Order {sales_order}.",
        "wastage_stock_entry": wastage_stock_entry_name,
        "is_wastage": is_wastage
    }

@frappe.whitelist()
def update_status_to_preparing(sales_order):
    if not sales_order:
        frappe.throw("Sales order is required")

    doc = frappe.get_doc("Sales Order", sales_order)
    doc.custom_order_in_kitchen_ = "Preparing"  # Or your field name for status
    doc.save()
    frappe.db.commit()
    return {"status": "success"}


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
