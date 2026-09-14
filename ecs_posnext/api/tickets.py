# -*- coding: utf-8 -*-
# POS Ticket redeem + renewal for ecs_posnext.
#
# - search_tickets / redeem_ticket: thin wrappers over posawesome's tested ticket
#   redeem API (posawesome is installed), so the POS only talks to ecs_posnext.
# - renew_ticket: NEW — "recharge" the same Ticket (extend valid_to + add uses) and
#   collect a paid Sales Invoice for the renewal fee.

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, today

from ecs_posnext.api.invoices import _submit_invoice_sync, update_invoice
from ecs_posnext.api.reservations import _default_mode_of_payment

RENEWAL_ITEM_CODE = "TICKET-RENEWAL"

# Membership/subscription items eligible for the "Upgrade" action on the
# Ticket Redeem & Renewal dialog.
SUBSCRIPTION_ITEM_CODES = [
    "DAZ 1 Month Membership",
    "DAZ 3 Months Membership",
    "DAZ 6 Months Membership",
    "DAZ 1 Year Membership",
]


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

    return search_redeem_tickets(search_keys, include_expired=1)


@frappe.whitelist()
def get_customer_membership(customer=None):
    """Active membership summary for a customer, for the POS customer badge.

    A ticket counts as an active membership when: vendor == customer,
    valid_to >= today, remaining_usage > 0, and its item is a Subscription
    item (Item.custom_item_type == "Subscription").
    """
    if not customer:
        return {"count": 0, "tickets": []}

    subscription_items = frappe.db.get_all(
        "Item", filters={"custom_item_type": "Subscription"}, pluck="name"
    )
    if not subscription_items:
        return {"count": 0, "tickets": []}

    tickets = frappe.db.get_all(
        "Ticket",
        filters={
            "vendor": customer,
            "valid_to": [">=", today()],
            "remaining_usage": [">", 0],
            "item": ["in", subscription_items],
        },
        fields=["name", "item", "valid_to", "remaining_usage", "global_maximum_usage"],
        order_by="valid_to asc",
    )
    return {"count": len(tickets), "tickets": tickets}


def _get_wristband_item_code(ticket):
    """POS Global Settings.wristband_item, falling back to the ticket's own item."""
    item_code = frappe.db.get_single_value("POS Global Settings", "wristband_item")
    return item_code or ticket.item


def _get_wristband_price_list_rate(item_code, pos_profile_doc):
    """Selling price for the wristband item; falls back to the item's standard rate."""
    price_list = pos_profile_doc.get("selling_price_list") if pos_profile_doc else None
    rate = None
    if price_list:
        rate = frappe.db.get_value(
            "Item Price",
            {"item_code": item_code, "price_list": price_list},
            "price_list_rate",
        )
    if rate is None:
        rate = frappe.db.get_value("Item", item_code, "standard_rate") or 0
    return flt(rate)


