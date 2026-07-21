# -*- coding: utf-8 -*-
# Copyright (c) 2024, POS Next and contributors
# For license information, please see license.txt

"""Sales Order history for the POS "History" dialog.

Only surfaces Sales Orders that contain at least one item whose
Item.custom_item_type is a third-party billing type (aggregator-billed
orders, e.g. Prepaid/Post Paid Third Party). custom_item_type lives on
Item, not on Sales Order/Sales Order Item, so this requires a join that
frappe.client.get_list can't express via its plain filters dict.
"""

import frappe
from frappe.query_builder import Order
from frappe.utils import cint, cstr

from ecs_posnext.api.constants import THIRD_PARTY_ITEM_TYPES


@frappe.whitelist()
def get_third_party_sales_orders(company=None, search_term=None, start=0, page_length=20):
	"""List Sales Orders that include a third-party billed item.

	Args:
		company: Optional company filter.
		search_term: Optional search on order name or customer name.
		start: Pagination offset.
		page_length: Page size.

	Returns:
		List of dicts with the same shape as the previous frappe.client.get_list
		call (name, customer, customer_name, customer_mobile, transaction_date,
		grand_total, status, docstatus), ordered by most recently modified.
	"""
	so = frappe.qb.DocType("Sales Order")
	soi = frappe.qb.DocType("Sales Order Item")
	item = frappe.qb.DocType("Item")
	customer = frappe.qb.DocType("Customer")

	query = (
		frappe.qb.from_(so)
		.join(soi).on(soi.parent == so.name)
		.join(item).on(item.name == soi.item_code)
		.left_join(customer).on(customer.name == so.customer)
		.select(
			so.name,
			so.customer,
			so.customer_name,
			customer.mobile_no.as_("customer_mobile"),
			so.transaction_date,
			so.grand_total,
			so.status,
			so.docstatus,
		)
		.where(item.custom_item_type.isin(THIRD_PARTY_ITEM_TYPES))
		.groupby(so.name)
		.orderby(so.modified, order=Order.desc)
		.offset(cint(start))
		.limit(cint(page_length))
	)

	if company:
		query = query.where(so.company == company)

	if search_term:
		term = f"%{cstr(search_term)}%"
		query = query.where((so.name.like(term)) | (so.customer_name.like(term)))

	return query.run(as_dict=True)
