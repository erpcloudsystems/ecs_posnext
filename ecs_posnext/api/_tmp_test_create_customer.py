import frappe


def run():
    frappe.set_user("Administrator")
    from ecs_posnext.api.customers import create_customer
    try:
        doc = create_customer(customer_name="Test QA Customer", mobile_no="", customer_group="Individual")
        print("SUCCESS:", doc.get("name"), doc.get("customer_name"), doc.get("first_name"), doc.get("last_name"))
        frappe.delete_doc("Customer", doc.get("name"), force=True)
        frappe.db.commit()
        print("cleanup done")
    except Exception:
        frappe.db.rollback()
        print("FAILED:")
        print(frappe.get_traceback())
