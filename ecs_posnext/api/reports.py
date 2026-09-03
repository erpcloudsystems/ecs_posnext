# Copyright (c) 2026, BrainWise and contributors
# For license information, please see license.txt

"""Runs Frappe/ERPNext reports from inside the POS.

The POS is a standalone Vue app: it does not load the desk bundle, so it cannot
do what ``query_report.js`` does and evaluate a report's ``.js`` file to
discover the filters the report expects. Filter definitions are resolved server
side instead, in the same order the desk resolves them:

1. the ``filters: [...]`` literal parsed out of the report's client script, then
2. the Report's own ``filters`` child table, for reports with no script
   (Report Builder and UI-authored Query Reports).

The order matters: the desk uses the child table *only* when the script defines
no filters, so resolving the child table first would show the cashier a
different filter bar than the desk shows — different fieldtypes, different
defaults — for the same report.

Step 1 reads a JavaScript literal, so values that are function calls cannot
always be resolved. The common ones the ERPNext reports use for defaults
(``frappe.datetime.*``, ``frappe.defaults.get_user_default``, ``__()``) are
evaluated here; anything else degrades to an empty default, which leaves the
cashier to pick a value rather than silently using a wrong one.
"""

import json
import os
import re

import frappe
from frappe import _
from frappe.modules import get_module_path, scrub
from frappe.utils import (
	add_days,
	add_months,
	cint,
	get_first_day,
	get_last_day,
	now_datetime,
	nowdate,
)

from ecs_posnext.pos_next.doctype.pos_report_settings.pos_report_settings import (
	get_pos_report_rows,
)

# Fieldtypes the POS filter bar knows how to render. Anything else is passed
# through as Data so the filter is still usable, just untyped.
SUPPORTED_FIELDTYPES = {
	"Data",
	"Select",
	"Link",
	"Date",
	"DateRange",
	"Datetime",
	"Check",
	"Int",
	"Float",
	"Currency",
	"MultiSelectList",
	"Percent",
	"Small Text",
	"Text",
	"Time",
}

# Stands for the ``<report_name>.html`` layout shipped beside a standard report's
# script; it has no Print Format document to name it by.
REPORT_LAYOUT = "__report_html__"

# Which engine owns a print template. Matches Print Format's print_format_type.
JS_TEMPLATE = "JS"
JINJA_TEMPLATE = "Jinja"

# A report run from the POS only ever shows the shift the cashier is on, so any
# filter that picks the shift's POS Profile - or the Branch that profile belongs
# to - is pinned to it and locked. Reports name such a filter by its link
# doctype, but a plain Data/Select one is matched by fieldname too.
BRANCH_DOCTYPE = "Branch"
BRANCH_FIELDNAMES = {"branch", "custom_branch"}

POS_PROFILE_DOCTYPE = "POS Profile"
POS_PROFILE_FIELDNAMES = {"pos_profile"}

SCOPED_FILTERS = (
	(BRANCH_DOCTYPE, BRANCH_FIELDNAMES),
	(POS_PROFILE_DOCTYPE, POS_PROFILE_FIELDNAMES),
)

# The same scope, for a Query Report that shows no filter for it: the query names
# the parameter and the shift answers it. Keyed by the doctype the value belongs
# to, like the scope itself. Kept in step with
# ``ecs_posnext.overrides.report.SCOPE_PARAMETERS``, which is what binds None for
# these when the run is not a POS one.
SCOPED_PARAMETERS = {
	"branch": BRANCH_DOCTYPE,
	"pos_profile": POS_PROFILE_DOCTYPE,
}

# Keys worth keeping off a parsed filter definition; the rest (get_query,
# on_change, get_data, formatter, ...) are functions with no server-side meaning.
FILTER_KEYS = {
	"fieldname",
	"label",
	"fieldtype",
	"options",
	"default",
	"reqd",
	"mandatory",
	"hidden",
	"width",
	"depends_on",
	"wildcard_filter",
	"read_only",
	"placeholder",
	"description",
}


