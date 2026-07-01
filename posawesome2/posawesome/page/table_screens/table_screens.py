import frappe

def get_context(context):
    pass
@frappe.whitelist()
def get_sales_order_details_for_table(table_name, branch):
    """Return latest open Sales Order linked to this table."""
    
    # Adjust filters as your workflow requires
    so = frappe.db.get_list(
        "Sales Order",
        filters={
            "custom_table_number": table_name,
            # "docstatus": 1   # submitted sales order or change as needed
            "custom_so_type":"Dinin",
            "branch": branch,      
            "custom_order_in_kitchen_":["!=","Completed"]
        },
        fields=["name"],
        limit_page_length=1,
        order_by="modified desc"
    )

    if so:
        so_name = so[0].name
        sales_order = frappe.get_doc("Sales Order", so_name)
        items = [
        {
                "item_code": d.item_code,
                "item_name": d.item_name,
                "qty": d.qty,
                "rate": d.rate,
                "amount": d.amount
            }
            for d in sales_order.items
        ]

        return {
            "name": sales_order.name,
            "customer": sales_order.customer,
            "grand_total": sales_order.grand_total,
            "items": items
        }
    return None
@frappe.whitelist()
def get_table_number_data(branch=None, page_no=1, page_length=20):
    page_no = int(page_no)
    page_length = int(page_length)
    start = (page_no - 1) * page_length

    filters = {}
    if branch:
        filters["branch"] = branch

    data = frappe.db.get_list(
        "Table Number",
        fields=["name", "no", "branch", "disabled"],
        filters=filters,
        limit_start=start,
        limit_page_length=page_length,
        order_by="no asc"
    )

    total = frappe.db.count("Table Number", filters=filters)

    return {
        "data": data,
        "total_count": total,
        "page_no": page_no,
        "page_length": page_length,
    }

@frappe.whitelist()
def reopen_table(table_name, branch, sales_order=None):
    # your logic here:
    # - mark the Table Number doc disabled=0
    # - optionally unlink/close/cancel the SO, or whatever your workflow requires
    # - frappe.publish_realtime("table_number_updated")
    frappe.db.set_value('Table Number', table_name,"disabled", 0)
    return {"ok": True}