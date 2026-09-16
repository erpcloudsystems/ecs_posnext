import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""Make the Pricing Rule daily time window official, and repair the migration.

	`pricing_rule_validity_datetime` moved the validity window onto two Datetime
	fields, and a daily time window was later added by hand through the UI. Two
	things are fixed here.

	The Time fields become code-managed like the Datetime ones, so a fresh site
	gets them too instead of only the site they were drawn on. They express the
	recurring part of the window: the Datetime fields say which span of days a
	rule exists, the Time fields say which hours of each of those days it applies.

	The Datetime fields are also backfilled from the legacy Date fields. The
	earlier patch created them empty and hid valid_from/valid_upto, and an empty
	end of the window reads as unbounded -- so every rule predating that patch,
	including ones whose valid_upto had already passed, was left valid forever.
	Copying the old dates across restores each rule's intended window: valid_from
	from the start of its day, valid_upto through the end of its own day, since a
	Date-only valid_upto has always meant that whole day was included.
	"""
	create_custom_fields(
		{
			"Pricing Rule": [
				{
					"fieldname": "custom_valid_time_from",
					"label": "Valid Time From",
					"fieldtype": "Time",
					"insert_after": "custom_valid_upto_datetime",
					"description": (
						"Optional. Time of day the Pricing Rule starts applying, on every day"
						" inside the Valid From/Valid To window. Leave both times empty to"
						" apply around the clock."
					),
				},
				{
					"fieldname": "custom_valid_time_upto",
					"label": "Valid Time Upto",
					"fieldtype": "Time",
					"insert_after": "custom_valid_time_from",
					"description": (
						"Optional. Time of day the Pricing Rule stops applying, on every day"
						" inside the Valid From/Valid To window. An earlier time than Valid"
						" Time From means the window crosses midnight."
					),
				},
			]
		},
		ignore_validate=True,
	)

	rules = frappe.get_all(
		"Pricing Rule",
		filters={"custom_valid_from_datetime": ("is", "not set")},
		or_filters=[
			["valid_from", "is", "set"],
			["valid_upto", "is", "set"],
		],
		fields=["name", "valid_from", "valid_upto", "custom_valid_upto_datetime"],
	)

	for rule in rules:
		values = {}
		if rule.valid_from:
			values["custom_valid_from_datetime"] = f"{rule.valid_from} 00:00:00"
		if rule.valid_upto and not rule.custom_valid_upto_datetime:
			values["custom_valid_upto_datetime"] = f"{rule.valid_upto} 23:59:59"

		if values:
			frappe.db.set_value("Pricing Rule", rule.name, values, update_modified=False)
