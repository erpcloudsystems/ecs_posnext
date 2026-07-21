# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

from ecs_posnext.api.business_day import get_business_day_window, get_profile_day_settings, log_pos_event

NON_CLOSED_STATES = ("Open", "Closing Required", "Closing Overdue", "Ready to Close")


class POSBusinessDay(Document):
	def validate(self):
		self._enforce_single_open_day()

	def _enforce_single_open_day(self):
		"""At most one non-Closed POS Business Day per (POS Profile, business date).

		A prior day left unclosed (e.g. yesterday "Closing Overdue") does NOT block
		today's day — only two days for the SAME date are disallowed. Blocking a new
		open until the previous day is closed is governed separately by the
		`custom_block_new_pos_opening_until_prev_closed` profile setting.
		"""
		if self.status == "Closed":
			return
		existing = frappe.db.get_all(
			"POS Business Day",
			filters={
				"pos_profile": self.pos_profile,
				"business_date": self.business_date,
				"status": ["in", NON_CLOSED_STATES],
				"name": ["!=", self.name or ""],
			},
			pluck="name",
		)
		if existing:
			frappe.throw(
				_("A POS Business Day ({0}) already exists for {1} on {2}.").format(
					existing[0], frappe.bold(self.pos_profile), self.business_date
				)
			)

	# ------------------------------------------------------------------
	# Summary aggregation
	# ------------------------------------------------------------------
	def refresh_summary(self, save=False):
		self._refresh_cashier_shifts()
		self._refresh_sales_summary()
		if save:
			self.save(ignore_permissions=True)

	def _refresh_cashier_shifts(self):
		if not frappe.db.exists("DocType", "POS Cashier Shift"):
			return
		self.set("cashier_shifts", [])
		shifts = frappe.db.get_all(
			"POS Cashier Shift",
			filters={"pos_business_day": self.name},
			fields=["name", "cashier_user", "employee", "opening_cash", "status", "cashier_shift_closing"],
		)
		for s in shifts:
			row = {
				"cashier": s.cashier_user,
				"employee": s.employee,
				"cashier_shift": s.name,
				"cashier_shift_closing": s.cashier_shift_closing,
				"opening_cash": flt(s.opening_cash),
				"status": s.status,
			}
			if s.cashier_shift_closing and frappe.db.exists("POS Cashier Shift Closing", s.cashier_shift_closing):
				closing = frappe.db.get_value(
					"POS Cashier Shift Closing",
					s.cashier_shift_closing,
					["cash_sales", "call_center_cash_collected", "expected_cash", "actual_counted_cash", "difference", "status"],
					as_dict=True,
				)
				row.update(
					{
						"pos_cash_sales": flt(closing.cash_sales),
						"call_center_cash_collected": flt(closing.call_center_cash_collected),
						"expected_cash": flt(closing.expected_cash),
						"actual_cash": flt(closing.actual_counted_cash),
						"difference": flt(closing.difference),
						"status": closing.status or s.status,
					}
				)
			self.append("cashier_shifts", row)

	def _refresh_sales_summary(self):
		# Reset
		for f in (
			"total_sales", "pos_sales", "call_center_sales", "cash_sales", "visa_sales",
			"online_payments", "aggregator_sales", "returns", "refunds", "discounts", "net_sales",
		):
			self.set(f, 0)

		if "custom_pos_business_day" not in frappe.get_meta("Sales Invoice").get_valid_columns():
			return

		invoices = frappe.db.get_all(
			"Sales Invoice",
			filters={"custom_pos_business_day": self.name, "docstatus": 1},
			fields=[
				"name", "grand_total", "net_total", "base_grand_total", "is_return",
				"discount_amount", "pos_profile", "custom_order_type",
			],
		)
		call_center_profiles = self._call_center_profiles()
		for inv in invoices:
			gt = flt(inv.grand_total)
			if inv.is_return:
				self.returns += abs(gt)
			else:
				self.total_sales += gt
				self.discounts += flt(inv.discount_amount)
				if inv.pos_profile in call_center_profiles:
					self.call_center_sales += gt
				else:
					self.pos_sales += gt

		self._summarise_payments(call_center_profiles)
		self._summarise_refunds()
		self._summarise_call_center_cash()
		self.net_sales = flt(self.total_sales) - flt(self.returns)

	def _summarise_call_center_cash(self):
		"""Cash the branch's cashiers collected to settle routed (Call Center) orders.

		Reported separately from Cash Sales: the SALE belongs to the day, but the MONEY
		belongs to whichever cashier took it. It arrives as a Payment Entry against that
		cashier's shift, not as a payment row on the invoice — which is why it is
		invisible to the invoice-based totals.
		"""
		shifts = frappe.get_all(
			"POS Cashier Shift", filters={"pos_business_day": self.name}, pluck="pos_opening_shift"
		)
		shifts = [s for s in shifts if s]
		if not shifts:
			self.call_center_cash_collected = 0
			return

		rows = frappe.get_all(
			"Payment Entry",
			filters={"docstatus": 1, "payment_type": "Receive", "reference_no": ["in", shifts]},
			fields=["mode_of_payment", "paid_amount"],
		)
		total = 0
		for r in rows:
			if frappe.get_cached_value("Mode of Payment", r.mode_of_payment, "type") == "Cash":
				total += flt(r.paid_amount)
		self.call_center_cash_collected = total

	def _summarise_refunds(self):
		"""Money actually handed back on returns.

		This is deliberately NOT the same as `returns`: `returns` is the value of the
		goods credited (the credit notes), while `refunds` is the cash/card actually
		paid back to customers. A credit note left unsettled (no payment rows) counts
		towards returns but not refunds — the difference is what is still owed.
		"""
		row = frappe.db.sql(
			"""
			select sum(sip.amount) as amount
			from `tabSales Invoice Payment` sip
			inner join `tabSales Invoice` si on si.name = sip.parent
			where si.custom_pos_business_day = %s and si.docstatus = 1
			  and ifnull(si.is_return, 0) = 1
			""",
			(self.name,),
			as_dict=True,
		)
		self.refunds = abs(flt(row[0].amount)) if row and row[0].get("amount") else 0

	def _summarise_payments(self, call_center_profiles):
		"""Split submitted-invoice payments by mode-of-payment classification."""
		rows = frappe.db.sql(
			"""
			select sip.mode_of_payment as mop, sum(sip.amount) as amount
			from `tabSales Invoice Payment` sip
			inner join `tabSales Invoice` si on si.name = sip.parent
			where si.custom_pos_business_day = %s and si.docstatus = 1 and ifnull(si.is_return,0) = 0
			group by sip.mode_of_payment
			""",
			(self.name,),
			as_dict=True,
		)
		for r in rows:
			amt = flt(r.amount)
			mop_type = frappe.db.get_value("Mode of Payment", r.mop, "type") or ""
			name_l = (r.mop or "").lower()
			if mop_type == "Cash":
				self.cash_sales += amt
			elif any(k in name_l for k in ("visa", "card", "mastercard", "credit")):
				self.visa_sales += amt
			elif any(k in name_l for k in ("talabat", "aggregator", "elmenus", "breadfast")):
				self.aggregator_sales += amt
			else:
				self.online_payments += amt

	@staticmethod
	def _call_center_profiles():
		return set(
			frappe.db.get_all("POS Profile", filters={"name": ["like", "%Call Center%"]}, pluck="name")
		)

	# ------------------------------------------------------------------
	# Closing validations (filled in Phase 5)
	# ------------------------------------------------------------------
	def evaluate_closing_issues(self):
		from ecs_posnext.api.business_day_closing import collect_closing_issues

		issues = collect_closing_issues(self)
		self.set("closing_issues", [])
		for issue in issues:
			self.append("closing_issues", issue)
		return issues

	def close(self, force=False, reason=None):
		if self.status == "Closed":
			frappe.throw(_("Business Day is already closed."))

		self.refresh_summary()
		issues = self.evaluate_closing_issues()
		if issues and not force:
			self.save(ignore_permissions=True)
			frappe.throw(
				_("Business Day cannot be closed: {0} unresolved issue(s). See Closing Issues.").format(len(issues))
			)

		old_status = self.status
		self.status = "Closed"
		self.closed_by = frappe.session.user
		self.closing_datetime = now_datetime()
		if force and reason:
			self.override_reason = reason
		self.save(ignore_permissions=True)

		log_pos_event(
			action="Override" if force else "Business Day Closing",
			reference_doctype=self.doctype,
			reference_name=self.name,
			pos_profile=self.pos_profile,
			pos_business_day=self.name,
			old_value=old_status,
			new_value="Closed",
			reason=reason,
		)
		return self


