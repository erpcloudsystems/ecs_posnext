import frappe

def check_links():
    frappe.connect()
    try:
        customer_groups = frappe.get_all("Customer Group", pluck="name")
        territories = frappe.get_all("Territory", pluck="name")
        print(f"Customer Groups: {customer_groups}")
        print(f"Territories: {territories}")
    finally:
        frappe.destroy()

if __name__ == "__main__":
    check_links()
