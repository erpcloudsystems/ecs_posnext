# -*- coding: utf-8 -*-
# Restaurant Operations Dashboard API

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate


@frappe.whitelist()
def get_ops_metrics(
    from_date=None,
    to_date=None,
    branches=None,
    order_type=None,
    price_list=None,
    mode_of_payment=None,
    cancel_status=None,
    employee=None,
):
    """Return aggregated restaurant KPIs for Sales Invoices."""
    filters = frappe._dict(
        {
            "from_date": from_date or getdate(),
            "to_date": to_date or getdate(),
            "branches": branches,
            "order_type": order_type,
            "price_list": price_list,
            "mode_of_payment": mode_of_payment,
            "cancel_status": cancel_status,
            "employee": employee,
        }
    )

    allowed_branches = _get_allowed_branches(frappe.session.user)
    requested_branches = _normalize_multi(filters.branches)
    if requested_branches:
        allowed_filter = [b for b in requested_branches if b in allowed_branches]
    else:
        allowed_filter = allowed_branches

    # If user has no allowed branches, return empty payload
    if allowed_filter is not None and len(allowed_filter) == 0:
        return _empty_payload()

    branch_expr = _get_branch_expr()
    price_list_expr = _get_price_list_expr()
    order_type_expr = _get_order_type_expr()

    conditions, params = _build_conditions(
        filters=filters,
        branch_expr=branch_expr,
        price_list_expr=price_list_expr,
        order_type_expr=order_type_expr,
        allowed_branches=allowed_filter,
    )

    kpis = _get_kpis(conditions, params)
    order_types = _get_order_type_summary(conditions, params, order_type_expr, kpis)
    price_lists = _get_price_list_summary(conditions, params, price_list_expr, kpis)
    top_items = _get_top_items(conditions, params, price_list_expr, kpis)
    peak_hours = _get_peak_hours(conditions, params)
    branches_summary = _get_branch_comparison(
        conditions, params, branch_expr, kpis, allowed_filter
    )

    return {
        "kpis": kpis,
        "order_type_summary": order_types,
        "price_list_summary": price_lists,
        "top_items": top_items,
        "peak_hours": peak_hours,
        "branch_comparison": branches_summary,
    }


@frappe.whitelist()
def get_filter_options():
    """Provide dropdown options for the dashboard filters."""
    allowed_branches = _get_allowed_branches(frappe.session.user)

    order_type_expr = _get_order_type_expr()
    order_types = frappe.db.sql(
        f"""SELECT DISTINCT {order_type_expr} AS order_type
            FROM `tabSales Order`
            WHERE docstatus = 1
            ORDER BY order_type""",
        as_dict=True,
    )

    price_lists = frappe.get_all("Price List", pluck="name", order_by="name")
    mode_of_payments = frappe.get_all("Mode of Payment", pluck="name", order_by="name")
    employees = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        pluck="name",
        order_by="name",
    )

    return {
        "branches": allowed_branches,
        "order_types": [d.order_type or "Unknown" for d in order_types],
        "price_lists": price_lists,
        "mode_of_payments": mode_of_payments,
        "employees": employees,
    }


def _empty_payload():
    return {
        "kpis": {},
        "order_type_summary": [],
        "price_list_summary": [],
        "top_items": [],
        "peak_hours": [],
        "branch_comparison": [],
    }


def _get_allowed_branches(user):
    """Fetch branches via POS Profiles assigned to the user."""
    profiles = frappe.get_all(
        "POS Profile User", filters={"user": user}, pluck="parent"
    )
    if not profiles:
        return []

    branches = []
    branch_field = "branch" if frappe.db.has_column("POS Profile", "branch") else None
    for profile in profiles:
        if branch_field:
            branch = frappe.db.get_value("POS Profile", profile, branch_field)
            if branch:
                branches.append(branch)
    return list(set(branches))


def _normalize_multi(val):
    if not val:
        return []
    if isinstance(val, (list, tuple)):
        return list(val)
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    return []


def _get_branch_expr():
    parts = []
    if frappe.db.has_column("POS Profile", "branch"):
        parts.append("pp.branch")
    if frappe.db.has_column("Sales Invoice", "branch"):
        parts.append("si.branch")
    if not parts:
        return "NULL"
    return "COALESCE({})".format(", ".join(parts))


