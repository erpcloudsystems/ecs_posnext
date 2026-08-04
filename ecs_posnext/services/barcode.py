"""
Barcode resolver service for POS Next.

This module provides an optional integration with the barcode_resolver app.
When barcode_resolver is installed, it enables advanced barcode parsing
for weighted and priced barcodes. When not installed, it gracefully
returns None.

Usage:
    from ecs_posnext.services import resolve_barcode, is_barcode_resolver_available

    # Check if feature is available
    if is_barcode_resolver_available():
        result = resolve_barcode("2001234001234")
        if result:
            print(result["item_barcode"], result["qty"])

    # Or simply call resolve_barcode (returns None if app not installed)
    result = resolve_barcode("2001234001234")
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, TypedDict

import frappe
from erpnext.stock.get_item_details import get_conversion_factor


class BarcodeResult(TypedDict, total=False):
    """Type definition for barcode resolution result."""

    item_barcode: str  # The barcode from Item Barcodes table
    integer_value: str  # Integer part of the encoded value
    decimal_value: str  # Decimal part of the encoded value
    barcode_type: str  # "Weighted" or "Priced"
    uom: str | None  # UOM from Item Barcodes table
    qty: float | None  # Quantity (only for weighted barcodes)


class ResolvedItemData(TypedDict, total=False):
    """Type definition for resolved item data to be applied to cart."""

    resolved_qty: float | None
    resolved_uom: str | None
    resolved_price: float | None
    resolved_barcode_type: str | None


@lru_cache(maxsize=1)
def is_barcode_resolver_available() -> bool:
    """
    Check if the barcode_resolver app is installed.

    Returns:
        bool: True if barcode_resolver is available, False otherwise.

    Note:
        Result is cached for performance. Server restart clears the cache.
    """
    return "barcode_resolver" in frappe.get_installed_apps()


# Weighing-scale (weight-embedded EAN-13) barcode layout:
# [2-digit prefix][5-digit item code][5-digit weight, kg with 3 decimals][1 check digit]
SCALE_BARCODE_LENGTH = 13
SCALE_ITEM_CODE_DIGITS = 5
SCALE_WEIGHT_DIGITS = 5
DEFAULT_SCALE_BARCODE_PREFIXES = ["20"]


def _ean13_check_digit(digits: str) -> int:
    """Compute the EAN-13 check digit from the first 12 digits of an EAN-13 string."""
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits[:12]))
    return (10 - (total % 10)) % 10


def _find_item_barcode_by_code(item_code_digits: str) -> str | None:
    """Match a scale barcode's embedded numeric item code to an existing Item Barcode/Item."""
    candidates = {item_code_digits, str(int(item_code_digits))}

    for candidate in candidates:
        barcode = frappe.db.get_value("Item Barcode", {"barcode": candidate}, "barcode")
        if barcode:
            return barcode

    for candidate in candidates:
        if frappe.db.exists("Item", candidate):
            return candidate

    return None