# ---------------------------------------------------------------------------
# Whitelisted endpoints
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_pos_reports(pos_profile: str | None = None) -> list[dict]:
	"""Reports configured for the POS that the current user may actually run."""
	reports = []
	for row in get_pos_report_rows(pos_profile):
		report = _get_permitted_report(row.report, raise_exception=False)
		if not report:
			continue
		reports.append(
			{
				"report": row.report,
				"label": _(row.label),
				"icon": row.icon,
				"report_type": report.report_type,
				"ref_doctype": report.ref_doctype,
				"can_export": _can_export(report.ref_doctype),
			}
		)

	return reports


@frappe.whitelist()
def get_report_definition(report_name: str, pos_profile: str | None = None) -> dict:
	"""Filter definitions and metadata needed to render ``report_name`` in the POS."""
	row = _get_configured_row(report_name, pos_profile)
	report = _get_permitted_report(report_name)

	filters = get_report_filters(report)
	_scope_filters(filters, _pos_scope(pos_profile))

	return {
		"report": report_name,
		"label": _(row.label),
		"icon": row.icon,
		"report_type": report.report_type,
		"ref_doctype": report.ref_doctype,
		"add_total_row": cint(report.add_total_row),
		"can_export": _can_export(report.ref_doctype),
		"filters": filters,
		"print_layouts": get_print_layouts(report),
	}


@frappe.whitelist()
def run_pos_report(
	report_name: str, filters: str | dict | None = None, pos_profile: str | None = None
) -> dict:
	"""Run a POS-configured report and return its columns and rows.

	Thin wrapper over the desk runner: it adds the check that the report is one
	the POS is configured to show, so this endpoint cannot be used to run
	arbitrary reports, and it forces a synchronous run because the POS has no
	Prepared Report inbox to collect a background result from.
	"""
	_get_configured_row(report_name, pos_profile)
	report = _get_permitted_report(report_name)

	from frappe.desk.query_report import run

	if isinstance(filters, str):
		filters = json.loads(filters or "{}")

	result = run(
		report_name,
		filters=_prepare_filters(report, filters or {}, pos_profile),
		ignore_prepared_report=True,
		are_default_filters=False,
	)

	return {
		"columns": result.get("columns") or [],
		"result": result.get("result") or [],
		"message": result.get("message"),
		"report_summary": result.get("report_summary"),
		"skip_total_row": cint(result.get("skip_total_row")),
		"add_total_row": cint(result.get("add_total_row")),
		"execution_time": result.get("execution_time"),
	}


@frappe.whitelist()
def render_report_print(
	report_name: str,
	print_layout: str | None = None,
	filters: str | dict | None = None,
	orientation: str = "Portrait",
	with_letterhead: int = 0,
	pos_profile: str | None = None,
) -> str:
	"""Render ``report_name`` with ``print_layout`` and return a complete printable HTML page.

	Server-side rendering is Jinja, so only a Jinja layout can come through here.
	A ``JS`` layout is a client-side template and is rendered in the browser off
	:func:`get_print_template` instead.
	"""
	_get_configured_row(report_name, pos_profile)
	report = _get_permitted_report(report_name)

	template, template_type = "", JINJA_TEMPLATE
	if print_layout:
		# Resolved before the report is run so an unsupported layout fails fast
		template, template_type = _resolve_print_template(report, print_layout)

		if template_type == JS_TEMPLATE:
			# Jinja cannot execute a JS template: `{% var x = 1 %}` is not a Jinja
			# tag, so rendering one here raises TemplateSyntaxError.
			frappe.throw(
				_(
					"Print layout {0} is a client-side (JS) template and cannot be rendered on the server. Reload the POS so it prints this layout in the browser."
				).format(frappe.bold(print_layout))
			)

	if isinstance(filters, str):
		filters = json.loads(filters or "{}")
	filters = _prepare_filters(report, filters or {}, pos_profile)

	from frappe.desk.query_report import run

	result = run(
		report_name,
		filters=filters,
		ignore_prepared_report=True,
		are_default_filters=False,
	)
	columns = result.get("columns") or []
	rows = result.get("result") or []

	body = ""
	if template:
		context = frappe._dict(
			report_name=report_name,
			title=_(report.report_name),
			data=rows,
			columns=columns,
			filters=filters,
			result=rows,
		)
		body = frappe.render_template(template, context)

	letterhead_html = _letterhead_html() if cint(with_letterhead) else ""

	page_size = "landscape" if orientation.lower() == "landscape" else "portrait"
	dir_attr = frappe.local.lang_direction or "ltr"

	return f"""<!doctype html>
<html dir="{dir_attr}">
<head>
<meta charset="utf-8">
<style>@page {{ size: A4 {page_size}; margin: 10mm; }}</style>
</head>
<body>
{letterhead_html}
{body}
</body>
</html>"""


