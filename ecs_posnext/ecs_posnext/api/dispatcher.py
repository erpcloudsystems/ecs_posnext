import frappe
from frappe import _
from frappe.utils import now_datetime, flt


# ---------------------------------------------------------------------------
# Permission query — Delivery Driver sees only their own assignments
# ---------------------------------------------------------------------------

def get_delivery_assignment_permission_conditions(user):
	# Driver has no direct user link; go through Employee.user_id → Driver.employee
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	driver = frappe.db.get_value("Driver", {"employee": employee}, "name") if employee else None
	if driver:
		return f"`tabDelivery Assignment`.driver = {frappe.db.escape(driver)}"
	return None


# ---------------------------------------------------------------------------
# Dispatcher desk API (called from Vue page)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_branches():
	"""Return all branches for shift opening selection."""
	return frappe.get_list("Branch", fields=["name"], order_by="name asc")


@frappe.whitelist()
def get_pos_profiles():
	"""Return POS profiles available for shift opening."""
	return frappe.get_list(
		"POS Profile",
		fields=["name", "company", "branch"],
		order_by="name asc",
	)


@frappe.whitelist()
def open_dispatcher_shift(pos_profile):
	"""Create and submit a POS Opening Shift for the dispatcher user."""
	user = frappe.session.user

	existing = frappe.db.get_value(
		"POS Opening Shift",
		{"user": user, "status": "Open", "docstatus": 1},
		"name",
	)
	if existing:
		frappe.throw(_("You already have an open shift: {0}").format(existing))

	company = frappe.db.get_value("POS Profile", pos_profile, "company")
	if not company:
		frappe.throw(_("POS Profile {0} not found").format(pos_profile))

	payment_methods = frappe.get_all(
		"POS Payment Method",
		filters={"parent": pos_profile},
		fields=["mode_of_payment"],
	)
	if not payment_methods:
		payment_methods = [{"mode_of_payment": "Cash"}]

	shift = frappe.get_doc({
		"doctype": "POS Opening Shift",
		"pos_profile": pos_profile,
		"user": user,
		"company": company,
		"period_start_date": frappe.utils.now_datetime(),
		"posting_date": frappe.utils.today(),
		"balance_details": [
			{"mode_of_payment": pm["mode_of_payment"], "amount": 0}
			for pm in payment_methods
		],
	})
	shift.insert(ignore_permissions=True)
	shift.submit()

	branch = frappe.db.get_value("POS Profile", pos_profile, "branch") or None
	return {
		"name": shift.name,
		"opening_time": shift.period_start_date,
		"branch": branch,
		"pos_profile": pos_profile,
		"dispatcher": user,
		"max_driver_orders": _get_max_driver_orders(shift.name),
	}


@frappe.whitelist()
def get_open_shift():
	"""Return the current user's open POS Opening Shift for dispatcher use."""
	user = frappe.session.user
	shift = frappe.db.get_value(
		"POS Opening Shift",
		{"user": user, "status": "Open", "docstatus": 1},
		["name", "pos_profile", "period_start_date"],
		as_dict=True,
	)
	if not shift:
		return None
	branch = frappe.db.get_value("POS Profile", shift.pos_profile, "branch") or None
	return {
		"name": shift.name,
		"opening_time": shift.period_start_date,
		"branch": branch,
		"dispatcher": user,
		"max_driver_orders": _get_max_driver_orders(shift.name),
	}


