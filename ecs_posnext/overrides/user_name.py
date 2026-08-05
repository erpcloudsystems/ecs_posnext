# -*- coding: utf-8 -*-
"""
Full-name fixes.

Frappe core's `User.set_full_name` builds `full_name` from only first + last name,
silently dropping `middle_name` (see frappe/core/doctype/user/user.py). Because
Employee syncs its name onto the linked User, the User's `full_name` — which is what
shows across the app (owner columns, session, reports) — loses the middle name.

Rather than patch Frappe core (not upgrade-safe), we recompute the name in a
`validate` doc_event that runs AFTER the controller's own validate, so it wins.
"""

import frappe


def _join(*parts):
	return " ".join(p.strip() for p in parts if p and p.strip())


def user_set_full_name(doc, method=None):
	"""Include middle_name in User.full_name."""
	doc.full_name = _join(doc.first_name, doc.get("middle_name"), doc.last_name)


def employee_set_full_name(doc, method=None):
	"""Ensure Employee.employee_name includes middle_name (defensive; core already does)."""
	doc.employee_name = _join(doc.first_name, doc.get("middle_name"), doc.last_name)
