import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Give Pricing Rule validity a time component, not just a date.

    Core's valid_from/valid_upto are Date fields and Frappe does not allow
    converting a standard Date field to Datetime, so the window moves to two new
    Datetime fields. A rule is active only while the current date and time falls
    inside the window; leaving a field empty means that end is unbounded, so
    existing rules keep working untouched.

    The legacy Date fields are hidden rather than dropped: submitted historical
    transactions already store their own applied rate/discount, so nothing that
    is already posted is affected either way.
    """
    create_custom_fields(
        {
            "Pricing Rule": [
                {
                    "fieldname": "custom_valid_from_datetime",
                    "label": "Valid From",
                    "fieldtype": "Datetime",
                    "insert_after": "valid_upto",
                    "description": (
                        "Pricing Rule becomes active only from this exact date and time."
                    ),
                },
                {
                    "fieldname": "custom_valid_upto_datetime",
                    "label": "Valid To",
                    "fieldtype": "Datetime",
                    "insert_after": "custom_valid_from_datetime",
                    "description": (
                        "Pricing Rule automatically becomes inactive after this exact date and time."
                    ),
                },
            ]
        },
        ignore_validate=True,
    )

    for fieldname in ("valid_from", "valid_upto"):
        if frappe.db.exists(
            "Property Setter",
            {"doc_type": "Pricing Rule", "field_name": fieldname, "property": "hidden"},
        ):
            continue

        frappe.make_property_setter(
            {
                "doctype": "Pricing Rule",
                "fieldname": fieldname,
                "property": "hidden",
                "value": 1,
                "property_type": "Check",
            },
            is_system_generated=False,
        )
