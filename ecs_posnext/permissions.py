import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# Link fields that must not restrict reading the document they belong to.
#
# - Item Default / Commission: ERPNext's get_item_details calls
#   item.check_permission("read"), and Frappe applies User Permissions to the
#   link fields of child rows too. An Item whose defaults point at another
#   branch's Account/Branch/Warehouse/Cost Center becomes unreadable to a
#   branch-restricted cashier.
# - POS Profile / POS Payment Method: ERPNext's get_pos_profile calls
#   frappe.has_permission("POS Profile", "read", throw=True) while building the
#   invoice. A cashier whose User Permissions don't cover the profile's
#   warehouse, branch, cost center or payment modes cannot read their own
#   profile, and update_invoice fails with a PermissionError. Which profiles a
#   cashier may read is instead governed by POS Profile User Permissions, see
#   ensure_cashier_pos_profile_user_permissions().
IGNORE_USER_PERMISSION_LINKS = {
	"Item Default": ("Account", "Branch", "Warehouse", "Cost Center"),
	"Commission": ("Account", "Branch", "Warehouse", "Cost Center"),
	"POS Profile": ("Account", "Branch", "Warehouse", "Cost Center", "Mode of Payment"),
	"POS Payment Method": ("Mode of Payment",),
}


def ensure_pos_permission_setup():
	"""Idempotent; runs on every migrate (after_migrate), not only once as a patch.

	Migrate re-syncs Custom Field rows from app custom/*.json files and
	fixtures, which resets their ignore_user_permissions flag, and patches run
	before that sync - so a one-off patch gets undone.
	"""
	ensure_links_ignore_user_permissions()
	ensure_cashier_pos_profile_user_permissions()


def ensure_links_ignore_user_permissions():
	"""Pin ignore_user_permissions=1 with Property Setters (which migrate keeps).

	The decision is based on an existing Property Setter, not on the current
	meta value: a Custom Field that has the flag set right now loses it on the
	next migrate.
	"""
	for doctype, restricted_links in IGNORE_USER_PERMISSION_LINKS.items():
		if not frappe.db.exists("DocType", doctype):
			continue

		changed = False
		for field in frappe.get_meta(doctype).get_link_fields():
			if field.options not in restricted_links:
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

	frappe.clear_cache(doctype="Item")
	frappe.clear_cache(doctype="POS Profile")


def ensure_cashier_pos_profile_user_permissions(pos_profile=None, user=None):
	"""Give each restricted cashier a User Permission on every POS Profile they are
	assigned to (POS Profile User), so they keep seeing only their own profiles
	in Desk once the profile's link fields no longer filter it.

	Only users who already have User Permissions are touched - adding one to an
	unrestricted user (e.g. a manager) would restrict them. The permission is
	scoped to the POS Profile doctype itself (applicable_for), so it does not
	filter the cashier's Sales Invoices, shifts or other documents.
	"""
	conditions = {"disabled": 0}
	if pos_profile:
		conditions["name"] = pos_profile

	profiles = frappe.get_all("POS Profile", filters=conditions, pluck="name")
	if not profiles:
		return

	assignment_filters = {"parent": ["in", profiles], "parenttype": "POS Profile"}
	if user:
		assignment_filters["user"] = user

	assignments = frappe.get_all(
		"POS Profile User",
		filters=assignment_filters,
		fields=["user", "parent"],
	)
	if not assignments:
		return

	restricted_users = set(
		frappe.get_all(
			"User Permission",
			filters={"user": ["in", list({a.user for a in assignments if a.user}) or [""]]},
			pluck="user",
			distinct=True,
		)
	)

	for a in assignments:
		if not a.user or a.user not in restricted_users:
			continue

		# Any existing permission that covers this profile for POS Profile
		if frappe.db.exists(
			"User Permission",
			{"user": a.user, "allow": "POS Profile", "for_value": a.parent},
		):
			continue

		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": a.user,
				"allow": "POS Profile",
				"for_value": a.parent,
				"apply_to_all_doctypes": 0,
				"applicable_for": "POS Profile",
			}
		).insert(ignore_permissions=True)


def on_pos_profile_update(doc, method=None):
	"""Keep cashier POS Profile permissions in sync when users are assigned."""
	ensure_cashier_pos_profile_user_permissions(pos_profile=doc.name)


def on_user_permission_insert(doc, method=None):
	"""A user who just became restricted keeps read access to their assigned
	POS Profiles. Our own POS Profile permissions are skipped, so the insert
	below never re-triggers this hook into more work."""
	if doc.allow == "POS Profile":
		return
	ensure_cashier_pos_profile_user_permissions(user=doc.user)
