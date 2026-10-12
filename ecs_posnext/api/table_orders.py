# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
Table Orders & Tables Dashboard API

Server-side held orders per table, and the dashboard that reads them. Held
orders live on the server (rather than only in the cashier's IndexedDB) so a
manager screen or a second terminal sees the true state of the floor.
"""

import json

import frappe
from frappe import _
from frappe.utils import cint, flt, now, time_diff_in_seconds

from ecs_posnext.api.table_sessions import _has_pos_profile_access

DOCTYPE_ORDER = "POS Table Order"
DOCTYPE_SESSION = "POS Table Session"
DOCTYPE_TABLE = "Table"

# Fallbacks used when a POS Profile has no POS Settings row yet
DEFAULT_IDLE_WARNING_MINUTES = 15
DEFAULT_IDLE_LATE_MINUTES = 30


def _parse_json_arg(value, name):
	"""Whitelisted methods receive JSON strings from the client; accept both forms."""
	if value is None:
		return None
	if isinstance(value, str):
		try:
			return json.loads(value) if value.strip() else None
		except ValueError:
			frappe.throw(_("Invalid JSON for {0}").format(name))
	return value


def _resolve_offline_actor(claimed_user):
	"""
	Validate the user a client says performed an action while offline.

	Only used on the offline-replay path: online, the acting user is
	`frappe.session.user` and is never taken from the request, so it cannot be
	spoofed. Even here the claim is only honoured for a real, enabled User -
	otherwise it falls back to the uploading session, and `synced_by` always
	records who actually sent it.

	Returns:
		str: the user id to attribute the action to.
	"""
	if not claimed_user or claimed_user == "Guest":
		return frappe.session.user

	enabled = frappe.db.get_value("User", claimed_user, "enabled")
	if enabled is None:
		frappe.log_error(
			f"Offline sync claimed unknown user {claimed_user!r}; "
			f"attributing to {frappe.session.user}",
			"POS Table Order Attribution",
		)
		return frappe.session.user

	if not enabled:
		# A disabled account should not be credited with new activity
		return frappe.session.user

	return claimed_user


def get_idle_thresholds(pos_profile=None):
	"""
	Idle thresholds (in minutes) for the given POS Profile.

	Returns:
		dict: {warning, late} - either may be 0, meaning that level is disabled.
	"""
	warning, late = DEFAULT_IDLE_WARNING_MINUTES, DEFAULT_IDLE_LATE_MINUTES

	if pos_profile:
		row = frappe.db.get_value(
			"POS Settings",
			{"pos_profile": pos_profile},
			["table_idle_warning_minutes", "table_idle_late_minutes"],
			as_dict=True,
		)
		if row:
			warning = cint(row.get("table_idle_warning_minutes"))
			late = cint(row.get("table_idle_late_minutes"))

	return {"warning": warning, "late": late}


def _idle_state(idle_minutes, thresholds):
	"""
	Map idle minutes onto a dashboard colour band.

	'late' is checked before 'warning' so the more severe band wins, and a
	threshold of 0 disables its band rather than matching everything.
	"""
	late = cint(thresholds.get("late"))
	warning = cint(thresholds.get("warning"))

	if late and idle_minutes >= late:
		return "late"
	if warning and idle_minutes >= warning:
		return "warning"
	return "ok"


def _get_open_orders(session):
	"""Every open order on a session - one normally, N once the bill is split."""
	return frappe.get_all(
		DOCTYPE_ORDER,
		filters={"table_session": session, "status": "Open"},
		fields=["name", "check_number", "room", "total_amount"],
		order_by="check_number asc, creation asc",
	)


def _get_working_order(session, throw_if_split=True):
	"""
	The single order a session is still building.

	Once a bill is split there is no single order any more, and silently picking
	one would put items or a payment on an arbitrary guest's check. Callers that
	cannot act on an ambiguous table get a clear error telling them to name the
	check instead.

	Returns:
		str|None: the order name, or None when the table has no open order.
	"""
	orders = _get_open_orders(session)

	if not orders:
		return None

	if len(orders) > 1:
		if throw_if_split:
			frappe.throw(
				_("Table has {0} separate checks. Choose which check to use.").format(len(orders)),
				title=_("Bill Is Split"),
			)
		return None

	return orders[0]["name"]


@frappe.whitelist()
def get_table_checks(session):
	"""
	Every check on a table, split or not - what the split screen and the
	dashboard read.

	Returns:
		dict: {session, table, is_split, checks: [...], total_amount, open_count}
	"""
	if not session or not frappe.db.exists(DOCTYPE_SESSION, session):
		return None

	sess = frappe.db.get_value(
		DOCTYPE_SESSION, session, ["name", "table", "guest_count", "status"], as_dict=True
	)

	checks = frappe.get_all(
		DOCTYPE_ORDER,
		filters={"table_session": session, "status": ["in", ["Open", "Settled"]]},
		fields=[
			"name",
			"check_number",
			"room",
			"status",
			"total_qty",
			"total_amount",
			"customer",
			"customer_name",
			"cashier",
			"sales_invoice",
			"external_reference",
		],
		order_by="check_number asc, creation asc",
	)

	for check in checks:
		check["items"] = frappe.get_all(
			"POS Table Order Item",
			filters={"parent": check["name"]},
			fields=["name", "item_code", "item_name", "qty", "uom", "rate", "amount", "added_by"],
			order_by="idx asc",
		)

	open_checks = [c for c in checks if c["status"] == "Open"]

	return {
		"session": sess["name"],
		"table": sess["table"],
		"guest_count": sess["guest_count"],
		"is_split": len(open_checks) > 1 or any(cint(c["check_number"]) > 0 for c in checks),
		"checks": checks,
		"open_count": len(open_checks),
		"total_amount": sum(flt(c["total_amount"]) for c in checks),
	}


@frappe.whitelist()
def split_table_order(order, checks):
	"""
	Split one table order into separate checks, one per guest or group.

	Splitting is by item: the caller says which lines and quantities belong to
	each check, and each check can carry its own `room` so it can be posted to
	that room separately.

	The split is all-or-nothing on quantities - every unit of every line has to
	land on exactly one check. A partial split would leave items belonging to
	nobody and a table that could never be fully settled.

	Args:
		order: The POS Table Order to split.
		checks: List (or JSON) of
			{room, customer, customer_name, items: [{item_code, uom, qty}]}.

	Returns:
		dict: {session, table, checks: [{name, check_number, room, total_amount}]}
	"""
	if not order:
		frappe.throw(_("Order is required"))

	checks = _parse_json_arg(checks, "checks") or []
	if len(checks) < 2:
		frappe.throw(_("A split needs at least two checks"))

	if not frappe.db.exists(DOCTYPE_ORDER, order):
		frappe.throw(_("Order {0} does not exist").format(order))

	src = frappe.get_doc(DOCTYPE_ORDER, order)

	if src.status != "Open":
		frappe.throw(_("Order {0} is not open").format(order))

	if cint(src.check_number):
		frappe.throw(
			_("Check {0} is already part of a split and cannot be split again").format(
				src.check_number
			)
		)

	# --- quantities must reconcile exactly against the source ---
	available = {}
	for row in src.items:
		key = (row.item_code, row.uom or "")
		available[key] = available.get(key, 0) + flt(row.qty)

	requested = {}
	for check in checks:
		for line in check.get("items") or []:
			key = (line.get("item_code"), line.get("uom") or "")
			requested[key] = requested.get(key, 0) + flt(line.get("qty"))

	for key, qty in requested.items():
		have = available.get(key, 0)
		if flt(qty, 6) > flt(have, 6):
			frappe.throw(
				_("Check lines ask for {0} x {1} but the order only has {2}").format(
					qty, key[0], have
				)
			)

	for key, have in available.items():
		asked = requested.get(key, 0)
		if flt(asked, 6) != flt(have, 6):
			frappe.throw(
				_("{0} x {1} is not assigned to any check. Every item must belong to a check.").format(
					flt(have) - flt(asked), key[0]
				),
				title=_("Unassigned Items"),
			)

	# Rates come from the source, never from the client, so a split cannot reprice
	rate_by_key = {}
	for row in src.items:
		rate_by_key.setdefault((row.item_code, row.uom or ""), row)

	created = []
	for index, check in enumerate(checks, start=1):
		lines = [line for line in (check.get("items") or []) if flt(line.get("qty")) > 0]
		if not lines:
			frappe.throw(_("Check {0} has no items").format(index))

		doc = frappe.new_doc(DOCTYPE_ORDER)
		doc.table_session = src.table_session
		doc.table = src.table
		doc.status = "Open"
		doc.check_number = index
		doc.split_from = src.name
		doc.room = check.get("room")
		doc.guest_count = 1
		doc.pos_profile = src.pos_profile
		doc.pos_opening_shift = src.pos_opening_shift
		doc.cashier = src.cashier
		doc.last_order_by = frappe.session.user
		doc.customer = check.get("customer") or src.customer
		doc.customer_name = check.get("customer_name") or src.customer_name

		for line in lines:
			source_row = rate_by_key.get((line.get("item_code"), line.get("uom") or ""))
			qty = flt(line.get("qty"))
			rate = flt(source_row.rate) if source_row else 0
			doc.append("items", {
				"item_code": line.get("item_code"),
				"item_name": source_row.item_name if source_row else None,
				"qty": qty,
				"uom": line.get("uom") or (source_row.uom if source_row else None),
				"rate": rate,
				"amount": qty * rate,
				# The waiter who rang the line keeps it across the split
				"added_by": source_row.added_by if source_row else frappe.session.user,
			})

		doc.flags.ignore_permissions = True
		doc.insert()
		created.append({
			"name": doc.name,
			"check_number": doc.check_number,
			"room": doc.room,
			"total_qty": doc.total_qty,
			"total_amount": doc.total_amount,
		})

	# The source's lines now live on the checks; leaving it Open would double the
	# table's total and give the cashier an extra payable order.
	src.status = "Cancelled"
	src.flags.ignore_permissions = True
	src.save()

	_log_split(src, created)

	return {
		"session": src.table_session,
		"table": src.table,
		"split_from": src.name,
		"checks": created,
	}


def _log_split(src, created):
	"""Record the split on the session timeline. Never fails the split itself."""
	try:
		summary = ", ".join(
			f"#{c['check_number']}"
			+ (f" -> room {c['room']}" if c.get("room") else "")
			+ f" ({c['total_amount']})"
			for c in created
		)
		frappe.get_doc(DOCTYPE_SESSION, src.table_session).add_comment(
			"Info",
			_("Order {0} split into {1} checks by {2}: {3}").format(
				src.name, len(created), frappe.session.user, summary
			),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "POS Table Split Log")


@frappe.whitelist()
def set_check_room(order, room=None):
	"""
	Charge a check to a room (or clear it).

	Kept editable while the check is still open: the room is what decides where
	the amount is posted, so a mis-typed one has to be fixable before payment
	rather than after.

	Returns:
		dict: {name, room}
	"""
	if not order:
		frappe.throw(_("Order is required"))

	if not frappe.db.exists(DOCTYPE_ORDER, order):
		frappe.throw(_("Order {0} does not exist").format(order))

	doc = frappe.get_doc(DOCTYPE_ORDER, order)

	if doc.status != "Open":
		frappe.throw(
			_("Check {0} is already {1} and cannot be re-charged to another room").format(
				doc.check_number or doc.name, doc.status.lower()
			)
		)

	if room and not frappe.db.exists("Room", room):
		frappe.throw(_("Room {0} does not exist").format(room))

	doc.room = room or None
	doc.flags.ignore_permissions = True
	doc.save()

	return {"name": doc.name, "room": doc.room}


@frappe.whitelist()
def get_open_tables(pos_profile=None, include_free=0):
	"""
	Every open table with its order summary and idle state - the tables dashboard.

	Idle time is measured from the last order, falling back to the seating time
	while nothing has been ordered yet, which is what makes "sat a long time
	without ordering" visible.

	Args:
		pos_profile: Optional filter to one POS Profile.
		include_free: Also return tables with no open session, so the same screen
			can be used to seat a table rather than only to watch the ones already
			seated. Free rows carry `seated = 0` and no order figures.

	Returns:
		dict: {tables, thresholds, server_now}
			`server_now` lets the client tick the timers locally without drifting
			against the server clock or the browser's timezone.
	"""
	if not _has_pos_profile_access(pos_profile):
		frappe.throw(_("You don't have access to this POS Profile"), frappe.PermissionError)

	filters = {"status": "Open"}
	if pos_profile:
		filters["pos_profile"] = pos_profile

	sessions = frappe.get_all(
		DOCTYPE_SESSION,
		filters=filters,
		fields=[
			"name",
			"table",
			"guest_count",
			"opened_at",
			"last_order_at",
			"cashier",
			"pos_profile",
			"pos_opening_shift",
		],
		order_by="opened_at asc",
	)

	include_free = cint(include_free)

	if not sessions:
		return {
			"tables": _free_table_rows(set()) if include_free else [],
			"thresholds": get_idle_thresholds(pos_profile),
			"server_now": now(),
		}

	# One query for every open order, rather than one per table
	orders = frappe.get_all(
		DOCTYPE_ORDER,
		filters={
			"status": "Open",
			"table_session": ["in", [s["name"] for s in sessions]],
		},
		fields=[
			"name",
			"table_session",
			"check_number",
			"room",
			"total_qty",
			"total_amount",
			"ordered_at",
			"last_order_at",
			"customer",
			"customer_name",
			"cashier",
			"last_order_by",
		],
	)
	# A split table has several open orders, so aggregate rather than keeping one:
	# picking one would under-report the table's total on the dashboard.
	orders_by_session = {}
	for row in orders:
		bucket = orders_by_session.setdefault(row["table_session"], {
			"checks": 0,
			"total_qty": 0.0,
			"total_amount": 0.0,
			"first": row,
			"last_order_at": None,
			"rooms": [],
		})
		bucket["checks"] += 1
		bucket["total_qty"] += flt(row.get("total_qty"))
		bucket["total_amount"] += flt(row.get("total_amount"))
		if row.get("room"):
			bucket["rooms"].append(row["room"])
		# The table is idle only since its most recent activity on any check
		stamp = row.get("last_order_at")
		if stamp and (not bucket["last_order_at"] or str(stamp) > str(bucket["last_order_at"])):
			bucket["last_order_at"] = stamp

	# Table metadata (area/capacity) in one query too
	table_names = [s["table"] for s in sessions if s.get("table")]
	table_meta = {}
	if table_names:
		for row in frappe.get_all(
			"Table",
			filters={"name": ["in", table_names]},
			fields=["name", "table_number", "area", "seating_capacity"],
		):
			table_meta[row["name"]] = row

	thresholds = get_idle_thresholds(pos_profile)
	server_now = now()
	result = []

	for session in sessions:
		order = orders_by_session.get(session["name"])

		# The order's own clock is authoritative; the session mirror and the
		# seating time are progressively weaker fallbacks.
		first = (order or {}).get("first") or {}
		idle_since = (
			(order or {}).get("last_order_at")
			or session.get("last_order_at")
			or session.get("opened_at")
		)
		idle_minutes = 0
		if idle_since:
			idle_minutes = int(max(0, time_diff_in_seconds(server_now, idle_since)) // 60)

		seated_minutes = 0
		if session.get("opened_at"):
			seated_minutes = int(
				max(0, time_diff_in_seconds(server_now, session["opened_at"])) // 60
			)

		meta = table_meta.get(session["table"], {})

		result.append({
			"seated": 1,
			"session": session["name"],
			"table": session["table"],
			"table_number": meta.get("table_number") or session["table"],
			"area": meta.get("area"),
			"seating_capacity": meta.get("seating_capacity"),
			"guest_count": cint(session.get("guest_count")),
			"cashier": session.get("cashier"),
			"pos_profile": session.get("pos_profile"),
			"opened_at": session.get("opened_at"),
			"seated_minutes": seated_minutes,
			# Order summary - all zero/None when the table has ordered nothing yet.
			# Totals span every open check on the table.
			"order": first.get("name") if (order or {}).get("checks") == 1 else None,
			"item_qty": flt((order or {}).get("total_qty")),
			"total_amount": flt((order or {}).get("total_amount")),
			"customer": first.get("customer"),
			"customer_name": first.get("customer_name"),
			# Who opened the order vs who last added to it - the session's cashier
			# is the fallback for a table that has ordered nothing yet.
			"order_cashier": first.get("cashier") or session.get("cashier"),
			"last_order_by": first.get("last_order_by"),
			# Split state, so the dashboard can show "3 checks" and offer per-check payment
			"open_checks": cint((order or {}).get("checks")),
			"is_split": cint((order or {}).get("checks")) > 1,
			"rooms": (order or {}).get("rooms") or [],
			"has_order": bool(order),
			"ordered_at": (order or {}).get("ordered_at"),
			"last_order_at": idle_since,
			"idle_minutes": idle_minutes,
			"idle_state": _idle_state(idle_minutes, thresholds),
		})

	if include_free:
		result.extend(_free_table_rows({s["table"] for s in sessions}))

	return {"tables": result, "thresholds": thresholds, "server_now": server_now}


def _free_table_rows(occupied_tables):
	"""
	Tables with nobody at them, shaped like the seated rows.

	Same shape deliberately: the dashboard renders one card component, and a free
	table differing only by `seated = 0` keeps that a single code path.
	"""
	filters = {"disabled": 0}
	if occupied_tables:
		filters["name"] = ["not in", list(occupied_tables)]

	rows = frappe.get_all(
		DOCTYPE_TABLE,
		filters=filters,
		fields=["name", "table_number", "area", "seating_capacity"],
		order_by="table_number asc",
	)

	return [{
		"seated": 0,
		"session": None,
		"table": row["name"],
		"table_number": row["table_number"] or row["name"],
		"area": row["area"],
		"seating_capacity": row["seating_capacity"],
		"guest_count": 0,
		"cashier": None,
		"pos_profile": None,
		"opened_at": None,
		"seated_minutes": 0,
		"order": None,
		"item_qty": 0,
		"total_amount": 0,
		"customer": None,
		"customer_name": None,
		"has_order": False,
		"ordered_at": None,
		"last_order_at": None,
		"idle_minutes": 0,
		"idle_state": "free",
		"order_cashier": None,
		"last_order_by": None,
		"open_checks": 0,
		"is_split": False,
		"rooms": [],
	} for row in rows]


@frappe.whitelist()
def save_table_order(
	table_session,
	items,
	cart_payload=None,
	customer=None,
	customer_name=None,
	guest_count=None,
	pos_profile=None,
	pos_opening_shift=None,
):
	"""
	Create or update the held order for a table session.

	One open order per session: saving again updates that order rather than
	stacking a second one, so "hold" is idempotent per table.

	Args:
		table_session: POS Table Session name.
		items: List (or JSON string) of {item_code, item_name, qty, uom, rate, amount}.
		cart_payload: Full POS cart as JSON, restored verbatim on resume.
		customer, customer_name, guest_count: Order context.
		pos_profile, pos_opening_shift: POS context.

	Returns:
		dict: {name, table, status, total_qty, total_amount, last_order_at}
	"""
	if not table_session:
		frappe.throw(_("Table Session is required"))

	if not frappe.db.exists(DOCTYPE_SESSION, table_session):
		frappe.throw(_("Table Session {0} does not exist").format(table_session))

	items = _parse_json_arg(items, "items") or []
	if not items:
		frappe.throw(_("Cannot hold an order with no items"))

	session = frappe.db.get_value(
		DOCTYPE_SESSION,
		table_session,
		["table", "guest_count", "pos_profile", "pos_opening_shift", "status"],
		as_dict=True,
	)

	if session.get("status") != "Open":
		frappe.throw(_("Table Session {0} is not open").format(table_session))

	# Throws when the bill is already split: adding to "the" order would silently
	# land the items on one guest's check.
	existing = _get_working_order(table_session)

	doc = frappe.get_doc(DOCTYPE_ORDER, existing) if existing else frappe.new_doc(DOCTYPE_ORDER)

	doc.table_session = table_session
	doc.table = session.get("table")
	doc.status = "Open"
	doc.guest_count = cint(guest_count) or cint(session.get("guest_count"))
	doc.pos_profile = pos_profile or session.get("pos_profile")
	doc.pos_opening_shift = pos_opening_shift or session.get("pos_opening_shift")
	# `cashier` is the user who OPENED the order and must survive a second waiter
	# adding a round to the same table; `last_order_by` carries who touched it last.
	if not doc.cashier:
		doc.cashier = frappe.session.user
	doc.last_order_by = frappe.session.user
	doc.customer = customer
	doc.customer_name = customer_name

	if cart_payload is not None:
		doc.cart_payload = (
			cart_payload if isinstance(cart_payload, str) else json.dumps(cart_payload, default=str)
		)

	doc.items = []
	for row in items:
		if not row.get("item_code"):
			continue
		qty = flt(row.get("qty"))
		rate = flt(row.get("rate"))
		doc.append("items", {
			"item_code": row.get("item_code"),
			"item_name": row.get("item_name"),
			"qty": qty,
			"uom": row.get("uom"),
			"rate": rate,
			# Derived here so the stored amount always matches qty x rate
			"amount": flt(row.get("amount")) or (qty * rate),
			# Attribution per line: a table's rounds can be taken by different
			# waiters, and anything pushed to an external system has to carry the
			# user who actually rang it. A line the client already attributes
			# (replayed from offline) keeps that user.
			"added_by": row.get("added_by") or frappe.session.user,
		})

	if not doc.items:
		frappe.throw(_("Cannot hold an order with no items"))

	doc.flags.ignore_permissions = True
	doc.save()

	return {
		"name": doc.name,
		"table": doc.table,
		"status": doc.status,
		"total_qty": doc.total_qty,
		"total_amount": doc.total_amount,
		"last_order_at": doc.last_order_at,
		"cashier": doc.cashier,
		"last_order_by": doc.last_order_by,
	}


@frappe.whitelist()
def get_table_order(order=None, table_session=None):
	"""
	Fetch a held order for resuming, including its exact cart payload.

	Args:
		order: POS Table Order name, or
		table_session: the session whose open order should be returned.

	Returns:
		dict|None: order details with `cart` parsed back from the payload.
	"""
	if not order and table_session:
		# A split table has no single order - the caller must name the check
		order = _get_working_order(table_session)

	if not order or not frappe.db.exists(DOCTYPE_ORDER, order):
		return None

	doc = frappe.get_doc(DOCTYPE_ORDER, order)

	cart = None
	if doc.cart_payload:
		try:
			cart = json.loads(doc.cart_payload)
		except ValueError:
			# A corrupt payload must not block resuming - the items table below
			# still describes the order well enough to rebuild it by hand.
			frappe.log_error(
				f"Corrupt cart_payload on {doc.name}", "POS Table Order Payload"
			)

	return {
		"name": doc.name,
		"table": doc.table,
		"table_session": doc.table_session,
		"guest_count": doc.guest_count,
		"status": doc.status,
		"customer": doc.customer,
		"customer_name": doc.customer_name,
		"total_qty": doc.total_qty,
		"total_amount": doc.total_amount,
		"ordered_at": doc.ordered_at,
		"last_order_at": doc.last_order_at,
		"items": [
			{
				"item_code": row.item_code,
				"item_name": row.item_name,
				"qty": row.qty,
				"uom": row.uom,
				"rate": row.rate,
				"amount": row.amount,
			}
			for row in doc.items
		],
		"cart": cart,
	}


@frappe.whitelist()
def settle_table_order(order=None, table_session=None, sales_invoice=None, external_reference=None):
	"""
	Mark a held order settled once its bill is paid.

	Never throws on a missing order: by the time this runs the sale is already
	submitted, and failing here would strand a paid invoice.

	Returns:
		dict: {name, status}
	"""
	if not order and table_session:
		# Each check is paid separately, so settling by session only works while
		# the table still has a single order.
		order = _get_working_order(table_session)

	if not order or not frappe.db.exists(DOCTYPE_ORDER, order):
		return {"name": order, "status": "Missing"}

	doc = frappe.get_doc(DOCTYPE_ORDER, order)
	if doc.status == "Open":
		doc.settle(sales_invoice=sales_invoice, external_reference=external_reference)

	remaining = len(_get_open_orders(doc.table_session))

	return {
		"name": doc.name,
		"status": doc.status,
		"check_number": doc.check_number,
		# The caller closes the table only once nothing is left to pay
		"remaining_open_checks": remaining,
	}


@frappe.whitelist()
def cancel_table_order(order=None, table_session=None):
	"""Release a held order that was abandoned. Returns {name, status}."""
	# Abandoning a table releases every check on it, not an arbitrary one
	if not order and table_session:
		cancelled = []
		for row in _get_open_orders(table_session):
			doc = frappe.get_doc(DOCTYPE_ORDER, row["name"])
			doc.status = "Cancelled"
			doc.flags.ignore_permissions = True
			doc.save()
			cancelled.append(doc.name)
		return {"status": "Cancelled", "orders": cancelled}

	if not order or not frappe.db.exists(DOCTYPE_ORDER, order):
		return {"name": order, "status": "Missing"}

	doc = frappe.get_doc(DOCTYPE_ORDER, order)
	if doc.status == "Open":
		doc.status = "Cancelled"
		doc.flags.ignore_permissions = True
		doc.save()

	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def sync_offline_table_order(
	offline_id,
	table,
	items,
	guest_count=None,
	cart_payload=None,
	customer=None,
	customer_name=None,
	pos_profile=None,
	pos_opening_shift=None,
	opened_at=None,
	last_order_at=None,
	cashier=None,
):
	"""
	Push a table seated and held while offline up to the server.

	Creates the session and its order in one call, keyed on the client-generated
	`offline_id`. Replaying the same sync is therefore harmless: the session is
	found rather than created a second time, and the order is updated in place.

	Seating and ordering times are taken from the client so the dashboard's idle
	and seated timers reflect when things actually happened, not when the network
	came back.

	Args:
		offline_id: Client-generated unique id for the offline session.
		table: Table the guests were seated at.
		items: Order lines (see `save_table_order`).
		guest_count: Guests seated.
		cart_payload: Full POS cart as JSON, restored verbatim on resume.
		customer, customer_name: Order context.
		pos_profile, pos_opening_shift: POS context.
		opened_at: When the table was actually seated, offline.
		last_order_at: When the order was actually last added to, offline.
		cashier: The POS Next user who actually took the order offline. Without
			this the record would be credited to whoever's terminal happened to
			upload it. Validated, and `synced_by` still records the uploader.

	Returns:
		dict: {status, session, order, ...}. `status` is one of:
			"synced"   - session and order are on the server
			"conflict" - the table was seated by someone else while we were
			             offline; nothing was written, the caller must keep its
			             local copy and let a human resolve it
	"""
	if not offline_id:
		frappe.throw(_("Offline ID is required"))
	if not table:
		frappe.throw(_("Table is required"))

	items = _parse_json_arg(items, "items") or []
	if not items:
		frappe.throw(_("Cannot sync an order with no items"))

	if not frappe.db.exists(DOCTYPE_TABLE, table):
		frappe.throw(_("Table {0} does not exist").format(table))

	guest_count = cint(guest_count) or 1
	actor = _resolve_offline_actor(cashier)

	# Every line replayed from offline belongs to the user who rang it, not the
	# one uploading it now.
	for row in items:
		if isinstance(row, dict):
			row.setdefault("added_by", actor)

	# Already synced? Reuse that session - this is what makes a replay safe.
	session_name = frappe.db.get_value(DOCTYPE_SESSION, {"offline_id": offline_id}, "name")

	if not session_name:
		# Someone else may have seated this table while we were offline. Merging
		# would splice two different parties' orders together, so refuse and hand
		# the decision back rather than corrupting either bill.
		clash = frappe.db.get_value(
			DOCTYPE_SESSION, {"table": table, "status": "Open"}, ["name", "cashier"], as_dict=True
		)
		if clash:
			return {
				"status": "conflict",
				"offline_id": offline_id,
				"table": table,
				"existing_session": clash["name"],
				"existing_cashier": clash.get("cashier"),
			}

		doc = frappe.new_doc(DOCTYPE_SESSION)
		doc.table = table
		doc.guest_count = guest_count
		doc.status = "Open"
		doc.pos_profile = pos_profile
		doc.pos_opening_shift = pos_opening_shift
		doc.offline_id = offline_id
		doc.cashier = actor
		doc.synced_by = frappe.session.user
		if opened_at:
			doc.opened_at = opened_at
		doc.insert(ignore_permissions=True)
		session_name = doc.name

		# before_insert stamps opened_at with now(); restore the offline time so
		# the dashboard reports how long the guests have really been seated.
		if opened_at:
			frappe.db.set_value(
				DOCTYPE_SESSION, session_name, "opened_at", opened_at, update_modified=False
			)

	order = save_table_order(
		table_session=session_name,
		items=items,
		cart_payload=cart_payload,
		customer=customer,
		customer_name=customer_name,
		guest_count=guest_count,
		pos_profile=pos_profile,
		pos_opening_shift=pos_opening_shift,
	)

	# save_table_order() attributes to the uploading session, since online that is
	# correct. On this path it is not: credit the offline actor and keep the
	# uploader in synced_by.
	if order.get("name"):
		frappe.db.set_value(
			DOCTYPE_ORDER,
			order["name"],
			{
				"cashier": actor,
				"last_order_by": actor,
				"synced_by": frappe.session.user,
			},
			update_modified=False,
		)

	# Same reasoning as opened_at: the order clock belongs to when the cashier
	# actually rang it up, otherwise every synced table looks freshly served.
	if last_order_at and order.get("name"):
		frappe.db.set_value(
			DOCTYPE_ORDER, order["name"], "last_order_at", last_order_at, update_modified=False
		)
		frappe.db.set_value(
			DOCTYPE_SESSION, session_name, "last_order_at", last_order_at, update_modified=False
		)

	return {
		"status": "synced",
		"offline_id": offline_id,
		"session": session_name,
		"order": order.get("name"),
		"table": table,
		"total_qty": order.get("total_qty"),
		"total_amount": order.get("total_amount"),
		"cashier": actor,
		"synced_by": frappe.session.user,
	}


@frappe.whitelist()
def promote_offline_session(
	offline_id,
	table,
	guest_count=None,
	pos_profile=None,
	pos_opening_shift=None,
	opened_at=None,
	cashier=None,
):
	"""
	Create the server-side session for a table seated offline, with no order yet.

	Used when connectivity returns mid-order: the cart is still open, so there is
	nothing to hold, but the session has to exist before anything can be saved
	against it.

	Returns:
		dict: {status, session} - `status` is "synced" or "conflict" (see
			`sync_offline_table_order`).
	"""
	if not offline_id:
		frappe.throw(_("Offline ID is required"))
	if not table:
		frappe.throw(_("Table is required"))

	if not frappe.db.exists(DOCTYPE_TABLE, table):
		frappe.throw(_("Table {0} does not exist").format(table))

	existing = frappe.db.get_value(DOCTYPE_SESSION, {"offline_id": offline_id}, "name")
	if existing:
		return {"status": "synced", "session": existing, "offline_id": offline_id}

	clash = frappe.db.get_value(
		DOCTYPE_SESSION, {"table": table, "status": "Open"}, ["name", "cashier"], as_dict=True
	)
	if clash:
		return {
			"status": "conflict",
			"offline_id": offline_id,
			"table": table,
			"existing_session": clash["name"],
			"existing_cashier": clash.get("cashier"),
		}

	doc = frappe.new_doc(DOCTYPE_SESSION)
	doc.table = table
	doc.guest_count = cint(guest_count) or 1
	doc.status = "Open"
	doc.pos_profile = pos_profile
	doc.pos_opening_shift = pos_opening_shift
	doc.offline_id = offline_id
	doc.cashier = _resolve_offline_actor(cashier)
	doc.synced_by = frappe.session.user
	if opened_at:
		doc.opened_at = opened_at
	doc.insert(ignore_permissions=True)

	if opened_at:
		frappe.db.set_value(
			DOCTYPE_SESSION, doc.name, "opened_at", opened_at, update_modified=False
		)

	return {"status": "synced", "session": doc.name, "offline_id": offline_id}


@frappe.whitelist()
def move_table_session(session, target_table, merge=False):
	"""
	Move an open order from one table to another.

	Moves the session **and its open order** together. `update_table_session`
	changes only the session, which left `POS Table Order.table` pointing at the
	old table - the dashboard read right while the order record disagreed.

	When the destination already has an open order the two are not silently
	combined: that is two different bills. The caller gets `status: "occupied"`
	and must ask for `merge=True` explicitly (joining tables).

	Args:
		session: POS Table Session to move.
		target_table: Table to move it to.
		merge: Combine into the destination's existing order (joining tables).

	Returns:
		dict: {status, ...}. `status` is one of:
			"moved"    - session and order now sit on target_table
			"merged"   - lines folded into the destination's order; this session
			             is closed
			"occupied" - destination busy and merge was not requested; nothing
			             was changed
			"unchanged" - already on that table
	"""
	if not session:
		frappe.throw(_("Session is required"))
	if not target_table:
		frappe.throw(_("Target table is required"))

	merge = cint(merge)

	if not frappe.db.exists(DOCTYPE_SESSION, session):
		frappe.throw(_("Session {0} does not exist").format(session))

	doc = frappe.get_doc(DOCTYPE_SESSION, session)
	if doc.status != "Open":
		frappe.throw(_("Session {0} is not open").format(session))

	if not frappe.db.exists(DOCTYPE_TABLE, target_table):
		frappe.throw(_("Table {0} does not exist").format(target_table))

	if frappe.db.get_value(DOCTYPE_TABLE, target_table, "disabled"):
		frappe.throw(_("Table {0} is disabled").format(target_table))

	source_table = doc.table
	if source_table == target_table:
		return {"status": "unchanged", "session": session, "table": target_table}

	destination = frappe.db.get_value(
		DOCTYPE_SESSION,
		{"table": target_table, "status": "Open"},
		["name", "cashier", "guest_count"],
		as_dict=True,
	)

	if destination and not merge:
		return {
			"status": "occupied",
			"session": session,
			"source_table": source_table,
			"target_table": target_table,
			"target_session": destination["name"],
			"target_cashier": destination.get("cashier"),
			"target_guest_count": destination.get("guest_count"),
		}

	if destination:
		return _merge_into_session(doc, destination["name"], source_table, target_table)

	return _move_to_free_table(doc, source_table, target_table)


def _move_to_free_table(doc, source_table, target_table):
	"""Move a session and its open order onto an empty table."""
	doc.table = target_table
	doc.save(ignore_permissions=True)

	# Orders carry their own `table`; without this they keep pointing at the table
	# the guests already left. Every check moves, not just one.
	orders = [row["name"] for row in _get_open_orders(doc.name)]
	for order in orders:
		frappe.db.set_value(DOCTYPE_ORDER, order, "table", target_table, update_modified=False)

	_log_move(doc.name, source_table, target_table, order=", ".join(orders) or None)

	return {
		"status": "moved",
		"session": doc.name,
		"order": orders[0] if len(orders) == 1 else None,
		"orders": orders,
		"source_table": source_table,
		"target_table": target_table,
	}


def _merge_into_session(source_doc, target_session, source_table, target_table):
	"""
	Fold a session's order into another table's order (joining tables).

	The destination keeps its own order and identity; the source is closed. Guest
	counts are added together, since the parties are now sitting as one.
	"""
	# Which of several checks a merge should fold into is genuinely ambiguous, and
	# guessing would combine the wrong guests' bills. Settle or unsplit first.
	source_open = _get_open_orders(source_doc.name)
	target_open = _get_open_orders(target_session)
	if len(source_open) > 1 or len(target_open) > 1:
		frappe.throw(
			_("A table whose bill is split into separate checks cannot be joined. Settle its checks first."),
			title=_("Bill Is Split"),
		)

	source_order = source_open[0]["name"] if source_open else None
	target_order = target_open[0]["name"] if target_open else None

	moved_lines = 0

	if source_order:
		src = frappe.get_doc(DOCTYPE_ORDER, source_order)

		if target_order:
			tgt = frappe.get_doc(DOCTYPE_ORDER, target_order)
		else:
			# Destination seated but yet to order - it becomes the merged order
			tgt = frappe.new_doc(DOCTYPE_ORDER)
			tgt.table_session = target_session
			tgt.table = target_table
			tgt.pos_profile = src.pos_profile
			tgt.pos_opening_shift = src.pos_opening_shift
			tgt.cashier = src.cashier
			tgt.status = "Open"

		for row in src.items:
			tgt.append("items", {
				"item_code": row.item_code,
				"item_name": row.item_name,
				"qty": row.qty,
				"uom": row.uom,
				"rate": row.rate,
				"amount": row.amount,
				# Each line keeps the waiter who rang it, across the merge
				"added_by": row.added_by,
			})
			moved_lines += 1

		tgt.last_order_by = frappe.session.user
		tgt.flags.ignore_permissions = True
		tgt.save()
		target_order = tgt.name

		# The source order's lines now live on the destination; leaving it Open
		# would double-count the table on the dashboard.
		src.status = "Cancelled"
		src.flags.ignore_permissions = True
		src.save()

	# Both parties are now one table
	target_guests = cint(frappe.db.get_value(DOCTYPE_SESSION, target_session, "guest_count"))
	frappe.db.set_value(
		DOCTYPE_SESSION,
		target_session,
		"guest_count",
		target_guests + cint(source_doc.guest_count),
		update_modified=False,
	)

	source_doc.status = "Closed"
	source_doc.closed_at = now()
	source_doc.save(ignore_permissions=True)

	_log_move(
		target_session, source_table, target_table, order=target_order, merged_from=source_doc.name
	)

	return {
		"status": "merged",
		"session": target_session,
		"closed_session": source_doc.name,
		"order": target_order,
		"source_table": source_table,
		"target_table": target_table,
		"moved_lines": moved_lines,
	}


def _log_move(session, source_table, target_table, order=None, merged_from=None):
	"""
	Leave the move on the session's timeline.

	A comment rather than new fields: moves are occasional, and the timeline
	already carries who did it and when, which is what an audit needs.
	"""
	try:
		if merged_from:
			text = _("Table {0} merged into table {1} (from session {2}) by {3}").format(
				source_table, target_table, merged_from, frappe.session.user
			)
		else:
			text = _("Order moved from table {0} to table {1} by {2}").format(
				source_table, target_table, frappe.session.user
			)
		if order:
			text += f" — {order}"

		frappe.get_doc(DOCTYPE_SESSION, session).add_comment("Info", text)
	except Exception:
		# An audit note must never fail the move itself
		frappe.log_error(frappe.get_traceback(), "POS Table Move Log")


@frappe.whitelist()
def get_tables_summary(pos_profile=None):
	"""
	Headline counts for the dashboard header.

	Returns:
		dict: open_tables, guests, tables_with_order, tables_without_order,
			total_amount, warning_tables, late_tables
	"""
	data = get_open_tables(pos_profile=pos_profile)
	tables = data["tables"]

	return {
		"open_tables": len(tables),
		"guests": sum(cint(t["guest_count"]) for t in tables),
		"tables_with_order": sum(1 for t in tables if t["has_order"]),
		"tables_without_order": sum(1 for t in tables if not t["has_order"]),
		"total_amount": sum(flt(t["total_amount"]) for t in tables),
		"warning_tables": sum(1 for t in tables if t["idle_state"] == "warning"),
		"late_tables": sum(1 for t in tables if t["idle_state"] == "late"),
		"thresholds": data["thresholds"],
		"server_now": data["server_now"],
	}