def decode_scale_barcode(barcode: str, pos_settings=None) -> BarcodeResult | None:
    """
    Decode an in-house weighing-scale barcode.

    The scale prints a 13-digit weight-embedded EAN-13: a 2-digit prefix
    (reserved GS1 in-store range, default 20-29), the item's 5-digit code,
    a 5-digit weight in kg (3 decimal places, e.g. "01250" -> 1.250 kg),
    and a real EAN-13 check digit.

    Returns None when the barcode isn't a match (wrong length/prefix/checksum)
    or the embedded code doesn't resolve to a known item — in which case it's
    treated as a normal product barcode instead.
    """
    if not barcode or len(barcode) != SCALE_BARCODE_LENGTH or not barcode.isdigit():
        return None

    prefixes = DEFAULT_SCALE_BARCODE_PREFIXES
    if pos_settings is not None:
        if not pos_settings.get("enable_scale_barcode", 1):
            return None
        configured = (pos_settings.get("scale_barcode_prefixes") or "").strip()
        if configured:
            prefixes = [p.strip() for p in configured.split(",") if p.strip()]

    if barcode[:2] not in prefixes:
        return None

    if _ean13_check_digit(barcode) != int(barcode[-1]):
        return None

    item_code_digits = barcode[2 : 2 + SCALE_ITEM_CODE_DIGITS]
    weight_digits = barcode[2 + SCALE_ITEM_CODE_DIGITS : 2 + SCALE_ITEM_CODE_DIGITS + SCALE_WEIGHT_DIGITS]

    item_barcode = _find_item_barcode_by_code(item_code_digits)
    if not item_barcode:
        return None

    weight_value = int(weight_digits)
    return {
        "item_barcode": item_barcode,
        "integer_value": str(weight_value // 1000),
        "decimal_value": f"{weight_value % 1000:03d}",
        "barcode_type": "Weighted",
        "uom": None,
    }


def resolve_barcode(barcode: str, pos_profile: str) -> BarcodeResult | None:
    """
    Resolve a barcode to weighted/priced item data.

    Tries the optional barcode_resolver app first (if installed, for
    custom/configurable rules), then falls back to this app's built-in
    weighing-scale barcode decoder.

    Args:
        barcode: The barcode string to resolve.

    Returns:
        BarcodeResult dict if the barcode matches a rule, None otherwise.

    Example:
        >>> result = resolve_barcode("2001234001500")
        >>> if result:
        ...     print(f"Item: {result['item_barcode']}, Qty: {result['qty']}")
    """
    pos_settings = None
    try:
        pos_settings = frappe.get_doc("POS Settings", {"pos_profile": pos_profile})
    except frappe.DoesNotExistError:
        pass

    if is_barcode_resolver_available():
        try:
            from barcode_resolver.barcode_resolver.doctype.barcode_rule.utils import (
                resolve_barcode as _resolve_barcode,
            )
            barcode_rules = [
                rule.barcode_rule for rule in (pos_settings.barcode_rules if pos_settings else []) if not rule.disable
            ]
            result = _resolve_barcode(barcode, barcode_rules)
            if result:
                return result
        except ImportError:
            # App might have been uninstalled, clear cache and fall through to built-in decoder
            is_barcode_resolver_available.cache_clear()
        except Exception:
            # Log unexpected errors but don't break POS functionality
            frappe.log_error(
                title="Barcode Resolver Error",
                message=f"Error resolving barcode: {barcode}",
            )

    return decode_scale_barcode(barcode, pos_settings=pos_settings)


def compute_resolved_item_data(
    resolved_barcode: BarcodeResult | None,
    item,
) -> ResolvedItemData | None:
    """
    Compute qty and uom from resolved barcode data.

    For weighted barcodes: uses qty directly from the barcode.
    For priced barcodes: computes qty = encoded_price / item_rate.

    Args:
        resolved_barcode: The result from resolve_barcode().
        item_rate: The item's unit price (required for priced barcodes).

    Returns:
        ResolvedItemData with resolved_qty, resolved_uom, and resolved_barcode_type,
        or None if no valid resolution.

    Example:
        >>> resolved = resolve_barcode("2001234001500")
        >>> if resolved:
        ...     item_data = compute_resolved_item_data(resolved, item_rate=10.0)
        ...     print(f"Qty: {item_data['resolved_qty']}, UOM: {item_data['resolved_uom']}")
    """
    if not resolved_barcode:
        return None

    barcode_type = resolved_barcode.get("barcode_type")
    barcode_uom = resolved_barcode.get("uom")
    # If barcode resolver didn't provide a UOM, fall back to item's stock UOM
    if not barcode_uom:
        barcode_uom = item.get("uom")
    uom_prices = item.get("uom_prices", {})
    barcode_uom_price = uom_prices.get(barcode_uom)
    item_uom = item.get("uom")
    item_price = item.get("rate")
    item_name = item.get("item_code")
    if item_name is None:
        frappe.log_error(
            title="Barcode Resolver Error",
            message=f"Item code is missing in item data: {item}",
        )
        return None

    integer_value = resolved_barcode.get("integer_value", "0")
    decimal_value = resolved_barcode.get("decimal_value", "0")
    if barcode_type == "Weighted":
        qty = float(f"{integer_value}.{decimal_value}")
        uom = barcode_uom
        price = barcode_uom_price
        if barcode_uom not in uom_prices:
            conversion_factor = get_conversion_factor(item_name, barcode_uom).get("conversion_factor", 1)
            qty *= conversion_factor
            uom = item_uom
            price = item_price

        return {
            "resolved_qty": qty,
            "resolved_uom": uom,
            "resolved_price": price,
            "resolved_barcode_type": barcode_type,
        }
    elif barcode_type == "Priced":
        encoded_price = float(f"{integer_value}.{decimal_value}")
        if barcode_uom in uom_prices:
            barcode_uom_price = uom_prices.get(barcode_uom)
            price = barcode_uom_price
            uom = barcode_uom
            qty = encoded_price / price if price and price > 0 else None
        else:
            conversion_factor = get_conversion_factor(item_name, barcode_uom).get("conversion_factor", 1)
            uom = barcode_uom
            price = conversion_factor * item_price
            # Add the calculated price as this barcode_uom price
            uom_prices[barcode_uom] = price
            qty = encoded_price / price if price and price > 0 else None
        return {
            "resolved_qty": qty,
            "resolved_uom": uom,
            "resolved_price": encoded_price,
            "resolved_barcode_type": barcode_type,
        }

    return None
