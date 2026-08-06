# -*- coding: utf-8 -*-
# Copyright (c) 2025, BrainWise and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe import _
from frappe.utils import flt, cint, nowdate, nowtime, get_datetime, cstr
from erpnext.stock.doctype.batch.batch import get_batch_qty, get_batch_no
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from ecs_posnext.api.offers import AllowedBranchFetcher, is_offer_allowed_for_branch


# ==========================================
# Constants for field names (avoid typos and enable refactoring)
# ==========================================
FIELD_IS_RATE_MANUALLY_EDITED = "is_rate_manually_edited"
FIELD_ORIGINAL_RATE = "original_rate"
FIELD_PRICE_LIST_RATE = "price_list_rate"
FIELD_RATE = "rate"
FIELD_ITEM_CODE = "item_code"
FIELD_DISCOUNT_PERCENTAGE = "discount_percentage"
FIELD_ALLOW_USER_TO_EDIT_RATE = "allow_user_to_edit_rate"
FIELD_MAX_DISCOUNT_ALLOWED = "max_discount_allowed"
FIELD_DISABLE_ROUNDED_TOTAL = "disable_rounded_total"
FIELD_ALLOW_NEGATIVE_STOCK = "allow_negative_stock"

# Doctypes
DOCTYPE_SALES_INVOICE = "Sales Invoice"
DOCTYPE_POS_SETTINGS = "POS Settings"
DOCTYPE_POS_PROFILE = "POS Profile"
DOCTYPE_COMMENT = "Comment"


try:
    from erpnext.accounts.doctype.pricing_rule.pricing_rule import (
        apply_pricing_rule as erpnext_apply_pricing_rule,
    )
    from erpnext.accounts.doctype.pricing_rule.utils import (
        get_applied_pricing_rules as erpnext_get_applied_pricing_rules,
    )
except Exception:  # pragma: no cover - ERPNext not installed in some environments
    erpnext_apply_pricing_rule = None
    erpnext_get_applied_pricing_rules = None


# ==========================================
# Helper Functions
# ==========================================


def calculate_price_list_rate(item_rate, discount_pct, current_price_list_rate):
    """
    Calculate price_list_rate from discounted rate and discount percentage.

    Formula: rate = price_list_rate * (1 - discount_percentage/100)
    Reverse: price_list_rate = rate / (1 - discount_percentage/100)

    Args:
        item_rate: The current item rate (after discount)
        discount_pct: The discount percentage (0-100)
        current_price_list_rate: The existing price_list_rate if any

    Returns:
        float: The calculated price_list_rate
    """
    # Early exit: no discount applied
    if discount_pct <= 0 or discount_pct >= 100:
        return current_price_list_rate if current_price_list_rate else item_rate

    # Reverse-calculate price_list_rate from discounted rate
    if item_rate > 0:
        discount_multiplier = 1 - discount_pct / 100
        return item_rate / discount_multiplier

    return current_price_list_rate if current_price_list_rate else item_rate


def validate_manual_rate_edit(item, pos_profile=None, pos_settings_cache=None):
    """
    Validate manually edited item rates against POS Settings business rules.

    This function enforces:
    1. Rate must be positive
    2. Rate editing must be enabled in POS Settings
    3. Rate reduction must not exceed max_discount_allowed (if configured)

    Args:
        item: The item dict/object with rate information. Must contain:
            - is_rate_manually_edited: Flag indicating manual edit (1 or 0)
            - item_code: The item code for error messages
            - rate: The edited rate
            - original_rate or price_list_rate: The original catalog price
        pos_profile: POS Profile name for settings lookup. Required for manual edits.
        pos_settings_cache: Optional pre-fetched POS Settings dict to avoid repeated DB queries.
            Should contain: allow_user_to_edit_rate, max_discount_allowed

    Returns:
        dict with 'valid' boolean and 'message' string if invalid
    """
    is_manual_edit = cint(item.get(FIELD_IS_RATE_MANUALLY_EDITED) or 0)

    # Skip validation if not a manual edit
    if not is_manual_edit:
        return {"valid": True}

    item_code = item.get(FIELD_ITEM_CODE)
    item_rate = flt(item.get(FIELD_RATE) or 0)
    original_rate = flt(item.get(FIELD_ORIGINAL_RATE) or item.get(FIELD_PRICE_LIST_RATE) or 0)

    # Validate rate is positive
    if item_rate <= 0:
        return {
            "valid": False,
            "message": _("Rate for item {0} must be greater than zero").format(item_code)
        }

    # POS Profile is required for manual rate edit validation
    if not pos_profile:
        return {
            "valid": False,
            "message": _("POS Profile is required to validate rate edit for item {0}").format(item_code)
        }

    # Use cached POS Settings if provided, otherwise fetch from DB
    pos_settings = pos_settings_cache
    if pos_settings is None:
        pos_settings = frappe.db.get_value(
            DOCTYPE_POS_SETTINGS,
            {"pos_profile": pos_profile},
            [FIELD_ALLOW_USER_TO_EDIT_RATE, FIELD_MAX_DISCOUNT_ALLOWED],
            as_dict=True
        )

    # Check if POS Settings exists
    if not pos_settings:
        return {
            "valid": False,
            "message": _("POS Settings not found for profile {0}. Cannot validate rate edit.").format(pos_profile)
        }

    # Check if rate editing is allowed (global setting OR item-level flag)
    global_rate_edit_allowed = cint(pos_settings.get(FIELD_ALLOW_USER_TO_EDIT_RATE))
    item_rate_edit_allowed = cint(
        frappe.db.get_value("Item", item_code, "custom_allow_rate_edit")
    ) if item_code else 0

    if not global_rate_edit_allowed and not item_rate_edit_allowed:
        return {
            "valid": False,
            "message": _("Rate editing is not allowed for item {0}").format(item_code)
        }

    # Validate against max discount if configured and rate is reduced
    max_discount = flt(pos_settings.get(FIELD_MAX_DISCOUNT_ALLOWED) or 0)
    if max_discount > 0 and original_rate > 0 and item_rate < original_rate:
        # Calculate effective discount percentage
        discount_pct = round(((original_rate - item_rate) / original_rate) * 100, 2)
        if discount_pct > max_discount:
            return {
                "valid": False,
                "message": _("Rate reduction for item {0} is {1}% which exceeds the maximum allowed discount of {2}%").format(
                    item_code, discount_pct, max_discount
                )
            }

    return {"valid": True}


def recursive_sanitize(data):
    """Recursively sanitize dictionaries and lists to replace "None", "null", 
    and "undefined" strings with None for common identifier fields.
    """
    if isinstance(data, dict):
        # Fields that are common candidates for causing DoesNotExistErrors
        identifier_keys = ["name", "pos_profile", "offline_id", "return_against", "doctype", "customer"]
        
        for key in list(data.keys()):
            val = data[key]
            
            # Sanitize identifier fields
            if key in identifier_keys:
                if isinstance(val, str) and val.strip() in ["None", "null", "undefined", ""]:
                    data[key] = None
                elif val is False:
                    data[key] = None
            
            # Recurse into nested structures
            if isinstance(val, (dict, list)):
                recursive_sanitize(val)
                
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                recursive_sanitize(item)
    
    return data


def log_manual_rate_edit(item, invoice_name, user=None):
    """
    Create an audit log entry for manual rate edits.

    This function creates a Comment on the Sales Invoice documenting the rate change.
    It should only be called ONCE per item, after the invoice is successfully submitted.

    Args:
        item: The item dict/object with rate information. Must contain:
            - is_rate_manually_edited: Flag indicating manual edit (1 or 0)
            - item_code: The item code
            - rate: The new/edited rate
            - original_rate: The original price before edit (or price_list_rate as fallback)
        invoice_name: The Sales Invoice document name
        user: Optional user who made the edit (defaults to session user)

    Returns:
        None
    """
    # Only log if rate was manually edited
    if not cint(item.get(FIELD_IS_RATE_MANUALLY_EDITED)):
        return

    user = user or frappe.session.user
    item_code = item.get(FIELD_ITEM_CODE)
    original_rate = flt(item.get(FIELD_ORIGINAL_RATE) or item.get(FIELD_PRICE_LIST_RATE) or 0)
    new_rate = flt(item.get(FIELD_RATE) or 0)

    # Skip logging if rates are the same (no actual change)
    if original_rate == new_rate:
        return

    # Calculate discount/markup percentage for logging
    change_pct = 0
    change_type = "reduction"
    if original_rate > 0:
        change_pct = round(abs((original_rate - new_rate) / original_rate) * 100, 2)
        if new_rate > original_rate:
            change_type = "increase"

    # Create audit comment on the invoice
    frappe.get_doc({
        "doctype": DOCTYPE_COMMENT,
        "comment_type": "Comment",
        "reference_doctype": DOCTYPE_SALES_INVOICE,
        "reference_name": invoice_name,
        "content": _("Manual rate edit by {user}: Item {item_code} rate changed from {original} to {new} ({change_pct}% {change_type})").format(
            user=user,
            item_code=item_code,
            original=frappe.format_value(original_rate, {"fieldtype": "Currency"}),
            new=frappe.format_value(new_rate, {"fieldtype": "Currency"}),
            change_pct=change_pct,
            change_type=change_type
        )
    }).insert(ignore_permissions=True)


def standardize_pricing_rules(items):
    """
    Standardize pricing_rules field on invoice items.
    ERPNext expects a comma-separated string, but frontend/offline may send:
    - Python list: ["PRLE-0001", "PRLE-0002"]
    - JSON string: '["PRLE-0001"]' or '[\\n "PRLE-0001"\\n]'

    Args:
        items: List of item dicts to standardize (modified in place)
    """
    for item in items or []:
        pricing_rules = item.get("pricing_rules")
        if not pricing_rules:
            continue

        item["pricing_rules"] = _pricing_rule_to_string(pricing_rules)


def _pricing_rule_to_string(value):
    """
    Convert pricing_rules value to comma-separated string.
    Returns empty string if value is invalid/unparseable.
    """
    if not value:
        return ""

    # Already a list - join it
    if isinstance(value, list):
        return ",".join(str(r) for r in value if r)

    # Must be a string at this point
    if not isinstance(value, str):
        return ""

    stripped = value.strip()

    # Not JSON-like - return as-is (already a string like "PRLE-0001,PRLE-0002")
    if not stripped.startswith("["):
        return stripped

    # Try to parse JSON array
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return ",".join(str(r) for r in parsed if r)
    except (json.JSONDecodeError, TypeError, ValueError):
        # Malformed JSON that looks like array - clear it to prevent issues
        frappe.log_error(
            f"Invalid pricing_rules JSON: {stripped[:100]}",
            "Pricing Rules Normalization"
        )
        return ""

    return ""


def get_payment_account(mode_of_payment, company):
    """
    Get account for mode of payment.
    Tries multiple fallback methods to find a suitable account.
    Results are cached per-request via frappe.local to avoid repeated DB lookups.
    """
    # Per-request cache: avoid repeated DB lookups for the same mode_of_payment + company
    cache_attr = "_payment_account_cache"
    if not hasattr(frappe.local, cache_attr):
        frappe.local._payment_account_cache = {}
    cache_key = (mode_of_payment, company)
    if cache_key in frappe.local._payment_account_cache:
        return frappe.local._payment_account_cache[cache_key]

    def _cache_and_return(result):
        frappe.local._payment_account_cache[cache_key] = result
        return result

    # Try 1: Mode of Payment Account table
    account = frappe.db.get_value(
        "Mode of Payment Account",
        {"parent": mode_of_payment, "company": company},
        "default_account",
    )
    if account:
        return _cache_and_return({"account": account})

    # Try 2: POS Payment Method from POS Profile
    account = frappe.db.sql(
        """
		SELECT ppm.default_account
		FROM `tabPOS Payment Method` ppm
		INNER JOIN `tabPOS Profile` pp ON ppm.parent = pp.name
		WHERE ppm.mode_of_payment = %s
		AND pp.company = %s
		AND ppm.default_account IS NOT NULL
		LIMIT 1
	""",
        (mode_of_payment, company),
        as_dict=1,
    )

    if account and account[0].default_account:
        return _cache_and_return({"account": account[0].default_account})

    # Try 3: Company default cash account (for cash payments)
    if "cash" in mode_of_payment.lower():
        account = frappe.get_value("Company", company, "default_cash_account")
        if account:
            return _cache_and_return({"account": account})

    # Try 4: Company default bank account
    account = frappe.get_value("Company", company, "default_bank_account")
    if account:
        return _cache_and_return({"account": account})

    # Try 5: Any Cash/Bank account for the company
    account = frappe.db.get_value(
        "Account",
        {"company": company, "account_type": ["in", ["Cash", "Bank"]], "is_group": 0},
        "name",
    )
    if account:
        return _cache_and_return({"account": account})

    # No account found - throw error
    frappe.throw(
        _(
            "Please set default Cash or Bank account in Mode of Payment {0} or set default accounts in Company {1}"
        ).format(mode_of_payment, company),
        title=_("Missing Account"),
    )


# ==========================================
# Stock Validation Functions
# ==========================================


def _get_available_stock(item):
    """Return available stock qty for an item row."""
    warehouse = item.get("warehouse")
    batch_no = item.get("batch_no")
    item_code = item.get("item_code")

    if not item_code or not warehouse:
        return 0

    if batch_no:
        return get_batch_qty(batch_no, warehouse) or 0

    # Get stock from Bin
    bin_qty = frappe.db.get_value(
        "Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"
    )
    return flt(bin_qty) or 0


def _collect_stock_errors(items):
    """Return list of items exceeding available stock.

    Uses batch SQL to fetch all non-batch stock in a single query
    instead of N individual queries.
    """
    errors = []

    # Separate batch items (need individual API calls) from non-batch items (can batch query)
    non_batch_items = []
    batch_items = []
    for d in items:
        if flt(d.get("qty")) < 0:
            continue
        if not d.get("item_code") or not d.get("warehouse"):
            continue
        if d.get("batch_no"):
            batch_items.append(d)
        else:
            non_batch_items.append(d)

    # Batch query: fetch all non-batch stock in a single SQL
    bin_stock = {}
    if non_batch_items:
        # Build unique (item_code, warehouse) pairs
        pairs = list({(d.get("item_code"), d.get("warehouse")) for d in non_batch_items})
        if pairs:
            conditions = " OR ".join(
                ["(item_code = %s AND warehouse = %s)"] * len(pairs)
            )
            flat_params = [v for pair in pairs for v in pair]
            rows = frappe.db.sql(
                f"SELECT item_code, warehouse, actual_qty FROM `tabBin` WHERE {conditions}",
                flat_params,
                as_dict=True,
            )
            for row in rows:
                bin_stock[(row.item_code, row.warehouse)] = flt(row.actual_qty)

    # Check non-batch items against batch-fetched stock
    for d in non_batch_items:
        available = bin_stock.get((d.get("item_code"), d.get("warehouse")), 0)
        requested = flt(
            d.get("stock_qty")
            or (flt(d.get("qty")) * flt(d.get("conversion_factor") or 1))
        )
        if requested > available:
            errors.append(
                {
                    "item_code": d.get("item_code"),
                    "warehouse": d.get("warehouse"),
                    "requested_qty": requested,
                    "available_qty": available,
                }
            )

    # Check batch items individually (ERPNext API limitation)
    for d in batch_items:
        available = get_batch_qty(d.get("batch_no"), d.get("warehouse")) or 0
        requested = flt(
            d.get("stock_qty")
            or (flt(d.get("qty")) * flt(d.get("conversion_factor") or 1))
        )

        if requested > available:
            errors.append(
                {
                    "item_code": d.get("item_code"),
                    "warehouse": d.get("warehouse"),
                    "requested_qty": requested,
                    "available_qty": available,
                }
            )

    return errors


def _should_block(pos_profile):
    """Check if sale should be blocked for insufficient stock."""
    # First check global ERPNext Stock Settings
    allow_negative = cint(
        frappe.db.get_single_value("Stock Settings", "allow_negative_stock") or 0
    )
    if allow_negative:
        return False

    # Check POS Settings for the specific profile
    if pos_profile:
        # Check if POS Settings allows negative stock
        pos_settings_allow_negative = cint(
            frappe.db.get_value(
                "POS Settings",
                {"pos_profile": pos_profile},
                "allow_negative_stock"
            ) or 0
        )
        if pos_settings_allow_negative:
            return False

        # Try to get custom field (may not exist in vanilla ERPNext)
        block_sale = cint(
            frappe.db.get_value(
                "POS Profile", pos_profile, "posa_block_sale_beyond_available_qty"
            )
            or 1
        )
        return bool(block_sale)

    # Default to blocking if no profile specified
    return True


def _validate_stock_on_invoice(invoice_doc):
    """Validate stock availability before submission."""
    if invoice_doc.doctype == "Sales Invoice" and not cint(
        getattr(invoice_doc, "update_stock", 0)
    ):
        return

    # Collect all stock items to check
    items_to_check = [d.as_dict() for d in invoice_doc.items if d.get("is_stock_item")]

    # Include packed items if present
    if hasattr(invoice_doc, "packed_items"):
        items_to_check.extend([d.as_dict() for d in invoice_doc.packed_items])

    # Check for stock errors
    errors = _collect_stock_errors(items_to_check)

    # Throw error if stock insufficient and blocking is enabled
    if errors and _should_block(invoice_doc.pos_profile):
        frappe.throw(frappe.as_json({"errors": errors}), frappe.ValidationError)


def _auto_set_return_batches(invoice_doc):
    """Assign batch numbers for return invoices without a source invoice.

    When an item requires a batch number, this function allocates the first
    available batch in FIFO order. If no batches exist in the selected
    warehouse, an informative error is raised.
    """
    if not invoice_doc.get("is_return") or invoice_doc.get("return_against"):
        return

    for d in invoice_doc.items:
        if not d.get("item_code") or not d.get("warehouse"):
            continue

        has_batch = frappe.db.get_value("Item", d.item_code, "has_batch_no")
        if has_batch and not d.get("batch_no"):
            batch_list = (
                get_batch_qty(item_code=d.item_code, warehouse=d.warehouse) or []
            )
            batch_list = [b for b in batch_list if flt(b.get("qty")) > 0]

            if batch_list:
                # FIFO: batches are already sorted by posting/expiry in ERPNext
                d.batch_no = batch_list[0].get("batch_no")
            else:
                frappe.throw(
                    _("No batches available in {0} for {1}.").format(
                        d.warehouse, d.item_code
                    )
                )


