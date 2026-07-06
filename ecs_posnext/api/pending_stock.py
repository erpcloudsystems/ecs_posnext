# -*- coding: utf-8 -*-
# Pending-stock (backorder) invoices for the POS.
#
# When "Draft on Insufficient Stock" is enabled on a POS Profile, sales with a short
# line are held as drafts (posa_pending_stock=1) instead of blocking checkout. This
# module lists those held drafts + the items that need restocking, and finalizes
# (submits) a draft once stock is available.

import frappe
from frappe import _
from frappe.utils import flt

from ecs_posnext.api.invoices import _get_available_stock, submit_invoice


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
    """List held pending-stock drafts with per-item availability + a restock summary.

    Returns {invoices: [...], items_needed: [...]}. Each invoice has a `ready` flag
    (all lines now have enough stock) so the UI can enable "Finalize".
    """
    names = frappe.get_all(
        "Sales Invoice",
        filters=_pending_filters(pos_profile, pos_opening_shift),
        pluck="name",
        order_by="modified desc",
        limit_page_length=0,
    )

    invoices = []
    needed = {}  # (item_code, warehouse) -> aggregated shortage
    for name in names:
        doc = frappe.get_doc("Sales Invoice", name)
        items = []
        ready = True
        for it in doc.items:
            required = flt(it.stock_qty) or (flt(it.qty) * flt(it.conversion_factor or 1))
            available = flt(_get_available_stock(it.as_dict()))
            short = available < required
            if short:
                ready = False
                key = (it.item_code, it.warehouse)
                agg = needed.setdefault(
                    key,
                    {
                        "item_code": it.item_code,
                        "item_name": it.item_name,
                        "warehouse": it.warehouse,
                        "required": 0,
                        "available": available,
                        "shortage": 0,
                    },
                )
                agg["required"] += required
                agg["shortage"] += required - available
            items.append(
                {
                    "item_code": it.item_code,
                    "item_name": it.item_name,
                    "warehouse": it.warehouse,
                    "qty": flt(it.qty),
                    "required": required,
                    "available": available,
                    "short": short,
                }
            )

        invoices.append(
            {
                "name": doc.name,
                "customer": doc.customer,
                "customer_name": doc.customer_name,
                "posting_date": str(doc.posting_date),
                "grand_total": flt(doc.grand_total),
                "currency": doc.currency,
                "ready": ready,
                "items": items,
            }
        )

    return {"invoices": invoices, "items_needed": list(needed.values())}


@frappe.whitelist()
def finalize_pending_invoice(invoice_name):
    """Submit a held pending-stock draft now that stock is available.

    Reuses submit_invoice with finalize_pending=1 so it runs the normal stock
    validation (throws if still short) + creates the Payment Entries; the draft's
    already-collected payments are preserved.
    """
    doc = frappe.get_doc("Sales Invoice", invoice_name)
    if doc.docstatus != 0:
        frappe.throw(_("Invoice {0} is not a draft").format(invoice_name))

    invoice = doc.as_dict()
    result = submit_invoice(invoice=invoice, data={"finalize_pending": 1})

    # Clear the pending flag on success (submitted → no longer in the list anyway).
    if frappe.db.exists("Sales Invoice", invoice_name):
        frappe.db.set_value(
            "Sales Invoice", invoice_name, "posa_pending_stock", 0, update_modified=False
        )
    frappe.db.commit()
    return result