@frappe.whitelist()
def search_filter_options(
	doctype: str,
	txt: str = "",
	filters: str | dict | list | None = None,
	page_length: int = 20,
) -> list[dict]:
	"""Link-field lookup for the POS report filter bar.

	Wraps the desk search so the POS gets a stable ``{value, description}`` shape
	regardless of how the target doctype configures its title/search fields.
	"""
	from frappe.desk.search import search_link

	if isinstance(filters, str):
		filters = json.loads(filters or "null")

	results = search_link(
		doctype,
		txt or "",
		filters=filters,
		page_length=cint(page_length) or 20,
	)

	return [
		{"value": row.get("value"), "description": row.get("description") or ""}
		for row in results
	]


@frappe.whitelist()
def get_print_template(
	report_name: str,
	print_layout: str | None = None,
	pos_profile: str | None = None,
	with_letterhead: int = 0,
) -> dict:
	"""The template the POS should render when printing ``report_name``.

	``print_layout`` is a name from ``get_print_layouts``. Only layouts that
	belong to this report are readable here, so this cannot be used to pull
	arbitrary Print Formats.

	``template_type`` tells the caller which engine owns the template: ``JS``
	templates must be rendered in the browser, ``Jinja`` ones on the server via
	:func:`render_report_print`.
	"""
	_get_configured_row(report_name, pos_profile)
	report = _get_permitted_report(report_name)

	template, template_type = _resolve_print_template(report, print_layout)

	return {
		"layout": print_layout,
		"template": template,
		"template_type": template_type,
		"letterhead": _letterhead_html() if cint(with_letterhead) else "",
	}


def _resolve_print_template(report, print_layout: str | None) -> tuple[str, str]:
	"""``(template, engine)`` for a layout of ``report``.

	A report's own ``<report_name>.html`` is always a client-side template - that
	is the only engine the desk ever renders it with - while a Print Format
	declares its engine in ``print_format_type``.
	"""
	if not print_layout:
		return "", JS_TEMPLATE

	if print_layout == REPORT_LAYOUT:
		return _get_report_html_format(report) or "", JS_TEMPLATE

	for layout in get_print_layouts(report):
		if layout["name"] != print_layout or layout["name"] == REPORT_LAYOUT:
			continue

		print_format = frappe.get_cached_doc("Print Format", print_layout)
		# Same shape the desk composes: the format's own CSS travels with its HTML
		css = f"<style>{print_format.css}</style>" if print_format.css else ""
		engine = JS_TEMPLATE if print_format.print_format_type == JS_TEMPLATE else JINJA_TEMPLATE
		return css + (print_format.html or ""), engine

	frappe.throw(
		_("Print Format {0} is not available for report {1}.").format(
			frappe.bold(print_layout), frappe.bold(report.name)
		),
		frappe.PermissionError,
	)


def _letterhead_html() -> str:
	lh_name = frappe.db.get_value("Letter Head", {"is_default": 1}, "name")
	if not lh_name:
		return ""

	return frappe.get_cached_doc("Letter Head", lh_name).content or ""


def get_print_layouts(report) -> list[dict]:
	"""Print layouts linked to ``report``, the default one first.

	Two sources, matching the desk: Print Formats saved with
	``print_format_for = Report``, and the ``<report_name>.html`` layout that
	ships beside a standard report's script. A linked Print Format wins as the
	default because it is the one somebody deliberately created for this report.
	"""
	layouts = [
		{"name": row.name, "label": _(row.name), "source": "Print Format"}
		for row in frappe.get_all(
			"Print Format",
			filters={
				"print_format_for": "Report",
				"report": report.name,
				"disabled": 0,
			},
			fields=["name"],
			order_by="name asc",
		)
	]

	if _get_report_html_format(report):
		layouts.append(
			{"name": REPORT_LAYOUT, "label": _("Report Layout"), "source": "Report"}
		)

	return layouts


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