# ==========================================
# Validation Functions
# ==========================================


@frappe.whitelist()
def validate_cart_items(items, pos_profile=None):
    """Validate cart items for available stock.

    Returns a list of item dicts where requested quantity exceeds availability.
    This can be used on the front-end for pre-submission checks.
    """
    if isinstance(items, str):
        items = json.loads(items)

    if pos_profile and not frappe.db.exists("POS Profile", pos_profile):
        pos_profile = None

    if not _should_block(pos_profile):
        return []

    errors = _collect_stock_errors(items)
    if not errors:
        return []

    return errors


@frappe.whitelist()
def validate_return_items(original_invoice_name, return_items, doctype="Sales Invoice"):
    """Ensure that return items do not exceed the quantity from the original invoice.
    Also validates return time frame based on POS Settings.

    Uses query builder for parameterized queries. Fetches invoice details, original
    item quantities, and already-returned quantities in 3 queries total.
    """
    from frappe.utils import date_diff, getdate
    from frappe.query_builder.functions import Sum, Abs

    if isinstance(return_items, str):
        return_items = json.loads(return_items)

    # Fetch invoice pos_profile and posting_date for validation
    si = frappe.qb.DocType(doctype)
    invoice_data = (
        frappe.qb.from_(si)
        .select(si.pos_profile, si.posting_date)
        .where(si.name == original_invoice_name)
    ).run(as_dict=True)

    if not invoice_data:
        return {"valid": False, "message": _("Invoice {0} not found").format(original_invoice_name)}

    invoice_info = invoice_data[0]

    # Check return validity period from POS Settings
    if invoice_info.pos_profile:
        return_validity_days = cint(
            frappe.db.get_value(
                "POS Settings",
                {"pos_profile": invoice_info.pos_profile},
                "return_validity_days"
            ) or 0
        )

        if return_validity_days > 0:
            days_since_invoice = date_diff(getdate(nowdate()), getdate(invoice_info.posting_date))
            if days_since_invoice > return_validity_days:
                return {
                    "valid": False,
                    "message": _(
                        "Return period has expired. Invoice {0} was created {1} days ago. "
                        "Returns are only allowed within {2} days of purchase."
                    ).format(original_invoice_name, days_since_invoice, return_validity_days),
                }

    # Aggregate original item quantities by item_code
    si_item = frappe.qb.DocType(f"{doctype} Item")
    original_items = (
        frappe.qb.from_(si_item)
        .select(si_item.item_code, Sum(si_item.qty).as_("total_qty"))
        .where(si_item.parent == original_invoice_name)
        .groupby(si_item.item_code)
    ).run(as_dict=True)

    original_item_qty = {item.item_code: flt(item.total_qty) for item in original_items}

    # Aggregate quantities already returned from previous return invoices
    ret_si = frappe.qb.DocType(doctype)
    ret_item = frappe.qb.DocType(f"{doctype} Item")

    returned_qty_data = (
        frappe.qb.from_(ret_si)
        .inner_join(ret_item).on(ret_item.parent == ret_si.name)
        .select(ret_item.item_code, Sum(Abs(ret_item.qty)).as_("returned_qty"))
        .where(
            (ret_si.return_against == original_invoice_name)
            & (ret_si.docstatus == 1)
            & (ret_si.is_return == 1)
        )
        .groupby(ret_item.item_code)
    ).run(as_dict=True)

    # Subtract returned quantities
    for row in returned_qty_data:
        if row.item_code in original_item_qty:
            original_item_qty[row.item_code] -= flt(row.returned_qty)

    # Validate new return items
    for item in return_items:
        item_code = item.get("item_code")
        return_qty = abs(flt(item.get("qty", 0)))
        remaining = original_item_qty.get(item_code, 0)
        if return_qty > remaining:
            return {
                "valid": False,
                "message": _(
                    "You are trying to return more quantity for item {0} than was sold."
                ).format(item_code),
            }

    return {"valid": True}


# ==========================================
# Invoice Management (Two-Step Flow)
# ==========================================


def _apply_cost_center_from_opening_shift(invoice_doc):
    """
    Set the invoice Cost Center from the POS Profile linked to its POS Opening Shift.

    The opening shift determines which branch/profile actually fulfils the order
    (e.g. Call Center orders route to the target branch's shift), so that shift's
    POS Profile carries the correct accounting Cost Center — not necessarily the
    ordering POS Profile on the invoice. The resolved cost center is applied to the
    header and propagated to every item so the whole invoice posts consistently.
    """
    opening_shift = invoice_doc.get("posa_pos_opening_shift")
    if isinstance(opening_shift, dict):
        opening_shift = opening_shift.get("name")
    if not opening_shift:
        return

    shift_profile = frappe.db.get_value("POS Opening Shift", opening_shift, "pos_profile")
    if not shift_profile:
        return

    cost_center = frappe.db.get_value("POS Profile", shift_profile, "cost_center")
    if not cost_center:
        return

    invoice_doc.cost_center = cost_center
    for item in invoice_doc.get("items", []):
        item.cost_center = cost_center


def _get_branch_warehouse(branch):
    """Warehouse of the POS Profile that belongs to this branch."""
    if not branch:
        return None
    return frappe.db.get_value(
        "POS Profile", {"branch": branch, "disabled": 0}, "warehouse"
    )


def _apply_branch_warehouse(invoice_doc, branch):
    """Point every line at the branch's warehouse.

    Call this AFTER set_missing_values(). ERPNext's set_pos_fields() calls
    get_pos_profile_item_details(..., update_data=True), which unconditionally
    re-stamps the POS Profile's warehouse onto every item, so anything set before
    that is discarded.
    """
    branch_warehouse = _get_branch_warehouse(branch)
    if not branch_warehouse:
        return

    for item in invoice_doc.get("items", []):
        item.warehouse = branch_warehouse

    for p_item in invoice_doc.get("packed_items", []):
        p_item.warehouse = branch_warehouse


def _prepare_invoice_doc(data):
    """
    Build and prepare an invoice document from POS data WITHOUT saving.

    Shared logic between update_invoice (draft) and submit_invoice (direct submit).
    This avoids the double save/reload cycle that was causing ~2-3s of extra latency.

    Returns:
        tuple: (invoice_doc, pos_profile_doc) - prepared document and cached profile
    """
    # Normalize input
    recursive_sanitize(data)
    
    pos_profile = data.get("pos_profile")
    # A caller may pass the whole POS Profile object (e.g. from check_opening_shift)
    # instead of its name — normalise to the name string so downstream loads/compares work.
    if isinstance(pos_profile, dict):
        pos_profile = pos_profile.get("name")
    if pos_profile in ["None", "null", "", False]:
        pos_profile = None

    # Same guard for the opening shift — callers sometimes pass the whole POS Opening
    # Shift object; the Link field and every db lookup need the name string.
    if isinstance(data.get("posa_pos_opening_shift"), dict):
        data["posa_pos_opening_shift"] = data["posa_pos_opening_shift"].get("name")

    doctype = data.get("doctype") or "Sales Invoice"
    if doctype in ["None", "null", "", False]:
        doctype = "Sales Invoice"
    data["doctype"] = doctype

    # Normalize pricing_rules before document creation
    standardize_pricing_rules(data.get("items"))

    # Create or update invoice
    name = data.get("name")
    if not name: # Catch both None and empty strings sanitized by helper
        name = None
        data.pop("name", None)

    if name:
        invoice_doc = frappe.get_doc(doctype, name)
        # Clear child tables to prevent duplicating lines when updating draft invoice
        invoice_doc.set("items", [])
        invoice_doc.set("payments", [])
        invoice_doc.set("sales_team", [])
        invoice_doc.update(data)
    else:
        invoice_doc = frappe.get_doc(data)

    # Parity with posawesome2: Adjust packed items and handle removed ingredients
    if hasattr(invoice_doc, "packed_items") and invoice_doc.packed_items:
        items_to_remove = []
        for item in invoice_doc.items:
            if item.get("posa_row_id"):
                removed_ingredients = []
                if item.get("removed_ingredients"):
                    try:
                        removed_ingredients = json.loads(item.removed_ingredients)
                        if not isinstance(removed_ingredients, list):
                            removed_ingredients = []
                    except (ValueError, TypeError):
                        removed_ingredients = []

                for p_item in invoice_doc.packed_items:
                    if p_item.get("posa_row_id") == item.get("posa_row_id"):
                        if p_item.item_code in removed_ingredients:
                            items_to_remove.append(p_item)
                        else:
                            # Multiply per-unit quantity by parent quantity
                            p_item.qty = flt(item.qty) * flt(p_item.qty)
        
        # Remove the filtered components from packed_items
        for p_item in items_to_remove:
            invoice_doc.packed_items.remove(p_item)

    # Recursively expand packed items that are themselves Product Bundles — e.g.
    # a variant selected inside a combo that has its own recipe/bundle. Its
    # bundle components are added to the packing list too (and nested bundles
    # are expanded as well).
    if hasattr(invoice_doc, "packed_items") and invoice_doc.packed_items:
        _seen_bundles = set()
        _queue = list(invoice_doc.packed_items)
        while _queue:
            p = _queue.pop(0)
            bundle_name = frappe.db.get_value(
                "Product Bundle", {"new_item_code": p.item_code}, "name"
            )
            if not bundle_name or bundle_name in _seen_bundles:
                continue
            _seen_bundles.add(bundle_name)
            try:
                bundle = frappe.get_doc("Product Bundle", bundle_name)
            except Exception:
                continue
            for b in bundle.items:
                row = invoice_doc.append("packed_items", {
                    "parent_item": p.get("parent_item") or p.item_code,
                    "item_code": b.item_code,
                    "qty": flt(b.qty) * flt(p.qty or 1),
                    "posa_row_id": p.get("posa_row_id"),
                    "warehouse": p.get("warehouse"),
                    "uom": b.uom or frappe.db.get_value("Item", b.item_code, "stock_uom"),
                    "conversion_factor": 1.0,
                    "rate": 0,
                })
                _queue.append(row)

    pos_profile_doc = None
    if pos_profile:
        try:
            pos_profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
        except Exception:
            frappe.throw(_("Unable to load POS Profile {0}").format(pos_profile))

        invoice_doc.pos_profile = pos_profile
        
        if pos_profile == "Call Center":
            current_notes = invoice_doc.get("posa_notes") or ""
            if "Created from Call Center" not in current_notes:
                invoice_doc.posa_notes = (current_notes + "\nCreated from Call Center").strip()
            
            # Note: Tagging is moved to submit_invoice/update_invoice after save()

        if pos_profile_doc:
            if pos_profile_doc.company and not invoice_doc.get("company"):
                invoice_doc.company = pos_profile_doc.company
            if pos_profile_doc.currency and not invoice_doc.get("currency"):
                invoice_doc.currency = pos_profile_doc.currency

            # Copy accounting dimensions from POS Profile
            profile_branch = getattr(pos_profile_doc, "branch", None)

            # A RETURN follows the SAME branch as the invoice it reverses — a return of a
            # Call Center order must not re-ask for the target branch; inherit it from the
            # original so it fulfils/reports against the right branch.
            if not data.get("branch"):
                return_against = data.get("return_against") or invoice_doc.get("return_against")
                if return_against:
                    original_branch = frappe.db.get_value("Sales Invoice", return_against, "branch")
                    if original_branch:
                        data["branch"] = original_branch

            selected_branch = data.get("branch") or profile_branch

            # MANDATORY: If in Call Center mode, a branch MUST be selected manually
            if pos_profile == "Call Center" and not data.get("branch"):
                frappe.throw(_("Target Branch is mandatory for Call Center orders."))

            if selected_branch:
                invoice_doc.branch = selected_branch
                for item in invoice_doc.get("items", []):
                    item.branch = selected_branch

                # Warehouse is re-applied after set_missing_values() further down:
                # ERPNext's set_pos_fields() stamps the POS Profile's own warehouse
                # over every line, which would send a Call Center order to the Call
                # Center warehouse instead of the branch fulfilling it.
                _apply_branch_warehouse(invoice_doc, selected_branch)

                for p_item in invoice_doc.get("packed_items", []):
                    if not flt(p_item.conversion_factor):
                        p_item.conversion_factor = 1.0

                # Link to the branch's open shift
                # Override if in Call Center mode or if branch is explicitly changed from profile default
                # if pos_profile == "Call Center" or selected_branch != profile_branch:
                #     branch_shift = _get_branch_open_shift(selected_branch)
                #     if branch_shift:
                #         invoice_doc.posa_pos_opening_shift = branch_shift

    # Validate return items if this is a return invoice
    return_against = invoice_doc.get("return_against")
    if return_against in ["None", "null", "", False]:
        return_against = None
        invoice_doc.return_against = None

    if (data.get("is_return") or invoice_doc.get("is_return")) and return_against:
        validation = validate_return_items(
            return_against,
            [d.as_dict() for d in invoice_doc.items],
            doctype=invoice_doc.doctype,
        )
        if not validation.get("valid"):
            frappe.throw(validation.get("message"))
    
    # Handle Delivery Charges
    delivery_charge_name = data.get("posa_delivery_charges")
    delivery_charge_rate = flt(data.get("posa_delivery_charges_rate"))
    passed_territory = data.get("territory")
    
    if passed_territory:
        invoice_doc.territory = passed_territory

    # Free Delivery: if this invoice's POS Profile waives delivery, force the charge to 0
    # regardless of what the (possibly cached/offline) payload sent.
    _fd_profile = invoice_doc.get("pos_profile") or data.get("pos_profile")
    if _fd_profile and cint(frappe.db.get_value("POS Profile", _fd_profile, "custom_free_delivery")):
        delivery_charge_rate = 0
        if delivery_charge_name and hasattr(invoice_doc, "taxes"):
            invoice_doc.taxes = [t for t in invoice_doc.taxes if t.description != delivery_charge_name]

    if delivery_charge_name and delivery_charge_rate:
        try:
            charge_doc = frappe.get_doc("Delivery Charges", delivery_charge_name)
            
            # Remove any existing delivery charge tax row to avoid duplicates
            if hasattr(invoice_doc, "taxes"):
                invoice_doc.taxes = [t for t in invoice_doc.taxes if t.description != delivery_charge_name]
            
            invoice_doc.append("taxes", {
                "charge_type": "Actual",
                "description": delivery_charge_name,
                "tax_amount": delivery_charge_rate,
                "cost_center": charge_doc.cost_center,
                "account_head": charge_doc.shipping_account,
                "add_deduct_tax": "Add",
                "included_in_print_rate": 0
            })
            
            # Recalculate totals
            invoice_doc.calculate_taxes_and_totals()
            
        except Exception as e:
            frappe.log_error(f"Error applying delivery charge: {str(e)}", "Delivery Charge Error")

    # Ensure customer exists
    customer_name = invoice_doc.get("customer")
    if customer_name and not frappe.db.exists("Customer", customer_name):
        try:
            cust = frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": customer_name,
                    "customer_group": "All Customer Groups",
                    "territory": "All Territories",
                    "customer_type": "Individual",
                }
            )
            cust.flags.ignore_permissions = True
            cust.insert()
            invoice_doc.customer = cust.name
            invoice_doc.customer_name = cust.customer_name
        except Exception as e:
            frappe.log_error(f"Failed to create customer {customer_name}: {e}")

    # Disable automatic pricing rules (we handle discounts manually from POS)
    invoice_doc.ignore_pricing_rule = 1
    invoice_doc.flags.ignore_pricing_rule = True

    # ========================================================================
    # OPTIMIZATION: Cache POS Settings to avoid repeated DB queries
    # ========================================================================
    pos_settings_cache = None
    if pos_profile:
        pos_settings_cache = frappe.db.get_value(
            DOCTYPE_POS_SETTINGS,
            {"pos_profile": pos_profile},
            [
                FIELD_ALLOW_USER_TO_EDIT_RATE,
                FIELD_MAX_DISCOUNT_ALLOWED,
                FIELD_ALLOW_NEGATIVE_STOCK
            ],
            as_dict=True
        )
        pos_profile_rounded = frappe.db.get_value(
            DOCTYPE_POS_PROFILE,
            pos_profile,
            FIELD_DISABLE_ROUNDED_TOTAL
        )
        if pos_settings_cache:
            pos_settings_cache[FIELD_DISABLE_ROUNDED_TOTAL] = pos_profile_rounded
        else:
            pos_settings_cache = {FIELD_DISABLE_ROUNDED_TOTAL: pos_profile_rounded}

    # ========================================================================
    # DISCOUNT CALCULATION - CRITICAL LOGIC
    # ========================================================================
    for item in invoice_doc.get("items", []):
        item_rate = flt(item.rate or 0)
        discount_pct = flt(item.discount_percentage or 0)
        frontend_price_list_rate = flt(item.get("price_list_rate") or 0)
        is_manual_edit = cint(item.get(FIELD_IS_RATE_MANUALLY_EDITED) or 0)

        if is_manual_edit:
            original_rate = flt(item.get(FIELD_ORIGINAL_RATE) or item.get(FIELD_PRICE_LIST_RATE) or 0)
            if original_rate > 0:
                item.price_list_rate = original_rate
            validation = validate_manual_rate_edit(item, pos_profile, pos_settings_cache)
            if not validation.get("valid"):
                frappe.throw(validation.get("message"))
        else:
            if frontend_price_list_rate > 0:
                item.price_list_rate = frontend_price_list_rate
            elif discount_pct > 0 and discount_pct < 100 and item_rate > 0:
                item.price_list_rate = calculate_price_list_rate(
                    item_rate, discount_pct, frontend_price_list_rate
                )
            else:
                item.price_list_rate = item_rate
            if flt(item.price_list_rate) < item_rate:
                item.price_list_rate = item_rate

        pricing_rules = item.get("pricing_rules")
        if pricing_rules:
            if isinstance(pricing_rules, list):
                item.pricing_rules = ",".join(str(r) for r in pricing_rules)
            elif isinstance(pricing_rules, str) and pricing_rules.startswith("["):
                try:
                    rules_list = json.loads(pricing_rules)
                    if isinstance(rules_list, list):
                        item.pricing_rules = ",".join(str(r) for r in rules_list)
                except (json.JSONDecodeError, TypeError):
                    item.pricing_rules = ""

    # Set invoice flags BEFORE calculations
    if doctype == "Sales Invoice":
        invoice_doc.is_pos = 1
        invoice_doc.update_stock = 1

    # ========================================================================
    # ROUNDING CONFIGURATION
    # ========================================================================
    disable_rounded = 1
    if pos_settings_cache and pos_settings_cache.get(FIELD_DISABLE_ROUNDED_TOTAL) is not None:
        disable_rounded = cint(pos_settings_cache.get(FIELD_DISABLE_ROUNDED_TOTAL))
    invoice_doc.disable_rounded_total = disable_rounded

    # Populate missing fields (company, currency, accounts, etc.)
    invoice_doc.set_missing_values()

    # MUST run after set_missing_values(): ERPNext's set_pos_fields() overwrites
    # every line's warehouse with the POS Profile's own, so setting it earlier is
    # silently undone. A Call Center order is fulfilled by its target branch, so
    # the stock has to come out of that branch's warehouse.
    if invoice_doc.get("branch"):
        _apply_branch_warehouse(invoice_doc, invoice_doc.branch)

    # Calculate totals and apply discounts
    invoice_doc.calculate_taxes_and_totals()
    if invoice_doc.grand_total is None:
        invoice_doc.grand_total = 0.0
    if invoice_doc.base_grand_total is None:
        invoice_doc.base_grand_total = 0.0

    # Set accounts for payment methods
    for payment in invoice_doc.payments:
        mode_of_payment = payment.get("mode_of_payment")
        if mode_of_payment and not payment.get("account"):
            try:
                account_info = get_payment_account(
                    mode_of_payment, invoice_doc.company
                )
                if account_info:
                    payment.account = account_info.get("account")
            except Exception as e:
                frappe.log_error(
                    f"Failed to get payment account for {mode_of_payment}: {e}",
                    "Payment Account Lookup"
                )

    # For return invoices, ensure payments are negative
    if invoice_doc.get("is_return"):
        if doctype == "Sales Invoice" and invoice_doc.get("payments"):
            for payment in invoice_doc.payments:
                payment.amount = -abs(payment.amount)
                if payment.base_amount:
                    payment.base_amount = -abs(payment.base_amount)
            invoice_doc.paid_amount = flt(sum(p.amount for p in invoice_doc.payments))
            invoice_doc.base_paid_amount = flt(
                sum(p.base_amount or 0 for p in invoice_doc.payments)
            )

    # Validate and track POS Coupon if coupon_code is provided
    coupon_code = data.get("coupon_code")
    if coupon_code:
        if frappe.db.table_exists("POS Coupon"):
            from ecs_posnext.pos_next.doctype.pos_coupon.pos_coupon import check_coupon_code
            coupon_result = check_coupon_code(
                coupon_code,
                customer=invoice_doc.customer,
                company=invoice_doc.company
            )
            if not coupon_result or not coupon_result.get("valid"):
                error_msg = coupon_result.get("msg", "Invalid coupon code") if coupon_result else "Invalid coupon code"
                frappe.throw(_(error_msg))
            invoice_doc.coupon_code = coupon_code

    invoice_doc.flags.ignore_permissions = True
    frappe.flags.ignore_account_permission = True

    return invoice_doc, pos_profile_doc


