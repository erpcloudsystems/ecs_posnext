import frappe
import json

def check_item_price(item_code, price_list="Standard Selling"):
    prices = frappe.get_all("Item Price", 
        filters={"item_code": item_code, "price_list": price_list},
        fields=["price_list_rate", "uom", "currency"]
    )
    return prices

item_code = "Sandwiches Round-LAR-DOU-FRA"
# Let's also check the template
template_code = "Sandwiches"

print(f"Prices for {item_code}:")
print(json.dumps(check_item_price(item_code), indent=2))

print(f"\nPrices for {template_code}:")
print(json.dumps(check_item_price(template_code), indent=2))

# Also check POS Profile to see which price list it uses
# Assuming there is at least one POS Profile
pos_profiles = frappe.get_all("POS Profile", fields=["name", "selling_price_list"])
print(f"\nPOS Profiles:")
print(json.dumps(pos_profiles, indent=2))