def _get_price_list_expr():
    parts = []
    if frappe.db.has_column("Sales Invoice Item", "price_list"):
        parts.append("sii.price_list")
    if frappe.db.has_column("Sales Invoice", "selling_price_list"):
        parts.append("si.selling_price_list")
    if not parts:
        return "'Unknown'"
    return "COALESCE({})".format(", ".join(parts))


def _get_order_type_expr():
    # Custom field then standard field
    return "COALESCE(so.custom_so_type, so.order_type, 'Unknown')"


def _build_conditions(filters, branch_expr, price_list_expr, order_type_expr, allowed_branches):
    cond = ["si.docstatus in (1,2)"]
    params = {}

    if filters.from_date:
        cond.append("si.posting_date >= %(from_date)s")
        params["from_date"] = filters.from_date
    if filters.to_date:
        cond.append("si.posting_date <= %(to_date)s")
        params["to_date"] = filters.to_date

    if filters.cancel_status:
        if filters.cancel_status.lower() == "cancelled":
            cond.append("si.docstatus = 2")
        elif filters.cancel_status.lower() in ("submitted", "active", "not cancelled"):
            cond.append("si.docstatus = 1")

    if allowed_branches:
        cond.append(f"{branch_expr} in %(branches)s")
        params["branches"] = tuple(allowed_branches)

    if filters.order_type:
        cond.append(f"{order_type_expr} = %(order_type)s")
        params["order_type"] = filters.order_type

    if filters.price_list:
        cond.append(f"{price_list_expr} = %(price_list)s")
        params["price_list"] = filters.price_list

    if filters.employee:
        cond.append("si.owner = %(employee)s")
        params["employee"] = filters.employee

    if filters.mode_of_payment:
        cond.append(
            """EXISTS (
                SELECT 1
                FROM `tabPayment Entry Reference` pref
                JOIN `tabPayment Entry` pe ON pref.parent = pe.name
                WHERE pref.reference_doctype = 'Sales Invoice'
                  AND pref.reference_name = si.name
                  AND pe.docstatus = 1
                  AND pe.payment_type = 'Receive'
                  AND pe.mode_of_payment = %(mode_of_payment)s
            )"""
        )
        params["mode_of_payment"] = filters.mode_of_payment

    return " AND ".join(cond), params


def _get_kpis(conditions, params):
    row = frappe.db.sql(
        f"""
        SELECT
            COUNT(DISTINCT si.name) AS total_orders,
            SUM(CASE WHEN si.docstatus = 1 THEN si.base_grand_total ELSE 0 END) AS total_value,
            SUM(CASE WHEN si.docstatus = 1 THEN COALESCE(si.base_discount_amount, 0) ELSE 0 END) AS discount_total,
            SUM(CASE WHEN si.docstatus = 2 THEN 1 ELSE 0 END) AS cancelled_count,
            SUM(CASE WHEN si.docstatus = 2 THEN si.base_grand_total ELSE 0 END) AS cancelled_value,
            COUNT(DISTINCT CASE WHEN si.docstatus = 1 THEN si.customer END) AS customers_served
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabSales Order` so ON so.name = sii.sales_order
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {conditions}
        """,
        params,
        as_dict=True,
    )[0]

    total_orders = row.total_orders or 0
    total_value = row.total_value or 0
    discount_total = row.discount_total or 0

    avg_order_value = total_value / total_orders if total_orders else 0
    net_sales = total_value  # grand_total is already net of discounts

    return {
        "total_orders": total_orders,
        "total_value": total_value,
        "avg_order_value": avg_order_value,
        "customers_served": row.customers_served or 0,
        "cancelled_count": row.cancelled_count or 0,
        "cancelled_value": row.cancelled_value or 0,
        "discount_total": discount_total,
        "net_sales": net_sales,
    }


def _get_order_type_summary(conditions, params, order_type_expr, kpis):
    total_value = kpis.get("total_value") or 1
    data = frappe.db.sql(
        f"""
        SELECT
            {order_type_expr} AS order_type,
            COUNT(DISTINCT si.name) AS orders,
            SUM(CASE WHEN si.docstatus = 1 THEN si.base_grand_total ELSE 0 END) AS value
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabSales Order` so ON so.name = sii.sales_order
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {conditions}
          AND si.docstatus = 1
        GROUP BY {order_type_expr}
        """,
        params,
        as_dict=True,
    )
    return [
        {
            "type": d.order_type or "Unknown",
            "orders": d.orders or 0,
            "value": d.value or 0,
            "contribution_pct": ((d.value or 0) / total_value) * 100 if total_value else 0,
        }
        for d in data
    ]


