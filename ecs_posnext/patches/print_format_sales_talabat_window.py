import frappe

SET_OLD = '{%- set is_dinein = (order_type|lower == "dine in") -%}'
SET_NEW = (
    '{%- set is_dinein = (order_type|lower == "dine in") -%}\n'
    '{%- set is_talabat = (order_type|lower == "talabat") -%}\n'
    '{%- set window_no = doc.custom_third_party_referance_number or "" -%}'
)

BANNER_OLD = '<div class="tablebanner">{{ _("TABLE") }} # {{ table_no }}</div>\n{%- endif -%}'
BANNER_NEW = (
    '<div class="tablebanner">{{ _("TABLE") }} # {{ table_no }}</div>\n{%- endif -%}\n'
    '{%- if is_talabat and window_no -%}\n'
    '<!-- ===== Talabat window number ===== -->\n'
    '<div class="tablebanner">شباك # {{ window_no }}</div>\n'
    '{%- endif -%}'
)


def execute():
    """print format sales: show the Talabat counter/window number as a banner,
    mirroring the Dine-In table banner. Idempotent."""
    name = "print format sales"
    if not frappe.db.exists("Print Format", name):
        return

    html = frappe.db.get_value("Print Format", name, "html") or ""
    if "custom_third_party_referance_number" in html:
        return  # already patched

    if SET_OLD in html and BANNER_OLD in html:
        html = html.replace(SET_OLD, SET_NEW, 1).replace(BANNER_OLD, BANNER_NEW, 1)
        frappe.db.set_value("Print Format", name, "html", html)
