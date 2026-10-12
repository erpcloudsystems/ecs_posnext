# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
Open Tables report

The back-office view of the floor: every seated table, what it has ordered, and
how long it has gone without ordering. Reads the same API the POS dashboard
uses, so the two can never disagree.
"""

from frappe import _

from ecs_posnext.api.table_orders import get_open_tables

# Frappe renders these as coloured indicator pills
STATUS_INDICATORS = {
	"late": "red",
	"warning": "orange",
	"ok": "green",
}


def status_label(state):
	"""
	Translated Status label.

	Built per call rather than in a module-level dict: `_()` at import time would
	freeze the label in whichever language happened to load the module first.
	"""
	return {
		"late": _("Late"),
		"warning": _("Waiting"),
		"ok": _("OK"),
	}.get(state, state)


def execute(filters=None):
	filters = filters or {}

	data = get_open_tables(pos_profile=filters.get("pos_profile"))
	rows = data["tables"]

	idle_state_filter = filters.get("idle_state")
	if idle_state_filter:
		rows = [row for row in rows if row["idle_state"] == idle_state_filter]

	if filters.get("only_without_order"):
		rows = [row for row in rows if not row["has_order"]]

	return get_columns(), get_data(rows), None, get_chart(rows), get_summary(rows, data)


def get_columns():
	return [
		{
			"label": _("Status"),
			"fieldname": "status_indicator",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Table"),
			"fieldname": "table",
			"fieldtype": "Link",
			"options": "Table",
			"width": 90,
		},
		{"label": _("Area"), "fieldname": "area", "fieldtype": "Data", "width": 110},
		{"label": _("Guests"), "fieldname": "guest_count", "fieldtype": "Int", "width": 80},
		{
			"label": _("Idle (min)"),
			"fieldname": "idle_minutes",
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"label": _("Seated (min)"),
			"fieldname": "seated_minutes",
			"fieldtype": "Int",
			"width": 110,
		},
		{"label": _("Items"), "fieldname": "item_qty", "fieldtype": "Float", "width": 90},
		{
			"label": _("Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Order"),
			"fieldname": "order",
			"fieldtype": "Link",
			"options": "POS Table Order",
			"width": 150,
		},
		{
			"label": _("Session"),
			"fieldname": "session",
			"fieldtype": "Link",
			"options": "POS Table Session",
			"width": 150,
		},
		{
			"label": _("Opened By"),
			"fieldname": "order_cashier",
			"fieldtype": "Link",
			"options": "User",
			"width": 160,
		},
		{
			"label": _("Last Order By"),
			"fieldname": "last_order_by",
			"fieldtype": "Link",
			"options": "User",
			"width": 160,
		},
		{
			"label": _("Seated At"),
			"fieldname": "opened_at",
			"fieldtype": "Datetime",
			"width": 160,
		},
		{
			"label": _("Last Order At"),
			"fieldname": "last_order_at",
			"fieldtype": "Datetime",
			"width": 160,
		},
	]


def get_data(rows):
	data = []
	for row in rows:
		state = row["idle_state"]
		data.append({
			# `indicator` drives the coloured pill; the label carries the meaning
			"status_indicator": status_label(state),
			"indicator": STATUS_INDICATORS.get(state, "gray"),
			"table": row["table"],
			"area": row["area"],
			"guest_count": row["guest_count"],
			"idle_minutes": row["idle_minutes"],
			"seated_minutes": row["seated_minutes"],
			"item_qty": row["item_qty"],
			"total_amount": row["total_amount"],
			"order": row["order"],
			"session": row["session"],
			"order_cashier": row.get("order_cashier") or row.get("cashier"),
			"last_order_by": row.get("last_order_by"),
			"opened_at": row["opened_at"],
			"last_order_at": row["last_order_at"],
		})
	return data


def get_chart(rows):
	"""Split the floor by attention needed - the report's headline."""
	late = sum(1 for row in rows if row["idle_state"] == "late")
	warning = sum(1 for row in rows if row["idle_state"] == "warning")
	ok = len(rows) - late - warning

	return {
		"data": {
			"labels": [_("OK"), _("Waiting"), _("Late")],
			"datasets": [{"name": _("Tables"), "values": [ok, warning, late]}],
		},
		"type": "donut",
		"colors": ["#22c55e", "#f59e0b", "#ef4444"],
	}


def get_summary(rows, data):
	thresholds = data["thresholds"]

	return [
		{
			"label": _("Open Tables"),
			"value": len(rows),
			"indicator": "Blue",
			"datatype": "Int",
		},
		{
			"label": _("Guests"),
			"value": sum(row["guest_count"] for row in rows),
			"indicator": "Blue",
			"datatype": "Int",
		},
		{
			"label": _("Open Total"),
			"value": sum(row["total_amount"] for row in rows),
			"indicator": "Green",
			"datatype": "Currency",
		},
		{
			"label": _("Nothing Ordered"),
			"value": sum(1 for row in rows if not row["has_order"]),
			"indicator": "Grey",
			"datatype": "Int",
		},
		{
			"label": _("Waiting {0}m+").format(thresholds["warning"] or "-"),
			"value": sum(1 for row in rows if row["idle_state"] == "warning"),
			"indicator": "Orange",
			"datatype": "Int",
		},
		{
			"label": _("Late {0}m+").format(thresholds["late"] or "-"),
			"value": sum(1 for row in rows if row["idle_state"] == "late"),
			"indicator": "Red",
			"datatype": "Int",
		},
	]