def _get_configured_row(report_name: str, pos_profile: str | None = None) -> frappe._dict:
	for row in get_pos_report_rows(pos_profile):
		if row.report == report_name:
			return row

	frappe.throw(
		_("Report {0} is not available in the POS.").format(frappe.bold(report_name)),
		frappe.PermissionError,
	)


def _get_permitted_report(report_name: str, raise_exception: bool = True):
	"""The Report doc, or None/PermissionError when the user cannot run it.

	Mirrors the desk's two-part gate: the report's own Roles table, plus
	``report`` permission on the doctype it reports on.
	"""
	if not frappe.db.exists("Report", report_name):
		if raise_exception:
			frappe.throw(_("Report {0} not found.").format(frappe.bold(report_name)))
		return None

	report = frappe.get_cached_doc("Report", report_name)

	problem = None
	if report.disabled:
		problem = _("Report {0} is disabled.").format(frappe.bold(report_name))
	elif not report.is_permitted():
		problem = _("You don't have access to Report: {0}").format(frappe.bold(report_name))
	elif report.ref_doctype and not frappe.has_permission(report.ref_doctype, "report"):
		problem = _("You don't have permission to get a report on: {0}").format(
			frappe.bold(report.ref_doctype)
		)

	if problem:
		if raise_exception:
			frappe.throw(problem, frappe.PermissionError)
		return None

	return report


def _can_export(ref_doctype: str | None) -> bool:
	"""Whether Export would succeed, so the POS can hide the button instead of failing."""
	if not ref_doctype:
		return False
	try:
		return bool(frappe.permissions.can_export(ref_doctype, raise_exception=False))
	except Exception:
		return False


# ---------------------------------------------------------------------------
# Filter resolution
# ---------------------------------------------------------------------------


def get_report_filters(report) -> list[dict]:
	"""Normalised filter definitions for ``report`` (a Report doc)."""
	# Script first, child table second - the order query_report.js uses
	raw = _filters_from_script(report) or _filters_from_report_doc(report)

	filters = [f for f in (_normalise_filter(f) for f in raw) if f]
	_resolve_dependent_lookups(filters)

	return filters


def _filters_from_report_doc(report) -> list[dict]:
	"""Filters defined on the Report document itself (the Filters child table)."""
	return [
		{
			"fieldname": row.fieldname,
			"label": row.label,
			"fieldtype": row.fieldtype,
			"options": row.options,
			"default": row.default,
			"reqd": cint(row.mandatory),
			"wildcard_filter": cint(row.wildcard_filter),
		}
		for row in (report.get("filters") or [])
		if row.fieldname
	]


def _filters_from_script(report) -> list[dict]:
	"""Filters parsed out of the report's client script."""
	script = _get_report_script(report)
	if not script:
		return []

	try:
		return _extract_filters(script)
	except Exception:
		# A parse failure must not stop the report from opening — the cashier
		# simply gets no filter bar rather than an error page.
		frappe.log_error(
			title="POS report filter parsing failed",
			message=f"Report: {report.name}\n\n{frappe.get_traceback()}",
		)
		return []


def _get_report_script(report) -> str | None:
	"""The report's JS, from disk for standard reports or the ``javascript`` field."""
	script_path = _report_file_path(report, "js")
	if script_path:
		with open(script_path) as f:
			return f.read()

	return report.javascript or None


def _get_report_html_format(report) -> str | None:
	"""The ``<report_name>.html`` print layout that ships beside a standard report."""
	print_path = _report_file_path(report, "html")
	if not print_path:
		return None

	from frappe.utils import get_html_format

	return get_html_format(print_path)


def _report_file_path(report, extension: str) -> str | None:
	"""Path to the report's ``.js``/``.html`` file on disk, if it has one.

	A Custom Report has no folder of its own — it borrows the script and print
	layout of the report it was derived from. Custom modules live only in the
	database, so they have no folder either.
	"""
	if report.report_type == "Custom Report" and report.reference_report:
		report = frappe.get_cached_doc("Report", report.reference_report)

	module = report.module or (
		report.ref_doctype and frappe.db.get_value("DocType", report.ref_doctype, "module")
	)
	if not module or frappe.get_cached_value("Module Def", module, "custom"):
		return None

	try:
		path = os.path.join(
			get_module_path(module),
			"report",
			scrub(report.name),
			f"{scrub(report.name)}.{extension}",
		)
	except Exception:
		return None

	return path if os.path.exists(path) else None


