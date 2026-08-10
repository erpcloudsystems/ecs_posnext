import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Add POS Customer Type field and make the Room dimension mandatory for Room Customers."""
	create_custom_fields(
		{
			"Sales Invoice": [
				{
					"fieldname": "posa_customer_type",
					"label": "POS Customer Type",
					"fieldtype": "Select",
					"options": "\nRoom Customer\nGuest Customer",
					"insert_after": "customer",
					"print_hide": 1,
				}
			]
		},
		ignore_validate=True,
	)

	if frappe.db.exists("Custom Field", "Sales Invoice-room"):
		frappe.db.set_value(
			"Custom Field",
			"Sales Invoice-room",
			"mandatory_depends_on",
			'eval:doc.posa_customer_type == "Room Customer"',
		)
		frappe.clear_cache(doctype="Sales Invoice")
