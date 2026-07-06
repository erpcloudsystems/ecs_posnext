# -*- coding: utf-8 -*-
# POS bridge to the loyalty_engine app (points + cashback wallet).
#
# Earning is handled automatically by loyalty_engine's global Sales Invoice hooks.
# Redemption is driven by two custom fields the POS sets on the Sales Invoice:
#   custom_loyalty_points_to_redeem (points)  and  custom_cashback_to_use (currency).
# loyalty_engine then posts the redeemed value as a payment line (under the configured
# default mode of payment) and debits the wallet FIFO on submit.
#
# This module only EXPOSES wallet balance + settings to the POS; it does not
# duplicate any loyalty business logic.

import frappe
from frappe.utils import flt


def _nearest_expiry(customer, reward_type, remaining_field):
    """Return (amount, date) of the soonest-expiring, still-available earn entries."""
    rows = frappe.db.get_all(
        "Loyalty Ledger Entry",
        filters={
            "customer": customer,
            "reward_type": reward_type,
            "entry_type": "Earn",
            "is_expired": 0,
            remaining_field: [">", 0],
            "expiry_date": ["is", "set"],
        },
        fields=["expiry_date", remaining_field],
        order_by="expiry_date asc",
    )
    if not rows:
        return (0.0, None)
    earliest = rows[0]["expiry_date"]
    amount = sum(flt(r[remaining_field]) for r in rows if r["expiry_date"] == earliest)
    return (flt(amount), earliest)


@frappe.whitelist()
def get_loyalty_info(customer=None):
    """Return the customer's wallet balance plus the loyalty settings the POS needs.

    Always returns a dict with `enabled`; when disabled or no customer, balances are 0.
    """
    settings = frappe.get_cached_doc("Loyalty Program Settings")
    enabled = bool(settings.get("enabled"))

    info = {
        "enabled": enabled,
        "points_exchange_rate": flt(settings.get("points_exchange_rate")) or 1.0,
        "max_points_redemption_percent": flt(settings.get("max_points_redemption_percent")) or 100.0,
        "max_cashback_usage_percent": flt(settings.get("max_cashback_usage_percent")) or 100.0,
        "default_mode_of_payment": settings.get("default_mode_of_payments"),
        "available_points": 0.0,
        "available_points_value": 0.0,
        "available_cashback": 0.0,
        "points_expiry_date": None,
        "cashback_expiry_date": None,
    }

    if not enabled or not customer:
        return info

    try:
        from loyalty_engine.apis.customer_wallet import get_customer_wallet

        wallet = get_customer_wallet(customer) or {}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS get_loyalty_info")
        return info

    rate = info["points_exchange_rate"]
    # loyalty_engine returns available_points already multiplied by the exchange rate
    # (i.e. a currency value); expose both the raw points and the currency value.
    points_value = flt(wallet.get("available_points"))
    points_expiring, points_expiry_date = _nearest_expiry(customer, "Points", "remaining_points")
    cashback_expiring, cashback_expiry_date = _nearest_expiry(
        customer, "Cashback", "remaining_cashback"
    )
    info.update(
        {
            "available_points_value": points_value,
            "available_points": flt(points_value / rate) if rate else points_value,
            "available_cashback": flt(wallet.get("available_cashback")),
            "customer_category": wallet.get("customer_category"),
            "visits": wallet.get("customer_total_visits"),
            "mobile_no": frappe.db.get_value("Customer", customer, "mobile_no"),
            # Soonest-expiring amounts (for the "some of your points expire on …" note).
            "points_expiring": points_expiring,
            "points_expiry_date": points_expiry_date or wallet.get("points_expiry_date"),
            "cashback_expiring": cashback_expiring,
            "cashback_expiry_date": cashback_expiry_date or wallet.get("cashback_expiry_date"),
        }
    )
    return info
