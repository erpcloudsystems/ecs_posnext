import frappe
from frappe import _


@frappe.whitelist()
def employee_query(doctype, txt, searchfield, start, page_len, filters):
	"""Custom search query for Employee - searches by both ID and employee_name, optionally filtered by branch."""
	import json
	txt = (txt or "").strip()
	like = f"%{txt}%"

	if isinstance(filters, str):
		filters = json.loads(filters) if filters else {}
	branch = (filters or {}).get("branch")

	branch_clause = "AND branch = %(branch)s" if branch else ""
	params = {"like": like, "start": int(start or 0), "page_len": int(page_len or 20)}
	if branch:
		params["branch"] = branch

	return frappe.db.sql(
		f"""
		SELECT name, employee_name
		FROM `tabEmployee`
		WHERE (name LIKE %(like)s OR employee_name LIKE %(like)s)
		{branch_clause}
		ORDER BY employee_name
		LIMIT %(start)s, %(page_len)s
		""",
		params,
	)


@frappe.whitelist()
def get_branch_balance(branch):
	if not branch:
		return {
			"branch": None,
			"account": None,
			"balance": 0,
			"currency": frappe.get_cached_value("Global Defaults", None, "default_currency"),
		}

	from frappe.utils import flt
	fixed_account = "صندوق عمولات المساعدين - HR"
	pos_profile = frappe.db.get_value("POS Profile", {"branch": branch}, ["name", "company"], as_dict=True)
	company = pos_profile.company if pos_profile else None

	balance = 0
	gl_result = frappe.db.sql(
		"""
		SELECT SUM(debit) - SUM(credit) AS balance
		FROM `tabGL Entry`
		WHERE account = %s
		  AND branch = %s
		  AND is_cancelled = 0
		  AND (%s IS NULL OR company = %s)
		""",
		(fixed_account, branch, company, company),
		as_dict=True,
	)
	balance = flt(gl_result[0].balance) if gl_result and gl_result[0].balance else 0

	return {
		"branch": branch,
		"account": fixed_account,
		"balance": balance,
		"currency": frappe.get_cached_value("Company", company, "default_currency") if company else frappe.get_cached_value("Global Defaults", None, "default_currency"),
	}


@frappe.whitelist()
def get_daily_payments(employee=None, from_date=None, to_date=None, branch=None, limit=50):
	"""Fetch Daily Payment records with optional filters by employee, date range, and branch."""
	filters = {}
	or_filters = []

	if branch:
		filters["branch"] = branch

	if from_date:
		if to_date:
			filters["date"] = ["between", [from_date, to_date]]
		else:
			filters["date"] = [">=", from_date]
	elif to_date:
		filters["date"] = ["<=", to_date]

	if employee:
		like = f"%{employee}%"
		or_filters = [
			["name", "like", like],
			["employee", "like", like],
			["employee_name", "like", like],
		]

	fields = [
		"name",
		"date",
		"employee",
		"employee_name",
		"branch",
		"amount",
		"mode_of_payment",
		"company",
		"loan_product",
		"expenses",
		"payment_to_employees",
		"docstatus",
	]

	records = frappe.get_list(
		"Daily Payment",
		filters=filters,
		or_filters=or_filters or None,
		fields=fields,
		order_by="date desc, creation desc",
		limit=int(limit),
	)

	return records


@frappe.whitelist()
def get_invoice_counts(branch=None, from_date=None, to_date=None, pos_opening_shift=None):
	"""Return invoice counts grouped by payment method for Cash and Visa (non-Cash)."""
	filters = [
		["docstatus", "=", 1],
		["is_pos", "=", 1],
	]

	if branch:
		filters.append(["branch", "=", branch])

	if from_date:
		if to_date:
			filters.append(["posting_date", "between", [from_date, to_date]])
		else:
			filters.append(["posting_date", ">=", from_date])
	elif to_date:
		filters.append(["posting_date", "<=", to_date])

	if pos_opening_shift:
		filters.append(["pos_opening_entry", "=", pos_opening_shift])

	invoices = frappe.get_list(
		"Sales Invoice",
		filters=filters,
		fields=["name"],
		limit=0,
	)

	invoice_names = [d.name for d in invoices]
	total = len(invoice_names)

	if not invoice_names:
		return {"cash": 0, "visa": 0, "total": 0}

	rows = frappe.db.sql(
		"""
		SELECT parent, mode_of_payment
		FROM `tabSales Invoice Payment`
		WHERE parent IN %(names)s
		  AND amount > 0
		""",
		{"names": tuple(invoice_names)},
		as_dict=True,
	)

	cash_invoices = set()
	visa_invoices = set()

	for row in rows:
		mode = (row.mode_of_payment or "").strip().lower()
		if mode == "cash" or "cash" in mode or "كاش" in mode or "نقد" in mode or "نقدي" in mode:
			cash_invoices.add(row.parent)
		else:
			visa_invoices.add(row.parent)

	for name in invoice_names:
		if name not in cash_invoices and name not in visa_invoices:
			cash_invoices.add(name)

	return {
		"cash": len(cash_invoices),
		"visa": len(visa_invoices),
		"total": total,
	}


@frappe.whitelist()
def get_daily_payment_detail(name):
	"""Fetch a single Daily Payment record with all details."""
	doc = frappe.get_doc("Daily Payment", name)
	return doc.as_dict()


@frappe.whitelist()
def create_daily_payment(date, branch, employee=None, amount=None, mode_of_payment=None,
						  payment_to_employees=0, expenses=0, loan_product=None,
						  general_expenses=None, pos_opening_shift=None):
	"""Create a new Daily Payment record."""
	import json

	doc = frappe.new_doc("Daily Payment")
	doc.date = date
	doc.branch = branch
	if pos_opening_shift:
		doc.pos_opening_shift = pos_opening_shift

	if frappe.parse_json(payment_to_employees) if isinstance(payment_to_employees, str) else payment_to_employees:
		doc.payment_to_employees = 1
		doc.employee = employee
		doc.amount = amount
		doc.loan_product = loan_product

	if frappe.parse_json(expenses) if isinstance(expenses, str) else expenses:
		doc.expenses = 1
		if general_expenses:
			rows = json.loads(general_expenses) if isinstance(general_expenses, str) else general_expenses
			for row in rows:
				doc.append("general_expenses", {
					"expense_claim_type": row.get("expense_claim_type") or "",
					"amount": row.get("amount") or 0,
					"description": row.get("description") or "",
				})

	if mode_of_payment:
		doc.mode_of_payment = mode_of_payment

	doc.insert(ignore_permissions=True)
	doc.submit()
	frappe.db.commit()

	return {"name": doc.name, "status": "submitted"}
