import frappe

def run():
    meta = frappe.get_meta("Sales Invoice")
    print("SALES INVOICE FIELDS:")
    fields = [f.fieldname for f in meta.fields]
    print(fields)
    print("\nIS posa_is_call_center in fields?")
    print("posa_is_call_center" in fields)

if __name__ == "__main__":
    run()
