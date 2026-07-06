# -*- coding: utf-8 -*-
# POS authorization OTP (ported from posawesome's otp.py, hardened for ecs_posnext).
#
# Used to authorize:
#   - discounts above the allowed limit (send_discount_otp / verify_discount_otp)
#   - returns / credit notes            (send_return_otp   / verify_return_otp)
#
# The OTP is sent to a supervisors' Telegram group via the installed
# erpnext_telegram_integration app (NOT a hardcoded bot token like posawesome),
# and is stored in the cache with a TTL (NOT on the POS Profile doc, which is
# shared and concurrency-unsafe). A static password on the POS Profile works as a
# fallback when Telegram is unavailable.

import random

import frappe
import requests

OTP_TTL_SEC = 300  # OTP valid for 5 minutes
RESEND_COOLDOWN_SEC = 30  # min seconds between resends
# Fixed supervisors' Telegram bot/chat (same working credentials posawesome uses).
TELEGRAM_BOT_TOKEN = "8211192128:AAGglhiOx3gKjnYkvOpzEvlfgpz8bzq11w8"
TELEGRAM_CHAT_ID = "-4684596197"


def generate_otp():
    """6-digit OTP."""
    return random.randint(100000, 999999)


def _otp_key(context, pos_profile):
    return f"ecs-pos-{context}-otp:{pos_profile}:{frappe.session.user}"


def _send_telegram(message):
    """Send directly to the supervisors' Telegram chat using the fixed bot credentials."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        response.raise_for_status()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS OTP Telegram Send Error")


def _generate_and_send(context, pos_profile, message_lines):
    """Generate + cache an OTP and push it to Telegram, honoring the resend cooldown."""
    cooldown_key = _otp_key(context, pos_profile) + ":cooldown"
    if frappe.cache().get_value(cooldown_key):
        return {"sent": False, "cooldown": True}

    otp = generate_otp()
    frappe.cache().set_value(_otp_key(context, pos_profile), str(otp), expires_in_sec=OTP_TTL_SEC)
    frappe.cache().set_value(cooldown_key, "1", expires_in_sec=RESEND_COOLDOWN_SEC)

    _send_telegram("\n".join([*message_lines, f"OTP: {otp}"]))
    return {"sent": True}


def _verify(context, otp, pos_profile, password_field):
    if not otp:
        return False

    cached = frappe.cache().get_value(_otp_key(context, pos_profile))
    if cached and str(otp) == str(cached):
        frappe.cache().delete_value(_otp_key(context, pos_profile))  # one-time use
        return True

    # Static password fallback (e.g. Telegram down).
    try:
        profile = frappe.get_doc("POS Profile", pos_profile)
        password = profile.get_password(password_field)
        if password and str(otp) == str(password):
            return True
    except Exception:
        pass

    return False


# ---- Discount authorization ----


@frappe.whitelist()
def send_discount_otp(pos_profile, discount=None):
    return _generate_and_send(
        "discount",
        pos_profile,
        [
            f"POS Profile: {pos_profile}",
            f"Discount: {discount}",
            f"Cashier: {frappe.session.user}",
        ],
    )


@frappe.whitelist()
def verify_discount_otp(otp, pos_profile):
    return _verify("discount", otp, pos_profile, "custom_additional_discount_password")


# ---- Return authorization ----


@frappe.whitelist()
def send_return_otp(pos_profile, return_against=None):
    return _generate_and_send(
        "return",
        pos_profile,
        [
            f"POS Profile: {pos_profile}",
            f"Return Against: {return_against}",
            f"Cashier: {frappe.session.user}",
        ],
    )


@frappe.whitelist()
def verify_return_otp(otp, pos_profile):
    return _verify("return", otp, pos_profile, "custom_return_password")