def _get_price_list_summary(conditions, params, price_list_expr, kpis):
    total_value = kpis.get("total_value") or 1
    data = frappe.db.sql(
        f"""
        SELECT
            {price_list_expr} AS channel,
            COUNT(DISTINCT si.name) AS orders,
            SUM(CASE WHEN si.docstatus = 1 THEN sii.base_net_amount ELSE 0 END) AS value
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabSales Order` so ON so.name = sii.sales_order
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {conditions}
          AND si.docstatus = 1
        GROUP BY {price_list_expr}
        """,
        params,
        as_dict=True,
    )
    return [
        {
            "channel": d.channel or "Unknown",
            "orders": d.orders or 0,
            "value": d.value or 0,
            "contribution_pct": ((d.value or 0) / total_value) * 100 if total_value else 0,
        }
        for d in data
    ]


def _get_top_items(conditions, params, price_list_expr, kpis):
    total_value = kpis.get("total_value") or 1
    items = frappe.db.sql(
        f"""
        SELECT
            sii.item_code,
            sii.item_name,
            SUM(CASE WHEN si.docstatus = 1 THEN sii.qty ELSE 0 END) AS qty,
            SUM(CASE WHEN si.docstatus = 1 THEN sii.base_net_amount ELSE 0 END) AS value
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabSales Order` so ON so.name = sii.sales_order
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {conditions}
          AND si.docstatus = 1
        GROUP BY sii.item_code, sii.item_name
        ORDER BY value DESC
        LIMIT 10
        """,
        params,
        as_dict=True,
    )

    top_item_codes = [d.item_code for d in items]
    sparklines = _get_item_sparklines(conditions, params, top_item_codes)

    result = []
    for d in items:
        result.append(
            {
                "item_code": d.item_code,
                "item_name": d.item_name,
                "qty": d.qty or 0,
                "value": d.value or 0,
                "contribution_pct": ((d.value or 0) / total_value) * 100 if total_value else 0,
                "sparkline": sparklines.get(d.item_code, []),
            }
        )
    return result


def _get_item_sparklines(conditions, params, item_codes):
    if not item_codes:
        return {}
    params = params.copy()
    params["item_codes"] = tuple(item_codes)

    data = frappe.db.sql(
        f"""
        SELECT
            sii.item_code,
            si.posting_date,
            SUM(sii.base_net_amount) AS value
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabSales Order` so ON so.name = sii.sales_order
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {conditions}
          AND si.docstatus = 1
          AND sii.item_code in %(item_codes)s
        GROUP BY sii.item_code, si.posting_date
        ORDER BY si.posting_date DESC
        """,
        params,
        as_dict=True,
    )

    spark = {}
    for row in data:
        spark.setdefault(row.item_code, []).append(
            {"date": row.posting_date, "value": row.value or 0}
        )
    # Ensure descending order limited to last 7 points
    for k, v in spark.items():
        spark[k] = v[:7]
    return spark


def _get_peak_hours(conditions, params):
    data = frappe.db.sql(
        f"""
        SELECT
            HOUR(si.posting_time) AS hour,
            COUNT(DISTINCT si.name) AS orders,
            AVG(si.base_grand_total) AS avg_value
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabSales Order` so ON so.name = sii.sales_order
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {conditions}
          AND si.docstatus = 1
        GROUP BY HOUR(si.posting_time)
        ORDER BY hour
        """,
        params,
        as_dict=True,
    )
    return [
        {"hour": d.hour, "orders": d.orders or 0, "avg_value": d.avg_value or 0}
        for d in data
    ]


def _get_branch_comparison(conditions, params, branch_expr, kpis, allowed_branches):
    if allowed_branches and len(allowed_branches) <= 1:
        return []

    data = frappe.db.sql(
        f"""
        SELECT
            {branch_expr} AS branch,
            COUNT(DISTINCT si.name) AS orders,
            SUM(CASE WHEN si.docstatus = 1 THEN si.base_grand_total ELSE 0 END) AS value,
            AVG(CASE WHEN si.docstatus = 1 THEN si.base_grand_total ELSE NULL END) AS avg_order_value
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabSales Order` so ON so.name = sii.sales_order
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {conditions}
          AND si.docstatus = 1
        GROUP BY {branch_expr}
        """,
        params,
        as_dict=True,
    )
    return [
        {
            "branch": d.branch or "Unknown",
            "orders": d.orders or 0,
            "value": d.value or 0,
            "avg_order_value": d.avg_order_value or 0,
        }
        for d in data
    ]
