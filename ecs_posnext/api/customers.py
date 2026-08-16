"""
POS Next Customer API
Handles customer search, creation, and management for POS operations
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_customers(search_term="", pos_profile=None, limit=20, modified_since=None):

    """
    Search customers for inline customer selection in POS.

    Args:
        search_term (str): Search query (name, mobile, or customer ID)
        pos_profile (str): POS Profile to filter by customer group
        limit (int): Maximum number of results to return
        modified_since (str): Fetch customers modified after this timestamp (ISO format)

    Returns:
        list: List of customer dictionaries with name, customer_name, mobile_no, email_id, disabled
    """
    try:
        frappe.logger().debug(
            f"get_customers called with search_term={search_term}, pos_profile={pos_profile}, limit={limit}, modified_since={modified_since}"
        )

        filters = {}

        # Filter by POS Profile customer group if specified
        if pos_profile:
            frappe.logger().debug(f"Loading POS Profile: {pos_profile}")
            profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
            # Check if customer_group field exists (it may not exist in all versions)
            if hasattr(profile_doc, "customer_group") and profile_doc.customer_group:
                filters["customer_group"] = profile_doc.customer_group
                frappe.logger().debug(f"Filtering by customer_group: {profile_doc.customer_group}")

        if modified_since:
            # Delta sync: include disabled customers so frontend can purge them
            filters["modified"] = [">=", modified_since]
        else:
            # Full fetch: only active customers
            filters["disabled"] = 0
            
        or_filters = {}
        if search_term:
            or_filters = {
                "name": ["like", f"%{search_term}%"],
                "customer_name": ["like", f"%{search_term}%"],
                "mobile_no": ["like", f"%{search_term}%"],
                "custom_other_mobile_no": ["like", f"%{search_term}%"],
                "email_id": ["like", f"%{search_term}%"],
            }

        customer_limit = limit if limit not in (None, 0) else frappe.db.count("Customer", filters)
        result = frappe.get_all(
            "Customer",
            filters=filters,
            or_filters=or_filters,
            fields=["name", "customer_name", "mobile_no", "custom_other_mobile_no", "email_id", "disabled"],
            limit=customer_limit,
            order_by="customer_name asc",
        )
        frappe.logger().debug(f"get_customers returned {len(result)} customers")
        return result
    except Exception as e:
        frappe.logger().error(f"Error in get_customers: {str(e)}")
        frappe.logger().error(frappe.get_traceback())
        frappe.throw(_("Error fetching customers: {0}").format(str(e)))


@frappe.whitelist()
def create_customer(customer_name, mobile_no=None, email_id=None, customer_group="أفراد", territory="All Territories", company=None):
    """
    Create a new customer from POS.

    Args:
        customer_name (str): Customer name (required)
        mobile_no (str): Mobile number (optional)
        email_id (str): Email address (optional)
        customer_group (str): Customer group (default: أفراد)
        territory (str): Territory (default: All Territories)
        company (str): Company (optional, used to auto-assign loyalty program)

    Returns:
        dict: Created customer document
    """
    # Check if user has permission to create customers
    if not frappe.has_permission("Customer", "create"):
        frappe.throw(_("You don't have permission to create customers"), frappe.PermissionError)

    if not customer_name:
        frappe.throw(_("Customer name is required"))

    # Auto-assign loyalty program based on company
    loyalty_program = None
    if company:
        loyalty_program = get_default_loyalty_program(company)

    customer = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": "Individual",
            "customer_group": customer_group or "أفراد",
            "territory": territory or "All Territories",
            "mobile_no": mobile_no or "",
            "email_id": email_id or "",
            "loyalty_program": loyalty_program,
        }
    )

    customer.insert()

    return customer.as_dict()


def get_default_loyalty_program(company):
    """
    Get the default loyalty program for a company.
    Prefers programs with auto_opt_in enabled.

    Args:
        company (str): Company name

    Returns:
        str: Loyalty program name or None
    """
    # First try to find a loyalty program with auto_opt_in for the company
    loyalty_program = frappe.db.get_value(
        "Loyalty Program",
        {"company": company, "auto_opt_in": 1},
        "name"
    )

    if loyalty_program:
        return loyalty_program

    # Fallback: any loyalty program for the company
    loyalty_program = frappe.db.get_value(
        "Loyalty Program",
        {"company": company},
        "name"
    )

    return loyalty_program


def auto_assign_loyalty_program(doc, method=None):
    """
    Auto-assign loyalty program to newly created customers.
    Called as after_insert hook on Customer doctype.

    Uses the default_loyalty_program from POS Settings.
    If no loyalty program is configured in POS Settings, no auto-assignment occurs.

    Args:
        doc: Customer document
        method: Hook method name (not used)
    """
    # Skip if customer already has a loyalty program
    if doc.loyalty_program:
        return

    # Get loyalty program from POS Settings
    loyalty_program = get_default_loyalty_program_from_settings()

    if loyalty_program:
        # Use db_set to avoid triggering validate hooks again
        doc.db_set("loyalty_program", loyalty_program, update_modified=False)
        frappe.logger().info(
            f"Auto-assigned loyalty program '{loyalty_program}' to customer '{doc.name}'"
        )


def get_default_loyalty_program_from_settings():
    """
    Get the default loyalty program from POS Settings.
    Checks all enabled POS Settings and returns the first configured loyalty program.

    Returns:
        str: Loyalty program name or None if not configured
    """
    # Find POS Settings with default_loyalty_program set
    pos_settings = frappe.get_all(
        "POS Settings",
        filters={"enabled": 1, "default_loyalty_program": ["is", "set"]},
        fields=["default_loyalty_program"],
        limit=1
    )

    if pos_settings and pos_settings[0].get("default_loyalty_program"):
        return pos_settings[0].default_loyalty_program

    return None


@frappe.whitelist()
def get_customer_details(customer):
    """
    Get detailed customer information.

    Args:
        customer (str): Customer ID

    Returns:
        dict: Customer details
    """
    if not customer:
        frappe.throw(_("Customer is required"))

    return frappe.get_cached_doc("Customer", customer).as_dict()

@frappe.whitelist()
def get_customer_addresses(customer):
    """
    Get addresses for a customer.

    Args:
        customer (str): Customer ID

    Returns:
        list: List of address dictionaries with name, address_display, city, and other details
    """
    if not customer:
        return []

    addresses = frappe.get_all(
        "Address",
        filters=[
            ["Dynamic Link", "link_doctype", "=", "Customer"],
            ["Dynamic Link", "link_name", "=", customer],
            ["disabled", "=", 0],
        ],
        fields=["name", "address_title", "address_line1", "address_line2", "city", "state", "country", "pincode", "phone", "email_id", "is_primary_address", "is_shipping_address", "territory", "branch", "custom_street", "custom_building_name", "custom_floor", "custom_apartment", "custom_mark"]
    )

    for addr in addresses:
        addr["address_display"] = frappe.get_doc("Address", addr.name).get_display()

    return addresses

@frappe.whitelist()
def get_territories(branch=None):
    filters = {}
    if branch:
        filters["branch"] = branch
    return frappe.get_all("Territory", filters=filters, fields=["name", "territory_name", "branch"], order_by="territory_name")

@frappe.whitelist()
def get_parent_territories():
    """Get territories that have children (parent territories) for city selection."""
    parent_names = frappe.get_all(
        "Territory",
        filters={"parent_territory": ["is", "set"]},
        fields=["parent_territory"],
        distinct=True
    )
    parents = list(set(t["parent_territory"] for t in parent_names))
    if not parents:
        return []
    return frappe.get_all(
        "Territory",
        filters={"name": ["in", parents]},
        fields=["name", "territory_name"],
        order_by="territory_name"
    )

@frappe.whitelist()
def get_child_territories(parent_territory):
    """Get child territories of a given parent territory for zone selection."""
    if not parent_territory:
        return []
    return frappe.get_all(
        "Territory",
        filters={"parent_territory": parent_territory},
        fields=["name", "territory_name"],
        order_by="territory_name"
    )

@frappe.whitelist()
def get_branches():
    """
    Get list of all branches with their associated POS Profiles, warehouses, and price lists.
    Returns:
        list: List of dicts with 'name' (branch name), 'pos_profile', 'warehouse', 'selling_price_list'
    """
    return frappe.get_all(
        "POS Profile",
        filters={"disabled": 0, "branch": ["is", "set"]},
        fields=["name as pos_profile", "branch as name", "warehouse", "selling_price_list"],
        order_by="branch asc"
    )

@frappe.whitelist()
def get_delivery_charge_for_territory(territory, pos_profile=None):
    """
    Get the delivery charge details for a given territory.
    
    Args:
        territory (str): Territory name
        pos_profile (str, optional): POS Profile name to get specific rate
        
    Returns:
        dict: {name, rate, label, shipping_account, cost_center} or None
    """
    if not territory:
        return None
        
    delivery_charge_name = frappe.db.get_value("Territory", territory, "delivery_charges")
    if not delivery_charge_name:
        return None
        
    charge_doc = frappe.get_doc("Delivery Charges", delivery_charge_name)
    if charge_doc.disabled:
        return None
        
    # Verify company if POS Profile is provided
    if pos_profile:
        profile_company = frappe.db.get_value("POS Profile", pos_profile, "company")
        if charge_doc.company != profile_company:
            return None
            
    # Default rate
    rate = charge_doc.default_rate

    # Check if there is a specific rate for this POS Profile
    if pos_profile:
        for profile_row in charge_doc.profiles:
            if profile_row.pos_profile == pos_profile:
                rate = profile_row.rate
                break

    # Free Delivery: when the POS Profile waives delivery, force the rate to 0 so the zone
    # still displays but nothing is charged.
    free_delivery = 0
    if pos_profile:
        free_delivery = frappe.utils.cint(frappe.db.get_value("POS Profile", pos_profile, "custom_free_delivery"))
        if free_delivery:
            rate = 0

    return {
        "name": charge_doc.name,
        "label": charge_doc.label,
        "rate": rate,
        "free_delivery": free_delivery,
        "territory": territory,
        "shipping_account": charge_doc.shipping_account,
        "cost_center": charge_doc.cost_center,
        "company": charge_doc.company
    }


@frappe.whitelist()
def get_customer_profile(customer, pos_profile=None, branch=None):
    """
    Get comprehensive customer profile for POS display.
    Includes: type (VIP/Blacklist), favorites, last order, notes, coupons.

    Args:
        customer (str): Customer ID
        pos_profile (str, optional): POS Profile for filtering

    Returns:
        dict: Customer profile data
    """
    if not customer:
        frappe.throw(_("Customer is required"))

    cust = frappe.get_cached_doc("Customer", customer)

    # Customer type
    customer_type = "Regular"
    if cust.get("custom_vip"):
        customer_type = "VIP"
    elif cust.get("custom_black_list") or cust.get("custom_is_blacklist") == "Yes":
        customer_type = "Blacklist"

    # Actual total orders count from Sales Invoices
    total_count_result = frappe.db.sql("""
        SELECT COUNT(*) as cnt FROM `tabSales Invoice`
        WHERE customer = %s AND docstatus = 1
    """, customer, as_dict=True)
    actual_total_orders = int(total_count_result[0].cnt if total_count_result else 0)

    # Branch-specific stats (when branch provided)
    branch_total_orders = 0
    last_order_in_branch = None
    if branch:
        branch_count = frappe.db.sql("""
            SELECT COUNT(*) as cnt FROM `tabSales Invoice`
            WHERE customer = %s AND branch = %s AND docstatus = 1
        """, (customer, branch), as_dict=True)
        branch_total_orders = int(branch_count[0].cnt if branch_count else 0)

        last_branch_inv = frappe.get_all(
            "Sales Invoice",
            filters={"customer": customer, "branch": branch, "docstatus": 1},
            fields=["name", "posting_date", "grand_total", "currency", "custom_order_type"],
            order_by="posting_date desc, creation desc",
            limit=1
        )
        if last_branch_inv:
            bi = last_branch_inv[0]
            last_order_in_branch = {
                "invoice_name": bi.name,
                "date": str(bi.posting_date),
                "grand_total": bi.grand_total,
                "currency": bi.currency,
                "order_type": bi.custom_order_type,
            }

    # Last order
    last_order = None
    last_invoice = frappe.get_all(
        "Sales Invoice",
        filters={"customer": customer, "docstatus": 1},
        fields=["name", "posting_date", "grand_total", "currency", "custom_order_type", "branch"],
        order_by="posting_date desc, creation desc",
        limit=1
    )
    if last_invoice:
        inv = last_invoice[0]
        # Get items from last order with full details for reorder
        last_order_items = frappe.get_all(
            "Sales Invoice Item",
            filters={"parent": inv.name},
            fields=["item_code", "item_name", "qty", "rate", "amount", "uom", "stock_uom",
                     "conversion_factor", "price_list_rate", "warehouse", "batch_no",
                     "serial_no", "item_group", "brand", "description",
                     "posa_row_id"],
            order_by="idx"
        )

        # Get packed items (Product Bundle components) from the invoice
        packed_items = frappe.get_all(
            "Packed Item",
            filters={"parent": inv.name},
            fields=["parent_item", "item_code", "item_name", "qty", "uom",
                     "warehouse", "conversion_factor", "rate", "posa_row_id",
                     "parent_detail_docname"],
            order_by="idx"
        )

        # Group packed items by posa_row_id for matching to parent items
        packed_by_row = {}
        for pi in packed_items:
            row_id = pi.get("posa_row_id") or pi.get("parent_detail_docname") or ""
            if row_id not in packed_by_row:
                packed_by_row[row_id] = []
            packed_by_row[row_id].append({
                "parent_item": pi.parent_item,
                "item_code": pi.item_code,
                "item_name": pi.item_name,
                "qty": pi.qty,
                "uom": pi.uom,
                "warehouse": pi.warehouse,
                "conversion_factor": pi.conversion_factor or 1,
                "rate": pi.rate or 0,
            })

        # Attach packed items (as components) to each parent item
        from erpnext.stock.doctype.packed_item.packed_item import is_product_bundle
        for item in last_order_items:
            row_id = item.get("posa_row_id") or ""
            if row_id and row_id in packed_by_row:
                # Reverse the qty multiplication (packed qty was multiplied by parent qty on submit)
                parent_qty = item.get("qty") or 1
                components = []
                for comp in packed_by_row[row_id]:
                    comp_copy = dict(comp)
                    # Restore per-unit qty
                    if parent_qty > 0:
                        comp_copy["qty"] = comp_copy["qty"] / parent_qty
                    components.append(comp_copy)
                item["components"] = components
            else:
                # No packed items from invoice — check if item is a Product Bundle
                # and fetch components from the bundle definition
                item_code = item.get("item_code")
                if item_code and is_product_bundle(item_code):
                    bundle_items = frappe.db.sql("""
                        SELECT pbi.item_code, pbi.qty, pbi.uom, pbi.description,
                               i.item_name, i.stock_uom
                        FROM `tabProduct Bundle Item` pbi
                        LEFT JOIN `tabItem` i ON i.name = pbi.item_code
                        WHERE pbi.parent = %s
                    """, item_code, as_dict=True)
                    item["components"] = [{
                        "parent_item": item_code,
                        "item_code": bi.item_code,
                        "item_name": bi.item_name or bi.item_code,
                        "qty": bi.qty or 1,
                        "uom": bi.uom or bi.stock_uom or "Unit",
                        "warehouse": item.get("warehouse") or "",
                        "conversion_factor": 1,
                        "rate": 0,
                    } for bi in bundle_items]
                    item["is_bundle"] = 1
                else:
                    item["components"] = []

        last_order = {
            "invoice_name": inv.name,
            "date": inv.posting_date,
            "grand_total": inv.grand_total,
            "currency": inv.currency,
            "order_type": inv.custom_order_type,
            "branch": inv.branch or "",
            "items": last_order_items,
            "packed_items": packed_items
        }

    # Customer notes (from comment)
    notes = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "Customer",
            "reference_name": customer,
            "comment_type": "Comment"
        },
        fields=["content", "creation", "owner"],
        order_by="creation desc",
        limit=5
    )

    # Coupons — total count + the customer's unused coupons (used = 0)
    coupons = []
    coupons_total = 0
    coupons_unused = 0
    try:
        coupons_total = frappe.db.count("Coupon Code", {"customer": customer})
        coupons_unused = frappe.db.count("Coupon Code", {"customer": customer, "used": 0})
        coupons = frappe.get_all(
            "Coupon Code",
            filters={"customer": customer, "used": 0},
            fields=["name", "coupon_code", "pricing_rule", "valid_from", "valid_upto"],
            order_by="valid_upto desc",
            limit=50,
        )
    except Exception:
        pass

    # Approved, unused compensation coupons — surfaced as a "customer notification"
    # so any Call Center Agent can read the code out and apply it at checkout.
    compensation_coupons = []
    try:
        if frappe.db.exists("DocType", "POS Coupon"):
            compensation_coupons = frappe.db.sql(
                """
                SELECT
                    pc.name, pc.coupon_code, pc.discount_type, pc.discount_percentage,
                    pc.discount_amount, pc.valid_upto, ccr.complaint_number
                FROM `tabPOS Coupon` pc
                INNER JOIN `tabCompensation Coupon Request` ccr ON ccr.pos_coupon = pc.name
                WHERE pc.customer = %s AND pc.used = 0 AND pc.disabled = 0
                ORDER BY pc.valid_upto ASC
                """,
                (customer,),
                as_dict=True,
            )
    except Exception:
        pass

    return {
        "customer_name": cust.customer_name,
        "customer_type": customer_type,
        "is_vip": bool(cust.get("custom_vip")),
        "is_blacklist": bool(cust.get("custom_black_list")) or cust.get("custom_is_blacklist") == "Yes",
        "favorite_item": cust.get("custom_favorite_item") or "",
        "favorite_branch": cust.get("custom_favorite_branch") or "",
        "last_branch": cust.get("custom_last_branch") or "",
        "total_orders": actual_total_orders,
        "last_order_at": str(cust.get("custom_last_order_at") or ""),
        "last_order": last_order,
        "branch_total_orders": branch_total_orders,
        "last_order_in_branch": last_order_in_branch,
        "notes": notes,
        "coupons": coupons,
        "coupons_total": coupons_total,
        "coupons_unused": coupons_unused,
        "compensation_coupons": compensation_coupons,
        "mobile_no": cust.get("mobile_no") or "",
        "loyalty_program": cust.get("loyalty_program") or "",
    }


@frappe.whitelist()
def add_customer_note(customer, note):
    """Add a note/comment to a customer."""
    if not customer or not note:
        frappe.throw(_("Customer and note are required"))

    comment = frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Comment",
        "reference_doctype": "Customer",
        "reference_name": customer,
        "content": note
    })
    comment.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"name": comment.name, "content": comment.content, "creation": str(comment.creation), "owner": comment.owner}


@frappe.whitelist()
def get_complaint_types():
    """Return available complaint types."""
    return frappe.get_all("Complaint Type", fields=["name"], order_by="name")


@frappe.whitelist()
def get_all_complaints(limit=100, status=None):
    """Return all complaints for the Complaints management page."""
    filters = {}
    if status:
        filters["status"] = status

    return frappe.get_all(
        "Customer Complaint",
        filters=filters,
        fields=[
            "name",
            "custom_complaint_number",
            "customer",
            "customer_name",
            "custome_phone",
            "type",
            "status",
            "branch",
            "owner",
            "complaint_date",
            "complaint_details",
            "custom_response_by",
            "creation",
        ],
        order_by="creation desc",
        limit=frappe.utils.cint(limit),
    )


@frappe.whitelist()
def get_customer_complaints(customer, limit=20):
    """Return complaints filed for a specific customer, newest first."""
    if not customer:
        return []
    return frappe.get_all(
        "Customer Complaint",
        filters={"customer": customer},
        fields=[
            "name",
            "custom_complaint_number",
            "status",
            "complaint_date",
            "complaint_details",
            "type",
            "custom_response_by",
            "creation",
            "custom_order_reference",
        ],
        order_by="creation desc",
        limit=frappe.utils.cint(limit),
    )


@frappe.whitelist()
def get_order_context_for_complaint(order_doctype, order_reference):
    """Resolve order/branch/business-day/cashier-shift/delivery context for a
    complaint being filed against a specific order (Sales Invoice/Sales Order).
    """
    if not order_doctype or not order_reference:
        frappe.throw(_("Order doctype and reference are required"))
    if order_doctype not in ("Sales Invoice", "Sales Order"):
        frappe.throw(_("Invalid order doctype"))
    if not frappe.db.exists(order_doctype, order_reference):
        frappe.throw(_("{0} {1} not found").format(order_doctype, order_reference))

    order = frappe.db.get_value(
        order_doctype, order_reference,
        [
            "name", "customer", "branch", "status", "docstatus",
            "posting_date", "posting_time", "custom_order_type",
            "custom_pos_business_day", "custom_pos_cashier_shift",
        ],
        as_dict=True,
    )

    # An order can go through several Delivery Assignments (reassignment after
    # a failed/returned delivery) — only the latest one is relevant here.
    delivery_assignment = frappe.db.get_value(
        "Delivery Assignment",
        {"order_doctype": order_doctype, "order_reference": order_reference},
        ["name", "status"],
        as_dict=True,
        order_by="creation desc",
    )

    # "Delivery Type" reflects the delivery's live status (Assigned/Picked Up/
    # Out for Delivery/Delivered/Returned/Failed) from its Delivery Assignment.
    # Orders with no assignment (e.g. Pickup/Dine-in) fall back to the order's
    # own channel (custom_order_type).
    delivery_type = (delivery_assignment.get("status") if delivery_assignment else None) or order.custom_order_type or ""

    return {
        "order_number": order.name,
        "customer": order.customer,
        "branch": order.branch or "",
        "order_status": order.status,
        "order_datetime": f"{order.posting_date} {order.posting_time}" if order.posting_date else None,
        "delivery_type": delivery_type,
        "pos_business_day": order.custom_pos_business_day or "",
        "pos_cashier_shift": order.custom_pos_cashier_shift or "",
        "assigned_delivery": delivery_assignment.get("name") if delivery_assignment else "",
    }


@frappe.whitelist()
def create_customer_complaint(customer, complaint_details, complaint_type=None, branch=None, response_by=None,
                              order_doctype=None, order_reference=None):
    """Create a new Customer Complaint and assign a sequential complaint number."""
    if not customer or not complaint_details:
        frappe.throw(_("Customer and complaint details are required"))

    cust = frappe.db.get_value("Customer", customer, ["customer_name", "mobile_no"], as_dict=True)
    if not cust:
        frappe.throw(_("Customer {0} not found").format(customer))

    # Sequential complaint number (global, zero-padded to 5 digits)
    count = frappe.db.count("Customer Complaint")
    complaint_number = "CC-{:05d}".format(count + 1)

    order_context = {}
    if order_doctype and order_reference:
        order_context = get_order_context_for_complaint(order_doctype, order_reference)
        branch = branch or order_context.get("branch")

    doc = frappe.get_doc({
        "doctype": "Customer Complaint",
        "customer": customer,
        "customer_name": cust.customer_name,
        "custome_phone": cust.mobile_no or "",
        "complaint_details": complaint_details,
        "type": complaint_type or None,
        "branch": branch or None,
        "status": "New",
        "complaint_date": frappe.utils.now_datetime(),
        "custom_complaint_number": complaint_number,
        "custom_response_by": response_by or None,
        "custom_order_doctype": order_doctype or None,
        "custom_order_reference": order_reference or None,
        "custom_pos_business_day": order_context.get("pos_business_day") or None,
        "custom_pos_cashier_shift": order_context.get("pos_cashier_shift") or None,
        "custom_assigned_delivery": order_context.get("assigned_delivery") or None,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    from ecs_posnext.api.business_day import log_pos_event
    log_pos_event(
        action="Complaint Created",
        reference_doctype="Customer Complaint",
        reference_name=doc.name,
        new_value="New",
        reason=f"Complaint {complaint_number} filed for customer {customer}",
    )

    return {
        "name": doc.name,
        "custom_complaint_number": complaint_number,
        "customer": doc.customer,
        "customer_name": doc.customer_name,
        "custome_phone": doc.custome_phone,
        "status": doc.status,
        "complaint_date": str(doc.complaint_date or doc.creation),
        "complaint_details": doc.complaint_details,
        "type": doc.type,
        "custom_response_by": str(doc.custom_response_by) if doc.custom_response_by else None,
        "custom_order_doctype": doc.custom_order_doctype,
        "custom_order_reference": doc.custom_order_reference,
        "custom_pos_business_day": doc.custom_pos_business_day,
        "custom_pos_cashier_shift": doc.custom_pos_cashier_shift,
        "custom_assigned_delivery": doc.custom_assigned_delivery,
    }


COMPLAINT_STATUSES = [
    "New", "Under Review", "Pending Approval", "Approved", "Rejected",
    "Coupon Issued", "Coupon Redeemed", "Closed",
]


@frappe.whitelist()
def update_complaint_status(complaint_name, status):
    """Update the status of a complaint."""
    if status not in COMPLAINT_STATUSES:
        frappe.throw(_("Invalid status"))

    old_status = frappe.db.get_value("Customer Complaint", complaint_name, "status")
    frappe.db.set_value("Customer Complaint", complaint_name, "status", status)
    frappe.db.commit()

    from ecs_posnext.api.business_day import log_pos_event
    log_pos_event(
        action="Complaint Status Change",
        reference_doctype="Customer Complaint",
        reference_name=complaint_name,
        old_value=old_status,
        new_value=status,
    )
    return {"status": status}


@frappe.whitelist()
def get_complaint_detail(complaint_name):
    """Return full complaint document for the detail drawer, including the
    linked order's context (Order Number, Branch, Business Day, Cashier Shift,
    Customer, Order Date & Time, Order Status, Delivery Type, Assigned Delivery)
    when the complaint was filed against a specific order.
    """
    doc = frappe.get_doc("Customer Complaint", complaint_name)

    order_context = None
    if doc.get("custom_order_doctype") and doc.get("custom_order_reference"):
        try:
            order_context = get_order_context_for_complaint(
                doc.custom_order_doctype, doc.custom_order_reference
            )
        except Exception:
            order_context = None

    return {
        "name": doc.name,
        "custom_complaint_number": doc.get("custom_complaint_number") or "",
        "customer": doc.customer,
        "customer_name": doc.customer_name,
        "custome_phone": doc.custome_phone or "",
        "type": doc.type or "",
        "status": doc.status,
        "complaint_date": str(doc.complaint_date) if doc.complaint_date else None,
        "complaint_details": doc.complaint_details or "",
        "custom_response_by": str(doc.custom_response_by) if doc.get("custom_response_by") else None,
        "assigned_to": doc.assigned_to or "",
        "resolution_notes": doc.resolution_notes or "",
        "creation": str(doc.creation),
        "modified": str(doc.modified),
        "owner": doc.owner,
        "custom_order_doctype": doc.get("custom_order_doctype") or "",
        "custom_order_reference": doc.get("custom_order_reference") or "",
        "custom_pos_business_day": doc.get("custom_pos_business_day") or "",
        "custom_pos_cashier_shift": doc.get("custom_pos_cashier_shift") or "",
        "custom_assigned_delivery": doc.get("custom_assigned_delivery") or "",
        "order_context": order_context,
    }


@frappe.whitelist()
def update_complaint(complaint_name, status=None, assigned_to=None,
                     resolution_notes=None, response_by=None, complaint_type=None):
    """Update editable fields on a Customer Complaint."""
    doc = frappe.get_doc("Customer Complaint", complaint_name)
    changed = False
    old_status = doc.status

    if status and status != doc.status:
        if status not in COMPLAINT_STATUSES:
            frappe.throw(_("Invalid status"))
        doc.status = status
        changed = True

    if assigned_to is not None:
        doc.assigned_to = assigned_to or None
        changed = True

    if resolution_notes is not None:
        doc.resolution_notes = resolution_notes
        changed = True

    if response_by is not None:
        doc.custom_response_by = response_by or None
        changed = True

    if complaint_type is not None:
        doc.type = complaint_type or None
        changed = True

    if changed:
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        if doc.status != old_status:
            from ecs_posnext.api.business_day import log_pos_event
            log_pos_event(
                action="Complaint Status Change",
                reference_doctype="Customer Complaint",
                reference_name=doc.name,
                old_value=old_status,
                new_value=doc.status,
            )

    return {
        "name": doc.name,
        "status": doc.status,
        "assigned_to": doc.assigned_to or "",
        "resolution_notes": doc.resolution_notes or "",
        "custom_response_by": str(doc.custom_response_by) if doc.get("custom_response_by") else None,
        "type": doc.type or "",
    }


@frappe.whitelist()
def get_users_for_assignment():
    """Return active system users for the assign-to dropdown."""
    return frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User", "name": ["!=", "Administrator"]},
        fields=["name", "full_name", "user_image"],
        order_by="full_name asc",
        limit=100,
    )


def create_complaint_coupon(customer, discount_type, discount_value,
                            valid_upto=None, max_uses=1, company=None,
                            branch=None, complaint_name=None,
                            include_fees=False, fees_amount=0):
    """Create a POS Coupon for a customer as complaint compensation.

    Not whitelisted: coupons are only ever minted after a Compensation Coupon
    Request is approved (see approve_coupon_request). Cashiers request; a Call
    Center manager approves, which calls this.
    """
    import random, string
    from frappe.utils import today, add_days

    if not customer:
        frappe.throw(_("Customer is required"))

    discount_value = frappe.utils.flt(discount_value)
    if discount_value <= 0:
        frappe.throw(_("Discount value must be greater than zero"))
    if discount_type not in ("Percentage", "Amount"):
        frappe.throw(_("Invalid discount type"))
    if discount_type == "Percentage" and discount_value > 100:
        frappe.throw(_("Percentage cannot exceed 100"))

    cust = frappe.db.get_value(
        "Customer", customer,
        ["customer_name", "mobile_no", "email_id"],
        as_dict=True
    )
    if not cust:
        frappe.throw(_("Customer not found"))

    # Auto-generate a unique coupon code
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    coupon_code = f"COMP-{suffix}"
    while frappe.db.exists("POS Coupon", {"coupon_code": coupon_code}):
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        coupon_code = f"COMP-{suffix}"

    if not company:
        company = frappe.defaults.get_defaults().get("company") or \
                  frappe.db.get_single_value("Global Defaults", "default_company")

    coupon_name = f"Compensation - {cust.customer_name} - {coupon_code}"
    expiry = valid_upto if valid_upto else add_days(today(), 30)

    fees_amount = frappe.utils.flt(fees_amount) if include_fees and discount_type == "Amount" else 0
    coupon_amount = discount_value + fees_amount if discount_type == "Amount" else 0

    doc = frappe.get_doc({
        "doctype": "POS Coupon",
        "coupon_name": coupon_name,
        "coupon_type": "Gift Card",
        "coupon_code": coupon_code,
        "customer": customer,
        "customer_name": cust.customer_name,
        "mobile_no": cust.mobile_no or "",
        "email_id": cust.email_id or "",
        "company": company,
        "discount_type": discount_type,
        "discount_percentage": discount_value if discount_type == "Percentage" else 0,
        "discount_amount": coupon_amount if discount_type == "Amount" else 0,
        "apply_on": "Grand Total",
        "valid_from": today(),
        "valid_upto": expiry,
        "maximum_use": frappe.utils.cint(max_uses) or 1,
        "one_use": 1 if frappe.utils.cint(max_uses) == 1 else 0,
        "used": 0,
    })
    doc.insert(ignore_permissions=True)

    # Create journal entry to charge the branch for the discount (Amount type only)
    je_name = None
    if discount_type == "Amount":
        je_name = _create_compensation_journal_entry(
            company=company,
            branch=branch,
            discount_amount=discount_value,
            coupon_code=coupon_code,
            customer_name=cust.customer_name,
            complaint_name=complaint_name,
            fees_amount=fees_amount,
        )

    frappe.db.commit()

    return {
        "name": doc.name,
        "coupon_code": coupon_code,
        "coupon_name": coupon_name,
        "discount_type": discount_type,
        "discount_value": discount_value,
        "valid_upto": str(expiry),
        "maximum_use": doc.maximum_use,
        "journal_entry": je_name,
    }


def _create_compensation_journal_entry(company, branch, discount_amount, coupon_code, customer_name,
                                       complaint_name=None, fees_amount=0):
    """
    Create a Journal Entry that debits the branch for the compensation coupon amount.
      Dr: Compensation Expense Account  (branch cost center)   — coupon value
      Dr: Compensation Fees Account     (branch cost center)   — delivery fees (optional)
      Cr: Compensation Credit Account                          — total
    Account names are read from POS Settings. Fails silently if not configured.
    """
    try:
        # POS Settings is not a Single doctype — query by branch first, fall back to any enabled record
        filters = {"branch": branch} if branch else {}
        pos_settings_list = frappe.get_all(
            "POS Settings",
            filters=filters,
            fields=["compensation_expense_account", "compensation_credit_account", "compensation_fees_account"],
            limit=1,
        )
        if not pos_settings_list and branch:
            pos_settings_list = frappe.get_all(
                "POS Settings",
                fields=["compensation_expense_account", "compensation_credit_account", "compensation_fees_account"],
                limit=1,
            )

        pos_cfg = pos_settings_list[0] if pos_settings_list else {}
        expense_account = pos_cfg.get("compensation_expense_account")
        credit_account  = pos_cfg.get("compensation_credit_account")
        fees_account    = pos_cfg.get("compensation_fees_account")

        if not expense_account or not credit_account:
            frappe.log_error(
                f"Compensation accounts not configured in POS Settings for branch '{branch}'. "
                f"Skipping JE for coupon {coupon_code}.",
                "Compensation JE – Missing Config"
            )
            return None

        fees_amount = frappe.utils.flt(fees_amount)
        if fees_amount and not fees_account:
            frappe.log_error(
                f"Delivery fees requested but compensation_fees_account not configured in POS Settings "
                f"for branch '{branch}'. Fees will be skipped for coupon {coupon_code}.",
                "Compensation JE – Missing Fees Account"
            )
            fees_amount = 0

        # Resolve branch cost center
        cost_center = None
        if branch:
            cost_center = (
                frappe.db.get_value("Cost Center", {"branch": branch, "company": company}, "name")
                or frappe.db.get_value("Cost Center", {"cost_center_name": branch, "company": company}, "name")
            )

        remark = f"تعويض عميل – كوبون: {coupon_code} – {customer_name}"
        if complaint_name:
            remark += f" – شكوى: {complaint_name}"

        total_credit = discount_amount + fees_amount

        accounts = [
            {
                "account": expense_account,
                "debit_in_account_currency": discount_amount,
                "credit_in_account_currency": 0,
                "cost_center": cost_center,
            },
        ]
        if fees_amount:
            accounts.append({
                "account": fees_account,
                "debit_in_account_currency": fees_amount,
                "credit_in_account_currency": 0,
                "cost_center": cost_center,
            })
        accounts.append({
            "account": credit_account,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": total_credit,
        })

        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "company": company,
            "posting_date": frappe.utils.today(),
            "user_remark": remark,
            "accounts": accounts,
        })
        je.insert(ignore_permissions=True)
        je.submit()
        frappe.logger().info(f"Compensation JE {je.name} created for coupon {coupon_code}")
        return je.name

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Compensation JE Error – coupon {coupon_code}")
        return None


@frappe.whitelist()
def get_daily_complaints_report(report_date=None):
    """Return complaints summary and list for a given date (default: today)."""
    from frappe.utils import today, getdate

    target_date = getdate(report_date) if report_date else getdate(today())
    date_str = str(target_date)

    rows = frappe.db.sql("""
        SELECT
            name,
            custom_complaint_number,
            customer,
            customer_name,
            custome_phone,
            type,
            status,
            complaint_date,
            complaint_details,
            custom_response_by
        FROM `tabCustomer Complaint`
        WHERE DATE(creation) = %s
        ORDER BY creation ASC
    """, (date_str,), as_dict=True)

    # Summary counts by status
    summary = {"Open": 0, "In Progress": 0, "Resolved": 0, "Rejected": 0, "total": len(rows)}
    by_type = {}

    for r in rows:
        r["complaint_date"] = str(r["complaint_date"]) if r["complaint_date"] else None
        r["custom_response_by"] = str(r["custom_response_by"]) if r["custom_response_by"] else None
        summary[r["status"]] = summary.get(r["status"], 0) + 1
        t = r["type"] or _("Unclassified")
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "date": date_str,
        "summary": summary,
        "by_type": [{"type": k, "count": v} for k, v in sorted(by_type.items(), key=lambda x: -x[1])],
        "complaints": [dict(r) for r in rows],
    }


# ---------------------------------------------------------------------------
# Compensation coupon approval workflow
#
# A cashier/agent requests a compensation coupon from the Complaints page. The
# request is created Pending and shown on the Need My Action page, where a Call
# Center manager approves it — which mints the actual POS Coupon (and its
# journal entry) — or rejects it, creating nothing.
# ---------------------------------------------------------------------------

COUPON_APPROVER_ROLES = ("System Manager", "Call center manager", "Deputy Call Center Manager")


def _require_coupon_approver():
    user = frappe.session.user
    if user == "Administrator":
        return
    if not set(COUPON_APPROVER_ROLES) & set(frappe.get_roles(user)):
        frappe.throw(_("You are not permitted to approve compensation coupons."), frappe.PermissionError)


def _publish_coupon_request_changed(action, branch=None):
    """Broadcast a coupon-request change so the Need My Action page refreshes live."""
    try:
        frappe.publish_realtime(
            event="coupon_request_changed",
            message={"action": action, "branch": branch, "timestamp": frappe.utils.now()},
            user=None,
            after_commit=True,
        )
    except Exception:
        # Realtime is best-effort — never fail the request because the socket is down.
        pass


@frappe.whitelist()
def request_complaint_coupon(customer, discount_type, discount_value,
                             valid_upto=None, max_uses=1, branch=None,
                             complaint_name=None, include_fees=False, fees_amount=0):
    """Create a Pending compensation-coupon request for manager approval.

    No POS Coupon is created here — that happens only on approval.
    """
    if not customer or not frappe.db.exists("Customer", customer):
        frappe.throw(_("Customer not found"))

    discount_value = frappe.utils.flt(discount_value)
    if discount_value <= 0:
        frappe.throw(_("Discount value must be greater than zero"))
    if discount_type not in ("Percentage", "Amount"):
        frappe.throw(_("Invalid discount type"))
    if discount_type == "Percentage" and discount_value > 100:
        frappe.throw(_("Percentage cannot exceed 100"))

    include_fees = 1 if frappe.parse_json(include_fees) else 0
    fees_amount = frappe.utils.flt(fees_amount) if include_fees and discount_type == "Amount" else 0

    cust = frappe.db.get_value(
        "Customer", customer, ["customer_name", "mobile_no"], as_dict=True
    ) or {}

    complaint_number = None
    if complaint_name:
        complaint_number = frappe.db.get_value(
            "Customer Complaint", complaint_name, "custom_complaint_number"
        )
        if not branch:
            branch = frappe.db.get_value("Customer Complaint", complaint_name, "branch")

    doc = frappe.get_doc({
        "doctype": "Compensation Coupon Request",
        "customer": customer,
        "customer_name": cust.get("customer_name"),
        "mobile": cust.get("mobile_no") or "",
        "branch": branch or None,
        "complaint": complaint_name or None,
        "complaint_number": complaint_number or None,
        "discount_type": discount_type,
        "discount_value": discount_value,
        "valid_upto": valid_upto or None,
        "max_uses": frappe.utils.cint(max_uses) or 1,
        "include_fees": include_fees,
        "fees_amount": fees_amount,
        "status": "Pending",
        "requested_by": frappe.session.user,
    }).insert(ignore_permissions=True)

    if complaint_name and frappe.db.exists("Customer Complaint", complaint_name):
        frappe.db.set_value("Customer Complaint", complaint_name, "status", "Pending Approval")

    frappe.db.commit()

    from ecs_posnext.api.business_day import log_pos_event
    log_pos_event(
        action="Coupon Request",
        reference_doctype="Compensation Coupon Request",
        reference_name=doc.name,
        new_value="Pending",
        reason=f"Compensation coupon requested for customer {customer}" + (f" (complaint {complaint_number})" if complaint_number else ""),
    )

    _publish_coupon_request_changed("create", doc.branch)
    return {"name": doc.name, "status": "Pending"}


@frappe.whitelist()
def get_pending_coupon_requests():
    """Pending compensation-coupon requests for the Need My Action page."""
    filters = {"status": "Pending"}
    try:
        from ecs_posnext.api.invoices import _get_user_branch_filter_info
        branch, is_cc = _get_user_branch_filter_info()
        if not is_cc and branch:
            filters["branch"] = branch
    except Exception:
        pass
    return frappe.get_all(
        "Compensation Coupon Request",
        filters=filters,
        fields=[
            "name", "customer", "customer_name", "mobile", "branch",
            "complaint", "complaint_number", "discount_type", "discount_value",
            "valid_upto", "max_uses", "include_fees", "fees_amount",
            "requested_by", "creation",
        ],
        order_by="creation desc",
    )


def _notify_coupon_request_decision(doc, decision, extra_message=None):
    """Notify the requesting agent that their coupon request was approved/rejected."""
    if not doc.requested_by:
        return
    subject = _("Your compensation coupon request was {0}").format(decision)
    message = _("Coupon request {0} for customer {1} was {2} by {3}.").format(
        doc.name, doc.customer_name or doc.customer, decision.lower(), frappe.session.user
    )
    if extra_message:
        message = f"{message} {extra_message}"
    try:
        notification = frappe.new_doc("Notification Log")
        notification.update({
            "subject": subject,
            "email_content": message,
            "for_user": doc.requested_by,
            "type": "Alert",
            "document_type": "Compensation Coupon Request",
            "document_name": doc.name,
        })
        notification.flags.ignore_permissions = True
        notification.insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Coupon request decision notification failed")


@frappe.whitelist()
def approve_coupon_request(name):
    """Approve a request — mint the POS Coupon and mark the request Approved."""
    _require_coupon_approver()
    doc = frappe.get_doc("Compensation Coupon Request", name)
    if doc.status != "Pending":
        frappe.throw(_("This request is already {0}.").format(doc.status))

    result = create_complaint_coupon(
        customer=doc.customer,
        discount_type=doc.discount_type,
        discount_value=doc.discount_value,
        valid_upto=str(doc.valid_upto) if doc.valid_upto else None,
        max_uses=doc.max_uses,
        branch=doc.branch,
        complaint_name=doc.complaint,
        include_fees=doc.include_fees,
        fees_amount=doc.fees_amount,
    )

    doc.status = "Approved"
    doc.approved_by = frappe.session.user
    doc.coupon_code = result.get("coupon_code")
    doc.pos_coupon = result.get("name")
    doc.save(ignore_permissions=True)

    if doc.complaint and frappe.db.exists("Customer Complaint", doc.complaint):
        frappe.db.set_value("Customer Complaint", doc.complaint, "status", "Coupon Issued")

    frappe.db.commit()

    from ecs_posnext.api.business_day import log_pos_event
    log_pos_event(
        action="Coupon Approval",
        reference_doctype="Compensation Coupon Request",
        reference_name=doc.name,
        old_value="Pending",
        new_value="Approved",
        reason=f"Coupon {result.get('coupon_code')} minted for customer {doc.customer}",
    )

    _notify_coupon_request_decision(doc, "Approved", extra_message=_("Coupon code: {0}").format(result.get("coupon_code")))
    _publish_coupon_request_changed("approve", doc.branch)
    return {"status": "Approved", "coupon_code": result.get("coupon_code")}


@frappe.whitelist()
def reject_coupon_request(name):
    """Reject a request — create no coupon."""
    _require_coupon_approver()
    doc = frappe.get_doc("Compensation Coupon Request", name)
    if doc.status != "Pending":
        frappe.throw(_("This request is already {0}.").format(doc.status))
    doc.status = "Rejected"
    doc.approved_by = frappe.session.user
    doc.save(ignore_permissions=True)

    if doc.complaint and frappe.db.exists("Customer Complaint", doc.complaint):
        frappe.db.set_value("Customer Complaint", doc.complaint, "status", "Under Review")

    frappe.db.commit()

    from ecs_posnext.api.business_day import log_pos_event
    log_pos_event(
        action="Coupon Rejection",
        reference_doctype="Compensation Coupon Request",
        reference_name=doc.name,
        old_value="Pending",
        new_value="Rejected",
    )

    _notify_coupon_request_decision(doc, "Rejected")
    _publish_coupon_request_changed("reject", doc.branch)
    return {"status": "Rejected"}