@frappe.whitelist()
def update_invoice(data):
    """Create or update invoice draft (Step 1)."""
    try:
        data = json.loads(data) if isinstance(data, str) else data
        invoice_doc, _pos_profile_doc = _prepare_invoice_doc(data)

        # Save as draft
        invoice_doc.docstatus = 0
        invoice_doc.save()

        # Add tag after save
        if data.get("pos_profile") == "Call Center":
            invoice_doc.add_tag("Call Center")

        # Update table status to disabled for Dine In orders
        if invoice_doc.custom_order_type == "Dine In" and invoice_doc.custom_table_number:
            frappe.db.set_value('Table Number', invoice_doc.custom_table_number, 'status', 'Disabled')

        return invoice_doc.as_dict()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Invoice Error")
        raise


PENDING_TIMEOUT_MINUTES = 5  # Pending records older than this are considered stale


def _is_pending_expired(modified_time):
    """Check if a pending record has expired based on modified time."""
    if not modified_time:
        return True  # No timestamp means treat as expired
    age_minutes = (frappe.utils.now_datetime() - modified_time).total_seconds() / 60
    return age_minutes > PENDING_TIMEOUT_MINUTES


def _reuse_sync_record(sync_record_name):
    """Reset an existing sync record to Pending status for retry."""
    sync_doc = frappe.get_doc("Offline Invoice Sync", sync_record_name)
    sync_doc.status = "Pending"
    sync_doc.synced_at = None
    sync_doc.flags.ignore_permissions = True
    sync_doc.save()
    return {"already_synced": False, "sync_record_name": sync_record_name}


def _ensure_offline_uniqueness(offline_id, pos_profile=None, customer=None):
    """
    Ensure offline invoice uniqueness with race condition protection.

    Uses a reservation pattern:
    1. Check if a sync record exists (with row-level lock)
    2. If synced with valid invoice, return existing invoice
    3. If synced but invoice deleted/invalid, allow retry
    4. If pending but expired (>5 min), allow retry
    5. If pending and active, reject (another request processing)
    6. If failed, allow retry
    7. If not exists, create pending reservation

    Args:
        offline_id: The unique offline ID from the client
        pos_profile: POS Profile name
        customer: Customer name

    Returns:
        dict with:
        - already_synced (bool): True if invoice was already synced
        - invoice_data (dict): Existing invoice data if already_synced
        - sync_record_name (str): Name of the sync record for this attempt
    """
    # Acquire row-level lock to prevent race conditions
    existing_sync = frappe.db.get_value(
        "Offline Invoice Sync",
        {"offline_id": offline_id},
        ["name", "sales_invoice", "status", "modified"],
        as_dict=True,
        for_update=True
    )

    if existing_sync:
        sync_status = existing_sync.get("status")
        sync_record_name = existing_sync.name

        # Handle Pending status
        if sync_status == "Pending":
            if _is_pending_expired(existing_sync.get("modified")):
                # Expired pending - allow retry
                return _reuse_sync_record(sync_record_name)
            else:
                # Active pending - reject with specific error code
                frappe.throw(
                    _("This invoice is currently being processed. Please wait."),
                    exc=frappe.ValidationError,
                    title="SYNC_IN_PROGRESS"
                )

        # Handle Failed status - allow retry
        if sync_status == "Failed":
            return _reuse_sync_record(sync_record_name)

        # Handle Synced status - verify invoice still valid
        if sync_status == "Synced" and existing_sync.sales_invoice and existing_sync.sales_invoice not in ["None", "null"]:
            if frappe.db.exists("Sales Invoice", existing_sync.sales_invoice):
                existing_invoice = frappe.get_doc("Sales Invoice", existing_sync.sales_invoice)
                if existing_invoice.docstatus == 1:
                    return {
                        "already_synced": True,
                        "invoice_data": {
                            "name": existing_invoice.name,
                            "status": existing_invoice.docstatus,
                            "grand_total": existing_invoice.grand_total,
                            "total": existing_invoice.total,
                            "net_total": existing_invoice.net_total,
                            "outstanding_amount": getattr(existing_invoice, "outstanding_amount", 0),
                            "paid_amount": getattr(existing_invoice, "paid_amount", 0),
                            "change_amount": getattr(existing_invoice, "change_amount", 0),
                            "duplicate_prevented": True,
                            "offline_id": offline_id,
                        }
                    }

            # Synced record points to deleted/invalid invoice - allow retry
            return _reuse_sync_record(sync_record_name)

        # Unknown status or synced without invoice - allow retry
        return _reuse_sync_record(sync_record_name)

    # No existing record - create pending reservation
    try:
        pending_sync = frappe.get_doc({
            "doctype": "Offline Invoice Sync",
            "offline_id": offline_id,
            "sales_invoice": "",
            "pos_profile": pos_profile,
            "customer": customer,
            "status": "Pending",
        })
        pending_sync.flags.ignore_permissions = True
        pending_sync.insert()

        return {
            "already_synced": False,
            "sync_record_name": pending_sync.name
        }
    except frappe.DuplicateEntryError:
        # Race condition: another request just created the record
        # Retry the check to get the new record
        return _ensure_offline_uniqueness(offline_id, pos_profile, customer)


def _complete_offline_sync(sync_record_name, invoice_name):
    """
    Mark an offline sync record as completed after successful invoice submission.

    Args:
        sync_record_name: Name of the Offline Invoice Sync record
        invoice_name: Name of the submitted Sales Invoice
    """
    if not sync_record_name:
        return

    try:
        sync_doc = frappe.get_doc("Offline Invoice Sync", sync_record_name)
        sync_doc.sales_invoice = invoice_name
        sync_doc.status = "Synced"
        sync_doc.synced_at = frappe.utils.now_datetime()
        sync_doc.flags.ignore_permissions = True
        sync_doc.save()
    except Exception as error:
        frappe.log_error(
            title="Offline Sync Completion Error",
            message=f"Failed to complete sync record {sync_record_name} for invoice {invoice_name}: {str(error)}"
        )


def _cleanup_failed_sync(sync_record_name):
    """
    Mark a sync record as failed when invoice submission fails.

    Instead of deleting, we mark as 'failed' to:
    1. Preserve audit trail of sync attempts
    2. Allow manual investigation of failures
    3. Enable retry logic based on failure count

    Args:
        sync_record_name: Name of the Offline Invoice Sync record
    """
    if not sync_record_name:
        return

    try:
        sync_doc = frappe.get_doc("Offline Invoice Sync", sync_record_name)
        sync_doc.status = "Failed"
        sync_doc.synced_at = frappe.utils.now_datetime()
        sync_doc.flags.ignore_permissions = True
        sync_doc.save()
    except Exception as error:
        frappe.log_error(
            title="Offline Sync Cleanup Error",
            message=f"Failed to mark sync record {sync_record_name} as failed: {str(error)}"
        )


@frappe.whitelist()
def check_offline_invoice_synced(offline_id):
    """
    Check if an offline invoice has already been synced.

    This endpoint is called by the frontend before attempting to sync
    an offline invoice, preventing duplicate submissions.

    Args:
        offline_id: The unique offline ID to check

    Returns:
        dict with 'synced' (bool) and 'sales_invoice' (str or None)
    """
    from ecs_posnext.pos_next.doctype.offline_invoice_sync.offline_invoice_sync import (
        OfflineInvoiceSync,
    )

    result = OfflineInvoiceSync.is_synced(offline_id)

    # Defensive check - ensure result is a dict
    if not result or not isinstance(result, dict):
        return {"synced": False, "sales_invoice": None}

    # Additionally verify the sales invoice still exists and is submitted
    if result.get("synced") and result.get("sales_invoice"):
        if frappe.db.exists("Sales Invoice", result["sales_invoice"]):
            docstatus = frappe.db.get_value(
                "Sales Invoice", result["sales_invoice"], "docstatus"
            )
            if docstatus == 1:  # Submitted
                return result

        # Invoice was deleted or not submitted, clear the sync record
        return {"synced": False, "sales_invoice": None}

    return result


def _reconcile_return_against_original(return_doc):
    """Knock a no-cash Return credit note off the original invoice it reverses.

    For an UNPAID / credit-sale original, the return carries no refund payment, so it
    lands as a standalone -X credit note while the original keeps its +X outstanding
    (still showing as collectible). This posts a Debtors knock-off Journal Entry so BOTH
    the original and the credit note settle to 0 — nothing collected, nothing owed.
    Skipped when the original was already paid or the return already carries a cash
    refund (return outstanding not negative).
    """
    if return_doc.docstatus != 1:
        return None  # only settle once the credit note is actually submitted
    original_name = return_doc.get("return_against")
    if not original_name:
        return None
    orig = frappe.db.get_value(
        "Sales Invoice", original_name,
        ["outstanding_amount", "debit_to", "customer", "company"], as_dict=True,
    )
    if not orig or flt(orig.outstanding_amount) <= 0:
        return None  # original already settled/paid — nothing to knock off
    ret_out = flt(frappe.db.get_value("Sales Invoice", return_doc.name, "outstanding_amount"))
    if ret_out >= 0:
        return None  # return already settled by a cash refund
    knockoff = min(flt(orig.outstanding_amount), abs(ret_out))
    if knockoff <= 0:
        return None

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Credit Note"
    je.posting_date = nowdate()
    je.company = orig.company
    je.user_remark = _("Auto-settle return {0} against {1}").format(return_doc.name, original_name)
    je.append("accounts", {
        "account": orig.debit_to, "party_type": "Customer", "party": orig.customer,
        "reference_type": "Sales Invoice", "reference_name": original_name,
        "credit_in_account_currency": knockoff,  # clears the original receivable
    })
    je.append("accounts", {
        "account": orig.debit_to, "party_type": "Customer", "party": orig.customer,
        "reference_type": "Sales Invoice", "reference_name": return_doc.name,
        "debit_in_account_currency": knockoff,  # clears the credit note
    })
    je.flags.ignore_permissions = True
    je.insert(ignore_permissions=True)
    je.submit()
    return je.name