def _normalise_filter(raw: dict) -> dict | None:
	"""Shape one parsed filter into what the POS filter bar consumes.

	The POS gets an unambiguous shape rather than the desk's polymorphic
	``options``: ``values`` holds a fixed list to pick from, ``link_doctype``
	the doctype to search, and ``link_doctype_from`` the name of a sibling
	filter that supplies the doctype at runtime (as General Ledger's Party does).
	"""
	fieldname = raw.get("fieldname")
	if not fieldname or not isinstance(fieldname, str):
		return None

	fieldtype = raw.get("fieldtype") or "Data"
	if not isinstance(fieldtype, str) or fieldtype not in SUPPORTED_FIELDTYPES:
		# Autocomplete, Dynamic Link and friends have no POS widget; typed in by hand
		fieldtype = "Data"

	options = raw.get("options")
	values = None
	link_doctype = None

	if fieldtype == "Select":
		values = _as_value_list(options) or None
	elif fieldtype == "MultiSelectList" and isinstance(options, list):
		# A string here names the doctype to search, an array is a fixed value list
		values = _as_value_list(options) or None

	if fieldtype in ("Link", "MultiSelectList") and isinstance(options, str):
		link_doctype = options

	if fieldtype == "Select" and not values:
		# Options built at runtime (currency lists, dimensions, ...) cannot be
		# resolved here, so let the value be typed instead of offering an empty list
		fieldtype = "Data"
	if fieldtype == "Link" and not link_doctype:
		fieldtype = "Data"

	default = raw.get("default")
	if fieldtype == "MultiSelectList":
		default = _as_value_list(default) or []
	elif isinstance(default, (dict, list)):
		default = None
	elif fieldtype == "Check":
		default = cint(bool(default))
	elif fieldtype in ("Date", "Datetime"):
		default = _resolve_date_keyword(default, fieldtype)

	return {
		"fieldname": fieldname,
		"label": _(raw.get("label") or fieldname.replace("_", " ").title()),
		"fieldtype": fieldtype,
		"values": values,
		"link_doctype": link_doctype,
		"link_doctype_from": None,
		"default": default,
		"reqd": cint(bool(raw.get("reqd") or raw.get("mandatory"))),
		"hidden": cint(bool(raw.get("hidden"))),
		"read_only": cint(bool(raw.get("read_only"))),
		"width": raw.get("width"),
		"description": raw.get("description"),
	}


def _resolve_date_keyword(default, fieldtype: str):
	"""Turn a keyword default such as ``Today`` into an actual date.

	A Report Filter's ``default`` column is plain text, so a date filter defined
	through the UI carries the framework's keyword rather than a value. Sending
	the keyword on to the report would put the literal string ``Today`` into the
	query's WHERE clause, which matches nothing.
	"""
	if not isinstance(default, str):
		return default

	keyword = default.strip().lower()
	if keyword == "now":
		return str(now_datetime()) if fieldtype == "Datetime" else nowdate()

	days = {"today": 0, "yesterday": -1, "tomorrow": 1}.get(keyword)
	if days is None:
		return default

	return str(add_days(nowdate(), days))


def _resolve_dependent_lookups(filters: list[dict]) -> None:
	"""Repoint lookups whose ``options`` named a sibling filter, not a doctype.

	General Ledger's Party filter is declared as ``options: "party_type"``: the
	doctype to search is whatever Party Type currently holds. Anything that is
	neither a doctype nor a sibling fieldname is dropped, leaving a plain input.
	"""
	fieldnames = {f["fieldname"] for f in filters}

	for f in filters:
		doctype = f.get("link_doctype")
		if not doctype or frappe.db.exists("DocType", doctype):
			continue

		f["link_doctype"] = None
		if doctype in fieldnames:
			f["link_doctype_from"] = doctype
		elif f["fieldtype"] == "Link":
			f["fieldtype"] = "Data"


# ---------------------------------------------------------------------------
# Shift scoping
# ---------------------------------------------------------------------------