@frappe.whitelist()
def get_unassigned_orders():
	"""
	Return Delivery / Talabat Sales Invoices that are submitted and NOT already assigned.
	Branch is auto-detected from the current user's open POS Opening Shift → POS Profile.
	All orders are shown regardless of KDS status; kds_status and kds_ready fields indicate
	kitchen readiness so the dispatcher can see orders as soon as they are placed.
	"""
	# Auto-detect branch from the current user's open shift
	branch = None
	user = frappe.session.user
	shift = frappe.db.get_value(
		"POS Opening Shift",
		{"user": user, "status": "Open", "docstatus": 1},
		"pos_profile",
	)
	if shift:
		branch = frappe.db.get_value("POS Profile", shift, "branch") or None

	# An order is "still assigned" only while an assignment holds it: in progress
	# (Assigned / Picked Up / Out for Delivery) or already Delivered. A 'Failed' or
	# 'Returned' assignment releases the order back to the pool, so those must NOT count
	# here — otherwise clicking "Return" on an assignment would never bring the order
	# back to the unassigned board for re-dispatch.
	assigned_refs = frappe.db.sql_list(
		"""
		SELECT order_reference FROM `tabDelivery Assignment`
		WHERE order_doctype = 'Sales Invoice'
		  AND status NOT IN ('Failed', 'Returned')
		  AND docstatus != 2
		"""
	)

	filters = {
		"docstatus": 1,
		"custom_order_type": ["in", ["Delivery", "Talabat"]],
		"is_return": 0,  # a returned order is not a delivery to dispatch
	}
	if branch:
		filters["branch"] = branch
	if assigned_refs:
		filters["name"] = ["not in", assigned_refs]

	invoices = frappe.get_all(
		"Sales Invoice",
		filters=filters,
		fields=["name", "customer", "customer_name", "outstanding_amount", "grand_total", "custom_so_type",
				"contact_mobile", "shipping_address_name", "customer_address", "territory",
				"custom_number_order", "custom_order_type", "payment_terms_template",
				"custom_payment_type", "custom_unique_talbat_number", "custom_third_party_referance_number",
				"posting_date", "posting_time"],
		order_by="posting_date desc, posting_time desc",
		limit=200,
	)

	if not invoices:
		return []

	invoice_names = [inv["name"] for inv in invoices]

	# Also drop any order that HAS been returned (a submitted Return points at it) — a
	# returned/rejected order must not be dispatched, even though it is is_return=0.
	returned_originals = set(
		frappe.get_all(
			"Sales Invoice",
			filters={"return_against": ["in", invoice_names], "is_return": 1, "docstatus": 1},
			pluck="return_against",
		)
	)
	if returned_originals:
		invoices = [inv for inv in invoices if inv["name"] not in returned_originals]
		if not invoices:
			return []
		invoice_names = [inv["name"] for inv in invoices]

	# Attach the LATEST return-request state per order so the board can disable a card
	# while a return is Pending, or re-enable it (with the reject reason) once Rejected.
	# Approved requests aren't handled here — a submitted credit note already dropped the
	# order above via `returned_originals`.
	rr_fields = ["sales_invoice", "status", "reason", "creation"]
	if frappe.db.has_column("Delivery Return Request", "reject_reason"):
		rr_fields.append("reject_reason")
	rr_map = {}
	for rr in frappe.get_all(
		"Delivery Return Request",
		filters={"sales_invoice": ["in", invoice_names], "status": ["in", ["Pending", "Rejected"]]},
		fields=rr_fields,
		order_by="creation asc",
	):
		rr_map[rr["sales_invoice"]] = rr  # asc order → last write wins = most recent
	for inv in invoices:
		rr = rr_map.get(inv["name"])
		inv["return_request_status"] = rr["status"] if rr else None
		inv["return_request_reason"] = (rr.get("reason") if rr else None)
		inv["return_reject_reason"] = (rr.get("reject_reason") if rr else None)

	# Fetch KDS status for each invoice
	kds_rows = frappe.db.sql(
		"""
		SELECT sales_invoice, status, ready_time, completed_time, expected_ready_time
		FROM `tabKDS Order`
		WHERE sales_invoice IN %(names)s
		  AND status != 'Cancelled'
		""",
		{"names": invoice_names},
		as_dict=True,
	)
	kds_map = {r.sales_invoice: r for r in kds_rows}

	# Fetch items for each invoice
	item_rows = frappe.db.sql(
		"""
		SELECT parent, item_name, SUM(qty) as qty
		FROM `tabSales Invoice Item`
		WHERE parent IN %(names)s
		GROUP BY parent, item_name
		""",
		{"names": invoice_names},
		as_dict=True,
	)
	items_map = {}
	for r in item_rows:
		items_map.setdefault(r.parent, []).append({"item_name": r.item_name, "qty": flt(r.qty)})

	# Enrich each invoice
	for inv in invoices:
		addr_name = inv.get("shipping_address_name") or inv.get("customer_address")
		if addr_name:
			addr = frappe.db.get_value("Address", addr_name, ["address_line1", "city"], as_dict=True)
			inv["delivery_address"] = f"{addr.address_line1 or ''}, {addr.city or ''}" if addr else ""
		else:
			inv["delivery_address"] = ""
		inv.pop("shipping_address_name", None)
		inv.pop("customer_address", None)

		inv["is_cod"] = flt(inv.get("outstanding_amount", 0)) > 0

		kds_row = kds_map.get(inv["name"])
		kds_status = kds_row["status"] if kds_row else None
		inv["kds_status"] = kds_status or "No KDS"
		# Kitchen is done (ready for dispatch) once the KDS order is Ready or Completed,
		# or when there is no KDS order at all (kitchen not tracked for this order).
		inv["kds_ready"] = (kds_status in ("Ready", "Completed")) if kds_status else True

		# Dispatcher waiting timer starts the moment the kitchen finished.
		# Prefer the actual ready_time, then completed_time, then the expected time.
		# Only set once the order is ready; otherwise no timer is shown yet.
		if inv["kds_ready"]:
			if kds_row and kds_row.get("ready_time"):
				inv["kitchen_ready_at"] = str(kds_row["ready_time"])
			elif kds_row and kds_row.get("completed_time"):
				inv["kitchen_ready_at"] = str(kds_row["completed_time"])
			elif kds_row and kds_row.get("expected_ready_time"):
				inv["kitchen_ready_at"] = str(kds_row["expected_ready_time"])
			else:
				# No KDS record — count from when the order was placed
				inv["kitchen_ready_at"] = str(inv["posting_date"]) + " " + str(inv["posting_time"])
		else:
			inv["kitchen_ready_at"] = None

		inv["items"] = items_map.get(inv["name"], [])

	return invoices


