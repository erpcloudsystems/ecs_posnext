# Copyright (c) 2026, Youssef Restom and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from erpnext.controllers.sales_and_purchase_return import make_return_doc


class Wastedge(Document):
	def on_submit(self):
		# frappe.throw(f"{self.type}")
		if self.type == "Loaded":
			self.process_loaded_type()
		if self.type=="Consumptions":
			self.process_consumptions_type()
			pass
			
	def on_cancel(self):
		if self.type == "Loaded":
			self.cancel_linked_documents()
	def process_consumptions_type(self):
		"""Process Consumptions type - stock entry."""
		stock_entry = self.create_consumptions_stock_entry()
		
	def create_consumptions_stock_entry(self):
		"""Create Stock Entry for consumptions wastage."""
		
		
		
		
		# Create Stock Entry
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Consumptions"
		stock_entry.custom_employee = self.employee
		stock_entry.posting_date = nowdate()
		stock_entry.set_posting_time = 1
		
		# Add custom field for loaded type if exists
		if hasattr(stock_entry, 'custom_wastedge_type'):
			stock_entry.custom_wastedge_type = "Loaded"
		
		# Add reference to wastedge
		if hasattr(stock_entry, 'custom_wastedge_reference'):
			stock_entry.custom_wastedge_reference = self.name
		
		
		# Add regular items that are stock items (negative qty for return/loaded)
		for item in self.items:
			is_stock_item = frappe.db.get_value("Item", item.item, "is_stock_item")
			if is_stock_item:
				stock_entry.append("items", {
					"item_code": item.item,
					"qty": flt(item.qty),
					"s_warehouse": item.warehouse,
					"uom": item.uom,
				})
		
		if not stock_entry.items:
			frappe.throw(_("No stock items found in the invoice"))
		
		stock_entry.insert()
		stock_entry.submit()
		
		# Link stock entry to wastedge
		
		return stock_entry.name
	def process_loaded_type(self):
		"""Process Loaded type - create return invoice and stock entry."""
		if not self.sales_invoice:
			frappe.throw(_("Sales Invoice is required for Loaded type"))
		
		# Step 1: Create Sales Invoice Return using standard function
		return_invoice = self.create_sales_return()
		
		# Step 2: Create Stock Entry for loaded items
		stock_entry = self.create_loaded_stock_entry()
		
		frappe.msgprint(
			_("Created Return Invoice: {0} and Stock Entry: {1}").format(
				frappe.utils.get_link_to_form("Sales Invoice", return_invoice),
				frappe.utils.get_link_to_form("Stock Entry", stock_entry)
			),
			indicator="green"
		)
	
	def create_sales_return(self):
		"""Create a Sales Invoice return using ERPNext standard function."""
		# Use standard make_return_doc function
		return_doc = make_return_doc("Sales Invoice", self.sales_invoice)
		return_doc.posting_date = nowdate()
		return_doc.is_pos = 0
		# Ensure all item quantities are negative
		for item in return_doc.items:
			if flt(item.qty) > 0:
				item.qty = -1 * flt(item.qty)
		# frappe.throw(f"{return_doc.items[0].qty}")
		return_doc.insert()
		return_doc.submit()
		
		# Link return invoice to wastedge
		
		return return_doc.name
	
	def create_loaded_stock_entry(self):
		"""Create Stock Entry for loaded wastage."""
		source_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
		
		# Get default warehouse from invoice or company
		warehouse = source_invoice.set_warehouse or frappe.db.get_single_value(
			"Stock Settings", "default_warehouse"
		)
		
		if not warehouse:
			frappe.throw(_("Please set a default warehouse in Stock Settings"))
		
		# Create Stock Entry
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Loaded"
		stock_entry.company = source_invoice.company
		# frappe.throw(f"{self.employee}")
		stock_entry.custom_employee = self.employee
		stock_entry.posting_date = nowdate()
		stock_entry.set_posting_time = 1
		
		# Add custom field for loaded type if exists
		if hasattr(stock_entry, 'custom_wastedge_type'):
			stock_entry.custom_wastedge_type = "Loaded"
		
		# Add reference to wastedge
		if hasattr(stock_entry, 'custom_wastedge_reference'):
			stock_entry.custom_wastedge_reference = self.name
		
		# Get packed items from invoice
		packed_items = frappe.get_all(
			"Packed Item",
			filters={"parent": self.sales_invoice},
			fields=["item_code", "qty", "warehouse", "uom"]
		)
		
		# Add packed items to stock entry (negative qty for return/loaded)
		for packed_item in packed_items:
			is_stock_item = frappe.db.get_value("Item", packed_item.item_code, "is_stock_item")
			if is_stock_item:
				item_warehouse = packed_item.warehouse or source_invoice.items[0].warehouse
				stock_entry.append("items", {
					"item_code": packed_item.item_code,
					"qty": flt(packed_item.qty),
					"s_warehouse": item_warehouse,
					"uom": packed_item.uom or frappe.db.get_value("Item", packed_item.item_code, "stock_uom"),
				})
		
		# Add regular items that are stock items (negative qty for return/loaded)
		for item in source_invoice.items:
			is_stock_item = frappe.db.get_value("Item", item.item_code, "is_stock_item")
			if is_stock_item:
				item_warehouse = item.warehouse or warehouse
				stock_entry.append("items", {
					"item_code": item.item_code,
					"qty": flt(item.qty),
					"s_warehouse": item.warehouse,
					"uom": item.uom,
				})
		
		if not stock_entry.items:
			frappe.throw(_("No stock items found in the invoice"))
		
		stock_entry.insert()
		stock_entry.submit()
		
		# Link stock entry to wastedge
		
		return stock_entry.name
	
	def cancel_linked_documents(self):
		"""Cancel linked return invoice and stock entry on wastedge cancellation."""
		# Cancel stock entry first
		if self.get("stock_entry"):
			stock_entry = frappe.get_doc("Stock Entry", self.stock_entry)
			if stock_entry.docstatus == 1:
				stock_entry.cancel()
		
		# Cancel return invoice
		if self.get("return_invoice"):
			return_invoice = frappe.get_doc("Sales Invoice", self.return_invoice)
			if return_invoice.docstatus == 1:
				return_invoice.cancel()
