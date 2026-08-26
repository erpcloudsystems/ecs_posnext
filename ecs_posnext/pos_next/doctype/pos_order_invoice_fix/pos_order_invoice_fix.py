# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt

import random
import string

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, flt, getdate, nowdate
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file


def _new_savepoint():
	name = "".join(random.choices(string.ascii_lowercase, k=12))
	frappe.db.savepoint(name)
	return name


def _release_savepoint(save_point):
	try:
		frappe.db.release_savepoint(save_point)
	except Exception:
		# Some doc_events hooks in this bench (e.g. ecs_vim's
		# enable_customer_if_exists, wired to Sales Invoice's before_insert)
		# call frappe.db.commit() unconditionally, which silently invalidates
		# any open savepoint. That's harmless here - there is nothing left to
		# release, the row's work is already durably committed.
		pass


def _rollback_to_savepoint(save_point):
	try:
		frappe.db.rollback(save_point=save_point)
	except Exception:
		# Savepoint already gone (see _release_savepoint) - fall back to a
		# plain rollback so whatever happened since the last real commit is
		# still undone.
		frappe.db.rollback()


class POSOrderInvoiceFix(Document):
	def _update_counts(self):
		self.total_orders = len(self.orders)
		self.pending_orders = len([r for r in self.orders if r.status == "Pending"])
		self.invoiced_orders = len([r for r in self.orders if r.status == "Invoice Created"])
		self.submitted_orders = len([r for r in self.orders if r.status == "Submitted"])
		self.reconciliation_orders = len(
			[r for r in self.orders if r.status == "Needs Payment Reconciliation"]
		)
		self.failed_orders = len([r for r in self.orders if r.status == "Failed"])
		self.skipped_orders = len([r for r in self.orders if r.status == "Skipped"])

	@frappe.whitelist()
	def import_orders(self):
		if not self.attach_file:
			frappe.throw(_("Please upload an Excel file first."))

		rows = read_xlsx_file_from_attached_file(file_url=self.attach_file)
		if not rows:
			frappe.throw(_("The uploaded file is empty."))

		header = [cstr(c).strip().lower() for c in rows[0]]

		def col_index(*names):
			for n in names:
				if n in header:
					return header.index(n)
			return None

		idx_id = col_index("id", "sales order", "order id", "so")
		idx_customer = col_index("customer")
		idx_date = col_index("date", "transaction date")

		if idx_id is None:
			frappe.throw(_("Could not find an 'ID' column in the uploaded file."))

		existing = {row.sales_order for row in self.orders if row.sales_order}
		added = 0
		skipped_duplicate = 0

		for raw in rows[1:]:
			if idx_id >= len(raw):
				continue
			so_name = cstr(raw[idx_id]).strip()
			if not so_name:
				continue
			if so_name in existing:
				skipped_duplicate += 1
				continue

			row = self.append("orders", {})
			row.sales_order = so_name
			existing.add(so_name)
			added += 1

			if not frappe.db.exists("Sales Order", so_name):
				row.status = "Failed"
				row.remarks = _("Sales Order not found")
				continue

			so = frappe.get_doc("Sales Order", so_name)

			if so.docstatus == 2:
				row.status = "Failed"
				row.remarks = _("Sales Order is cancelled")
				continue
			if so.docstatus == 0:
				row.status = "Failed"
				row.remarks = _("Sales Order is still a draft")
				continue

			if so.get("custom_sales_invoice"):
				row.status = "Skipped"
				row.sales_invoice = so.custom_sales_invoice
				row.remarks = _("Already linked to an invoice")
				continue

			# customer: prefer the Excel value, fall back to the Sales Order's own customer
			customer = None
			if idx_customer is not None and idx_customer < len(raw) and cstr(raw[idx_customer]).strip():
				candidate = cstr(raw[idx_customer]).strip()
				if frappe.db.exists("Customer", candidate):
					customer = candidate
			if not customer:
				customer = so.customer
			row.customer = customer
			row.customer_name = (
				frappe.db.get_value("Customer", customer, "customer_name") or so.customer_name
			)

			# date: prefer the Excel value, fall back to the Sales Order's transaction date
			txn_date = None
			if idx_date is not None and idx_date < len(raw) and raw[idx_date]:
				try:
					txn_date = getdate(raw[idx_date])
				except Exception:
					txn_date = None
			row.transaction_date = txn_date or so.transaction_date

			# pos profile: only the Sales Order's own pos_profile (free text field),
			# if it resolves to a real POS Profile - no fallback. Without one we
			# can't fetch the profile's fields (accounts, update_stock, payment
			# methods), so fail the row instead of guessing.
			if not so.get("pos_profile") or not frappe.db.exists("POS Profile", so.pos_profile):
				row.status = "Failed"
				row.remarks = _("Sales Order has no POS Profile set")
				continue
			row.pos_profile = so.pos_profile

			row.grand_total = so.grand_total

			# look for an existing advance Payment Entry already allocated against this Sales Order
			pe_refs = frappe.get_all(
				"Payment Entry Reference",
				filters={
					"reference_doctype": "Sales Order",
					"reference_name": so.name,
					"docstatus": 1,
				},
				fields=["parent", "allocated_amount"],
			)
			if pe_refs:
				pe_names = list({d.parent for d in pe_refs})
				pe_docs = frappe.get_all(
					"Payment Entry",
					filters={"name": ["in", pe_names], "docstatus": 1},
					fields=["name", "mode_of_payment"],
				)
				mop_map = {d.name: d.mode_of_payment for d in pe_docs}
				modes = {mop_map.get(d.parent) for d in pe_refs if mop_map.get(d.parent)}
				# store every Payment Entry that has an allocation against this Sales
				# Order (comma-separated) - there can be more than one - so submit_invoices
				# can unlink each of them, not just the first
				row.advance_payment_entry = ", ".join(pe_names)
				row.mode_of_payment = list(modes)[0] if len(modes) == 1 else None
				row.paid_amount = sum(flt(d.allocated_amount) for d in pe_refs)
			else:
				# no advance on file: treat the order as fully paid at the counter
				row.paid_amount = so.grand_total

			if not row.mode_of_payment:
				row.mode_of_payment = frappe.db.get_value(
					"POS Profile", row.pos_profile, "posa_cash_mode_of_payment"
				)

			row.status = "Pending"

		self._update_counts()
		self.log = _("Imported {0} new row(s). Skipped {1} duplicate row(s) already in the table.").format(
			added, skipped_duplicate
		)
		self.save()
		return self.log

	@frappe.whitelist()
	def create_invoices(self):
		from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

		processed, skipped, failed = 0, 0, 0
		error_lines = []

		for row in self.orders:
			if row.status != "Pending":
				continue

			sp = _new_savepoint()
			try:
				so = frappe.get_doc("Sales Order", row.sales_order)

				if so.docstatus != 1:
					frappe.throw(_("Sales Order is not submitted"))

				if so.get("custom_sales_invoice"):
					row.status = "Skipped"
					row.sales_invoice = so.custom_sales_invoice
					row.remarks = _("Already linked to an invoice")
					skipped += 1
					_release_savepoint(sp)
					continue

				if not row.pos_profile:
					frappe.throw(_("No POS Profile resolved for this row"))

				pos_profile_doc = frappe.get_cached_doc("POS Profile", row.pos_profile)

				si = make_sales_invoice(so.name, ignore_permissions=True)
				si.is_pos = 1
				si.pos_profile = row.pos_profile

				# make_sales_invoice() may have auto-pulled this customer's OTHER,
				# unrelated unallocated advances (from unconnected past sales) into
				# this invoice's Advances table if the Sales Order had "Allocate
				# Advances Automatically" checked. This tool only ever wants to
				# reconcile the one specific advance tied to THIS Sales Order
				# (handled explicitly in submit_invoices), so drop anything it
				# picked up on its own.
				si.set("advances", [])
				si.allocate_advances_automatically = 0

				if row.customer and row.customer != si.customer:
					from erpnext.accounts.party import get_party_account

					si.customer = row.customer
					si.debit_to = get_party_account("Customer", si.customer, si.company)

				si.posting_date = nowdate()

				# pulls in the rest of the POS Profile's fields (price list, accounts,
				# update_stock, tax settings, item defaults, available payment modes...)
				si.set_missing_values()

				# For some POS Profiles, the payment rows set_missing_values() just
				# added come back with amount=None rather than 0 - ERPNext's own
				# verify_payment_amount_is_positive()/set_paid_amount() assume a
				# number and crash (TypeError) on None. Normalize defensively.
				for p in si.payments:
					if p.amount is None:
						p.amount = 0

				# Run a full validate pass now (not just calculate_taxes_and_totals) so
				# that validate-time hooks which can shift grand_total - e.g. ecs_posnext's
				# apply_tax_inclusive(), which flips inclusive/exclusive VAT based on POS
				# Settings - have already settled the total BEFORE we size the payment
				# amount below. Sizing it off a pre-hook total would leave the invoice
				# over/under-paid once insert() runs validate() again for real.
				si.flags.ignore_permissions = True
				si.run_method("validate")

				# The sale itself didn't change, only its document type - the invoice
				# must charge the customer exactly what the Sales Order already showed.
				# A mismatch here (seen when a POS Profile's POS Settings Tax Inclusive
				# value disagrees with how the order was actually taxed at the time of
				# sale) means apply_tax_inclusive() added or removed VAT on top of the
				# original amount. Absorb the difference via the discount amount and
				# re-validate - the same "converge on the real total" approach
				# ecs_posnext's own invoice flow uses for post-validation rounding
				# corrections - rather than silently over/under-charging the customer.
				correction_note = ""
				original_discount_amount = flt(si.discount_amount)
				for _attempt in range(5):
					diff = flt(si.grand_total) - flt(so.grand_total)
					if abs(diff) <= 0.02:
						break
					si.discount_amount = flt(si.discount_amount) + diff
					si.run_method("validate")
				else:
					diff = flt(si.grand_total) - flt(so.grand_total)

				# Flag it whenever a correction actually happened, not just when the
				# final residual is still large - a sizeable discount_amount with no
				# explanation on the invoice would be confusing even if it did land
				# within tolerance.
				if flt(si.discount_amount) != original_discount_amount:
					correction_note = _(
						"Applied a {0} discount adjustment to correct a Tax Inclusive "
						"mismatch between POS Profile {1} and the original Sales Order. "
					).format(si.discount_amount, row.pos_profile)

				if abs(flt(si.grand_total) - flt(so.grand_total)) > 0.5:
					frappe.throw(
						_(
							"After applying POS Profile {0}, the invoice total ({1}) could "
							"not be reconciled with the Sales Order total ({2}). Check the "
							"Tax Inclusive setting in POS Settings for this profile."
						).format(row.pos_profile, si.grand_total, so.grand_total)
					)

				if flt(si.grand_total) > 0:
					target_mode = row.mode_of_payment or pos_profile_doc.posa_cash_mode_of_payment
					if not target_mode:
						default_rows = [p for p in si.payments if cint(p.default)]
						if default_rows:
							target_mode = default_rows[0].mode_of_payment
						elif si.payments:
							target_mode = si.payments[0].mode_of_payment

					if not target_mode:
						frappe.throw(
							_(
								"No mode of payment could be determined. Set a Cash Mode of "
								"Payment on POS Profile {0}."
							).format(row.pos_profile)
						)

					# If this Sales Order already has a real advance Payment Entry, the
					# cash was already received and posted to GL once. Do NOT also feed
					# it through the invoice's own Payments table - ecs_posnext auto-
					# creates a brand new Payment Entry on submit from that table, which
					# would double-count the cash. Leave the row at 0 (still satisfies
					# ERPNext's "at least one payment row" rule) and reconcile the real,
					# pre-existing Payment Entry against this invoice separately - see
					# submit_invoices().
					# Pay the invoice's own final grand_total (not the Sales Order's
					# original amount) - the discount correction above can leave a tiny
					# residual between the two, and paying off THIS invoice's actual
					# total is what makes it come out fully Paid instead of Partly Paid
					# by a few cents.
					amount = 0 if row.advance_payment_entry else flt(si.grand_total)
					matched = next(
						(p for p in si.payments if p.mode_of_payment == target_mode), None
					)
					if matched:
						matched.amount = amount
					else:
						si.append("payments", {"mode_of_payment": target_mode, "amount": amount})

				si.insert(ignore_permissions=True)

				so.db_set("custom_sales_invoice", si.name, update_modified=False)

				row.sales_invoice = si.name
				row.status = "Invoice Created"
				row.remarks = correction_note + (
					_(
						"Draft created unpaid on purpose - existing Payment Entry {0} will be "
						"reconciled after submit."
					).format(row.advance_payment_entry)
					if row.advance_payment_entry
					else ""
				)
				processed += 1
				_release_savepoint(sp)
			except Exception as e:
				_rollback_to_savepoint(sp)
				row.status = "Failed"
				row.remarks = cstr(e)[:250]
				failed += 1
				error_lines.append(f"{row.sales_order}: {e}")
				frappe.log_error(
					title="POS Order Invoice Fix - create_invoices",
					message=frappe.get_traceback(),
				)

		self._update_counts()
		self.log = _("Created {0} invoice(s). {1} skipped. {2} failed.").format(
			processed, skipped, failed
		)
		if error_lines:
			self.log += "\n" + "\n".join(error_lines)
		self.save(ignore_permissions=True)
		return self.log

	@frappe.whitelist()
	def submit_invoices(self):
		from erpnext.accounts.utils import unlink_ref_doc_from_payment_entries

		processed, failed = 0, 0
		error_lines = []

		for row in self.orders:
			if row.status != "Invoice Created":
				continue

			sp = _new_savepoint()
			try:
				if not row.sales_invoice:
					frappe.throw(_("No Sales Invoice linked to this row"))

				si = frappe.get_doc("Sales Invoice", row.sales_invoice)

				if si.docstatus == 1:
					row.status = "Submitted"
					_release_savepoint(sp)
					continue

				si.submit()

				if row.advance_payment_entry:
					# This order already had one or more real advance Payment Entries,
					# so the invoice was deliberately submitted with a zero-amount
					# payment row (see create_invoices) to avoid a second, duplicate
					# Payment Entry being auto-created. Release each of the old
					# allocations from the Sales Order so those Payment Entries are
					# free to be reconciled against this invoice instead - via the
					# Payment Reconciliation Tool, which handles the GL correctly.
					so = frappe.get_doc("Sales Order", row.sales_order)
					pe_names = [n.strip() for n in row.advance_payment_entry.split(",") if n.strip()]
					for pe_name in pe_names:
						unlink_ref_doc_from_payment_entries(ref_doc=so, payment_name=pe_name)
					row.status = "Needs Payment Reconciliation"
					row.remarks = _(
						"Submitted unpaid on purpose. Payment Entry(s) {0} were released "
						"from the Sales Order - reconcile them against this invoice via "
						"the Payment Reconciliation Tool."
					).format(row.advance_payment_entry)
				else:
					row.status = "Submitted"
					row.remarks = ""

				processed += 1
				_release_savepoint(sp)
			except Exception as e:
				_rollback_to_savepoint(sp)
				row.status = "Failed"
				row.remarks = cstr(e)[:250]
				failed += 1
				error_lines.append(f"{row.sales_order}: {e}")
				frappe.log_error(
					title="POS Order Invoice Fix - submit_invoices",
					message=frappe.get_traceback(),
				)

		self._update_counts()
		self.log = _("Submitted {0} invoice(s). {1} failed.").format(processed, failed)
		if error_lines:
			self.log += "\n" + "\n".join(error_lines)
		self.save(ignore_permissions=True)
		return self.log
