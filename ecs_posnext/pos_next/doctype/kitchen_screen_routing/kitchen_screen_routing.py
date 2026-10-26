# Copyright (c) 2026, ecs_posnext and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class KitchenScreenRouting(Document):
	def validate(self):
		seen = set()
		for row in self.rules:
			key = (row.branch, row.item_group)
			if key in seen:
				frappe.throw(
					_("Row #{0}: Duplicate rule for Branch {1} and Item Group {2}").format(
						row.idx, frappe.bold(row.branch), frappe.bold(row.item_group)
					)
				)
			seen.add(key)
