# Copyright (c) 2026, ECS and contributors
"""Customer receipt: make the money owed refer to the ORDER, not to one invoice.

`sales_receipt_show_additions` already prints the added items and an "ORDER TOTAL" that
covers the whole order. The badge below it did not follow: it read `doc.outstanding_amount`
— this invoice alone — so a receipt could show "ORDER TOTAL 1,750" and, four lines later,
"Outstanding: 1,400". The driver reads the last number.

Worse, the PAID badge came from the same single-invoice figure: an order whose original
was settled but whose addition was not printed as PAID with money still owed on it.

So both now count the additions. Each invoice still prints its own legal total; only the
badge speaks for the order.

Idempotent — skipped when already applied or when the additions block is absent.
"""

import frappe

FORMAT = "print format sales"
MARKER = "kds-order-outstanding"
BASE_MARKER = "kds-additions"

# --- 1. carry the additions' own outstanding alongside their totals ---
FETCH_OLD = """      fields=["name", "custom_number_order", "grand_total"],
      order_by="creation asc") if not parent_order else [] -%}
{%- set ns_add = namespace(total=0) -%}
{%- for a in additions -%}{%- set ns_add.total = ns_add.total + (a.grand_total or 0) -%}{%- endfor -%}"""

FETCH_NEW = """      fields=["name", "custom_number_order", "grand_total", "outstanding_amount"],
      order_by="creation asc") if not parent_order else [] -%}
{#- kds-order-outstanding: the order owes what this invoice owes PLUS what its additions
    still owe. The badge below speaks for the order; each invoice keeps its own total. -#}
{%- set ns_add = namespace(total=0, outstanding=0) -%}
{%- for a in additions -%}{%- set ns_add.total = ns_add.total + (a.grand_total or 0) -%}
{%- set ns_add.outstanding = ns_add.outstanding + (a.outstanding_amount or 0) -%}{%- endfor -%}
{%- set order_outstanding = (doc.outstanding_amount or 0) + ns_add.outstanding -%}"""

# --- 2. badge + amount reflect the order ---
BADGE_OLD = """	{%- if is_paid -%}
	<span class="typebadge">&#10003; {{ _("PAID") }}</span>
	{%- else -%}
	<span class="typebadge" style="background:#fff; color:#000; border:2px solid #000;">{{ _("UNPAID") }}</span>
	{%- if doc.outstanding_amount -%}
	<div style="font-size:11px; font-weight:bold; margin-top:4px;">{{ _("Outstanding") }}: {{ "%.2f"|format(doc.outstanding_amount) }} {{ currency }}</div>
	{%- endif -%}
	{%- endif -%}"""

BADGE_NEW = """	{%- if is_paid and order_outstanding <= 0.009 -%}
	<span class="typebadge">&#10003; {{ _("PAID") }}</span>
	{%- else -%}
	<span class="typebadge" style="background:#fff; color:#000; border:2px solid #000;">{{ _("UNPAID") }}</span>
	{%- if order_outstanding > 0.009 -%}
	<div style="font-size:11px; font-weight:bold; margin-top:4px;">{{ _("Outstanding") }}: {{ "%.2f"|format(order_outstanding) }} {{ currency }}</div>
	{%- if additions and (doc.outstanding_amount or 0) != order_outstanding -%}
	<div style="font-size:10px; margin-top:2px;">({{ _("this receipt") }}: {{ "%.2f"|format(doc.outstanding_amount or 0) }} + {{ _("additions") }}: {{ "%.2f"|format(ns_add.outstanding) }})</div>
	{%- endif -%}
	{%- endif -%}
	{%- endif -%}"""


def execute():
	html = frappe.db.get_value("Print Format", FORMAT, "html")
	if not html:
		return
	if MARKER in html:
		return  # already applied
	if BASE_MARKER not in html:
		frappe.log_error(
			f"{FORMAT} has no {BASE_MARKER} block — run sales_receipt_show_additions first.",
			"Receipt Order Outstanding",
		)
		return

	for old, new in ((FETCH_OLD, FETCH_NEW), (BADGE_OLD, BADGE_NEW)):
		if html.count(old) != 1:
			frappe.log_error(
				f"{FORMAT}: expected exactly one match, found {html.count(old)}. Format edited by hand — skipped.",
				"Receipt Order Outstanding",
			)
			return
		html = html.replace(old, new)

	frappe.db.set_value("Print Format", FORMAT, "html", html)
	frappe.clear_cache()
