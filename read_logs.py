import frappe
frappe.init(site="mumo15.erpnext.cloud", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
logs = frappe.get_all("Error Log", filters={"title": ["like", "%POS Submit Invoice%"]}, fields=["*"], limit=5, order_by="creation desc")
for log in logs:
    print(f"--- {log.creation} - {log.title} ---")
    print(log.error)
    print("\n")