@frappe.whitelist()
def submit_invoice(invoice=None, data=None):
    """Submit the invoice (Step 2)."""

    # Log incoming data for debugging
    frappe.log_error(
        title="POS Submit Invoice Entry",
        message=f"Raw Invoice: {frappe.as_json(invoice)}\nRaw Data: {frappe.as_json(data)}"
    )

    # -----------------------------
    # Helpers
    # -----------------------------
    def is_empty_value(value):
        if value is None:
            return True

        if isinstance(value, str):
            return value.strip() in ["", "None", "none", "null", "undefined", "False", "false"]

        return value is False

    # -----------------------------
    # Handle different calling conventions
    # -----------------------------
    if is_empty_value(invoice):
        if data:
            data_parsed = json.loads(data) if isinstance(data, str) else data

            if isinstance(data_parsed, dict):
                if "invoice" in data_parsed:
                    invoice = data_parsed.get("invoice")
                    data = data_parsed.get("data", {})
                elif "name" in data_parsed or "doctype" in data_parsed:
                    # Data itself might be the invoice
                    invoice = data_parsed
                    data = {}
                else:
                    frappe.throw(
                        _("Missing invoice parameter. Received data: {0}").format(
                            json.dumps(data_parsed, default=str)
                        )
                    )
            else:
                frappe.throw(_("Missing invoice parameter"))
        else:
            frappe.throw(_("Both invoice and data parameters are missing"))

    # -----------------------------
    # Parse JSON strings if needed
    # -----------------------------
    if isinstance(data, str):
        data = data.strip()
        data = json.loads(data) if data and data != "{}" else {}

    if isinstance(invoice, str):
        invoice = invoice.strip()

        if is_empty_value(invoice):
            frappe.throw(_("Invalid invoice parameter"))

        try:
            invoice = json.loads(invoice)
        except Exception:
            frappe.throw(_("Invalid invoice JSON: {0}").format(invoice))

    # Log incoming request for debugging
    frappe.log_error(
        title="POS Submit Invoice Debug",
        message=f"Invoice: {frappe.as_json(invoice)}\nData: {frappe.as_json(data)}"
    )

    # -----------------------------
    # Ensure invoice and data are dicts
    # -----------------------------
    if not isinstance(invoice, dict):
        frappe.throw(_("Invalid invoice format"))

    if not isinstance(data, dict):
        data = {}

    # -----------------------------
    # Deep sanitize all identifiers
    # -----------------------------
    recursive_sanitize(invoice)
    recursive_sanitize(data)

    # ============================================================
    # IMPORTANT FIX
    # Remove invalid Sales Invoice name before _prepare_invoice_doc
    # This prevents: Sales Invoice None not found
    # ============================================================
    invoice_name = invoice.get("name")

    if is_empty_value(invoice_name):
        invoice.pop("name", None)

    # لو doctype جاي غلط
    doctype = invoice.get("doctype", "Sales Invoice")
    if is_empty_value(doctype):
        doctype = "Sales Invoice"
        invoice["doctype"] = "Sales Invoice"

    pos_profile = invoice.get("pos_profile")

    # Normalize pricing_rules before processing
    standardize_pricing_rules(invoice.get("items"))

    # ========================================================================
    # OFFLINE INVOICE DEDUPLICATION
    # ========================================================================
    offline_id = invoice.get("offline_id") or data.get("offline_id")
    sync_record_name = None

    if offline_id:
        dedup_result = _ensure_offline_uniqueness(
            offline_id=offline_id,
            pos_profile=pos_profile,
            customer=invoice.get("customer")
        )

        if dedup_result and dedup_result.get("already_synced"):
            return dedup_result.get("invoice_data", {})

        sync_record_name = dedup_result.get("sync_record_name") if dedup_result else None

    invoice_submitted = False

    try:
        # Debug before prepare
        frappe.log_error(
            title="Before Prepare Invoice Doc",
            message=(
                f"invoice.name={repr(invoice.get('name'))}\n"
                f"invoice.doctype={repr(invoice.get('doctype'))}\n"
                f"invoice={frappe.as_json(invoice)}"
            )
        )

        # Build and prepare invoice doc
        invoice_doc, pos_profile_doc = _prepare_invoice_doc(invoice)

        # Cost Center follows the POS Profile linked to the invoice's POS Opening Shift
        _apply_cost_center_from_opening_shift(invoice_doc)

        # Invoice follows the Business Day; stamp it + the owning cashier shift, and
        # enforce the sales cut-off (no-op unless business-day control is enabled).
        from ecs_posnext.api.business_day import apply_business_day_to_invoice
        apply_business_day_to_invoice(invoice_doc)

        # For return invoices, set update_outstanding_for_self = 0
        if invoice_doc.get("is_return") and invoice_doc.get("return_against"):
            invoice_doc.update_outstanding_for_self = 0

        # Handle sales team
        sales_team_data = invoice.get("sales_team") or data.get("sales_team")

        if sales_team_data and isinstance(sales_team_data, list):
            invoice_doc.sales_team = []

            for member in sales_team_data:
                if member and isinstance(member, dict):
                    invoice_doc.append("sales_team", {
                        "sales_person": member.get("sales_person"),
                        "allocated_percentage": member.get("allocated_percentage", 0),
                    })

        # Handle POS Coupon
        coupon_code = invoice.get("coupon_code") or data.get("coupon_code")

        if coupon_code:
            if frappe.db.table_exists("POS Coupon"):
                try:
                    from ecs_posnext.pos_next.doctype.pos_coupon.pos_coupon import increment_coupon_usage
                    increment_coupon_usage(coupon_code)
                except Exception as e:
                    frappe.log_error(
                        title="Failed to increment coupon usage",
                        message=f"Coupon: {coupon_code}, Error: {str(e)}"
                    )

        # Auto-set batch numbers for returns
        _auto_set_return_batches(invoice_doc)

        # Handle write-off amount
        write_off_amount = flt(data.get("write_off_amount") or invoice.get("write_off_amount") or 0)

        if write_off_amount > 0 and doctype == "Sales Invoice":
            if pos_profile:
                try:
                    pos_profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
                    write_off_account = pos_profile_doc.write_off_account
                    write_off_cost_center = pos_profile_doc.write_off_cost_center
                    write_off_limit = flt(pos_profile_doc.write_off_limit or 0)

                    if write_off_limit > 0 and write_off_amount > write_off_limit:
                        frappe.throw(
                            _("Write-off amount {0} exceeds limit {1}").format(
                                write_off_amount,
                                write_off_limit
                            )
                        )

                    if write_off_account:
                        invoice_doc.write_off_account = write_off_account
                        invoice_doc.write_off_cost_center = write_off_cost_center
                        invoice_doc.write_off_amount = write_off_amount
                        invoice_doc.base_write_off_amount = write_off_amount

                except Exception as e:
                    frappe.log_error(
                        f"Failed to apply write-off from POS Profile {pos_profile}: {e}",
                        "POS Write-Off Error"
                    )

        # Validate stock availability
        _validate_stock_on_invoice(invoice_doc)

        # Generate custom order sequence number
        parent_order_number = invoice.get("parent_order_number")
        if parent_order_number:
            # Supplement invoice: count existing suffixed invoices for this parent
            count = frappe.db.sql(
                """
                SELECT COUNT(name)
                FROM `tabSales Invoice`
                WHERE custom_number_order LIKE %s
                """,
                (f"{parent_order_number}-%",)
            )[0][0]
            invoice_doc.custom_number_order = f"{parent_order_number}-{count + 1}"

        elif not invoice_doc.get("custom_number_order") and invoice_doc.get("custom_order_type"):
            shift_start_str, _ = _get_user_shift_date_range()

            order_type = invoice_doc.get("custom_order_type")
            pos_profile = invoice_doc.get("pos_profile")
            branch = invoice_doc.get("branch")

            # Talabat (aggregator) orders are numbered T-*, with their own sequence.
            # Everything else (Dine In / Pickup / Delivery ...) shares a single M-* sequence.
            is_talabat = order_type == "Talabat"
            prefix = "T" if is_talabat else "M"

            # Count within the current shift, grouped by channel (Talabat vs. everything
            # else), excluding supplement invoices (X-Y-Z format). Scope by branch so all
            # POS Profiles serving the same branch (including Call Center orders targeting
            # it) share one continuous sequence; fall back to POS Profile if no branch.
            channel_condition = (
                "AND custom_order_type = 'Talabat'"
                if is_talabat
                else "AND custom_order_type != 'Talabat'"
            )

            if branch:
                scope_condition = "branch = %s"
                scope_value = branch
            else:
                scope_condition = "pos_profile = %s"
                scope_value = pos_profile

            count = frappe.db.sql(
                f"""
                SELECT COUNT(name)
                FROM `tabSales Invoice`
                WHERE {scope_condition}
                  {channel_condition}
                  AND TIMESTAMP(posting_date, posting_time) >= %s
                  AND (custom_number_order IS NULL OR custom_number_order NOT LIKE '%%-%%-%%')
                  AND is_return = 0
                """,
                (scope_value, shift_start_str)
            )[0][0]

            # Read the cycling limit from POS Profile (0 = no cycling)
            limit = frappe.utils.cint(
                frappe.db.get_value("POS Profile", pos_profile, "custom_order_number_limit") or 0
            )

            if limit and limit > 0:
                # Cycle: 1 → 2 → ... → limit → 1 → 2 → ...
                seq = (count % limit) + 1
            else:
                seq = count + 1

            invoice_doc.custom_number_order = f"{prefix}-{seq}"

        # Return controls: record WHO initiated the return (for the KDS alarm label) and
        # enforce the branch grace window — past it, prepared food is likely wasted, so a
        # branch manager must have approved (branch_approved flag from the password prompt).
        if invoice_doc.get("is_return") and invoice_doc.get("return_against"):
            return_source = (data.get("return_source") or invoice.get("return_source") or "User")
            if invoice_doc.meta.has_field("custom_return_source"):
                invoice_doc.custom_return_source = return_source
            branch_approved = bool(data.get("branch_approved") or invoice.get("branch_approved"))
            from ecs_posnext.ecs_posnext.api.kds import assert_return_within_grace
            assert_return_within_grace(invoice_doc.get("return_against"), branch_approved)

        # Save before submit
        invoice_doc.flags.ignore_permissions = True
        frappe.flags.ignore_account_permission = True

        invoice_doc.save()

        # Add tag after save
        is_call_center_invoice = "call center" in (invoice_doc.pos_profile or "").lower()
        if is_call_center_invoice or invoice_doc.pos_profile == "Call Center":
            invoice_doc.add_tag("Call Center")

        # Submit invoice if NOT a call center POS profile, or if force_submit is requested
        force_submit = flt(data.get("force_submit") or invoice.get("force_submit") or 0)
        
        # Allow Call Center to submit if Payment Type is selected and outstanding > 0
        call_center_can_submit = is_call_center_invoice and invoice_doc.custom_payment_type and invoice_doc.outstanding_amount > 0

        # Talabat orders never need branch approval — submit them straight away so
        # they go to the kitchen / dispatch instead of waiting in Need My Action.
        is_talabat = (invoice_doc.custom_order_type or "").strip().lower() == "talabat"

        # A return / credit note is a reversal of an already-existing order, not a new
        # order that needs branch approval — always submit it (even on Call Center),
        # otherwise it gets stuck as a Draft and never reverses the original.
        is_return_invoice = bool(invoice_doc.get("is_return"))

        if not is_call_center_invoice or force_submit or call_center_can_submit or is_talabat or is_return_invoice:
            invoice_doc.submit()
        invoice_submitted = True

        # Handle wallet transaction reversal for returns
        if invoice_doc.get("is_return") and invoice_doc.get("return_against"):
            try:
                from ecs_posnext.pos_next.doctype.wallet_transaction.wallet_transaction import reverse_wallet_transactions_for_return

                reverse_wallet_transactions_for_return(
                    original_invoice=invoice_doc.return_against,
                    return_invoice=invoice_doc.name
                )

            except Exception as wallet_error:
                frappe.log_error(
                    title="Wallet Reversal on Return Error",
                    message=(
                        f"Return Invoice: {invoice_doc.name}, "
                        f"Error: {str(wallet_error)}\n{frappe.get_traceback()}"
                    )
                )

                frappe.msgprint(
                    _("Return submitted but wallet reversal failed. Please check manually."),
                    alert=True,
                    indicator="orange"
                )

            # Settle a no-cash return against its (unpaid) original so the original
            # stops showing as collectible. No-op when the original was already paid
            # or the return carried a real cash refund.
            try:
                _reconcile_return_against_original(invoice_doc)
            except Exception:
                frappe.log_error(title="Return auto-settle failed", message=frappe.get_traceback())

        # Complete the offline sync record
        if sync_record_name:
            _complete_offline_sync(sync_record_name, invoice_doc.name)

        # Handle credit redemption after successful submission
        customer_credit_dict = data.get("customer_credit_dict") or invoice.get("customer_credit_dict")
        redeemed_customer_credit = data.get("redeemed_customer_credit") or invoice.get("redeemed_customer_credit")

        if redeemed_customer_credit and customer_credit_dict:
            try:
                from ecs_posnext.api.credit_sales import redeem_customer_credit
                redeem_customer_credit(invoice_doc.name, customer_credit_dict)

            except Exception as credit_error:
                frappe.log_error(
                    title="Credit Redemption Error",
                    message=(
                        f"Invoice: {invoice_doc.name}, "
                        f"Error: {str(credit_error)}\n{frappe.get_traceback()}"
                    )
                )

                frappe.msgprint(
                    _("Invoice submitted successfully but credit redemption failed. Please contact administrator."),
                    alert=True,
                    indicator="orange"
                )

        # Update table status to disabled for Dine In orders
        if invoice_doc.custom_order_type == "Dine In" and invoice_doc.custom_table_number:
            frappe.db.set_value('Table Number', invoice_doc.custom_table_number, 'status', 'Disabled')

        # Log manual rate edits for audit trail
        if doctype == DOCTYPE_SALES_INVOICE:
            incoming_items = invoice.get("items") or []

            for item in incoming_items:
                if cint(item.get(FIELD_IS_RATE_MANUALLY_EDITED)):
                    log_manual_rate_edit({
                        FIELD_ITEM_CODE: item.get(FIELD_ITEM_CODE),
                        "item_name": item.get("item_name"),
                        FIELD_RATE: flt(item.get(FIELD_RATE)),
                        FIELD_ORIGINAL_RATE: flt(
                            item.get(FIELD_ORIGINAL_RATE) or item.get(FIELD_PRICE_LIST_RATE)
                        ),
                        FIELD_IS_RATE_MANUALLY_EDITED: 1
                    }, invoice_doc.name)

        # Return complete invoice details
        result = {
            "name": invoice_doc.name,
            "status": invoice_doc.docstatus,
            "grand_total": invoice_doc.grand_total,
            "total": invoice_doc.total,
            "net_total": invoice_doc.net_total,
            "outstanding_amount": getattr(invoice_doc, "outstanding_amount", 0),
            "paid_amount": getattr(invoice_doc, "paid_amount", 0),
            "change_amount": getattr(invoice_doc, "change_amount", 0),
        }

        if offline_id:
            result["offline_id"] = offline_id

        return result

    except frappe.ValidationError as e:
        frappe.log_error(
            title="POS Submit Invoice ValidationError",
            message=f"Error: {str(e)}\nTraceback: {frappe.get_traceback()}"
        )
        raise

    except Exception:
        frappe.log_error(
            title="Submit Invoice Error",
            message=frappe.get_traceback()
        )
        raise

    finally:
        if sync_record_name and not invoice_submitted:
            _cleanup_failed_sync(sync_record_name)
# ==========================================
# Invoice History Management
# ==========================================


@frappe.whitelist()
def get_invoice(invoice_name):
	"""
	Get a single invoice with all details for POS.

	Args:
		invoice_name: Sales Invoice name

	Returns:
		Complete invoice document with items and payments
	"""
	if not invoice_name:
		frappe.throw(_("Invoice name is required"))

	if not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_("Invoice {0} does not exist").format(invoice_name))

	# Check permissions
	if not frappe.has_permission("Sales Invoice", "read", invoice_name):
		frappe.throw(_("You don't have permission to view this invoice"))

	if not invoice_name or invoice_name in ["None", "null", "", False]:
		frappe.throw(_("Invoice name is required"))

	# Get invoice document
	invoice = frappe.get_doc("Sales Invoice", invoice_name)

	return invoice.as_dict()


@frappe.whitelist()
def get_invoices(pos_profile, limit=100):
	"""
	Get list of invoices for a POS Profile.

	Args:
		pos_profile: POS Profile name
		limit: Maximum number of invoices to return (default 100)

	Returns:
		List of invoices with details
	"""
	if not pos_profile:
		frappe.throw(_("POS Profile is required"))

	# Check if user has access to this POS Profile
	has_access = frappe.db.exists(
		"POS Profile User",
		{"parent": pos_profile, "user": frappe.session.user}
	)

	if not has_access and not frappe.has_permission("Sales Invoice", "read"):
		frappe.throw(_("You don't have access to this POS Profile"))

	# Query for invoices
	invoices = frappe.db.sql("""
		SELECT
			name,
			customer,
			customer_name,
			posting_date,
			posting_time,
			grand_total,
			paid_amount,
			outstanding_amount,
			status,
			docstatus,
			is_return,
			return_against
		FROM
			`tabSales Invoice`
		WHERE
			pos_profile = %(pos_profile)s
			AND docstatus = 1
			AND is_pos = 1
		ORDER BY
			posting_date DESC,
			posting_time DESC
		LIMIT %(limit)s
	""", {
		"pos_profile": pos_profile,
		"limit": limit
	}, as_dict=True)

	# Load items for each invoice for filtering purposes
	for invoice in invoices:
		items = frappe.db.sql("""
			SELECT
				item_code,
				item_name,
				qty,
				rate,
				amount
			FROM
				`tabSales Invoice Item`
			WHERE
				parent = %(invoice_name)s
			ORDER BY
				idx
		""", {
			"invoice_name": invoice.name
		}, as_dict=True)
		invoice.items = items

	return invoices


# ==========================================
# All Orders (Sales Invoices across all branches)
# ==========================================


def _get_user_branch_filter_info():
	"""
	Returns (branch, is_call_center) for the current user.
	'Call Center' users can see all branches.
	Others are restricted to their POS Profile's branch.
	"""
	user = frappe.session.user

	# Find the user's currently open POS shift
	shift = frappe.db.sql("""
		SELECT pos_profile
		FROM `tabPOS Opening Shift`
		WHERE status = 'Open' AND user = %s AND docstatus != 2
		ORDER BY creation DESC
		LIMIT 1
	""", (user,), as_dict=True)

	pos_profile = None
	if shift:
		pos_profile = shift[0].pos_profile
	elif frappe.db.has_column("User", "pos_profile"):
		# Fallback to a default POS Profile on the User — only if that (optional) custom
		# field actually exists. Without this guard the query errors with "Unknown column
		# 'pos_profile'" for any user with no open shift, breaking the whole All Orders list.
		pos_profile = frappe.db.get_value("User", user, "pos_profile")

	# Administrator bypass ONLY if no profile/shift found
	if user == "Administrator" and not pos_profile:
		frappe.logger().debug(f"POS Branch Filter: Administrator bypass (no profile)")
		return None, True

	if not pos_profile:
		frappe.logger().debug(f"POS Branch Filter: No profile found for user {user}")
		return None, False

	branch = frappe.db.get_value("POS Profile", pos_profile, "branch")
	# Case-insensitive check for Call Center
	is_call_center = "call center" in (pos_profile or "").lower()

	frappe.logger().debug(f"POS Branch Filter: User={user}, Profile={pos_profile}, Branch={branch}, CallCenter={is_call_center}")

	return branch, is_call_center


def _get_user_shift_date_range():
	"""
	Get datetime range from the current user's open POS Profile shift.

	Determines the "logical shift window" based on the current time and the
	shift start/end times from the POS Profile, so the date range always
	reflects the CURRENT or LAST shift — not a stale period_start_date from an
	old POS Opening Shift that was never closed.

	Returns (shift_start_datetime, shift_end_datetime) as 'YYYY-MM-DD HH:MM:SS'
	strings for precise time-based filtering. Falls back to full-day range if
	no open shift or no shift times configured.
	"""
	from frappe.utils import get_time, getdate, now_datetime
	from datetime import timedelta

	# Find the user's currently open POS shift
	shift = frappe.db.sql("""
		SELECT pos_profile, period_start_date
		FROM `tabPOS Opening Shift`
		WHERE status = 'Open' AND user = %s AND docstatus != 2
		ORDER BY creation DESC
		LIMIT 1
	""", (frappe.session.user,), as_dict=True)

	today = frappe.utils.today()
	today_date = getdate(today)

	if not shift:
		# No open shift — default to full day today
		return f"{today} 00:00:00", f"{today} 23:59:59"

	pos_profile_name = shift[0].pos_profile
	profile_data = frappe.db.get_value(
		"POS Profile",
		pos_profile_name,
		["custom_shift_start_time", "custom_shift_end_time"],
		as_dict=True,
	)

	start_time = profile_data.get("custom_shift_start_time") if profile_data else None
	end_time = profile_data.get("custom_shift_end_time") if profile_data else None

	if not start_time or not end_time:
		return f"{today} 00:00:00", f"{today} 23:59:59"

	start_t = get_time(start_time)
	end_t = get_time(end_time)

	now = now_datetime()
	current_time = now.time()

	# Format times as HH:MM:SS
	start_time_str = start_t.strftime("%H:%M:%S")
	end_time_str = end_t.strftime("%H:%M:%S")

	if start_t <= end_t:
		# Same-day shift (e.g. 13:00–18:00)
		if current_time >= start_t:
			# Currently in shift or past shift end — show today's shift
			shift_date = today_date
		else:
			# Before shift start today — show yesterday's shift
			shift_date = today_date - timedelta(days=1)

		return f"{shift_date} {start_time_str}", f"{shift_date} {end_time_str}"
	else:
		# Overnight shift (e.g. 13:00–06:00)
		if current_time >= start_t:
			# After shift start today — shift runs into tomorrow
			next_day = today_date + timedelta(days=1)
			return f"{today_date} {start_time_str}", f"{next_day} {end_time_str}"
		elif current_time <= end_t:
			# Early morning — still in yesterday's shift
			yesterday = today_date - timedelta(days=1)
			return f"{yesterday} {start_time_str}", f"{today_date} {end_time_str}"
		else:
			# Between shifts — show last overnight shift
			yesterday = today_date - timedelta(days=1)
			return f"{yesterday} {start_time_str}", f"{today_date} {end_time_str}"


