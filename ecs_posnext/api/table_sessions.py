# -*- coding: utf-8 -*-
# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""
Table Session API

Backs the "select table + guest count before adding items" flow. A POS Table
Session is opened before the cart accepts any item and carries the table/guest
context for the whole order.
"""

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import cint, now

DOCTYPE_SESSION = "POS Table Session"
DOCTYPE_TABLE = "Table"


def _has_pos_profile_access(pos_profile):
	"""Same access rule the rest of the app uses: profile membership or doctype perms."""
	if not pos_profile:
		return True

	if frappe.db.exists("POS Profile User", {"parent": pos_profile, "user": frappe.session.user}):
		return True

	return frappe.has_permission("POS Profile", "read", pos_profile)


@frappe.whitelist()
def get_tables(pos_profile=None, search_term=None, limit=50):
	"""
	List selectable tables, each flagged with its current open session (if any).

	The `occupied` flag lets the UI show which tables already have an order in
	progress, and `session` lets it resume that order instead of starting a
	second one for the same table.

	Args:
		pos_profile: Used for access checking only - tables are not profile-scoped.
		search_term: Optional filter matching anywhere in the table number or area.
		limit: Max rows to return (capped at 200).

	Returns:
		list[dict]: table_number, area, room, seating_capacity, occupied, session,
			session_guest_count
	"""
	if not _has_pos_profile_access(pos_profile):
		frappe.throw(_("You don't have access to this POS Profile"), frappe.PermissionError)

	limit = max(1, min(cint(limit) or 50, 200))

	Table = DocType(DOCTYPE_TABLE)
	query = (
		frappe.qb.from_(Table)
		.select(
			Table.name,
			Table.table_number,
			Table.area,
			Table.room,
			Table.seating_capacity,
		)
		.where(Table.disabled == 0)
		.orderby(Table.table_number)
		.limit(limit)
	)

	if search_term:
		term = f"%{search_term.strip()}%"
		query = query.where(Table.table_number.like(term) | Table.area.like(term))

	tables = query.run(as_dict=True)

	if not tables:
		return []

	# One query for every open session, rather than one per table
	open_sessions = frappe.get_all(
		DOCTYPE_SESSION,
		filters={"status": "Open", "table": ["in", [t["name"] for t in tables]]},
		fields=["name", "table", "guest_count"],
	)
	sessions_by_table = {s["table"]: s for s in open_sessions}

	for table in tables:
		session = sessions_by_table.get(table["name"])
		table["occupied"] = 1 if session else 0
		table["session"] = session["name"] if session else None
		table["session_guest_count"] = session["guest_count"] if session else None

	return tables


@frappe.whitelist()
def start_table_session(table, guest_count, pos_profile=None, pos_opening_shift=None):
	"""
	Open a session for a table, or resume the one already open for it.

	Resuming rather than throwing keeps the cashier moving: picking an occupied
	table is a normal way to get back to that table's order.

	Args:
		table: Table name.
		guest_count: Number of guests seated (must be >= 1).
		pos_profile: Active POS Profile.
		pos_opening_shift: Active POS Opening Shift.

	Returns:
		dict: session details plus `resumed` telling the UI which case it got.
	"""
	if not table:
		frappe.throw(_("Table is required"))

	guest_count = cint(guest_count)
	if guest_count < 1:
		frappe.throw(_("Guest Count must be at least 1"))

	if not _has_pos_profile_access(pos_profile):
		frappe.throw(_("You don't have access to this POS Profile"), frappe.PermissionError)

	if not frappe.db.exists(DOCTYPE_TABLE, table):
		frappe.throw(_("Table {0} does not exist").format(table))

	existing = frappe.db.get_value(
		DOCTYPE_SESSION,
		{"table": table, "status": "Open"},
		["name", "guest_count", "pos_profile", "pos_opening_shift", "opened_at"],
		as_dict=True,
	)

	if existing:
		# Seating changed on an order already in progress - keep the session,
		# update the head count.
		if existing["guest_count"] != guest_count:
			frappe.db.set_value(DOCTYPE_SESSION, existing["name"], "guest_count", guest_count)
			existing["guest_count"] = guest_count

		return {
			"name": existing["name"],
			"table": table,
			"guest_count": existing["guest_count"],
			"status": "Open",
			"opened_at": existing["opened_at"],
			"resumed": True,
		}

	doc = frappe.new_doc(DOCTYPE_SESSION)
	doc.table = table
	doc.guest_count = guest_count
	doc.status = "Open"
	doc.pos_profile = pos_profile
	doc.pos_opening_shift = pos_opening_shift
	doc.insert(ignore_permissions=True)

	return {
		"name": doc.name,
		"table": doc.table,
		"guest_count": doc.guest_count,
		"status": doc.status,
		"opened_at": doc.opened_at,
		"resumed": False,
	}


@frappe.whitelist()
def update_table_session(session, table=None, guest_count=None):
	"""
	Change the table and/or guest count on an open session.

	Backs the header chip, so a cashier can fix a wrong table or add a guest
	mid-order without abandoning the cart.

	Args:
		session: POS Table Session name.
		table: New table (moves the order to another table).
		guest_count: New guest count.

	Returns:
		dict: updated session details.
	"""
	if not session:
		frappe.throw(_("Session is required"))

	doc = frappe.get_doc(DOCTYPE_SESSION, session)

	if doc.status != "Open":
		frappe.throw(_("Session {0} is not open").format(session))

	moved_from = None
	if table and table != doc.table:
		if not frappe.db.exists(DOCTYPE_TABLE, table):
			frappe.throw(_("Table {0} does not exist").format(table))
		moved_from = doc.table
		doc.table = table

	if guest_count is not None:
		guest_count = cint(guest_count)
		if guest_count < 1:
			frappe.throw(_("Guest Count must be at least 1"))
		doc.guest_count = guest_count

	doc.save(ignore_permissions=True)

	# A table change here is a move, so the session's open order has to follow it.
	# Without this the order keeps pointing at the table the guests left, and the
	# dashboard (which reads the session) disagrees with the order record.
	if moved_from:
		from ecs_posnext.api.table_orders import DOCTYPE_ORDER, _get_open_orders, _log_move

		# Every check on the table moves with it, not just one
		orders = [row["name"] for row in _get_open_orders(doc.name)]
		for order in orders:
			frappe.db.set_value(
				DOCTYPE_ORDER, order, "table", doc.table, update_modified=False
			)
		_log_move(doc.name, moved_from, doc.table, order=", ".join(orders) or None)

	return {
		"name": doc.name,
		"table": doc.table,
		"guest_count": doc.guest_count,
		"status": doc.status,
		"opened_at": doc.opened_at,
		"moved_from": moved_from,
	}


@frappe.whitelist()
def close_table_session(session, sales_invoice=None, external_reference=None):
	"""
	Close a session once its order is settled.

	Args:
		session: POS Table Session name.
		sales_invoice: Optional Sales Invoice the order became.
		external_reference: Optional reference from the external system it was
			posted to (e.g. Protel).

	Returns:
		dict: {name, status}
	"""
	if not session:
		frappe.throw(_("Session is required"))

	if not frappe.db.exists(DOCTYPE_SESSION, session):
		# Nothing to close - treat as already done so the caller isn't blocked
		# from finishing a sale over a session that was cleaned up elsewhere.
		return {"name": session, "status": "Missing"}

	doc = frappe.get_doc(DOCTYPE_SESSION, session)

	# A split table is only finished when every check has been paid. Closing early
	# would free the table and hide the unpaid checks from the dashboard.
	from ecs_posnext.api.table_orders import _get_open_orders

	remaining = _get_open_orders(session)
	if remaining:
		return {
			"name": doc.name,
			"status": doc.status,
			"remaining_open_checks": len(remaining),
			"closed": False,
		}

	if doc.status == "Open":
		doc.close_session(sales_invoice=sales_invoice, external_reference=external_reference)

	return {"name": doc.name, "status": doc.status, "remaining_open_checks": 0, "closed": True}


@frappe.whitelist()
def cancel_table_session(session):
	"""
	Cancel a session that was opened by mistake, freeing its table.

	Args:
		session: POS Table Session name.

	Returns:
		dict: {name, status}
	"""
	if not session:
		frappe.throw(_("Session is required"))

	if not frappe.db.exists(DOCTYPE_SESSION, session):
		return {"name": session, "status": "Missing"}

	doc = frappe.get_doc(DOCTYPE_SESSION, session)

	if doc.status == "Open":
		doc.status = "Cancelled"
		doc.closed_at = now()
		doc.save(ignore_permissions=True)

	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def get_open_table_sessions(pos_profile=None):
	"""
	All currently open sessions, newest first.

	Args:
		pos_profile: Optional filter to one POS Profile.

	Returns:
		list[dict]: name, table, guest_count, opened_at, cashier, pos_profile
	"""
	if not _has_pos_profile_access(pos_profile):
		frappe.throw(_("You don't have access to this POS Profile"), frappe.PermissionError)

	filters = {"status": "Open"}
	if pos_profile:
		filters["pos_profile"] = pos_profile

	return frappe.get_all(
		DOCTYPE_SESSION,
		filters=filters,
		fields=["name", "table", "guest_count", "opened_at", "cashier", "pos_profile"],
		order_by="opened_at desc",
	)


@frappe.whitelist()
def get_table_session(session):
	"""
	Fetch one session, used to re-hydrate table/guest context on a resumed draft.

	Args:
		session: POS Table Session name.

	Returns:
		dict|None: session details, or None if it no longer exists.
	"""
	if not session or not frappe.db.exists(DOCTYPE_SESSION, session):
		return None

	return frappe.db.get_value(
		DOCTYPE_SESSION,
		session,
		["name", "table", "guest_count", "status", "opened_at", "pos_profile", "pos_opening_shift"],
		as_dict=True,
	)
