# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from io import BytesIO

import openpyxl
import frappe
from frappe import _
from frappe.desk.utils import provide_binary_file


@frappe.whitelist()
def get_daily_item_sales_summary(filters=None):
    """Item-wise sales for a Business Day, with a per-branch breakdown."""
    filters = _parse_filters(filters)
    cond, params = _build_conditions(filters)

    branch_expr = _branch_expr()
    net_expr = "COALESCE(sii.base_net_amount, sii.net_amount, 0)"

    item_summary = frappe.db.sql(
        f"""
        SELECT
            sii.item_code,
            sii.item_name,
            SUM(sii.qty) AS total_qty,
            COUNT(DISTINCT si.name) AS invoice_count,
            SUM({net_expr}) AS total_amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {cond}
        GROUP BY sii.item_code, sii.item_name
        ORDER BY sii.item_name
        """,
        params,
        as_dict=True,
    )

    branch_detail = frappe.db.sql(
        f"""
        SELECT
            sii.item_code,
            sii.item_name,
            {branch_expr} AS branch,
            SUM(sii.qty) AS total_qty,
            COUNT(DISTINCT si.name) AS invoice_count,
            SUM({net_expr}) AS total_amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabPOS Profile` pp ON pp.name = si.pos_profile
        WHERE {cond}
        GROUP BY sii.item_code, sii.item_name, {branch_expr}
        ORDER BY sii.item_name, branch
        """,
        params,
        as_dict=True,
    )

    totals = {
        "total_qty": sum(d.total_qty or 0 for d in item_summary),
        "invoice_count": sum(d.invoice_count or 0 for d in item_summary),
        "total_amount": sum(d.total_amount or 0 for d in item_summary),
        "item_count": len(item_summary),
    }

    return {
        "item_summary": item_summary,
        "branch_detail": branch_detail,
        "totals": totals,
    }


@frappe.whitelist()
def download_excel(filters=None):
    """Stream the report (Item Summary + Branch Breakdown) as a real .xlsx file."""
    data = get_daily_item_sales_summary(filters)

    summary_rows = [["Item Code", "Item Name", "Total Qty Sold", "No. of Invoices", "Total Sales Amount"]]
    for d in data["item_summary"]:
        summary_rows.append(
            [d.item_code, d.item_name, d.total_qty, d.invoice_count, d.total_amount]
        )

    detail_rows = [["Item Code", "Item Name", "Branch", "Qty Sold", "No. of Invoices", "Sales Amount"]]
    for d in data["branch_detail"]:
        detail_rows.append(
            [d.item_code, d.item_name, d.branch, d.total_qty, d.invoice_count, d.total_amount]
        )

    wb = openpyxl.Workbook(write_only=True)
    _add_sheet(wb, "Item Summary", summary_rows)
    _add_sheet(wb, "Branch Breakdown", detail_rows)

    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    provide_binary_file("Daily Item Sales Summary", "xlsx", xlsx_file.getvalue())


def _add_sheet(wb, sheet_name, rows):
    ws = wb.create_sheet(sheet_name)
    for row in rows:
        ws.append(row)


def _parse_filters(filters):
    if isinstance(filters, str):
        filters = json.loads(filters or "{}")
    return filters or {}


def _build_conditions(filters):
    business_day = filters.get("business_day")
    branches = _normalize(filters.get("branches"))
    warehouses = _normalize(filters.get("warehouses"))
    item_groups = _normalize(filters.get("item_groups"))
    items = _normalize(filters.get("items"))

    conditions = ["si.docstatus = 1"]
    params = {}

    business_day_col = _business_day_column()
    if business_day:
        if not business_day_col:
            frappe.throw(_("Sales Invoice has no Business Day link column."))
        conditions.append(f"si.`{business_day_col}` = %(business_day)s")
        params["business_day"] = business_day

    branch_expr = _branch_expr()
    if branches:
        conditions.append(f"{branch_expr} in %(branches)s")
        params["branches"] = tuple(branches)

    if warehouses:
        conditions.append("sii.warehouse in %(warehouses)s")
        params["warehouses"] = tuple(warehouses)

    if item_groups:
        conditions.append("sii.item_group in %(item_groups)s")
        params["item_groups"] = tuple(item_groups)

    if items:
        conditions.append("sii.item_code in %(items)s")
        params["items"] = tuple(items)

    return " AND ".join(conditions), params


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


def _business_day_column():
    if frappe.db.has_column("Sales Invoice", "custom_pos_business_day"):
        return "custom_pos_business_day"
    if frappe.db.has_column("Sales Invoice", "pos_business_day"):
        return "pos_business_day"
    return None
