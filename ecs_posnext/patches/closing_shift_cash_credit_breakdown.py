import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Split the closing-shift difference into cash vs (branch) credit, and add a
    direct-sale reconciliation summary (expected vs collected, cash & credit).

    "Branch / direct sale" = modes of payment configured on the shift's POS Profile.
    Talabat / external modes are excluded from these figures.
    """
    create_custom_fields(
        {
            "POS Closing Shift": [
                {
                    "fieldname": "actual_credit_card",
                    "label": "Actual Credit Card",
                    "fieldtype": "Currency",
                    "insert_after": "total_cash",
                    "description": "Actual amount closed on the branch credit card (direct sale).",
                },
                {
                    "fieldname": "diff_breakdown_section",
                    "label": "Difference Breakdown",
                    "fieldtype": "Section Break",
                    "insert_after": "total_diff",
                },
                {
                    "fieldname": "total_diff_cash",
                    "label": "Total Diff Cash",
                    "fieldtype": "Currency",
                    "read_only": 1,
                    "insert_after": "diff_breakdown_section",
                },
                {
                    "fieldname": "total_diff_credit",
                    "label": "Total Diff Credit",
                    "fieldtype": "Currency",
                    "read_only": 1,
                    "insert_after": "total_diff_cash",
                },
                {
                    "fieldname": "direct_sale_section",
                    "label": "Direct Sale Reconciliation (بيع مباشر)",
                    "fieldtype": "Section Break",
                    "insert_after": "total_diff_credit",
                },
                {
                    "fieldname": "direct_cash_sold",
                    "label": "Cash Sold (Expected)",
                    "fieldtype": "Currency",
                    "read_only": 1,
                    "insert_after": "direct_sale_section",
                },
                {
                    "fieldname": "direct_cash_collected",
                    "label": "Cash Collected (Actual)",
                    "fieldtype": "Currency",
                    "read_only": 1,
                    "insert_after": "direct_cash_sold",
                },
                {
                    "fieldname": "direct_sale_col_break",
                    "fieldtype": "Column Break",
                    "insert_after": "direct_cash_collected",
                },
                {
                    "fieldname": "direct_credit_sold",
                    "label": "Credit Sold (Expected)",
                    "fieldtype": "Currency",
                    "read_only": 1,
                    "insert_after": "direct_sale_col_break",
                },
                {
                    "fieldname": "direct_credit_collected",
                    "label": "Credit Collected (Actual)",
                    "fieldtype": "Currency",
                    "read_only": 1,
                    "insert_after": "direct_credit_sold",
                },
            ]
        },
        ignore_validate=True,
    )
