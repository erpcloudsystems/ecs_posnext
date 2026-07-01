import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class DispatchShift(Document):
	def validate(self):
		if not self.posting_date:
			self.posting_date = frappe.utils.today()
		if not self.dispatcher:
			self.dispatcher = frappe.session.user
		self._validate_single_open_shift()

	def _validate_single_open_shift(self):
		if self.docstatus != 0:
			return
		existing = frappe.db.exists(
			"Dispatch Shift",
			{
				"dispatcher": self.dispatcher,
				"status": "Open",
				"docstatus": 1,
				"name": ["!=", self.name or ""],
			},
		)
		if existing:
			frappe.throw(
				_("Dispatcher {0} already has an open shift: {1}. Close it before opening a new one.").format(
					self.dispatcher, existing
				)
			)

	def on_submit(self):
		self.db_set("status", "Open")
		self.db_set("opening_time", now_datetime())
		frappe.publish_realtime("dispatch_desk_refresh", {"shift": self.name})

	def on_cancel(self):
		self._block_cancel_if_accounting_exists()
		self.db_set("status", "Draft")

	def _block_cancel_if_accounting_exists(self):
		if frappe.db.exists(
			"Payment Entry",
			{"custom_dispatch_shift": self.name, "docstatus": 1},
		):
			frappe.throw(
				_("Cannot cancel shift {0} — submitted Payment Entries exist. Cancel them first.").format(
					self.name
				)
			)
		if self.journal_entry and frappe.db.get_value(
			"Journal Entry", self.journal_entry, "docstatus"
		) == 1:
			frappe.throw(
				_("Cannot cancel shift {0} — a submitted handover Journal Entry exists.").format(
					self.name
				)
			)

	@frappe.whitelist()
	def close_shift(self):
		from ecs_posnext.ecs_posnext.api.dispatcher import close_dispatch_shift

		close_dispatch_shift(self.name)
