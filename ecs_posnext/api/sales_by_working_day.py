# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import frappe
from frappe import _
from frappe.utils import getdate, get_datetime, add_days


SHIFT_WINDOWS = {
    "Morning": (9, 0, 20, 0),
    "Evening": (20, 0, 6, 0),
    # Whole Day for this business: same working window spanning the two shifts
    "Whole Day": (9, 0, 6, 0),
}


@frappe.whitelist()
def get_sales_by_working_day(filters=None):
    """Aggregate sales for a working day + shift window (morning/evening)."""
    if isinstance(filters, str):
        filters = json.loads(filters or "{}")
    filters = filters or {}

    mode = filters.get("mode") or "whole_day"
    working_day = filters.get("working_day") or getdate()
    shift = filters.get("shift") or "Whole Day"
    branches = _normalize(filters.get("branches"))
    pos_profiles = _normalize(filters.get("pos_profiles"))
    cashiers = _normalize(filters.get("cashiers"))
    items = _normalize(filters.get("items"))
    order_types = _normalize(filters.get("order_types"))
    mops = _normalize(filters.get("modes_of_payment"))
    price_lists = _normalize(filters.get("price_lists"))

    pos_profile_for_window = _normalize(filters.get("pos_profile_for_window"))
    if pos_profile_for_window:
        pos_profile_for_window = pos_profile_for_window[0]
    else:
        pos_profile_for_window = None

    shift_overrides = filters.get("shift_overrides") or {}

    # Compute time window based on mode
    if mode == "date_range":
        from_date = filters.get("from_date") or getdate()
        to_date = filters.get("to_date") or getdate()
        start_dt = get_datetime(f"{from_date} 00:00:00")
        end_dt = get_datetime(f"{to_date} 23:59:59")
    else:
        start_dt, end_dt = _compute_window(
            working_day, shift, pos_profiles, pos_profile_for_window, shift_overrides=shift_overrides
        )
    params = {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "start_date": start_dt.date(),
        "end_date": end_dt.date(),
    }

    branch_col = _branch_column()
    if branches and not branch_col:
        frappe.throw(_("Branch filter is set but Sales Invoice has no branch column."))
    price_list_col = "selling_price_list" if frappe.db.has_column("Sales Invoice", "selling_price_list") else None
    has_si_custom_so = frappe.db.has_column("Sales Invoice", "custom_so_type")

    time_cond = "timestamp(si.posting_date, ifnull(si.posting_time, '00:00:00')) BETWEEN %(start_dt)s AND %(end_dt)s"
    date_only_cond = "(si.posting_time is null or si.posting_time = '') and si.posting_date between %(start_date)s and %(end_date)s"
    where = ["si.docstatus = 1", f"(({time_cond}) OR ({date_only_cond}))"]
    if branches and branch_col:
        where.append(f"si.`{branch_col}` in %(branches)s")
        params["branches"] = tuple(branches)
    if pos_profiles:
        where.append("si.pos_profile in %(pos_profiles)s")
        params["pos_profiles"] = tuple(pos_profiles)
    if cashiers:
        where.append("si.owner in %(cashiers)s")
        params["cashiers"] = tuple(cashiers)
    if price_lists:
        if not price_list_col:
            frappe.throw(_("Price List filter is set but Sales Invoice has no price list column."))
        where.append(f"si.`{price_list_col}` in %(price_lists)s")
        params["price_lists"] = tuple(price_lists)
    if mops:
        where.append(
            """
            (
                EXISTS (
                    SELECT 1 FROM `tabSales Invoice Payment` sipx
                    WHERE sipx.parent = si.name AND sipx.mode_of_payment in %(mops)s
                )
                OR EXISTS (
                    SELECT 1
                    FROM `tabPayment Entry Reference` perx
                    JOIN `tabPayment Entry` pex ON pex.name = perx.parent
                    WHERE perx.reference_doctype = 'Sales Invoice'
                        AND perx.reference_name = si.name
                        AND pex.docstatus = 1
                        AND pex.mode_of_payment in %(mops)s
                )
            )
            """
        )
        params["mops"] = tuple(mops)

    cond = " AND ".join(where)

    has_sales_order = frappe.db.has_column("Sales Invoice", "sales_order")
    has_custom_so_type = frappe.db.has_column("Sales Order", "custom_so_type")
    join_so = "LEFT JOIN `tabSales Order` so ON so.name = si.sales_order" if has_sales_order else ""

    # Determine the expression used for order type
    if has_sales_order and has_custom_so_type and has_si_custom_so:
        order_type_expr = "COALESCE(so.custom_so_type, si.custom_so_type)"
    elif has_sales_order and has_custom_so_type:
        order_type_expr = "so.custom_so_type"
    elif has_si_custom_so:
        order_type_expr = "si.custom_so_type"
    else:
        order_type_expr = None

    cond_order = ""
    if order_types:
        if order_type_expr:
            cond_order = f"AND {order_type_expr} in %(order_types)s"
            params["order_types"] = tuple(order_types)
        else:
            frappe.throw(_("Order Type filter is set but no order type field exists on Sales Invoice or linked Sales Order."))

    detail = frappe.db.sql(
        f"""
        SELECT
            si.name,
            si.posting_date,
            si.posting_time,
            {f"si.`{branch_col}`" if branch_col else "NULL"} AS branch,
            si.pos_profile,
            si.customer,
            si.grand_total,
            si.net_total,
            si.outstanding_amount,
            si.total_qty,
            {order_type_expr if order_type_expr else "'Unknown'"} AS order_type,
            {f"si.`{price_list_col}`" if price_list_col else "NULL"} AS price_list
        FROM `tabSales Invoice` si
        {join_so}
        WHERE {cond}
        {cond_order}
        """,
        params,
        as_dict=True,
    )

    return_where = [f"(({time_cond}) OR ({date_only_cond}))", "si.docstatus = 2"]
    if branches and branch_col:
        return_where.append(f"si.`{branch_col}` in %(branches)s")
    if pos_profiles:
        return_where.append("si.pos_profile in %(pos_profiles)s")
    if cashiers:
        return_where.append("si.owner in %(cashiers)s")
    if price_lists and price_list_col:
        return_where.append(f"si.`{price_list_col}` in %(price_lists)s")
    return_cond = " AND ".join(return_where)

    return_invoices = frappe.db.sql(
        f"""
        SELECT
            si.name,
            si.posting_date,
            si.posting_time,
            {f"si.`{branch_col}`" if branch_col else "NULL"} AS branch,
            si.pos_profile,
            si.customer,
            si.grand_total,
            si.net_total,
            si.total_qty
        FROM `tabSales Invoice` si
        {join_so}
        WHERE {return_cond}
        {cond_order}
        ORDER BY si.posting_date DESC, si.posting_time DESC
        """,
        params,
        as_dict=True,
    )

    return_totals = {
        "grand_total": sum([d.grand_total for d in return_invoices]),
        "net_total": sum([d.net_total for d in return_invoices]),
        "count": len(return_invoices),
    }

    totals = {
        "grand_total": sum([d.grand_total for d in detail]),
        "net_total": sum([d.net_total for d in detail]),
        "outstanding_total": sum([d.outstanding_amount for d in detail]),
        "total_qty": sum([d.total_qty for d in detail]),
        "count": len(detail),
    }

    branch_summary = {}
    for d in detail:
        key = d.branch or "Unknown"
        row = branch_summary.setdefault(
            key,
            {"branch": key, "grand_total": 0, "net_total": 0, "total_qty": 0, "count": 0},
        )
        row["grand_total"] += d.grand_total
        row["net_total"] += d.net_total
        row["total_qty"] += d.total_qty
        row["count"] += 1

    order_cats = {}
    for d in detail:
        key = d.order_type or "Unknown"
        row = order_cats.setdefault(
            key,
            {"order_type": key, "grand_total": 0, "net_total": 0, "total_qty": 0, "count": 0},
        )
        row["grand_total"] += d.grand_total
        row["net_total"] += d.net_total
        row["total_qty"] += d.total_qty
        row["count"] += 1

    order_source = {}
    for d in detail:
        key = d.price_list or "Unknown"
        row = order_source.setdefault(
            key,
            {"price_list": key, "grand_total": 0, "net_total": 0, "total_qty": 0, "count": 0},
        )
        row["grand_total"] += d.grand_total
        row["net_total"] += d.net_total
        row["total_qty"] += d.total_qty
        row["count"] += 1

    if frappe.db.has_column("Payment Entry", "posting_time"):
        pe_time_cond = "timestamp(pe.posting_date, ifnull(pe.posting_time, '00:00:00')) BETWEEN %(start_dt)s AND %(end_dt)s"
        pe_date_only_cond = "(pe.posting_time is null or pe.posting_time = '') and pe.posting_date between %(start_date)s and %(end_date)s"
    else:
        pe_time_cond = "pe.posting_date between %(start_dt)s and %(end_dt)s"
        pe_date_only_cond = "pe.posting_date between %(start_date)s and %(end_date)s"
    pe_window_cond = f"(({pe_time_cond}) OR ({pe_date_only_cond}))"

    payments = frappe.db.sql(
        f"""
        SELECT mode_of_payment, SUM(amount) AS amount
        FROM (
            SELECT
                sip.mode_of_payment,
                SUM(sip.amount) AS amount
            FROM `tabSales Invoice Payment` sip
            JOIN `tabSales Invoice` si ON si.name = sip.parent
            {join_so}
            WHERE {cond}
            {cond_order}
            {("AND sip.mode_of_payment in %(mops)s" if mops else "")}
            GROUP BY sip.mode_of_payment

            UNION ALL

            SELECT
                pe.mode_of_payment,
                SUM(per.allocated_amount) AS amount
            FROM `tabPayment Entry Reference` per
            JOIN `tabPayment Entry` pe ON pe.name = per.parent
            JOIN `tabSales Invoice` si ON si.name = per.reference_name
            {join_so}
            WHERE pe.docstatus = 1
              AND per.reference_doctype = 'Sales Invoice'
              AND {pe_window_cond}
              AND {cond}
              {cond_order}
              {("AND pe.mode_of_payment in %(mops)s" if mops else "")}
            GROUP BY pe.mode_of_payment
        ) x
        GROUP BY mode_of_payment
        """,
        params,
        as_dict=True,
    )

    invoices_items = frappe.db.sql(
        f"""
        SELECT
            si.name as sales_invoice,
            si.posting_date,
            si.posting_time,
            {f"si.`{branch_col}`" if branch_col else "NULL"} AS branch,
            si.pos_profile,
            si.customer,
            sii.item_code,
            sii.item_name,
            sii.item_group,
            sii.qty,
            sii.net_rate,
            sii.net_amount,
            sii.amount
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        {join_so}
        WHERE {cond}
        {cond_order}
        {("AND sii.item_code in %(items)s" if items else "")}
        """,
        {
            **params,
            **({"items": tuple(items)} if items else {}),
        },
        as_dict=True,
    )

    if items:
        inv_with_items = {it.sales_invoice for it in invoices_items}
        detail = [d for d in detail if d.name in inv_with_items]

    customer_where = ["c.creation BETWEEN %(start_dt)s AND %(end_dt)s"]
    customer_params = {
        "start_dt": start_dt,
        "end_dt": end_dt,
    }
    if branches:
        customer_where.append("emp.branch in %(customer_branches)s")
        customer_params["customer_branches"] = tuple(branches)

    new_customers = frappe.db.sql(
        f"""
        SELECT
            c.name,
            c.customer_name,
            c.creation,
            emp.branch AS branch,
            c.owner
        FROM `tabCustomer` c
        LEFT JOIN `tabUser` u ON u.name = c.owner
        LEFT JOIN `tabEmployee` emp ON emp.user_id = u.name
        WHERE {' AND '.join(customer_where)}
        ORDER BY c.creation DESC
        """,
        customer_params,
        as_dict=True,
    )

    cheque_avg = (totals["net_total"] / totals["count"]) if totals["count"] else 0

    return {
        "totals": totals,
        "branch_summary": list(branch_summary.values()),
        "payments": payments,
        "detail": detail,
        "return_invoices": return_invoices,
        "return_totals": return_totals,
        "invoices_items": invoices_items,
        "new_customers": new_customers,
        "new_customers_count": len(new_customers),
        "order_categorization": list(order_cats.values()),
        "order_source": list(order_source.values()),
        "period": {"start": start_dt, "end": end_dt},
        "cheque_avg": cheque_avg,
    }


