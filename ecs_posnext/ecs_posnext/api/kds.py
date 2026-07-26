import frappe
import json
from frappe.utils import now_datetime, add_to_date, flt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_item_ingredients(item_code):
    """Return ingredient list from Product Bundle, falling back to template if variant."""
    if not item_code:
        return []

    def _bundle_ingredients(code):
        bundle = frappe.db.get_value("Product Bundle", {"new_item_code": code}, "name")
        if not bundle:
            return []
        items = frappe.get_all(
            "Product Bundle Item",
            filters={"parent": bundle},
            fields=["item_code", "qty", "description"],
        )
        for i in items:
            i["item_name"] = frappe.db.get_value("Item", i.item_code, "item_name") or i.item_code
        return items

    ingredients = _bundle_ingredients(item_code)
    if not ingredients:
        variant_of = frappe.db.get_value("Item", item_code, "variant_of")
        if variant_of:
            ingredients = _bundle_ingredients(variant_of)
    return ingredients


def _get_item_kds_station(item_code):
    """Return kds_station for an item, falling back to its variant template if not set."""
    if not item_code:
        return ""
    station = frappe.db.get_value("Item", item_code, "kds_station") or ""
    if not station:
        variant_of = frappe.db.get_value("Item", item_code, "variant_of")
        if variant_of:
            station = frappe.db.get_value("Item", variant_of, "kds_station") or ""
    return station


_SETTINGS_FIELDS = [
    "default_target_minutes", "warning_threshold_pct",
    "pickup_target_minutes", "delivery_target_minutes",
    "dine_in_target_minutes", "talabat_target_minutes",
]


def _get_settings_for_branch(branch):
    """Return KDS Settings for the given branch, falling back to the default record."""
    settings = None
    if branch:
        settings = frappe.db.get_value(
            "KDS Settings", {"branch": branch}, _SETTINGS_FIELDS, as_dict=True,
        )
    if not settings:
        settings = frappe.db.get_value(
            "KDS Settings", {"is_default": 1}, _SETTINGS_FIELDS, as_dict=True,
        )
    return settings or {
        "default_target_minutes": 15, "warning_threshold_pct": 70,
        "pickup_target_minutes": 0, "delivery_target_minutes": 0,
        "dine_in_target_minutes": 0, "talabat_target_minutes": 0,
    }


def _get_target_minutes(settings, order_type):
    """Pick the per-order-type target, falling back to default_target_minutes."""
    mapping = {
        "Pickup":   "pickup_target_minutes",
        "Delivery": "delivery_target_minutes",
        "Dine In":  "dine_in_target_minutes",
        "Talabat":  "talabat_target_minutes",
    }
    field = mapping.get(order_type or "")
    if field:
        val = settings.get(field) or 0
        if val > 0:
            return val
    return settings.get("default_target_minutes") or 15


# ---------------------------------------------------------------------------
# Sales Invoice on_submit hook — creates KDS Order
# ---------------------------------------------------------------------------

def on_sales_invoice_submit(doc, method=None):
    # A Return / Credit Note reverses a sale — there is nothing for the kitchen to
    # prepare, so it must never raise a KDS ticket (an un-completable ticket would
    # otherwise block the POS Business Day from closing).
    if doc.get("is_return"):
        return
    if frappe.db.exists("KDS Order", {"sales_invoice": doc.name}):
        return
    try:
        _create_kds_order(doc)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "KDS Order Creation Failed")


def on_sales_invoice_cancel(doc, method=None):
    """When a Sales Invoice is cancelled, cancel its KDS Order so it disappears
    from the kitchen (KDS) and dispatch screens."""
    orders = frappe.get_all(
        "KDS Order",
        filters={"sales_invoice": doc.name, "status": ["!=", "Cancelled"]},
        pluck="name",
    )
    for order in orders:
        try:
            frappe.db.set_value("KDS Order", order, "status", "Cancelled")
        except Exception:
            frappe.log_error(frappe.get_traceback(), "KDS Order Cancel Failed")

    if orders:
        frappe.publish_realtime(
            "kds_update",
            {
                "action": "order_cancelled",
                "invoice": doc.name,
                "branch": doc.get("branch"),
            },
            after_commit=True,
        )
        frappe.publish_realtime(
            "dispatch_desk_refresh",
            {"source": "kds", "invoice": doc.name},
            after_commit=True,
        )


