# -*- coding: utf-8 -*-
# Party reservation closing for the POS.
#
# Flow:
#   - A party is reserved (via the web/booking flow in ecs_vim) as a Sales Order
#     with pos_status="Open", advance_amount, select_event/select_slot, branch and
#     delivery_date (= visit/party date). A "deposit" Sales Invoice records the
#     down payment and is linked to the Sales Order.
#   - In the POS the cashier picks a Visit Date + Customer, selects the reserved
#     Sales Order (items auto-load), then closes the party: the deposit invoice is
#     reversed (return invoice) and the full party invoice is created, so the
#     customer pays (full - deposit). The Sales Order is then marked "Executed".
#
# NOTE: the accounting netting (deposit reversal + advance/credit application on
# the full invoice) must be validated against the GL with finance before rollout.

import json

import frappe
from frappe import _
from frappe.utils import flt, nowdate

from ecs_posnext.api.invoices import submit_invoice, update_invoice

DEPOSIT_ITEM_CODE = "PARTY-DEPOSIT"


def _get_or_create_deposit_item():
    """Return the dedicated party-deposit service item, creating it once if missing."""
    if frappe.db.exists("Item", DEPOSIT_ITEM_CODE):
        return DEPOSIT_ITEM_CODE

    group = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"
    item = frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": DEPOSIT_ITEM_CODE,
            "item_name": "Party Deposit",
            "item_group": group,
            "stock_uom": "Nos",
            "is_stock_item": 0,
            "is_sales_item": 1,
            "is_purchase_item": 0,
            "include_item_in_manufacturing": 0,
        }
    )
    item.flags.ignore_permissions = True
    item.insert()
    return DEPOSIT_ITEM_CODE


def _default_mode_of_payment(pos_profile_doc):
    """Pick the default (or first) mode of payment from the POS Profile."""
    if pos_profile_doc and pos_profile_doc.get("payments"):
        default = next((p for p in pos_profile_doc.payments if p.get("default")), None)
        return (default or pos_profile_doc.payments[0]).mode_of_payment
    return "Cash"


def _get_deposit_invoices(sales_order):
    """Return all (partial) deposit Sales Invoices for a reservation.

    Deposit invoices are identified by the header link `extended_order_no` (set by
    create_deposit_invoice), which the full closing invoice does NOT set — so this
    never picks up the full party invoice. A reservation may have several deposit
    invoices (e.g. 200 now, 400 later). Only submitted, non-return invoices.
    """
    if not sales_order:
        return []

    return frappe.db.get_all(
        "Sales Invoice",
        filters={"extended_order_no": sales_order, "is_return": 0, "docstatus": 1},
        fields=["name", "grand_total"],
        order_by="creation",
    )


def _net_unreversed_deposit(sales_order):
    """Sum of deposit invoices that have NOT already been reversed by a credit note.

    Already-reversed deposits (e.g. from an earlier failed close, where the credit
    note can't be cancelled because it was reported to ZATCA) are excluded so the
    closing invoice does not double-net them.
    """
    total = 0.0
    for deposit in _get_deposit_invoices(sales_order):
        already_returned = frappe.db.exists(
            "Sales Invoice", {"return_against": deposit["name"], "docstatus": 1}
        )
        if not already_returned:
            total += flt(deposit["grand_total"])
    return total


@frappe.whitelist()
def get_reservation_sales_orders(pos_profile, visit_date=None, customer=None):
    """List open party-reservation Sales Orders for a visit date and/or customer.

    Port of posawesome's get_sales_order_names, parameterized (no SQL injection).
    Returns each SO with remaining (un-invoiced) item quantities and the linked
    deposit invoice so the POS can close it.
    """
    filters = {"pos_status": "Open", "docstatus": 1}
    if visit_date:
        filters["delivery_date"] = visit_date
    if customer:
        filters["customer"] = customer

    sales_orders = frappe.db.get_all(
        "Sales Order",
        filters=filters,
        fields=[
            "name",
            "customer",
            "customer_name",
            "contact_mobile",
            "delivery_date",
            "pos_status",
            "select_event",
            "select_slot",
            "branch",
            "grand_total",
            "advance_amount",
            "custom_advance_paid",
        ],
        order_by="name",
    )

    for row in sales_orders:
        # Quantities already invoiced against this SO, per item.
        invoiced = frappe.db.sql(
            """
            SELECT item_code, SUM(qty) AS qty, SUM(amount) AS amount
            FROM `tabSales Invoice Item`
            WHERE sales_order = %s AND docstatus = 1
            GROUP BY item_code
            """,
            (row["name"],),
            as_dict=1,
        )
        invoiced_map = {i["item_code"]: i for i in invoiced}

        so_doc = frappe.get_doc("Sales Order", row["name"])
        remaining_items = []
        description_lines = []
        for it in so_doc.items:
            already = invoiced_map.get(it.item_code)
            remaining_qty = it.qty - (already["qty"] if already else 0)
            description_lines.append(f"{it.item_name} - ({remaining_qty})")
            if remaining_qty > 0:
                remaining_items.append(
                    {
                        "item_code": it.item_code,
                        "item_name": it.item_name,
                        "qty": remaining_qty,
                        "rate": it.rate,
                        "uom": it.uom,
                        "warehouse": it.warehouse,
                        "sales_order": row["name"],
                    }
                )

        row["items"] = remaining_items
        row["description"] = "\n".join(description_lines)
        deposits = _get_deposit_invoices(row["name"])
        row["deposit_invoices"] = [d["name"] for d in deposits]
        # Net (unreversed) deposit = what reduces the amount due at close.
        row["total_deposit"] = _net_unreversed_deposit(row["name"])

    return sales_orders


