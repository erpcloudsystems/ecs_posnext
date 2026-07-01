
import frappe
from erpnext.stock.get_item_details import get_item_details

def test_erpnext_api():
    frappe.init(site="mumo15.erpnext.cloud", sites_path="/home/frappe/frappe-bench/sites")
    frappe.connect()
    try:
        args = frappe._dict({
            'item_code': 'SAND-RO-LAR-DOU-FRA',
            'pos_profile': 'Call Center',
            'company': 'Mumo',
            'doctype': 'Sales Invoice'
        })
        res = get_item_details(args)
        print(f"RESULT: Price List used: {res.get('price_list')} -> Rate: {res.get('price_list_rate')}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    test_erpnext_api()
