import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


def _sync_driver_availability(driver, exclude_assignment=None):
	"""
	Recompute a driver's dispatch status from their outstanding assignments.

	A driver becomes 'Available' as soon as they have no non-terminal assignments
	left (across all shifts), otherwise 'On Delivery'. A manually parked driver
	('Off Duty') is never auto-reactivated. Talabat assignments have no driver.

	`exclude_assignment` skips the assignment currently being saved, whose new
	terminal status is not committed yet when this runs in before_save.
	"""
	if not driver:
		return
	current = frappe.db.get_value("Driver", driver, "dispatch_current_status")
	if current == "Off Duty":
		return
	filters = {
		"driver": driver,
		"status": ["in", ["Assigned", "Picked Up", "Out for Delivery"]],
		"docstatus": ["!=", 2],
	}
	if exclude_assignment:
		filters["name"] = ["!=", exclude_assignment]
	active = frappe.db.count("Delivery Assignment", filters)
	new_status = "Available" if active == 0 else "On Delivery"
	if new_status != current:
		frappe.db.set_value("Driver", driver, "dispatch_current_status", new_status)


class DeliveryAssignment(Document):
	def validate(self):
		self._validate_shift_open()
		self._enforce_prepaid_zero()
		self._validate_channel_driver()

	def _validate_channel_driver(self):
		# Internal deliveries require one of our drivers; Talabat is handled by the platform's own driver.
		if (self.delivery_channel or "Internal") == "Internal" and not self.driver:
			frappe.throw(_("A driver is required for internal delivery assignments."))

	def before_save(self):
		if not self.assigned_time:
			self.assigned_time = now_datetime()
		self._fetch_order_details()
		self._handle_status_transition()

	def _validate_shift_open(self):
		shift_status = frappe.db.get_value("POS Opening Shift", self.shift, "status")
		if shift_status != "Open":
			# frappe.throw(
			# 	_("Delivery Assignment can only be created/updated while the POS Shift is Open. Shift {0} is {1}.").format(
			# 		self.shift, shift_status
			# 	)
			# )
			pass

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
				# Prepaid (incl. Talabat handover) never collects — leave amount at zero.
				if self.payment_mode != "Prepaid":
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
			if not self.out_for_delivery_time:
				self.out_for_delivery_time = now_datetime()
			if self.driver:
				frappe.db.set_value("Driver", self.driver, "dispatch_current_status", "On Delivery")

		elif self.status == "Delivered":
			self.delivered_time = now_datetime()
			settings = frappe.get_single("Dispatch Settings")
			if self.payment_mode == "Cash (COD)" and not self.amount_collected:
				if not settings.allow_collection_mismatch:
					frappe.throw(_("Amount Collected is required for COD deliveries."))
			if settings.require_proof_on_delivery and not self.proof_image:
				frappe.throw(_("Proof of delivery image is required."))
			_sync_driver_availability(self.driver, exclude_assignment=self.name)

		elif self.status in ("Returned", "Failed"):
			self.amount_collected = 0
			self.delivered_time = now_datetime()
			_sync_driver_availability(self.driver, exclude_assignment=self.name)

		frappe.publish_realtime("dispatch_desk_refresh", {"shift": self.shift})
