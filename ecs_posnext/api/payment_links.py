# -*- coding: utf-8 -*-
"""POS "Send Payment Link" (Paymob) and Tabby payment links.

Flow:
  1. Checkout with a "Paymob" payment row (shown to the cashier as "Send Payment
     Link") or with Tabby: the Sales Invoice is saved as a DRAFT with its payment
     amounts, a Paymob link is created for the link amount and SMSed to the
     customer. Nothing is submitted.
  2. When the customer pays, the draft is submitted through the normal POS submit
     pipeline (invoices._finalize_invoice_submit). This is triggered by:
       - the Paymob processed webhook (ecs_vim.paymob_gateway), or
       - the cashier pressing "Check status" in the Payment Links dialog, or
       - the background check every few minutes (check_pending_payment_links).
  3. The cashier sees every held invoice and its status in the Payment Links dialog.

Statuses (Sales Invoice.payment_status): Pending -> Paid (submitted) / Failed.
"""

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, now_datetime

PAYMENT_LINK_MODE = "Paymob"
TABBY_MODE = "Tabby"
# Paymob payment-method IDs for Tabby (same as ecs_vim/posawesome).
TABBY_PAYMENT_METHODS = [21373, 24013]
INQUIRY_URL = "https://ksa.paymob.com/api/ecommerce/orders/transaction_inquiry"
BACKGROUND_CHECK_DAYS = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def merchant_order_id(invoice_name):
    # Must match ecs_vim.invoice_billing.create_paymob_intention
    return f"SI-{invoice_name}"


def _mode_amount(doc_or_payments, mode):
    rows = doc_or_payments.get("payments") if hasattr(doc_or_payments, "get") else doc_or_payments
    return flt(sum(flt(r.get("amount")) for r in (rows or []) if r.get("mode_of_payment") == mode), 2)


def link_kind(invoice, is_tabby=False):
    """'tabby' / 'link' / None for an invoice dict or document."""
    if is_tabby or _mode_amount(invoice, TABBY_MODE) > 0:
        return "tabby"
    if _mode_amount(invoice, PAYMENT_LINK_MODE) > 0:
        return "link"
    return None


def _link_payment_methods(kind):
    if kind == "tabby":
        return TABBY_PAYMENT_METHODS
    settings = frappe.get_single("Paymob Settings Integration")
    ids = [cint(settings.get("integration_id")), cint(settings.get("integration_id_apple_pay"))]
    ids = [i for i in ids if i]
    if not ids:
        frappe.throw(_("Paymob card / Apple Pay integration IDs are not set in Paymob Settings Integration"))
    return ids


def _set_status(name, status, txn_id=None, url=None):
    values = {"payment_status": status, "custom_payment_status": status}
    if txn_id:
        values["custom_payment_invoice_id"] = txn_id
    if url:
        values["custom_url"] = url
    frappe.db.set_value("Sales Invoice", name, values, update_modified=False)


def _send_link_sms(si, payment_url, amount):
    mobile = frappe.db.get_value("Customer", si.customer, "mobile_no")
    if not (mobile and payment_url):
        return False, mobile
    try:
        from ecs_vim.sms.send_sms import send_sms

        send_sms(
            _("Payment link for invoice {0} ({1} SAR): {2}").format(si.name, flt(amount, 2), payment_url),
            mobile,
        )
        return True, mobile
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Payment Link SMS Send Error")
        return False, mobile


# ---------------------------------------------------------------------------
# Create / resend
# ---------------------------------------------------------------------------