def _pos_scope(pos_profile: str | None) -> dict[str, str]:
	"""The values the cashier's shift fixes, keyed by the doctype they belong to.

	A report run from the POS covers one shift, so the POS Profile that shift was
	opened with - and the Branch that profile belongs to - are facts about the
	run, not choices. When the caller did not name a profile, the user's own open
	shift supplies it, so the scope cannot be sidestepped by leaving the argument
	out.
	"""
	if not pos_profile:
		pos_profile = frappe.db.get_value(
			"POS Opening Shift",
			{"user": frappe.session.user, "status": "Open", "docstatus": 1},
			"pos_profile",
			order_by="period_start_date desc",
		)

	if not pos_profile:
		return {}

	scope = {POS_PROFILE_DOCTYPE: pos_profile}

	if frappe.get_meta("POS Profile").has_field("branch"):
		branch = frappe.db.get_value("POS Profile", pos_profile, "branch")
		if branch:
			scope[BRANCH_DOCTYPE] = branch

	return scope


def _scoped_value(f: dict, scope: dict[str, str]):
	"""The value the shift fixes filter ``f`` to, or None when it fixes nothing.

	Shaped the way the filter expects to receive it, so a MultiSelectList gets a
	list where a Link gets a bare name.
	"""
	for doctype, fieldnames in SCOPED_FILTERS:
		value = scope.get(doctype)
		if not value:
			continue
		if f.get("link_doctype") == doctype or f.get("fieldname") in fieldnames:
			return [value] if f.get("fieldtype") == "MultiSelectList" else value

	return None


def _scope_filters(filters: list[dict], scope: dict[str, str]) -> None:
	"""Pin every scoped filter to the shift's value and lock it against editing.

	Cosmetic only — :func:`_prepare_filters` is what actually holds the scope.
	This is so the cashier sees which profile and branch the figures are for
	instead of an empty filter that looks like it covers the whole company.
	"""
	for f in filters:
		value = _scoped_value(f, scope)
		if value is None:
			continue
		f["default"] = value
		f["read_only"] = 1


def _prepare_filters(report, filters: dict, pos_profile: str | None) -> dict:
	"""The filter values to run ``report`` with, scoped to the cashier's shift.

	Whatever the client sent for a scoped filter is discarded rather than
	validated: those filters are locked in the POS, so a request naming another
	profile is not a case worth honouring, and silently correcting it keeps the
	report from erroring out.

	Filters the cashier left empty stay out of the dict. A Query Report needs
	them present to bind its SQL parameters, but that is put right for every
	caller in :mod:`ecs_posnext.overrides.report`, not here.
	"""
	prepared = dict(filters or {})
	scope = _pos_scope(pos_profile)

	for f in get_report_filters(report):
		value = _scoped_value(f, scope)
		if value is not None:
			prepared[f["fieldname"]] = value

	prepared.update(_scoped_parameters(report, scope))

	return prepared


def _scoped_parameters(report, scope: dict[str, str]) -> dict[str, str]:
	"""The shift's values for the query parameters ``report`` declares no filter for.

	A report can be scoped without offering the cashier a branch to pick - the
	query names the parameter and gets the answer from here. Without this the
	report would fall back to whatever scope the query applies when nothing pins
	the run, which for a cashier is every branch they are a POS user of rather
	than the one they are standing in.

	A parameter the report *does* declare a filter for is left alone: that one is
	handled above, where the filter it belongs to is also locked in the filter bar.
	"""
	if report.report_type != "Query Report":
		return {}

	from ecs_posnext.overrides.report import QUERY_PARAMETER

	named = set(QUERY_PARAMETER.findall(report.query or ""))
	declared = {f["fieldname"] for f in get_report_filters(report)}

	return {
		name: scope[doctype]
		for name, doctype in SCOPED_PARAMETERS.items()
		if name in named and name not in declared and scope.get(doctype)
	}


def _as_value_list(options) -> list[str]:
	"""A fixed option list, from a newline string, an array, or an array of dicts."""
	if isinstance(options, str):
		return [o.strip() for o in options.split("\n") if o.strip()]
	if isinstance(options, list):
		flat = []
		for option in options:
			if isinstance(option, dict):
				value = option.get("value") or option.get("label")
			else:
				value = option
			if value not in (None, ""):
				flat.append(str(value))
		return flat
	return []


