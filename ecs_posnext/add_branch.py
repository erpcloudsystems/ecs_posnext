import frappe

def add_custom_field():
    if not frappe.db.exists("Custom Field", "Table Number-branch"):
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Table Number",
            "fieldname": "branch",
            "label": "Branch",
            "fieldtype": "Link",
            "options": "Branch",
            "insert_after": "no"
        })
        custom_field.insert()
        frappe.db.commit()
        return "Created"
    return "Exists"
