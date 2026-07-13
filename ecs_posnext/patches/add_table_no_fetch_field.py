import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Add a display-only Table No field on Sales Invoice.

    custom_table_number is a Link to "Table Number" (now hash-named, branch-scoped),
    so it holds an opaque id. This companion field fetches the human table number
    (Table Number.no) for display on KDS / kitchen / reports, while the Link is kept
    intact for lookups and status updates.
    """
    create_custom_fields(
        {
            "Sales Invoice": [
                {
                    "fieldname": "custom_table_no",
                    "label": "Table No",
                    "fieldtype": "Data",
                    "fetch_from": "custom_table_number.no",
                    "read_only": 1,
                    "insert_after": "custom_table_number",
                    "translatable": 0,
                }
            ]
        },
        ignore_validate=True,
    )

    _fix_sales_print_format()


def _fix_sales_print_format():
    """Make the 'print format sales' receipt show the human table number.

    The template read the Link id (doc.custom_table_number); prefer the fetched
    number (doc.custom_table_no) and fall back to the link for older invoices.
    Idempotent: only rewrites when the old expression is still present.
    """
    name = "print format sales"
    if not frappe.db.exists("Print Format", name):
        return

    html = frappe.db.get_value("Print Format", name, "html") or ""
    old = 'doc.custom_table_number or ""'
    new = 'doc.custom_table_no or doc.custom_table_number or ""'
    if old in html and new not in html:
        frappe.db.set_value("Print Format", name, "html", html.replace(old, new))

