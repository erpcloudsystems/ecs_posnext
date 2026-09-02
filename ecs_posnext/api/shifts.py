# -*- coding: utf-8 -*-
# Copyright (c) 2024, POS Next and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe import _
from frappe.utils import convert_utc_to_system_timezone, get_datetime, nowdate, nowtime
from ecs_posnext.api.utilities import get_wallet_payment_modes


@frappe.whitelist()
def get_opening_dialog_data():
	"""Get data required for opening shift dialog"""
	data = {}

	# Get POS Profiles where current user is defined in POS Profile User table
	pos_profiles_data = frappe.db.sql(
		"""
		SELECT DISTINCT p.name, p.company, p.currency, p.warehouse, p.selling_price_list
		FROM `tabPOS Profile` p
		INNER JOIN `tabPOS Profile User` u ON u.parent = p.name
		WHERE p.disabled = 0 AND u.user = %s
		ORDER BY p.name
		""",
		frappe.session.user,
		as_dict=1,
	)

	data["pos_profiles_data"] = pos_profiles_data

	# Derive companies from accessible POS Profiles
	company_names = []
	for profile in pos_profiles_data:
		if profile.company and profile.company not in company_names:
			company_names.append(profile.company)
	data["companies"] = [{"name": c} for c in company_names]

	# Get payment methods for POS profiles (exclude wallet payment methods)
	pos_profiles_list = [p.name for p in pos_profiles_data]

	if pos_profiles_list:
		# Exclude wallet payment modes from opening balance
		wallet_modes = get_wallet_payment_modes()

		payment_filters = {"parent": ["in", pos_profiles_list]}
		if wallet_modes:
			payment_filters["mode_of_payment"] = ["not in", wallet_modes]

		data["payments_method"] = frappe.get_list(
			"POS Payment Method",
			filters=payment_filters,
			fields=["*"],
			limit_page_length=0,
			order_by="parent",
			ignore_permissions=True,
		)

		# Set currency from pos profile
		for mode in data["payments_method"]:
			mode["currency"] = frappe.get_cached_value("POS Profile", mode["parent"], "currency")
	else:
		data["payments_method"] = []

	return data


@frappe.whitelist()
def check_opening_shift(user=None):
	"""Check if user has an open shift"""
	if not user:
		user = frappe.session.user

	open_shifts = frappe.db.get_all(
		"POS Opening Shift",
		filters={
			"user": user,
			"pos_closing_shift": ["is", "not set"],
			"docstatus": 1,
			"status": "Open",
		},
		fields=["name", "pos_profile", "period_start_date"],
		order_by="period_start_date desc",
	)

	if not open_shifts:
		return None

	# Get the latest open shift
	shift_data = open_shifts[0]
	data = {}
	data["pos_opening_shift"] = frappe.get_doc("POS Opening Shift", shift_data["name"])
	data["pos_profile"] = frappe.get_doc("POS Profile", shift_data["pos_profile"])
	data["company"] = frappe.get_doc("Company", data["pos_profile"].company)
	# Include server timestamp so frontend can compute shift duration
	# without timezone mismatch (period_start_date is in server timezone)
	data["server_now"] = str(get_datetime())

	return data


def _get_last_open_shift(pos_profile=None, user=None):
	"""Return the name of the latest POS Opening Shift that is still Open.

	Prefers the current user's own open shift; falls back to the latest open
	shift of the given POS Profile so the lookup never spans other profiles.
	"""
	base_filters = {
		"pos_closing_shift": ["is", "not set"],
		"docstatus": 1,
		"status": "Open",
	}
	if pos_profile:
		base_filters["pos_profile"] = pos_profile

	for extra in ({"user": user or frappe.session.user}, {}):
		shifts = frappe.db.get_all(
			"POS Opening Shift",
			filters={**base_filters, **extra},
			fields=["name"],
			order_by="period_start_date desc",
			limit=1,
		)
		if shifts:
			return shifts[0].name

	return None


@frappe.whitelist()
def get_shift_invoices(pos_profile=None, pos_opening_shift=None, limit=10):
	"""Return the most recent Sales Invoices of the last open POS Opening Shift.

	Used by the POS invoice history for non-admin users, which must never show
	invoices from other shifts. When no open shift can be resolved, an empty
	list is returned rather than falling back to an unscoped query.
	"""
	limit = frappe.utils.cint(limit) or 10

	shift = pos_opening_shift or _get_last_open_shift(pos_profile)
	if not shift:
		return {"pos_opening_shift": None, "invoices": []}

	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"is_pos": 1, "posa_pos_opening_shift": shift},
		fields=[
			"name",
			"customer",
			"customer_name",
			"posting_date",
			"posting_time",
			"grand_total",
			"status",
			"docstatus",
			"is_return",
		],
		order_by="creation desc",
		limit=limit,
	)

	return {"pos_opening_shift": shift, "invoices": invoices}


def _to_system_timezone(timestamp):
	"""Parse a client-supplied timestamp into a naive system-timezone datetime.

	The POS sends offline timestamps as ``new Date().toISOString()``, i.e. UTC
	with a trailing ``Z``. Datetime columns are naive and hold system-timezone
	values, so storing the parsed value as-is shifted every offline timestamp by
	the UTC offset — on a ``Africa/Cairo`` site that is 2-3 hours, which also
	lands a shift opened just after midnight on the previous calendar day.
	Timestamps that carry no offset are already system-local and pass through.
	"""
	parsed = get_datetime(timestamp)
	if parsed is None or parsed.tzinfo is None:
		return parsed

	return convert_utc_to_system_timezone(parsed).replace(tzinfo=None)


