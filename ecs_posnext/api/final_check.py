import frappe

def check():
    template = "SAND-RO"
    # Check if template is bundle
    is_bundle = frappe.db.get_value("Item", template, "enabled_item_bundle")
    print(f"Template {template} enabled_item_bundle: {is_bundle}")
    
    # Check Product Bundle for template
    pb = frappe.db.get_value("Product Bundle", {"new_item_code": template}, "name")
    print(f"Template Product Bundle: {pb}")
    
    # Check variants
    variants = frappe.get_all("Item", filters={"variant_of": template}, fields=["name", "enabled_item_bundle"])
    bundle_variants = [v.name for v in variants if v.enabled_item_bundle]
    print(f"Number of variants: {len(variants)}")
    print(f"Variants with enabled_item_bundle=1: {len(bundle_variants)}")
    
    # Check if any variant has a Product Bundle
    all_variant_names = [v.name for v in variants]
    pbs = frappe.get_all("Product Bundle", filters={"new_item_code": ["in", all_variant_names]}, fields=["name", "new_item_code"])
    print(f"Variants with Product Bundle records: {len(pbs)}")
    for p in pbs:
        print(f"  Variant {p.new_item_code} has bundle {p.name}")

if __name__ == "__main__":
    frappe.init(site="mumo15.erpnext.cloud")
    frappe.connect()
    check()
    frappe.destroy()
