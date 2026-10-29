import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# Item child tables whose link fields must not restrict reading the Item itself
CHILD_DOCTYPES = ("Item Default", "Commission")
RESTRICTED_LINKS = ("Account", "Branch", "Warehouse", "Cost Center")


def execute():
	"""Let branch-restricted cashiers read Items during POS invoicing.

	ERPNext's get_item_details calls item.check_permission("read"), and Frappe
	applies User Permissions to the link fields of child rows too. An Item whose
	Item Defaults or Commission rows point at another branch's Account, Branch,
	Warehouse or Cost Center is therefore unreadable to a restricted cashier,
	and update_invoice / submit_invoice fail with a PermissionError on Item.

	Property Setters are used for custom fields too: migrate re-syncs Custom
	Field rows from app installs and fixtures, which resets the flag on them.
	"""
	for doctype in CHILD_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue

		for field in frappe.get_meta(doctype).get_link_fields():
			if field.options not in RESTRICTED_LINKS or field.ignore_user_permissions:
				continue

			make_property_setter(
				doctype,
				field.fieldname,
				"ignore_user_permissions",
				1,
				"Check",
				validate_fields_for_doctype=False,
			)

		frappe.clear_cache(doctype=doctype)

	frappe.clear_cache(doctype="Item")
