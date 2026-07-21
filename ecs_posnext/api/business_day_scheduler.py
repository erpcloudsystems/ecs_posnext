# Copyright (c) 2026, ECS and contributors
# For license information, please see license.txt
"""Scheduler jobs for the POS Business Day lifecycle.

Runs per POS Profile independently — nothing about timing is global. Transitions:
  Open --(now > sales cut-off)--> Closing Required
  --(now > mandatory deadline)--> Ready to Close (clean) | Closing Overdue (has issues)
  Ready to Close --(auto-close enabled)--> Closed
"""

import frappe
from frappe.utils import get_datetime, now_datetime

from ecs_posnext.api.business_day import get_profile_day_settings, log_pos_event

NON_CLOSED = ("Open", "Closing Required", "Closing Overdue", "Ready to Close")


def process_business_days():
	"""Entry point invoked by the scheduler (cron)."""
	now = now_datetime()
	days = frappe.get_all(
		"POS Business Day",
		filters={"status": ["in", NON_CLOSED]},
		fields=["name", "pos_profile", "status", "sales_cutoff_datetime", "mandatory_closing_deadline"],
	)
	for row in days:
		try:
			_process_one(row, now)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"POS Business Day scheduler failed for {row.name}")
	frappe.db.commit()


def _process_one(row, now):
	settings = get_profile_day_settings(row.pos_profile)
	if not settings.get("custom_enable_business_day_control"):
		return

	cutoff = get_datetime(row.sales_cutoff_datetime) if row.sales_cutoff_datetime else None
	deadline = get_datetime(row.mandatory_closing_deadline) if row.mandatory_closing_deadline else None

	# Open -> Closing Required at cut-off
	if row.status == "Open" and cutoff and now > cutoff:
		_set_status(row.name, row.pos_profile, "Open", "Closing Required")
		row.status = "Closing Required"

	# At/after the mandatory deadline, evaluate readiness
	if deadline and now > deadline and row.status in ("Open", "Closing Required", "Closing Overdue", "Ready to Close"):
		doc = frappe.get_doc("POS Business Day", row.name)
		doc.refresh_summary()
		issues = doc.evaluate_closing_issues()
		doc.save(ignore_permissions=True)

		if not issues:
			if settings.get("custom_auto_close_business_day_when_ready"):
				doc.close(force=False)
			elif doc.status != "Ready to Close":
				_set_status(row.name, row.pos_profile, doc.status, "Ready to Close")
		else:
			if doc.status != "Closing Overdue":
				_set_status(row.name, row.pos_profile, doc.status, "Closing Overdue")
				_notify_overdue(doc, issues)


def _set_status(name, pos_profile, old, new):
	frappe.db.set_value("POS Business Day", name, "status", new)
	log_pos_event(
		action="Business Day Closing",
		reference_doctype="POS Business Day",
		reference_name=name,
		pos_profile=pos_profile,
		pos_business_day=name,
		old_value=old,
		new_value=new,
	)


def _notify_overdue(doc, issues):
	"""Notify Branch Managers + Operations Management that a day is overdue."""
	recipients = _role_users(["POSNext Branch Manager", "POSNext Operations Manager"])
	if not recipients:
		return
	subject = frappe._("POS Business Day {0} is overdue").format(doc.name)
	message = frappe._("Business Day {0} ({1}) passed its closing deadline with {2} unresolved issue(s).").format(
		doc.name, doc.pos_profile, len(issues)
	)
	for user in recipients:
		try:
			notification = frappe.new_doc("Notification Log")
			notification.update(
				{
					"subject": subject,
					"email_content": message,
					"for_user": user,
					"type": "Alert",
					"document_type": "POS Business Day",
					"document_name": doc.name,
				}
			)
			notification.flags.ignore_permissions = True
			notification.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "POS Business Day overdue notification failed")


def _role_users(roles):
	users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", roles], "parenttype": "User"},
		distinct=True,
		pluck="parent",
	)
	return [u for u in users if u not in ("Administrator", "Guest") and frappe.db.get_value("User", u, "enabled")]
