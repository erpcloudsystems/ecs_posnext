import frappe
import json

def debug_pos_data():
    profiles = frappe.get_all("POS Profile", fields=["name", "company"])
    print(f"Total Profiles: {len(profiles)}")
    for p in profiles:
        payments = frappe.get_all("POS Payment Method", filters={"parent": p.name}, fields=["mode_of_payment"])
        users = frappe.get_all("POS Profile User", filters={"parent": p.name}, fields=["user"])
        print(f"Profile: {p.name}, Payments: {len(payments)}, Users: {[u.user for u in users]}")

if __name__ == "__main__":
    debug_pos_data()
