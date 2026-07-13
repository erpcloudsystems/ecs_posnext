import frappe

OLD = (
    '<div class="col-8">{{ doc.custom_table_number or "" }}</div>\n'
    '      {% endif %}'
)
NEW = (
    '<div class="col-8">{{ doc.custom_table_no or doc.custom_table_number or "" }}</div>\n'
    '      {% endif %}\n\n'
    '      {% if doc.custom_order_type == "Talabat" %}\n'
    '        <div class="col-4">شباك:</div>\n'
    '        <div class="col-8">{{ doc.custom_third_party_referance_number or "" }}</div>\n'
    '      {% endif %}'
)


def execute():
    """Kitchen Receipt: show the Talabat counter/window number and use the human
    table number. Idempotent — only rewrites when the Talabat block is missing.
    """
    name = "Kitchen Receipt"
    if not frappe.db.exists("Print Format", name):
        return

    html = frappe.db.get_value("Print Format", name, "html") or ""
    if "custom_third_party_referance_number" in html:
        return  # already patched
    if OLD in html:
        frappe.db.set_value("Print Format", name, "html", html.replace(OLD, NEW, 1))