@frappe.whitelist()
def give_free_wristband(
    ticket_name,
    pos_profile,
    mode_of_payment=None,
    pos_opening_shift=None,
):
    """Give one free wristband on a ticket: a zero-value (100% discount) POS invoice
    for the wristband item, plus counter updates on the ticket.

    Steps:
      1. Create + submit a POS Sales Invoice with the wristband item at its normal
         price but a 100% discount (rate 0), so the giveaway is a real, auditable
         invoice rather than a silent counter bump. custom_is_wordpress = 1 so the
         Sales Invoice submit trigger doesn't try to generate a new ticket.
      2. On the ticket: increment used_free_wristband / decrement remaining_free_wristband.
    """
    if not pos_profile:
        frappe.throw(_("POS Profile is required"))

    ticket = frappe.get_doc("Ticket", ticket_name)
    if ticket.get("is_frozen"):
        reason = ticket.get("frozen_reason")
        frappe.throw(_("This ticket is frozen") + (f": {reason}" if reason else ""))
    if cint(ticket.remaining_free_wristband) <= 0:
        frappe.throw(_("This ticket has no remaining free wristband"))

    item_code = _get_wristband_item_code(ticket)
    if not item_code:
        frappe.throw(
            _(
                "No Wristband Item is set in POS Global Settings, and this ticket has no item to fall back to"
            )
        )

    pos_profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
    price_list_rate = _get_wristband_price_list_rate(item_code, pos_profile_doc)

    invoice_data = {
        "doctype": "Sales Invoice",
        "pos_profile": pos_profile,
        "customer": ticket.vendor,
        "is_pos": 1,
        "update_stock": 0,
        "custom_is_wordpress": 1,
        "posa_pos_opening_shift": pos_opening_shift,
        "items": [
            {
                "item_code": item_code,
                "qty": 1,
                "price_list_rate": price_list_rate,
                "discount_percentage": 100,
                "rate": 0,
                # Rate is genuinely 0 after the 100% discount — if the item is a stock
                # item with no valuation rate, ERPNext otherwise refuses to post the
                # accounting entries ("Valuation Rate ... is required").
                "allow_zero_valuation_rate": 1,
            }
        ],
        "payments": [
            {
                "mode_of_payment": mode_of_payment
                or _default_mode_of_payment(pos_profile_doc),
                "amount": 0,
            }
        ],
        "remarks": _("Free wristband for ticket {0}").format(ticket_name),
    }
    draft = update_invoice(invoice_data)
    invoice_data["name"] = draft.get("name")
    _submit_invoice_sync(invoice=invoice_data, data={})

    ticket.used_free_wristband = cint(ticket.used_free_wristband) + 1
    ticket.remaining_free_wristband = max(
        cint(ticket.maximum_free_wristband) - cint(ticket.used_free_wristband), 0
    )
    ticket.append(
        "sales_invoices",
        {
            "sales_invoice": draft.get("name"),
            "type": "Wristband",
            "amount": 0,
        },
    )

    ticket.flags.ignore_permissions = True
    ticket.save(ignore_permissions=True)
    ticket.add_comment(
        "Comment",
        _("Free wristband given (invoice {0})").format(draft.get("name")),
    )
    frappe.db.commit()

    return {
        "ticket": ticket_name,
        "wristband_invoice": draft.get("name"),
        "used_free_wristband": ticket.used_free_wristband,
        "remaining_free_wristband": ticket.remaining_free_wristband,
    }


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
    ticket_name,
    added_uses,
    amount,
    pos_profile,
    mode_of_payment=None,
    extend_days=None,
    pos_opening_shift=None,
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
    if ticket.get("is_frozen"):
        reason = ticket.get("frozen_reason")
        frappe.throw(_("This ticket is frozen and cannot be renewed") + (f": {reason}" if reason else ""))

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
        "posa_pos_opening_shift": pos_opening_shift,
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
    _submit_invoice_sync(invoice=invoice_data, data={})

    # 2) Recharge the ticket (controller does not recompute these on save).
    ticket.global_maximum_usage = (ticket.global_maximum_usage or 0) + added_uses

    # Renewal restarts the ticket's usage: current usage is cleared and the
    # full (new) maximum becomes available again.
    ticket.current_usage = 0
    ticket.remaining_usage = ticket.global_maximum_usage

    ticket.used_free_wristband = 0
    ticket.remaining_free_wristband = cint(ticket.maximum_free_wristband)

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
        "current_usage": ticket.current_usage,
        "remaining_usage": ticket.remaining_usage,
        "used_free_wristband": ticket.used_free_wristband,
        "remaining_free_wristband": ticket.remaining_free_wristband,
    }


# ---------------------------------------------------------------------------
# Upgrade (buy a new membership subscription for the ticket's customer) — NEW
# ---------------------------------------------------------------------------


def _get_subscription_item_rate(item_code, pos_profile):
    """Selling price for a membership item, taken from Item Price.

    The POS Profile's selling price list decides which Item Price applies, and
    the price is the one effective today: rows dated in the future or already
    expired are skipped, and the newest still-valid row wins (an item commonly
    carries several Item Price rows with different valid_from dates, so picking
    one arbitrarily would bill last season's price).

    Falls back to the item's standard rate when the price list has no row.
    """
    price_list = (
        frappe.db.get_value("POS Profile", pos_profile, "selling_price_list")
        if pos_profile
        else None
    )
    rate = None
    if price_list:
        rows = frappe.db.sql(
            """
            SELECT price_list_rate
            FROM `tabItem Price`
            WHERE item_code = %(item_code)s
              AND price_list = %(price_list)s
              AND selling = 1
              AND (valid_from IS NULL OR valid_from <= %(today)s)
              AND (valid_upto IS NULL OR valid_upto >= %(today)s)
            ORDER BY valid_from DESC, modified DESC
            LIMIT 1
            """,
            {"item_code": item_code, "price_list": price_list, "today": today()},
        )
        if rows:
            rate = rows[0][0]
    if rate is None:
        rate = frappe.db.get_value("Item", item_code, "standard_rate") or 0
    return flt(rate)


