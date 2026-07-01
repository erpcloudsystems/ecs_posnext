import frappe
from frappe import _
from frappe.utils import flt, nowdate, now_datetime


@frappe.whitelist()
def get_pending_delivery_orders(branch=None):
    """Get orders pending delivery assignment"""
    filters = {
        "docstatus": 1,
        "custom_so_type": "Delivery",
        "custom_order_in_kitchen_": ["not in", ["Completed"]],
    }
    
    if branch:
        filters["branch"] = branch
    
    orders = frappe.get_all(
        "Sales Order",
        filters=filters,
        fields=[
            "name",
            "custom_number_order",
            "customer_name",
            "contact_mobile",
            "grand_total",
            "branch",
            "driver",
            "custom_order_in_kitchen_",
            "transaction_date",
            "creation",
        ],
        order_by="creation DESC",
        limit_page_length=200,
    )
    
    # Get driver info for assigned orders
    for order in orders:
        if order.driver:
            driver_info = frappe.db.get_value(
                "Driver", order.driver, ["full_name", "cell_number"], as_dict=True
            )
            if driver_info:
                order["driver_name"] = driver_info.full_name
                order["driver_phone"] = driver_info.cell_number
    
    return orders


@frappe.whitelist()
def get_drivers_with_capacity(branch=None):
    """Get drivers with their current order count and capacity"""
    filters = {}
    if branch:
        filters["custom_branch"] = branch
    
    drivers = frappe.get_all(
        "Driver",
        filters=filters,
        fields=["name", "full_name", "cell_number", "custom_branch"],
        ignore_permissions=True,
        limit=100
    )
    
    # Get capacity from POS Profile
    pos_profile = None
    if branch:
        pos_profile = frappe.db.get_value(
            "POS Profile",
            {"branch": branch, "disabled": 0},
            ["name", "custom_driver_capacity"],
            as_dict=True
        )
    
    capacity = flt(pos_profile.get("custom_driver_capacity") if pos_profile else 0) or 5  # Default 5
    
    # Get current active orders count for each driver
    for driver in drivers:
        active_orders = frappe.db.count(
            "Sales Order",
            filters={
                "driver": driver.name,
                "docstatus": 1,
                "custom_order_in_kitchen_": ["in", ["Delivery", "Out for Delivery"]],
            }
        )
        driver["active_orders"] = active_orders
        driver["capacity"] = capacity
        driver["available_slots"] = max(0, capacity - active_orders)
        driver["is_available"] = active_orders < capacity
    
    return drivers


@frappe.whitelist()
def assign_driver_to_order(order_name, driver_name):
    """Assign a driver to an order with capacity check"""
    if not order_name or not driver_name:
        frappe.throw(_("Order and Driver are required"))
    
    # Get driver info
    driver = frappe.get_doc("Driver", driver_name)
    branch = driver.get("custom_branch")
    
    # Get capacity from POS Profile
    pos_profile = frappe.db.get_value(
        "POS Profile",
        {"branch": branch, "disabled": 0},
        ["name", "custom_driver_capacity"],
        as_dict=True
    )
    
    capacity = flt(pos_profile.get("custom_driver_capacity") if pos_profile else 0) or 5
    
    # Check current active orders
    active_orders = frappe.db.count(
        "Sales Order",
        filters={
            "driver": driver_name,
            "docstatus": 1,
            "custom_order_in_kitchen_": ["in", ["Delivery", "Out for Delivery"]],
        }
    )
    
    if active_orders >= capacity:
        frappe.throw(
            _("Driver {0} has reached maximum capacity ({1} orders). Cannot assign more orders.").format(
                driver.full_name, int(capacity)
            )
        )
    
    # Assign driver to order
    so = frappe.get_doc("Sales Order", order_name)
    so.driver = driver_name
    so.custom_order_in_kitchen_ = "Delivery"
    so.custom_assigned_time = now_datetime()
    so.flags.ignore_permissions = True
    so.save()
    
    # Update Sales Invoice if exists
    sales_invoice = frappe.db.sql(
        """SELECT parent FROM `tabSales Invoice Item` WHERE sales_order = %s""",
        (order_name,),
        as_dict=True
    )
    if sales_invoice:
        frappe.db.set_value("Sales Invoice", sales_invoice[0].parent, "driver", driver_name)
    
    frappe.db.commit()
    
    return {
        "status": "success",
        "message": _("Driver {0} assigned to order {1}").format(driver.full_name, order_name)
    }


@frappe.whitelist()
def confirm_delivery(order_name):
    """Driver confirms delivery completion"""
    if not order_name:
        frappe.throw(_("Order is required"))
    
    so = frappe.get_doc("Sales Order", order_name)
    
    if not so.driver:
        frappe.throw(_("No driver assigned to this order"))
    
    so.custom_delivered = 1
    so.custom_order_in_kitchen_ = "Completed"
    so.custom_delivered_time = now_datetime()
    so.flags.ignore_permissions = True
    so.save()
    frappe.db.commit()
    
    return {
        "status": "success",
        "message": _("Order {0} marked as delivered").format(order_name)
    }


@frappe.whitelist()
def get_driver_active_orders(driver_name=None):
    """Get active orders for a driver"""
    if not driver_name:
        # Get driver linked to current user
        driver_name = frappe.db.get_value("Driver", {"user": frappe.session.user}, "name")
    
    if not driver_name:
        return []
    
    orders = frappe.get_all(
        "Sales Order",
        filters={
            "driver": driver_name,
            "docstatus": 1,
            "custom_order_in_kitchen_": ["in", ["Delivery", "Out for Delivery"]],
        },
        fields=[
            "name",
            "custom_number_order",
            "customer_name",
            "contact_mobile",
            "grand_total",
            "custom_branch",
            "custom_order_in_kitchen_",
            "creation",
        ],
        order_by="creation asc",
    )
    
    return orders


@frappe.whitelist()
def get_branches_for_dispatcher():
    """Get branches user has permission to manage"""
    allowed_branches = frappe.get_list(
        "User Permission",
        filters={
            "user": frappe.session.user,
            "allow": "Branch"
        },
        pluck="for_value"
    )
    
    if allowed_branches:
        branches = frappe.get_all(
            "Branch",
            filters={"name": ["in", allowed_branches]},
            fields=["name"],
            limit=100
        )
    else:
        branches = frappe.get_all("Branch", fields=["name"], limit=100)
    
    return [b.name for b in branches]
