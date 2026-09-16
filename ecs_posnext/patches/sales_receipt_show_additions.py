# Copyright (c) 2026, ECS and contributors
"""Customer receipt ("print format sales"): make additions visible.

Items added to an order after it was placed live on their own supplement invoice, so the
original order's receipt listed only its first items and the two prints disagreed with
the kitchen ticket, which shows the whole order.

Each invoice still prints its own legal total — additions are NOT folded into it. What is
added is context:

* on the ORIGINAL order's receipt: the added items, listed per supplement invoice, plus
  an informational combined order total;
* on a SUPPLEMENT's receipt: a banner naming the order it belongs to.

Idempotent — skipped when the format is already patched or has been edited by hand.
"""

import frappe

MARKER = "kds-additions"

# --- 1. prefetch the addition invoices next to the other header lookups ---
PRE_OLD = """{%- set name_parts = doc.name.split("-") -%}"""

PRE_NEW = """{#- kds-additions: items added to this order after it was placed live on their own
    supplement invoices. Linked by custom_parent_order (a docname — order labels cycle
    per branch and cannot identify an order). -#}
{%- set parent_order = doc.custom_parent_order or doc.custom_parent_invoice or "" -%}
{%- set parent_order_no = frappe.db.get_value("Sales Invoice", parent_order, "custom_number_order") if parent_order else "" -%}
{%- set additions = frappe.get_all("Sales Invoice",
      filters={"custom_parent_order": doc.name, "docstatus": 1, "is_return": 0},
      fields=["name", "custom_number_order", "grand_total"],
      order_by="creation asc") if not parent_order else [] -%}
{%- set ns_add = namespace(total=0) -%}
{%- for a in additions -%}{%- set ns_add.total = ns_add.total + (a.grand_total or 0) -%}{%- endfor -%}
{%- set name_parts = doc.name.split("-") -%}"""

# --- 2. banner on a supplement's own receipt ---
BANNER_OLD = """{%- if doc.customer_name -%}
<div class="kv"><span class="ic">"""

BANNER_NEW = """{%- if parent_order_no -%}
<!-- ===== kds-additions: this receipt is an addition to an earlier order ===== -->
<div class="tablebanner" style="font-size:15px;">&#10133; {{ _("Addition to order") }} {{ parent_order_no }}</div>
{%- endif -%}
{%- if doc.customer_name -%}
<div class="kv"><span class="ic">"""

# --- 3. the added items, under the invoice's own items ---
ITEMS_OLD = """		{%- endfor -%}
	</tbody>
</table>

<!-- ===== Totals ===== -->"""

ITEMS_NEW = """		{%- endfor -%}
		{%- for a in additions -%}
		<!-- ===== kds-additions: items added later, on invoice {{ a.name }} ===== -->
		<tr>
			<td colspan="3" style="font-weight:bold;font-size:10px;padding-top:9px;border-bottom:1px solid #000;">
				&#10133; {{ _("Added") }} &mdash; {{ a.custom_number_order or a.name }}
			</td>
		</tr>
			{%- for item in frappe.get_all("Sales Invoice Item",
					filters={"parent": a.name}, fields=["item_name", "qty", "amount"],
					order_by="idx asc") -%}
			<tr>
				<td class="n">{{ item.item_name }}</td>
				<td class="q">{{ "%.0f"|format(item.qty) }}</td>
				<td class="p">{{ "%.2f"|format(item.amount) }}</td>
			</tr>
			{%- endfor -%}
		{%- endfor -%}
	</tbody>
</table>

<!-- ===== Totals ===== -->"""

# --- 4. combined order total, clearly marked as informational ---
TOTAL_OLD = """<div class="totalbox">
	<span class="l">{{ _("TOTAL") }}</span>
	<span class="r">{{ "%.2f"|format(doc.grand_total) }} {{ currency }}</span>
</div>"""

TOTAL_NEW = """<div class="totalbox">
	<span class="l">{{ _("TOTAL") }}</span>
	<span class="r">{{ "%.2f"|format(doc.grand_total) }} {{ currency }}</span>
</div>

{%- if additions -%}
<!-- ===== kds-additions: order total across this invoice and its additions ===== -->
<div class="srow" style="font-weight:normal;">
	<span class="l" style="font-weight:normal;">&#10133; {{ _("Additions") }}</span>
	<span class="r" style="font-weight:normal;">{{ "%.2f"|format(ns_add.total) }}</span>
</div>
<div class="totalbox">
	<span class="l">{{ _("ORDER TOTAL") }}</span>
	<span class="r">{{ "%.2f"|format(doc.grand_total + ns_add.total) }} {{ currency }}</span>
</div>
<div class="c" style="font-size:9px;margin-top:-4px;">
	{{ _("Additions are billed on their own receipts") }}
</div>
{%- endif -%}"""

REPLACEMENTS = [
	("prefetch", PRE_OLD, PRE_NEW),
	("addition banner", BANNER_OLD, BANNER_NEW),
	("added items", ITEMS_OLD, ITEMS_NEW),
	("order total", TOTAL_OLD, TOTAL_NEW),
]


def execute():
	name = "print format sales"
	if not frappe.db.exists("Print Format", name):
		return

	html = frappe.db.get_value("Print Format", name, "html") or ""
	if MARKER in html:
		return  # already patched

	missing = [label for label, old, _new in REPLACEMENTS if html.count(old) != 1]
	if missing:
		frappe.log_error(
			"Sales receipt addition support skipped — no single match for: {0}. "
			"The print format was edited by hand; it was left untouched.".format(", ".join(missing)),
			"KDS Print Format Patch",
		)
		return

	for _label, old, new in REPLACEMENTS:
		html = html.replace(old, new, 1)

	frappe.db.set_value("Print Format", name, "html", html)
	frappe.db.commit()