def _create_kds_order(doc):
    settings = _get_settings_for_branch(doc.get("branch"))
    order_type = doc.get("custom_order_type") or ""
    target_min = _get_target_minutes(settings, order_type)
    now = now_datetime()

    today_count = frappe.db.count(
        "KDS Order",
        {"order_time": [">=", frappe.utils.today()]},
    )
    order_no = str(today_count + 1).zfill(3)

    items_rows = []
    for item in doc.items:
        main_station = _get_item_kds_station(item.item_code)
        components_raw = item.get("custom_selected_components") or ""
        components = []
        if components_raw:
            try:
                components = json.loads(components_raw)
            except Exception:
                components = []

        # Use item index as group id to link parent + its components
        group_id = str(item.idx)

        # Main item — if it has no station and has components, mark Ready immediately
        # (the components carry the actual station work)
        main_status = "Ready" if (not main_station and components) else "Pending"

        # Fetch ingredients from Product Bundle (for standalone variant items)
        main_ingredients = [] if components else _get_item_ingredients(item.item_code)

        # Convert removed_ingredients from item codes → item names using the ingredient list
        raw_removed = item.get("removed_ingredients") or ""
        removed_codes = []
        if raw_removed:
            try:
                removed_codes = json.loads(raw_removed) if isinstance(raw_removed, str) else raw_removed
            except Exception:
                removed_codes = []
        # Build a code→name map from fetched ingredients
        code_to_name = {i["item_code"]: i.get("item_name", i["item_code"]) for i in main_ingredients}
        removed_names = [code_to_name.get(c, c) for c in removed_codes] if removed_codes else []

        items_rows.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "kds_station": main_station,
            "qty": item.qty,
            "is_special": 0,
            # Per-item note from the variant picker / checkout dialog (Sales Invoice Item.posa_notes)
            "special_notes": item.get("posa_notes") or "",
            "station_status": main_status,
            "selected_components": components_raw,
            "ingredients": json.dumps(main_ingredients) if main_ingredients else "",
            "removed_ingredients": json.dumps(removed_names) if removed_names else "",
            "is_component": 0,
            "combo_item_name": "",
            "combo_group_id": group_id,
        })

        # Expand each component into its own KDS Order Item at its own station
        for comp in components:
            comp_code = comp.get("item_code") or ""
            comp_station = _get_item_kds_station(comp_code)
            comp_status = "Pending" if comp_station else "Ready"
            removed_names = comp.get("removed_ingredient_names") or []
            all_ingredients = comp.get("ingredients") or []
            items_rows.append({
                "item_code": comp_code,
                "item_name": comp.get("item_name") or comp_code,
                "kds_station": comp_station,
                "qty": comp.get("quantity") or 1,
                "is_special": 0,
                "special_notes": comp.get("notes") or "",
                "station_status": comp_status,
                "selected_components": "",
                "ingredients": json.dumps(all_ingredients) if all_ingredients else "",
                "removed_ingredients": json.dumps(removed_names) if removed_names else "",
                "is_component": 1,
                "combo_item_name": item.item_name,
                "combo_group_id": group_id,
            })

    kds_order = frappe.get_doc({
        "doctype": "KDS Order",
        "naming_series": "KDS-.YYYY.MM.DD.-",
        "sales_invoice": doc.name,
        "branch": doc.get("branch"),
        "order_no": order_no,
        "order_type": order_type,
        "custom_number_order": doc.get("custom_number_order") or "",
        "order_time": now,
        "target_minutes": target_min,
        "expected_ready_time": add_to_date(now, minutes=target_min),
        "status": "Pending",
        "items": items_rows,
    })
    kds_order.insert(ignore_permissions=True)

    frappe.publish_realtime(
        "kds_update",
        {
            "action": "new_order",
            "order": kds_order.name,
            "branch": doc.get("branch"),
        },
        after_commit=True,
    )


