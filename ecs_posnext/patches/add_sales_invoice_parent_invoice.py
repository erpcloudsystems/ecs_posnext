# Copyright (c) 2026, ECS and contributors
"""Add a real parent-invoice link to supplement Sales Invoices.

A supplement ("إضافة") is a separate Sales Invoice created by pressing "+" on an
already-submitted order. Until now the only trace of its parent was the display
label in `custom_number_order` (e.g. parent "M-36" → supplement "M-36-1"). That
label is regenerated every shift, so the same "M-36" belongs to a different order
on a different day — which made supplements attach to, and show under, the wrong
order (a day-3 order showing a day-4 supplement).

This field stores the parent's actual docname (ACC-SINV-...), which is unique and
never recycled, so both numbering and grouping become exact.

Existing rows are deliberately left untouched: they keep grouping by the legacy
label fallback in the All Orders screen.
"""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Invoice": [
				{
					"fieldname": "custom_parent_invoice",
					"label": "Parent Invoice (Supplement Of)",
					"fieldtype": "Link",
					"options": "Sales Invoice",
					"insert_after": "custom_number_order",
					"read_only": 1,
					"no_copy": 1,
				},
			]
		},
		ignore_validate=True,
	)