def get_or_create_for(pos_profile, at_datetime=None, company=None, opened_by=None):
	"""Return the open POS Business Day for a profile/time, creating one if needed."""
	window = get_business_day_window(pos_profile, at_datetime)

	# A day already exists for this exact (profile, business date) -> reuse it.
	same_date = frappe.db.get_all(
		"POS Business Day",
		filters={
			"pos_profile": pos_profile,
			"business_date": window.business_date,
			"status": ["in", NON_CLOSED_STATES],
		},
		pluck="name",
		limit=1,
	)
	if same_date:
		return frappe.get_doc("POS Business Day", same_date[0])

	# The day for this date was already CLOSED. Never silently create a second day for
	# the same business date — that would split one day's takings across two records and
	# let transactions land after the books were signed off. A manager must reopen it.
	closed_same_date = frappe.db.get_value(
		"POS Business Day",
		{"pos_profile": pos_profile, "business_date": window.business_date, "status": "Closed"},
		"name",
	)
	if closed_same_date:
		frappe.throw(
			_(
				"The POS Business Day for {0} ({1}) is already closed, so this transaction "
				"cannot be recorded. A manager must reopen that business day first."
			).format(window.business_date, closed_same_date),
			title=_("Business Day Closed"),
		)

	# Optionally block opening a new day while a PRIOR day is still unclosed.
	settings = get_profile_day_settings(pos_profile)
	if settings.get("custom_block_new_pos_opening_until_prev_closed"):
		prior = frappe.db.get_all(
			"POS Business Day",
			filters={
				"pos_profile": pos_profile,
				"business_date": ["<", window.business_date],
				"status": ["in", NON_CLOSED_STATES],
			},
			fields=["name", "business_date"],
			order_by="business_date desc",
			limit=1,
		)
		if prior:
			frappe.throw(
				_("Previous POS Business Day {0} ({1}) for {2} is not closed yet.").format(
					prior[0].name, prior[0].business_date, frappe.bold(pos_profile)
				)
			)

	company = company or frappe.db.get_value("POS Profile", pos_profile, "company")
	doc = frappe.get_doc(
		{
			"doctype": "POS Business Day",
			"company": company,
			"pos_profile": pos_profile,
			"business_date": window.business_date,
			"start_datetime": window.start_datetime,
			"sales_cutoff_datetime": window.sales_cutoff_datetime,
			"mandatory_closing_deadline": window.mandatory_closing_deadline,
			"status": "Open",
			"opened_by": opened_by or frappe.session.user,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	log_pos_event(
		action="Opening Shift",
		reference_doctype="POS Business Day",
		reference_name=doc.name,
		pos_profile=pos_profile,
		pos_business_day=doc.name,
		new_value="Open",
	)
	return doc


@frappe.whitelist()
def refresh_business_day_summary(business_day):
	doc = frappe.get_doc("POS Business Day", business_day)
	doc.refresh_summary(save=True)
	return doc.as_dict()
