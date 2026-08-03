# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from collections import defaultdict
import frappe
from frappe import _
from frappe.utils import getdate, get_datetime, add_days


CALL_CENTER_POS_PROFILE = "Call Center"


@frappe.whitelist()
def get_call_center_users():
    """Get all users assigned to the Call Center POS Profile"""
    users = frappe.get_all(
        "POS Profile User",
        filters={"parent": CALL_CENTER_POS_PROFILE},
        pluck="user"
    )
    return users or []


@frappe.whitelist()
def get_call_center_per_hour(filters=None):
    if isinstance(filters, str):
        filters = json.loads(filters or "{}")
    filters = filters or {}

    mode = filters.get("mode") or "whole_day"
    working_day = filters.get("working_day") or getdate()
    shift = filters.get("shift") or "Morning"
    branches = _normalize(filters.get("branches"))
    cashier = filters.get("cashier") or ""
    order_types = _normalize(filters.get("order_types")) or ["Delivery"]

    shift_overrides = filters.get("shift_overrides") or {}

    # Get users from Call Center POS Profile
    call_center_users = get_call_center_users()
    if not call_center_users:
        return {
            "totals": {"count": 0, "grand_total": 0, "net_total": 0},
            "hours": [],
            "chart": {"labels": [], "orders": [], "grand_totals": []},
            "period": {"start": None, "end": None},
        }

    # If specific cashier selected, filter to that user only
    if cashier:
        if cashier in call_center_users:
            cashiers = [cashier]
        else:
            return {
                "totals": {"count": 0, "grand_total": 0, "net_total": 0},
                "hours": [],
                "chart": {"labels": [], "orders": [], "grand_totals": []},
                "period": {"start": None, "end": None},
            }
    else:
        cashiers = call_center_users

    # Compute time window based on mode
    if mode == "date_range":
        from_date = filters.get("from_date") or getdate()
        to_date = filters.get("to_date") or getdate()
        start_dt = get_datetime(f"{from_date} 00:00:00")
        end_dt = get_datetime(f"{to_date} 23:59:59")
    else:
        start_dt, end_dt = _compute_window(working_day, shift, shift_overrides=shift_overrides)

    branch_col = _branch_column()
    if branches and not branch_col:
        frappe.throw(_("Branch filter is set but Sales Invoice has no branch column."))

    has_sales_order = frappe.db.has_column("Sales Invoice", "sales_order")
    so_type_col = _order_type_column("Sales Order")
    si_type_col = _order_type_column("Sales Invoice")

    order_type_expr = None
    if si_type_col and so_type_col and has_sales_order:
        order_type_expr = f"COALESCE(si.`{si_type_col}`, so.`{so_type_col}`)"
    elif si_type_col:
        order_type_expr = f"si.`{si_type_col}`"
    elif so_type_col and has_sales_order:
        order_type_expr = f"so.`{so_type_col}`"

    if not order_type_expr:
        frappe.throw(_("Order Type is required but no order type field exists on Sales Order or Sales Invoice."))

    where = [
        "si.docstatus = 1",
        # A return credit note is NOT a separate order.
        "ifnull(si.is_return, 0) = 0",
        # A returned order should count as 0 — drop the original too when a submitted
        # return credit note points at it.
        "not exists (select 1 from `tabSales Invoice` r where r.return_against = si.name and ifnull(r.is_return,0) = 1 and r.docstatus = 1)",
        "timestamp(si.posting_date, ifnull(si.posting_time, '00:00:00')) BETWEEN %(start_dt)s AND %(end_dt)s",
        f"{order_type_expr} in %(order_types)s",
        "si.owner in %(cashiers)s",
    ]
    params = {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "start_date": start_dt.date(),
        "end_date": end_dt.date(),
        "order_types": tuple(order_types),
        "cashiers": tuple(cashiers),
    }
    if branches and branch_col:
        where.append(f"si.`{branch_col}` in %(branches)s")
        params["branches"] = tuple(branches)

    cond = " AND ".join(where)
    join_so = ""
    if has_sales_order and so_type_col:
        join_so = "LEFT JOIN `tabSales Order` so ON so.name = si.sales_order"

    invoices = frappe.db.sql(
        f"""
        SELECT
            si.name,
            si.posting_date,
            si.posting_time,
            si.grand_total,
            si.net_total,
            si.total_qty,
            si.pos_profile,
            si.owner,
            {f"si.`{branch_col}`" if branch_col else "NULL"} as branch
        FROM `tabSales Invoice` si
        {join_so}
        WHERE {cond}
        """,
        params,
        as_dict=True,
    )

    if not invoices:
        return {
            "totals": {"count": 0, "grand_total": 0, "net_total": 0},
            "hours": [],
            "chart": {"labels": [], "orders": [], "grand_totals": []},
            "period": {"start": start_dt, "end": end_dt},
        }

    inv_names = [d.name for d in invoices]
    payments_by_inv = _get_payments(inv_names, params)

    hours = defaultdict(lambda: {"count": 0, "grand_total": 0, "net_total": 0, "mops": defaultdict(float)})
    total_gt = total_nt = 0
    for inv in invoices:
        ts = get_datetime(f"{inv.posting_date} {inv.posting_time or '00:00:00'}")
        bucket = ts.replace(minute=0, second=0, microsecond=0)
        data = hours[bucket]
        data["count"] += 1
        data["grand_total"] += inv.grand_total
        data["net_total"] += inv.net_total
        for mop, amt in payments_by_inv.get(inv.name, {}).items():
            data["mops"][mop] += amt
        total_gt += inv.grand_total
        total_nt += inv.net_total

    sorted_hours = []
    labels = []
    order_counts = []
    grand_series = []
    for bucket in sorted(hours.keys()):
        entry = hours[bucket]
        labels.append(bucket.strftime("%H:%M"))
        order_counts.append(entry["count"])
        grand_series.append(entry["grand_total"])
        sorted_hours.append(
            {
                "hour": bucket.strftime("%Y-%m-%d %H:%M"),
                "count": entry["count"],
                "grand_total": entry["grand_total"],
                "net_total": entry["net_total"],
                "mops": [{"mode_of_payment": k, "amount": v} for k, v in entry["mops"].items()],
            }
        )

    return {
        "totals": {"count": len(invoices), "grand_total": total_gt, "net_total": total_nt},
        "hours": sorted_hours,
        "chart": {"labels": labels, "orders": order_counts, "grand_totals": grand_series},
        "period": {"start": start_dt, "end": end_dt},
    }