# ---------------------------------------------------------------------------
# Whitelisted API
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_stations_summary():
    """Return all active stations with their pending order counts (all branches)."""
    stations = frappe.get_all(
        "KDS Station",
        filters={"is_active": 1},
        fields=["name", "station_name", "branch", "enable_special_print", "sort_order"],
        order_by="sort_order asc, station_name asc",
    )

    if not stations:
        return stations

    rows = frappe.db.sql(
        """
        SELECT koi.kds_station, COUNT(DISTINCT ko.name) AS pending_orders
        FROM `tabKDS Order Item` koi
        JOIN `tabKDS Order` ko ON ko.name = koi.parent
        WHERE koi.station_status = 'Pending'
          AND ko.status IN ('Pending', 'Preparing', 'Ready')
        GROUP BY koi.kds_station
        """,
        as_dict=True,
    )
    counts = {r.kds_station: r.pending_orders for r in rows}
    for s in stations:
        s["pending_orders"] = counts.get(s["station_name"], 0)

    return stations


@frappe.whitelist()
def get_settings(branch=None):
    settings = _get_settings_for_branch(branch)
    stations = frappe.get_all(
        "KDS Station",
        filters={"is_active": 1},
        fields=["name", "station_name", "branch", "enable_special_print", "sort_order"],
        order_by="sort_order asc",
    )
    return {"settings": settings, "stations": stations}


def _drop_return_orders(orders):
    """Remove orders whose linked Sales Invoice is a Return / Credit Note.

    A return reverses a sale — the kitchen/assembly/dispatch should never see it. New
    returns no longer create KDS tickets, but this also hides any that were created
    before that fix (and any that slip through another path)."""
    inv_names = [o.get("sales_invoice") for o in orders if o.get("sales_invoice")]
    if not inv_names:
        return orders
    # Hide an order if its invoice IS a return, OR has been returned (a submitted
    # Return points at it) — a returned/rejected order has nothing left to prepare.
    hidden = set(
        frappe.get_all("Sales Invoice", filters={"name": ["in", inv_names], "is_return": 1}, pluck="name")
    )
    hidden |= set(
        frappe.get_all(
            "Sales Invoice",
            filters={"return_against": ["in", inv_names], "is_return": 1, "docstatus": 1},
            pluck="return_against",
        )
    )
    return [o for o in orders if o.get("sales_invoice") not in hidden]


@frappe.whitelist()
def get_active_orders(branch=None):
    filters = {"status": ["in", ["Pending", "Preparing", "Ready"]]}
    if branch:
        filters["branch"] = branch

    orders = frappe.get_all(
        "KDS Order",
        filters=filters,
        fields=[
            "name", "order_no", "custom_number_order", "sales_invoice", "branch",
            "order_time", "target_minutes", "expected_ready_time", "status", "order_type",
        ],
        order_by="order_time asc",
        limit=200,
    )
    orders = _drop_return_orders(orders)

    for order in orders:
        order["items"] = frappe.get_all(
            "KDS Order Item",
            filters={"parent": order["name"]},
            fields=["name", "item_code", "item_name", "kds_station", "qty",
                    "is_special", "special_notes", "station_status",
                    "selected_components", "ingredients", "removed_ingredients",
                    "is_component", "combo_item_name", "combo_group_id"],
            order_by="idx asc",
        )

        # Enrich with display fields from the linked Sales Invoice (table / customer / rider)
        inv = order.get("sales_invoice")
        if inv:
            si = frappe.db.get_value(
                "Sales Invoice", inv,
                ["custom_table_number", "custom_table_no", "customer_name", "posa_notes",
                 "custom_payment_type", "outstanding_amount", "custom_third_party_referance_number"],
                as_dict=True,
            ) or {}
            # Show the human table number; fall back to the link id for older invoices.
            order["table_number"] = si.get("custom_table_no") or si.get("custom_table_number")
            order["customer_name"] = si.get("customer_name")
            order["order_note"] = si.get("posa_notes")
            order["custom_payment_type"] = si.get("custom_payment_type")
            order["outstanding_amount"] = si.get("outstanding_amount")
            # Talabat counter/window number (external reference) shown on the card.
            order["window_no"] = si.get("custom_third_party_referance_number")

            otype = (order.get("order_type") or "").lower()
            if otype == "talabat":
                order["rider"] = "Talabat"
            elif otype == "delivery":
                driver = frappe.db.get_value(
                    "Delivery Assignment",
                    {"order_reference": inv, "order_doctype": "Sales Invoice"},
                    "driver",
                )
                if driver:
                    order["rider"] = frappe.db.get_value("Driver", driver, "full_name") or driver

    return orders


