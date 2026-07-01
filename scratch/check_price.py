
import frappe

def check_item_price():
    item_code = 'SAND-RO-LAR-DOU-FRA'
    price_list = 'mumo'
    
    prices = frappe.get_all('Item Price', 
                           filters={'item_code': item_code, 'price_list': price_list},
                           fields=['name', 'item_code', 'price_list', 'price_list_rate', 'currency', 'uom'])
    
    print(f"Prices for {item_code} in {price_list}:")
    for p in prices:
        print(p)

    # Also check if it has variants or is a variant
    item = frappe.get_doc('Item', item_code)
    print(f"\nItem Details for {item_code}:")
    print(f"Is Variant: {item.variant_of}")
    print(f"UOM: {item.stock_uom}")
    
    if item.variant_of:
        parent_item = frappe.get_doc('Item', item.variant_of)
        print(f"Parent Item: {parent_item.name}")
        parent_prices = frappe.get_all('Item Price', 
                               filters={'item_code': item.variant_of, 'price_list': price_list},
                               fields=['name', 'item_code', 'price_list', 'price_list_rate', 'currency', 'uom'])
        print(f"Parent Prices:")
        for p in parent_prices:
            print(p)

if __name__ == "__main__":
    frappe.init(site="mumo15.erpnext.cloud")
    frappe.connect()
    try:
        check_item_price()
    finally:
        frappe.destroy()
