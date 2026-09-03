# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""Gives a Query Report the parameters only a Script Report normally gets.

A Query Report's SQL is bound with the filter values as named parameters, and
every caller drops the filters nobody filled in - the desk's
``get_filter_values`` keeps only truthy values, the POS filter bar does the same,
and a dashboard chart or Auto Email Report saves only what was set. So the moment
a query mentions ``%(pos_shift)s`` and the user leaves that filter empty, pymysql
raises ``KeyError: 'pos_shift'`` while it is still assembling the statement. The
same goes for a parameter that has no filter at all, because it is answered by
who is running the report rather than by the user.

That is why ERPNext writes anything of the sort as a Script Report: a Script
Report reads its filters as a plain dict, where a missing key is simply falsy,
and can look at the session while it builds its conditions. Filling those keys
in before the query is bound gives a Query Report the same freedom, without the
report having to become a script.

:func:`_bind_query_parameters` is the whole of it, and it runs for every caller
alike: the desk, the POS, a Prepared Report, an Auto Email Report.
"""

import re

import frappe
from frappe.core.doctype.report.report import Report

# The named parameters a query binds, e.g. `%(pos_shift)s`
QUERY_PARAMETER = re.compile(r"%\((\w+)\)s")

# Roles that are not tied to the branches they run a POS for. Someone who
# administers the whole chain reports on all of it.
UNSCOPED_ROLES = {"System Manager"}


class POSReport(Report):
	def execute_query_report(self, filters):
		return super().execute_query_report(_bind_query_parameters(self, filters))


def _pos_profile_user():
	"""The user whose POS Profiles a report scopes itself to, or None for every branch.

	A cashier has business seeing the branches they are a POS user of and no others,
	so the query restricts itself to those. Someone who administers the chain is not
	tied to a branch, so they get None and the query leaves the scope open.
	"""
	if frappe.session.user == "Administrator":
		return None

	if UNSCOPED_ROLES & set(frappe.get_roles()):
		return None

	return frappe.session.user


# Parameters a query can name that the session answers rather than the user.
#
# A report scoped through one of these needs no filter for it, so there is
# nothing for a request to name.
SESSION_PARAMETERS = {
	# The POS user whose branches the report covers; see :func:`_pos_profile_user`
	"pos_profile_user": _pos_profile_user,
}

# Parameters a query can name that only a run from the POS answers: the profile
# and branch the cashier's shift pins the run to, supplied by
# ``ecs_posnext.api.reports._scoped_parameters``. Nothing pins a run from the
# desk, so there they bind None and the query is left with whatever scope
# :data:`SESSION_PARAMETERS` gives it.
SCOPE_PARAMETERS = {"pos_profile", "branch"}


def _bind_query_parameters(report, filters):
	"""``filters``, with every parameter the query names given a value to bind.

	Only parameters the query actually names are touched, and a parameter the
	report declares a filter for is left to that filter - except a session
	parameter, which is answered by the session whatever the report says.
	"""
	if not isinstance(filters, dict):
		return filters

	named = set(QUERY_PARAMETER.findall(report.query or ""))
	if not named:
		return filters

	prepared = dict(filters)

	# Whatever arrived for a session parameter is overwritten rather than
	# validated: it is the scope the report runs under, not a choice, so a
	# request that names a value of its own is not a case worth honouring -
	# honouring it would be the way around the scope.
	for name in named & set(SESSION_PARAMETERS):
		prepared[name] = SESSION_PARAMETERS[name]()

	blank = {name for name in named if _is_blank(prepared.get(name))}
	if not blank:
		return prepared

	declared = _declared_filters(report)
	if declared is None:
		return prepared

	# An unpinned scope parameter binds None, but only where the report has no
	# filter of that name - one that does is an ordinary filter and is left to
	# the rule below.
	for name in (blank & SCOPE_PARAMETERS) - {f["fieldname"] for f in declared}:
		prepared[name] = None

	# An optional filter the user left empty binds None too. A *mandatory* one
	# that arrived blank is left missing on purpose: the query would otherwise
	# run against NULL and quietly return nothing, and an empty report that
	# looks like a real answer is worse than the error.
	for name in blank & {f["fieldname"] for f in declared if not f["reqd"]}:
		prepared[name] = None

	return prepared


def _declared_filters(report):
	"""The filters ``report`` declares, or None when they cannot be resolved."""
	from ecs_posnext.api.reports import get_report_filters

	try:
		return get_report_filters(report)
	except Exception:
		# Never let filter introspection be the reason a report fails to run;
		# without it the query simply raises the KeyError it always raised.
		frappe.log_error(
			title="Optional filter lookup failed",
			message=f"Report: {report.name}\n\n{frappe.get_traceback()}",
		)
		return None


def _is_blank(value) -> bool:
	"""Whether ``value`` is an unset filter — an unticked Check is a value, not a blank."""
	if isinstance(value, (list, tuple)):
		return not value

	return value is None or value == ""