# ---------------------------------------------------------------------------
# JavaScript literal parsing
#
# Just enough of a reader to lift `filters: [ {...}, {...} ]` out of a report
# script. It is deliberately not a JS engine: strings, comments and nesting are
# respected so the array can be sliced accurately, and each value is then
# matched against the handful of expressions ERPNext reports actually use.
# ---------------------------------------------------------------------------

_STRING_QUOTES = ("'", '"', "`")


def _extract_filters(script: str) -> list[dict]:
	"""Every ``filters: [...]`` array in ``script``, first non-empty one wins."""
	for match in re.finditer(r"""["']?filters["']?\s*:\s*\[""", script):
		start = script.index("[", match.start())
		array = _read_balanced(script, start, "[", "]")
		if array is None:
			continue

		parsed = []
		for entry in _split_top_level(array[1:-1]):
			entry = _strip_comments(entry).strip()
			if not entry.startswith("{"):
				continue
			obj = _parse_object(entry)
			if obj.get("fieldname"):
				parsed.append(obj)

		if parsed:
			return parsed

	return []


def _read_balanced(text: str, start: int, opener: str, closer: str) -> str | None:
	"""``text`` from ``start`` up to and including the matching ``closer``."""
	depth = 0
	i = start
	length = len(text)

	while i < length:
		char = text[i]

		if char in _STRING_QUOTES:
			i = _skip_string(text, i)
			continue
		if char == "/" and i + 1 < length and text[i + 1] in "/*":
			i = _skip_comment(text, i)
			continue

		if char == opener:
			depth += 1
		elif char == closer:
			depth -= 1
			if depth == 0:
				return text[start : i + 1]
		i += 1

	return None


def _skip_string(text: str, i: int) -> int:
	"""Index just past the string literal that starts at ``i``."""
	quote = text[i]
	i += 1
	while i < len(text):
		if text[i] == "\\":
			i += 2
			continue
		if text[i] == quote:
			return i + 1
		i += 1
	return i


def _skip_comment(text: str, i: int) -> int:
	"""Index just past the comment that starts at ``i``."""
	if text[i + 1] == "/":
		end = text.find("\n", i)
		return len(text) if end == -1 else end + 1
	end = text.find("*/", i)
	return len(text) if end == -1 else end + 2


def _strip_comments(text: str) -> str:
	out = []
	i = 0
	length = len(text)
	while i < length:
		char = text[i]
		if char in _STRING_QUOTES:
			end = _skip_string(text, i)
			out.append(text[i:end])
			i = end
			continue
		if char == "/" and i + 1 < length and text[i + 1] in "/*":
			i = _skip_comment(text, i)
			continue
		out.append(char)
		i += 1
	return "".join(out)


def _split_top_level(text: str, separator: str = ",") -> list[str]:
	"""Split on ``separator`` at nesting depth zero, ignoring strings/comments."""
	parts = []
	depth = 0
	buffer = []
	i = 0
	length = len(text)

	while i < length:
		char = text[i]

		if char in _STRING_QUOTES:
			end = _skip_string(text, i)
			buffer.append(text[i:end])
			i = end
			continue
		if char == "/" and i + 1 < length and text[i + 1] in "/*":
			end = _skip_comment(text, i)
			buffer.append(" ")
			i = end
			continue

		if char in "[{(":
			depth += 1
		elif char in "]})":
			depth -= 1

		if char == separator and depth == 0:
			parts.append("".join(buffer))
			buffer = []
		else:
			buffer.append(char)
		i += 1

	tail = "".join(buffer).strip()
	if tail:
		parts.append(tail)

	return [p for p in (part.strip() for part in parts) if p]


def _parse_object(text: str) -> dict:
	"""A ``{ key: value }`` literal as a dict, keeping only FILTER_KEYS."""
	text = text.strip()
	if text.startswith("{"):
		text = text[1:]
	if text.endswith("}"):
		text = text[:-1]

	obj = {}
	for entry in _split_top_level(text):
		key, value = _split_key_value(entry)
		if not key:
			continue

		if key in ("get_data", "get_query") and "options" not in obj:
			# MultiSelectList / Link filters name their target doctype only
			# inside these callbacks, e.g. frappe.db.get_link_options("Item", txt)
			doctype = _doctype_from_callback(value)
			if doctype:
				obj["options"] = doctype
			continue

		if key not in FILTER_KEYS:
			continue

		obj[key] = _parse_value(value)

	return obj


