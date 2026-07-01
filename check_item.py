import frappe
import json

def check_item():
    template = "SAND-RO"
    item_info = frappe.db.get_value("Item", template, ["name", "item_name", "enabled_item_bundle"], as_dict=1)
    print(f"Template: {item_info}")
    
    variants = frappe.get_all("Item", filters={"variant_of": template}, fields=["name", "enabled_item_bundle"])
    print(f"Variants: {variants}")
    
    # Check for Product Bundle
    bundle = frappe.db.get_value("Product Bundle", {"new_item_code": template}, "name")
    print(f"Template Bundle: {bundle}")
    
    if bundle:
        items = frappe.get_all("Product Bundle Item", filters={"parent": bundle}, fields=["item_code", "show_in_pos"])
        print(f"Template Ingredients: {items}")

if __name__ == "__main__":
    frappe.init(site="mumo15.erpnext.cloud")
    frappe.connect()
    check_item()
    frappe.destroy()
