import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

ANCHOR = '{%- if is_delivery and doc.address_display -%}'
BLOCK = (
    '{%- if is_delivery and doc.custom_delivery_note -%}\n'
    '<!-- ===== Delivery note (for the driver) ===== -->\n'
    '<div style="border:1px dashed #000; border-radius:6px; padding:6px 8px; '
    'margin:6px 0; font-size:13px; font-weight:bold;">'
    '📝 {{ _("Delivery Note") }}: {{ doc.custom_delivery_note }}</div>\n'
    '{%- endif -%}\n'
)


def execute():
    """Add a driver-facing delivery note field and show it on the dispatch print."""
    create_custom_fields(
        {
            "Sales Invoice": [
                {
                    "fieldname": "custom_delivery_note",
                    "label": "Delivery Note",
                    "fieldtype": "Small Text",
                    "insert_after": "custom_order_type",
                    "translatable": 0,
                }
            ]
        },
        ignore_validate=True,
    )

    name = "print format sales"
    if not frappe.db.exists("Print Format", name):
        return
    html = frappe.db.get_value("Print Format", name, "html") or ""
    if "custom_delivery_note" in html:
        return  # already patched
    if ANCHOR in html:
        frappe.db.set_value("Print Format", name, "html", html.replace(ANCHOR, BLOCK + ANCHOR, 1))
