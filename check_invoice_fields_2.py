import frappe

def run():
    meta = frappe.get_meta("Sales Invoice")
    print("HAS custom_order_type?")
    print(meta.has_field("custom_order_type"))
    print("\nHAS posa_is_call_center?")
    print(meta.has_field("posa_is_call_center"))
    print("\nALL CUSTOM FIELDS:")
    print(frappe.get_all("Custom Field", filters={"dt": "Sales Invoice"}, fields=["fieldname"]))

if __name__ == "__main__":
    run()
