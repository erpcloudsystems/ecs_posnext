import frappe
import json

def list_info():
    data = {
        "customer_groups": frappe.get_all("Customer Group", filters={"is_group": 0}, pluck="name"),
        "territories": frappe.get_all("Territory", filters={"is_group": 0}, pluck="name"),
        "default_customer_group": frappe.db.get_default("customer_group"),
        "default_territory": frappe.db.get_default("territory")
    }
    print(json.dumps(data, indent=4))

if __name__ == "__main__":
    list_info()