def _get_branch_open_shift(branch_name):
	"""
	Find the most recently opened 'Open' POS Opening Shift for a specific branch.
	Uses caching to reduce DB load.
	"""
	if not branch_name:
		return None

	# Try to get from cache first
	cache_key = f"branch_open_shift:{branch_name}"
	cached_val = frappe.cache().get_value(cache_key)
	if cached_val:
		return cached_val

	# 1. Find all POS Profiles associated with this branch
	branch_profiles = frappe.get_all(
		"POS Profile",
		filters={"branch": branch_name, "disabled": 0},
		pluck="name"
	)

	if not branch_profiles:
		return None

	# 2. Find any open shift for these profiles
	open_shift = frappe.db.get_value(
		"POS Opening Shift",
		{
			"pos_profile": ["in", branch_profiles],
			"status": "Open",
			"docstatus": 1
		},
		"name",
		order_by="period_start_date desc"
	)

	# Cache for 86400 seconds (1 day)
	if open_shift in ["None", "null", "", False]:
		open_shift = None

	if open_shift:
		frappe.cache().set_value(cache_key, open_shift, expires_in_sec=86400)

	return open_shift


@frappe.whitelist()
def clear_branch_shift_cache(branch_name):
	"""
	Clear the cached open shift for a branch.
	Called when shifts are opened or closed.
	"""
	if branch_name:
		frappe.cache().delete_value(f"branch_open_shift:{branch_name}")


@frappe.whitelist()
def get_all_orders_config():
	"""
	Get All Orders page configuration for the current user.

	Checks the 'All Orders Settings' DocType to see if the current user
	is listed in the user_date_ranges child table.

	Child table field 'days':
		- 0 = unlimited (user can pick any date range)
		- N = user can view last N days

	Returns:
		dict with:
		- can_select_dates (bool): True if user is in the settings table
		- days (int): Max past days (0 = unlimited)
		- date_from (str): Default start date
		- date_to (str): Default end date
	"""
	from frappe.utils import add_days

	user = frappe.session.user
	can_select = False
	max_days = 0
	date_from = None
	date_to = None
	shift_start = None
	shift_end = None

	try:
		settings = frappe.get_single("All Orders Settings")
		for row in settings.user_date_ranges or []:
			if row.user == user:
				can_select = True
				max_days = cint(row.days)
				break
	except Exception:
		pass

	if can_select:
		date_to = frappe.utils.today()
		if max_days > 0:
			date_from = add_days(date_to, -max_days)
		else:
			# Unlimited — default to last 30 days but user can change freely
			date_from = add_days(date_to, -30)
	else:
		# User not in settings — use shift-based datetime range
		shift_start, shift_end = _get_user_shift_date_range()
		# Extract date portions for the date inputs
		date_from = str(shift_start)[:10]
		date_to = str(shift_end)[:10]

	# Fill defaults if still empty
	if not date_from:
		date_from = frappe.utils.today()
	if not date_to:
		date_to = frappe.utils.today()

	# Include order number limit from the current user's POS Profile
	order_number_limit = 0
	try:
		from ecs_posnext.api.shifts import check_opening_shift
		shift_info = check_opening_shift(frappe.session.user)
		if shift_info and shift_info.get("pos_profile"):
			profile_name = shift_info["pos_profile"].get("name") or shift_info["pos_profile"]
			order_number_limit = cint(
				frappe.db.get_value("POS Profile", profile_name, "custom_order_number_limit") or 0
			)
	except Exception:
		pass

	return {
		"can_select_dates": can_select,
		"days": max_days,
		"date_from": date_from,
		"date_to": date_to,
		"shift_start": shift_start,
		"shift_end": shift_end,
		"order_number_limit": order_number_limit,
	}


@frappe.whitelist()
def update_order_number_limit(pos_profile, limit):
    """Update custom_order_number_limit on the given POS Profile. System Manager only."""
    if "System Manager" not in frappe.get_roles(frappe.session.user):
        frappe.throw(_("Only System Managers can change the Order Number Limit"))

    limit_val = cint(limit)
    if limit_val < 0:
        frappe.throw(_("Limit must be 0 (no cycling) or a positive number"))

    if not frappe.db.exists("POS Profile", pos_profile):
        frappe.throw(_("POS Profile {0} not found").format(pos_profile))

    frappe.db.set_value("POS Profile", pos_profile, "custom_order_number_limit", limit_val)
    frappe.db.commit()
    return {"message": _("Order Number Limit updated to {0}").format(limit_val), "limit": limit_val}


# How far back a customer-number / name search looks (independent of the browse max_days).
SEARCH_LOOKBACK_DAYS = 730


@frappe.whitelist()
def get_all_orders(date_from=None, date_to=None, limit=500, search=None, respect_dates=None):
	"""
	Get all Sales Invoices across all branches for the All Orders page.

	Enforces date range security: if the current user is NOT in All Orders Settings,
	the date range is forced to the POS Profile shift range (ignoring client params).

	Args:
		date_from: Start date (YYYY-MM-DD). Only used if user has date permission.
		date_to: End date (YYYY-MM-DD). Only used if user has date permission.
		limit: Maximum number of invoices to return (default 500)
		search: Optional text (order #, customer name/number, mobile). When given, the
			search runs server-side across the user's FULL allowed date range — so a
			customer's older orders are found, not just those in the current window.

	Returns:
		List of invoices with basic details and items
	"""
	search = (search or "").strip()
	# Check user permission for date selection
	user = frappe.session.user
	can_select = False

	try:
		settings = frappe.get_single("All Orders Settings")
		for row in settings.user_date_ranges or []:
			if row.user == user:
				can_select = True
				break
	except Exception:
		pass

	use_shift_datetime = False

	if can_select:
		# User is allowed to pick dates — use provided or default to today
		if not date_from:
			date_from = nowdate()
		if not date_to:
			date_to = nowdate()

		# Enforce max days limit server-side
		max_days = 0
		try:
			settings = frappe.get_single("All Orders Settings")
			for row in settings.user_date_ranges or []:
				if row.user == user:
					max_days = cint(row.days)
					break
		except Exception:
			pass

		from frappe.utils import add_days

		# A bare customer lookup (searching WITHOUT having picked a date range) looks across
		# a broad history window so a customer's older orders are found. But once the user
		# has EXPLICITLY set a date range (respect_dates), the search must stay INSIDE that
		# range — otherwise the date filter appears to stop working when you type a search.
		if search and not cint(respect_dates):
			date_from = add_days(nowdate(), -SEARCH_LOOKBACK_DAYS)
			date_to = nowdate()
		elif max_days > 0:
			earliest = add_days(nowdate(), -max_days)
			if str(date_from) < earliest:
				date_from = earliest
	else:
		shift_start, shift_end = _get_user_shift_date_range()

	# Branch Access Control: Call Center sees everything, others see their branch
	branch, is_call_center = _get_user_branch_filter_info()
	branch_cond = ""
	branch_params = {}
	if not is_call_center:
		branch_cond = " AND si.branch = %(user_branch)s "
		branch_params["user_branch"] = branch or "___NONE___"

	# Order-type visibility: only Call Center users/roles can see Talabat &
	# Delivery orders; everyone else has them hidden.
	cc_roles = {"CallCenterAgent", "Call center supervisor", "Call center manager", "System Manager"}
	has_cc_role = bool(cc_roles & set(frappe.get_roles(user)))
	order_type_cond = ""
	if not (is_call_center or has_cc_role):
		order_type_cond = " AND IFNULL(si.custom_order_type, '') NOT IN ('Talabat', 'Delivery') "

	# Hide return credit notes and fully-returned originals from the All Orders list.
	# Return credit notes carry mixed DB statuses (Return / Unpaid / Overdue) — the
	# "Return" label is derived from is_return — so filter on the flag, not the status.
	status_cond = " AND IFNULL(si.is_return, 0) = 0 AND IFNULL(si.status, '') != 'Credit Note Issued' "

	# Server-side search (order #, customer name/number, mobile) across the full window.
	search_cond = ""
	if search:
		search_cond = """ AND (
			si.name LIKE %(search)s
			OR si.custom_number_order LIKE %(search)s
			OR si.contact_mobile LIKE %(search)s
			OR si.customer_name LIKE %(search)s
			OR cust.mobile_no LIKE %(search)s
			OR cust.custom_other_mobile_no LIKE %(search)s
			OR si.custom_unique_talbat_number LIKE %(search)s
		) """
		branch_params["search"] = f"%{search}%"

	# A search is a targeted customer lookup — return every match, no row cap.
	limit_clause = "" if search else "LIMIT %(limit)s"

	# Build the query based on whether we're using datetime or date filtering
	if use_shift_datetime:
		# Shift-based: use TIMESTAMP for precise time filtering
		invoices = frappe.db.sql("""
			SELECT
				si.name,
				si.customer,
				si.customer_name,
				si.posting_date,
				si.posting_time,
				si.grand_total,
				si.net_total,
				si.paid_amount,
				si.outstanding_amount,
				si.status,
				si.docstatus,
				si.is_return,
				si.return_against,
				si.is_pos,
				si.pos_profile,
				si.currency,
				si.custom_order_type,
				si.custom_number_order,
				si.custom_receipt_number,
				si.custom_third_party_referance_number,
				si.custom_unique_talbat_number,
				si.branch,
				si.driver,
				si.owner,
				COALESCE(si.custom_is_rejected, 0) AS custom_is_rejected,
				si.custom_payment_type,
				si.custom_rejection_reason,
				COALESCE(cust.mobile_no, '') AS mobile_no,
				COALESCE(cust.custom_other_mobile_no, '') AS other_mobile_no,
				ko.status AS kds_status
			FROM
				`tabSales Invoice` si
				LEFT JOIN `tabCustomer` cust ON cust.name = si.customer
				LEFT JOIN `tabKDS Order` ko ON ko.sales_invoice = si.name
			WHERE
				TIMESTAMP(si.posting_date, si.posting_time) BETWEEN %(shift_start)s AND %(shift_end)s
				AND si.docstatus != 2
				{branch_cond}{order_type_cond}{status_cond}{search_cond}
			ORDER BY
				si.posting_date DESC,
				si.posting_time DESC,
				si.creation DESC
			{limit_clause}
		""".format(branch_cond=branch_cond, order_type_cond=order_type_cond, status_cond=status_cond, search_cond=search_cond, limit_clause=limit_clause), {
			"shift_start": shift_start,
			"shift_end": shift_end,
			"limit": cint(limit),
			**branch_params
		}, as_dict=True)
	else:
		# Date-based: use posting_date for privileged users who pick dates
		invoices = frappe.db.sql("""
			SELECT
				si.name,
				si.customer,
				si.customer_name,
				si.posting_date,
				si.posting_time,
				si.grand_total,
				si.net_total,
				si.paid_amount,
				si.outstanding_amount,
				si.status,
				si.docstatus,
				si.is_return,
				si.return_against,
				si.is_pos,
				si.pos_profile,
				si.currency,
				si.custom_order_type,
				si.custom_number_order,
				si.custom_receipt_number,
				si.custom_third_party_referance_number,
				si.custom_unique_talbat_number,
				si.branch,
				si.driver,
				si.owner,
				COALESCE(si.custom_is_rejected, 0) AS custom_is_rejected,
				si.custom_payment_type,
				si.custom_rejection_reason,
				COALESCE(cust.mobile_no, '') AS mobile_no,
				COALESCE(cust.custom_other_mobile_no, '') AS other_mobile_no,
				ko.status AS kds_status
			FROM
				`tabSales Invoice` si
				LEFT JOIN `tabCustomer` cust ON cust.name = si.customer
				LEFT JOIN `tabKDS Order` ko ON ko.sales_invoice = si.name
			WHERE
				si.posting_date BETWEEN %(date_from)s AND %(date_to)s
				AND si.docstatus != 2
				{branch_cond}{order_type_cond}{status_cond}{search_cond}
			ORDER BY
				si.posting_date DESC,
				si.posting_time DESC,
				si.creation DESC
			{limit_clause}
		""".format(branch_cond=branch_cond, order_type_cond=order_type_cond, status_cond=status_cond, search_cond=search_cond, limit_clause=limit_clause), {
			"date_from": date_from,
			"date_to": date_to,
			"limit": cint(limit),
			**branch_params
		}, as_dict=True)

	# Batch-load items for all invoices
	if invoices:
		invoice_names = [inv.name for inv in invoices]
		placeholders = ", ".join(["%s"] * len(invoice_names))
		items = frappe.db.sql(f"""
			SELECT
				parent,
				item_code,
				item_name,
				qty,
				rate,
				amount,
				uom
			FROM
				`tabSales Invoice Item`
			WHERE
				parent IN ({placeholders})
			ORDER BY
				parent, idx
		""", tuple(invoice_names), as_dict=True)

		# Group items by invoice
		items_map = {}
		for item in items:
			items_map.setdefault(item.parent, []).append(item)

		# Resolve creator (owner) display names in one batch
		owner_ids = list({inv.owner for inv in invoices if inv.get("owner")})
		owner_name_map = {}
		if owner_ids:
			for u in frappe.get_all(
				"User", filters=[["name", "in", owner_ids]], fields=["name", "full_name"]
			):
				owner_name_map[u.name] = u.full_name

		# Latest non-cancelled Delivery Assignment status per invoice (delivery flow)
		da_status_map = {}
		da_rows = frappe.db.sql(f"""
			SELECT da.order_reference, da.status
			FROM `tabDelivery Assignment` da
			INNER JOIN (
				SELECT order_reference, MAX(creation) AS mx
				FROM `tabDelivery Assignment`
				WHERE order_doctype = 'Sales Invoice' AND docstatus != 2
				  AND order_reference IN ({placeholders})
				GROUP BY order_reference
			) latest ON latest.order_reference = da.order_reference AND latest.mx = da.creation
			WHERE da.order_doctype = 'Sales Invoice' AND da.docstatus != 2
		""", tuple(invoice_names), as_dict=True)
		da_status_map = {r.order_reference: r.status for r in da_rows}

		for inv in invoices:
			inv.items = items_map.get(inv.name, [])
			inv.owner_name = owner_name_map.get(inv.owner) or inv.owner
			# Delivery status from the Delivery Assignment (empty for non-delivery orders)
			inv.delivery_status = da_status_map.get(inv.name)

			# Derive a display status
			if inv.docstatus == 0:
				inv.display_status = "Draft"
			elif inv.is_return:
				inv.display_status = "Return"
			elif inv.outstanding_amount > 0:
				inv.display_status = "Unpaid"
			elif inv.status == "Paid":
				inv.display_status = "Paid"
			else:
				inv.display_status = inv.status or "Submitted"

	return invoices


@frappe.whitelist()
def get_active_drivers():
	"""
	Get all drivers with status 'Active'.

	Returns:
		List of dicts with name and full_name for each active driver.
	"""
	drivers = frappe.get_all(
		"Driver",
		filters={"status": "Active"},
		fields=["name", "full_name"],
		order_by="full_name asc",
		limit_page_length=0,
	)
	return drivers


@frappe.whitelist()
def assign_driver_to_invoice(invoice_name, driver):
	"""
	Assign a driver to a Sales Invoice.

	Args:
		invoice_name: Sales Invoice name
		driver: Driver name (ID) to assign

	Returns:
		dict with success message
	"""
	if not invoice_name or not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_("Invoice {0} does not exist").format(invoice_name))

	if driver and not frappe.db.exists("Driver", driver):
		frappe.throw(_("Driver {0} does not exist").format(driver))

	frappe.db.set_value("Sales Invoice", invoice_name, "driver", driver or "")
	frappe.db.commit()

	# Emit realtime event so other open AllOrders pages refresh
	try:
		pos_profile = frappe.db.get_value("Sales Invoice", invoice_name, "pos_profile") or ""
		frappe.publish_realtime(
			event="pos_order_changed",
			message={
				"invoice_name": invoice_name,
				"action": "update",
				"pos_profile": pos_profile,
				"timestamp": frappe.utils.now(),
			},
			user=None,
			after_commit=True,
		)
	except Exception:
		pass

	driver_name = ""
	if driver:
		driver_name = frappe.db.get_value("Driver", driver, "full_name") or driver

	return {"message": _("Driver {0} assigned to {1}").format(driver_name, invoice_name)}


@frappe.whitelist()
def convert_order_type(invoice_name, order_type):
	allowed = ("Delivery", "Pickup", "Dine In")
	if order_type not in allowed:
		frappe.throw(_("Invalid order type: {0}").format(order_type))
	if not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_("Invoice {0} not found").format(invoice_name))
	frappe.db.set_value("Sales Invoice", invoice_name, "custom_order_type", order_type)
	frappe.db.commit()
	try:
		pos_profile = frappe.db.get_value("Sales Invoice", invoice_name, "pos_profile") or ""
		frappe.publish_realtime(
			event="pos_order_changed",
			message={"invoice_name": invoice_name, "action": "update", "pos_profile": pos_profile},
			after_commit=True,
		)
	except Exception:
		pass
	return {"status": "success"}


@frappe.whitelist()
def get_all_order_items(invoice_name):
	"""
	Get items for a specific Sales Invoice.

	Args:
		invoice_name: Sales Invoice name

	Returns:
		List of items with details
	"""
	if not invoice_name or not frappe.db.exists("Sales Invoice", invoice_name):
		frappe.throw(_("Invoice not found"))

	items = frappe.db.sql("""
		SELECT
			item_code,
			item_name,
			qty,
			rate,
			amount,
			uom
		FROM
			`tabSales Invoice Item`
		WHERE
			parent = %(invoice_name)s
		ORDER BY
			idx
	""", {"invoice_name": invoice_name}, as_dict=True)

	return items



