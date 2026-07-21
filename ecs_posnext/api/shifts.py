# -*- coding: utf-8 -*-
# Copyright (c) 2024, POS Next and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe import _
from frappe.utils import nowdate, nowtime, get_datetime
from ecs_posnext.api.utilities import get_wallet_payment_modes

SUPERVISOR_ROLES = {
	"POSNext Supervisor",
	"POSNext Branch Manager",
	"POSNext Operations Manager",
	"Sales Manager",
	"System Manager",
	"Administrator",
}


def _is_supervisor(user=None):
	return bool(set(frappe.get_roles(user or frappe.session.user)) & SUPERVISOR_ROLES)


def _enforce_supervisor_open(pos_profile, user):
	"""Block CREATING a shift from scratch when the profile requires supervisor opening.

	A cashier can still START (submit) a shift a supervisor prepared for them — that
	path is checked by the caller before this runs.
	"""
	if not pos_profile:
		return
	if not frappe.db.get_value("POS Profile", pos_profile, "custom_supervisor_opens_cashier_shifts"):
		return
	if not _is_supervisor(user):
		frappe.throw(
			_(
				"You cannot open a shift yourself. Ask your supervisor to prepare your shift, "
				"then you can start it."
			),
			title=_("Supervisor Required"),
		)


@frappe.whitelist()
def get_opening_dialog_data(pos_profile=None):
	"""Get data required for opening shift dialog"""
	data = {}

	if pos_profile:
		pos_profiles_data = [frappe.db.get_value("POS Profile", pos_profile, ["name", "company", "currency", "warehouse", "selling_price_list"], as_dict=1)]
	else:
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
		# Check for prepared shifts by supervisor (Draft)
		prepared_shifts = frappe.db.get_all(
			"POS Opening Shift",
			filters={
				"user": user,
				"docstatus": 0,
				"is_prepared_by_supervisor": 1,
			},
			fields=["name", "pos_profile", "period_start_date"],
			order_by="period_start_date desc",
		)
		if prepared_shifts:
			shift_data = prepared_shifts[0]
			data = {}
			data["pos_opening_shift"] = frappe.get_doc("POS Opening Shift", shift_data["name"])
			data["pos_profile"] = frappe.get_doc("POS Profile", shift_data["pos_profile"])
			data["company"] = frappe.get_doc("Company", data["pos_profile"].company)
			data["server_now"] = str(get_datetime())
			data["is_prepared"] = True

			employee = frappe.db.get_value("Employee", {"user_id": user}, ["name", "employee_name"], as_dict=1)
			if employee:
				data["employee_code"] = employee.name
				data["employee_name"] = employee.employee_name

			return data

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

	# Get employee info
	employee = frappe.db.get_value("Employee", {"user_id": user}, ["name", "employee_name"], as_dict=1)
	if employee:
		data["employee_code"] = employee.name
		data["employee_name"] = employee.employee_name

	return data


