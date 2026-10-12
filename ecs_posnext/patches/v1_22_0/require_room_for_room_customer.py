import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""
	Carry the "a Room Customer must name a room" rule over to Sales Order.

	v1_15_0 put it on Sales Invoice, which is where the POS used to book a sale.
	The POS books a Sales Order now, so the rule stopped applying to anything and
	room-service sales went out with no room on them - unable to reach Protel,
	because nothing said whose folio to charge.
	"""
	create_custom_fields(
		{
			"Sales Order": [
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

	if frappe.db.exists("Custom Field", "Sales Order-room"):
		frappe.db.set_value(
			"Custom Field",
			"Sales Order-room",
			"mandatory_depends_on",
			'eval:doc.posa_customer_type == "Room Customer"',
		)
		frappe.clear_cache(doctype="Sales Order")