@frappe.whitelist()
def get_need_my_action_orders():
	user = frappe.session.user
	branch, is_call_center = _get_user_branch_filter_info()

	branch_cond = ""
	branch_params = {}
	if not is_call_center:
		branch_cond = " AND si.branch = %(user_branch)s "
		branch_params["user_branch"] = branch or "___NONE___"

	invoices = frappe.db.sql("""
		SELECT
			si.name,
			si.customer,
			si.customer_name,
			si.posting_date,
			si.posting_time,
			si.grand_total,
			si.net_total,
			si.paid_amount,
			si.outstanding_amount,
			si.status,
			si.docstatus,
			si.is_return,
			si.return_against,
			si.is_pos,
			si.pos_profile,
			si.currency,
			si.custom_order_type,
			si.custom_number_order,
			si.custom_receipt_number,
			si.custom_third_party_referance_number,
			si.custom_unique_talbat_number,
			si.branch,
			si.driver,
			COALESCE(NULLIF(si.contact_mobile, ''), cust.mobile_no) AS mobile_no,
			cust.custom_other_mobile_no AS other_mobile_no
		FROM
			`tabSales Invoice` si
			LEFT JOIN `tabCustomer` cust ON cust.name = si.customer
		WHERE
			si.docstatus = 0
			AND (COALESCE(si.custom_is_rejected, 0) = 0)
			AND (COALESCE(si.custom_order_type, '') != 'Talabat')
			AND (LOWER(si.pos_profile) LIKE '%%call center%%' OR EXISTS(
				SELECT 1 FROM `tabTag Link` tl WHERE tl.document_type='Sales Invoice' AND tl.document_name=si.name AND tl.tag='Call Center'
			))
			{branch_cond}
		ORDER BY
			si.posting_date DESC,
			si.posting_time DESC,
			si.creation DESC
	""".format(branch_cond=branch_cond), branch_params, as_dict=True)

	# Batch-load items for all invoices
	if invoices:
		invoice_names = [inv.name for inv in invoices]
		placeholders = ", ".join(["%s"] * len(invoice_names))
		items = frappe.db.sql(f"""
			SELECT
				parent,
				item_code,
				item_name,
				qty,
				rate,
				amount,
				uom,
				warehouse
			FROM
				`tabSales Invoice Item`
			WHERE
				parent IN ({placeholders})
			ORDER BY
				parent, idx
		""", tuple(invoice_names), as_dict=True)

		items_map = {}
		for item in items:
			items_map.setdefault(item.parent, []).append(item)

		for inv in invoices:
			inv.items = items_map.get(inv.name, [])
			inv.display_status = "Draft"

	return invoices


# ==========================================
# Draft Invoice Management
# ==========================================


@frappe.whitelist()
def get_draft_invoices(pos_opening_shift, doctype="Sales Invoice"):
    """Get all draft invoices for a POS opening shift."""
    filters = {
        "docstatus": 0,
    }

    # Add pos_opening_shift filter if the field exists
    if frappe.db.has_column(doctype, "pos_opening_shift"):
        filters["pos_opening_shift"] = pos_opening_shift

    # Performance: Get all invoice names first
    invoices_list = frappe.get_list(
        doctype,
        filters=filters,
        fields=["name"],
        limit_page_length=0,
        order_by="modified desc",
    )

    # Performance: Batch load all documents at once using get_cached_doc
    # This leverages Frappe's internal caching and is faster than individual queries
    data = []
    for invoice in invoices_list:
        data.append(frappe.get_cached_doc(doctype, invoice["name"]))

    return data

@frappe.whitelist()
def get_unpaid_invoice_for_table(table_number):
    """Get the latest unpaid Sales Invoice for a given table."""
    invoice_name = frappe.db.get_value(
        "Sales Invoice",
        {
            "custom_table_number": table_number,
            "docstatus": 1,
            "custom_order_type": "Dine In",
            "outstanding_amount": (">", 0)
        },
        "name",
        order_by="modified desc"
    )
    if invoice_name:
        return frappe.get_cached_doc("Sales Invoice", invoice_name).as_dict()
    return None


@frappe.whitelist()
def delete_invoice(invoice):
    """Delete draft invoice."""
    doctype = "Sales Invoice"

    if not frappe.db.exists(doctype, invoice):
        frappe.throw(_("Invoice {0} does not exist").format(invoice))

    # Check if it's a draft
    if frappe.db.get_value(doctype, invoice, "docstatus") != 0:
        frappe.throw(_("Cannot delete submitted invoice {0}").format(invoice))

    frappe.delete_doc(doctype, invoice, force=1)
    return _("Invoice {0} Deleted").format(invoice)


@frappe.whitelist()
def reject_order_payment(invoice_name, reason=None):
    """Flag a Call Center draft order as rejected without deleting it."""
    doctype = "Sales Invoice"

    if not frappe.db.exists(doctype, invoice_name):
        frappe.throw(_("Invoice {0} does not exist").format(invoice_name))

    if frappe.db.get_value(doctype, invoice_name, "docstatus") != 0:
        frappe.throw(_("Cannot reject a submitted invoice {0}").format(invoice_name))

    frappe.db.set_value(
        doctype,
        invoice_name,
        {
            "custom_is_rejected": 1,
            "custom_rejection_reason": reason or "",
        },
        update_modified=True,
    )
    frappe.db.commit()

    # db.set_value bypasses document hooks, so emit the realtime event manually
    try:
        pos_profile = frappe.db.get_value(doctype, invoice_name, "pos_profile") or ""
        frappe.publish_realtime(
            event="pos_order_changed",
            message={
                "invoice_name": invoice_name,
                "action": "reject",
                "docstatus": 0,
                "pos_profile": pos_profile,
                "timestamp": frappe.utils.now(),
            },
            user=None,
            after_commit=True,
        )
    except Exception:
        pass

    return {"message": _("Order {0} has been rejected").format(invoice_name)}


@frappe.whitelist()
def return_order_to_need_my_action(invoice_name, payment_type=None, receipt_number=None):
    """
    Clear the 'rejected' flag on a Call Center draft so it reappears in Need My Action.

    When a draft is rejected from Need My Action, custom_is_rejected is set to 1 and the
    order drops off the list. It has no other way back, so this restores it. Only drafts
    (docstatus 0) can be returned — a submitted invoice is no longer awaiting checkout.

    The Call Center may correct the expected payment type (custom_payment_type) and the
    receipt number (custom_receipt_number) while returning the order so the cashier can
    complete checkout with the right details.
    """
    doctype = "Sales Invoice"

    if not frappe.db.exists(doctype, invoice_name):
        frappe.throw(_("Invoice {0} does not exist").format(invoice_name))

    if frappe.db.get_value(doctype, invoice_name, "docstatus") != 0:
        frappe.throw(_("Only draft orders can be returned to Need My Action ({0}).").format(invoice_name))

    updates = {
        "custom_is_rejected": 0,
        "custom_rejection_reason": "",
    }
    if payment_type is not None:
        updates["custom_payment_type"] = payment_type
    if receipt_number is not None:
        updates["custom_receipt_number"] = receipt_number

    frappe.db.set_value(doctype, invoice_name, updates, update_modified=True)
    frappe.db.commit()

    # db.set_value bypasses document hooks, so emit the realtime event manually
    try:
        pos_profile = frappe.db.get_value(doctype, invoice_name, "pos_profile") or ""
        frappe.publish_realtime(
            event="pos_order_changed",
            message={
                "invoice_name": invoice_name,
                "action": "return_to_action",
                "docstatus": 0,
                "pos_profile": pos_profile,
                "timestamp": frappe.utils.now(),
            },
            user=None,
            after_commit=True,
        )
    except Exception:
        pass

    return {"message": _("Order {0} returned to Need My Action").format(invoice_name)}


@frappe.whitelist()
def cleanup_old_drafts(pos_profile=None, max_age_hours=24):
    """
    Clean up old draft invoices to prevent stock reservation issues.
    Deletes drafts older than max_age_hours (default 24 hours).

    Uses batch SQL delete instead of per-document ORM delete for performance.
    Draft invoices (docstatus=0) have no GL/stock/payment ledger entries,
    so direct SQL is safe.
    """
    from datetime import datetime, timedelta

    cutoff_time = datetime.now() - timedelta(hours=int(max_age_hours))
    cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")

    # Build WHERE clause
    conditions = "si.docstatus = 0 AND si.modified < %(cutoff)s"
    params = {"cutoff": cutoff_str}

    if pos_profile:
        conditions += " AND si.pos_profile = %(pos_profile)s"
        params["pos_profile"] = pos_profile

    # Get draft names (limit 200 per run for safety)
    draft_names = frappe.db.sql(
        f"SELECT name FROM `tabSales Invoice` si WHERE {conditions} LIMIT 200",
        params,
        pluck="name",
    )

    if not draft_names:
        return {"deleted": 0, "message": "No old drafts to clean up"}

    placeholders = ", ".join(["%s"] * len(draft_names))

    # Batch delete child tables
    child_tables = [
        "Sales Invoice Item",
        "Sales Invoice Payment",
        "Sales Taxes and Charges",
        "Payment Schedule",
        "Sales Invoice Timesheet",
    ]
    for table in child_tables:
        frappe.db.sql(
            f"DELETE FROM `tab{table}` WHERE parent IN ({placeholders}) AND parenttype='Sales Invoice'",
            draft_names,
        )

    # Clean up metadata
    frappe.db.sql(
        f"DELETE FROM `tabComment` WHERE reference_doctype='Sales Invoice' AND reference_name IN ({placeholders})",
        draft_names,
    )
    frappe.db.sql(
        f"DELETE FROM `tabVersion` WHERE ref_doctype='Sales Invoice' AND docname IN ({placeholders})",
        draft_names,
    )

    # Delete parent records (re-check docstatus=0 for safety)
    frappe.db.sql(
        f"DELETE FROM `tabSales Invoice` WHERE name IN ({placeholders}) AND docstatus = 0",
        draft_names,
    )

    frappe.db.commit()

    # Bulk clear document cache (cheaper than per-doc clearing for large batches)
    if len(draft_names) > 10:
        frappe.cache.delete_keys("Sales Invoice::*")
    else:
        for name in draft_names:
            frappe.clear_document_cache("Sales Invoice", name)

    return {
        "deleted": len(draft_names),
        "message": f"Cleaned up {len(draft_names)} old draft invoices",
    }


# ==========================================
# Return Invoice Management
# ==========================================


@frappe.whitelist()
def get_returnable_invoices(limit=50, pos_profile=None):
    """Get list of invoices that have items available for return.
    Filters by return validity period if configured in POS Settings.

    Uses query builder with LEFT JOINs to calculate original and returned quantities
    in a single query. Returns invoices where total_original_qty > total_returned_qty.
    """
    from frappe.query_builder.functions import Sum, Coalesce, Abs
    from frappe.query_builder import Case
    from frappe.utils import add_days, today

    # Check return validity days from POS Settings
    return_validity_days = 0
    if pos_profile:
        return_validity_days = cint(
            frappe.db.get_value(
                "POS Settings",
                {"pos_profile": pos_profile},
                "return_validity_days"
            ) or 0
        )

    # Define tables
    si = frappe.qb.DocType("Sales Invoice")
    si_item = frappe.qb.DocType("Sales Invoice Item")
    ret_si = frappe.qb.DocType("Sales Invoice").as_("ret_si")
    ret_item = frappe.qb.DocType("Sales Invoice Item").as_("ret_item")

    # Build query with query builder
    query = (
        frappe.qb.from_(si)
        .left_join(si_item).on(si_item.parent == si.name)
        .left_join(ret_si).on(
            (ret_si.return_against == si.name)
            & (ret_si.docstatus == 1)
            & (ret_si.is_return == 1)
        )
        .left_join(ret_item).on(
            (ret_item.parent == ret_si.name)
            & ((ret_item.sales_invoice_item == si_item.name) | (ret_item.item_code == si_item.item_code))
        )
        .select(
            si.name,
            si.customer,
            si.customer_name,
            si.contact_mobile,
            si.posting_date,
            si.grand_total,
            si.status,
            Coalesce(Sum(Case().when(ret_item.qty.isnotnull(), Abs(ret_item.qty)).else_(0)), 0).as_("total_returned_qty"),
            Coalesce(Sum(Case().when(si_item.qty.isnotnull(), si_item.qty).else_(0)), 0).as_("total_original_qty"),
        )
        .where(
            (si.docstatus == 1)
            & (si.is_return == 0)
            & (si.is_pos == 1)
        )
        .groupby(si.name)
        .orderby(si.posting_date, order=frappe.qb.desc)
        .orderby(si.creation, order=frappe.qb.desc)
        .limit(cint(limit))
    )

    # Add date filter if return validity is configured
    if return_validity_days > 0:
        cutoff_date = add_days(today(), -return_validity_days)
        query = query.where(si.posting_date >= cutoff_date)

    # Execute and filter results with HAVING equivalent (post-filter)
    results = query.run(as_dict=True)

    # Filter: only include invoices where original qty > returned qty
    returnable_invoices = [
        inv for inv in results
        if flt(inv.get("total_original_qty", 0)) > flt(inv.get("total_returned_qty", 0))
    ]

    return returnable_invoices


@frappe.whitelist()
def search_invoice_by_number(search_term, pos_profile=None):
    """Search for invoices by invoice number across the entire database.
    No date restrictions - searches all returnable invoices matching the term.

    Uses query builder with LEFT JOINs to calculate remaining returnable quantities.
    Only returns invoices that have items available for return.

    Args:
        search_term: Invoice number or partial number to search for (min 3 chars)
        pos_profile: Optional POS profile for context (reserved for future use)

    Returns:
        List of matching invoices with return availability info (max 10 results)
    """
    from frappe.query_builder.functions import Sum, Coalesce, Abs
    from frappe.query_builder import Case

    if not search_term or len(search_term) < 3:
        return []

    search_term = cstr(search_term).strip()

    # Define tables
    si = frappe.qb.DocType("Sales Invoice")
    si_item = frappe.qb.DocType("Sales Invoice Item")
    ret_si = frappe.qb.DocType("Sales Invoice").as_("ret_si")
    ret_item = frappe.qb.DocType("Sales Invoice Item").as_("ret_item")

    # Build query with query builder
    query = (
        frappe.qb.from_(si)
        .left_join(si_item).on(si_item.parent == si.name)
        .left_join(ret_si).on(
            (ret_si.return_against == si.name)
            & (ret_si.docstatus == 1)
            & (ret_si.is_return == 1)
        )
        .left_join(ret_item).on(
            (ret_item.parent == ret_si.name)
            & ((ret_item.sales_invoice_item == si_item.name) | (ret_item.item_code == si_item.item_code))
        )
        .select(
            si.name,
            si.customer,
            si.customer_name,
            si.contact_mobile,
            si.posting_date,
            si.grand_total,
            si.status,
            Coalesce(Sum(Case().when(ret_item.qty.isnotnull(), Abs(ret_item.qty)).else_(0)), 0).as_("total_returned_qty"),
            Coalesce(Sum(Case().when(si_item.qty.isnotnull(), si_item.qty).else_(0)), 0).as_("total_original_qty"),
        )
        .where(
            (si.docstatus == 1)
            & (si.is_return == 0)
            & (si.is_pos == 1)
            & (si.name.like(f"%{search_term}%"))
        )
        .groupby(si.name)
        .orderby(si.posting_date, order=frappe.qb.desc)
        .orderby(si.creation, order=frappe.qb.desc)
        .limit(10)
    )

    results = query.run(as_dict=True)

    # Filter: only include invoices where original qty > returned qty
    matching_invoices = [
        inv for inv in results
        if flt(inv.get("total_original_qty", 0)) > flt(inv.get("total_returned_qty", 0))
    ]

    return matching_invoices


@frappe.whitelist()
def check_invoice_return_validity(invoice_name):
    """Check if an invoice is within the return validity period.

    Returns detailed information for the UI to display, including:
    - valid: Boolean indicating if return is allowed
    - error_type: 'not_found' or 'return_period_expired' if invalid
    - Additional context (invoice_date, days_since, allowed_days) for expired returns
    """
    from frappe.utils import date_diff, getdate, formatdate

    # Fetch only the fields needed for validation
    si = frappe.qb.DocType("Sales Invoice")
    invoice_data = (
        frappe.qb.from_(si)
        .select(si.pos_profile, si.posting_date)
        .where(si.name == invoice_name)
    ).run(as_dict=True)

    if not invoice_data:
        return {
            "valid": False,
            "error_type": "not_found",
            "message": _("Invoice {0} does not exist").format(invoice_name)
        }

    invoice_info = invoice_data[0]

    # Check return validity period from POS Settings
    if invoice_info.pos_profile:
        return_validity_days = cint(
            frappe.db.get_value(
                "POS Settings",
                {"pos_profile": invoice_info.pos_profile},
                "return_validity_days"
            ) or 0
        )

        if return_validity_days > 0:
            days_since_invoice = date_diff(getdate(nowdate()), getdate(invoice_info.posting_date))
            if days_since_invoice > return_validity_days:
                return {
                    "valid": False,
                    "error_type": "return_period_expired",
                    "invoice_name": invoice_name,
                    "invoice_date": formatdate(invoice_info.posting_date),
                    "days_since": days_since_invoice,
                    "allowed_days": return_validity_days,
                    "message": _("Return period has expired")
                }

    return {"valid": True}


@frappe.whitelist()
def get_invoice_for_return(invoice_name):
    """Get invoice with return tracking - calculates remaining qty for each item.
    Also validates return validity period based on POS Settings.

    Returns the full invoice document with each item's qty adjusted to show
    only the remaining returnable quantity (original qty minus already returned).
    """
    from frappe.utils import date_diff, getdate
    from frappe.query_builder.functions import Sum, Abs, Coalesce

    # Validate invoice exists and get fields needed for return period check
    si = frappe.qb.DocType("Sales Invoice")
    invoice_check = (
        frappe.qb.from_(si)
        .select(si.pos_profile, si.posting_date)
        .where(si.name == invoice_name)
    ).run(as_dict=True)

    if not invoice_check:
        frappe.throw(_("Invoice {0} does not exist").format(invoice_name))

    invoice_info = invoice_check[0]

    # Check return validity period from POS Settings
    if invoice_info.pos_profile:
        return_validity_days = cint(
            frappe.db.get_value(
                "POS Settings",
                {"pos_profile": invoice_info.pos_profile},
                "return_validity_days"
            ) or 0
        )

        if return_validity_days > 0:
            days_since_invoice = date_diff(getdate(nowdate()), getdate(invoice_info.posting_date))
            if days_since_invoice > return_validity_days:
                frappe.throw(
                    _("Return period has expired. Invoice {0} was created {1} days ago. "
                      "Returns are only allowed within {2} days of purchase.").format(
                        invoice_name, days_since_invoice, return_validity_days
                    )
                )

    # Aggregate quantities already returned from previous return invoices.
    # Uses COALESCE to match by sales_invoice_item (row ID) first, then item_code as fallback.
    ret_si = frappe.qb.DocType("Sales Invoice")
    ret_item = frappe.qb.DocType("Sales Invoice Item")

    returned_qty_results = (
        frappe.qb.from_(ret_si)
        .inner_join(ret_item).on(ret_item.parent == ret_si.name)
        .select(
            Coalesce(ret_item.sales_invoice_item, ret_item.item_code).as_("key_field"),
            Sum(Abs(ret_item.qty)).as_("returned_qty")
        )
        .where(
            (ret_si.return_against == invoice_name)
            & (ret_si.docstatus == 1)
            & (ret_si.is_return == 1)
        )
        .groupby(Coalesce(ret_item.sales_invoice_item, ret_item.item_code))
    ).run(as_dict=True)

    returned_qty = {row["key_field"]: flt(row["returned_qty"]) for row in returned_qty_results}

    if not invoice_name or invoice_name in ["None", "null", "", False]:
        frappe.throw(_("Invoice {0} does not exist").format(invoice_name))

    # Get the full invoice document (needed for complete response)
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    invoice_dict = invoice.as_dict()

    # Calculate remaining quantities
    updated_items = []
    for item in invoice_dict.get("items", []):
        # Check how much has been returned using the item's name (row ID)
        already_returned = returned_qty.get(item.name, 0)
        remaining_qty = flt(item.qty) - already_returned

        if remaining_qty > 0:
            item_copy = item.copy()
            item_copy["original_qty"] = item.qty
            item_copy["qty"] = remaining_qty
            item_copy["already_returned"] = already_returned
            updated_items.append(item_copy)

    invoice_dict["items"] = updated_items
    return invoice_dict