@frappe.whitelist()
def load_sales_order_into_cart(sales_order, pos_profile=None):
    """Build a full Sales Invoice from a Sales Order and return cart-ready items/taxes.

    Uses ERPNext's standard make_sales_invoice so pricing, taxes and SO links are
    populated correctly. The frontend uses this to auto-load the party items.
    """
    from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

    si = make_sales_invoice(sales_order)
    si.is_pos = 1
    if pos_profile:
        si.pos_profile = pos_profile

    items = [
        {
            "item_code": it.item_code,
            "item_name": it.item_name,
            "qty": it.qty,
            "rate": it.rate,
            "uom": it.uom,
            "warehouse": it.warehouse,
            "sales_order": sales_order,
        }
        for it in si.items
    ]
    taxes = [
        {
            "charge_type": t.charge_type,
            "account_head": t.account_head,
            "rate": t.rate,
            "description": t.description,
            "included_in_print_rate": t.included_in_print_rate,
        }
        for t in si.get("taxes", [])
    ]

    return {
        "sales_order": sales_order,
        "customer": si.customer,
        "customer_name": si.customer_name,
        "items": items,
        "taxes": taxes,
        "total_deposit": _net_unreversed_deposit(sales_order),
    }


@frappe.whitelist()
def create_deposit_invoice(
    sales_order,
    pos_profile=None,
    amount=None,
    payments=None,
    posting_date=None,
    mode_of_payment=None,
    pos_opening_shift=None,
):
    """Create + submit a paid POS deposit (down-payment) Sales Invoice for a reservation.

    The deposit invoice is a single line of the dedicated "Party Deposit" item at the
    deposit amount, recorded as paid (is_pos) and linked to the Sales Order via
    `extended_order_no`. It is reversed later when the party is closed.

    Args:
        sales_order: the reservation Sales Order.
        pos_profile: active POS Profile, only meaningful when there's a live POS
                     session (e.g. the in-app Reservations screen). Optional —
                     when omitted (e.g. the "Create Deposit Invoice" button on
                     the Sales Order desk form, where there is no POS session),
                     no profile is guessed and none is set on the invoice;
                     company and branch are taken from the Sales Order instead.
        amount: deposit amount; defaults to the SO's advance_amount.
        payments: optional list of {mode_of_payment, amount}; takes precedence
                  over `mode_of_payment` when given.
        posting_date: invoice posting date; defaults to today.
        mode_of_payment: single mode of payment for the full amount; ignored
                         if `payments` is given; defaults to the profile's
                         default mode of payment when a POS Profile is given,
                         otherwise required.
        pos_opening_shift: the cashier's active POS Opening Shift, so the deposit
                            shows up in that shift's cash reconciliation.
    """
    so = frappe.get_doc("Sales Order", sales_order)
    amount = flt(amount) or flt(so.get("advance_amount"))
    if amount <= 0:
        frappe.throw(_("Please specify a deposit amount greater than zero"))

    if isinstance(payments, str):
        payments = json.loads(payments)

    # Multiple (partial) deposits are allowed per reservation (e.g. 200 now, 400 later),
    # so we do NOT block when a deposit invoice already exists.

    # pos_profile is only set when the caller actually has a POS session (the
    # in-app Reservations screen passes the cashier's active profile). We never
    # guess one here — any other enabled profile for the company is effectively
    # random and can carry the wrong branch/accounts onto the invoice.
    pos_profile_doc = frappe.get_cached_doc("POS Profile", pos_profile) if pos_profile else None
    if not payments and not mode_of_payment and not pos_profile_doc:
        frappe.throw(_("Please specify a mode of payment"))

    item_code = _get_or_create_deposit_item()

    # Copy the Sales Order's own VAT template + rows onto the deposit invoice so it
    # is taxed the same way the full party invoice / a normal POS sale would be.
    # Without this the invoice keeps an empty "taxes" table while
    # custom_zatca_tax_category still defaults to "Standard", which makes ZATCA's
    # e-invoice XML generation blow up (it indexes taxes[0] unconditionally for a
    # Standard-rated invoice).
    #
    # `amount` is the exact figure the cashier collects and records under
    # `payments` below, so tax must be forced inclusive here (regardless of the
    # SO template's own setting) — otherwise VAT is added on top of `amount`,
    # the grand total no longer matches what was collected, and the invoice
    # comes out "Partly Paid".
    taxes_and_charges = so.get("taxes_and_charges")
    taxes = [
        {
            "charge_type": t.charge_type,
            "account_head": t.account_head,
            "rate": t.rate,
            "description": t.description,
            "included_in_print_rate": 1,
            "cost_center": t.cost_center,
        }
        for t in so.get("taxes", [])
    ]

    invoice_data = {
        "doctype": "Sales Invoice",
        "customer": so.customer,
        "company": so.company,
        # Same fieldname on Sales Order and Sales Invoice — copy directly so the
        # deposit invoice lands on the reservation's own branch, not the POS
        # profile's.
        "dimension_branch": so.get("dimension_branch"),
        "is_pos": 1,
        "update_stock": 0,
        "extended_order_no": sales_order,
        "posting_date": posting_date or nowdate(),
        "posa_pos_opening_shift": pos_opening_shift,
        "taxes_and_charges": taxes_and_charges,
        "taxes": taxes,
        "items": [
            {
                "item_code": item_code,
                "qty": 1,
                "rate": amount,
                "sales_order": sales_order,
                "dimension_branch": so.get("dimension_branch"),
            }
        ],
        "payments": payments
        or [
            {
                "mode_of_payment": mode_of_payment or _default_mode_of_payment(pos_profile_doc),
                "amount": amount,
            }
        ],
    }
    if pos_profile:
        invoice_data["pos_profile"] = pos_profile

    draft = update_invoice(invoice_data)
    invoice_data["name"] = draft.get("name")
    result = submit_invoice(invoice=invoice_data, data={})
    frappe.db.commit()

    return {"deposit_invoice": draft.get("name"), "amount": amount, "result": result}


