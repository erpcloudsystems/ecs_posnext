import frappe
from frappe.utils import cint


def execute():
    """Back-fill Warning After (min) from the existing Warning Threshold %.

    The threshold is now entered in minutes and the percentage is derived from it.
    Converting the other way first keeps every branch's current amber timing
    exactly where it was instead of snapping to the new field's default.
    """
    if not frappe.db.table_exists("KDS Settings"):
        return

    if not frappe.db.has_column("KDS Settings", "warning_threshold_minutes"):
        frappe.reload_doc("pos_next", "doctype", "kds_settings")

    rows = frappe.get_all(
        "KDS Settings",
        fields=["name", "default_target_minutes", "warning_threshold_pct", "warning_threshold_minutes"],
    )

    for row in rows:
        # Overwrite unconditionally. The field is new, so any value already there
        # is the schema default that was stamped on when the DocType synced — not
        # something anyone chose. Skipping those would leave minutes disagreeing
        # with the live percentage, and the next save would silently shift the
        # amber timing.
        target = cint(row.default_target_minutes) or 15
        pct = cint(row.warning_threshold_pct) or 70
        minutes = round(target * pct / 100)

        # Keep it strictly below target so validate() can't reject the record.
        minutes = max(1, min(minutes, target - 1)) if target > 1 else 1

        frappe.db.set_value("KDS Settings", row.name, "warning_threshold_minutes", minutes, update_modified=False)
