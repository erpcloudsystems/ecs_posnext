# -*- coding: utf-8 -*-
# POS payment integrations for ecs_posnext, delegating to the existing ecs_vim gateways:
#   - Credit card (Span / DigitalPay terminal): checkout + status polling -> approval code(s)
#   - Tabby (Paymob QuickLink): create a payment link + SMS it to the customer
#
# All heavy lifting (terminal API, Paymob API, approval-code child table) already lives
# in ecs_vim; these are thin, whitelisted wrappers so the POS only calls ecs_posnext.

import frappe
from frappe import _

# Paymob payment-method IDs for Tabby (same as ecs_vim/posawesome).
TABBY_PAYMENT_METHODS = [21373, 24013]


# ---------------------------------------------------------------------------
# Credit card (Span / DigitalPay)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def has_card_terminal(pos_profile=None):
    """True if an active DigitalPay (Span) terminal is mapped to this POS Profile.

    The POS uses this to decide whether credit-card payments must go through the
    terminal-approval flow. Profiles without a terminal take card payments normally.
    """
    if not pos_profile:
        return False
    return bool(
        frappe.db.get_value(
            "DigitalPay Terminal", {"is_active": 1, "pos_profile": pos_profile}, "name"
        )
    )


@frappe.whitelist()
def card_checkout(pos_profile, amount, reference_name, reference_doctype="Sales Invoice"):
    """Send an amount to the card terminal and return the created transaction."""
    from ecs_vim.api import dp_create_checkout

    result = dp_create_checkout(
        amount_sar=amount,
        pos_profile=pos_profile,
        reference_doctype=reference_doctype,
        reference_name=reference_name,
    )
    if not result or not result.get("transaction"):
        frappe.throw(_("Could not start the card terminal transaction. Check the terminal mapping for this POS Profile."))
    return result


@frappe.whitelist()
def card_status(tx_name):
    """Poll a card transaction. Returns status (+ approval_code when APPROVED).

    dp_verify also appends the approval code to the Sales Invoice's
    custom_approval_codes child table (by reference), so multiple card
    transactions accumulate multiple approval codes on the invoice.
    """
    from ecs_vim.api import dp_verify

    result = dp_verify(tx_name) or {}
    tx_status = frappe.db.get_value("DigitalPay Transaction", tx_name, "status")
    return {
        "status": result.get("status") or tx_status,
        "approval_code": result.get("approval_code"),
        "retrieval_reference_number": result.get("retrieval_reference_number"),
    }


# ---------------------------------------------------------------------------
# Tabby (Paymob QuickLink)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def create_tabby_link(invoice_name):
    """Create a Tabby (Paymob QuickLink) payment link for a Sales Invoice and SMS it.

    Returns {payment_url, sms_sent, mobile}.
    """
    from ecs_vim.invoice_billing import create_paymob_intention

    si = frappe.get_doc("Sales Invoice", invoice_name)
    result = create_paymob_intention(
        si,
        payment_methods=TABBY_PAYMENT_METHODS,
        paid_for_doctype="Sales Invoice",
    )
    if not result or not result.get("success"):
        error = (result or {}).get("error") if isinstance(result, dict) else None
        frappe.throw(_("Failed to create the Tabby payment link. {0}").format(error or ""))

    payment_url = result.get("payment_url")

    mobile = frappe.db.get_value("Customer", si.customer, "mobile_no")
    sms_sent = False
    if mobile and payment_url:
        try:
            from ecs_vim.sms.send_sms import send_sms

            send_sms(
                _("Payment link for invoice {0}: {1}").format(si.name, payment_url),
                mobile,
            )
            sms_sent = True
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Tabby SMS Send Error")

    return {"payment_url": payment_url, "sms_sent": sms_sent, "mobile": mobile}
