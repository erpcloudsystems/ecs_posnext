/**
 * Rendering, printing and exporting helpers for reports shown inside the POS.
 *
 * Export deliberately reuses the framework endpoint (`export_query`) instead of
 * building files here, so a POS export is byte-for-byte what the desk produces.
 * That endpoint answers with a file attachment rather than JSON, so it is driven
 * by a form POST into a hidden iframe — an iframe rather than the top window
 * because a failed export would otherwise navigate the POS away mid-shift.
 */

import { ensureCSRFToken } from "@/utils/csrf"
import { logger } from "@/utils/logger"

const log = logger.create("reportOutput")

const EXPORT_ENDPOINT = "/api/method/frappe.desk.query_report.export_query"
const EXPORT_FRAME_NAME = "pos-report-export-frame"
const PRINT_FRAME_NAME = "pos-report-print-frame"

// A download fires no load event, so a load means the server answered with a
// page — an error. Give it long enough that a slow report is not called a
// failure, but not so long that the caller's spinner outlives the download.
const EXPORT_SETTLE_MS = 4000

const NUMERIC_FIELDTYPES = new Set(["Currency", "Float", "Int", "Percent"])

/**
 * Cell value for a column, whichever shape the report returned rows in.
 * Reports may key rows by fieldname or by label, or return plain arrays.
 */
export function getCellValue(row, column, columnIndex) {
	if (Array.isArray(row)) return row[columnIndex]
	if (!row || typeof row !== "object") return row

	const byFieldname = row[column.fieldname]
	if (byFieldname !== undefined) return byFieldname
	return row[column.label]
}

export function isNumericColumn(column) {
	return NUMERIC_FIELDTYPES.has(column?.fieldtype)
}

/**
 * Display value for a report cell.
 *
 * Currency is intentionally shown without a symbol: a report can mix company
 * and party currencies in one row, and a single POS-profile symbol stamped on
 * every column would be wrong more often than it is right.
 */
export function formatReportValue(value, column) {
	if (value === null || value === undefined || value === "") return ""

	const fieldtype = column?.fieldtype
	const precision = Number.isFinite(column?.precision) ? column.precision : null

	if (fieldtype === "Check") return value ? "✓" : ""

	if (NUMERIC_FIELDTYPES.has(fieldtype)) {
		const number = Number.parseFloat(value)
		if (Number.isNaN(number)) return String(value)

		if (fieldtype === "Int") return number.toLocaleString()

		const decimals = precision ?? 2
		const formatted = number.toLocaleString(undefined, {
			minimumFractionDigits: decimals,
			maximumFractionDigits: decimals,
		})
		return fieldtype === "Percent" ? `${formatted}%` : formatted
	}

	if (fieldtype === "Date") return formatDateValue(value)
	if (fieldtype === "Datetime") {
		const parsed = new Date(String(value).replace(" ", "T"))
		return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString()
	}

	return String(value)
}

function formatDateValue(value) {
	// Report dates arrive as YYYY-MM-DD; parsing them through Date() would shift
	// the day for anyone behind UTC, so reorder the parts directly
	const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value))
	if (match) return `${match[3]}/${match[2]}/${match[1]}`
	return String(value)
}

