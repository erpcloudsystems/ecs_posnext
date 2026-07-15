from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Let a Pricing Rule be limited to specific branches.

    An empty table means the rule applies at every branch, so existing rules keep
    working untouched. The POS matches this against the invoice branch (the target
    branch for Call Center, otherwise the POS Profile's own branch).
    """
    create_custom_fields(
        {
            "Pricing Rule": [
                {
                    "fieldname": "custom_allowed_branches",
                    "label": "Allowed Branches",
                    "fieldtype": "Table MultiSelect",
                    "options": "POS Offer Allowed Branch",
                    "insert_after": "company",
                    "description": (
                        "Limit this rule to these branches. Leave empty to allow all branches."
                    ),
                }
            ]
        },
        ignore_validate=True,
    )
