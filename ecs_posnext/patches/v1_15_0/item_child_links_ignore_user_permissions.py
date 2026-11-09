import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# Item child tables whose link fields must not restrict reading the Item itself
CHILD_DOCTYPES = ("Item Default", "Commission")
RESTRICTED_LINKS = ("Account", "Branch", "Warehouse", "Cost Center")


def execute():
	ensure_item_child_links_ignore_user_permissions()


def ensure_item_child_links_ignore_user_permissions():
	"""Let branch-restricted cashiers read Items during POS invoicing.

	ERPNext's get_item_details calls item.check_permission("read"), and Frappe
	applies User Permissions to the link fields of child rows too. An Item whose
	Item Defaults or Commission rows point at another branch's Account, Branch,
	Warehouse or Cost Center is therefore unreadable to a restricted cashier,
	and update_invoice / submit_invoice fail with a PermissionError on Item.

	Runs on every migrate (after_migrate), not only once as a patch: migrate
	re-syncs Custom Field rows from app custom/*.json files and fixtures, which
	resets their ignore_user_permissions flag, and patches run before that sync.
	The decision is based on an existing Property Setter, not on the current
	meta value, because a Custom Field that has the flag set right now will
	lose it on the next migrate.
	"""
	changed = False
	for doctype in CHILD_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue

		for field in frappe.get_meta(doctype).get_link_fields():
			if field.options not in RESTRICTED_LINKS:
				continue

			# Standard fields that already ignore user permissions keep the flag
			# from core JSON; only Custom Fields get reset by migrate.
			if field.ignore_user_permissions and not field.get("is_custom_field"):
				continue

			if frappe.db.exists(
				"Property Setter",
				{
					"doc_type": doctype,
					"field_name": field.fieldname,
					"property": "ignore_user_permissions",
					"value": "1",
				},
			):
				continue

			make_property_setter(
				doctype,
				field.fieldname,
				"ignore_user_permissions",
				1,
				"Check",
				validate_fields_for_doctype=False,
			)
			changed = True

		if changed:
			frappe.clear_cache(doctype=doctype)

	if changed:
		frappe.clear_cache(doctype="Item")
