# -*- coding: utf-8 -*-
# POS Ticket redeem + renewal for ecs_posnext.
#
# - search_tickets / redeem_ticket: thin wrappers over posawesome's tested ticket
#   redeem API (posawesome is installed), so the POS only talks to ecs_posnext.
# - renew_ticket: NEW — "recharge" the same Ticket (extend valid_to + add uses) and
#   collect a paid Sales Invoice for the renewal fee.

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, today

from ecs_posnext.api.invoices import submit_invoice, update_invoice
from ecs_posnext.api.reservations import _default_mode_of_payment

RENEWAL_ITEM_CODE = "TICKET-RENEWAL"


def _get_or_create_renewal_item():
    """Dedicated renewal service item (no Ticket Settings → no new ticket generated)."""
    if frappe.db.exists("Item", RENEWAL_ITEM_CODE):
        return RENEWAL_ITEM_CODE

    group = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"
    item = frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": RENEWAL_ITEM_CODE,
            "item_name": "Ticket Renewal",
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
    return RENEWAL_ITEM_CODE


def _resolve_branch(branch, pos_profile):
    """Redeem branch = the POS Profile's Dimension Branch (posawesome convention)."""
    if branch:
        return branch
    if pos_profile:
        return frappe.db.get_value("POS Profile", pos_profile, "dimension_branch")
    return None


# ---------------------------------------------------------------------------
# Redeem (delegates to posawesome's tested implementation)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def search_tickets(search_keys):
    """Search redeemable tickets by redeem_code / customer (delegates to posawesome)."""
    from posawesome.posawesome.api.redeem_ticket import search_redeem_tickets

    return search_redeem_tickets(search_keys)


@frappe.whitelist()
def redeem_ticket(
    ticket_name,
    customer,
    number_of_redeems,
    branch=None,
    pos_profile=None,
    attend_event=None,
    booklet=None,
):
    """Redeem N uses of a ticket (delegates to posawesome — keeps all validations)."""
    from posawesome.posawesome.api.redeem_ticket import redeem_ticket as _redeem

    return _redeem(
        ticket_name=ticket_name,
        customer=customer,
        number_of_redeems=number_of_redeems,
        branch=_resolve_branch(branch, pos_profile),
        attend_event=attend_event,
        booklet=booklet,
    )


# ---------------------------------------------------------------------------
# Renew (recharge the same ticket + paid invoice) — NEW
# ---------------------------------------------------------------------------


@frappe.whitelist()
def renew_ticket(
    ticket_name, added_uses, amount, pos_profile, mode_of_payment=None, extend_days=None
):
    """Recharge the SAME ticket: extend validity + add uses, billed as a paid invoice.

    Steps:
      1. Create + submit a paid POS Sales Invoice for `amount` using a dedicated
         renewal service item (no Ticket Settings, so no new ticket is generated).
      2. On the existing ticket: add `added_uses` to global_maximum_usage and
         remaining_usage, and extend valid_to by (extend_days or the item's
         Ticket Settings number_of_days), measured from the later of today / current
         expiry.
    """
    added_uses = int(added_uses)
    amount = flt(amount)
    if added_uses <= 0:
        frappe.throw(_("Added uses must be greater than zero"))
    if amount <= 0:
        frappe.throw(_("Renewal amount must be greater than zero"))
    if not pos_profile:
        frappe.throw(_("POS Profile is required"))

    ticket = frappe.get_doc("Ticket", ticket_name)
    pos_profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)

    # 1) Paid renewal invoice. Bill the ticket's OWN item so the sale reports
    #    against the real product, and flag custom_is_wordpress = 1 so the Sales
    #    Invoice submit trigger skips generating a brand-new ticket.
    item_code = ticket.item or _get_or_create_renewal_item()
    invoice_data = {
        "doctype": "Sales Invoice",
        "pos_profile": pos_profile,
        "customer": ticket.vendor,
        "is_pos": 1,
        "update_stock": 0,
        "custom_is_wordpress": 1,
        "items": [{"item_code": item_code, "qty": 1, "rate": amount}],
        "payments": [
            {
                "mode_of_payment": mode_of_payment
                or _default_mode_of_payment(pos_profile_doc),
                "amount": amount,
            }
        ],
        "remarks": _("Ticket renewal for {0}").format(ticket_name),
    }
    draft = update_invoice(invoice_data)
    invoice_data["name"] = draft.get("name")
    submit_invoice(invoice=invoice_data, data={})

    # 2) Recharge the ticket (controller does not recompute these on save).
    ticket.global_maximum_usage = (ticket.global_maximum_usage or 0) + added_uses
    ticket.remaining_usage = (ticket.remaining_usage or 0) + added_uses

    days = None
    if extend_days:
        days = int(extend_days)
    elif ticket.ticket_settings:
        days = frappe.db.get_value(
            "Ticket Settings", ticket.ticket_settings, "number_of_days"
        )
    # Renewal restarts the validity window today and extends valid_to by `days`
    # from the later of today / current expiry (so an active ticket is topped up,
    # an expired one is revived from today).
    today_date = getdate(today())
    ticket.valid_from = today_date
    if days:
        base = today_date
        if ticket.valid_to and getdate(ticket.valid_to) > base:
            base = getdate(ticket.valid_to)
        ticket.valid_to = add_days(base, int(days))

    # Keep a history of every invoice raised against this ticket.
    ticket.append(
        "sales_invoices",
        {
            "sales_invoice": draft.get("name"),
            "type": "Renewal",
            "amount": amount,
            "added_uses": added_uses,
        },
    )

    ticket.flags.ignore_permissions = True
    ticket.save(ignore_permissions=True)
    ticket.add_comment(
        "Comment",
        _("Renewed: +{0} uses, valid to {1} (invoice {2})").format(
            added_uses, ticket.valid_to, draft.get("name")
        ),
    )
    frappe.db.commit()

    return {
        "ticket": ticket_name,
        "renewal_invoice": draft.get("name"),
        "valid_to": str(ticket.valid_to),
        "global_maximum_usage": ticket.global_maximum_usage,
        "remaining_usage": ticket.remaining_usage,
    }
