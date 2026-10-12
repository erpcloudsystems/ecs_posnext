# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
POS Sales Detail report

What the POS sold, by item, item group or room, and which shift sold it.

Reads Sales Orders, not Sales Invoices: this POS submits a Sales Order plus a
Material Issue Stock Entry for every sale, so a report built on invoices would
come back empty.

Employee sales say which kind they are - Cash, Loan or Benefits - and a Benefits
handout is reported as a quantity with no money against it, because staff welfare
is not revenue. A handout that the POS booked as a Material Issue alone, with no
Sales Order behind it, is read from that Stock Entry.

Amounts are net of tax and the tax is read off the Sales Order itself, never
recomputed here, so the report agrees with the order whether the POS profile
charges tax on top of the menu price or inside it. The summary also carries the
orders' grand total so a partly filtered report can be told apart at a glance
rather than a manager wondering why the report and the shift close disagree.
"""

import datetime

import frappe
from frappe import _
from frappe.utils import flt

# A staff handout is not revenue, so it is reported as a quantity with no money
# against it. The other two are ordinary sales that happen to be to an employee.
UNPRICED_SALE_TYPE = "Benefits"

# Which line fields each grouping collapses on. Values are filter values, not
# labels, so they stay stable when the report is translated.
#
# The room groupings collapse on `place`, not on the room: a sale with no room
# was sold at a table, and an Officer table and a Hospitality table are not the
# same business at all. Keying on the room would pile both into one blank row.
GROUP_KEYS = {
	"Item": ("item_code",),
	"Item Group": ("item_group",),
	"Room": ("place",),
	"Shift": ("shift",),
	"Item Group + Item": ("item_group", "item_code"),
	"Room + Item": ("place", "item_code"),
}

CHART_LIMIT = 12


def execute(filters=None):
	filters = frappe._dict(filters or {})
	group_by = filters.get("group_by") or "Item"

	lines = _fetch_lines(filters)
	data = lines if group_by == "Detail" else _group(lines, group_by)

	return (
		_columns(group_by, _currency(lines)),
		data,
		None,
		_chart(data, group_by),
		_summary(lines),
	)


def _has(doctype, fieldname):
	return frappe.get_meta(doctype).has_field(fieldname)


def _fetch_lines(filters):
	"""
	One row per sold item line, from both of the things a POS sale can leave.

	Most sales are a Sales Order. A staff handout is not: with stock issuing on,
	the POS books Benefits as a Material Issue and nothing else, so a report that
	read only Sales Orders would say the stock walked out by itself.
	"""
	lines = _order_lines(filters) + _employee_issue_lines(filters)
	lines.sort(key=lambda line: (line.get("date") or datetime.date.min), reverse=True)

	_set_place(lines)
	return lines


def _order_lines(filters):
	"""
	The sold lines of every POS Sales Order.

	A POS sale is recognised by the fields the POS writes on it - the shift it
	belongs to, or the Stock Entry it issued stock through. Without one of those
	a Sales Order is back-office paperwork, not a till sale, and does not belong
	in a POS report.
	"""
	if not _has("Sales Order", "posa_pos_opening_shift"):
		frappe.throw(
			_("This report needs the POS fields on Sales Order. Run {0} to add them.").format(
				"<code>bench --site &lt;site&gt; migrate</code>"
			)
		)

	markers = ["so.posa_pos_opening_shift IS NOT NULL"]
	if _has("Sales Order", "pos_stock_entry"):
		markers.append("so.pos_stock_entry IS NOT NULL")

	# Split checks can be charged room by room, so the line's own room wins where
	# it is set and the order's room is the fallback.
	room_expr = "so.room"
	if _has("Sales Order Item", "room"):
		room_expr = "COALESCE(soi.room, so.room)"
	if not _has("Sales Order", "room"):
		room_expr = "soi.room" if _has("Sales Order Item", "room") else "NULL"

	table_expr = _table_expr()
	conditions, values = _conditions(filters, room_expr, table_expr)

	lines = frappe.db.sql(
		"""
		SELECT
			so.transaction_date       AS date,
			so.name                   AS sales_order,
			so.posa_pos_opening_shift AS shift,
			os.user                   AS cashier,
			so.customer_name          AS customer_name,
			so.currency               AS currency,
			so.grand_total            AS order_total,
			so.net_total              AS order_net_total,
			so.total_taxes_and_charges AS order_tax,
			{room_expr}               AS room,
			{table_expr}              AS pos_table,
			{employee}                AS employee,
			{sale_type}               AS pos_sale_type,
			so.name                   AS voucher,
			soi.item_code, soi.item_name, soi.item_group,
			soi.qty, soi.uom,
			soi.amount                AS gross_amount,
			soi.net_amount            AS net_amount,
			{line_tax}                AS line_tax,
			EXISTS (
				SELECT 1 FROM `tabSales Taxes and Charges` stc
				WHERE stc.parenttype = 'Sales Order'
					AND stc.parent = so.name
					AND stc.included_in_print_rate = 1
			)                         AS tax_inclusive
		FROM `tabSales Order` so
		INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
		LEFT JOIN `tabPOS Opening Shift` os ON os.name = so.posa_pos_opening_shift
		{table_joins}
		WHERE so.docstatus = 1
			AND ({markers})
			{conditions}
		ORDER BY so.transaction_date DESC, so.creation DESC, soi.idx ASC
		""".format(
			room_expr=room_expr,
			table_expr=table_expr,
			table_joins=_table_joins(),
			employee=_optional("Sales Order", "employee", "so.employee"),
			sale_type=_optional("Sales Order", "pos_sale_type", "so.pos_sale_type"),
			line_tax=_line_tax_expr(),
			markers=" OR ".join(markers),
			conditions="".join(conditions),
		),
		values,
		as_dict=True,
	)

	_set_tax(lines)
	_hide_unpriced(lines)
	return lines


def _optional(doctype, fieldname, expr):
	"""`expr` where the site has that field, NULL where it does not."""
	return expr if _has(doctype, fieldname) else "NULL"


def _employee_issue_lines(filters):
	"""
	The sold lines of every employee issue the POS booked without a Sales Order.

	A Benefits handout with stock issuing on is a Material Issue and nothing more,
	so it is read here or not at all. An issue that does have a Sales Order - the
	Cash and Loan flows write both and cross-link them - is left out, because the
	order already reports it and counting both would sell the same water twice.

	A Material Issue records what left the store, not what anybody paid, so the
	money is priced back on from the POS Profile that issued it. Benefits stay
	unpriced, because a handout has no price to recover.
	"""
	if not _has("Stock Entry", "pos_sale_type"):
		return []

	# Filters this source cannot answer. A Material Issue has no customer, no POS
	# profile and no shift, so a report narrowed to one of those is asking for
	# till sales and an employee issue is not one.
	if any(filters.get(key) for key in ("customer", "pos_profile", "pos_opening_shift", "pos_table")):
		return []

	conditions, values = _issue_conditions(filters)

	lines = frappe.db.sql(
		"""
		SELECT
			se.posting_date  AS date,
			se.name          AS voucher,
			se.name          AS stock_entry,
			se.owner         AS cashier,
			se.company       AS company,
			{room}           AS room,
			{employee}       AS employee,
			se.pos_sale_type AS pos_sale_type,
			sed.item_code, sed.item_name, sed.item_group,
			sed.qty, sed.uom, sed.s_warehouse AS warehouse
		FROM `tabStock Entry` se
		INNER JOIN `tabStock Entry Detail` sed ON sed.parent = se.name
		WHERE se.docstatus = 1
			AND IFNULL(se.pos_sale_type, '') != ''
			AND {unlinked}
			{conditions}
		ORDER BY se.posting_date DESC, se.creation DESC, sed.idx ASC
		""".format(
			room=_optional("Stock Entry", "room", "se.room"),
			employee=_optional("Stock Entry", "employee", "se.employee"),
			unlinked=_unlinked_issue_expr(),
			conditions="".join(conditions),
		),
		values,
		as_dict=True,
	)

	for line in lines:
		line.sales_order = None
		line.order_total = 0.0

	_price_employee_issues(lines)
	_hide_unpriced(lines)

	return lines


def _unlinked_issue_expr():
	"""True for a Material Issue that no Sales Order reports."""
	tests = []
	if _has("Stock Entry", "pos_sales_order"):
		tests.append("IFNULL(se.pos_sales_order, '') = ''")
	if _has("Sales Order", "pos_stock_entry"):
		tests.append(
			"NOT EXISTS (SELECT 1 FROM `tabSales Order` so2 WHERE so2.pos_stock_entry = se.name)"
		)
	return " AND ".join(tests) or "1 = 1"


def _issue_conditions(filters):
	"""The filters a Material Issue can answer, as SQL fragments and values."""
	conditions = []
	values = {}

	simple = {
		"company": "se.company",
		"item_group": "sed.item_group",
		"item_code": "sed.item_code",
		"cashier": "se.owner",
		"pos_sale_type": "se.pos_sale_type",
	}
	if _has("Stock Entry", "room"):
		simple["room"] = "se.room"
	if _has("Stock Entry", "employee"):
		simple["employee"] = "se.employee"

	for key, column in simple.items():
		if filters.get(key):
			conditions.append(f" AND {column} = %({key})s")
			values[key] = filters.get(key)

	# A room filter the Stock Entry cannot answer must exclude it, not ignore it
	if filters.get("room") and "room" not in simple:
		conditions.append(" AND 1 = 0")
	if filters.get("employee") and "employee" not in simple:
		conditions.append(" AND 1 = 0")

	if filters.get("from_date"):
		conditions.append(" AND se.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append(" AND se.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	return conditions, values


def _price_employee_issues(lines):
	"""
	Price an employee issue at what the POS would have charged for it.

	A Cash sale was paid for and a Loan is owed, so both have a price; only a
	Benefits handout does not. But a Material Issue stores no price - it values
	stock at cost, which is not what an employee paid - so the price is recovered
	from the same configuration the POS priced the cart with: the profile that
	issued the stock, its selling price list, and its tax setting.

	The profile is found by the warehouse the stock left, which is the profile's
	own warehouse - that is where the POS took it from when it built the issue.

	A line whose item has no price on that list keeps empty money columns rather
	than a made-up figure.
	"""
	# Start every line unpriced, so one whose item has no list price ends up with
	# empty money columns rather than with no columns at all.
	_hide_unpriced(lines, every_line=True)

	priceable = [
		line for line in lines
		if line.get("pos_sale_type") != UNPRICED_SALE_TYPE and line.get("item_code")
	]
	for line in priceable:
		profile = _issuing_profile(line.get("warehouse"), line.get("company"))
		rate = _selling_rate(line, profile)
		line.currency = (profile or {}).get("currency") or _company_currency(line)

		if rate is None:
			continue

		qty = flt(line.get("qty"))
		tax_rate = flt((profile or {}).get("tax_rate"))
		if (profile or {}).get("tax_inclusive"):
			gross = flt(rate * qty, 2)
			net = flt(gross / (1 + tax_rate / 100), 2) if tax_rate else gross
		else:
			net = flt(rate * qty, 2)
			gross = flt(net * (1 + tax_rate / 100), 2) if tax_rate else net

		line.amount = net
		line.tax_amount = flt(gross - net, 2)
		line.amount_with_tax = gross
		line.rate = flt(net / qty, 2) if qty else 0.0
		line.rate_with_tax = flt(gross / qty, 2) if qty else 0.0

	for line in lines:
		if not line.get("currency"):
			line.currency = _company_currency(line)


def _issuing_profile(warehouse, company):
	"""
	The POS Profile that issued stock from this warehouse, and how it prices.

	Returns None where no single profile owns the warehouse: two profiles selling
	out of one store cannot be told apart from the issue alone, and guessing which
	price list applied would put a number in a financial report that nothing backs.
	"""
	if not warehouse:
		return None

	cache = frappe.flags.setdefault("pos_sales_detail_profiles", {})
	key = (warehouse, company)
	if key in cache:
		return cache[key]

	filters = {"warehouse": warehouse}
	if company:
		filters["company"] = company
	names = frappe.get_all("POS Profile", filters=filters, pluck="name")

	profile = None
	if len(names) == 1:
		doc = frappe.get_cached_doc("POS Profile", names[0])
		profile = frappe._dict(
			name=doc.name,
			price_list=doc.get("selling_price_list"),
			currency=doc.get("currency"),
			tax_rate=_template_tax_rate(doc.get("taxes_and_charges")),
			tax_inclusive=frappe.db.get_value(
				"POS Settings", {"pos_profile": doc.name}, "tax_inclusive"
			),
		)

	cache[key] = profile
	return profile


def _template_tax_rate(template):
	"""The percentage a Sales Taxes and Charges Template charges on the net total."""
	if not template:
		return 0.0

	return sum(
		flt(row.rate)
		for row in frappe.get_all(
			"Sales Taxes and Charges",
			filters={
				"parent": template,
				"parenttype": "Sales Taxes and Charges Template",
				"charge_type": "On Net Total",
			},
			fields=["rate"],
		)
	)


def _selling_rate(line, profile):
	"""
	The list price for this item, in the unit it was issued in.

	A price quoted for the issued unit wins; a price with no unit against it is
	the item's own rate and is the fallback. Prices that had not started or had
	already expired on the day of the issue are ignored, the same way the POS
	would have ignored them.
	"""
	price_list = (profile or {}).get("price_list") or frappe.db.get_single_value(
		"Selling Settings", "selling_price_list"
	)
	if not price_list:
		return None

	cache = frappe.flags.setdefault("pos_sales_detail_prices", {})
	key = (price_list, line.get("item_code"))
	if key not in cache:
		cache[key] = frappe.get_all(
			"Item Price",
			filters={"price_list": price_list, "item_code": line.get("item_code"), "selling": 1},
			fields=["uom", "price_list_rate", "valid_from", "valid_upto"],
		)

	on = line.get("date")
	usable = [
		row for row in cache[key]
		if not on or ((not row.valid_from or row.valid_from <= on) and (not row.valid_upto or row.valid_upto >= on))
	]

	for row in usable:
		if row.uom and row.uom == line.get("uom"):
			return flt(row.price_list_rate)
	for row in usable:
		if not row.uom:
			return flt(row.price_list_rate)
	return None


def _company_currency(line):
	company = line.get("company") or frappe.defaults.get_user_default("Company")
	return frappe.get_cached_value("Company", company, "default_currency") if company else None


def _hide_unpriced(lines, every_line=False):
	"""
	Blank the money on a line that nobody paid for.

	A Benefits handout is staff welfare, not a sale: reporting a price against it
	would put a number in the revenue columns that never reached the drawer. The
	quantity is what there is to report, so the money columns are emptied rather
	than zeroed - an empty cell says "no price", a 0.00 says "sold for nothing".

	An employee issue read off a Material Issue has no price at all, whatever its
	type, because a stock movement does not record one.
	"""
	for line in lines:
		if every_line or line.get("pos_sale_type") == UNPRICED_SALE_TYPE:
			for field in ("rate", "rate_with_tax", "amount", "tax_amount", "amount_with_tax"):
				line[field] = None


def _table_joins():
	"""
	Reach the table a sale was served at, through whichever link the POS wrote.

	A check opened on a table is settled against its session; a check split off
	one carries its own table order. Both are followed so a split check is still
	attributed to the table it was served at rather than falling back to walk-in.
	"""
	joins = []
	if _has("Sales Order", "pos_table_session"):
		joins.append(
			"LEFT JOIN `tabPOS Table Session` pts ON pts.name = so.pos_table_session"
		)
	if _has("Sales Order", "pos_table_order"):
		joins.append("LEFT JOIN `tabPOS Table Order` pto ON pto.name = so.pos_table_order")
	return "\n\t\t".join(joins)


def _table_expr():
	"""The table a sale was served at, or NULL where the POS records no table."""
	sources = []
	if _has("Sales Order", "pos_table_order"):
		sources.append("pto.`table`")
	if _has("Sales Order", "pos_table_session"):
		sources.append("pts.`table`")

	if not sources:
		return "NULL"
	return sources[0] if len(sources) == 1 else "COALESCE({0})".format(", ".join(sources))


def _set_place(lines):
	"""
	Say where each sale went, in one column a manager can group on.

	A sale charged to a room is the room. An employee sale says so and says which
	kind, because Cash, Loan and Benefits are three different things: one is paid
	now, one is owed, one is never paid at all. Everything else was served at a
	table, and the table is the answer worth reading: "Officer" and "Hospitality"
	are different business, not two anonymous walk-ins. Only a sale with none of
	those - rung up straight at the till - is left as a walk-in.

	The sale type is part of this value rather than a column beside it so that it
	is also part of the grouping key, which is what keeps an unpriced Benefits
	handout out of a row that reports revenue.

	Numbered tables are prefixed so a table 1 is not mistaken for a room 1; named
	ones like Officer are left as they are, because "Table Officer" reads as
	nonsense.
	"""
	for line in lines:
		table = line.get("pos_table")
		sale_type = line.get("pos_sale_type")
		if line.get("room"):
			line.place = line.room
		elif sale_type:
			line.place = _("Employee - {0}").format(_(sale_type))
		elif not table:
			line.place = _("Walk-in")
		elif str(table).isdigit():
			line.place = _("Table {0}").format(table)
		else:
			line.place = str(table)


def _line_tax_expr():
	"""
	SQL for the tax ERPNext already worked out for a sold line.

	ERPNext stores the per-item breakup of every tax row on the order itself, so
	the report reads it instead of splitting the order's tax total by hand. That
	is the only figure that stays right once items on one order are taxed at
	different rates, or exempt.

	Older orders were submitted before ERPNext kept that breakup, so the column
	comes back NULL for them and `_set_tax` falls back to sharing out the order
	total.
	"""
	if not frappe.db.table_exists("Item Wise Tax Detail"):
		return "NULL"

	# Stored in company currency, so it is brought back to the order's currency
	# the same way every other amount on the line is quoted.
	return """(
			SELECT SUM(iwt.amount) / IFNULL(NULLIF(so.conversion_rate, 0), 1)
			FROM `tabItem Wise Tax Detail` iwt
			WHERE iwt.parenttype = 'Sales Order'
				AND iwt.parent = so.name
				AND iwt.item_row = soi.name
				AND iwt.docstatus < 2
		)"""


def _set_tax(lines):
	"""
	Give every line its tax, its amount before tax and the amount actually paid.

	Both money figures are the order's own. Which one is stored and which is the
	remainder depends on how the POS profile charges tax: an inclusive profile
	sells at the menu price and the line amount is what the customer paid, so the
	amount before tax is what is left of it; an exclusive profile adds the tax on
	top of the line, so the line amount is the amount before tax.

	Taking the line amount for both - as a report that ignores the setting does -
	charges the tax twice on an inclusive profile, which is why the report used to
	come out above the till.

	Where the order predates ERPNext's stored breakup the order's tax total is
	shared out in proportion to what each line contributed, with the last line of
	the order taking whatever rounding left over so the column still adds up to
	the tax actually charged. That share is measured against the whole order, so a
	line carries the same tax however the report is narrowed.
	"""
	by_order = {}
	for line in lines:
		by_order.setdefault(line.sales_order, []).append(line)

	for order_lines in by_order.values():
		if all(line.get("line_tax") is not None for line in order_lines):
			for line in order_lines:
				line.tax_amount = flt(line.line_tax, 2)
		else:
			_share_out_tax(order_lines)

		for line in order_lines:
			line.pop("line_tax", None)
			gross = flt(line.pop("gross_amount", 0))
			net = flt(line.pop("net_amount", 0))
			tax = flt(line.tax_amount)

			if line.pop("tax_inclusive", 0):
				line.amount_with_tax = flt(gross, 2)
				line.amount = flt(gross - tax, 2)
			else:
				line.amount = flt(net, 2)
				line.amount_with_tax = flt(net + tax, 2)

			qty = flt(line.qty)
			line.rate = flt(line.amount / qty, 2) if qty else 0.0
			line.rate_with_tax = flt(line.amount_with_tax / qty, 2) if qty else 0.0


def _share_out_tax(order_lines):
	"""Fallback for orders with no stored breakup: split the order's tax total."""
	first = order_lines[0]
	order_tax = flt(first.order_tax)
	order_net = flt(first.order_net_total)

	# Every line of this order is present only when nothing filtered them out
	whole_order = abs(sum(flt(l.net_amount) for l in order_lines) - order_net) < 0.01

	running = 0.0
	for index, line in enumerate(order_lines):
		if not order_tax or not order_net:
			line.tax_amount = 0.0
		elif whole_order and index == len(order_lines) - 1:
			line.tax_amount = flt(order_tax - running, 2)
		else:
			line.tax_amount = flt(order_tax * flt(line.net_amount) / order_net, 2)
			running += line.tax_amount


