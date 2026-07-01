
import frappe
import json

def test_get_item_variants():
    frappe.init(site="mumo15.erpnext.cloud", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    try:
        from ecs_posnext.api.items import get_item_variants
        res = get_item_variants(template_item='SAND-RO', pos_profile='Sidi Beshr')
        print(f"DEBUG: Found {len(res)} variants")
        for v in res:
            if v['item_code'] == 'SAND-RO-LAR-DOU-FRA':
                print(f"DEBUG: Found SAND-RO-LAR-DOU-FRA: {v['price_list_rate']}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    test_get_item_variants()