@frappe.whitelist()
def get_live_orders(branch=None):
	"""
	Return all 'live' Sales Invoices from today for the given branch.
	An order stays live until it reaches a terminal state:
	  - Delivery/Talabat : terminal when DA status in (Delivered, Returned, Failed)
	  - Dine In/Pickup   : terminal when KDS status = Completed, or no KDS record exists
	Results sorted by: late orders first, then newest first.
	"""
	from frappe.utils import get_datetime

	# Step 1 — fetch today's submitted invoices for all 4 order types
	filters = {
		"docstatus": 1,
		"posting_date": frappe.utils.today(),
		"custom_order_type": ["in", ["Delivery", "Talabat", "Dine In", "Pickup"]],
	}
	if branch:
		filters["branch"] = branch

	invoices = frappe.get_all(
		"Sales Invoice",
		filters=filters,
		fields=[
			"name", "customer", "customer_name", "grand_total", "outstanding_amount",
			"custom_number_order", "custom_order_type", "contact_mobile",
			"posting_date", "posting_time", "branch", "owner",
		],
		order_by="posting_date desc, posting_time desc",
		limit=500,
	)
	if not invoices:
		return []

	invoice_names = [inv["name"] for inv in invoices]

	# Step 2 — 6 batch queries; no N+1

	# Q1: KDS Order status + timing
	kds_rows = frappe.db.sql(
		"""
		SELECT sales_invoice, status AS kds_status,
		       order_time AS kds_order_time, target_minutes, expected_ready_time
		FROM `tabKDS Order`
		WHERE sales_invoice IN %(names)s AND status != 'Cancelled'
		""",
		{"names": invoice_names}, as_dict=True,
	)
	kds_map = {r.sales_invoice: r for r in kds_rows}

	# Q2: KDS Order Items (for detail modal)
	kds_item_rows = frappe.db.sql(
		"""
		SELECT ko.sales_invoice, koi.item_name, koi.qty, koi.kds_station,
		       koi.station_status, koi.is_component, koi.special_notes,
		       koi.removed_ingredients, koi.combo_group_id
		FROM `tabKDS Order Item` koi
		JOIN `tabKDS Order` ko ON ko.name = koi.parent
		WHERE ko.sales_invoice IN %(names)s AND ko.status != 'Cancelled'
		ORDER BY koi.idx ASC
		""",
		{"names": invoice_names}, as_dict=True,
	)
	kds_items_map = {}
	for r in kds_item_rows:
		kds_items_map.setdefault(r.sales_invoice, []).append(r)

	# Q3: Latest non-cancelled Delivery Assignment per invoice
	da_rows = frappe.db.sql(
		"""
		SELECT da.order_reference, da.name AS assignment_name, da.driver,
		       da.status AS da_status, da.payment_mode,
		       da.amount_to_collect, da.amount_collected,
		       da.delivery_address, da.assigned_time
		FROM `tabDelivery Assignment` da
		INNER JOIN (
		    SELECT order_reference, MAX(creation) AS max_creation
		    FROM `tabDelivery Assignment`
		    WHERE order_reference IN %(names)s
		      AND order_doctype = 'Sales Invoice'
		      AND docstatus != 2
		    GROUP BY order_reference
		) latest ON da.order_reference = latest.order_reference
		        AND da.creation = latest.max_creation
		WHERE da.docstatus != 2
		""",
		{"names": invoice_names}, as_dict=True,
	)
	da_map = {r.order_reference: r for r in da_rows}

	# Enrich driver names in one query
	driver_ids = list({r.driver for r in da_rows if r.driver})
	driver_name_map = {}
	if driver_ids:
		driver_rows = frappe.get_all(
			"Driver", filters={"name": ["in", driver_ids]}, fields=["name", "full_name"]
		)
		driver_name_map = {d["name"]: d["full_name"] for d in driver_rows}

	# Q4: Payment rows from Sales Invoice Payment child table
	payment_rows = frappe.db.sql(
		"""
		SELECT parent, mode_of_payment, amount
		FROM `tabSales Invoice Payment`
		WHERE parent IN %(names)s ORDER BY idx ASC
		""",
		{"names": invoice_names}, as_dict=True,
	)
	payment_map = {}
	for r in payment_rows:
		payment_map.setdefault(r.parent, []).append({"mode_of_payment": r.mode_of_payment, "amount": flt(r.amount)})

	# Q5: Invoice item summary
	item_rows = frappe.db.sql(
		"""
		SELECT parent, item_name, SUM(qty) AS qty
		FROM `tabSales Invoice Item`
		WHERE parent IN %(names)s
		GROUP BY parent, item_name
		""",
		{"names": invoice_names}, as_dict=True,
	)
	items_map = {}
	for r in item_rows:
		items_map.setdefault(r.parent, []).append({"item_name": r.item_name, "qty": flt(r.qty)})

	# Q6: Owner full names
	owner_ids = list({inv["owner"] for inv in invoices})
	user_rows = frappe.get_all("User", filters={"name": ["in", owner_ids]}, fields=["name", "full_name"])
	owner_name_map = {u["name"]: u["full_name"] or u["name"] for u in user_rows}

	# Step 3 — terminal filter + enrich
	live = []
	for inv in invoices:
		kds = kds_map.get(inv["name"])
		da  = da_map.get(inv["name"])
		kds_status = kds["kds_status"] if kds else None
		da_status  = da["da_status"]   if da  else None
		is_delivery = inv["custom_order_type"] in ("Delivery", "Talabat")

		# Skip terminal orders
		if is_delivery:
			if da_status in ("Delivered", "Returned", "Failed"):
				continue
		else:
			# Dine In / Pickup: done when KDS Completed or no KDS record
			if kds_status == "Completed" or kds_status is None:
				continue

		posting_dt = str(inv["posting_date"]) + " " + str(inv["posting_time"])

		inv["unified_status"]    = _compute_unified_status(inv["custom_order_type"], kds_status, da_status)
		inv["kds_status"]        = kds_status or "No KDS"
		inv["kds_order_time"]    = str(kds["kds_order_time"])  if kds and kds.get("kds_order_time") else None
		inv["target_minutes"]    = kds["target_minutes"]  if kds else None
		inv["expected_ready_time"] = str(kds["expected_ready_time"]) if kds and kds.get("expected_ready_time") else None
		inv["kds_items"]         = kds_items_map.get(inv["name"], [])
		inv["da_status"]         = da_status
		inv["driver_name"]       = driver_name_map.get(da["driver"]) if da and da.get("driver") else None
		inv["payment_mode"]      = da.get("payment_mode") if da else None
		inv["amount_to_collect"] = flt(da.get("amount_to_collect", 0)) if da else 0
		inv["delivery_address"]  = da.get("delivery_address") if da else None
		inv["is_cod"]            = flt(inv.get("outstanding_amount", 0)) > 0
		inv["payments"]          = payment_map.get(inv["name"], [])
		inv["items"]             = items_map.get(inv["name"], [])
		inv["owner_name"]        = owner_name_map.get(inv["owner"], inv["owner"])
		inv["posting_datetime"]  = posting_dt
		live.append(inv)

	# Step 4 — sort: late orders first, then newest first
	def _is_late(inv):
		ot = inv.get("kds_order_time") or inv.get("posting_datetime")
		if not ot or not inv.get("target_minutes"):
			return False
		try:
			elapsed_min = (now_datetime() - get_datetime(ot)).total_seconds() / 60
			return elapsed_min > inv["target_minutes"]
		except Exception:
			return False

	def _sort_ts(inv):
		try:
			return get_datetime(inv["posting_datetime"]).timestamp()
		except Exception:
			return 0

	live.sort(key=lambda inv: (0 if _is_late(inv) else 1, -_sort_ts(inv)))
	return live


