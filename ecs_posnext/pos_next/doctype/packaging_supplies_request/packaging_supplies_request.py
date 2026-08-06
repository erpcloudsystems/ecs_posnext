# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from ecs_posnext.api.branch_requisition import validate_requisition


class PackagingSuppliesRequest(Document):
	def validate(self):
		validate_requisition(self)
