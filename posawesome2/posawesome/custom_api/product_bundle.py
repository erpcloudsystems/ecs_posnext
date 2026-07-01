import frappe

@frappe.whitelist()
def checkIsProdBundle(item_code):
    item = frappe.get_cached_doc('Item', item_code)
    response = []
    processed_templates = {}  # Track processed template items by classification
    variant_items_by_template = {}  # Collect variant item codes by template
    
    # Check for new combo_components first
    if item.enabled_item_bundle and hasattr(item, 'combo_components') and item.combo_components:
        return get_combo_components_for_pos(item)
    
    if item.enabled_item_bundle:
        # First pass: collect all items that are templates with custom_variant OR variants of a template
        for row in item.custom_item_options:
            if row.custom_hide_from_pos:
                continue
            
            option_item = frappe.get_cached_doc('Item', row.item_code)
            
            # Case 1: Item is a template with has_variants=True and has custom_variant set
            if option_item.has_variants and row.custom_variant:
                template_code = row.item_code
                classification = row.item_classification
                template_key = f"{classification}_{template_code}"
                
                if template_key not in variant_items_by_template:
                    variant_items_by_template[template_key] = {
                        'template_code': template_code,
                        'classification': classification,
                        'variants': [],
                        'first_row': row
                    }
                # Add the custom_variant to the list
                if row.custom_variant not in variant_items_by_template[template_key]['variants']:
                    variant_items_by_template[template_key]['variants'].append(row.custom_variant)
            
            # Case 2: Item is a variant of a template
            elif option_item.variant_of:
                template_code = option_item.variant_of
                classification = row.item_classification
                template_key = f"{classification}_{template_code}"
                
                if template_key not in variant_items_by_template:
                    variant_items_by_template[template_key] = {
                        'template_code': template_code,
                        'classification': classification,
                        'variants': [],
                        'first_row': row
                    }
                variant_items_by_template[template_key]['variants'].append(row.item_code)
        
        # Second pass: process items
        for row in item.custom_item_options:
            if row.custom_hide_from_pos:
                continue
            
            option_item = frappe.get_cached_doc('Item', row.item_code)
            option_data = row.as_dict()
            
            # Case 1: Template item with custom_variant - group them
            if option_item.has_variants and row.custom_variant:
                template_code = row.item_code
                classification = row.item_classification
                template_key = f"{classification}_{template_code}"
                
                # If we haven't processed this template for this classification yet
                if template_key not in processed_templates:
                    variant_codes = variant_items_by_template[template_key]['variants']
                    
                    # Get only the variants that are in the combo
                    added_variants = get_specific_variants(variant_codes)
                    # Extract attributes from added variants only
                    added_attributes = extract_attributes_from_variants(added_variants)
                    
                    # Create a single entry for the template with nested selection
                    template_data = {
                        'item_code': template_code,
                        'item_name': option_item.item_name,
                        'item_classification': classification,
                        'rate': 0,
                        'qty': row.qty,
                        'max_required': row.max_required,
                        'state': row.state,
                        'is_template': True,
                        'let_customer_choose': True,
                        'template_attributes': added_attributes,
                        'template_variants': added_variants
                    }
                    response.append(template_data)
                    processed_templates[template_key] = True
                # Skip individual entries since we're using nested selection
                continue
            
            # Case 2: Item is a variant of a template
            if option_item.variant_of:
                template_code = option_item.variant_of
                classification = row.item_classification
                template_key = f"{classification}_{template_code}"
                
                # If we haven't processed this template for this classification yet
                if template_key not in processed_templates:
                    template_item = frappe.get_cached_doc('Item', template_code)
                    variant_codes = variant_items_by_template[template_key]['variants']
                    
                    # Get only the variants that are in the combo
                    added_variants = get_specific_variants(variant_codes)
                    # Extract attributes from added variants only
                    added_attributes = extract_attributes_from_variants(added_variants)
                    
                    # Create a single entry for the template with nested selection
                    template_data = {
                        'item_code': template_code,
                        'item_name': template_item.item_name,
                        'item_classification': classification,
                        'rate': 0,
                        'qty': row.qty,
                        'max_required': row.max_required,
                        'state': row.state,
                        'is_template': True,
                        'let_customer_choose': True,
                        'template_attributes': added_attributes,
                        'template_variants': added_variants
                    }
                    response.append(template_data)
                    processed_templates[template_key] = True
                # Skip individual variants since we're using nested selection
                continue
            
            # Case 3: Template item without custom_variant (let customer choose any variant)
            if option_item.has_variants and not row.custom_variant:
                option_data['is_template'] = True
                option_data['let_customer_choose'] = True
                option_data['template_attributes'] = get_option_item_attributes(row.item_code)
                option_data['template_variants'] = get_option_item_variants(row.item_code)
                response.append(option_data)
                continue
            
            # Case 4: Regular item (not a template, not a variant)
            option_data['is_template'] = False
            option_data['let_customer_choose'] = False
            option_data['has_variant_selection'] = False
            response.append(option_data)
            
        return response
    return False