def _compute_unified_status(order_type, kds_status, da_status):
	"""Map order type + KDS + DA statuses to a single frontend display token."""
	if order_type in ("Delivery", "Talabat") and da_status:
		if da_status in ("Returned", "Failed"):      return "da_problem"
		if da_status == "Out for Delivery":           return "da_out"
		if da_status in ("Assigned", "Picked Up"):   return "da_assigned"
	if kds_status == "Completed": return "kds_completed"
	if kds_status == "Ready":     return "kds_ready"
	if kds_status == "Preparing": return "kds_preparing"
	if kds_status == "Pending":   return "kds_pending"
	return "no_kds"


@frappe.whitelist()
def get_available_drivers(branch=None):
	"""
	Return drivers who can still take an order: Active, not Off Duty, matching the
	branch, and still under their capacity (max orders per the shift's POS Profile).

	A driver stays in the list — even while On Delivery — until their capacity is
	full, so the dispatcher can keep loading them up to the limit.
	"""
	filters = {"status": "Active", "dispatch_current_status": ["!=", "Off Duty"]}
	if branch:
		filters["custom_branch"] = branch
	drivers = frappe.get_all(
		"Driver",
		filters=filters,
		fields=["name", "full_name", "cell_number", "dispatch_current_status", "dispatch_active_shift", "custom_branch as branch"],
		order_by="full_name asc",
	)

	# Capacity from the dispatcher's open shift POS Profile
	user = frappe.session.user
	shift = frappe.db.get_value(
		"POS Opening Shift", {"user": user, "status": "Open", "docstatus": 1}, "name"
	)
	max_orders = _get_max_driver_orders(shift)

	# Keep only drivers still under capacity, enriched with their current load
	result = []
	for driver in drivers:
		driver["active_load"] = frappe.db.count(
			"Delivery Assignment",
			{
				"driver": driver["name"],
				"status": ["in", ["Assigned", "Picked Up", "Out for Delivery"]],
				"docstatus": ["!=", 2],
			},
		)
		driver["max_orders"] = max_orders
		if driver["active_load"] < max_orders:
			result.append(driver)
	return result


@frappe.whitelist()
def get_active_assignments(shift=None):
	"""
	Return all non-terminal assignments, optionally filtered by shift.
	Scoped to the current user's branch (auto-detected from their open POS Opening
	Shift → POS Profile) so each branch only sees its own delivery assignments.
	"""
	filters = {
		"status": ["in", ["Assigned", "Picked Up", "Out for Delivery"]],
		"docstatus": ["!=", 2],
	}
	if shift:
		filters["shift"] = shift
	assignments = frappe.get_all(
		"Delivery Assignment",
		filters=filters,
		fields=[
			"name", "driver", "delivery_channel", "order_reference", "customer", "delivery_address",
			"contact_phone", "payment_mode", "amount_to_collect", "amount_collected", "status",
			"creation as assigned_at", "out_for_delivery_time",
		],
		order_by="driver asc, creation asc",
	)

	# Restrict to the branch of the current user's open shift. Each assignment is
	# tied to a Sales Invoice (order_reference) that carries the branch.
	branch = None
	user = frappe.session.user
	open_shift = frappe.db.get_value(
		"POS Opening Shift",
		{"user": user, "status": "Open", "docstatus": 1},
		"pos_profile",
	)
	if open_shift:
		branch = frappe.db.get_value("POS Profile", open_shift, "branch") or None

	if branch and assignments:
		ref_names = list({a["order_reference"] for a in assignments if a.get("order_reference")})
		branch_refs = set(
			frappe.get_all(
				"Sales Invoice",
				filters={"name": ["in", ref_names], "branch": branch, "is_return": 0},
				pluck="name",
			)
		) if ref_names else set()
		# Keep branch orders; drop assignments whose invoice belongs to another branch.
		# Assignments with no order_reference are kept (nothing to scope them by).
		assignments = [
			a for a in assignments
			if not a.get("order_reference") or a["order_reference"] in branch_refs
		]

	# Enrich with driver name (Talabat assignments have no internal driver)
	driver_names = {}
	for a in assignments:
		if not a.driver:
			a["driver_name"] = None
			continue
		if a.driver not in driver_names:
			driver_names[a.driver] = frappe.db.get_value("Driver", a.driver, "full_name") or a.driver
		a["driver_name"] = driver_names[a.driver]

	# Enrich with KDS status + the human order number (custom_number_order) per invoice
	invoice_names = [a["order_reference"] for a in assignments if a.get("order_reference")]
	kds_map = {}
	number_order_map = {}
	if invoice_names:
		kds_rows = frappe.db.sql(
			"""SELECT sales_invoice, status FROM `tabKDS Order`
			   WHERE sales_invoice IN %(names)s AND status != 'Cancelled'""",
			{"names": invoice_names}, as_dict=True,
		)
		kds_map = {r.sales_invoice: r.status for r in kds_rows}

		number_order_map = {
			r.name: r
			for r in frappe.get_all(
				"Sales Invoice",
				filters={"name": ["in", invoice_names]},
				fields=["name", "custom_number_order", "customer_name"],
			)
		}

	for a in assignments:
		kds_status = kds_map.get(a.get("order_reference"))
		a["kds_status"] = kds_status or "No KDS"
		# Kitchen is done once the KDS order is Ready or Completed (or no KDS order exists)
		a["kds_ready"] = (kds_status in ("Ready", "Completed")) if kds_status else True
		# Order number + customer name shown on the dispatch board
		inv_row = number_order_map.get(a.get("order_reference"))
		a["custom_number_order"] = inv_row.custom_number_order if inv_row else None
		a["customer_name"] = inv_row.customer_name if inv_row else None

	return assignments


@frappe.whitelist()
def get_pos_payment_modes(shift=None):
	"""
	Return the mode-of-payment options for the dispatcher's POS Profile so the
	collect screen can offer more than cash and support split payment.
	"""
	user = frappe.session.user
	if not shift:
		shift = frappe.db.get_value(
			"POS Opening Shift", {"user": user, "status": "Open", "docstatus": 1}, "name"
		)
	pos_profile = frappe.db.get_value("POS Opening Shift", shift, "pos_profile") if shift else None

	modes = []
	if pos_profile:
		rows = frappe.get_all(
			"POS Payment Method",
			filters={"parent": pos_profile},
			fields=["mode_of_payment"],
			order_by="idx asc",
		)
		for r in rows:
			mtype = frappe.get_cached_value("Mode of Payment", r.mode_of_payment, "type")
			modes.append({"mode_of_payment": r.mode_of_payment, "type": mtype})

	if not modes:
		modes = [{"mode_of_payment": "Cash", "type": "Cash"}]
	return modes


