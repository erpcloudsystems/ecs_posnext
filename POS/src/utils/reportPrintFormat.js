/**
 * Render a report Print Format in the browser.
 *
 * Report print templates are Frappe JS templates (`print_format_type = "JS"`, or
 * a standard report's `<report_name>.html`), so the desk renders them with its
 * client-side engine and never with Jinja. The POS has to do the same: pushing
 * one through server-side Jinja fails on the very first `{% var x = 1 %}`.
 *
 * The context below is the subset of the desk's template scope that report
 * layouts actually reach for - the report data plus the number, date and
 * translation helpers Frappe exposes as globals. The POS does not load the desk
 * bundle, so those helpers are ported here.
 */

import { renderTemplate } from "@/utils/microtemplate"
import { getCurrencySymbol, getPrecision, roundTo } from "@/utils/currency"
import { formatReportValue, visibleColumns } from "@/utils/reportOutput"
import { logger } from "@/utils/logger"

const log = logger.create("reportPrintFormat")

// Ported from frappe/public/js/frappe/utils/number_format.js
const NUMBER_FORMAT_INFO = {
	"#,###.##": { decimal_str: ".", group_sep: "," },
	"#.###,##": { decimal_str: ",", group_sep: "." },
	"# ###.##": { decimal_str: ".", group_sep: " " },
	"# ###,##": { decimal_str: ",", group_sep: " " },
	"#'###.##": { decimal_str: ".", group_sep: "'" },
	"#, ###.##": { decimal_str: ".", group_sep: ", " },
	"#,##,###.##": { decimal_str: ".", group_sep: "," },
	"#,###.###": { decimal_str: ".", group_sep: "," },
	"#.###": { decimal_str: "", group_sep: "." },
	"#,###": { decimal_str: "", group_sep: "," },
}

const DEFAULT_NUMBER_FORMAT = "#,###.##"
const DEFAULT_DATE_FORMAT = "dd-mm-yyyy"

function sysdefaults() {
	return (
		(typeof window !== "undefined" && window.frappe?.boot?.sysdefaults) || {}
	)
}

function numberFormat() {
	return (
		getPrecision().number_format ||
		sysdefaults().number_format ||
		DEFAULT_NUMBER_FORMAT
	)
}

function numberFormatInfo(format) {
	const info = {
		...(NUMBER_FORMAT_INFO[format] || { decimal_str: ".", group_sep: "," }),
	}
	info.precision =
		info.decimal_str === ""
			? 0
			: (format.split(info.decimal_str).slice(1)[0] || "").length
	return info
}

function cint(value, defaultValue = 0) {
	const number = Number.parseInt(value, 10)
	return Number.isNaN(number) ? defaultValue : number
}

function cstr(value) {
	return value === null || value === undefined ? "" : String(value)
}

/** frappe.flt: tolerant parse of anything a template may hold, then optional rounding. */
function flt(value, decimals, format) {
	if (value === null || value === undefined || value === "") return 0

	let number = value
	if (typeof number !== "number") {
		number = String(number)

		// A formatted value may carry its currency symbol
		if (number.indexOf(" ") !== -1) {
			const parts = number.split(" ")
			number = Number.isNaN(Number.parseFloat(parts[0]))
				? parts.slice(parts.length - 1).join(" ")
				: number
		}

		const info = numberFormatInfo(format || numberFormat())
		if (info.group_sep) number = number.split(info.group_sep).join("")
		if (info.decimal_str && info.decimal_str !== ".") {
			number = number.split(info.decimal_str).join(".")
		}

		number = Number.parseFloat(number)
		if (Number.isNaN(number)) number = 0
	}

	return decimals === null || decimals === undefined
		? number
		: roundTo(number, cint(decimals))
}

/** frappe.format_number: group and localise a number per the system number format. */
function formatNumber(value, format, decimals) {
	const activeFormat = format || numberFormat()
	const info = numberFormatInfo(activeFormat)

	let precision = decimals
	if (precision === null || precision === undefined) {
		precision = format
			? info.precision
			: (getPrecision().float ?? info.precision)
	}
	precision = cint(precision)

	let number = flt(value, precision, activeFormat)
	const isNegative = number < 0
	number = Math.abs(number)

	const parts = number.toFixed(precision).split(".")
	if (info.group_sep) {
		parts[0] = groupDigits(
			parts[0],
			info.group_sep,
			activeFormat === "#,##,###.##",
		)
	}
	if (!parts[0]) parts[0] = "0"

	const decimalPart =
		parts[1] && info.decimal_str ? info.decimal_str + parts[1] : ""
	return (isNegative ? "-" : "") + parts[0] + decimalPart
}

/** Thousands grouping, with the 2-digit tail groups Indian formats use. */
function groupDigits(integer, separator, indian) {
	const digits = integer.split("").reverse()
	const out = []
	let size = 3

	for (let i = 0; i < digits.length; i++) {
		if (i > 0 && i === size) {
			out.push(separator)
			size += indian ? 2 : 3
		}
		out.push(digits[i])
	}

	return out.reverse().join("")
}

function formatCurrencyValue(value, currency, decimals) {
	const precision = decimals ?? getPrecision().currency ?? 2
	const formatted = formatNumber(value, null, precision)
	const symbol = currency ? getCurrencySymbol(currency) : ""
	return symbol ? `${symbol} ${formatted}` : formatted
}

// ---------------------------------------------------------------------------
// frappe.datetime
// ---------------------------------------------------------------------------

