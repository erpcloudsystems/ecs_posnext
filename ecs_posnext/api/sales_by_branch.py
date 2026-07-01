# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import frappe
from frappe import _
from frappe.utils import getdate


@frappe.whitelist()
def get_sales_by_branch(filters=None):
    """Return sales breakdown by branch and product."""
    if isinstance(filters, str):
        filters = json.loads(filters or "{}")
    filters = filters or {}

    from_date = filters.get("from_date") or getdate()
    to_date = filters.get("to_date") or getdate()
    branches = _normalize(filters.get("branches"))
    pos_profiles = _normalize(filters.get("pos_profiles"))
    items = _normalize(filters.get("items"))
    item_groups = _normalize(filters.get("item_groups"))
    owners = _normalize(filters.get("owners"))

    branch_expr = _branch_expr()

    base_conditions = ["si.docstatus = 1", "si.posting_date between %(from_date)s and %(to_date)s"]
    params = {"from_date": from_date, "to_date": to_date}

    if branches:
        base_conditions.append(f"{branch_expr} in %(branches)s")
        params["branches"] = tuple(branches)
    if pos_profiles:
        base_conditions.append("si.pos_profile in %(pos_profiles)s")
        params["pos_profiles"] = tuple(pos_profiles)
    item_conditions = []
    if items:
        item_conditions.append("sii.item_code in %(items)s")
        params["items"] = tuple(items)
    if item_groups:
        item_conditions.append("sii.item_group in %(item_groups)s")
        params["item_groups"] = tuple(item_groups)
    if owners:
        base_conditions.append("si.owner in %(owners)s")
        params["owners"] = tuple(owners)

    cond_detail = " AND ".join(base_conditions + item_conditions)

    gross_expr = "COALESCE(sii.base_amount, sii.amount, 0)"
    net_expr = "COALESCE(sii.base_net_amount, sii.net_amount, 0)"
    discount_expr = f"COALESCE({gross_expr} - {net_expr}, 0)"

    detail = frappe.db.sql(
        f"""
        SELECT
            {branch_expr} AS branch,
            si.pos_profile,
            sii.item_code,
            sii.item_name,
            sii.item_group,
            SUM(sii.qty) AS qty,
            SUM({gross_expr}) AS gross_sales,
            SUM({discount_expr}) AS discount_amount,
            SUM({net_expr}) AS net_sales
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {cond_detail}
        GROUP BY {branch_expr}, si.pos_profile, sii.item_code, sii.item_name, sii.item_group
        """,
        params,
        as_dict=True,
    )

    total_net = sum(d.net_sales or 0 for d in detail)

    for d in detail:
        d.tax_amount = d.get("tax_amount") or 0
        d.net_with_tax = (d.net_sales or 0) + d.tax_amount
        d.sales_pct = ((d.net_sales or 0) / total_net * 100) if total_net else 0

    # branch summary
    branch_summary = {}
    for d in detail:
        key = d.branch or "Unknown"
        row = branch_summary.setdefault(
            key,
            {
                "branch": key,
                "gross_sales": 0,
                "discount_amount": 0,
                "tax_amount": 0,
                "net_sales": 0,
                "net_with_tax": 0,
                "qty": 0,
            },
        )
        row["gross_sales"] += d.gross_sales or 0
        row["discount_amount"] += d.discount_amount or 0
        row["tax_amount"] += d.tax_amount or 0
        row["net_sales"] += d.net_sales or 0
        row["net_with_tax"] += d.net_with_tax or 0
        row["qty"] += d.qty or 0

    totals = {
        "gross_sales": sum(r["gross_sales"] for r in branch_summary.values()),
        "discount_amount": sum(r["discount_amount"] for r in branch_summary.values()),
        "tax_amount": sum(r["tax_amount"] for r in branch_summary.values()),
        "net_sales": sum(r["net_sales"] for r in branch_summary.values()),
        "net_with_tax": sum(r["net_with_tax"] for r in branch_summary.values()),
        "qty": sum(r["qty"] for r in branch_summary.values()),
    }

    chart = {
        "labels": [r["branch"] for r in branch_summary.values()],
        "values": [r["net_sales"] for r in branch_summary.values()],
    }

    orders_cond_items = []
    if items:
        orders_cond_items.append("sii2.item_code in %(items)s")
    if item_groups:
        orders_cond_items.append("sii2.item_group in %(item_groups)s")
    cond_orders = " AND ".join(base_conditions + orders_cond_items)

    orders = frappe.db.sql(
        f"""
        SELECT
            si.name,
            si.customer_name,
            {branch_expr} AS branch,
            si.pos_profile,
            si.posting_date,
            COALESCE(si.base_grand_total, si.grand_total, 0) AS grand_total,
            COALESCE(si.base_discount_amount, 0) AS discount_amount,
            COALESCE(si.base_total_taxes_and_charges, 0) AS tax_amount,
            COALESCE(si.base_net_total, si.base_total, 0) AS net_total
        FROM `tabSales Invoice` si
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        LEFT JOIN `tabSales Invoice Item` sii2 ON sii2.parent = si.name
        WHERE {cond_orders}
        GROUP BY si.name
        ORDER BY si.posting_date DESC, si.name DESC
        """,
        params,
        as_dict=True,
    )

    return {
        "detail": detail,
        "branch_summary": list(branch_summary.values()),
        "totals": totals,
        "chart": chart,
        "orders": orders,
    }


def _normalize(val):
    if not val:
        return []
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    if isinstance(val, (list, tuple)):
        cleaned = []
        for v in val:
            if isinstance(v, dict):
                cleaned.append(v.get("value") or v.get("name") or v.get("label") or "")
            else:
                cleaned.append(v)
        return [c for c in cleaned if c]
    return [val]


def _branch_expr():
    parts = []
    if frappe.db.has_column("POS Profile", "branch"):
        parts.append("pp.branch")
    if frappe.db.has_column("Sales Invoice", "branch"):
        parts.append("si.branch")
    if not parts:
        return "'Unknown'"
    return f"COALESCE({', '.join(parts)})"
