import frappe
from frappe import _


@frappe.whitelist()
def create_item(
    item_code,
    item_name,
    item_group,
    item_name_arabic=None,
    item_classification=None,
    standard_rate=0,
    is_stock_item=0,
    enabled_item_bundle=0,
    custom_fast_sell=0,
    description=None,
    image=None
):
    """
    Create a new Item with bundle-compatible fields.
    
    Args:
        item_code: Unique item code
        item_name: Item name in English
        item_group: Item group (must exist)
        item_name_arabic: Item name in Arabic (optional)
        item_classification: Link to Item Classification (optional)
        standard_rate: Default selling price
        is_stock_item: Whether to track stock (0 or 1)
        enabled_item_bundle: Enable bundle customization (0 or 1)
        custom_fast_sell: Skip bundle dialog (0 or 1)
        description: Item description
        image: Image URL or path
    
    Returns:
        dict: Created item data or error message
    """
    try:
        if frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item {0} already exists").format(item_code)}
        
        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = item_name
        item.item_group = item_group
        item.stock_uom = "Unit"
        item.is_stock_item = is_stock_item
        item.standard_rate = standard_rate
        item.description = description or item_name
        
        if item_name_arabic:
            item.custom_item_name_arabic = item_name_arabic
        
        if item_classification:
            item.custom_item_classification = item_classification
        
        if image:
            item.image = image
        
        item.enabled_item_bundle = enabled_item_bundle
        item.custom_fast_sell = custom_fast_sell
        
        item.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Item {0} created successfully").format(item_code),
            "item": item.as_dict()
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Item Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def create_bundle_item(
    item_code,
    item_name,
    item_group,
    bundle_options,
    item_name_arabic=None,
    standard_rate=0,
    description=None,
    image=None,
    custom_fast_sell=0
):
    """
    Create a new Item with bundle options (custom_item_options table).
    
    Args:
        item_code: Unique item code
        item_name: Item name in English
        item_group: Item group
        bundle_options: List of bundle option dicts:
            [
                {
                    "item_code": "Spicy",
                    "item_name": "Spicy",
                    "item_classification": "Type",
                    "qty": 1,
                    "rate": 0,
                    "state": "Item Must Be Selected",  # or "Minimum 1 Item is Required In Section"
                    "max_required": 1,
                    "hide_from_pos": 0
                },
                ...
            ]
        item_name_arabic: Item name in Arabic (optional)
        standard_rate: Default selling price
        description: Item description
        image: Image URL
        custom_fast_sell: Skip bundle dialog (0 or 1)
    
    Returns:
        dict: Created item data or error message
    """
    try:
        if frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item {0} already exists").format(item_code)}
        
        if isinstance(bundle_options, str):
            import json
            bundle_options = json.loads(bundle_options)
        
        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = item_name
        item.item_group = item_group
        item.stock_uom = "Unit"
        item.is_stock_item = 0
        item.standard_rate = standard_rate
        item.description = description or item_name
        item.enabled_item_bundle = 1
        item.custom_fast_sell = custom_fast_sell
        
        if item_name_arabic:
            item.custom_item_name_arabic = item_name_arabic
        
        if image:
            item.image = image
        
        for opt in bundle_options:
            item.append("custom_item_options", {
                "item_code": opt.get("item_code"),
                "item_name": opt.get("item_name") or opt.get("item_code"),
                "item_classification": opt.get("item_classification"),
                "qty": opt.get("qty", 0),
                "rate": opt.get("rate", 0),
                "state": opt.get("state", ""),
                "max_required": opt.get("max_required", 1),
                "custom_hide_from_pos": opt.get("hide_from_pos", 0),
                "is_bundle": opt.get("is_bundle", 0),
                "custom_main_item": opt.get("main_item"),
                "custom_large": opt.get("is_large", 0),
                "custom_meduim": opt.get("is_medium", 0),
                "custom_variant": opt.get("variant", ""),
            })
        
        item.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Bundle Item {0} created successfully").format(item_code),
            "item": item.as_dict()
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Bundle Item Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def add_bundle_option(item_code, option):
    """
    Add a single bundle option to an existing item.
    
    Args:
        item_code: Existing item code
        option: Bundle option dict
    
    Returns:
        dict: Success or error message
    """
    try:
        if not frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item {0} not found").format(item_code)}
        
        if isinstance(option, str):
            import json
            option = json.loads(option)
        
        item = frappe.get_doc("Item", item_code)
        item.enabled_item_bundle = 1
        
        item.append("custom_item_options", {
            "item_code": option.get("item_code"),
            "item_name": option.get("item_name") or option.get("item_code"),
            "item_classification": option.get("item_classification"),
            "qty": option.get("qty", 0),
            "rate": option.get("rate", 0),
            "state": option.get("state", ""),
            "max_required": option.get("max_required", 1),
            "custom_hide_from_pos": option.get("hide_from_pos", 0),
            "custom_main_item": option.get("custom_main_item", ""),
            "custom_variant": option.get("variant", ""),
            "custom_let_customer_choose": option.get("let_customer_choose", 0),
        })
        
        item.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Option added to {0}").format(item_code)
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Add Bundle Option Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_item_classifications():
    """Get all Item Classifications for dropdown."""
    return frappe.get_all(
        "Item Classification",
        fields=["name", "item_classification"],
        order_by="name"
    )


