# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import frappe
from frappe import _
from frappe.utils import getdate, flt


@frappe.whitelist()
def make_super_closing(business_day=None, pos_profiles=None, company=None):
    """
    Create a POS Super Closing by aggregating POS Closing Shifts for the given business day and profiles.
    - business_day: date string
    - pos_profiles: comma separated or list
    """
    business_day = getdate(business_day) if business_day else getdate()
    profiles = _normalize(pos_profiles)

    # Find closing shifts whose window overlaps the business day
    query = """
        SELECT
            name,
            pos_profile,
            user,
            grand_total,
            net_total,
            company,
            period_start_date,
            period_end_date
        FROM `tabPOS Closing Shift`
        WHERE docstatus = 1
          AND DATE(period_start_date) <= %(day)s
          AND DATE(period_end_date) >= %(day)s
    """
    params = {"day": business_day}
    if profiles:
        query += " AND pos_profile IN %(profiles)s"
        params["profiles"] = tuple(profiles)
    if company:
        query += " AND company = %(company)s"
        params["company"] = company

    query += " ORDER BY period_start_date ASC"

    shifts = frappe.db.sql(query, params, as_dict=True)

    if not shifts:
        recent = frappe.db.sql(
            """
            SELECT name, pos_profile, company, posting_date, period_start_date, period_end_date
            FROM `tabPOS Closing Shift`
            WHERE docstatus = 1
            ORDER BY creation DESC
            LIMIT 5
            """,
            as_dict=True,
        )
        frappe.log_error(
            title="POS Super Closing lookup failed",
            message=f"Day: {business_day}\nProfiles: {profiles}\nCompany: {company}\nParams: {params}\nRecent shifts: {recent}",
        )
        frappe.throw(_("No POS Closing Shifts found for {0}").format(business_day))

    # choose first as morning, last as evening if two exist
    morning = shifts[0]["name"]
    evening = shifts[-1]["name"] if len(shifts) > 1 else None

    # aggregate sales from POS Closing Shifts (net_total preferred)
    total_sales = sum(flt(s.get("net_total")) for s in shifts)

    # aggregate payments by summing closing_amount from payment_reconciliation
    payments_total = 0
    for s in shifts:
        recs = frappe.get_all(
            "POS Closing Shift Detail",
            filters={"parent": s["name"]},
            fields=["closing_amount"],
        )
        payments_total += sum(flt(r.closing_amount) for r in recs)

    variance = payments_total - total_sales

    doc = frappe.get_doc(
        {
            "doctype": "POS Super Closing",
            "business_day": business_day,
            "company": (company or (shifts[0].get("company") if shifts else None)),
            "pos_profiles": ", ".join(profiles) if profiles else None,
            "morning_shift": morning,
            "evening_shift": evening,
            "total_sales": total_sales,
            "total_payments": payments_total,
            "variance": variance,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _normalize(val):
    if not val:
        return []
    if isinstance(val, str):
        if val.strip() in ("[]", ""):
            return []
        return [v.strip() for v in val.split(",") if v.strip()]
    if isinstance(val, (list, tuple)):
        cleaned = []
        for v in val:
            if isinstance(v, dict):
                cleaned.append(v.get("value") or v.get("name") or v.get("label") or "")
            else:
                cleaned.append(v)
        return [c for c in cleaned if c and c != "[]"]
    return [val]
