# -*- coding: utf-8 -*-
"""Restrict printing of closing records to within their own business day.

A Branch Manager may VIEW the last closings any time (read permission), but a closing
receipt may only be PRINTED while its business day is still current. Once that business
day's window has passed, printing is blocked — even for the most recent records.

Enforced via a `before_print` doc-event: Frappe's /printview calls
``doc.run_method("before_print", ...)`` (frappe/www/printview.py), so throwing here stops
both the desk print icon and the POS print, while read/view is untouched.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, getdate, add_to_date


def _window_end(doc):
	"""End of the business-day window the record belongs to (= the NEXT day's start).
	Returns None when business-day control is off or the window can't be resolved."""
	from ecs_posnext.api.business_day import get_window_for_business_date, is_business_day_enabled

	profile = None
	business_date = None

	if doc.doctype == "POS Cashier Shift Closing":
		bd = doc.get("pos_business_day")
		if bd:
			row = frappe.db.get_value(
				"POS Business Day", bd, ["pos_profile", "business_date"], as_dict=True
			)
			if row:
				profile, business_date = row.pos_profile, row.business_date
		if not profile:
			profile = doc.get("pos_profile")
			business_date = getdate(doc.get("shift_end") or doc.get("shift_start") or now_datetime())
	elif doc.doctype == "POS Business Day":
		profile = doc.get("pos_profile")
		business_date = doc.get("business_date")

	if not profile or not business_date:
		return None
	if not is_business_day_enabled(profile):
		return None
	try:
		w = get_window_for_business_date(profile, getdate(business_date))
		# A business day runs from its start to the next day's start — that next start is
		# the moment printing must stop.
		return add_to_date(get_datetime(w.get("start_datetime")), days=1)
	except Exception:
		return None


def before_print_closing(doc, method=None, *args, **kwargs):
	"""Block the printout once the record's business-day window has passed."""
	if (frappe.session.user or "") == "Administrator":
		return
	end = _window_end(doc)
	if end and now_datetime() > get_datetime(end):
		frappe.throw(
			_(
				"Printing this closing is only allowed within its own business day. "
				"That business day has ended, so this record can no longer be printed."
			),
			title=_("Print Not Allowed"),
		)
