
import frappe

def final_check():
    item_code = 'SAND-RO-LAR-DOU-FRA'
    
    # Check all Item Prices for this item
    prices = frappe.get_all('Item Price', 
                           filters={'item_code': item_code},
                           fields=['name', 'price_list', 'price_list_rate', 'currency', 'uom', 'modified'])
    
    print(f"DEBUG: All prices for {item_code}:")
    for p in prices:
        print(p)

    # Check Mumo price list specifically
    mumo_prices = [p for p in prices if p.price_list.lower() == 'mumo']
    print(f"\nDEBUG: Mumo prices:")
    for p in mumo_prices:
        print(p)

if __name__ == "__main__":
    frappe.init(site="mumo15.erpnext.cloud")
    frappe.connect()
    try:
        final_check()
    finally:
        frappe.destroy()
