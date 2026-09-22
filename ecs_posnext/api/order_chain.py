# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""An order and the additions made to it.

Pressing "+" on an order does not extend its invoice — it creates a SEPARATE supplement
Sales Invoice linked back by `custom_parent_order` (see api/invoices.py). The customer,
the driver and the cashier all still see ONE order, so anything that asks "what is still
owed on this order?" has to ask about the whole chain, not the single invoice it happens
to hold a name for.

Answering that per-invoice is what left additions delivered but unpaid: the driver was
handed the original amount, and the cashier settling the order in All Orders could only
clear the invoice they had open.
"""

import frappe
from frappe import _
from frappe.utils import flt, fmt_money


def order_chain_root(invoice):
	"""The original order an invoice belongs to (itself, if it is the original)."""
	if not invoice:
		return None
	return frappe.db.get_value("Sales Invoice", invoice, "custom_parent_order") or invoice


def chain_invoices_with_outstanding(invoice):
	"""The order and every addition to it that still owes money, oldest first.

	Only invoices of the same customer and company are chained, so a mis-linked
	supplement can never drag an unrelated debt into someone's collection.
	"""
	root = order_chain_root(invoice)
	if not root:
		return []
	base = frappe.db.get_value(
		"Sales Invoice", root, ["customer", "company", "outstanding_amount", "docstatus"], as_dict=True
	)
	if not base:
		return []

	rows = []
	if base.docstatus == 1 and flt(base.outstanding_amount) > 0:
		rows.append(frappe._dict({"name": root, "outstanding": flt(base.outstanding_amount)}))

	for r in frappe.get_all(
		"Sales Invoice",
		filters={
			"custom_parent_order": root,
			"docstatus": 1,
			"is_return": 0,
			"customer": base.customer,
			"company": base.company,
			"outstanding_amount": [">", 0],
		},
		fields=["name", "outstanding_amount"],
		order_by="creation",
	):
		if r.name != root:
			rows.append(frappe._dict({"name": r.name, "outstanding": flt(r.outstanding_amount)}))
	return rows


def chain_outstanding(invoice):
	"""Total still owed on an order including every addition to it."""
	return flt(sum(r.outstanding for r in chain_invoices_with_outstanding(invoice)))


def allocate_across_chain(invoice, amount):
	"""Split `amount` over the chain, oldest invoice first.

	Returns [(invoice_name, allocated), ...]; anything beyond what the chain owes is left
	out, so a caller never over-allocates.
	"""
	allocations = []
	left = flt(amount)
	for row in chain_invoices_with_outstanding(invoice):
		if left <= 0:
			break
		take = min(left, row.outstanding)
		if take <= 0:
			continue
		allocations.append((row.name, flt(take)))
		left -= take
	return allocations


def _has_live_assignment(invoice, exclude=None):
	"""True when another delivery assignment is already out collecting this invoice."""
	name = frappe.db.get_value(
		"Delivery Assignment",
		{
			"order_reference": invoice,
			"order_doctype": "Sales Invoice",
			"status": ["in", ["Assigned", "Picked Up", "Out for Delivery"]],
			"docstatus": ["!=", 2],
		},
		"name",
	)
	return bool(name and name != exclude)


def collectible_for_assignment(invoice, exclude_assignment=None):
	"""What ONE delivery assignment should collect for an order.

	An addition sometimes gets an assignment of its own — it existed before the order went
	out, so the board raised it as its own card. Handing the whole chain to every
	assignment then bills the same money on each: an 820 order with a 200 addition showed
	1,020 on both cards and the dispatcher's total read 2,040.

	So the ORDER's assignment carries the chain minus whatever another live assignment is
	already covering, and an ADDITION's assignment carries only itself.
	"""
	root = order_chain_root(invoice)
	if invoice != root:
		return flt(frappe.db.get_value("Sales Invoice", invoice, "outstanding_amount"))

	total = 0.0
	for row in chain_invoices_with_outstanding(root):
		if row.name != invoice and _has_live_assignment(row.name, exclude_assignment):
			continue
		total += flt(row.outstanding)
	return flt(total)


def sync_delivery_collection_on_addition(doc, method=None):
	"""doc_event on Sales Invoice.on_submit — keep a driver's collection amount whole.

	An addition is a separate invoice, so the Delivery Assignment already out with a driver
	still shows what the ORIGINAL order cost. Refreshing it here rather than from the KDS
	merge path matters: that path runs only when the parent still has an active kitchen
	ticket, so additions to orders the kitchen had already finished — or never handled —
	left the driver collecting too little, with no sign anything was missing.
	"""
	root = doc.get("custom_parent_order")
	if not root:
		return

	assignment = frappe.db.get_value(
		"Delivery Assignment",
		{
			"order_reference": root,
			"order_doctype": "Sales Invoice",
			"status": ["in", ["Assigned", "Picked Up", "Out for Delivery"]],
			"docstatus": ["!=", 2],
		},
		["name", "payment_mode", "amount_to_collect"],
		as_dict=True,
	)
	if not assignment:
		return

	due = collectible_for_assignment(root, exclude_assignment=assignment.name)
	updates = {"amount_to_collect": due}
	# An addition to a prepaid order creates money that must now be collected on delivery.
	# Leaving the assignment "Prepaid" would tell the driver to collect nothing at all.
	if due > 0 and assignment.payment_mode != "Cash (COD)":
		updates["payment_mode"] = "Cash (COD)"

	frappe.db.set_value("Delivery Assignment", assignment.name, updates)
	frappe.publish_realtime(
		"dispatch_desk_refresh",
		{"source": "addition", "assignment": assignment.name, "action": "collection_amount_updated"},
		after_commit=True,
	)


def live_additions(root):
	"""Additions to an order that still stand — submitted, not cancelled, not returned."""
	rows = []
	for a in frappe.get_all(
		"Sales Invoice",
		filters={"custom_parent_order": root, "docstatus": 1, "is_return": 0},
		fields=["name", "custom_number_order", "grand_total", "outstanding_amount"],
		order_by="creation",
	):
		if a.name == root:
			continue
		if frappe.db.exists(
			"Sales Invoice", {"return_against": a.name, "docstatus": 1, "is_return": 1}
		):
			continue
		rows.append(a)
	return rows


def _returns_whole_order(doc, original):
	"""True when this return, together with any earlier ones, sends back every item."""
	prior = flt(
		frappe.db.sql(
			"""
			SELECT IFNULL(SUM(ABS(ri.qty)), 0)
			FROM `tabSales Invoice Item` ri
			JOIN `tabSales Invoice` r ON r.name = ri.parent
			WHERE r.return_against = %s AND r.docstatus = 1 AND r.is_return = 1 AND r.name != %s
			""",
			(original.name, doc.name or ""),
		)[0][0]
	)
	this_return = sum(abs(flt(i.qty)) for i in doc.get("items") or [])
	ordered = sum(abs(flt(i.qty)) for i in original.get("items") or [])
	if ordered <= 0:
		return True
	return (prior + this_return) >= ordered - 0.001


def return_additions_with_order(doc, method=None):
	"""doc_event on Sales Invoice.on_submit — a whole-order return takes its additions with it.

	Pressing "+" on an order bills the extra items on a SEPARATE supplement invoice, and
	every return path works on one invoice at a time with no knowledge of that link. So
	returning the original left its additions standing: the customer was refunded and the
	items came back, while the addition stayed billed as revenue and its stock stayed
	consumed. Three of the five orders this happened to were only put right because someone
	remembered to return the addition by hand; two were never caught.

	A PARTIAL return is left alone — keeping an addition while sending back part of the
	order is a real thing a customer asks for. Only a return that sends back the whole
	order carries its additions with it.

	Runs after the order's own return is submitted, and throws on failure so a half-done
	chain rolls back with it rather than leaving the customer refunded for part of an order.
	"""
	if not doc.get("is_return") or not doc.get("return_against"):
		return
	if doc.flags.get("ignore_addition_return_guard"):
		return

	original = frappe.get_doc("Sales Invoice", doc.return_against)
	root = order_chain_root(original.name)
	if original.name != root:
		return  # an addition is being returned on its own — nothing follows it
	if not _returns_whole_order(doc, original):
		return

	pending = live_additions(root)
	if not pending:
		return

	from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return

	from ecs_posnext.api.business_day import log_pos_event

	created = []
	for addition in pending:
		try:
			ret = make_sales_return(addition.name)
			# Book the credit note AGAINST THE ADDITION, the way every POS return is
			# created (submit_invoice does the same). Left at ERPNext's default of 1 the
			# note settles against itself: the addition stays Unpaid for its full amount
			# while the credit note carries the negative balance beside it, so a returned
			# order still shows money owed.
			ret.update_outstanding_for_self = 0
			# Stamp the shift doing the return, not the one that sold the addition: the
			# refund leaves TODAY's drawer, so that is the shift whose cash it must move.
			for field in ("posa_pos_opening_shift", "custom_pos_business_day", "custom_pos_cashier_shift"):
				if ret.meta.has_field(field) and doc.get(field):
					ret.set(field, doc.get(field))
			ret.flags.ignore_permissions = True
			ret.flags.ignore_addition_return_guard = True  # stops this hook recursing
			ret.insert(ignore_permissions=True)
			ret.submit()
			created.append((addition, ret.name))
			log_pos_event(
				action="Return",
				reference_doctype="Sales Invoice",
				reference_name=ret.name,
				pos_profile=doc.get("pos_profile"),
				pos_business_day=doc.get("custom_pos_business_day"),
				old_value=addition.name,
				new_value=ret.name,
				reason=_("Addition {0} returned automatically with order {1} (return {2}).").format(
					addition.custom_number_order or addition.name, root, doc.name
				),
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Addition Return Failed")
			frappe.throw(
				_(
					"The order was returned but its addition {0} ({1}) could not be returned with"
					" it, so nothing was saved. Return the addition on its own first, then retry."
				).format(addition.custom_number_order or addition.name, addition.name),
				title=_("Addition Return Failed"),
			)

	if created:
		lines = "".join(
			"<li><b>{0}</b> — {1} &rarr; {2}</li>".format(
				a.custom_number_order or a.name, fmt_money(flt(a.grand_total)), ret_name
			)
			for a, ret_name in created
		)
		frappe.msgprint(
			_("The additions on this order were returned with it:<ul>{0}</ul>").format(lines),
			title=_("Additions Returned"),
			indicator="orange",
		)
