import frappe

# --- Kitchen Receipt: add a Talabat No row inside the existing Talabat block ---
KR_OLD = (
    '        <div class="col-8">{{ doc.custom_third_party_referance_number or "" }}</div>\n'
    '      {% endif %}'
)
KR_NEW = (
    '        <div class="col-8">{{ doc.custom_third_party_referance_number or "" }}</div>\n'
    '        <div class="col-4">Talabat No:</div>\n'
    '        <div class="col-8">{{ doc.custom_unique_talbat_number or "" }}</div>\n'
    '      {% endif %}'
)

# --- print format sales: add a Talabat number banner after the window banner ---
PS_OLD = (
    '<div class="tablebanner">شباك # {{ window_no }}</div>\n'
    '{%- endif -%}'
)
PS_NEW = (
    '<div class="tablebanner">شباك # {{ window_no }}</div>\n'
    '{%- endif -%}\n'
    '{%- if is_talabat and doc.custom_unique_talbat_number -%}\n'
    '<!-- ===== Talabat unique number ===== -->\n'
    '<div class="tablebanner">طلبات # {{ doc.custom_unique_talbat_number }}</div>\n'
    '{%- endif -%}'
)


def _apply(name, old, new):
    if not frappe.db.exists("Print Format", name):
        return
    html = frappe.db.get_value("Print Format", name, "html") or ""
    if "custom_unique_talbat_number" in html:
        return  # already patched
    if old in html:
        frappe.db.set_value("Print Format", name, "html", html.replace(old, new, 1))


def execute():
    """Add the Talabat unique number (custom_unique_talbat_number) to the print
    formats only — next to the شباك number. Idempotent."""
    _apply("Kitchen Receipt", KR_OLD, KR_NEW)
    _apply("print format sales", PS_OLD, PS_NEW)
