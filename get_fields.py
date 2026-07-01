import frappe
import json

frappe.init(site="pos")
frappe.connect()

fields = [f.fieldname for f in frappe.get_meta("Sales Invoice").fields if "pay" in f.fieldname or "type" in f.fieldname or "mode" in f.fieldname]
print(json.dumps(fields, indent=2))
