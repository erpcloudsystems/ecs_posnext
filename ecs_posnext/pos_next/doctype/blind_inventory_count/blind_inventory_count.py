# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Blind Inventory Count — an end-of-day physical stock count for the Branch Manager.

The manager enters the physically counted quantities WITHOUT seeing the system's
expected quantities. The expected (system) qty and the resulting variance are captured
and revealed ONLY when the document is submitted. This is an AUDIT record: it does NOT
move stock — it just records what was counted versus what the system believed.

A submitted count for the current open POS Business Day is REQUIRED before that day can
be closed (see ecs_posnext.api.business_day / POS Business Day.close).
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

# Rows where |counted - system| is at or below this are treated as an exact match.
VARIANCE_TOLERANCE = 0.001


class BlindInventoryCount(Document):
	def validate(self):
		self._set_defaults()
		self._resolve_business_day()

		if not self.get("items"):
			frappe.throw(_("Add at least one item to count."))

		# While the count is still a draft it must stay BLIND: never expose the system
		# quantity or variance. These are populated only on submit (see reveal_variance).
		if self.docstatus == 0:
			for row in self.items:
				row.system_qty = 0
				row.variance_qty = 0
				row.valuation_rate = 0
				row.variance_value = 0
			self.has_variance = 0
			self.total_items = 0
			self.items_with_variance = 0
			self.total_variance_qty = 0
			self.total_variance_value = 0

	def before_submit(self):
		self.reveal_variance()

	def reveal_variance(self):
		"""Read the system (expected) qty for every row and compute the variance. Runs at
		submit time so the counter never sees expected figures beforehand."""
		self.count_datetime = self.count_datetime or now_datetime()

		total_items = 0
		items_with_variance = 0
		total_variance_qty = 0.0
		total_variance_value = 0.0

		for row in self.items:
			if not row.item_code:
				continue
			warehouse = row.warehouse or self.warehouse
			row.warehouse = warehouse

			bin_row = frappe.db.get_value(
				"Bin",
				{"item_code": row.item_code, "warehouse": warehouse},
				["actual_qty", "valuation_rate"],
				as_dict=True,
			)
			system_qty = flt(bin_row.actual_qty) if bin_row else 0.0
			val_rate = flt(bin_row.valuation_rate) if bin_row else 0.0

			row.system_qty = system_qty
			row.valuation_rate = val_rate
			row.variance_qty = flt(row.counted_qty) - system_qty
			row.variance_value = row.variance_qty * val_rate

			total_items += 1
			if abs(row.variance_qty) > VARIANCE_TOLERANCE:
				items_with_variance += 1
				total_variance_qty += abs(row.variance_qty)
				total_variance_value += abs(row.variance_value)

		self.total_items = total_items
		self.items_with_variance = items_with_variance
		self.total_variance_qty = total_variance_qty
		self.total_variance_value = total_variance_value
		self.has_variance = 1 if items_with_variance else 0

	def _set_defaults(self):
		if not self.count_datetime:
			self.count_datetime = now_datetime()
		if not self.counted_by:
			self.counted_by = frappe.session.user
		if self.pos_profile and not self.warehouse:
			self.warehouse = frappe.db.get_value("POS Profile", self.pos_profile, "warehouse")
		if self.pos_profile and not self.company:
			self.company = frappe.db.get_value("POS Profile", self.pos_profile, "company")
		if not self.warehouse:
			frappe.throw(_("Warehouse is required — set a warehouse on POS Profile {0} or pick one.").format(self.pos_profile))
		# Stamp every row's warehouse so the count is unambiguous.
		for row in self.get("items") or []:
			if not row.warehouse:
				row.warehouse = self.warehouse

	def _resolve_business_day(self):
		"""Bind the count to the current OPEN business day for the profile."""
		if self.pos_business_day:
			return
		if not self.pos_profile:
			return
		open_bd = frappe.db.get_value(
			"POS Business Day",
			{"pos_profile": self.pos_profile, "status": "Open"},
			"name",
			order_by="business_date desc",
		)
		if open_bd:
			self.pos_business_day = open_bd


@frappe.whitelist()
def get_default_count_items(warehouse):
	"""Return the items flagged `custom_include_in_blind_count` on Item — WITHOUT any
	quantity (blind). These are auto-loaded into every new count sheet so the manager only
	enters counted qty. Flagged items are included even if they have no Bin yet (system 0),
	so a stock-out that is physically present still gets counted."""
	rows = frappe.db.sql(
		"""
		SELECT i.name AS item_code, i.item_name, i.stock_uom
		FROM `tabItem` i
		WHERE i.is_stock_item = 1
		  AND IFNULL(i.disabled, 0) = 0
		  AND IFNULL(i.custom_include_in_blind_count, 0) = 1
		ORDER BY i.item_name
		""",
		as_dict=True,
	)
	return [
		{
			"item_code": r.item_code,
			"item_name": r.item_name,
			"uom": r.stock_uom,
			"warehouse": warehouse,
		}
		for r in rows
	]


@frappe.whitelist()
def get_warehouse_count_items(warehouse):
	"""Return every stock Item that has a Bin in this warehouse — WITHOUT any quantity, so
	the count sheet the manager fills stays blind. Used by the 'Load Items' button."""
	if not warehouse:
		return []
	rows = frappe.db.sql(
		"""
		SELECT b.item_code, i.item_name, i.stock_uom
		FROM `tabBin` b
		INNER JOIN `tabItem` i ON i.name = b.item_code
		WHERE b.warehouse = %(wh)s
		  AND i.is_stock_item = 1
		  AND IFNULL(i.disabled, 0) = 0
		ORDER BY i.item_name
		""",
		{"wh": warehouse},
		as_dict=True,
	)
	return [
		{
			"item_code": r.item_code,
			"item_name": r.item_name,
			"uom": r.stock_uom,
			"warehouse": warehouse,
		}
		for r in rows
	]


def assert_business_day_counted(business_day):
	"""Raise unless a SUBMITTED Blind Inventory Count exists for this business day.
	Called by POS Business Day.close() to enforce the mandatory end-of-day count."""
	if not business_day:
		return
	exists = frappe.db.exists(
		"Blind Inventory Count",
		{"pos_business_day": business_day, "docstatus": 1},
	)
	if not exists:
		frappe.throw(
			_(
				"A submitted Blind Inventory Count is required before this Business Day can be "
				"closed. Please complete and submit the end-of-day stock count first."
			),
			title=_("Inventory Count Required"),
		)
