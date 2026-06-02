# -*- coding: utf-8 -*-
"""
Create custom fields on Sales Invoice and Sales Invoice Item
needed for kitchen order tracking.

Run with:
    bench --site <sitename> execute ecs_posnext.api.setup_kitchen_fields.setup
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup():
    """Create all kitchen-related custom fields on Sales Invoice doctypes."""
    custom_fields = {
        "Sales Invoice": [
            {
                "fieldname": "custom_order_in_kitchen_",
                "fieldtype": "Select",
                "label": "Order In Kitchen",
                "options": "Pending\nPreparing\nDining\nPacking\nReady to Pick Up\nDelivery\nCompleted",
                "insert_after": "custom_so_type",
                "translatable": 0,
            },
            {
                "fieldname": "custom_skip_kitchen",
                "fieldtype": "Check",
                "label": "Skip Kitchen",
                "insert_after": "custom_order_in_kitchen_",
                "default": "0",
            },
            {
                "fieldname": "custom_time",
                "fieldtype": "Duration",
                "label": "Time",
                "insert_after": "custom_skip_kitchen",
            },
        ],
        "Sales Invoice Item": [
            {
                "fieldname": "custom_item_class",
                "fieldtype": "Data",
                "label": "Item Class",
                "insert_after": "item_name",
            },
            {
                "fieldname": "custom_item_status",
                "fieldtype": "Select",
                "label": "Item Status",
                "options": "Pending\nPreparing\nPacking\nDelivery\nCompleted",
                "insert_after": "custom_item_class",
            },
        ],
    }

    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    print("Kitchen order custom fields created successfully.")
