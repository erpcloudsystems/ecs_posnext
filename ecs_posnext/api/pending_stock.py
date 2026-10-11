# -*- coding: utf-8 -*-
# Pending-stock (backorder) invoices for the POS.
#
# When "Draft on Insufficient Stock" is enabled on a POS Profile, a sale whose
# submit throws (for any reason — not a qty pre-check) is held as a draft
# (posa_pending_stock=1) with the error saved as posa_pending_stock_reason. This
# module lists those held drafts with their reason, and finalizes (submits) a
# draft once the cause is fixed.

import frappe
from frappe import _
from frappe.utils import flt

from ecs_posnext.api.invoices import _hold_as_pending_stock, _submit_invoice


def _pending_filters(pos_profile=None, pos_opening_shift=None):
    filters = {"docstatus": 0, "posa_pending_stock": 1}
    if pos_opening_shift:
        filters["posa_pos_opening_shift"] = pos_opening_shift
    elif pos_profile:
        filters["pos_profile"] = pos_profile
    return filters


@frappe.whitelist()
def count_pending_stock_invoices(pos_profile=None, pos_opening_shift=None):
    """Fast count of held pending-stock drafts (used to guard shift closing)."""
    return frappe.db.count("Sales Invoice", _pending_filters(pos_profile, pos_opening_shift))


@frappe.whitelist()
def get_pending_stock_invoices(pos_profile=None, pos_opening_shift=None):
    """List held pending-stock drafts with the error that held each one.

    Returns {invoices: [...]}.
    """
    has_reason = frappe.db.has_column("Sales Invoice", "posa_pending_stock_reason")
    names = frappe.get_all(
        "Sales Invoice",
        filters=_pending_filters(pos_profile, pos_opening_shift),
        pluck="name",
        order_by="modified desc",
        limit_page_length=0,
    )

    invoices = []
    for name in names:
        doc = frappe.get_doc("Sales Invoice", name)
        invoices.append(
            {
                "name": doc.name,
                "customer": doc.customer,
                "customer_name": doc.customer_name,
                "posting_date": str(doc.posting_date),
                "grand_total": flt(doc.grand_total),
                "currency": doc.currency,
                "reason": doc.get("posa_pending_stock_reason") if has_reason else None,
                "items": [
                    {
                        "item_code": it.item_code,
                        "item_name": it.item_name,
                        "warehouse": it.warehouse,
                        "qty": flt(it.qty),
                    }
                    for it in doc.items
                ],
            }
        )

    return {"invoices": invoices}


@frappe.whitelist()
def finalize_pending_invoice(invoice_name):
    """Submit a held pending-stock draft, synchronously.

    Runs the normal submit (Step 1 + Step 2) inline so the cashier sees the
    outcome right away. On failure the draft stays held and its reason is
    updated to the new error, which is re-raised to the UI.
    """
    doc = frappe.get_doc("Sales Invoice", invoice_name)
    if doc.docstatus != 0:
        frappe.throw(_("Invoice {0} is not a draft").format(invoice_name))

    try:
        result = _submit_invoice(invoice=doc.as_dict(), data={"finalize_pending": 1})
    except Exception as e:
        frappe.db.rollback()
        _hold_as_pending_stock("Sales Invoice", invoice_name, e)
        raise

    values = {"posa_pending_stock": 0}
    if frappe.db.has_column("Sales Invoice", "posa_pending_stock_reason"):
        values["posa_pending_stock_reason"] = None
    frappe.db.set_value("Sales Invoice", invoice_name, values, update_modified=False)
    frappe.db.commit()
    return result
