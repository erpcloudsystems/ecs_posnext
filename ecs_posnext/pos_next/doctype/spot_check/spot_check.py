# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class SpotCheck(Document):
	@frappe.whitelist()
	def get_data(self):
		if not self.pos_profile or not self.date:
			frappe.throw(_("Please select POS Profile and Date"))

		self.set("shifts", [])
		for field in ("total_cash", "total_credit", "total_qty", "total_invoices", "grand_total"):
			self.set(field, 0)

		shifts = get_shifts(self.pos_profile, getdate(self.date))
		if not shifts:
			return

		totals = get_shift_totals([s.name for s in shifts])
		for shift in shifts:
			t = totals.get(shift.name, frappe._dict())
			row = self.append("shifts", {
				"pos_opening_shift": shift.name,
				"user": shift.user,
				"status": shift.status,
				"period_start_date": shift.period_start_date,
				"cash": flt(t.cash),
				"credit": flt(t.credit),
				"total_qty": flt(t.total_qty),
				"total_invoices": t.total_invoices or 0,
				"grand_total": flt(t.grand_total),
			})
			self.total_cash += row.cash
			self.total_credit += row.credit
			self.total_qty += row.total_qty
			self.total_invoices += row.total_invoices
			self.grand_total += row.grand_total


def get_shifts(pos_profile, date):
	"""Submitted opening shifts of the profile that were active on the given date."""
	return frappe.db.sql(
		"""
		select os.name, os.user, os.status, os.period_start_date
		from `tabPOS Opening Shift` os
		left join `tabPOS Closing Shift` cs on cs.name = os.pos_closing_shift and cs.docstatus = 1
		where os.docstatus = 1
			and os.pos_profile = %(pos_profile)s
			and date(os.period_start_date) <= %(date)s
			and (os.status = 'Open' or date(coalesce(cs.period_end_date, os.period_start_date)) >= %(date)s)
		order by os.period_start_date
		""",
		{"pos_profile": pos_profile, "date": date},
		as_dict=True,
	)


def get_shift_totals(shift_names):
	"""Cash / credit / qty / count / grand total of submitted invoices per opening shift.

	Cash = payments whose Mode of Payment type is Cash, net of change returned.
	Credit = all other (non-cash) payments.
	"""
	invoices = frappe.db.sql(
		"""
		select name, posa_pos_opening_shift as shift, total_qty, base_grand_total, base_change_amount
		from `tabSales Invoice`
		where docstatus = 1 and posa_pos_opening_shift in %(shifts)s
		""",
		{"shifts": shift_names},
		as_dict=True,
	)

	totals = {}
	for inv in invoices:
		t = totals.setdefault(inv.shift, frappe._dict(cash=0, credit=0, total_qty=0, total_invoices=0, grand_total=0))
		t.total_qty += flt(inv.total_qty)
		t.total_invoices += 1
		t.grand_total += flt(inv.base_grand_total)
		t.cash -= flt(inv.base_change_amount)

	if not invoices:
		return totals

	shift_of = {inv.name: inv.shift for inv in invoices}
	payments = frappe.db.sql(
		"""
		select sip.parent, sip.base_amount, mop.type
		from `tabSales Invoice Payment` sip
		left join `tabMode of Payment` mop on mop.name = sip.mode_of_payment
		where sip.parenttype = 'Sales Invoice' and sip.parent in %(invoices)s
		""",
		{"invoices": list(shift_of)},
		as_dict=True,
	)
	for p in payments:
		t = totals[shift_of[p.parent]]
		if p.type == "Cash":
			t.cash += flt(p.base_amount)
		else:
			t.credit += flt(p.base_amount)

	return totals