def _conditions(filters, room_expr, table_expr):
	"""SQL fragments and their bound values, one per filter the user set."""
	conditions = []
	values = {}

	simple = {
		"company": "so.company",
		"pos_opening_shift": "so.posa_pos_opening_shift",
		"item_group": "soi.item_group",
		"item_code": "soi.item_code",
		"customer": "so.customer",
	}
	if _has("Sales Order", "pos_sale_type"):
		simple["pos_sale_type"] = "so.pos_sale_type"
	if _has("Sales Order", "employee"):
		simple["employee"] = "so.employee"

	for key, column in simple.items():
		if filters.get(key):
			conditions.append(f" AND {column} = %({key})s")
			values[key] = filters.get(key)

	if filters.get("room"):
		conditions.append(f" AND {room_expr} = %(room)s")
		values["room"] = filters.get("room")

	# A filter the Sales Order cannot answer must exclude it, not be ignored
	for key in ("pos_sale_type", "employee"):
		if filters.get(key) and key not in simple:
			conditions.append(" AND 1 = 0")

	if filters.get("pos_table") and table_expr != "NULL":
		conditions.append(f" AND {table_expr} = %(pos_table)s")
		values["pos_table"] = filters.get("pos_table")

	# The profile lives on the shift, not on the Sales Order, so filtering by it
	# necessarily drops orders rung up before the shift field existed.
	if filters.get("pos_profile"):
		conditions.append(" AND os.pos_profile = %(pos_profile)s")
		values["pos_profile"] = filters.get("pos_profile")

	if filters.get("cashier"):
		conditions.append(" AND os.user = %(cashier)s")
		values["cashier"] = filters.get("cashier")

	if filters.get("from_date"):
		conditions.append(" AND so.transaction_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append(" AND so.transaction_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	return conditions, values


def _group(lines, group_by):
	"""
	Collapse the lines onto the chosen key, summing quantity and amount.

	`orders` counts distinct vouchers - a Sales Order, or the Material Issue an
	employee handout left instead - rather than lines, so "12 orders" means twelve
	sales and not twelve rows.

	A bucket whose lines were all unpriced keeps empty money columns instead of
	summing to zero, so a Benefits row still reads as "no price" rather than as
	"sold for nothing".
	"""
	keys = GROUP_KEYS.get(group_by) or GROUP_KEYS["Item"]
	buckets = {}

	for line in lines:
		key = tuple(line.get(field) for field in keys)
		bucket = buckets.get(key)
		if not bucket:
			bucket = buckets[key] = frappe._dict(
				{field: line.get(field) for field in keys},
				qty=0.0,
				amount=0.0,
				tax_amount=0.0,
				amount_with_tax=0.0,
				currency=line.get("currency"),
				_orders=set(),
				_priced=False,
			)
			# Carried for readability, taken from the first line of the bucket:
			# every line in it shares the key these describe.
			if "item_code" in keys:
				bucket.item_name = line.get("item_name")
				bucket._uoms = set()
			if group_by == "Shift":
				bucket.cashier = line.get("cashier")
				bucket.date = line.get("date")

		bucket.qty += flt(line.get("qty"))
		bucket.amount += flt(line.get("amount"))
		bucket.tax_amount += flt(line.get("tax_amount"))
		bucket.amount_with_tax += flt(line.get("amount_with_tax"))
		bucket._priced = bucket._priced or line.get("amount") is not None
		bucket._orders.add(line.get("voucher"))
		if "_uoms" in bucket:
			bucket._uoms.add(line.get("uom"))

	rows = []
	for bucket in buckets.values():
		bucket.orders = len(bucket.pop("_orders"))
		if "_uoms" in bucket:
			# Left blank when an item was sold in more than one unit, because a
			# single label over a summed quantity would be a lie
			uoms = bucket.pop("_uoms")
			bucket.uom = uoms.pop() if len(uoms) == 1 else None
		# The average paid per unit, which is not the list rate once an item is
		# sold at different prices across the period.
		bucket.avg_rate = flt(bucket.amount / bucket.qty) if bucket.qty else 0.0
		bucket.avg_rate_with_tax = (
			flt(bucket.amount_with_tax / bucket.qty) if bucket.qty else 0.0
		)
		if not bucket.pop("_priced"):
			for field in ("avg_rate", "avg_rate_with_tax", "amount", "tax_amount", "amount_with_tax"):
				bucket[field] = None
		rows.append(bucket)

	rows.sort(key=lambda row: flt(row.get("amount")), reverse=True)

	if "item_code" in keys and "item_group" not in keys:
		_label_item_groups(rows)

	return rows


def _label_item_groups(rows):
	"""
	Name each item's group from the Item master rather than the sold line.

	The line stores the group the item had when it was sold, so an item moved to
	another group since would have its own total labelled with whichever group
	happened to come first. Grouping *by* item group still reads the line, which
	is the historical truth; this only labels a row that is keyed by item.
	"""
	codes = [row.get("item_code") for row in rows if row.get("item_code")]
	if not codes:
		return

	groups = dict(
		frappe.get_all(
			"Item",
			filters={"name": ["in", codes]},
			fields=["name", "item_group"],
			as_list=True,
		)
	)
	for row in rows:
		row.item_group = groups.get(row.get("item_code"))


def _currency(lines):
	return lines[0].get("currency") if lines else None


def _columns(group_by, currency):
	def money(label, fieldname, width=120):
		return {
			"label": label,
			"fieldname": fieldname,
			"fieldtype": "Currency",
			"options": "currency",
			"width": width,
		}

	if group_by == "Detail":
		return [
			{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 95},
			{
				"label": _("Shift"),
				"fieldname": "shift",
				"fieldtype": "Link",
				"options": "POS Opening Shift",
				"width": 150,
			},
			{
				"label": _("Cashier"),
				"fieldname": "cashier",
				"fieldtype": "Link",
				"options": "User",
				"width": 150,
			},
			{
				"label": _("Sales Order"),
				"fieldname": "sales_order",
				"fieldtype": "Link",
				"options": "Sales Order",
				"width": 160,
			},
			{
				"label": _("Stock Entry"),
				"fieldname": "stock_entry",
				"fieldtype": "Link",
				"options": "Stock Entry",
				"width": 160,
			},
			{
				"label": _("Room"),
				"fieldname": "room",
				"fieldtype": "Link",
				"options": "Room",
				"width": 80,
			},
			{
				"label": _("Table"),
				"fieldname": "pos_table",
				"fieldtype": "Link",
				"options": "Table",
				"width": 110,
			},
			{
				"label": _("Employee"),
				"fieldname": "employee",
				"fieldtype": "Link",
				"options": "Employee",
				"width": 110,
			},
			{
				"label": _("Sale Type"),
				"fieldname": "pos_sale_type",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Item"),
				"fieldname": "item_code",
				"fieldtype": "Link",
				"options": "Item",
				"width": 200,
			},
			{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
			{
				"label": _("Item Group"),
				"fieldname": "item_group",
				"fieldtype": "Link",
				"options": "Item Group",
				"width": 140,
			},
			{"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 80},
			{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 90},
			money(_("Net Rate"), "rate", 105),
			money(_("Rate with Tax"), "rate_with_tax", 115),
			money(_("Net Amount"), "amount"),
			money(_("Tax"), "tax_amount", 100),
			money(_("Amount with Tax"), "amount_with_tax", 140),
			{"label": _("Customer"), "fieldname": "customer_name", "fieldtype": "Data", "width": 160},
			{"label": _("Currency"), "fieldname": "currency", "fieldtype": "Data", "width": 1, "hidden": 1},
		]

	keys = GROUP_KEYS.get(group_by) or GROUP_KEYS["Item"]
	key_columns = {
		"item_code": {
			"label": _("Item"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 220,
		},
		"item_group": {
			"label": _("Item Group"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 180,
		},
		"place": {
			"label": _("Room / Table"),
			"fieldname": "place",
			"fieldtype": "Data",
			"width": 140,
		},
		"shift": {
			"label": _("Shift"),
			"fieldname": "shift",
			"fieldtype": "Link",
			"options": "POS Opening Shift",
			"width": 180,
		},
	}

	columns = [key_columns[field] for field in keys]

	if group_by == "Shift":
		columns.append(
			{
				"label": _("Cashier"),
				"fieldname": "cashier",
				"fieldtype": "Link",
				"options": "User",
				"width": 170,
			}
		)
	if "item_code" in keys:
		columns.append(
			{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200}
		)
		if "item_group" not in keys:
			columns.append(
				{
					"label": _("Item Group"),
					"fieldname": "item_group",
					"fieldtype": "Link",
					"options": "Item Group",
					"width": 150,
				}
			)
		columns.append(
			{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 90}
		)

	columns += [
		{"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 90},
		money(_("Avg Net Rate"), "avg_rate", 115),
		money(_("Avg Rate with Tax"), "avg_rate_with_tax", 130),
		money(_("Net Amount"), "amount", 130),
		money(_("Tax"), "tax_amount", 110),
		money(_("Amount with Tax"), "amount_with_tax", 140),
		{"label": _("Orders"), "fieldname": "orders", "fieldtype": "Int", "width": 90},
		{"label": _("Currency"), "fieldname": "currency", "fieldtype": "Data", "width": 1, "hidden": 1},
	]
	return columns


def _chart(data, group_by):
	if not data or group_by == "Detail":
		return None

	keys = GROUP_KEYS.get(group_by) or GROUP_KEYS["Item"]
	top = data[:CHART_LIMIT]

	return {
		"data": {
			"labels": [
				" / ".join(str(row.get(field) or _("None")) for field in keys) for row in top
			],
			"datasets": [{"name": _("Amount"), "values": [flt(row.get("amount")) for row in top]}],
		},
		"type": "bar",
		"colors": ["#2563eb"],
		"fieldtype": "Currency",
	}


def _summary(lines):
	if not lines:
		return None

	currency = _currency(lines)
	tax_total = sum(flt(line.get("tax_amount")) for line in lines)
	items_total = sum(flt(line.get("amount")) for line in lines)
	# Each order's grand total counted once, however many lines it has. A voucher
	# nobody paid for - a Benefits handout, or an employee issue with no order
	# behind it at all - still counts as a transaction but brings no money with it,
	# so it does not quietly put a staff handout back into the day's takings.
	order_totals = {}
	for line in lines:
		voucher = line.get("voucher")
		order_totals.setdefault(voucher, 0.0)
		if line.get("amount") is not None:
			order_totals[voucher] = flt(line.get("order_total"))

	return [
		{
			"label": _("Net Total"),
			"value": items_total,
			"datatype": "Currency",
			"options": currency,
			"indicator": "Blue",
		},
		{
			"label": _("Tax"),
			"value": tax_total,
			"datatype": "Currency",
			"options": currency,
			"indicator": "Orange",
		},
		{
			"label": _("Total with Tax"),
			"value": items_total + tax_total,
			"datatype": "Currency",
			"options": currency,
			"indicator": "Green",
		},
		{
			# The orders' own grand totals. Differs from the line above when a filter
			# holds part of an order, and when the day includes an employee issue that
			# left no Sales Order to total - the line above prices those, this does not.
			"label": _("Sales Orders Total (incl. tax)"),
			"value": sum(order_totals.values()),
			"datatype": "Currency",
			"options": currency,
			"indicator": "Green",
		},
		{
			"label": _("Quantity"),
			"value": sum(flt(line.get("qty")) for line in lines),
			"datatype": "Float",
		},
		{"label": _("Orders"), "value": len(order_totals), "datatype": "Int"},
		{
			"label": _("Items Sold"),
			"value": len({line.get("item_code") for line in lines}),
			"datatype": "Int",
		},
	]