def get_combo_components_for_pos(item):
    """Get combo components in nested structure for POS display."""
    response = []
    template_groups = {}  # Group variants by their template
    processed_templates = set()
    
    # First pass: collect all variants grouped by template (only non-standalone)
    for idx, comp in enumerate(item.combo_components):
        comp_item = frappe.get_cached_doc('Item', comp.item_code)
        section_name = comp.section_name or 'Default'
        is_standalone = getattr(comp, 'is_standalone', 1)  # Default to standalone
        
        # Only group variants that are NOT standalone
        if comp_item.variant_of and not is_standalone:
            template_code = comp_item.variant_of
            key = f"{section_name}__{template_code}"
            
            if key not in template_groups:
                template_groups[key] = {
                    'section_name': section_name,
                    'section_type': comp.section_type if hasattr(comp, 'section_type') else 'Component',
                    'is_required': comp.is_required if hasattr(comp, 'is_required') else 0,
                    'template_code': template_code,
                    'variants': [],
                    'min_qty': comp.min_qty or 0,
                    'max_qty': comp.max_qty or 1,
                    'first_idx': idx  # Track first occurrence for ordering
                }
            
            template_groups[key]['variants'].append({
                'item_code': comp.item_code,
                'item_name': comp_item.item_name,
                'rate': comp.extra_price or 0,
                'default_selected': comp.default_selected,
                'qty': comp.qty or 1,
                'show_bundle_in_pos': comp.show_bundle_in_pos if hasattr(comp, 'show_bundle_in_pos') else 0
            })
    
    # Second pass: build response in original order
    for idx, comp in enumerate(item.combo_components):
        comp_item = frappe.get_cached_doc('Item', comp.item_code)
        section_name = comp.section_name or 'Default'
        is_standalone = getattr(comp, 'is_standalone', 1)  # Default to standalone
        
        if comp_item.variant_of and not is_standalone:
            # This is a variant from template - add template entry on first occurrence
            template_code = comp_item.variant_of
            key = f"{section_name}__{template_code}"
            
            if key not in processed_templates:
                processed_templates.add(key)
                group = template_groups[key]
                template_item = frappe.get_cached_doc('Item', template_code)
                
                # Get variant details with attributes
                variant_codes = [v['item_code'] for v in group['variants']]
                variants_with_attrs = get_specific_variants(variant_codes)
                
                # Add extra_price from combo to variants
                for v in variants_with_attrs:
                    combo_variant = next((cv for cv in group['variants'] if cv['item_code'] == v['item_code']), None)
                    if combo_variant:
                        v['rate'] = combo_variant['rate']
                        v['default_selected'] = combo_variant['default_selected']
                        v['show_bundle_in_pos'] = combo_variant.get('show_bundle_in_pos', 0)
                
                # Extract attributes from variants
                attributes = extract_attributes_from_variants(variants_with_attrs)
                
                response.append({
                    'item_code': template_code,
                    'item_name': template_item.item_name,
                    'item_classification': section_name,
                    'section_type': group.get('section_type', 'Component'),
                    'is_required': group.get('is_required', 0),
                    'rate': 0,
                    'is_template': True,
                    'let_customer_choose': True,
                    'template_attributes': attributes,
                    'template_variants': variants_with_attrs,
                    'min_required': group['min_qty'],
                    'max_required': group['max_qty']
                })
        else:
            # Regular item OR standalone variant - add directly
            response.append({
                'item_code': comp.item_code,
                'item_name': comp_item.item_name,
                'item_classification': section_name,
                'section_type': comp.section_type if hasattr(comp, 'section_type') else 'Component',
                'is_required': comp.is_required if hasattr(comp, 'is_required') else 0,
                'rate': comp.extra_price or 0,
                'qty': comp.qty or 1,
                'default_selected': comp.default_selected,
                'is_template': False,
                'min_required': comp.min_qty or 0,
                'max_required': comp.max_qty or 1,
                'show_bundle_in_pos': comp.show_bundle_in_pos if hasattr(comp, 'show_bundle_in_pos') else 0
            })
    
    return response


