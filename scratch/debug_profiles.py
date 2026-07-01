import frappe
frappe.connect()
profiles = frappe.get_all('POS Profile', fields=['name', 'branch'])
for p in profiles:
    print(f"{p.name} -> {p.branch}")