def _parse_item_wise_tax_detail(raw_detail):
    """Parse item_wise_tax_detail from string or dict format."""
    if not raw_detail:
        return {}
    if isinstance(raw_detail, str):
        return json.loads(raw_detail)
    return raw_detail


def _build_item_tax_map(taxes: list) -> dict:
    """Build item_code -> tax_amount map from taxes child table.

    Args:
        taxes: List of tax row dicts containing item_wise_tax_detail

    Returns:
        Dict mapping item_code to total tax amount (absolute value)

    Note:
        item_wise_tax_detail format: {"ITEM-CODE": [tax_rate, tax_amount]}
        Return documents have negative amounts, hence abs() is used.
    """
    from collections import defaultdict
    tax_map = defaultdict(float)

    for tax_row in taxes:
        try:
            details = _parse_item_wise_tax_detail(tax_row.get("item_wise_tax_detail"))
            for item_code, (_, tax_amount) in details.items():
                tax_map[item_code] += abs(flt(tax_amount))
        except (json.JSONDecodeError, TypeError, ValueError, KeyError):
            continue

    return dict(tax_map)


@frappe.whitelist()
def prepare_return_invoice(invoice_name, pos_opening_shift=None):
    """Prepare a return invoice using ERPNext's make_sales_return.

    This uses ERPNext's standard return document creation which properly copies
    all child tables including:
    - sales_team: For correct commission reversal on returned items
    - taxes: For correct tax reversal
    - Other child tables maintained by ERPNext

    The function validates:
    - Invoice exists and is submitted (docstatus = 1)
    - Invoice is not already a return
    - Return is within the validity period (if configured in POS Settings)

    Args:
        invoice_name: The original Sales Invoice name to create return against
        pos_opening_shift: The current POS Opening Shift name

    Returns:
        dict: The prepared return invoice document with:
            - items: Only items with remaining_qty > 0 (not fully returned)
            - _original_invoice: Reference data from original invoice (payments, amounts)
            - Each item includes original_qty, already_returned, and remaining_qty
    """
    from frappe.utils import date_diff, getdate
    from frappe.query_builder.functions import Sum, Abs, Coalesce
    from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return

    # Validate invoice and get fields needed for return period check
    si = frappe.qb.DocType("Sales Invoice")
    invoice_check = (
        frappe.qb.from_(si)
        .select(
            si.docstatus,
            si.is_return,
            si.pos_profile,
            si.posting_date,
            si.is_pos,
            si.grand_total,
            si.paid_amount,
            si.outstanding_amount,
            si.customer,
            si.customer_name,
            si.net_total,
            si.total_taxes_and_charges
        )
        .where(si.name == invoice_name)
    ).run(as_dict=True)

    if not invoice_check:
        frappe.throw(_("Invoice {0} does not exist").format(invoice_name))

    invoice_info = invoice_check[0]

    # Validate docstatus
    if invoice_info.docstatus != 1:
        frappe.throw(_("Invoice must be submitted to create a return"))

    # Check if it's already a return
    if invoice_info.is_return:
        frappe.throw(_("Cannot create return against a return invoice"))

    # Check return validity period from POS Settings
    if invoice_info.pos_profile:
        return_validity_days = cint(
            frappe.db.get_value(
                "POS Settings",
                {"pos_profile": invoice_info.pos_profile},
                "return_validity_days"
            ) or 0
        )

        if return_validity_days > 0:
            days_since_invoice = date_diff(getdate(nowdate()), getdate(invoice_info.posting_date))
            if days_since_invoice > return_validity_days:
                frappe.throw(
                    _("Return period has expired. Invoice {0} was created {1} days ago. "
                      "Returns are only allowed within {2} days of purchase.").format(
                        invoice_name, days_since_invoice, return_validity_days
                    )
                )

    # Use ERPNext's make_sales_return to create properly mapped return document
    # This automatically copies sales_team, taxes, and other child tables.
    # get_mapped_doc enforces "create" permission on Sales Invoice for the SESSION user,
    # which POS cashiers / call-center staff don't hold — elevate to Administrator around
    # ONLY the mapping call (nothing is saved here), then restore the real user.
    _mapping_user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        return_doc = make_sales_return(invoice_name)
    finally:
        frappe.set_user(_mapping_user)

    # Set POS-specific fields
    if pos_opening_shift:
        return_doc.posa_pos_opening_shift = pos_opening_shift

    # Ensure POS flags are set
    return_doc.is_pos = invoice_info.is_pos
    return_doc.pos_profile = invoice_info.pos_profile

    # Aggregate quantities already returned from previous return invoices
    ret_si = frappe.qb.DocType("Sales Invoice")
    ret_item = frappe.qb.DocType("Sales Invoice Item")

    returned_qty_results = (
        frappe.qb.from_(ret_si)
        .inner_join(ret_item).on(ret_item.parent == ret_si.name)
        .select(
            Coalesce(ret_item.sales_invoice_item, ret_item.item_code).as_("key_field"),
            Sum(Abs(ret_item.qty)).as_("returned_qty")
        )
        .where(
            (ret_si.return_against == invoice_name)
            & (ret_si.docstatus == 1)
            & (ret_si.is_return == 1)
        )
        .groupby(Coalesce(ret_item.sales_invoice_item, ret_item.item_code))
    ).run(as_dict=True)

    returned_qty_map = {row["key_field"]: flt(row["returned_qty"]) for row in returned_qty_results}

    # Convert to dict and update items with remaining quantities
    return_dict = return_doc.as_dict()

    # Fetch original invoice payments for refund handling in frontend
    si_payment = frappe.qb.DocType("Sales Invoice Payment")
    payments_data = (
        frappe.qb.from_(si_payment)
        .select(
            si_payment.mode_of_payment,
            si_payment.amount,
            si_payment.base_amount,
            si_payment.account
        )
        .where(si_payment.parent == invoice_name)
    ).run(as_dict=True)

    # Include original invoice data for reference (payments, amounts, etc.)
    return_dict["_original_invoice"] = {
        "name": invoice_name,
        "grand_total": invoice_info.grand_total,
        "paid_amount": invoice_info.paid_amount,
        "outstanding_amount": invoice_info.outstanding_amount,
        "customer": invoice_info.customer,
        "customer_name": invoice_info.customer_name,
        "posting_date": invoice_info.posting_date,
        "payments": payments_data,
        "net_total": invoice_info.net_total,
        "total_taxes_and_charges": invoice_info.total_taxes_and_charges,
    }

    item_tax_map = _build_item_tax_map(return_dict.get("taxes", []))

    # Check if taxes are inclusive by inspecting the tax rows copied from the original
    # invoice (immutable after submission, unlike POS Settings which can change later).
    # Only consider percentage-based taxes (On Net Total, etc.) — Actual charge types
    # are never inclusive (same logic as sales_invoice_hooks.apply_tax_inclusive).
    applicable_taxes = [
        tax for tax in return_dict.get("taxes", [])
        if tax.get("charge_type") != "Actual"
    ]
    tax_inclusive = bool(applicable_taxes) and all(
        tax.get("included_in_print_rate") for tax in applicable_taxes
    )

    precision = cint(frappe.get_cached_value("System Settings", None, "currency_precision")) or 2

    def process_return_item(item):
        """Process single item for return, returns None if not returnable."""
        item_ref = item.get("sales_invoice_item") or item.get("item_code")
        original_qty = abs(flt(item.get("qty", 0)))
        remaining_qty = original_qty - returned_qty_map.get(item_ref, 0)

        if remaining_qty <= 0:
            return None

        # Get rate breakdown for display
        price_list_rate = flt(item.get("price_list_rate") or item.get("rate"), precision)
        net_rate = flt(item.get("net_rate") or item.get("rate"), precision)
        tax_per_unit = flt(item_tax_map.get(item.get("item_code"), 0) / original_qty, precision) if original_qty else 0

        # For inclusive taxes, use the original rate (already includes tax) to prevent
        # ERPNext from back-calculating and double-reducing the tax.
        # For exclusive taxes, use net_rate as before.
        if tax_inclusive:
            item_rate = flt(item.get("rate"), precision)
            rate_with_tax = item_rate
            # Both price_list_rate and rate are tax-inclusive, so discount is their difference
            discount_per_unit = flt(price_list_rate - item_rate, precision)
        else:
            item_rate = net_rate
            rate_with_tax = flt(net_rate + tax_per_unit, precision)
            discount_per_unit = flt(price_list_rate - net_rate, precision)

        return {
            **item,
            "original_qty": original_qty,
            "already_returned": original_qty - remaining_qty,
            "remaining_qty": remaining_qty,
            "qty": -remaining_qty,
            "price_list_rate": price_list_rate,
            "rate": item_rate,
            "discount_per_unit": discount_per_unit,
            "amount": flt(item_rate * -remaining_qty, precision),
            "tax_per_unit": tax_per_unit,
            "rate_with_tax": rate_with_tax,
            "tax_included_in_rate": tax_inclusive,
        }

    return_dict["items"] = [
        processed for item in return_dict.get("items", [])
        if (processed := process_return_item(item)) is not None
    ]

    # Check if all items have been fully returned
    if not return_dict["items"]:
        frappe.throw(_("All items from this invoice have already been returned"))

    return return_dict


@frappe.whitelist()
def search_invoices_for_return(
    invoice_name=None,
    company=None,
    customer_name=None,
    customer_id=None,
    mobile_no=None,
    from_date=None,
    to_date=None,
    min_amount=None,
    max_amount=None,
    page=1,
    doctype="Sales Invoice",
):
    """Search for invoices that can be returned with pagination.

    Supports filtering by:
    - invoice_name: Partial match on invoice number
    - company: Exact match
    - customer_name, customer_id, mobile_no: Partial match (OR condition)
    - from_date, to_date: Date range
    - min_amount, max_amount: Amount range

    Returns invoices with their items adjusted to show remaining returnable quantities.
    """
    from frappe.query_builder.functions import Sum, Abs, Count

    page = cint(page) or 1
    page_length = 100
    start = (page - 1) * page_length

    # Build main invoice query
    si = frappe.qb.DocType(doctype)

    # Start building the query
    query = (
        frappe.qb.from_(si)
        .select(
            si.name,
            si.customer,
            si.customer_name,
            si.posting_date,
            si.grand_total,
            si.status
        )
        .where(
            (si.docstatus == 1)
            & (si.is_return == 0)
        )
        .orderby(si.posting_date, order=frappe.qb.desc)
        .orderby(si.name, order=frappe.qb.desc)
        .limit(page_length)
        .offset(start)
    )

    # Add company filter
    if company:
        query = query.where(si.company == company)

    # Add invoice name filter
    if invoice_name:
        query = query.where(si.name.like(f"%{invoice_name}%"))

    # Add date range filters
    if from_date and to_date:
        query = query.where(si.posting_date.between(from_date, to_date))
    elif from_date:
        query = query.where(si.posting_date >= from_date)
    elif to_date:
        query = query.where(si.posting_date <= to_date)

    # Add amount filters
    if min_amount and max_amount:
        query = query.where(si.grand_total.between(float(min_amount), float(max_amount)))
    elif min_amount:
        query = query.where(si.grand_total >= float(min_amount))
    elif max_amount:
        query = query.where(si.grand_total <= float(max_amount))

    # Search customers matching any of the provided criteria (OR logic)
    if customer_name or customer_id or mobile_no:
        cust = frappe.qb.DocType("Customer")
        cust_query = frappe.qb.from_(cust).select(cust.name).limit(100)

        # Build OR conditions for customer search
        cust_conditions = []
        if customer_name:
            cust_conditions.append(cust.customer_name.like(f"%{customer_name}%"))
        if customer_id:
            cust_conditions.append(cust.name.like(f"%{customer_id}%"))
        if mobile_no:
            cust_conditions.append(cust.mobile_no.like(f"%{mobile_no}%"))

        # Combine with OR
        if cust_conditions:
            combined_condition = cust_conditions[0]
            for cond in cust_conditions[1:]:
                combined_condition = combined_condition | cond
            cust_query = cust_query.where(combined_condition)

        customers = cust_query.run(as_dict=True)
        customer_ids = [c.name for c in customers]

        if customer_ids:
            query = query.where(si.customer.isin(customer_ids))
        else:
            return {"invoices": [], "has_more": False}

    # Execute main query
    invoices_list = query.run(as_dict=True)

    if not invoices_list:
        return {"invoices": [], "has_more": False}

    invoice_names = [inv["name"] for inv in invoices_list]

    # Count total matching invoices for pagination
    count_query = (
        frappe.qb.from_(si)
        .select(Count(si.name).as_("total"))
        .where(
            (si.docstatus == 1)
            & (si.is_return == 0)
        )
    )

    # Re-apply the same filters for count
    if company:
        count_query = count_query.where(si.company == company)
    if invoice_name:
        count_query = count_query.where(si.name.like(f"%{invoice_name}%"))
    if from_date and to_date:
        count_query = count_query.where(si.posting_date.between(from_date, to_date))
    elif from_date:
        count_query = count_query.where(si.posting_date >= from_date)
    elif to_date:
        count_query = count_query.where(si.posting_date <= to_date)
    if min_amount and max_amount:
        count_query = count_query.where(si.grand_total.between(float(min_amount), float(max_amount)))
    elif min_amount:
        count_query = count_query.where(si.grand_total >= float(min_amount))
    elif max_amount:
        count_query = count_query.where(si.grand_total <= float(max_amount))
    if customer_name or customer_id or mobile_no:
        if customer_ids:
            count_query = count_query.where(si.customer.isin(customer_ids))

    count_result = count_query.run(as_dict=True)
    total_count = count_result[0].total if count_result else 0

    # Batch fetch returned quantities for all invoices in current page
    ret_si = frappe.qb.DocType(doctype)
    ret_item = frappe.qb.DocType(f"{doctype} Item")

    returned_qty_results = (
        frappe.qb.from_(ret_si)
        .inner_join(ret_item).on(ret_item.parent == ret_si.name)
        .select(
            ret_si.return_against.as_("invoice_name"),
            ret_item.item_code,
            Sum(Abs(ret_item.qty)).as_("returned_qty")
        )
        .where(
            (ret_si.return_against.isin(invoice_names))
            & (ret_si.docstatus == 1)
            & (ret_si.is_return == 1)
        )
        .groupby(ret_si.return_against, ret_item.item_code)
    ).run(as_dict=True)

    # Build a map of invoice_name -> {item_code: returned_qty}
    returned_qty_map = {}
    for row in returned_qty_results:
        inv_name = row["invoice_name"]
        if inv_name not in returned_qty_map:
            returned_qty_map[inv_name] = {}
        returned_qty_map[inv_name][row["item_code"]] = flt(row["returned_qty"])

    # Batch fetch all items for invoices in current page
    si_item = frappe.qb.DocType(f"{doctype} Item")
    all_items = (
        frappe.qb.from_(si_item)
        .select(
            si_item.parent,
            si_item.name,
            si_item.item_code,
            si_item.item_name,
            si_item.qty,
            si_item.rate,
            si_item.amount,
            si_item.stock_qty,
            si_item.uom,
            si_item.warehouse
        )
        .where(si_item.parent.isin(invoice_names))
        .orderby(si_item.idx)
    ).run(as_dict=True)

    # Group items by parent invoice
    items_by_invoice = {}
    for item in all_items:
        parent = item["parent"]
        if parent not in items_by_invoice:
            items_by_invoice[parent] = []
        items_by_invoice[parent].append(item)

    # Process and return results
    data = []
    for invoice in invoices_list:
        inv_name = invoice["name"]
        returned_qty = returned_qty_map.get(inv_name, {})
        items = items_by_invoice.get(inv_name, [])

        # Calculate remaining quantities
        filtered_items = []
        for item in items:
            already_returned = returned_qty.get(item["item_code"], 0)
            remaining_qty = flt(item["qty"]) - already_returned

            if remaining_qty > 0:
                new_item = item.copy()
                new_item["qty"] = remaining_qty
                new_item["amount"] = remaining_qty * flt(item["rate"])
                if item.get("stock_qty") and item.get("qty"):
                    new_item["stock_qty"] = flt(item["stock_qty"]) / flt(item["qty"]) * remaining_qty
                filtered_items.append(frappe._dict(new_item))

        # Only include invoices with returnable items
        if filtered_items or not returned_qty:
            invoice_data = frappe._dict(invoice)
            invoice_data["items"] = filtered_items if filtered_items else items
            data.append(invoice_data)

    # Check if there are more results
    has_more = (start + page_length) < total_count

    return {"invoices": data, "has_more": has_more}


# ==========================================
# Legacy/Helper Functions
# ==========================================


def _resolve_branch(invoice, profile):
    """Branch this sale belongs to.

    Call Center has no branch of its own and targets one explicitly per order;
    every other profile uses its own. Mirrors the resolution used when the
    invoice is actually created.
    """
    return invoice.get("branch") or profile.get("branch")