def get_specific_variants(variant_codes):
    """Get specific variants by their item codes."""
    variants = []
    for code in variant_codes:
        variant = frappe.get_all(
            "Item",
            filters={"item_code": code, "disabled": 0},
            fields=["item_code", "item_name", "standard_rate", "custom_show_bundle_in_pos"]
        )
        if variant:
            v = variant[0]
            v['show_bundle_in_pos'] = v.get('custom_show_bundle_in_pos', 0)
            v['attributes'] = frappe.get_all(
                "Item Variant Attribute",
                filters={"parent": v['item_code']},
                fields=["attribute", "attribute_value"]
            )
            variants.append(v)
    return variants


def extract_attributes_from_variants(variants):
    """Extract unique attributes and their values from a list of variants."""
    attributes_map = {}
    
    for v in variants:
        for attr in v.get('attributes', []):
            attr_name = attr['attribute']
            attr_value = attr['attribute_value']
            
            if attr_name not in attributes_map:
                attributes_map[attr_name] = set()
            attributes_map[attr_name].add(attr_value)
    
    # Convert to list format
    attributes = []
    for attr_name, values in attributes_map.items():
        attributes.append({
            'attribute': attr_name,
            'values': [{'attribute_value': v} for v in sorted(values)]
        })
    
    return attributes


def get_option_item_attributes(item_code):
    """Get attributes for a template item."""
    attributes = frappe.db.get_all(
        "Item Variant Attribute",
        fields=["attribute"],
        filters={"parenttype": "Item", "parent": item_code},
        order_by="idx asc",
    )
    
    for a in attributes:
        values = frappe.db.get_all(
            "Item Attribute Value",
            fields=["attribute_value", "abbr"],
            filters={"parenttype": "Item Attribute", "parent": a.attribute},
            order_by="idx asc",
        )
        a['values'] = values
    
    return attributes


def get_option_item_variants(item_code):
    """Get all variants for a template item."""
    variants = frappe.get_all(
        "Item",
        filters={"variant_of": item_code, "disabled": 0},
        fields=["item_code", "item_name", "standard_rate"]
    )
    
    # Get attributes for each variant
    for v in variants:
        v['attributes'] = frappe.get_all(
            "Item Variant Attribute",
            filters={"parent": v['item_code']},
            fields=["attribute", "attribute_value"]
        )
    
    return variants

@frappe.whitelist()
def get_items(item_code):
    if not frappe.db.exists('Product Bundle', {"new_item_code": item_code}):
        return False
    item = frappe.get_cached_doc('Product Bundle', {"new_item_code":item_code})
    response = []
    # if item.enabled_item_bundle:
    for row in item.items:
        response.append(
            {
                **row.as_dict()
            }
        )
    return response

@frappe.whitelist()
def get_items_2(item_code):
    if not frappe.db.exists('Product Bundle', {"new_item_code": item_code}):
        return False
    item = frappe.get_cached_doc('Item', item_code)
    if not item.custom_fast_sell:
        return False
    item = frappe.get_cached_doc('Product Bundle', {"new_item_code":item_code})
    response = []
    # if item.enabled_item_bundle:
    for row in item.items:
        response.append(
            {
                **row.as_dict()
            }
        )
    return response
    return False