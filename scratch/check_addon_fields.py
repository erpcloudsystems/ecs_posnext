import frappe
import json

def check_item_addon():
    try:
        meta = frappe.get_meta('Item Addon')
        fields = [{
            'fieldname': f.fieldname,
            'label': f.label,
            'fieldtype': f.fieldtype,
            'options': f.options
        } for f in meta.fields]
        print(json.dumps(fields, indent=4))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    frappe.init(site="mumo15.erpnext.cloud")
    frappe.connect()
    check_item_addon()
