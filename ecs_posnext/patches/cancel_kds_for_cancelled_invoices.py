import frappe


def execute():
    """Retroactively cancel KDS Orders whose Sales Invoice has been cancelled.

    Going forward this is handled by the ``on_cancel`` hook
    (ecs_posnext.ecs_posnext.api.kds.on_sales_invoice_cancel), but invoices that
    were cancelled before that hook existed still have active KDS Orders that keep
    showing up on the kitchen (KDS) and dispatch screens. This patch cleans them up.

    Idempotent: it only touches KDS Orders that are not already Cancelled, so it is
    safe to run repeatedly.
    """
    if not frappe.db.table_exists("KDS Order"):
        return

    stale = frappe.db.sql(
        """
        SELECT ko.name
        FROM `tabKDS Order` ko
        JOIN `tabSales Invoice` si ON si.name = ko.sales_invoice
        WHERE si.docstatus = 2
          AND ko.status != 'Cancelled'
        """,
        pluck=True,
    )

    for name in stale:
        frappe.db.set_value("KDS Order", name, "status", "Cancelled", update_modified=False)

    if stale:
        frappe.db.commit()
        print(f"[ecs_posnext] Cancelled {len(stale)} KDS Order(s) for cancelled invoices")
