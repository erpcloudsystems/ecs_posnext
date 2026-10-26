import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
	"""Allow the same table number in different branches.

	Table Number.no is unique in the kak app; uniqueness per branch is
	enforced instead by ecs_posnext.validations.validate_table_number.
	"""
	if not frappe.db.exists("DocType", "Table Number"):
		return

	make_property_setter(
		"Table Number", "no", "unique", 0, "Check", validate_fields_for_doctype=False
	)

	if frappe.db.has_index("tabTable Number", "no"):
		frappe.db.sql_ddl("ALTER TABLE `tabTable Number` DROP INDEX `no`")

	frappe.clear_cache(doctype="Table Number")