def _filter_rules_by_branch(rule_map, branch):
    """Drop pricing rules that are not allowed at `branch`.

    A rule with no branches listed applies everywhere.
    """
    if not rule_map:
        return rule_map

    branches_map = AllowedBranchFetcher.fetch(list(rule_map.keys()))
    if not branches_map:
        return rule_map

    return {
        name: details
        for name, details in rule_map.items()
        if is_offer_allowed_for_branch(branches_map.get(name), branch)
    }


def _resolve_selling_price_list(invoice, profile, customer=None):
    """Resolve the price list used to evaluate Pricing Rules.

    Mirrors the chain a Sales Invoice resolves on submit (POS Profile ->
    Customer -> Customer Group -> Selling Settings). Pricing Rules bound to a
    `for_price_list` only match when this is populated, so falling back the
    same way keeps the POS preview consistent with the submitted invoice.
    """
    price_list = (
        invoice.get("price_list")
        or invoice.get("selling_price_list")
        or profile.get("selling_price_list")
    )
    if price_list:
        return price_list

    if customer:
        # db.get_value (not get_cached_value) so an unknown customer yields None
        # instead of raising and silently disabling every offer.
        price_list, customer_group = (
            frappe.db.get_value(
                "Customer", customer, ["default_price_list", "customer_group"]
            )
            or (None, None)
        )
        if price_list:
            return price_list

        if customer_group:
            price_list = frappe.db.get_value(
                "Customer Group", customer_group, "default_price_list"
            )
            if price_list:
                return price_list

    return frappe.db.get_single_value("Selling Settings", "selling_price_list")


@frappe.whitelist()
def apply_offers(invoice_data, selected_offers=None):
    """Calculate and apply promotional offers using ERPNext Pricing Rules.

    Args:
            invoice_data (str | dict): Sales Invoice payload used for offer evaluation.
            selected_offers (str | list | None): Optional collection of Pricing Rule names.
                    When provided, results are filtered to only include these rules.
                    ERPNext handles all conflict resolution based on priority.
    """
    try:
        if isinstance(invoice_data, str):
            invoice_data = json.loads(invoice_data or "{}")

        invoice = frappe._dict(invoice_data or {})
        items = invoice.get("items") or []

        if isinstance(selected_offers, str):
            try:
                selected_offers = json.loads(selected_offers)
            except ValueError:
                selected_offers = [selected_offers]

        if isinstance(selected_offers, (list, tuple, set)):
            selected_offer_names = {
                cstr(name) for name in selected_offers if cstr(name)
            }
        else:
            selected_offer_names = set()

        if not items:
            return {"items": []}

        if not invoice.get("pos_profile") or not erpnext_apply_pricing_rule:
            # Either no POS profile supplied or ERPNext promotional engine unavailable
            return {"items": items}

        profile = frappe.get_cached_doc("POS Profile", invoice.get("pos_profile"))

        # Batch fetch all item details in a single query (reduces N queries to 1)
        item_codes = list({item.get("item_code") for item in items if item.get("item_code")})
        item_details_map = {}
        if item_codes:
            item_records = frappe.get_all(
                "Item",
                filters={"name": ["in", item_codes]},
                fields=["name", "item_name", "item_group", "brand", "stock_uom"],
            )
            item_details_map = {r.name: r for r in item_records}

        pricing_items = []
        index_map = []
        prepared_items = [frappe._dict(row) for row in items]

        for idx, item in enumerate(prepared_items):
            item_code = item.get("item_code")
            qty = flt(item.get("qty") or item.get("quantity") or 0)

            if not item_code or qty <= 0:
                continue

            # Use batch-fetched item details
            cached = item_details_map.get(item_code)

            conversion_factor = flt(item.get("conversion_factor") or 1) or 1
            price_list_rate = flt(item.get("price_list_rate") or item.get("rate") or 0)

            pricing_items.append(
                frappe._dict(
                    {
                        "doctype": "Sales Invoice Item",
                        "name": item.get("name") or f"POS-{idx}",
                        "item_code": item_code,
                        "item_name": (
                            cached.item_name if cached else item.get("item_name")
                        ),
                        "item_group": (
                            cached.item_group if cached else item.get("item_group")
                        ),
                        "brand": (cached.brand if cached else item.get("brand")),
                        "qty": qty,
                        "stock_qty": qty * conversion_factor,
                        "conversion_factor": conversion_factor,
                        "uom": item.get("uom")
                        or item.get("stock_uom")
                        or (cached.stock_uom if cached else None),
                        "stock_uom": item.get("stock_uom")
                        or (cached.stock_uom if cached else None),
                        "price_list_rate": price_list_rate,
                        "base_price_list_rate": price_list_rate,
                        "rate": flt(item.get("rate") or price_list_rate),
                        "base_rate": flt(item.get("rate") or price_list_rate),
                        "discount_percentage": 0,
                        "discount_amount": 0,
                        "warehouse": item.get("warehouse") or profile.warehouse,
                        "parenttype": invoice.get("doctype") or "Sales Invoice",
                    }
                )
            )
            index_map.append(idx)

            # Clear previously applied promotional metadata if the
            # current quantity can no longer satisfy the rule.
            item.discount_percentage = 0
            item.discount_amount = 0
            item.pricing_rules = []
            item.applied_promotional_schemes = []

        if not pricing_items:
            return {"items": items}

        company_currency = frappe.get_cached_value(
            "Company", profile.company, "default_currency"
        )

        # Get customer details if customer is provided
        customer = invoice.get("customer")
        customer_group = invoice.get("customer_group")
        territory = invoice.get("territory")

        if customer and not customer_group:
            # Fetch customer_group from customer
            try:
                customer_data = frappe.get_cached_value(
                    "Customer", customer, ["customer_group", "territory"], as_dict=1
                )
                if customer_data:
                    customer_group = customer_data.get("customer_group")
                    if not territory:
                        territory = customer_data.get("territory")
            except Exception as e:
                # Customer lookup failed, will use defaults
                frappe.log_error(
                    f"Failed to fetch customer data for {customer}: {e}",
                    "Customer Data Lookup"
                )

        # If still no customer_group, use default
        if not customer_group:
            customer_group = "All Customer Groups"

        pricing_args = frappe._dict(
            {
                "doctype": invoice.get("doctype") or "Sales Invoice",
                "name": invoice.get("name") or "POS-INVOICE",
                "company": profile.company,
                "transaction_date": invoice.get("posting_date") or nowdate(),
                "posting_date": invoice.get("posting_date") or nowdate(),
                "currency": invoice.get("currency")
                or profile.get("currency")
                or company_currency,
                "conversion_rate": flt(invoice.get("conversion_rate") or 1) or 1,
                "plc_conversion_rate": flt(invoice.get("plc_conversion_rate") or 1)
                or 1,
                "price_list": _resolve_selling_price_list(invoice, profile, customer),
                "customer": customer,
                "customer_group": customer_group,
                "territory": territory,
                "items": pricing_items,
            }
        )

        # Call ERPNext pricing engine - it handles all conflicts based on priority
        #
        # Why we pass pricing_args twice:
        # - 1st param (args): ERPNext extracts and pops 'items' from this, then processes each item individually
        # - 2nd param (doc): Used by 'mixed_conditions' pricing rules to access the FULL items list
        #                    for quantity accumulation across different items in the same group
        #
        # Example: A rule "Buy 2 from Demo Item Group, get 10% off" with mixed_conditions=1
        # needs to see ALL items (1 Book + 1 Camera) to know total qty=2, not just each item's qty=1
        #
        # See: erpnext/accounts/doctype/pricing_rule/utils.py -> get_qty_and_rate_for_mixed_conditions()
        pricing_results = erpnext_apply_pricing_rule(pricing_args, doc=pricing_args) or []

        if not pricing_results:
            return {"items": items}

        raw_rule_names = set()
        for result in pricing_results:
            if not result:
                continue
            rules = []
            if erpnext_get_applied_pricing_rules:
                rules = erpnext_get_applied_pricing_rules(result.get("pricing_rules"))
            else:
                raw_rules = result.get("pricing_rules") or []
                if isinstance(raw_rules, str):
                    if raw_rules.startswith("["):
                        rules = json.loads(raw_rules)
                    else:
                        rules = [r.strip() for r in raw_rules.split(",") if r.strip()]
                elif isinstance(raw_rules, (list, tuple, set)):
                    rules = list(raw_rules)
            raw_rule_names.update(rules)

        # Build a map of applicable pricing rules from the ERPNext engine results.
        #
        # ERPNext has two types of pricing rules:
        #
        # 1. Promotional Scheme Rules (promotional_scheme is set):
        #    - Created automatically when a Promotional Scheme is saved
        #    - The scheme acts as a "template" that generates one or more Pricing Rules
        #    - Example: "Summer Sale" scheme creates "PRLE-0001", "PRLE-0002" rules
        #
        # 2. Standalone Pricing Rules (promotional_scheme is empty):
        #    - Created directly as Pricing Rule documents
        #    - Not linked to any Promotional Scheme
        #    - Example: A direct "10% off Item X" rule created in Pricing Rule doctype
        #
        # We include BOTH types for POS, but exclude coupon_code_based rules
        # (those require explicit coupon entry and are handled separately).
        #
        rule_map = {}
        if raw_rule_names:
            rule_records = frappe.get_all(
                "Pricing Rule",
                filters={"name": ["in", list(raw_rule_names)]},
                fields=[
                    "name",
                    "promotional_scheme",
                    "coupon_code_based",
                    "promotional_scheme_id",
                    "price_or_product_discount",
                ],
            )
            for record in rule_records:
                # Skip coupon-based rules (require explicit coupon code entry)
                if record.coupon_code_based:
                    continue

                # Include both promotional scheme rules and standalone pricing rules
                rule_map[record.name] = record

        # Honour the per-rule branch restriction. Done here rather than in the
        # ERPNext engine call so the POS preview and the submitted invoice agree.
        rule_map = _filter_rules_by_branch(rule_map, _resolve_branch(invoice, profile))

        if selected_offer_names:
            # Restrict available rules to the ones explicitly selected from the UI.
            rule_map = {
                name: details
                for name, details in rule_map.items()
                if name in selected_offer_names
            }

        if not rule_map:
            return {"items": items}

        applied_rules = set()
        free_items = []

        for result, item_index in zip(pricing_results, index_map):
            if not result:
                continue

            if erpnext_get_applied_pricing_rules:
                rule_names = erpnext_get_applied_pricing_rules(
                    result.get("pricing_rules")
                )
            else:
                raw_rules = result.get("pricing_rules") or []
                if isinstance(raw_rules, str):
                    if raw_rules.startswith("["):
                        rule_names = json.loads(raw_rules)
                    else:
                        rule_names = [
                            r.strip() for r in raw_rules.split(",") if r.strip()
                        ]
                elif isinstance(raw_rules, (list, tuple, set)):
                    rule_names = list(raw_rules)
                else:
                    rule_names = []

            applicable_rule_names = [
                name for name in rule_names or [] if name in rule_map
            ]

            if not applicable_rule_names:
                continue

            applied_rules.update(applicable_rule_names)

            item_doc = prepared_items[item_index]
            qty = flt(item_doc.get("qty") or item_doc.get("quantity") or 0)
            price_list_rate = flt(
                result.get("price_list_rate")
                or item_doc.get("price_list_rate")
                or item_doc.get("rate")
                or 0
            )

            # Get discount from result or fetch from pricing rule
            discount_percentage = flt(result.get("discount_percentage") or 0)
            per_unit_discount = flt(result.get("discount_amount") or 0)

            # If ERPNext didn't calculate discount (validate_applied_rule=1),
            # we need to fetch and apply it manually
            if (
                not discount_percentage
                and not per_unit_discount
                and applicable_rule_names
            ):
                for rule_name in applicable_rule_names:
                    rule_doc = rule_map.get(rule_name)
                    if not rule_doc:
                        continue

                    # Fetch full pricing rule to get discount values
                    full_rule = frappe.get_cached_doc("Pricing Rule", rule_name)

                    if (
                        full_rule.rate_or_discount == "Discount Percentage"
                        and full_rule.discount_percentage
                    ):
                        discount_percentage += flt(full_rule.discount_percentage)
                    elif (
                        full_rule.rate_or_discount == "Discount Amount"
                        and full_rule.discount_amount
                    ):
                        per_unit_discount += flt(full_rule.discount_amount)
                    elif full_rule.rate_or_discount == "Rate" and full_rule.rate:
                        # Apply fixed rate
                        price_list_rate = flt(full_rule.rate)

            line_discount_amount = 0
            if discount_percentage and qty and price_list_rate:
                line_discount_amount = price_list_rate * qty * discount_percentage / 100
            elif per_unit_discount and qty:
                line_discount_amount = per_unit_discount * qty
            else:
                line_discount_amount = per_unit_discount

            if (
                not discount_percentage
                and line_discount_amount
                and qty
                and price_list_rate
            ):
                base_amount = price_list_rate * qty
                if base_amount:
                    discount_percentage = (line_discount_amount / base_amount) * 100

            item_doc.discount_percentage = discount_percentage
            item_doc.discount_amount = line_discount_amount
            item_doc.price_list_rate = price_list_rate
            item_doc.rate = flt(item_doc.get("rate") or price_list_rate)
            # ERPNext expects pricing_rules as comma-separated string, not a list
            item_doc.pricing_rules = ",".join(applicable_rule_names) if applicable_rule_names else ""

            item_doc.applied_promotional_schemes = list(
                {
                    rule_map[name].promotional_scheme
                    for name in applicable_rule_names
                    if rule_map[name].promotional_scheme
                }
            )

            for free_item in result.get("free_item_data") or []:
                rule_name = free_item.get("pricing_rules")
                if not rule_name or rule_name not in rule_map:
                    continue
                free_item_doc = frappe._dict(free_item)
                free_item_doc.applied_promotional_scheme = rule_map[
                    rule_name
                ].promotional_scheme
                free_items.append(free_item_doc)

        return {
            "items": [dict(item) for item in prepared_items],
            "free_items": [dict(item) for item in free_items],
            "applied_pricing_rules": sorted(applied_rules),
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Apply Offers Error")
        frappe.throw(_("Error applying offers: {0}").format(str(e)))


@frappe.whitelist()
def process_return_by_cancel(invoice_name, returned_items, pos_opening_shift=None, pos_profile=None, return_reason=None):
    """Process a return by cancelling the original invoice.

    If there are remaining items (not all returned), a new Sales Invoice
    is created with only the remaining items.

    Args:
        invoice_name: Original Sales Invoice name
        returned_items: JSON list of returned items with sales_invoice_item and return_qty
        pos_opening_shift: Current POS Opening Shift
        pos_profile: POS Profile (fallback if original doesn't have one)
        return_reason: Optional reason for the return

    Returns:
        dict: cancelled_invoice, new_invoice (if any), has_remaining_items
    """
    import json

    returned_items = json.loads(returned_items) if isinstance(returned_items, str) else returned_items

    if not invoice_name or invoice_name in ["None", "null", "", False]:
        frappe.throw(_("Invoice must be submitted to process a return"))

    original = frappe.get_doc("Sales Invoice", invoice_name)
    if original.docstatus != 1:
        frappe.throw(_("Invoice must be submitted to process a return"))

    # Build map of returned items by row name or item_code
    returned_map = {}
    for item in returned_items:
        key = item.get("sales_invoice_item") or item.get("name") or item.get("item_code")
        returned_map[key] = flt(item.get("return_qty", 0))

    # Determine remaining items
    remaining_items = []
    for item in original.items:
        returned_qty = returned_map.get(item.name, 0)
        if returned_qty == 0:
            returned_qty = returned_map.get(item.item_code, 0)

        remaining_qty = flt(item.qty) - returned_qty
        if remaining_qty > 0:
            remaining_items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": remaining_qty,
                "rate": flt(item.rate),
                "price_list_rate": flt(item.price_list_rate),
                "discount_percentage": flt(item.discount_percentage),
                "warehouse": item.warehouse,
                "uom": item.uom,
                "conversion_factor": flt(item.conversion_factor or 1),
                "branch": item.branch,
            })

    # Cancel the original invoice
    try:
        original.cancel()
    except Exception as e:
        frappe.log_error(f"Failed to cancel invoice {invoice_name}: {str(e)}")
        frappe.throw(_("Failed to cancel invoice {0}: {1}").format(invoice_name, str(e)))

    new_invoice_name = None
    if remaining_items:
        # Build proportional payments based on original invoice payments.
        # If the original had no payments (credit sale), the new invoice
        # also has no payments.
        original_payments = original.get("payments") or []
        original_total = flt(original.grand_total)
        new_payments = []
        if original_payments and original_total > 0:
            # Proportional payments: new invoice total / original grand_total
            new_total = sum(
                flt(it["qty"]) * flt(it["rate"]) for it in remaining_items
            )
            ratio = new_total / original_total if original_total else 0
            for p in original_payments:
                p_amount = flt(p.get("amount", 0)) * ratio
                if p_amount > 0:
                    new_payments.append({
                        "mode_of_payment": p.get("mode_of_payment"),
                        "amount": round(p_amount, 2),
                    })

        new_invoice_data = {
            "doctype": "Sales Invoice",
            "customer": original.customer,
            "company": original.company,
            "pos_profile": original.pos_profile or pos_profile,
            "is_pos": 1,
            "update_stock": 1,
            "posting_date": frappe.utils.nowdate(),
            "posting_time": frappe.utils.nowtime(),
            "set_posting_time": 1,
            "items": remaining_items,
            "payments": new_payments,
            "remarks": return_reason or _("Amended from {0}").format(invoice_name),
        }

        if original.branch:
            new_invoice_data["branch"] = original.branch

        # Copy sales team
        if original.sales_team:
            new_invoice_data["sales_team"] = []
            for member in original.sales_team:
                new_invoice_data["sales_team"].append({
                    "sales_person": member.sales_person,
                    "allocated_percentage": flt(member.allocated_percentage),
                })

        # Use standard submit flow to create and submit the new invoice
        result = submit_invoice(invoice=json.dumps(new_invoice_data), data="{}")
        if result and isinstance(result, dict):
            new_invoice_name = result.get("name")

    return {
        "cancelled_invoice": invoice_name,
        "new_invoice": new_invoice_name,
        "has_remaining_items": bool(remaining_items),
    }