const pad = (value) => String(value).padStart(2, "0")

function nowdate() {
	const now = new Date()
	return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

function nowTime() {
	const now = new Date()
	return `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

function dateFormat() {
	return sysdefaults().date_format || DEFAULT_DATE_FORMAT
}

/**
 * frappe.datetime.str_to_user: a `YYYY-MM-DD[ HH:mm:ss]` string in the system
 * date format. Reordered textually rather than parsed through Date(), which
 * would shift the day for anyone behind UTC.
 */
function strToUser(value) {
	const text = cstr(value).trim()
	if (!text) return ""

	const match =
		/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}:\d{2})(?::\d{2})?)?/.exec(text)
	if (!match) return text

	const [, year, month, day, time] = match
	const date = dateFormat()
		.replace("yyyy", year)
		.replace("mm", month)
		.replace("dd", day)

	return time ? `${date} ${time}` : date
}

/** frappe.datetime.user_to_str: the inverse, best effort, for round-tripping. */
function userToStr(value) {
	const text = cstr(value).trim()
	if (!text) return ""
	if (/^\d{4}-\d{2}-\d{2}/.test(text)) return text

	const parts = text.split(/[^\d]+/).filter(Boolean)
	if (parts.length < 3) return text

	const order = dateFormat()
		.split(/[^a-z]+/i)
		.filter(Boolean)
	const picked = { yyyy: "", mm: "", dd: "" }
	order.forEach((token, index) => {
		if (token in picked) picked[token] = parts[index] || ""
	})

	if (!picked.yyyy || !picked.mm || !picked.dd) return text
	return `${picked.yyyy}-${pad(picked.mm)}-${pad(picked.dd)}`
}

function datetimeShim() {
	return {
		now_date: nowdate,
		nowdate,
		get_today: nowdate,
		now_time: nowTime,
		now_datetime: () => `${nowdate()} ${nowTime()}`,
		str_to_user: strToUser,
		user_to_str: userToStr,
		str_to_obj: (value) => new Date(cstr(value).replace(" ", "T")),
		obj_to_str: (value) =>
			value instanceof Date
				? `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`
				: cstr(value),
		obj_to_user: (value) =>
			strToUser(
				value instanceof Date
					? `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`
					: cstr(value),
			),
		get_user_date_fmt: dateFormat,
	}
}

/**
 * The app's `__` off `window` rather than an import: the translation module pulls
 * in the whole frappe-ui/Vue stack, which a print helper has no business needing.
 */
function translate(...args) {
	if (typeof window !== "undefined" && typeof window.__ === "function") {
		return window.__(...args)
	}
	return cstr(args[0])
}

function escapeHTML(text) {
	return cstr(text)
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;")
}

/**
 * The scope a report print template is evaluated in.
 *
 * `with(context)` means anything the template names has to be here or on
 * `window`: a missing helper is a ReferenceError that kills the whole print, so
 * this deliberately mirrors what the desk exposes as globals.
 */
export function buildTemplateContext({
	reportName,
	title,
	subtitle = "",
	columns = [],
	rows = [],
	filters = {},
	landscape = false,
	printSettings = {},
}) {
	const existing = (typeof window !== "undefined" && window.frappe) || {}

	const frappeShim = {
		...existing,
		datetime: { ...(existing.datetime || {}), ...datetimeShim() },
		utils: { ...(existing.utils || {}), escape_html: escapeHTML },
		format: (value, df) => formatReportValue(value, df),
		format_value: (value, df) => formatReportValue(value, df),
	}

	return {
		// data, under every name the desk uses for it
		data: rows,
		result: rows,
		original_data: rows,
		columns,
		visible_columns: visibleColumns(columns),
		filters,
		report_name: reportName,
		report: { report_name: reportName, name: reportName },
		title: title || reportName,
		subtitle,
		landscape,
		print_settings: printSettings,
		can_use_smaller_font: 0,

		// helpers Frappe exposes as globals
		frappe: frappeShim,
		flt,
		cint,
		cstr,
		format_number: formatNumber,
		format_currency: formatCurrencyValue,
		escape_html: escapeHTML,
		in_list: (list, value) => Array.isArray(list) && list.includes(value),
		is_null: (value) => value === null || value === undefined || value === "",
		__: translate,
	}
}

/**
 * A complete printable page for `template`, rendered against the report data.
 *
 * The A4 `@page` rule is written before the template's own styles so a receipt
 * format that declares `@page { size: 80mm auto }` still wins.
 *
 * @throws when the template fails to compile or render - the caller decides
 *         whether to fall back to the plain table layout.
 */
export function renderReportPrintFormat({
	template,
	letterhead = "",
	orientation = "Landscape",
	...context
}) {
	const body = renderTemplate(
		template,
		buildTemplateContext({
			...context,
			landscape: orientation.toLowerCase() === "landscape",
		}),
	)

	const pageSize =
		orientation.toLowerCase() === "landscape" ? "landscape" : "portrait"
	const root = typeof document !== "undefined" ? document.documentElement : null
	const dir = root?.dir === "rtl" ? "rtl" : "ltr"
	const lang = root?.lang || "en"

	log.debug(`Rendered print format for ${context.reportName}`)

	return `<!doctype html>
<html dir="${dir}" lang="${lang}">
<head>
<meta charset="utf-8">
<style>@page { size: A4 ${pageSize}; margin: 10mm; }</style>
</head>
<body>
${letterhead || ""}
${body}
</body>
</html>`
}
