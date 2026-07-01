import frappe
print(f"Product Bundle for SING-H-X: {frappe.db.get_value('Product Bundle', {'new_item_code': 'SING-H-X'}, 'name')}")
bundle_items = frappe.get_all('Product Bundle Item', filters={'parent': 'SING-H-X'}, fields=['item_code', 'qty'])
print(f"Items: {bundle_items}")
