# -*- coding: utf-8 -*-
"""Per-user custom order of the POS item grid and item group tabs.

Stored per (user, POS Profile) as a user default (tabDefaultValue, parent = user),
so no new doctype / migrate is needed.

Layout shape:
    {
        "groups": ["Group A", "Group B", ...],          # order of the group tabs
        "items": {
            "__all__": ["ITEM-1", "ITEM-2", ...],       # "All Items" tab
            "<item group>": ["ITEM-3", ...],             # one list per group tab
        },
    }
Anything not listed keeps its normal position after the listed entries.
"""

import json

import frappe
from frappe import _

MAX_GROUPS = 500
MAX_ITEM_LISTS = 500
MAX_ITEMS_PER_LIST = 2000
MAX_NAME_LEN = 140


def _key(pos_profile):
    return f"ecs_posnext_layout::{pos_profile}"


def _empty():
    return {"groups": [], "items": {}}


def _clean_names(values, limit):
    out, seen = [], set()
    for v in values or []:
        if not isinstance(v, str):
            continue
        v = v.strip()[:MAX_NAME_LEN]
        if v and v not in seen:
            seen.add(v)
            out.append(v)
        if len(out) >= limit:
            break
    return out


def _normalize(layout):
    if isinstance(layout, str):
        try:
            layout = json.loads(layout)
        except Exception:
            return _empty()
    if not isinstance(layout, dict):
        return _empty()
    items = layout.get("items") if isinstance(layout.get("items"), dict) else {}
    clean_items = {}
    for k, v in list(items.items())[:MAX_ITEM_LISTS]:
        if isinstance(k, str) and k.strip():
            lst = _clean_names(v, MAX_ITEMS_PER_LIST)
            if lst:
                clean_items[k.strip()[:MAX_NAME_LEN]] = lst
    return {"groups": _clean_names(layout.get("groups"), MAX_GROUPS), "items": clean_items}


def _check_profile(pos_profile):
    if not pos_profile or not frappe.db.exists("POS Profile", pos_profile):
        frappe.throw(_("POS Profile {0} not found").format(pos_profile))


@frappe.whitelist()
def get_pos_layout(pos_profile):
    """The current user's saved order for this POS Profile."""
    _check_profile(pos_profile)
    raw = frappe.defaults.get_user_default(_key(pos_profile))
    return _normalize(raw) if raw else _empty()


@frappe.whitelist(methods=["POST"])
def save_pos_layout(pos_profile, layout):
    """Save the current user's order for this POS Profile (replaces the previous one)."""
    _check_profile(pos_profile)
    clean = _normalize(layout)
    frappe.defaults.set_user_default(_key(pos_profile), json.dumps(clean, separators=(",", ":")))
    return clean


@frappe.whitelist(methods=["POST"])
def reset_pos_layout(pos_profile):
    """Forget the current user's order for this POS Profile."""
    _check_profile(pos_profile)
    frappe.defaults.clear_user_default(_key(pos_profile))
    return _empty()