@frappe.whitelist()
def update_assignment_status(assignment, status, amount_collected=None, payments=None):
	"""
	Update a Delivery Assignment status from the dispatcher desk.

	payments: optional JSON list of {mode_of_payment, amount} — lets the dispatcher
	collect a COD invoice across one or more payment modes (cash, card, …). When
	provided it takes precedence over amount_collected.
	"""
	import json

	if isinstance(payments, str):
		payments = json.loads(payments) if payments else None
	if payments:
		payments = [p for p in payments if flt(p.get("amount")) > 0]

	doc = frappe.get_doc("Delivery Assignment", assignment)
	if doc.status in ("Delivered", "Returned", "Failed"):
		frappe.throw(_("Assignment {0} is already in a terminal state.").format(assignment))
	doc.status = status
	if payments:
		doc.amount_collected = sum(flt(p.get("amount")) for p in payments)
	elif amount_collected is not None:
		doc.amount_collected = flt(amount_collected)
	doc.save(ignore_permissions=True)

	# Create Payment Entry(ies) immediately when COD delivery is collected
	if status == "Delivered" and doc.payment_mode == "Cash (COD)" and doc.order_reference:
		_create_cod_payment_entries(doc, payments)

	return {"status": doc.status}


@frappe.whitelist()
def mark_delivery_failed(assignment, reason=""):
	"""
	Mark a Delivery Assignment as Failed and record the reason.
	The linked Sales Invoice will appear in Need My Action for cancellation.
	"""
	doc = frappe.get_doc("Delivery Assignment", assignment)
	if doc.status in ("Delivered", "Returned", "Failed"):
		frappe.throw(_("Assignment {0} is already in a terminal state.").format(assignment))
	doc.status = "Failed"
	doc.delivery_notes = reason or doc.delivery_notes
	doc.save(ignore_permissions=True)
	return {"status": "Failed", "order_reference": doc.order_reference}


@frappe.whitelist()
def cancel_failed_delivery_order(assignment):
	"""
	Cancel the Sales Invoice linked to a Failed delivery assignment.
	Called from Need My Action after the dispatcher reviews the failure.
	"""
	doc = frappe.get_doc("Delivery Assignment", assignment)
	if doc.status != "Failed":
		frappe.throw(_("Only Failed assignments can be cancelled this way."))
	if not doc.order_reference:
		frappe.throw(_("No Sales Invoice linked to assignment {0}.").format(assignment))

	inv = frappe.get_doc("Sales Invoice", doc.order_reference)
	if inv.docstatus == 2:
		frappe.throw(_("Invoice {0} is already cancelled.").format(doc.order_reference))
	if inv.docstatus == 1:
		inv.cancel()

	frappe.db.set_value("Delivery Assignment", assignment, "status", "Returned")
	return {"cancelled": doc.order_reference}


@frappe.whitelist()
def get_failed_delivery_orders():
	"""
	Return Failed delivery assignments with their invoice details for Need My Action.
	Only returns assignments whose invoice is not yet cancelled.
	"""
	# Branch must be resolved the SAME way as the rest of the dispatcher desk — from the
	# current user's open POS Opening Shift → POS Profile → branch. Using Employee.branch
	# here (as before) silently hid Failed orders whenever the dispatcher's Employee branch
	# differed from the branch they are actually operating (e.g. Employee=Smouha but the
	# open shift's profile is Miami), and showed ALL branches when Employee.branch was empty.
	user = frappe.session.user
	# Call Center Managers / Deputies oversee every branch and usually have no open
	# dispatcher shift — give them (and System Managers) unscoped, all-branch visibility.
	overseer = bool(
		{"Call center manager", "Deputy Call Center Manager", "System Manager"} & set(frappe.get_roles(user))
	)
	if overseer:
		branch = ""
	else:
		open_shift = frappe.db.get_value(
			"POS Opening Shift",
			{"user": user, "status": "Open", "docstatus": 1},
			"pos_profile",
		)
		branch = (frappe.db.get_value("POS Profile", open_shift, "branch") if open_shift else "") or ""

	assignments = frappe.db.sql("""
		SELECT
			da.name,
			da.order_reference,
			da.customer,
			da.delivery_address,
			da.delivery_notes,
			da.driver,
			da.shift,
			da.assigned_time,
			da.modified_by AS marked_failed_by,
			da.modified AS marked_failed_at,
			si.grand_total,
			si.custom_order_type,
			si.custom_number_order,
			si.posting_date,
			si.posting_time,
			si.branch,
			si.pos_profile,
			si.posa_pos_opening_shift AS pos_opening_shift,
			si.currency
		FROM `tabDelivery Assignment` da
		INNER JOIN `tabSales Invoice` si ON si.name = da.order_reference
		WHERE da.status = 'Failed'
		  AND da.docstatus != 2
		  AND si.docstatus = 1
		  {branch_cond}
		ORDER BY da.assigned_time DESC
	""".format(
		branch_cond="AND si.branch = %(branch)s" if branch else ""
	), {"branch": branch} if branch else {}, as_dict=True)

	return assignments


@frappe.whitelist()
def mark_assignment_returned(assignment):
	"""Mark a Failed Delivery Assignment as Returned after the invoice has been cancelled."""
	frappe.db.set_value("Delivery Assignment", assignment, "status", "Returned")
	return {"status": "Returned"}


@frappe.whitelist()
def record_driver_charge(assignment, amount, notes=""):
	"""Record a charge against the driver for a failed delivery."""
	frappe.db.set_value("Delivery Assignment", assignment, {
		"driver_charge_amount": flt(amount),
		"driver_charge_notes": notes or "",
	})
	return {"charged": flt(amount)}


