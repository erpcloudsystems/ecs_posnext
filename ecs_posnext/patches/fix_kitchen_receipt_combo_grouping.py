# Copyright (c) 2026, ECS and contributors
"""Kitchen Receipt: stop printing a combo's components under unrelated items.

The macro paired a component with its parent by comparing `combo_group_id`. That id was
the invoice's item idx, and a supplement invoice's idx restarts at 1 — so once its rows
were merged into the original ticket the ids collided and, for example, Pepsi printed
with Big Mumo's components. The rewritten macro pairs by position instead: a component
belongs to the item it directly follows.

Idempotent — skipped when the format is already rewritten or has been edited by hand.
"""

import frappe

MARKER = "Components of this item"

OLD = '{# ============ KDS-driven items (mirrors the Assembly screen card) ============ #}\n{% macro kds_item_rows(kds_items) %}\n  {% for it in kds_items if not it.is_component %}\n    <tr>\n      <td width="40px" style="border-bottom: 0px !important;">{{ fmt_qty(it.qty) }} -</td>\n      <td style="border-bottom: 0px !important;">\n        <div class="d-flex flex-column">\n          <span class="fw-bold">\n            {{ it.item_name }}{% if it.kds_station %} <span class="fs-6">[{{ it.kds_station }}]</span>{% endif %}\n          </span>\n\n          {# Combo components (children with the same combo_group_id) #}\n          {% for ch in kds_items if ch.is_component and ch.combo_group_id and ch.combo_group_id == it.combo_group_id %}\n            <span class="ms-2">{{ fmt_qty(ch.qty) }} - {{ ch.item_name }}{% if ch.kds_station %} [{{ ch.kds_station }}]{% endif %}</span>\n            {# Removed ingredients on the component #}\n            {% if ch.removed_ingredients and ch.removed_ingredients.strip().startswith(\'[\') %}\n              {% for ri in json.loads(ch.removed_ingredients) %}\n                <span class="ms-4 text-decoration-line-through">✕ {{ ri.item_name if ri is mapping else ri }}</span>\n              {% endfor %}\n            {% endif %}\n            {% if ch.special_notes %}<span class="ms-4 fst-italic">— {{ ch.special_notes }}</span>{% endif %}\n          {% endfor %}\n\n          {# Removed ingredients on the main item #}\n          {% if it.removed_ingredients and it.removed_ingredients.strip().startswith(\'[\') %}\n            {% for ri in json.loads(it.removed_ingredients) %}\n              <span class="ms-2 text-decoration-line-through">✕ {{ ri.item_name if ri is mapping else ri }}</span>\n            {% endfor %}\n          {% endif %}\n        </div>\n      </td>\n    </tr>\n    <tr>\n      <td colspan="2" style="border-top: 0px !important;">\n        <span class="ms-2">Notes : {{ it.special_notes or "" }}</span>\n      </td>\n    </tr>\n  {% endfor %}\n{% endmacro %}\n\n'

NEW = '{# ============ KDS-driven items (mirrors the Assembly screen card) ============ #}\n{% macro kds_item_rows(kds_items) %}\n  {% for it in kds_items %}\n    {% if not it.is_component %}\n      {# Components of this item = the component rows that directly follow it, up to the\n         next non-component row. Matching on combo_group_id printed one combo\'s\n         components under unrelated items, because the id repeats once a supplement\n         invoice is merged into the same ticket. #}\n      {% set ns = namespace(children=[]) %}\n      {% for ch in kds_items[loop.index0 + 1:] %}\n        {% if ch.is_component and ns.children|length == loop.index0 %}\n          {% set _ = ns.children.append(ch) %}\n        {% endif %}\n      {% endfor %}\n    <tr>\n      <td width="40px" style="border-bottom: 0px !important;">{{ fmt_qty(it.qty) }} -</td>\n      <td style="border-bottom: 0px !important;">\n        <div class="d-flex flex-column">\n          <span class="fw-bold">\n            {{ it.item_name }}{% if it.kds_station %} <span class="fs-6">[{{ it.kds_station }}]</span>{% endif %}\n          </span>\n\n          {% for ch in ns.children %}\n            <span class="ms-2">{{ fmt_qty(ch.qty) }} - {{ ch.item_name }}{% if ch.kds_station %} [{{ ch.kds_station }}]{% endif %}</span>\n            {# Removed ingredients on the component #}\n            {% if ch.removed_ingredients and ch.removed_ingredients.strip().startswith(\'[\') %}\n              {% for ri in json.loads(ch.removed_ingredients) %}\n                <span class="ms-4 text-decoration-line-through">✕ {{ ri.item_name if ri is mapping else ri }}</span>\n              {% endfor %}\n            {% endif %}\n            {% if ch.special_notes %}<span class="ms-4 fst-italic">— {{ ch.special_notes }}</span>{% endif %}\n          {% endfor %}\n\n          {# Removed ingredients on the main item #}\n          {% if it.removed_ingredients and it.removed_ingredients.strip().startswith(\'[\') %}\n            {% for ri in json.loads(it.removed_ingredients) %}\n              <span class="ms-2 text-decoration-line-through">✕ {{ ri.item_name if ri is mapping else ri }}</span>\n            {% endfor %}\n          {% endif %}\n        </div>\n      </td>\n    </tr>\n    <tr>\n      <td colspan="2" style="border-top: 0px !important;">\n        <span class="ms-2">Notes : {{ it.special_notes or "" }}</span>\n      </td>\n    </tr>\n    {% endif %}\n  {% endfor %}\n{% endmacro %}\n\n'


def execute():
	name = "Kitchen Receipt"
	if not frappe.db.exists("Print Format", name):
		return

	html = frappe.db.get_value("Print Format", name, "html") or ""
	if MARKER in html:
		return  # already rewritten
	if OLD not in html:
		frappe.log_error(
			"Kitchen Receipt combo-grouping fix skipped: the KDS item macro no longer "
			"matches the expected text, so it was left untouched.",
			"KDS Print Format Patch",
		)
		return

	frappe.db.set_value("Print Format", name, "html", html.replace(OLD, NEW, 1))
	frappe.db.commit()