@frappe.whitelist()
def get_sales_by_date_range(filters=None):
    """Get sales data for a date range or single working day."""
    if isinstance(filters, str):
        filters = json.loads(filters or "{}")
    filters = filters or {}

    mode = filters.get("mode") or "whole_day"
    
    if mode == "whole_day":
        # Use the existing function for single day
        return get_sales_by_working_day(filters)
    
    # Date Range Mode
    from_date = filters.get("from_date") or getdate()
    to_date = filters.get("to_date") or getdate()
    branches = _normalize(filters.get("branches"))
    pos_profiles = _normalize(filters.get("pos_profiles"))
    cashiers = _normalize(filters.get("cashiers"))
    items = _normalize(filters.get("items"))
    order_types = _normalize(filters.get("order_types"))
    mops = _normalize(filters.get("modes_of_payment"))
    price_lists = _normalize(filters.get("price_lists"))

    # For date range, we use full days (00:00:00 to 23:59:59)
    start_dt = get_datetime(f"{from_date} 00:00:00")
    end_dt = get_datetime(f"{to_date} 23:59:59")
    
    params = {
        "start_dt": start_dt,
        "end_dt": end_dt,
        "start_date": getdate(from_date),
        "end_date": getdate(to_date),
    }

    branch_col = _branch_column()
    if branches and not branch_col:
        frappe.throw(_("Branch filter is set but Sales Invoice has no branch column."))
    price_list_col = "selling_price_list" if frappe.db.has_column("Sales Invoice", "selling_price_list") else None
    has_si_custom_so = frappe.db.has_column("Sales Invoice", "custom_so_type")

    time_cond = "timestamp(si.posting_date, ifnull(si.posting_time, '00:00:00')) BETWEEN %(start_dt)s AND %(end_dt)s"
    date_only_cond = "si.posting_date between %(start_date)s and %(end_date)s"
    where = ["si.docstatus = 1", f"(({time_cond}) OR ({date_only_cond}))"]
    
    if branches and branch_col:
        where.append(f"si.`{branch_col}` in %(branches)s")
        params["branches"] = tuple(branches)
    if pos_profiles:
        where.append("si.pos_profile in %(pos_profiles)s")
        params["pos_profiles"] = tuple(pos_profiles)
    if cashiers:
        where.append("si.owner in %(cashiers)s")
        params["cashiers"] = tuple(cashiers)
    if price_lists:
        if not price_list_col:
            frappe.throw(_("Price List filter is set but Sales Invoice has no price list column."))
        where.append(f"si.`{price_list_col}` in %(price_lists)s")
        params["price_lists"] = tuple(price_lists)
    if mops:
        where.append(
            """
            (
                EXISTS (
                    SELECT 1 FROM `tabSales Invoice Payment` sipx
                    WHERE sipx.parent = si.name AND sipx.mode_of_payment in %(mops)s
                )
                OR EXISTS (
                    SELECT 1
                    FROM `tabPayment Entry Reference` perx
                    JOIN `tabPayment Entry` pex ON pex.name = perx.parent
                    WHERE perx.reference_doctype = 'Sales Invoice'
                        AND perx.reference_name = si.name
                        AND pex.docstatus = 1
                        AND pex.mode_of_payment in %(mops)s
                )
            )
            """
        )
        params["mops"] = tuple(mops)

    cond = " AND ".join(where)

    has_sales_order = frappe.db.has_column("Sales Invoice", "sales_order")
    has_custom_so_type = frappe.db.has_column("Sales Order", "custom_so_type")
    join_so = "LEFT JOIN `tabSales Order` so ON so.name = si.sales_order" if has_sales_order else ""

    if has_sales_order and has_custom_so_type and has_si_custom_so:
        order_type_expr = "COALESCE(so.custom_so_type, si.custom_so_type)"
    elif has_sales_order and has_custom_so_type:
        order_type_expr = "so.custom_so_type"
    elif has_si_custom_so:
        order_type_expr = "si.custom_so_type"
    else:
        order_type_expr = None

    cond_order = ""
    if order_types:
        if order_type_expr:
            cond_order = f"AND {order_type_expr} in %(order_types)s"
            params["order_types"] = tuple(order_types)
        else:
            frappe.throw(_("Order Type filter is set but no order type field exists."))

    detail = frappe.db.sql(
        f"""
        SELECT
            si.name,
            si.posting_date,
            si.posting_time,
            {f"si.`{branch_col}`" if branch_col else "NULL"} AS branch,
            si.pos_profile,
            si.customer,
            si.grand_total,
            si.net_total,
            si.total_qty,
            {order_type_expr if order_type_expr else "'Unknown'"} AS order_type,
            {f"si.`{price_list_col}`" if price_list_col else "NULL"} AS price_list
        FROM `tabSales Invoice` si
        {join_so}
        WHERE {cond}
        {cond_order}
        """,
        params,
        as_dict=True,
    )

    totals = {
        "grand_total": sum([d.grand_total for d in detail]),
        "net_total": sum([d.net_total for d in detail]),
        "total_qty": sum([d.total_qty for d in detail]),
        "count": len(detail),
    }

    branch_summary = {}
    for d in detail:
        key = d.branch or "Unknown"
        row = branch_summary.setdefault(
            key,
            {"branch": key, "grand_total": 0, "net_total": 0, "total_qty": 0, "count": 0},
        )
        row["grand_total"] += d.grand_total
        row["net_total"] += d.net_total
        row["total_qty"] += d.total_qty
        row["count"] += 1

    order_cats = {}
    for d in detail:
        key = d.order_type or "Unknown"
        row = order_cats.setdefault(
            key,
            {"order_type": key, "grand_total": 0, "net_total": 0, "total_qty": 0, "count": 0},
        )
        row["grand_total"] += d.grand_total
        row["net_total"] += d.net_total
        row["total_qty"] += d.total_qty
        row["count"] += 1

    order_source = {}
    for d in detail:
        key = d.price_list or "Unknown"
        row = order_source.setdefault(
            key,
            {"price_list": key, "grand_total": 0, "net_total": 0, "total_qty": 0, "count": 0},
        )
        row["grand_total"] += d.grand_total
        row["net_total"] += d.net_total
        row["total_qty"] += d.total_qty
        row["count"] += 1

    if frappe.db.has_column("Payment Entry", "posting_time"):
        pe_time_cond = "timestamp(pe.posting_date, ifnull(pe.posting_time, '00:00:00')) BETWEEN %(start_dt)s AND %(end_dt)s"
        pe_date_only_cond = "pe.posting_date between %(start_date)s and %(end_date)s"
    else:
        pe_time_cond = "pe.posting_date between %(start_dt)s and %(end_dt)s"
        pe_date_only_cond = "pe.posting_date between %(start_date)s and %(end_date)s"
    pe_window_cond = f"(({pe_time_cond}) OR ({pe_date_only_cond}))"

    payments = frappe.db.sql(
        f"""
        SELECT mode_of_payment, SUM(amount) AS amount
        FROM (
            SELECT
                sip.mode_of_payment,
                SUM(sip.amount) AS amount
            FROM `tabSales Invoice Payment` sip
            JOIN `tabSales Invoice` si ON si.name = sip.parent
            {join_so}
            WHERE {cond}
            {cond_order}
            {("AND sip.mode_of_payment in %(mops)s" if mops else "")}
            GROUP BY sip.mode_of_payment

            UNION ALL

            SELECT
                pe.mode_of_payment,
                SUM(per.allocated_amount) AS amount
            FROM `tabPayment Entry Reference` per
            JOIN `tabPayment Entry` pe ON pe.name = per.parent
            JOIN `tabSales Invoice` si ON si.name = per.reference_name
            {join_so}
            WHERE pe.docstatus = 1
              AND per.reference_doctype = 'Sales Invoice'
              AND {pe_window_cond}
              AND {cond}
              {cond_order}
              {("AND pe.mode_of_payment in %(mops)s" if mops else "")}
            GROUP BY pe.mode_of_payment
        ) x
        GROUP BY mode_of_payment
        """,
        params,
        as_dict=True,
    )

    invoices_items = frappe.db.sql(
        f"""
        SELECT
            si.name as sales_invoice,
            si.posting_date,
            si.posting_time,
            {f"si.`{branch_col}`" if branch_col else "NULL"} AS branch,
            si.pos_profile,
            si.customer,
            sii.item_code,
            sii.item_name,
            sii.item_group,
            sii.qty,
            sii.net_rate,
            sii.net_amount,
            sii.amount
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        {join_so}
        WHERE {cond}
        {cond_order}
        {("AND sii.item_code in %(items)s" if items else "")}
        """,
        {
            **params,
            **({"items": tuple(items)} if items else {}),
        },
        as_dict=True,
    )

    if items:
        inv_with_items = {it.sales_invoice for it in invoices_items}
        detail = [d for d in detail if d.name in inv_with_items]

    cheque_avg = (totals["net_total"] / totals["count"]) if totals["count"] else 0

    return {
        "totals": totals,
        "branch_summary": list(branch_summary.values()),
        "payments": payments,
        "detail": detail,
        "invoices_items": invoices_items,
        "order_categorization": list(order_cats.values()),
        "order_source": list(order_source.values()),
        "period": {"start": str(from_date), "end": str(to_date)},
        "cheque_avg": cheque_avg,
    }


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


def _compute_window(working_day, shift, pos_profiles=None, explicit_profile=None, shift_overrides=None):
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


def _branch_column():
    if frappe.db.has_column("Sales Invoice", "branch"):
        return "branch"
    if frappe.db.has_column("Sales Invoice", "custom_branch"):
        return "custom_branch"
    return None


def _parse_time_parts(val):
    if not val:
        return None
    try:
        # If it's already a time object
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
