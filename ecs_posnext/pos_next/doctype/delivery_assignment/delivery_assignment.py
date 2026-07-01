import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class DeliveryAssignment(Document):
	def validate(self):
		self._validate_shift_open()
		self._enforce_prepaid_zero()

	def before_save(self):
		if not self.assigned_time:
			self.assigned_time = now_datetime()
		self._fetch_order_details()
		self._handle_status_transition()

	def _validate_shift_open(self):
		shift_status = frappe.db.get_value("POS Opening Shift", self.shift, "status")
		if shift_status != "Open":
			frappe.throw(
				_("Delivery Assignment can only be created/updated while the POS Shift is Open. Shift {0} is {1}.").format(
					self.shift, shift_status
				)
			)

	def _enforce_prepaid_zero(self):
		if self.payment_mode == "Prepaid":
			self.amount_to_collect = 0

	def _fetch_order_details(self):
		if not self.order_reference:
			return
		try:
			if self.order_doctype == "Sales Invoice":
				doc = frappe.get_doc("Sales Invoice", self.order_reference)
				self.customer = doc.customer
				self.amount_to_collect = doc.outstanding_amount if not self.amount_to_collect else self.amount_to_collect
				addr = frappe.db.get_value(
					"Address",
					{"name": doc.shipping_address_name or doc.customer_address},
					["address_line1", "city"],
					as_dict=True,
				)
				if addr:
					self.delivery_address = f"{addr.address_line1}, {addr.city}"
				self.contact_phone = doc.contact_mobile or doc.contact_phone or ""
			elif self.order_doctype == "Delivery Note":
				doc = frappe.get_doc("Delivery Note", self.order_reference)
				self.customer = doc.customer
				self.contact_phone = doc.contact_phone or ""
		except Exception:
			pass

	def _handle_status_transition(self):
		prev = self.get_doc_before_save()
		if not prev or prev.status == self.status:
			return

		if self.status == "Out for Delivery":
			frappe.db.set_value("Driver", self.driver, "dispatch_current_status", "On Delivery")

		elif self.status == "Delivered":
			self.delivered_time = now_datetime()
			settings = frappe.get_single("Dispatch Settings")
			if self.payment_mode == "Cash (COD)" and not self.amount_collected:
				if not settings.allow_collection_mismatch:
					frappe.throw(_("Amount Collected is required for COD deliveries."))
			if settings.require_proof_on_delivery and not self.proof_image:
				frappe.throw(_("Proof of delivery image is required."))
			if self._all_driver_assignments_terminal():
				frappe.db.set_value("Driver", self.driver, "dispatch_current_status", "Available")

		elif self.status in ("Returned", "Failed"):
			self.amount_collected = 0
			self.delivered_time = now_datetime()
			if self._all_driver_assignments_terminal():
				frappe.db.set_value("Driver", self.driver, "dispatch_current_status", "Available")

		frappe.publish_realtime("dispatch_desk_refresh", {"shift": self.shift})

	def _all_driver_assignments_terminal(self):
		"""Return True if all other active assignments for this driver are in a terminal state."""
		active = frappe.db.count(
			"Delivery Assignment",
			{
				"driver": self.driver,
				"shift": self.shift,
				"name": ["!=", self.name],
				"status": ["in", ["Assigned", "Picked Up", "Out for Delivery"]],
				"docstatus": ["!=", 2],
			},
		)
		return active == 0
