import frappe
import json

def get_last_error():
    logs = frappe.get_all("Error Log", 
        fields=["name", "method", "error", "creation"], 
        filters={"method": ["like", "%submit_invoice%"]},
        order_by="creation desc", 
        limit=1
    )
    if logs:
        print(json.dumps(logs[0], indent=4, default=str))
    else:
        print("No logs found for submit_invoice")

if __name__ == "__main__":
    frappe.connect(site="mumo15.erpnext.cloud")
    get_last_error()