@frappe.whitelist()
def create_opening_shift(pos_profile, company, balance_details):
	"""Create a new POS Opening Shift"""
	balance_details = json.loads(balance_details) if isinstance(balance_details, str) else balance_details

	# Check if user already has an open or prepared shift
	existing_shift_data = check_opening_shift(frappe.session.user)

	# "Supervisor opens cashier shifts": a cashier MAY submit (start) a shift that a
	# supervisor prepared for them, but MAY NOT create one from scratch. Only the
	# create path is gated. The server-side flag lets internal flows (COD auto-shift)
	# through — clients cannot set frappe.flags.
	is_prepared_by_supervisor = bool(existing_shift_data and existing_shift_data.get("is_prepared"))
	if not frappe.flags.get("pos_internal_shift") and not is_prepared_by_supervisor:
		_enforce_supervisor_open(pos_profile, frappe.session.user)
	
	if existing_shift_data and not existing_shift_data.get("is_prepared"):
		frappe.throw(_("You already have an open shift: {0}").format(existing_shift_data["pos_opening_shift"].name))

	if existing_shift_data and existing_shift_data.get("is_prepared"):
		new_pos_opening = frappe.get_doc("POS Opening Shift", existing_shift_data["pos_opening_shift"].name)
		# Update profile and company if they changed
		new_pos_opening.pos_profile = pos_profile
		new_pos_opening.company = company
		# Update period start date to now
		new_pos_opening.period_start_date = get_datetime()
		new_pos_opening.posting_date = nowdate()
		new_pos_opening.posting_time = nowtime()
	else:
		new_pos_opening = frappe.get_doc(
			{
				"doctype": "POS Opening Shift",
				"period_start_date": get_datetime(),
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
	
	if new_pos_opening.name:
		new_pos_opening.save(ignore_permissions=True)
	else:
		new_pos_opening.insert(ignore_permissions=True)
		
	new_pos_opening.submit()

	data = {}
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
def submit_closing_shift(closing_shift):
	"""Submit closing shift"""
	from ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift import submit_closing_shift as submit_shift

	try:
		# closing_shift is already a JSON string from frontend
		# If it's a dict, convert to JSON string
		if isinstance(closing_shift, dict):
			closing_shift = json.dumps(closing_shift)

		result = submit_shift(closing_shift)
		return {"name": result, "status": "success"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Submit Closing Shift Error")
		frappe.throw(_("Error submitting closing shift: {0}").format(str(e)))

@frappe.whitelist()
def supervisor_open_shift_for_cashier(cashier, pos_profile, balance_details, company=None):
	"""A supervisor fully opens (submits) a shift on behalf of a cashier.

	The cashier then just logs in and sells — they never open a shift themselves.
	Triggers the business-day hook, so the POS Business Day + Cashier Shift are created.
	"""
	if not _is_supervisor(frappe.session.user):
		frappe.throw(_("Only a supervisor can open a shift for a cashier."))

	balance_details = json.loads(balance_details) if isinstance(balance_details, str) else balance_details

	existing = check_opening_shift(cashier)
	if existing:
		shift = existing["pos_opening_shift"]
		name = shift.name if hasattr(shift, "name") else shift.get("name")
		frappe.throw(_("Cashier {0} already has an active shift: {1}").format(cashier, name))

	company = company or frappe.db.get_value("POS Profile", pos_profile, "company")
	formatted = [
		{"mode_of_payment": d.get("mode_of_payment"), "amount": d.get("opening_amount", d.get("amount", 0))}
		for d in balance_details
	]

	doc = frappe.get_doc(
		{
			"doctype": "POS Opening Shift",
			"period_start_date": get_datetime(),
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"user": cashier,
			"pos_profile": pos_profile,
			"company": company,
			"status": "Open",
			"balance_details": formatted,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()  # fires sync_cashier_shift_on_opening -> creates Business Day + Cashier Shift

	from ecs_posnext.api.business_day import log_pos_event

	log_pos_event(
		action="Opening Shift",
		reference_doctype="POS Opening Shift",
		reference_name=doc.name,
		pos_profile=pos_profile,
		new_value="Opened for {0} by supervisor {1}".format(cashier, frappe.session.user),
	)
	return {"pos_opening_shift": doc.as_dict()}


@frappe.whitelist()
def prepare_opening_shift(user, pos_profile, cash_amount):
	"""Prepare a new POS Opening Shift by Supervisor"""
	# Only a supervisor may prepare a shift. Without this, a cashier could prepare
	# their own shift and then start it, defeating "supervisor opens cashier shifts".
	if not _is_supervisor(frappe.session.user):
		frappe.throw(
			_("Only a supervisor can prepare a cashier's shift."),
			title=_("Supervisor Required"),
		)

	# Check if user already has an open or prepared shift
	existing_shift = check_opening_shift(user)
	if existing_shift:
		if existing_shift.get("is_prepared"):
			frappe.throw(_("User already has a prepared shift: {0}").format(existing_shift["pos_opening_shift"].name))
		else:
			frappe.throw(_("User already has an open shift: {0}").format(existing_shift["pos_opening_shift"].name))

	pos_profile_doc = frappe.get_doc("POS Profile", pos_profile)
	
	new_pos_opening = frappe.get_doc(
		{
			"doctype": "POS Opening Shift",
			"period_start_date": get_datetime(),
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"user": user,
			"pos_profile": pos_profile,
			"company": pos_profile_doc.company,
			"is_prepared_by_supervisor": 1,
			"status": "Draft",
		}
	)

	# Find Cash payment method
	cash_payment_method = None
	for method in pos_profile_doc.payments:
		mode_type = frappe.db.get_value("Mode of Payment", method.mode_of_payment, "type")
		if mode_type == "Cash" or "Cash" in method.mode_of_payment:
			cash_payment_method = method.mode_of_payment
			break
	
	if not cash_payment_method and pos_profile_doc.payments:
		cash_payment_method = pos_profile_doc.payments[0].mode_of_payment

	if cash_payment_method:
		new_pos_opening.append("balance_details", {
			"mode_of_payment": cash_payment_method,
			"amount": cash_amount
		})

	new_pos_opening.insert(ignore_permissions=True)

	return new_pos_opening.name

@frappe.whitelist()
def auto_process_payment_with_temp_shift(invoice, pos_profile_name, payment_methods_json):
	"""Automatically create a shift, process a payment, and close the shift."""
	from ecs_posnext.api.shifts import create_opening_shift
	from ecs_posnext.api.payment_entry import create_pos_payment_entry
	from ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift import make_closing_shift_from_opening, submit_closing_shift

	pos_profile = frappe.get_doc("POS Profile", pos_profile_name)

	# 1. Create Opening Shift (internal flow — bypass the supervisor-open gate)
	default_pay_method = pos_profile.payments[0].mode_of_payment if pos_profile.payments else "Cash"
	balance_details = frappe.as_json([{"mode_of_payment": default_pay_method, "opening_amount": 0}])
	frappe.flags.pos_internal_shift = True
	try:
		shift_data = create_opening_shift(pos_profile.name, pos_profile.company, balance_details)
	finally:
		frappe.flags.pos_internal_shift = False
	opening_shift_name = shift_data["pos_opening_shift"]["name"]

	# 2. Process Payment
	payload = {
		"selected_invoice": invoice,
		"pos_profile": pos_profile.as_dict(),
		"pos_profile_name": pos_profile.name,
		"pos_opening_shift_name": opening_shift_name,
		"payment_methods": frappe.parse_json(payment_methods_json),
		"submit": True
	}
	create_pos_payment_entry(frappe.as_json(payload))

	# 3. Create and Submit Closing Shift
	opening_shift_doc = frappe.get_doc("POS Opening Shift", opening_shift_name)
	opening_shift_json = frappe.as_json(opening_shift_doc.as_dict())
	
	closing_dict = make_closing_shift_from_opening(opening_shift_json)
	
	# Auto-fill closing amounts to match expected amounts to avoid difference
	for row in closing_dict.get("payment_reconciliation", []):
		row["closing_amount"] = row.get("expected_amount", 0)
		row["difference"] = 0

	closing_dict["closing_amount"] = closing_dict.get("expected_amount", 0)
	closing_dict["difference"] = 0
	
	closing_shift_json = frappe.as_json(closing_dict)
	submit_closing_shift(closing_shift_json)

	return "Success"