@frappe.whitelist()
def get_item_groups():
    """Get all Item Groups for dropdown."""
    return frappe.get_all(
        "Item Group",
        fields=["name"],
        filters={"is_group": 0},
        order_by="name"
    )


@frappe.whitelist()
def get_items_for_bundle():
    """Get items that can be added as bundle options."""
    return frappe.get_all(
        "Item",
        fields=["item_code", "item_name", "custom_item_name_arabic", "custom_item_classification", "standard_rate", "image", "has_variants", "item_group", "modified"],
        filters={"disabled": 0},
        order_by="modified desc",
        limit=500
    )


@frappe.whitelist()
def get_item_with_options(item_code):
    """Get item details with its bundle options."""
    if not frappe.db.exists("Item", item_code):
        return {"success": False, "message": _("Item not found")}
    
    item = frappe.get_doc("Item", item_code)
    return {
        "success": True,
        "item": {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_name_arabic": item.custom_item_name_arabic,
            "item_group": item.item_group,
            "item_classification": item.custom_item_classification,
            "standard_rate": item.standard_rate,
            "enabled_item_bundle": item.enabled_item_bundle,
            "enable_product_bundle": frappe.db.exists("Product Bundle", {"new_item_code": item_code}),
            "custom_fast_sell": item.custom_fast_sell,
            "image": item.image,
            "bundle_options": [opt.as_dict() for opt in item.custom_item_options] if item.custom_item_options else []
        }
    }