def create_payment_link(invoice_name, kind):
    """Create a Paymob link for the draft invoice's link amount and SMS it."""
    from ecs_vim.invoice_billing import create_paymob_intention

    si = frappe.get_doc("Sales Invoice", invoice_name)
    if si.docstatus != 0:
        frappe.throw(_("Invoice {0} is already submitted").format(si.name))

    mode = TABBY_MODE if kind == "tabby" else PAYMENT_LINK_MODE
    amount = _mode_amount(si, mode) or flt(si.rounded_total or si.grand_total, 2)

    result = create_paymob_intention(
        si,
        payment_methods=_link_payment_methods(kind),
        paid_amount=amount,
        paid_for_doctype="Sales Invoice",
    )
    if not result or not result.get("success"):
        error = (result or {}).get("error") if isinstance(result, dict) else None
        frappe.throw(_("Failed to create the payment link. {0}").format(error or ""))

    payment_url = result.get("payment_url")
    _set_status(si.name, "Pending", url=payment_url)
    sms_sent, mobile = _send_link_sms(si, payment_url, amount)
    si.add_comment("Comment", _("Payment link sent ({0} SAR): {1}").format(amount, payment_url))
    return {"payment_url": payment_url, "sms_sent": sms_sent, "mobile": mobile, "amount": amount, "kind": kind}


@frappe.whitelist()
def resend_payment_link(invoice_name, new_link=0):
    """SMS the existing link again, or create a fresh one (e.g. after a failed payment)."""
    si = frappe.get_doc("Sales Invoice", invoice_name)
    if si.docstatus != 0:
        frappe.throw(_("Invoice {0} is already submitted").format(si.name))
    kind = link_kind(si) or "link"
    if cint(new_link) or not si.get("custom_url"):
        return create_payment_link(si.name, kind)
    mode = TABBY_MODE if kind == "tabby" else PAYMENT_LINK_MODE
    amount = _mode_amount(si, mode) or flt(si.rounded_total or si.grand_total, 2)
    sms_sent, mobile = _send_link_sms(si, si.custom_url, amount)
    return {"payment_url": si.custom_url, "sms_sent": sms_sent, "mobile": mobile, "amount": amount, "kind": kind}


# ---------------------------------------------------------------------------
# Settle (paid -> submit)
# ---------------------------------------------------------------------------


def settle_paid_invoice(invoice_name, txn_id=None, source="webhook"):
    """Mark the held invoice Paid and submit it through the POS submit pipeline.
    Idempotent: does nothing if the invoice is no longer a draft."""
    row = frappe.db.get_value("Sales Invoice", invoice_name, ["docstatus"], as_dict=True, for_update=True)
    if not row or row.docstatus != 0:
        return False

    _set_status(invoice_name, "Paid", txn_id=txn_id)
    si = frappe.get_doc("Sales Invoice", invoice_name)
    payments = [
        {"mode_of_payment": p.mode_of_payment, "amount": flt(p.amount)} for p in si.payments if flt(p.amount)
    ]

    from ecs_posnext.api.invoices import _finalize_invoice_submit

    previous_user = frappe.session.user
    try:
        # The webhook / scheduler user may not have Sales Invoice submit rights.
        frappe.set_user("Administrator")
        _finalize_invoice_submit(
            name=invoice_name,
            doctype="Sales Invoice",
            invoice={"payments": payments, "pos_profile": si.pos_profile},
            data={},
        )
    finally:
        frappe.set_user(previous_user)

    frappe.get_doc("Sales Invoice", invoice_name).add_comment(
        "Comment", _("Payment link paid (txn {0}, via {1}); invoice submitted").format(txn_id or "-", source)
    )
    frappe.db.commit()
    return True


def handle_paymob_result(invoice_name, success, txn_id=None, source="webhook"):
    """Called by the Paymob webhook (ecs_vim) for POS Sales Invoices."""
    if success:
        return settle_paid_invoice(invoice_name, txn_id, source)
    if frappe.db.get_value("Sales Invoice", invoice_name, "docstatus") == 0:
        _set_status(invoice_name, "Failed", txn_id=txn_id)
        frappe.db.commit()
    return False