def _get_payments(inv_names, base_params):
    if not inv_names:
        return {}
    payments = defaultdict(lambda: defaultdict(float))
    for row in frappe.db.sql(
        """
        SELECT parent, mode_of_payment, SUM(amount) as amt
        FROM `tabSales Invoice Payment`
        WHERE parent in %(inv_names)s
        GROUP BY parent, mode_of_payment
        """,
        {"inv_names": tuple(inv_names)},
        as_dict=True,
    ):
        payments[row.parent][row.mode_of_payment] += row.amt

    if frappe.db.has_column("Payment Entry", "posting_time"):
        pe_time_cond = "timestamp(pe.posting_date, ifnull(pe.posting_time, '00:00:00')) BETWEEN %(start_dt)s AND %(end_dt)s"
        pe_date_only_cond = "(pe.posting_time is null or pe.posting_time = '') and pe.posting_date between %(start_date)s and %(end_date)s"
    else:
        pe_time_cond = "pe.posting_date between %(start_dt)s and %(end_dt)s"
        pe_date_only_cond = "pe.posting_date between %(start_date)s and %(end_date)s"
    pe_window_cond = f"(({pe_time_cond}) OR ({pe_date_only_cond}))"

    for row in frappe.db.sql(
        f"""
        SELECT per.reference_name as parent, pe.mode_of_payment, SUM(per.allocated_amount) as amt
        FROM `tabPayment Entry Reference` per
        JOIN `tabPayment Entry` pe ON pe.name = per.parent
        WHERE per.reference_doctype = 'Sales Invoice'
          AND per.reference_name in %(inv_names)s
          AND pe.docstatus = 1
          AND {pe_window_cond}
        GROUP BY per.reference_name, pe.mode_of_payment
        """,
        {
            "inv_names": tuple(inv_names),
            "start_dt": base_params.get("start_dt"),
            "end_dt": base_params.get("end_dt"),
            "start_date": base_params.get("start_date"),
            "end_date": base_params.get("end_date"),
        },
        as_dict=True,
    ):
        payments[row.parent][row.mode_of_payment] += row.amt

    return payments


def _normalize(val):
    if not val:
        return []
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    if isinstance(val, (list, tuple)):
        out = []
        for v in val:
            if not v:
                continue
            if isinstance(v, str):
                candidate = v.strip()
            elif isinstance(v, dict):
                candidate = (v.get("value") or v.get("label") or v.get("name") or "").strip()
            else:
                candidate = ""
            if candidate:
                out.append(candidate)
        return out
    return [val]


SHIFT_WINDOWS = {
    "Morning": (9, 0, 22, 0),
    "Evening": (22, 0, 9, 0),
    "Whole Day": (9, 0, 9, 0),
}


def _compute_window(working_day, shift, shift_overrides=None):
    shift_overrides = shift_overrides or {}
    default = SHIFT_WINDOWS.get(shift, SHIFT_WINDOWS["Morning"])

    def pick(key, fallback):
        override_val = _parse_time_parts(shift_overrides.get(key))
        if override_val:
            return override_val
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


def _branch_column():
    if frappe.db.has_column("Sales Invoice", "branch"):
        return "branch"
    if frappe.db.has_column("Sales Invoice", "custom_branch"):
        return "custom_branch"
    return None


def _order_type_column(doctype):
    cols = set(frappe.db.get_table_columns(doctype) or [])
    # Prefer custom_order_type (the field the POS actually stamps) over the legacy
    # custom_so_type.
    for candidate in ["custom_order_type", "custom_so_type", "custom_custom_so_type", "so_type", "order_type"]:
        if candidate in cols:
            return candidate
    return None


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