@frappe.whitelist()
def create_opening_shift(pos_profile, company, balance_details, op_id=None, period_start_date=None):
	"""Create a new POS Opening Shift.

	Supports offline creation: when an ``op_id`` is supplied (from the offline
	operation queue) creation is idempotent — re-syncing the same op returns the
	already-created shift instead of raising a duplicate. ``period_start_date``
	lets the client pass the real offline start time.
	"""
	from ecs_posnext.api.offline_ops import create_op_sync_record, ensure_op_once

	balance_details = json.loads(balance_details) if isinstance(balance_details, str) else balance_details

	# Idempotency: this offline op already produced a shift — return it as-is
	if op_id:
		existing_name = ensure_op_once(op_id, "open_shift")
		if existing_name and frappe.db.exists("POS Opening Shift", existing_name):
			doc = frappe.get_doc("POS Opening Shift", existing_name)
			return {
				"name": doc.name,
				"pos_opening_shift": doc.as_dict(),
				"pos_profile": frappe.get_doc("POS Profile", doc.pos_profile),
				"company": frappe.get_doc("Company", doc.company),
			}

	# Check if user already has an open shift
	existing_shift = check_opening_shift(frappe.session.user)
	if existing_shift:
		frappe.throw(_("You already have an open shift: {0}").format(existing_shift["pos_opening_shift"].name))

	new_pos_opening = frappe.get_doc(
		{
			"doctype": "POS Opening Shift",
			"period_start_date": _to_system_timezone(period_start_date)
			if period_start_date
			else get_datetime(),
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"user": frappe.session.user,
			"pos_profile": pos_profile,
			"company": company,
			"status": "Open",
		}
	)

	# Add balance details - map opening_amount to amount
	formatted_balance_details = []
	for detail in balance_details:
		formatted_balance_details.append({
			"mode_of_payment": detail.get("mode_of_payment"),
			"amount": detail.get("opening_amount", 0)
		})

	new_pos_opening.set("balance_details", formatted_balance_details)
	new_pos_opening.insert(ignore_permissions=True)
	new_pos_opening.submit()

	# Record the offline op so re-syncs are idempotent
	if op_id:
		create_op_sync_record(op_id, "open_shift", "POS Opening Shift", new_pos_opening.name)

	data = {}
	data["name"] = new_pos_opening.name
	data["pos_opening_shift"] = new_pos_opening.as_dict()
	data["pos_profile"] = frappe.get_doc("POS Profile", pos_profile)
	data["company"] = frappe.get_doc("Company", company)

	return data


@frappe.whitelist()
def get_closing_shift_data(opening_shift):
	"""Get data for closing shift"""
	from ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift import make_closing_shift_from_opening

	try:
		# Get the opening shift document
		opening_shift_doc = frappe.get_doc("POS Opening Shift", opening_shift)

		# Convert to dict with proper datetime serialization
		opening_shift_dict = opening_shift_doc.as_dict()
		opening_shift_json = json.dumps(opening_shift_dict, default=str)

		# Create closing shift from opening shift (returns a dict)
		closing_data = make_closing_shift_from_opening(opening_shift_json)

		# Ensure datetime values are JSON serializable
		return json.loads(json.dumps(closing_data, default=str))
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Closing Shift Data Error")
		frappe.throw(_("Error getting closing shift data: {0}").format(str(e)))


@frappe.whitelist()
def submit_closing_shift(closing_shift, op_id=None):
	"""Submit closing shift.

	Supports offline closing: with an ``op_id`` from the offline operation queue,
	submission is idempotent — re-syncing returns the already-created closing.
	The referenced opening shift must exist (offline temp names are resolved to
	real names client-side before this is called).
	"""
	from ecs_posnext.api.offline_ops import create_op_sync_record, ensure_op_once
	from ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift import submit_closing_shift as submit_shift

	# Idempotency: this offline op already produced a closing — return it as-is
	if op_id:
		existing_name = ensure_op_once(op_id, "close_shift")
		if existing_name:
			return {"name": existing_name, "status": "success"}

	try:
		# closing_shift is already a JSON string from frontend
		# If it's a dict, convert to JSON string
		if isinstance(closing_shift, dict):
			closing_shift = json.dumps(closing_shift)

		# Guard: the opening shift must exist on the server. When syncing offline
		# ops, the open_shift op is flushed first; if it hasn't landed yet, signal
		# an in-progress state so the client retries instead of failing hard.
		parsed = json.loads(closing_shift) if isinstance(closing_shift, str) else closing_shift
		opening = parsed.get("pos_opening_shift") if isinstance(parsed, dict) else None
		if opening and not frappe.db.exists("POS Opening Shift", opening):
			frappe.throw(_("SYNC_IN_PROGRESS: opening shift {0} not found yet").format(opening))

		result = submit_shift(closing_shift)

		if op_id:
			create_op_sync_record(op_id, "close_shift", "POS Closing Shift", result)

		return {"name": result, "status": "success"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Submit Closing Shift Error")
		frappe.throw(_("Error submitting closing shift: {0}").format(str(e)))
