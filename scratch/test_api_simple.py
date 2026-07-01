
import frappe

def test_api():
    frappe.init(site="mumo15.erpnext.cloud", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    try:
        from ecs_posnext.api.items import get_item_variants
        res = get_item_variants('SAND-RO', 'Call Center')
        for v in res:
            if v['item_code'] == 'SAND-RO-LAR-DOU-FRA':
                print(f"RESULT: {v['item_code']} -> Price List: {v.get('price_list_name')} -> Rate: {v.get('price_list_rate')}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    test_api()