@frappe.whitelist()
def close_party_reservation(sales_order, invoice_data, data=None, pos_profile=None):
    """Close a reserved party: bill the full party and net out the deposits paid.

    Instead of reversing each deposit invoice and reallocating credit (which is fragile),
    the full party invoice carries a single NEGATIVE "Party Deposit" line equal to the
    total deposit already paid. So:
        net invoice total = full - total_deposit   (the customer pays this now)
    and the deposit-item revenue cancels out across the deposit invoices (+) and this
    invoice (-), leaving exactly the party's real revenue. No returns, no credit JEs.

    Args:
        sales_order: the reserved Sales Order (pos_status="Open").
        invoice_data: the draft-invoice input (same dict the cart builds) for the full
                      party invoice; the cashier's payments collect (full - deposit).
        data: extra submit data (change_amount, write_off_amount, customer_credit_dict).
        pos_profile: active POS Profile.
    """
    invoice_data = json.loads(invoice_data) if isinstance(invoice_data, str) else invoice_data
    data = json.loads(data) if isinstance(data, str) else (data or {})

    if not frappe.db.exists("Sales Order", sales_order):
        frappe.throw(_("Sales Order {0} not found").format(sales_order))

    profile = pos_profile or invoice_data.get("pos_profile")

    # Only net deposits that haven't already been reversed (avoids double-netting
    # when an earlier attempt left an uncancellable credit note).
    total_deposit = _net_unreversed_deposit(sales_order)

    # Build the full party invoice; link each real line back to the SO.
    invoice_data["pos_profile"] = profile
    invoice_data.setdefault("is_pos", 1)
    for item in invoice_data.get("items", []):
        item.setdefault("sales_order", sales_order)

    # Net out the deposits already paid with one negative deposit line.
    if total_deposit > 0:
        invoice_data.setdefault("items", []).append(
            {
                "item_code": _get_or_create_deposit_item(),
                "item_name": "Party Deposit (paid)",
                "qty": 1,
                "rate": -total_deposit,
                "sales_order": sales_order,
            }
        )

    draft = update_invoice(invoice_data)
    invoice_data["name"] = draft.get("name")
    full_result = submit_invoice(invoice=invoice_data, data=data)

    # Mark the reservation as executed so it drops out of the open list.
    frappe.db.set_value("Sales Order", sales_order, "pos_status", "Executed")
    frappe.db.commit()

    return {
        "sales_order": sales_order,
        "total_deposit": total_deposit,
        "full_invoice": full_result,
    }
