import { describe, expect, it } from "vitest"

import {
	buildTemplateContext,
	renderReportPrintFormat,
} from "@/utils/reportPrintFormat"
import { renderTemplate } from "@/utils/microtemplate"

/**
 * A report Print Format is a Frappe JS template. This is a condensed version of
 * a real one: an inline `{% ... %}` code block that walks `data`, plus output
 * tags that call the number/date helpers Frappe exposes as globals. Rendering it
 * through Jinja is what raised "tag name expected"; it has to compile here.
 */
const TEMPLATE = `<style>.receipt { direction: rtl; }</style>
{%
	var fmt = function (v) {
		var n = flt(v);
		var dec = (Math.abs(n - Math.round(n)) > 0.005) ? 2 : 0;
		return format_number(n, null, dec);
	};
	var total = 0;
	var employees = [];
	for (var i = 0; i < data.length; i++) {
		var row = data[i];
		if (!row || !row.row_type) { continue; }
		if (row.row_type == "main") {
			employees.push({ name: row.employee_name, amount: flt(row.amount) });
			total += flt(row.amount);
		}
	}
%}
<div class="receipt">
	<div class="printed">{%= frappe.datetime.now_datetime() %}</div>
	{% if (filters.from_date) { %}
	<div class="from">{%= frappe.datetime.str_to_user(filters.from_date) %}</div>
	{% } %}
	{% for (var k = 0; k < employees.length; k++) { %}
	<div class="emp">{%= employees[k].name %} = {%= fmt(employees[k].amount) %}</div>
	{% } %}
	<div class="total">{%= fmt(total) %}</div>
</div>`

const DATA = [
	{
		row_type: "main",
		employee_name: "Mahmoud",
		amount: 1234.5,
		grand_total: 5000,
	},
	{ row_type: "item_header", sales_invoice: "Item Name" },
	{
		row_type: "item_row",
		sales_invoice: "Haircut",
		salary_component: 2,
		amount: 25,
		grand_total: 150,
	},
	{ amount: null, grand_total: null }, // the spacing row the report appends
	{ row_type: "main", employee_name: "Sara", amount: 300, grand_total: 900 },
]

function render(extra = {}) {
	return renderReportPrintFormat({
		template: TEMPLATE,
		reportName: "Extra Salary Report",
		title: "Extra Salary Report",
		columns: [{ fieldname: "amount", label: "Amount", fieldtype: "Currency" }],
		rows: DATA,
		filters: { from_date: "2026-08-01", branch: "Main" },
		orientation: "Portrait",
		...extra,
	})
}

describe("renderReportPrintFormat", () => {
	it("renders a JS print format into a complete page", () => {
		const html = render()

		expect(html).toContain("<!doctype html>")
		expect(html).toContain("@page { size: A4 portrait")
		expect(html).toContain("Mahmoud = 1,234.50")
		expect(html).toContain("Sara = 300")
		expect(html).toContain('<div class="total">1,534.50</div>')
	})

	it("leaves no template tags behind", () => {
		const html = render()

		expect(html).not.toContain("{%")
		expect(html).not.toContain("%}")
	})

	it("keeps the format's own stylesheet", () => {
		expect(render()).toContain(".receipt { direction: rtl; }")
	})

	it("includes the letterhead when one is passed", () => {
		expect(render({ letterhead: "<div id='lh'>Salon</div>" })).toContain(
			"<div id='lh'>Salon</div>",
		)
	})

	it("renders a conditional filter block only when the filter has a value", () => {
		expect(render()).toContain('<div class="from">')
		expect(render({ filters: {} })).not.toContain('<div class="from">')
	})

	it("throws on a broken template so the caller can fall back", () => {
		expect(() => render({ template: "{% for (var i = 0; %}" })).toThrow()
	})
})

describe("template context helpers", () => {
	const context = buildTemplateContext({
		reportName: "R",
		title: "R",
		rows: [],
		columns: [],
		filters: {},
	})

	it("exposes the data under every name the desk uses", () => {
		const filled = buildTemplateContext({
			reportName: "R",
			rows: DATA,
			columns: [],
			filters: {},
		})

		expect(filled.data).toBe(DATA)
		expect(filled.result).toBe(DATA)
		expect(filled.original_data).toBe(DATA)
	})

	it("parses grouped and empty values like flt", () => {
		expect(context.flt("1,234.50")).toBe(1234.5)
		expect(context.flt(null)).toBe(0)
		expect(context.flt("")).toBe(0)
		expect(context.flt("abc")).toBe(0)
		// Rounds with the system method (Banker's by default): .5 goes to even
		expect(context.flt(2.345, 2)).toBe(2.34)
		expect(context.flt(2.335, 2)).toBe(2.34)
	})

	it("groups thousands and honours an explicit precision", () => {
		expect(context.format_number(1234567.891, null, 2)).toBe("1,234,567.89")
		expect(context.format_number(1234, null, 0)).toBe("1,234")
		expect(context.format_number(-1234.5, null, 2)).toBe("-1,234.50")
		expect(context.format_number(0, null, 0)).toBe("0")
	})

	it("formats dates in the system date format without shifting the day", () => {
		expect(context.frappe.datetime.str_to_user("2026-08-05")).toBe("05-08-2026")
		expect(context.frappe.datetime.str_to_user("2026-08-05 13:45:00")).toBe(
			"05-08-2026 13:45",
		)
		expect(context.frappe.datetime.str_to_user("")).toBe("")
		expect(context.frappe.datetime.user_to_str("05-08-2026")).toBe("2026-08-05")
	})

	it("stamps a now_datetime the server would accept", () => {
		expect(context.frappe.datetime.now_datetime()).toMatch(
			/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/,
		)
	})
})

describe("microtemplate", () => {
	it("supports the jinja-ish sugar the desk accepts", () => {
		const html = renderTemplate("{% if name %}{{ name }}{% endif %}", {
			name: "Sara",
		})

		expect(html).toBe("Sara")
	})
})
