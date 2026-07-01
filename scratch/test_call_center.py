
import frappe
import json

def test_api_call():
    frappe.init(site="mumo15.erpnext.cloud", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    try:
        from ecs_posnext.api.items import get_item_variants
        
        # Parameters from user request
        template_item = "SAND-RO"
        pos_profile = "Call Center"
        warehouse = None
        price_list = None
        
        print(f"DEBUG: Calling get_item_variants with profile: {pos_profile}")
        res = get_item_variants(
            template_item=template_item, 
            pos_profile=pos_profile, 
            warehouse=warehouse, 
            price_list=price_list
        )
        
        print(f"DEBUG: Found {len(res)} variants")
        for v in res:
            if v['item_code'] == 'SAND-RO-LAR-DOU-FRA':
                print(f"DEBUG: SAND-RO-LAR-DOU-FRA details: {json.dumps(v, indent=2)}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    test_api_call()