def _stamp_pos_links(pe, opening_shift):
	"""Stamp the POS Business Day / Cashier Shift links on a Payment Entry, resolved from
	its POS Opening Shift, so COD collections are linkable/filterable directly."""
	if not opening_shift:
		return
	cs = frappe.db.get_value(
		"POS Cashier Shift", {"pos_opening_shift": opening_shift},
		["name", "pos_business_day"], as_dict=True,
	)
	if not cs:
		return
	if pe.meta.has_field("custom_pos_cashier_shift"):
		pe.custom_pos_cashier_shift = cs.name
	if pe.meta.has_field("custom_pos_business_day"):
		pe.custom_pos_business_day = cs.pos_business_day


def _resolve_shift_for_invoice(assignment_doc):
	"""
	Return the POS Opening Shift name to stamp on the Payment Entry.
	Priority:
	  1. Shift already on the Delivery Assignment
	  2. posa_pos_opening_shift on the Sales Invoice (set when the invoice was submitted via POS)
	  3. Current open shift for the current user
	"""
	if assignment_doc.shift:
		return assignment_doc.shift

	if assignment_doc.order_reference:
		inv_shift = frappe.db.get_value(
			"Sales Invoice", assignment_doc.order_reference, "posa_pos_opening_shift"
		)
		if inv_shift:
			return inv_shift

	# Last resort: current user's open shift
	user = frappe.session.user
	return frappe.db.get_value(
		"POS Opening Shift",
		{"user": user, "status": "Open", "docstatus": 1},
		"name",
	) or None


def _create_cod_payment_entries(assignment_doc, payments=None):
	"""
	Create Payment Entry(ies) for a COD delivery so they appear in POS Closing Shift
	payment reconciliation (filtered by reference_no = shift name).

	payments: optional list of {mode_of_payment, amount}. When omitted, a single
	cash Payment Entry is created (legacy behaviour). Multiple entries — one per
	mode of payment — support split payment on a single invoice.
	"""
	if not assignment_doc.order_reference:
		frappe.throw(_("Cannot create payment entry: Delivery Assignment {0} has no linked Sales Invoice.").format(
			assignment_doc.name
		))

	# Resolve shift — mandatory for the PE to appear in POS Closing Shift
	shift = _resolve_shift_for_invoice(assignment_doc)
	if not shift:
		frappe.throw(_(
			"Cannot record COD payment for {0}: no POS Opening Shift found. "
			"Open a shift on the dispatcher page and retry."
		).format(assignment_doc.name))

	# Save shift back onto the assignment if it was missing
	if not assignment_doc.shift:
		frappe.db.set_value("Delivery Assignment", assignment_doc.name, "shift", shift)

	# Skip if the Sales Invoice is already fully settled
	outstanding = flt(frappe.db.get_value("Sales Invoice", assignment_doc.order_reference, "outstanding_amount"))
	if outstanding <= 0:
		return

	pos_profile = frappe.db.get_value("POS Opening Shift", shift, "pos_profile")
	company = frappe.db.get_value("Sales Invoice", assignment_doc.order_reference, "company")
	settings = frappe.get_single("Dispatch Settings")

	# Build the list of (mode, amount) splits
	if payments:
		splits = [
			{"mode_of_payment": p.get("mode_of_payment") or _resolve_cash_mode(pos_profile),
			 "amount": flt(p.get("amount"))}
			for p in payments if flt(p.get("amount")) > 0
		]
	else:
		collected = flt(assignment_doc.amount_collected or assignment_doc.amount_to_collect)
		splits = [{"mode_of_payment": _resolve_cash_mode(pos_profile), "amount": collected}]

	if not splits or sum(s["amount"] for s in splits) <= 0:
		frappe.throw(_("Collected amount is zero for {0}.").format(assignment_doc.name))

	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	remaining = outstanding
	for split in splits:
		mode_of_payment = split["mode_of_payment"]
		amount = split["amount"]

		paid_to = _resolve_cash_account(mode_of_payment, company) or settings.driver_cash_clearing_account
		if not paid_to:
			frappe.throw(_(
				"Cannot create payment entry for {0}: no GL account found "
				"(POS Profile: {1}, Mode of Payment: {2}). "
				"Configure an account for this Mode of Payment or a clearing account in Dispatch Settings."
			).format(assignment_doc.name, pos_profile, mode_of_payment))

		pe = get_payment_entry("Sales Invoice", assignment_doc.order_reference)
		pe.mode_of_payment = mode_of_payment
		pe.paid_to = paid_to
		pe.paid_amount = amount
		pe.received_amount = amount
		# Allocate against the invoice up to what is still outstanding; any excess stays unallocated.
		alloc = min(amount, remaining) if remaining > 0 else 0
		if pe.references:
			pe.references[0].allocated_amount = alloc
		remaining = flt(remaining - alloc)
		# reference_no = shift name → picked up by get_payments_entries() in POS Closing Shift
		pe.reference_no = shift
		pe.reference_date = frappe.utils.today()
		pe.remarks = _("COD Collection — Delivery Assignment {0}, Driver {1}, {2}").format(
			assignment_doc.name, assignment_doc.driver or _("Talabat"), mode_of_payment
		)
		_stamp_pos_links(pe, shift)
		pe.insert(ignore_permissions=True)
		pe.submit()


def _resolve_cash_mode(pos_profile):
	"""Return the Cash mode of payment for a POS Profile."""
	if pos_profile:
		# Custom field shortcut
		cash_mode = frappe.db.get_value("POS Profile", pos_profile, "posa_cash_mode_of_payment")
		if cash_mode:
			return cash_mode
		# Walk payment methods
		for p in frappe.get_all("POS Payment Method", filters={"parent": pos_profile}, fields=["mode_of_payment"]):
			if frappe.get_cached_value("Mode of Payment", p.mode_of_payment, "type") == "Cash":
				return p.mode_of_payment
	return "Cash"


