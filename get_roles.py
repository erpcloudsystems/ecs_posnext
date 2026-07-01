import frappe
def get_roles():
    roles = frappe.get_all("Role", pluck="name")
    for r in roles:
        if "manager" in r.lower() or "supervisor" in r.lower() or "call center" in r.lower():
            print(r)
