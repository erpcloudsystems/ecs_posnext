import frappe

def run():
    print("TERRITORY FIELDS:")
    print([f.fieldname for f in frappe.get_meta('Territory').fields])
    print("\nPOS PROFILE FIELDS:")
    print([f.fieldname for f in frappe.get_meta('POS Profile').fields])
    print("\nCUSTOM FIELDS FOR TERRITORY:")
    print(frappe.get_all('Custom Field', filters={'dt': 'Territory'}, fields=['fieldname']))

if __name__ == "__main__":
    run()
