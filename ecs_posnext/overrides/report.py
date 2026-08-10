# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""Lets a Query Report have optional filters.

A Query Report's SQL is bound with the filter values as named parameters, and
every caller drops the filters nobody filled in - the desk's
``get_filter_values`` keeps only truthy values, the POS filter bar does the same,
and a dashboard chart or Auto Email Report saves only what was set. So the moment
a query mentions ``%(pos_shift)s`` and the user leaves that filter empty, pymysql
raises ``KeyError: 'pos_shift'`` while it is still assembling the statement.

That is why ERPNext writes anything with an optional filter as a Script Report:
a Script Report reads its filters as a plain dict, where a missing key is simply
falsy. Putting the blank keys back before the query is bound gives a Query Report
the same freedom, without the report having to become a script.
"""

import re

import frappe
from frappe.core.doctype.report.report import Report

# The named parameters a query binds, e.g. `%(pos_shift)s`
QUERY_PARAMETER = re.compile(r"%\((\w+)\)s")


class POSReport(Report):
	def execute_query_report(self, filters):
		return super().execute_query_report(_bind_blank_filters(self, filters))


def _bind_blank_filters(report, filters):
	"""``filters``, plus a None for each optional parameter the query needs.

	Only parameters the query actually names are considered, and only when the
	report declares them as filters that are not mandatory. A mandatory filter
	that arrived blank is left missing on purpose: the query would otherwise run
	against NULL and quietly return nothing, and an empty report that looks like
	a real answer is worse than the error.
	"""
	if not isinstance(filters, dict):
		return filters

	blank = {name for name in QUERY_PARAMETER.findall(report.query or "") if _is_blank(filters.get(name))}
	if not blank:
		return filters

	from ecs_posnext.api.reports import get_report_filters

	try:
		optional = {f["fieldname"] for f in get_report_filters(report) if not f["reqd"]}
	except Exception:
		# Never let filter introspection be the reason a report fails to run;
		# without it the query simply raises the KeyError it always raised.
		frappe.log_error(
			title="Optional filter lookup failed",
			message=f"Report: {report.name}\n\n{frappe.get_traceback()}",
		)
		return filters

	prepared = dict(filters)
	for name in blank & optional:
		prepared[name] = None

	return prepared


def _is_blank(value) -> bool:
	"""Whether ``value`` is an unset filter — an unticked Check is a value, not a blank."""
	if isinstance(value, (list, tuple)):
		return not value

	return value is None or value == ""