def _create_pos_upgrade_invoice(
    subscription, item_code, rate, pos_profile, mode_of_payment, pos_opening_shift, ticket_name
):
    """Bill an upgrade as a normal paid POS invoice and link it to the subscription.

    The subscription's own invoice path (Daz Yearly Subscription.on_submit →
    _bg_create_invoice_and_email) is the ONLINE one: no POS Profile, branch
    hardcoded to Head Office, paid by Paymob. An upgrade sold at the till has to
    land in the cashier's till instead, so it is billed here with the POS
    Profile and POS Opening Shift the cashier is working on, and the online
    invoice is suppressed (skip_invoice_creation flag) by the caller.

    custom_is_wordpress = 1 so the Sales Invoice submit trigger doesn't generate
    a second set of tickets — the subscription already created them.
    """
    pos_profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
    item = frappe.get_cached_doc("Item", item_code)

    invoice_data = {
        "doctype": "Sales Invoice",
        "pos_profile": pos_profile,
        "customer": subscription.customer,
        "is_pos": 1,
        "update_stock": 0,
        "custom_is_wordpress": 1,
        "posa_pos_opening_shift": pos_opening_shift,
        "items": [
            {
                "item_code": item_code,
                "item_name": item.item_name,
                "qty": 1,
                "uom": "Ticket",
                "conversion_factor": 1,
                "price_list_rate": rate,
                "rate": rate,
            }
        ],
        "payments": [
            {
                "mode_of_payment": mode_of_payment
                or _default_mode_of_payment(pos_profile_doc),
                "amount": rate,
            }
        ],
        "remarks": _("Subscription upgrade for ticket {0}").format(ticket_name),
    }
    draft = update_invoice(invoice_data)
    invoice_name = draft.get("name")
    invoice_data["name"] = invoice_name

    # Collect exactly what the invoice ended up totalling (the POS Profile's tax
    # template can add exclusive VAT on top of the Item Price), otherwise the
    # sale submits with an outstanding balance the cashier never sees.
    grand_total = flt(draft.get("grand_total"))
    if grand_total:
        invoice_data["payments"][0]["amount"] = grand_total

    _submit_invoice_sync(invoice=invoice_data, data={})

    frappe.db.set_value(
        "Daz Yearly Subscription", subscription.name, "sales_invoice", invoice_name
    )
    for tname in (
        frappe.db.get_all("Ticket Chiled", filters={"parent": subscription.name}, pluck="ticket")
        or []
    ):
        frappe.db.set_value(
            "Ticket", tname, "sales_invoice", invoice_name, update_modified=False
        )
    frappe.db.commit()

    return invoice_name


@frappe.whitelist()
def upgrade_ticket_subscription(
    ticket_name,
    item_code,
    pos_profile=None,
    mode_of_payment=None,
    pos_opening_shift=None,
):
    """Upgrade a subscription ticket to a different membership plan.

    Only available for tickets whose item is one of SUBSCRIPTION_ITEM_CODES.
    Creates + submits a "Daz Yearly Subscription" for the ticket's customer
    with the chosen plan; submitting it is what creates the new Ticket(s)
    (Daz Yearly Subscription.on_submit).

    Sold from a POS Profile, the upgrade is billed here as a paid POS Sales
    Invoice carrying that profile and the cashier's POS Opening Shift, priced
    from the profile's Item Price. Without a POS Profile (online flow) the
    subscription's own background job creates the Paymob invoice as before.
    """
    if item_code not in SUBSCRIPTION_ITEM_CODES:
        frappe.throw(_("{0} is not a valid subscription plan").format(item_code))

    ticket = frappe.get_doc("Ticket", ticket_name)
    if ticket.item not in SUBSCRIPTION_ITEM_CODES:
        frappe.throw(_("This ticket is not a subscription ticket and cannot be upgraded"))
    if not ticket.vendor:
        frappe.throw(_("This ticket has no customer to upgrade"))

    item = frappe.get_cached_doc("Item", item_code)
    rate = _get_subscription_item_rate(item_code, pos_profile)
    company = frappe.db.get_value("POS Profile", pos_profile, "company") if pos_profile else None
    company = company or frappe.defaults.get_global_default("company")

    subscription = frappe.new_doc("Daz Yearly Subscription")
    subscription.customer = ticket.vendor
    subscription.company = company
    subscription.append(
        "items",
        {
            "item_code": item_code,
            "item_name": item.item_name,
            "description": item.item_name,
            "qty": 1,
            "uom": "Ticket",
            "conversion_factor": 1,
            "rate": rate,
        },
    )
    subscription.flags.ignore_permissions = True
    # Billed at the till below — don't also raise the online Paymob invoice.
    if pos_profile:
        subscription.flags.skip_invoice_creation = True
    subscription.insert(ignore_permissions=True)
    subscription.submit()
    frappe.db.commit()

    new_ticket = frappe.db.get_value("Ticket Chiled", {"parent": subscription.name}, "ticket")

    invoice_name = None
    if pos_profile:
        invoice_name = _create_pos_upgrade_invoice(
            subscription,
            item_code,
            rate,
            pos_profile,
            mode_of_payment,
            pos_opening_shift,
            ticket_name,
        )

    return {
        "subscription": subscription.name,
        "new_ticket": new_ticket,
        "invoice": invoice_name,
        "rate": rate,
    }