def _split_key_value(entry: str) -> tuple[str | None, str]:
	"""Split ``key: value`` on the first top-level colon."""
	depth = 0
	i = 0
	length = len(entry)

	while i < length:
		char = entry[i]
		if char in _STRING_QUOTES:
			i = _skip_string(entry, i)
			continue
		if char in "[{(":
			depth += 1
		elif char in "]})":
			depth -= 1
		elif char == ":" and depth == 0:
			key = entry[:i].strip().strip("\"'`")
			return key or None, entry[i + 1 :].strip()
		i += 1

	return None, ""


def _doctype_from_callback(value: str) -> str | None:
	match = re.search(
		r"""(?:get_link_options|search_link|get_list|get_all)\(\s*["']([^"']+)["']""", value
	)
	if match:
		return match.group(1)
	match = re.search(r"""doctype\s*:\s*["']([^"']+)["']""", value)
	return match.group(1) if match else None


def _parse_value(text: str):
	"""Best-effort evaluation of a JS value literal or a known helper call."""
	text = _strip_comments(text).strip().rstrip(",").strip()
	if not text:
		return None

	if text[0] in _STRING_QUOTES:
		return _unquote(text)

	if text in ("true", "false"):
		return text == "true"
	if text in ("null", "undefined"):
		return None

	if re.fullmatch(r"-?\d+", text):
		return int(text)
	if re.fullmatch(r"-?\d*\.\d+", text):
		return float(text)

	if text.startswith("["):
		array = _read_balanced(text, 0, "[", "]") or text
		return [_parse_value(item) for item in _split_top_level(array[1:-1])]

	if text.startswith("{"):
		return _parse_object_verbatim(text)

	if text.startswith("__("):
		inner = _read_balanced(text, text.index("("), "(", ")")
		if inner:
			args = _split_top_level(inner[1:-1])
			return _parse_value(args[0]) if args else None
		return None

	return _eval_helper(text)


def _parse_object_verbatim(text: str) -> dict:
	"""A nested object literal, keeping every key (used by MultiSelectList defaults)."""
	body = (_read_balanced(text, 0, "{", "}") or text)[1:-1]
	obj = {}
	for entry in _split_top_level(body):
		key, value = _split_key_value(entry)
		if key:
			obj[key] = _parse_value(value)
	return obj


def _unquote(text: str) -> str:
	end = _skip_string(text, 0)
	body = text[1 : end - 1]
	return body.encode("utf-8").decode("unicode_escape")


def _eval_helper(text: str):
	"""Evaluate the date/default helpers ERPNext reports use for filter defaults."""
	text = re.sub(r"\s+", "", text)

	simple = {
		"frappe.datetime.get_today()": nowdate,
		"frappe.datetime.nowdate()": nowdate,
		"frappe.datetime.now_date()": nowdate,
		"frappe.datetime.month_start()": lambda: str(get_first_day(nowdate())),
		"frappe.datetime.month_end()": lambda: str(get_last_day(nowdate())),
		"frappe.datetime.year_start()": lambda: nowdate()[:4] + "-01-01",
		"frappe.datetime.year_end()": lambda: nowdate()[:4] + "-12-31",
	}
	if text in simple:
		return simple[text]()

	match = re.fullmatch(r"frappe\.datetime\.add_days\((.+),(-?\d+)\)", text)
	if match:
		base = _parse_value(match.group(1))
		return str(add_days(base, int(match.group(2)))) if base else None

	match = re.fullmatch(r"frappe\.datetime\.add_months\((.+),(-?\d+)\)", text)
	if match:
		base = _parse_value(match.group(1))
		return str(add_months(base, int(match.group(2)))) if base else None

	match = re.fullmatch(r"""frappe\.defaults\.get_user_default\(["']([^"']+)["']\)""", text)
	if match:
		return frappe.defaults.get_user_default(match.group(1))

	match = re.fullmatch(r"""frappe\.defaults\.get_default\(["']([^"']+)["']\)""", text)
	if match:
		return frappe.defaults.get_defaults().get(match.group(1))

	# Anything else (fiscal-year lookups, custom helpers, inline functions) is
	# left unset so the cashier picks the value instead of inheriting a guess
	return None