@frappe.whitelist()
def get_station_orders(station, branch=None):
    matching_parents = frappe.db.sql_list(
        """
        SELECT DISTINCT parent FROM `tabKDS Order Item`
        WHERE kds_station = %s AND station_status = 'Pending'
        """,
        station,
    )
    if not matching_parents:
        return []

    filters = {
        "name": ["in", matching_parents],
        "status": ["in", ["Pending", "Preparing", "Ready"]],
    }
    if branch:
        filters["branch"] = branch

    orders = frappe.get_all(
        "KDS Order",
        filters=filters,
        fields=[
            "name", "order_no", "custom_number_order", "sales_invoice", "branch",
            "order_time", "target_minutes", "expected_ready_time", "status",
        ],
        order_by="order_time asc",
        limit=200,
    )
    orders = _drop_return_orders(orders)

    for order in orders:
        order["items"] = frappe.get_all(
            "KDS Order Item",
            filters={"parent": order["name"], "kds_station": station},
            fields=["name", "item_code", "item_name", "kds_station", "qty",
                    "is_special", "special_notes", "station_status",
                    "selected_components", "ingredients", "removed_ingredients",
                    "is_component", "combo_item_name", "combo_group_id"],
            order_by="idx asc",
        )

    return orders


@frappe.whitelist()
def complete_order(kds_order, force=0):
    doc = frappe.get_doc("KDS Order", kds_order)
    if doc.status in ("Completed", "Cancelled"):
        return {"status": doc.status}

    if frappe.utils.cint(force):
        # Mark all pending station items as Ready so station screens reflect completion
        frappe.db.sql(
            "UPDATE `tabKDS Order Item` SET station_status='Ready' WHERE parent=%s AND station_status='Pending'",
            kds_order,
        )

    doc.db_set("status", "Completed")
    doc.db_set("completed_time", now_datetime())
    frappe.publish_realtime(
        "kds_update",
        {"action": "order_completed", "order": kds_order, "branch": doc.branch},
        after_commit=True,
    )
    frappe.publish_realtime(
        "dispatch_desk_refresh",
        {"source": "kds", "invoice": doc.sales_invoice},
        after_commit=True,
    )
    return {"status": "Completed"}


@frappe.whitelist()
def complete_station(kds_order, station):
    doc = frappe.get_doc("KDS Order", kds_order)

    for item in doc.items:
        if item.kds_station == station and item.station_status == "Pending":
            frappe.db.set_value(
                "KDS Order Item", item.name, "station_status", "Ready"
            )

    # Only items with an assigned station count toward "ready"
    # Items without a station (e.g. main combo row) start as Ready and are excluded
    pending_count = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabKDS Order Item` WHERE parent=%s AND station_status='Pending' AND kds_station IS NOT NULL AND kds_station!=''",
        kds_order,
    )[0][0]

    if pending_count == 0:
        doc.db_set("status", "Ready")
        frappe.publish_realtime(
            "kds_update",
            {"action": "order_ready", "order": kds_order, "branch": doc.branch},
            after_commit=True,
        )
    else:
        frappe.publish_realtime(
            "kds_update",
            {"action": "station_done", "order": kds_order, "station": station, "branch": doc.branch},
            after_commit=True,
        )

    return {"pending_items": pending_count}