export function visibleColumns(columns) {
	return (columns || []).filter((column) => column && !column.hidden)
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

/**
 * Download the report as CSV or Excel through the framework's export endpoint.
 *
 * @param {Object} options
 * @param {string} options.reportName
 * @param {Object} options.filters - filter values as sent to the report
 * @param {Object} options.appliedFilters - label -> value, printed into the file
 * @param {"CSV"|"Excel"} options.fileFormat
 * @returns {Promise<void>} rejects with the server's message if the export failed
 */
export async function exportReport({
	reportName,
	filters = {},
	appliedFilters = {},
	fileFormat = "Excel",
}) {
	await ensureCSRFToken({ silent: true })

	const iframe = getFrame(EXPORT_FRAME_NAME)
	const form = document.createElement("form")
	form.method = "POST"
	form.action = EXPORT_ENDPOINT
	form.target = iframe.name
	form.style.display = "none"

	appendFields(form, {
		report_name: reportName,
		file_format_type: fileFormat,
		filters: JSON.stringify(filters || {}),
		applied_filters: JSON.stringify(appliedFilters || {}),
		// Empty means "every row" — the POS has no column/row hiding of its own
		visible_idx: JSON.stringify([]),
		custom_columns: JSON.stringify([]),
		// Empty rather than "0": the endpoint tests some of these flags for
		// truthiness before running them through cint, and "0" is a truthy string
		include_indentation: "",
		include_filters: "",
		include_hidden_columns: "",
		export_in_background: "",
		csv_delimiter: ",",
		csrf_token: window.csrf_token || "",
	})

	document.body.appendChild(form)

	return new Promise((resolve, reject) => {
		let settled = false

		const finish = (error) => {
			if (settled) return
			settled = true
			iframe.removeEventListener("load", onLoad)
			form.remove()
			error ? reject(error) : resolve()
		}

		function onLoad() {
			const message = readFrameError(iframe)
			finish(message ? new Error(message) : null)
		}

		iframe.addEventListener("load", onLoad)
		setTimeout(() => finish(null), EXPORT_SETTLE_MS)

		form.submit()
	})
}

/** The server's complaint, when the iframe holds a page instead of a download. */
function readFrameError(iframe) {
	try {
		const body = iframe.contentDocument?.body
		const text = (body?.innerText || "").trim()
		if (!text) return null

		// Frappe answers a failed whitelisted call with JSON in a <pre>, and a
		// raised exception with an error page — either way the text is the message
		try {
			const parsed = JSON.parse(text)
			const messages = parsed?._server_messages
				? JSON.parse(parsed._server_messages).map((m) => JSON.parse(m).message)
				: null
			return (messages?.join(" ") || parsed?.exception || parsed?.message || text).toString()
		} catch {
			return text.split("\n").slice(0, 3).join(" ")
		}
	} catch (error) {
		// Cross-origin or a real download — nothing readable, so nothing failed
		log.debug("Export frame not readable:", error?.message)
		return null
	}
}

function appendFields(form, values) {
	for (const [name, value] of Object.entries(values)) {
		const field = document.createElement("textarea")
		field.name = name
		field.value = value ?? ""
		form.appendChild(field)
	}
}

function getFrame(name) {
	let iframe = document.querySelector(`iframe[name="${name}"]`)
	if (!iframe) {
		iframe = document.createElement("iframe")
		iframe.name = name
		iframe.setAttribute("aria-hidden", "true")
		iframe.style.position = "fixed"
		iframe.style.width = "0"
		iframe.style.height = "0"
		iframe.style.border = "0"
		iframe.style.visibility = "hidden"
		document.body.appendChild(iframe)
	}
	return iframe
}

// ---------------------------------------------------------------------------
// Print
// ---------------------------------------------------------------------------

/**
 * Print the rows currently on screen.
 *
 * Built from the loaded result rather than re-run on the server so what prints
 * is exactly what the cashier is looking at.
 */
export function printReport({ title, subtitle, columns, rows, appliedFilters = {}, totalRowIndex = -1, orientation = "Portrait" }) {
	const iframe = getFrame(PRINT_FRAME_NAME)
	const html = buildPrintHTML({ title, subtitle, columns, rows, appliedFilters, totalRowIndex, orientation })

	const doc = iframe.contentDocument || iframe.contentWindow?.document
	if (!doc) {
		log.error("Print frame unavailable")
		return
	}

	doc.open()
	doc.write(html)
	doc.close()

	// Let the document lay out before the print dialog measures it
	const trigger = () => {
		try {
			iframe.contentWindow.focus()
			iframe.contentWindow.print()
		} catch (error) {
			log.error("Print failed:", error)
		}
	}
	if (doc.readyState === "complete") setTimeout(trigger, 50)
	else iframe.contentWindow.addEventListener("load", () => setTimeout(trigger, 50), { once: true })
}

/**
 * Print a pre-built HTML string (e.g. server-rendered print format) in the hidden iframe.
 */
export function printHtmlString(html) {
	const iframe = getFrame(PRINT_FRAME_NAME)
	const doc = iframe.contentDocument || iframe.contentWindow?.document
	if (!doc) {
		log.error("Print frame unavailable")
		return
	}
	doc.open()
	doc.write(html)
	doc.close()
	const trigger = () => {
		try {
			iframe.contentWindow.focus()
			iframe.contentWindow.print()
		} catch (error) {
			log.error("Print failed:", error)
		}
	}
	if (doc.readyState === "complete") setTimeout(trigger, 50)
	else iframe.contentWindow.addEventListener("load", () => setTimeout(trigger, 50), { once: true })
}

function buildPrintHTML({ title, subtitle, columns, rows, appliedFilters, totalRowIndex, orientation = "Portrait" }) {
	const cols = visibleColumns(columns)
	const dir = document.documentElement.dir === "rtl" ? "rtl" : "ltr"
	const lang = document.documentElement.lang || "en"

	const head = cols
		.map((column) => `<th${isNumericColumn(column) ? ' class="num"' : ""}>${escapeHTML(column.label || column.fieldname)}</th>`)
		.join("")

	const body = (rows || [])
		.map((row, rowIndex) => {
			const cells = cols
				.map((column, columnIndex) => {
					const value = formatReportValue(getCellValue(row, column, columnIndex), column)
					return `<td${isNumericColumn(column) ? ' class="num"' : ""}>${escapeHTML(value)}</td>`
				})
				.join("")
			return `<tr${rowIndex === totalRowIndex ? ' class="total"' : ""}>${cells}</tr>`
		})
		.join("")

	const filterRows = Object.entries(appliedFilters)
		.filter(([, value]) => value !== "" && value !== null && value !== undefined)
		.map(
			([label, value]) =>
				`<span class="chip"><b>${escapeHTML(label)}:</b> ${escapeHTML(
					Array.isArray(value) ? value.join(", ") : String(value),
				)}</span>`,
		)
		.join("")

	const pageSize = orientation.toLowerCase() === "portrait" ? "portrait" : "landscape"
	return `<!doctype html>
<html dir="${dir}" lang="${escapeHTML(lang)}">
<head>
<meta charset="utf-8" />
<title>${escapeHTML(title || "Report")}</title>
<style>
	@page { size: A4 ${pageSize}; margin: 10mm; }
	* { box-sizing: border-box; }
	body { font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; color: #111827; margin: 0; padding: 0; }
	h1 { font-size: 16px; margin: 0 0 2px; }
	.sub { font-size: 11px; color: #6b7280; margin-bottom: 8px; }
	.filters { margin-bottom: 8px; }
	.chip { display: inline-block; font-size: 10px; color: #374151; background: #f3f4f6; border-radius: 4px; padding: 2px 6px; margin: 0 4px 4px 0; }
	table { width: 100%; border-collapse: collapse; font-size: 10px; }
	th, td { border: 1px solid #d1d5db; padding: 3px 5px; text-align: start; vertical-align: top; }
	th { background: #f3f4f6; font-weight: 600; }
	td.num, th.num { text-align: end; white-space: nowrap; }
	tr.total td { font-weight: 700; background: #f9fafb; }
	thead { display: table-header-group; }
	tr { page-break-inside: avoid; }
	.empty { font-size: 11px; color: #6b7280; padding: 12px 0; }
</style>
</head>
<body>
	<h1>${escapeHTML(title || "Report")}</h1>
	${subtitle ? `<div class="sub">${escapeHTML(subtitle)}</div>` : ""}
	${filterRows ? `<div class="filters">${filterRows}</div>` : ""}
	${
		body
			? `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`
			: `<div class="empty">No data</div>`
	}
</body>
</html>`
}

function escapeHTML(value) {
	return String(value ?? "")
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#39;")
}