@frappe.whitelist()
def update_item(item_code, updates):
    """
    Update an existing item.
    
    Args:
        item_code: Item to update
        updates: Dict of fields to update
    """
    try:
        if not frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item not found")}
        
        if isinstance(updates, str):
            import json
            updates = json.loads(updates)
        
        item = frappe.get_doc("Item", item_code)
        
        allowed_fields = [
            "item_name", "custom_item_name_arabic", "item_group",
            "custom_item_classification", "standard_rate", "description",
            "enabled_item_bundle", "custom_fast_sell", "image", "disabled"
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(item, field, value)
        
        item.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {"success": True, "message": _("Item updated successfully")}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Item Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def clear_bundle_options(item_code):
    """Remove all bundle options from an item."""
    try:
        if not frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item not found")}
        
        item = frappe.get_doc("Item", item_code)
        item.custom_item_options = []
        item.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {"success": True, "message": _("Bundle options cleared")}
        
    except Exception as e:
        return {"success": False, "message": str(e)}


# ============ Product Bundle (Stock Items) Management ============

@frappe.whitelist()
def get_product_bundle(item_code):
    """Get Product Bundle items for an item (stock items that will be deducted)."""
    try:
        # Get bundle name first
        bundle_name = frappe.db.get_value("Product Bundle", {"new_item_code": item_code}, "name")
        
        if not bundle_name:
            return {"success": True, "exists": False, "items": []}
        
        bundle = frappe.get_doc("Product Bundle", bundle_name)
        items = []
        for row in bundle.items:
            items.append({
                "item_code": row.item_code,
                "item_name": frappe.db.get_value("Item", row.item_code, "item_name") or row.item_code,
                "qty": row.qty,
                "rate": row.rate or 0,
                "uom": row.uom,
                "description": row.description,
                "custom_hide": row.get("custom_hide", 0),
                "custom_product_item_classification": row.get("custom_product_item_classification", ""),
                "custom_teigger_item": row.get("custom_teigger_item", ""),
                "custom_teigger_item_2": row.get("custom_teigger_item_2", ""),
                "custom_spicy": row.get("custom_spicy", 0),
                "custom_regular": row.get("custom_regular", 0),
            })
        
        return {
            "success": True,
            "exists": True,
            "bundle_name": bundle.name,
            "items": items
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Product Bundle Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def create_product_bundle(item_code, items):
    """
    Create or update Product Bundle for an item.
    
    Args:
        item_code: The parent item code (new_item_code in Product Bundle)
        items: List of bundle items:
            [
                {
                    "item_code": "RAW-CHICKEN",
                    "qty": 4,
                    "uom": "Unit",
                    "rate": 0,
                    "description": "",
                    "custom_hide": 0,
                    "custom_product_item_classification": "Pieces",
                    "custom_teigger_item": "",
                    "custom_spicy": 0,
                    "custom_regular": 0
                },
                ...
            ]
    """
    try:
        if isinstance(items, str):
            import json
            items = json.loads(items)
        
        # Check if Product Bundle already exists
        bundle_name = frappe.db.get_value("Product Bundle", {"new_item_code": item_code}, "name")
        
        if bundle_name:
            bundle = frappe.get_doc("Product Bundle", bundle_name)
            bundle.items = []
        else:
            bundle = frappe.new_doc("Product Bundle")
            bundle.new_item_code = item_code
        
        # Add items
        for item in items:
            bundle.append("items", {
                "item_code": item.get("item_code"),
                "qty": item.get("qty", 1),
                "uom": item.get("uom", "Unit"),
                "rate": item.get("rate", 0),
                "description": item.get("description", ""),
                "custom_hide": item.get("custom_hide", 0),
                "custom_product_item_classification": item.get("custom_product_item_classification", ""),
                "custom_teigger_item": item.get("custom_teigger_item", ""),
                "custom_teigger_item_2": item.get("custom_teigger_item_2", ""),
                "custom_spicy": item.get("custom_spicy", 0),
                "custom_regular": item.get("custom_regular", 0),
            })
        
        bundle.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Product Bundle saved successfully"),
            "bundle_name": bundle.name
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Product Bundle Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def add_product_bundle_item(item_code, bundle_item):
    """Add a single item to Product Bundle."""
    try:
        if isinstance(bundle_item, str):
            import json
            bundle_item = json.loads(bundle_item)
        
        bundle_name = frappe.db.get_value("Product Bundle", {"new_item_code": item_code}, "name")
        
        if not bundle_name:
            # Create new Product Bundle
            bundle = frappe.new_doc("Product Bundle")
            bundle.new_item_code = item_code
        else:
            bundle = frappe.get_doc("Product Bundle", bundle_name)
        
        bundle.append("items", {
            "item_code": bundle_item.get("item_code"),
            "qty": bundle_item.get("qty", 1),
            "uom": bundle_item.get("uom", "Unit"),
            "rate": bundle_item.get("rate", 0),
            "description": bundle_item.get("description", ""),
            "custom_hide": bundle_item.get("custom_hide", 0),
            "custom_product_item_classification": bundle_item.get("custom_product_item_classification", ""),
            "custom_teigger_item": bundle_item.get("custom_teigger_item", ""),
            "custom_teigger_item_2": bundle_item.get("custom_teigger_item_2", ""),
            "custom_spicy": bundle_item.get("custom_spicy", 0),
            "custom_regular": bundle_item.get("custom_regular", 0),
        })
        
        bundle.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {"success": True, "message": _("Item added to Product Bundle")}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Add Product Bundle Item Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def delete_product_bundle(item_code):
    """Delete or clear Product Bundle for an item."""
    try:
        # Get the bundle name first
        bundle_name = frappe.db.get_value("Product Bundle", {"new_item_code": item_code}, "name")
        
        if not bundle_name:
            return {"success": True, "message": _("Product Bundle not found")}
        
        try:
            # Try to delete the bundle
            frappe.delete_doc("Product Bundle", bundle_name, ignore_permissions=True)
            frappe.db.commit()
            return {"success": True, "message": _("Product Bundle deleted")}
        except frappe.LinkExistsError:
            # Bundle is linked to other documents, just clear the items instead
            bundle = frappe.get_doc("Product Bundle", bundle_name)
            bundle.items = []
            bundle.save(ignore_permissions=True)
            frappe.db.commit()
            return {"success": True, "message": _("Product Bundle items cleared (bundle is linked to existing documents)")}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Delete Product Bundle Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_stock_items():
    """Get stock items that can be added to Product Bundle."""
    return frappe.get_all(
        "Item",
        fields=["item_code", "item_name", "stock_uom", "standard_rate"],
        filters={"disabled": 0, "is_stock_item": 1},
        order_by="item_name",
        limit=500
    )


@frappe.whitelist()
def get_product_item_classifications():
    """Get all Product Item Classifications for dropdown."""
    return frappe.get_all(
        "Item Classification",
        fields=["name"],
        order_by="name"
    )


@frappe.whitelist()
def get_price_lists():
    """Get all enabled Price Lists for dropdown."""
    return frappe.get_all(
        "Price List",
        fields=["name", "currency"],
        filters={"enabled": 1, "selling": 1},
        order_by="name"
    )


@frappe.whitelist()
def get_item_price(item_code, price_list=None):
    """
    Get item price from Price List.
    
    Args:
        item_code: Item code to get price for
        price_list: Price List name (optional, uses default if not provided)
    
    Returns:
        dict: Item price details
    """
    if not price_list:
        # Get default selling price list
        price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
    
    if not price_list:
        # Fallback to standard rate
        standard_rate = frappe.db.get_value("Item", item_code, "standard_rate") or 0
        return {"price": standard_rate, "price_list": None}
    
    # Get price from Item Price
    item_price = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": price_list, "selling": 1},
        ["price_list_rate", "currency"],
        as_dict=True
    )
    
    if item_price:
        return {
            "price": item_price.price_list_rate,
            "currency": item_price.currency,
            "price_list": price_list
        }
    
    # Fallback to standard rate
    standard_rate = frappe.db.get_value("Item", item_code, "standard_rate") or 0
    return {"price": standard_rate, "price_list": price_list}


@frappe.whitelist()
def get_item_variants(item_code):
    """
    Get all variants of a template item.
    
    Args:
        item_code: The template item code
        
    Returns:
        dict: List of variants with their details
    """
    try:
        if not frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item not found")}
        
        item = frappe.get_doc("Item", item_code)
        
        if not item.has_variants:
            return {"success": True, "variants": [], "has_variants": False}
        
        # Get all variants of this template
        variants = frappe.get_all(
            "Item",
            filters={"variant_of": item_code, "disabled": 0},
            fields=["item_code", "item_name", "standard_rate", "image", "disabled"]
        )
        
        # Get variant attributes for each variant
        for variant in variants:
            attributes = frappe.get_all(
                "Item Variant Attribute",
                filters={"parent": variant.item_code},
                fields=["attribute", "attribute_value"]
            )
            variant["attributes"] = attributes
            
            # Get product bundle if exists
            variant["has_recipe"] = frappe.db.exists("Product Bundle", {"new_item_code": variant.item_code})
        
        return {
            "success": True,
            "has_variants": True,
            "variants": variants
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Item Variants Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def create_item_variant(template_item_code, variant_name, attributes, standard_rate=0):
    """
    Create a new variant for a template item.
    
    Args:
        template_item_code: The template item code
        variant_name: Name for the variant (e.g., "Small", "Large")
        attributes: List of attribute dicts [{"attribute": "Size", "attribute_value": "Small"}]
        standard_rate: Price for this variant
        
    Returns:
        dict: Created variant data or error message
    """
    try:
        if not frappe.db.exists("Item", template_item_code):
            return {"success": False, "message": _("Template item not found")}
        
        template = frappe.get_doc("Item", template_item_code)
        
        # Ensure template has variants enabled
        if not template.has_variants:
            template.has_variants = 1
            template.save(ignore_permissions=True)
        
        if isinstance(attributes, str):
            import json
            attributes = json.loads(attributes)
        
        # Generate variant item code
        variant_item_code = f"{template_item_code}-{variant_name.upper().replace(' ', '-')}"
        
        if frappe.db.exists("Item", variant_item_code):
            return {"success": False, "message": _("Variant {0} already exists").format(variant_item_code)}
        
        # Create variant item
        variant = frappe.new_doc("Item")
        variant.item_code = variant_item_code
        variant.item_name = f"{template.item_name} - {variant_name}"
        variant.item_group = template.item_group
        variant.stock_uom = template.stock_uom
        variant.is_stock_item = template.is_stock_item
        variant.standard_rate = standard_rate or template.standard_rate
        variant.variant_of = template_item_code
        variant.description = f"{template.description or template.item_name} - {variant_name}"
        
        if template.image:
            variant.image = template.image
        
        # Add variant attributes
        for attr in attributes:
            # Ensure attribute exists
            if not frappe.db.exists("Item Attribute", attr.get("attribute")):
                # Create the attribute
                new_attr = frappe.new_doc("Item Attribute")
                new_attr.attribute_name = attr.get("attribute")
                new_attr.append("item_attribute_values", {
                    "attribute_value": attr.get("attribute_value"),
                    "abbr": attr.get("attribute_value")[:3].upper()
                })
                new_attr.insert(ignore_permissions=True)
            
            variant.append("attributes", {
                "attribute": attr.get("attribute"),
                "attribute_value": attr.get("attribute_value")
            })
        
        variant.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Variant {0} created successfully").format(variant_item_code),
            "variant": variant.as_dict()
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Item Variant Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def update_item_variant(variant_item_code, updates):
    """
    Update an existing variant.
    
    Args:
        variant_item_code: The variant item code
        updates: Dict of fields to update
        
    Returns:
        dict: Success status
    """
    try:
        if not frappe.db.exists("Item", variant_item_code):
            return {"success": False, "message": _("Variant not found")}
        
        if isinstance(updates, str):
            import json
            updates = json.loads(updates)
        
        variant = frappe.get_doc("Item", variant_item_code)
        
        allowed_fields = ["item_name", "standard_rate", "description", "image", "disabled"]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(variant, field, value)
        
        variant.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {"success": True, "message": _("Variant updated successfully")}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Item Variant Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def delete_item_variant(variant_item_code):
    """
    Delete a variant item.
    
    Args:
        variant_item_code: The variant item code to delete
        
    Returns:
        dict: Success status
    """
    try:
        if not frappe.db.exists("Item", variant_item_code):
            return {"success": False, "message": _("Variant not found")}
        
        # Check if variant has transactions
        has_transactions = frappe.db.exists("Sales Invoice Item", {"item_code": variant_item_code})
        if has_transactions:
            # Just disable instead of delete
            frappe.db.set_value("Item", variant_item_code, "disabled", 1)
            frappe.db.commit()
            return {"success": True, "message": _("Variant disabled (has transactions)")}
        
        # Delete product bundle if exists
        if frappe.db.exists("Product Bundle", {"new_item_code": variant_item_code}):
            frappe.delete_doc("Product Bundle", variant_item_code, ignore_permissions=True)
        
        # Delete the variant
        frappe.delete_doc("Item", variant_item_code, ignore_permissions=True)
        frappe.db.commit()
        
        return {"success": True, "message": _("Variant deleted successfully")}
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Delete Item Variant Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_item_attributes():
    """
    Get all available item attributes for variants with their values.
    
    Returns:
        list: List of item attributes with values
    """
    attributes = frappe.get_all(
        "Item Attribute",
        fields=["name", "attribute_name"],
        order_by="attribute_name"
    )
    
    # Get values for each attribute
    for attr in attributes:
        attr_doc = frappe.get_doc("Item Attribute", attr.name)
        attr["values"] = [
            {
                "value": v.attribute_value,
                "abbr": v.abbr
            }
            for v in attr_doc.item_attribute_values
        ]
    
    return attributes


@frappe.whitelist()
def get_template_attributes(item_code):
    """
    Get attributes assigned to a template item.
    
    Args:
        item_code: The template item code
        
    Returns:
        dict: Template attributes with their values
    """
    try:
        if not frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item not found")}
        
        item = frappe.get_doc("Item", item_code)
        
        if not item.has_variants:
            return {"success": True, "has_variants": False, "attributes": []}
        
        # Get attributes assigned to this template
        template_attributes = []
        for attr in item.attributes:
            attr_doc = frappe.get_doc("Item Attribute", attr.attribute)
            template_attributes.append({
                "attribute": attr.attribute,
                "values": [
                    {
                        "value": v.attribute_value,
                        "abbr": v.abbr
                    }
                    for v in attr_doc.item_attribute_values
                ]
            })
        
        return {
            "success": True,
            "has_variants": True,
            "attributes": template_attributes
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Template Attributes Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def add_attribute_to_template(item_code, attribute_name, values=None):
    """
    Add an attribute to a template item and optionally create attribute values.
    
    Args:
        item_code: The template item code
        attribute_name: Name of the attribute (e.g., "Size", "Type")
        values: List of values for this attribute (e.g., ["Medium", "Large"])
        
    Returns:
        dict: Success or error message
    """
    try:
        if not frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item not found")}
        
        if isinstance(values, str):
            import json
            values = json.loads(values)
        
        # Create or get the attribute
        if not frappe.db.exists("Item Attribute", attribute_name):
            attr_doc = frappe.new_doc("Item Attribute")
            attr_doc.attribute_name = attribute_name
            attr_doc.insert(ignore_permissions=True)
        else:
            attr_doc = frappe.get_doc("Item Attribute", attribute_name)
        
        # Add values to attribute if provided
        if values:
            existing_values = [v.attribute_value for v in attr_doc.item_attribute_values]
            for val in values:
                if val not in existing_values:
                    attr_doc.append("item_attribute_values", {
                        "attribute_value": val,
                        "abbr": val[:3].upper()
                    })
            attr_doc.save(ignore_permissions=True)
        
        # Add attribute to template item
        item = frappe.get_doc("Item", item_code)
        
        # Enable variants if not already
        if not item.has_variants:
            item.has_variants = 1
        
        # Check if attribute already added
        existing_attrs = [a.attribute for a in item.attributes]
        if attribute_name not in existing_attrs:
            item.append("attributes", {"attribute": attribute_name})
            item.save(ignore_permissions=True)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Attribute {0} added to {1}").format(attribute_name, item_code)
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Add Attribute to Template Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def create_variant_combination(template_item_code, attributes, price=0):
    """
    Create a variant with multiple attribute values (e.g., Size=Large, Type=Spicy).
    
    Args:
        template_item_code: The template item code
        attributes: List of {attribute, value} pairs
        price: Price for this variant
        
    Returns:
        dict: Created variant data or error message
    """
    try:
        if not frappe.db.exists("Item", template_item_code):
            return {"success": False, "message": _("Template item not found")}
        
        if isinstance(attributes, str):
            import json
            attributes = json.loads(attributes)
        
        template = frappe.get_doc("Item", template_item_code)
        
        # Build variant code and name from attributes
        attr_parts = []
        attr_name_parts = []
        for attr in attributes:
            attr_parts.append(attr.get("value", "").upper().replace(" ", "-"))
            attr_name_parts.append(attr.get("value", ""))
        
        variant_suffix = "-".join(attr_parts)
        variant_name_suffix = " - ".join(attr_name_parts)
        
        variant_item_code = f"{template_item_code}-{variant_suffix}"
        
        if frappe.db.exists("Item", variant_item_code):
            return {"success": False, "message": _("Variant {0} already exists").format(variant_item_code)}
        
        # Ensure all attributes are on template
        for attr in attributes:
            attr_name = attr.get("attribute")
            attr_value = attr.get("value")
            
            # Ensure attribute exists
            if not frappe.db.exists("Item Attribute", attr_name):
                new_attr = frappe.new_doc("Item Attribute")
                new_attr.attribute_name = attr_name
                new_attr.insert(ignore_permissions=True)
            
            # Ensure value exists in attribute
            attr_doc = frappe.get_doc("Item Attribute", attr_name)
            value_exists = any(v.attribute_value == attr_value for v in attr_doc.item_attribute_values)
            if not value_exists:
                attr_doc.append("item_attribute_values", {
                    "attribute_value": attr_value,
                    "abbr": attr_value[:3].upper()
                })
                attr_doc.save(ignore_permissions=True)
            
            # Ensure attribute is on template
            if not template.has_variants:
                template.has_variants = 1
            
            existing_attrs = [a.attribute for a in template.attributes]
            if attr_name not in existing_attrs:
                template.append("attributes", {"attribute": attr_name})
        
        template.save(ignore_permissions=True)
        
        # Create variant item
        variant = frappe.new_doc("Item")
        variant.item_code = variant_item_code
        variant.item_name = f"{template.item_name} - {variant_name_suffix}"
        variant.item_group = template.item_group
        variant.stock_uom = template.stock_uom or "Unit"
        variant.is_stock_item = template.is_stock_item
        variant.standard_rate = float(price) if price else template.standard_rate
        variant.variant_of = template_item_code
        variant.description = f"{template.description or template.item_name} - {variant_name_suffix}"
        
        # Add variant attributes
        for attr in attributes:
            variant.append("attributes", {
                "attribute": attr.get("attribute"),
                "attribute_value": attr.get("value")
            })
        
        variant.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Variant {0} created successfully").format(variant_item_code),
            "variant": {
                "item_code": variant.item_code,
                "item_name": variant.item_name,
                "standard_rate": variant.standard_rate,
                "attributes": attributes
            }
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Variant Combination Error")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def create_simple_variant(template_item_code, variant_name, price=0):
    """
    Create a simple variant without complex attributes.
    Just creates a variant with name and price.
    
    Args:
        template_item_code: The template item code
        variant_name: Name for the variant (e.g., "Small", "Medium", "Large")
        price: Price for this variant
        
    Returns:
        dict: Created variant data or error message
    """
    try:
        if not frappe.db.exists("Item", template_item_code):
            return {"success": False, "message": _("Template item not found")}
        
        template = frappe.get_doc("Item", template_item_code)
        
        # Generate variant item code
        variant_item_code = f"{template_item_code}-{variant_name.upper().replace(' ', '-')}"
        
        if frappe.db.exists("Item", variant_item_code):
            return {"success": False, "message": _("Variant {0} already exists").format(variant_item_code)}
        
        # Ensure "Size" attribute exists
        size_attr = "Size"
        if not frappe.db.exists("Item Attribute", size_attr):
            new_attr = frappe.new_doc("Item Attribute")
            new_attr.attribute_name = size_attr
            new_attr.insert(ignore_permissions=True)
        
        # Ensure attribute value exists
        attr_doc = frappe.get_doc("Item Attribute", size_attr)
        value_exists = any(v.attribute_value == variant_name for v in attr_doc.item_attribute_values)
        if not value_exists:
            attr_doc.append("item_attribute_values", {
                "attribute_value": variant_name,
                "abbr": variant_name[:3].upper()
            })
            attr_doc.save(ignore_permissions=True)
        
        # Enable variants on template if not already
        if not template.has_variants:
            template.has_variants = 1
            # Add Size attribute to template
            template.append("attributes", {"attribute": size_attr})
            template.save(ignore_permissions=True)
        
        # Create variant item
        variant = frappe.new_doc("Item")
        variant.item_code = variant_item_code
        variant.item_name = f"{template.item_name} - {variant_name}"
        variant.item_group = template.item_group
        variant.stock_uom = template.stock_uom or "Unit"
        variant.is_stock_item = template.is_stock_item
        variant.standard_rate = float(price) if price else template.standard_rate
        variant.variant_of = template_item_code
        variant.description = f"{template.description or template.item_name} - {variant_name}"
        
        if template.image:
            variant.image = template.image
        
        # Add variant attribute
        variant.append("attributes", {
            "attribute": size_attr,
            "attribute_value": variant_name
        })
        
        variant.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Variant {0} created successfully").format(variant_name),
            "variant": {
                "item_code": variant.item_code,
                "item_name": variant.item_name,
                "name": variant_name,
                "price": variant.standard_rate,
                "has_recipe": False
            }
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Simple Variant Error")
        return {"success": False, "message": str(e)}
