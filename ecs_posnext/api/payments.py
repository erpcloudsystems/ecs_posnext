# -*- coding: utf-8 -*-
# POS payment integrations for ecs_posnext:
#   - Credit card (Geidea Web ECR): the browser drives the terminal directly over a
#     WebSocket to the Geidea Windows service on the cashier PC (ws://localhost:5000).
#     The server only hands the POS the terminal's connection settings; there is no
#     server-side gateway to call, so nothing here talks to the terminal itself.
#   - Tabby (Paymob QuickLink): create a payment link + SMS it to the customer, via ecs_vim.

import frappe
from frappe import _
from frappe.utils import cint

# Paymob payment-method IDs for Tabby (same as ecs_vim/posawesome).
TABBY_PAYMENT_METHODS = [21373, 24013]


# ---------------------------------------------------------------------------
# Credit card (Geidea Web ECR)
# ---------------------------------------------------------------------------

# Fields the POS needs to open the WebSocket and build the CONNECT payload.
# Names match the Geidea Web ECR JSON keys where the doc defines them (including
# the "BraudRate" spelling used by the service).
_TERMINAL_FIELDS = (
    "name",
    "terminal_name",
    "service_url",
    "connection_mode",
    "com_name",
    "braud_rate",
    "data_bits",
    "parity",
    "ip_address",
    "port",
    "app_id",
    "print_settings",
)


@frappe.whitelist()
def has_card_terminal(pos_profile=None):
    """True if an active Geidea terminal is mapped to this POS Profile.

    The POS uses this to decide whether credit-card payments must go through the
    terminal-approval flow. Profiles without a terminal take card payments normally.
    """
    if not pos_profile:
        return False
    return bool(
        frappe.db.get_value(
            "Geidea Terminal", {"is_active": 1, "pos_profile": pos_profile}, "name"
        )
    )


@frappe.whitelist()
def get_card_terminal(pos_profile=None):
    """Connection settings for this POS Profile's active Geidea terminal.

    Returns None when the profile has no active terminal, which the POS reads as
    "take card payments without the terminal-approval gate".
    """
    if not pos_profile:
        return None

    terminal = frappe.db.get_value(
        "Geidea Terminal",
        {"is_active": 1, "pos_profile": pos_profile},
        _TERMINAL_FIELDS,
        as_dict=True,
    )
    if not terminal:
        return None

    return {
        "name": terminal.name,
        "terminal_name": terminal.terminal_name,
        "service_url": terminal.service_url or "ws://localhost:5000/messages",
        "connection_mode": terminal.connection_mode or "TCP",
        "com_name": terminal.com_name,
        "braud_rate": terminal.braud_rate or "38400",
        "data_bits": terminal.data_bits or "8",
        "parity": terminal.parity or "none",
        "ip_address": terminal.ip_address,
        "port": cint(terminal.port) or None,
        "app_id": terminal.app_id or "11",
        "print_settings": terminal.print_settings or "1",
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