def _resolve_cash_account(mode_of_payment, company):
	"""Return the GL account for a cash mode of payment in the given company."""
	return frappe.db.get_value(
		"Mode of Payment Account",
		{"parent": mode_of_payment, "company": company},
		"default_account",
	)


def _get_max_driver_orders(shift):
	"""Max concurrent orders a driver may carry, configured on the shift's POS Profile."""
	max_orders = None
	if shift:
		pos_profile = frappe.db.get_value("POS Opening Shift", shift, "pos_profile")
		if pos_profile:
			max_orders = frappe.db.get_value("POS Profile", pos_profile, "custom_max_driver_orders")
	return int(max_orders) if max_orders and int(max_orders) > 0 else 2


def _driver_active_load(driver):
	"""Count a driver's non-terminal assignments across all shifts."""
	return frappe.db.count(
		"Delivery Assignment",
		{
			"driver": driver,
			"status": ["in", ["Assigned", "Picked Up", "Out for Delivery"]],
			"docstatus": ["!=", 2],
		},
	)


@frappe.whitelist()
def create_assignments(driver, orders, shift=None):
	"""
	Bulk-create Delivery Assignments.
	orders: JSON list of Sales Invoice names.
	shift: optional POS Opening Shift name; auto-detected from current user if omitted.
	"""
	import json

	if isinstance(orders, str):
		orders = json.loads(orders)

	# Auto-detect shift if not provided
	if not shift:
		user = frappe.session.user
		open_shift = frappe.db.get_value(
			"POS Opening Shift",
			{"user": user, "status": "Open", "docstatus": 1},
			"name",
		)
		shift = open_shift or ""

	# Enforce the per-driver order cap (configurable on the POS Profile)
	max_orders = _get_max_driver_orders(shift)
	current_load = _driver_active_load(driver)
	if current_load + len(orders) > max_orders:
		driver_name = frappe.db.get_value("Driver", driver, "full_name") or driver
		frappe.throw(
			_("{0} already has {1} active order(s); the limit is {2}. Cannot assign {3} more.").format(
				driver_name, current_load, max_orders, len(orders)
			)
		)

	settings = frappe.get_single("Dispatch Settings")
	created = []

	for invoice_name in orders:
		inv = frappe.get_doc("Sales Invoice", invoice_name)
		is_cod = flt(inv.outstanding_amount) > 0
		da = frappe.get_doc(
			{
				"doctype": "Delivery Assignment",
				"shift": shift,
				"driver": driver,
				"order_doctype": "Sales Invoice",
				"order_reference": invoice_name,
				"payment_mode": "Cash (COD)" if is_cod else "Prepaid",
				"amount_to_collect": flt(inv.outstanding_amount) if is_cod else 0,
				"status": "Assigned",
			}
		)
		da.insert(ignore_permissions=True)
		created.append(da.name)

	# Driver stays "Available" until they physically leave (Out for Delivery)
	# Status is updated to "On Delivery" when update_assignment_status sets "Out for Delivery"

	frappe.publish_realtime("dispatch_desk_refresh", {"shift": shift})
	return created


@frappe.whitelist()
def handover_to_talabat(orders, shift=None):
	"""
	Hand Talabat orders over to the Talabat platform's own driver.

	Creates a driverless Delivery Assignment on the 'Talabat' channel, straight to
	'Out for Delivery', so the order leaves the unassigned board and is tracked as
	"with Talabat driver" until the dispatcher confirms the customer received it
	(marking it Delivered). Talabat is prepaid — nothing to collect, no driver touched.
	"""
	import json

	if isinstance(orders, str):
		orders = json.loads(orders)

	if not shift:
		user = frappe.session.user
		shift = frappe.db.get_value(
			"POS Opening Shift",
			{"user": user, "status": "Open", "docstatus": 1},
			"name",
		) or ""

	created = []
	for invoice_name in orders:
		# Cash Talabat orders: dispatcher collects from the Talabat driver on return.
		# Prepaid Talabat orders: nothing to collect — just confirm receipt.
		outstanding = flt(frappe.db.get_value("Sales Invoice", invoice_name, "outstanding_amount"))
		is_cod = outstanding > 0
		da = frappe.get_doc(
			{
				"doctype": "Delivery Assignment",
				"shift": shift,
				"delivery_channel": "Talabat",
				"order_doctype": "Sales Invoice",
				"order_reference": invoice_name,
				"payment_mode": "Cash (COD)" if is_cod else "Prepaid",
				"amount_to_collect": outstanding if is_cod else 0,
				"status": "Out for Delivery",
			}
		)
		da.insert(ignore_permissions=True)
		created.append(da.name)

	frappe.publish_realtime("dispatch_desk_refresh", {"shift": shift})
	return created


@frappe.whitelist()
def deliver_talabat(order, payments=None, shift=None):
	"""
	Deliver a Talabat order in a single step — no assign, no tracking.

	Paid orders are marked Delivered immediately. Unpaid (cash) orders record the
	collected payment(s) first, then deliver. The driverless Talabat assignment is
	created and finalised within the same request, so it never lingers in an
	'Out for Delivery' / assigned state.
	"""
	names = handover_to_talabat([order], shift)
	da_name = names[0]
	update_assignment_status(da_name, "Delivered", payments=payments)
	return {"assignment": da_name, "status": "Delivered"}


# ---------------------------------------------------------------------------
# Shift close + accounting
# ---------------------------------------------------------------------------