def _inquire(invoice_name):
    """Ask Paymob for the latest transaction of this invoice.
    Returns ("Paid"|"Failed"|"Pending", txn_id) or (None, None) when unknown."""
    import requests

    secret_key = frappe.get_single("Paymob Settings Integration").get_password("secret_key", raise_exception=False)
    if not secret_key:
        return None, None
    try:
        r = requests.get(
            INQUIRY_URL,
            params={"merchant_order_id": merchant_order_id(invoice_name)},
            headers={"Authorization": f"Token {secret_key}"},
            timeout=15,
        )
        if r.status_code >= 400:
            return None, None  # 404: customer has not opened / paid the link yet
        data = r.json()
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Payment link inquiry failed for {invoice_name}")
        return None, None

    transactions = data if isinstance(data, list) else data.get("results") or [data]
    transactions = [t for t in transactions if isinstance(t, dict) and t.get("id")]
    if not transactions:
        return None, None
    txn = next((t for t in transactions if t.get("success")), transactions[0])
    txn_id = str(txn.get("id") or "")
    if txn.get("success"):
        return "Paid", txn_id
    if txn.get("pending"):
        return "Pending", txn_id
    return "Failed", txn_id


# ---------------------------------------------------------------------------
# Cashier: list + check status
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_payment_links(pos_profile=None, days=7):
    """Invoices held for a payment link (and recently paid ones) for the cashier."""
    since = add_days(now_datetime(), -cint(days or 7))
    filters = {
        "creation": [">=", since],
        "payment_status": ["in", ["Pending", "Failed", "Paid"]],
        "docstatus": ["!=", 2],
        "custom_url": ["is", "set"],
    }
    if pos_profile:
        filters["pos_profile"] = pos_profile
    rows = frappe.get_all(
        "Sales Invoice",
        filters=filters,
        fields=[
            "name", "customer", "customer_name", "grand_total", "rounded_total", "docstatus",
            "payment_status", "custom_url", "creation", "owner",
        ],
        order_by="creation desc",
        limit=200,
    )
    for row in rows:
        row["mobile"] = frappe.db.get_value("Customer", row.customer, "mobile_no")
        payments = frappe.get_all(
            "Sales Invoice Payment",
            filters={"parent": row.name, "mode_of_payment": ["in", [PAYMENT_LINK_MODE, TABBY_MODE]]},
            fields=["mode_of_payment", "amount"],
        )
        row["link_amount"] = flt(sum(flt(p.amount) for p in payments), 2) or flt(row.rounded_total or row.grand_total, 2)
        row["kind"] = "tabby" if any(p.mode_of_payment == TABBY_MODE for p in payments) else "link"
        # Paid + still draft means the submit after payment failed: show it as needing attention.
        row["status"] = "Paid" if row.docstatus == 1 else ("Error" if row.payment_status == "Paid" else row.payment_status)
    return rows


@frappe.whitelist()
def check_payment_link_status(invoice_name):
    """Ask Paymob now; submits the invoice if it has been paid."""
    docstatus, status = frappe.db.get_value("Sales Invoice", invoice_name, ["docstatus", "payment_status"])
    if docstatus == 1:
        return {"status": "Paid", "submitted": True}
    if docstatus == 2:
        return {"status": "Cancelled", "submitted": False}

    result, txn_id = _inquire(invoice_name)
    if result == "Paid" or (status == "Paid" and result is None):
        # Paid (or already marked paid by the webhook but the submit failed): submit now.
        settle_paid_invoice(invoice_name, txn_id, source="cashier check")
        return {"status": "Paid", "submitted": True}
    if result == "Failed":
        _set_status(invoice_name, "Failed", txn_id=txn_id)
        frappe.db.commit()
        return {"status": "Failed", "submitted": False}
    return {"status": status or "Pending", "submitted": False}


def check_pending_payment_links():
    """Scheduler: settle held invoices whose link was paid but the webhook was missed."""
    since = add_days(now_datetime(), -BACKGROUND_CHECK_DAYS)
    names = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": 0, "payment_status": ["in", ["Pending", "Paid"]], "custom_url": ["is", "set"], "creation": [">=", since]},
        pluck="name",
        limit=100,
    )
    for name in names:
        try:
            check_payment_link_status(name)
        except Exception:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), f"Payment link background check failed for {name}")
