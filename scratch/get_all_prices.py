import frappe
import json

prices = frappe.get_all('Item Price', 
    filters={'item_code': 'Sandwiches Round-LAR-DOU-FRA'}, 
    fields=['*']
)
print(json.dumps(prices, indent=2, default=str))
