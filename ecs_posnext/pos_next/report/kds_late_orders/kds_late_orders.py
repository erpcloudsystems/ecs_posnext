import frappe


def execute(filters=None):
    columns = [
        {"label": "Order No",         "fieldname": "order_no",        "fieldtype": "Data",     "width": 90},
        {"label": "Sales Invoice",    "fieldname": "sales_invoice",   "fieldtype": "Link",     "options": "Sales Invoice", "width": 160},
        {"label": "Branch",           "fieldname": "branch",          "fieldtype": "Link",     "options": "Branch",        "width": 130},
        {"label": "Station",          "fieldname": "kds_station",     "fieldtype": "Link",     "options": "KDS Station",   "width": 130},
        {"label": "Order Time",       "fieldname": "order_time",      "fieldtype": "Datetime", "width": 150},
        {"label": "Target (min)",     "fieldname": "target_minutes",  "fieldtype": "Int",      "width": 100},
        {"label": "Elapsed (min)",    "fieldname": "elapsed_minutes", "fieldtype": "Int",      "width": 110},
        {"label": "Overdue By (min)", "fieldname": "overdue_minutes", "fieldtype": "Int",      "width": 120},
        {"label": "Order Status",     "fieldname": "status",          "fieldtype": "Data",     "width": 100},
        {"label": "Station Status",   "fieldname": "station_status",  "fieldtype": "Data",     "width": 110},
    ]
    return columns, get_data(filters or {})


def get_filters():
    return [
        {
            "fieldname": "branch",
            "label": "Branch",
            "fieldtype": "Link",
            "options": "Branch",
        },
        {
            "fieldname": "station",
            "label": "Station",
            "fieldtype": "Link",
            "options": "KDS Station",
        },
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.utils.today(),
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.utils.today(),
        },
    ]


def get_data(filters):
    cond = "AND ko.status NOT IN ('Completed', 'Cancelled') AND koi.station_status = 'Pending'"
    values = {}

    if filters.get("branch"):
        cond += " AND ko.branch = %(branch)s"
        values["branch"] = filters["branch"]
    if filters.get("station"):
        cond += " AND koi.kds_station = %(station)s"
        values["station"] = filters["station"]
    if filters.get("from_date"):
        cond += " AND DATE(ko.order_time) >= %(from_date)s"
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        cond += " AND DATE(ko.order_time) <= %(to_date)s"
        values["to_date"] = filters["to_date"]

    return frappe.db.sql(
        f"""
        SELECT
            ko.order_no,
            ko.sales_invoice,
            ko.branch,
            koi.kds_station,
            ko.order_time,
            ko.target_minutes,
            ko.status,
            koi.station_status,
            TIMESTAMPDIFF(MINUTE, ko.order_time, NOW()) AS elapsed_minutes,
            GREATEST(0, TIMESTAMPDIFF(MINUTE, ko.order_time, NOW()) - ko.target_minutes) AS overdue_minutes
        FROM `tabKDS Order` ko
        JOIN `tabKDS Order Item` koi ON koi.parent = ko.name
        WHERE koi.kds_station IS NOT NULL
          AND koi.kds_station != ''
          AND TIMESTAMPDIFF(MINUTE, ko.order_time, NOW()) > ko.target_minutes
          {cond}
        GROUP BY ko.name, koi.kds_station
        ORDER BY overdue_minutes DESC, ko.order_no ASC
        """,
        values=values,
        as_dict=True,
    )
