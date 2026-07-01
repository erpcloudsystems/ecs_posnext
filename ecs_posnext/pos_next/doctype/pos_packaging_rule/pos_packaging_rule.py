# Copyright (c) 2024, Youssef Restom and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class POSPackagingRule(Document):
    pass


@frappe.whitelist()
def get_packaging_items_for_order_type(order_type):
    """Get global packaging items for a specific order type"""
    rules = frappe.get_all(
        'POS Packaging Rule',
        filters={'order_type': order_type, 'enabled': 1},
        fields=['name']
    )
    
    if not rules:
        return []
    
    rule = frappe.get_doc('POS Packaging Rule', rules[0].name)
    return [
        {
            'item_code': item.item_code,
            'qty': item.qty,
            'uom': item.uom
        }
        for item in rule.packaging_items
    ]


@frappe.whitelist()
def get_all_packaging_for_item(item_code, order_type):
    """Get all packaging items (global + item-specific) for an item and order type"""
    packaging_items = []
    
    # 1. Get global packaging for order type
    global_items = get_packaging_items_for_order_type(order_type)
    packaging_items.extend(global_items)
    
    # 2. Get item-specific packaging
    item = frappe.get_cached_doc('Item', item_code)
    
    # Map order type to field name
    field_map = {
        'Delivery': 'packaging_delivery',
        'Dine-in': 'packaging_dinein',
        'Takeaway': 'packaging_takeaway'
    }
    
    field_name = field_map.get(order_type)
    if field_name and hasattr(item, field_name):
        item_packaging = getattr(item, field_name, []) or []
        for pkg in item_packaging:
            packaging_items.append({
                'item_code': pkg.item_code,
                'qty': pkg.qty,
                'uom': pkg.uom
            })
    
    return packaging_items


@frappe.whitelist()
def get_packaging_for_items(items, order_type):
    """Get aggregated packaging items for a list of items based on order type"""
    import json
    
    items_list = json.loads(items) if isinstance(items, str) else items
    
    # Map order type to field name
    field_map = {
        'Delivery': 'packaging_delivery',
        'Dinin': 'packaging_dinein',
        'Takeaway': 'packaging_takeaway',
        'Pickup': 'packaging_takeaway',
        'Car Service': 'packaging_takeaway',
        'Talabat': 'packaging_delivery'
    }
    
    field_name = field_map.get(order_type, 'packaging_delivery')
    
    # Aggregate packaging by item_code
    packaging_totals = {}
    
    for item in items_list:
        item_code = item.get('item_code')
        item_qty = item.get('qty', 1)
        
        if not item_code:
            continue
        
        # Get item packaging
        try:
            item_doc = frappe.get_cached_doc('Item', item_code)
            item_packaging = getattr(item_doc, field_name, []) or []
            
            for pkg in item_packaging:
                pkg_item_code = pkg.item_code
                pkg_qty = (pkg.qty or 1) * item_qty
                
                if pkg_item_code in packaging_totals:
                    packaging_totals[pkg_item_code]['qty'] += pkg_qty
                else:
                    # Get item name
                    pkg_item_name = frappe.db.get_value('Item', pkg_item_code, 'item_name') or pkg_item_code
                    packaging_totals[pkg_item_code] = {
                        'item_code': pkg_item_code,
                        'item_name': pkg_item_name,
                        'qty': pkg_qty,
                        'uom': pkg.uom or 'Unit'
                    }
        except Exception:
            continue
    
    return list(packaging_totals.values())