@frappe.whitelist()
def close_dispatch_shift(shift_name, force_close=False):
	"""Finalize COD accounting for all delivery assignments under this POS Opening Shift."""
	# 1. Validate all assignments are in a terminal state
	pending_list = frappe.get_all(
		"Delivery Assignment",
		filters={
			"shift": shift_name,
			"status": ["in", ["Assigned", "Picked Up", "Out for Delivery"]],
			"docstatus": ["!=", 2],
		},
		fields=["name", "order_reference", "status"],
	)
	if pending_list:
		if not force_close:
			names = ", ".join(f"{p.name} ({p.status})" for p in pending_list[:5])
			frappe.throw(
				_("Cannot close shift — {0} assignment(s) still in progress: {1}. "
				  "Use 'Return' on each or force-close.").format(len(pending_list), names)
			)
		# Force-close: mark all pending as Returned
		for p in pending_list:
			frappe.db.set_value("Delivery Assignment", p.name, {
				"status": "Returned",
				"amount_collected": 0,
			})

	settings = frappe.get_single("Dispatch Settings")

	# 2. Compute summary
	assignments = frappe.get_all(
		"Delivery Assignment",
		filters={"shift": shift_name, "docstatus": ["!=", 2]},
		fields=["name", "status", "payment_mode", "amount_to_collect", "amount_collected", "order_reference"],
	)

	total = len(assignments)
	delivered = [a for a in assignments if a.status == "Delivered"]
	returned = [a for a in assignments if a.status == "Returned"]
	failed = [a for a in assignments if a.status == "Failed"]

	cash_expected = sum(
		flt(a.amount_to_collect)
		for a in delivered
		if a.payment_mode == "Cash (COD)"
	)
	cash_collected = sum(
		flt(a.amount_collected)
		for a in delivered
		if a.payment_mode == "Cash (COD)"
	)
	cash_difference = flt(cash_collected - cash_expected, 2)

	if not settings.allow_collection_mismatch and cash_difference != 0:
		frappe.throw(
			_("Cash difference of {0} detected. Set 'Allow Collection Mismatch' to proceed.").format(
				cash_difference
			)
		)

	company = frappe.db.get_single_value("Global Defaults", "default_company")

	# 3. Create Payment Entries for delivered COD Sales Invoices (only those not yet settled)
	if settings.auto_create_payment_entry:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		shift_pos_profile = frappe.db.get_value("POS Opening Shift", shift_name, "pos_profile")

		for da in delivered:
			if da.payment_mode != "Cash (COD)" or not da.order_reference:
				continue
			# Skip if the Sales Invoice is already fully settled (PE was created on collect)
			outstanding = flt(frappe.db.get_value("Sales Invoice", da.order_reference, "outstanding_amount"))
			if outstanding <= 0:
				continue
			try:
				da_company = frappe.db.get_value("Sales Invoice", da.order_reference, "company")
				mode_of_payment = _resolve_cash_mode(shift_pos_profile)
				paid_to = _resolve_cash_account(mode_of_payment, da_company) or settings.driver_cash_clearing_account
				if not paid_to:
					continue
				pe = get_payment_entry("Sales Invoice", da.order_reference)
				pe.mode_of_payment = mode_of_payment
				pe.paid_to = paid_to
				pe.paid_amount = flt(da.amount_collected or da.amount_to_collect)
				pe.received_amount = pe.paid_amount
				pe.reference_no = shift_name
				pe.reference_date = frappe.utils.today()
				pe.remarks = _("COD Collection — Delivery Assignment {0}").format(da.name)
				_stamp_pos_links(pe, shift_name)
				pe.insert(ignore_permissions=True)
				pe.submit()
			except Exception as e:
				frappe.log_error(
					f"PE creation failed for DA {da.name}: {e}",
					"Dispatch Close Shift",
				)

	# 4. Short/Over Journal Entry
	if cash_difference != 0 and settings.cash_short_over_account and settings.driver_cash_clearing_account:
		je_diff = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"posting_date": frappe.utils.today(),
				"company": company,
				"remark": _("Cash short/over for POS Shift {0}").format(shift_name),
				"accounts": _build_diff_je_lines(
					cash_difference,
					settings.cash_short_over_account,
					settings.driver_cash_clearing_account,
					company,
				),
			}
		)
		je_diff.insert(ignore_permissions=True)
		je_diff.submit()

	# 5. Handover Journal Entry
	if cash_collected and settings.default_cash_in_hand_account and settings.driver_cash_clearing_account:
		je_handover = frappe.get_doc(
			{
				"doctype": "Journal Entry",
				"voucher_type": "Cash Entry",
				"posting_date": frappe.utils.today(),
				"company": company,
				"remark": _("Cash handover for POS Shift {0}").format(shift_name),
				"accounts": [
					{
						"account": settings.default_cash_in_hand_account,
						"debit_in_account_currency": flt(cash_collected),
						"credit_in_account_currency": 0,
						"cost_center": frappe.db.get_single_value("Global Defaults", "default_cost_center"),
					},
					{
						"account": settings.driver_cash_clearing_account,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": flt(cash_collected),
						"cost_center": frappe.db.get_single_value("Global Defaults", "default_cost_center"),
					},
				],
			}
		)
		je_handover.insert(ignore_permissions=True)
		je_handover.submit()

	frappe.publish_realtime("dispatch_desk_refresh", {"shift": shift_name})
	return {
		"status": "Closed",
		"total_assignments": total,
		"delivered_count": len(delivered),
		"returned_count": len(returned),
		"failed_count": len(failed),
		"cash_expected": flt(cash_expected, 2),
		"cash_collected": flt(cash_collected, 2),
		"cash_difference": flt(cash_difference, 2),
	}


def _build_diff_je_lines(cash_difference, short_over_account, clearing_account, company):
	"""Build JE account lines for short/over posting."""
	cost_center = frappe.db.get_single_value("Global Defaults", "default_cost_center")
	if cash_difference > 0:
		# Over: collected more than expected → Dr Clearing / Cr Short-Over (income)
		return [
			{"account": clearing_account, "debit_in_account_currency": flt(cash_difference), "credit_in_account_currency": 0, "cost_center": cost_center},
			{"account": short_over_account, "debit_in_account_currency": 0, "credit_in_account_currency": flt(cash_difference), "cost_center": cost_center},
		]
	else:
		# Short: collected less than expected → Dr Short-Over (expense) / Cr Clearing
		amt = abs(cash_difference)
		return [
			{"account": short_over_account, "debit_in_account_currency": flt(amt), "credit_in_account_currency": 0, "cost_center": cost_center},
			{"account": clearing_account, "debit_in_account_currency": 0, "credit_in_account_currency": flt(amt), "cost_center": cost_center},
		]
