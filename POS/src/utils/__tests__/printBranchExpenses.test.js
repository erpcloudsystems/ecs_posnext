import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/utils/apiWrapper", () => ({ call: vi.fn() }))
// Partial: `reportPrintFormat` reads its column/value helpers out of this same
// module, so replacing it wholesale takes the renderer down with it.
vi.mock("@/utils/reportOutput", async (importOriginal) => ({
	...(await importOriginal()),
	openPrintWindow: vi.fn(() => true),
	printHtmlString: vi.fn(),
}))

import { call } from "@/utils/apiWrapper"
import { printBranchExpenses } from "@/utils/printBranchExpenses"
import { openPrintWindow, printHtmlString } from "@/utils/reportOutput"

// Stands in for the report's own `<report>.html`: enough of it to prove the
// rows, the pinned branch and the shift day reach the page.
const TEMPLATE = `<div class="exp">
	<div class="branch">{%= filters.branch %} - {%= filters.shift_date %}</div>
	{% for (var i = 0; i < data.length; i++) { %}
	<div class="row">{%= data[i].description %} = {%= format_number(flt(data[i].amount), null, 2) %}</div>
	{% } %}
</div>`

const ROWS = [{ description: "سلفة شهرية", amount: 500 }]

/** The two calls the printer makes, in whichever order it makes them. */
function respondWith({ rows = ROWS, template = TEMPLATE } = {}) {
	call.mockImplementation(async (method) => {
		if (method === "ecs_posnext.api.reports.run_pos_report") {
			return {
				// what the server ran with - the branch it pinned, not what we sent
				filters: {
					view_by: "شيفت",
					shift_date: "2026-09-20",
					branch: "الحجاز",
				},
				columns: [{ fieldname: "amount", label: "المبلغ", fieldtype: "Float" }],
				result: rows,
			}
		}
		if (method === "ecs_posnext.api.reports.get_print_template") {
			return { template, template_type: "JS", letterhead: "" }
		}
		throw new Error(`unexpected call: ${method}`)
	})
}

function argsFor(method) {
	return call.mock.calls.find(([name]) => name === method)?.[1]
}

beforeEach(() => {
	vi.clearAllMocks()
	openPrintWindow.mockReturnValue(true)
})

describe("printBranchExpenses", () => {
	it("runs the report for the shift day the closing belongs to", async () => {
		respondWith()

		const result = await printBranchExpenses({
			posProfile: "الحجاز",
			periodStartDate: "2026-09-21 02:30:00",
		})

		expect(result).toEqual({ ok: true })

		const run = argsFor("ecs_posnext.api.reports.run_pos_report")
		expect(run.report_name).toBe("مصاريف الفروع")
		expect(run.pos_profile).toBe("الحجاز")
		// opened at 02:30, so it is still the previous trading day
		expect(JSON.parse(run.filters)).toEqual({
			view_by: "شيفت",
			shift_date: "2026-09-20",
		})
	})

	it("leaves the branch to the server rather than naming one", async () => {
		respondWith()

		await printBranchExpenses({
			posProfile: "الحجاز",
			periodStartDate: "2026-09-20 17:00:00",
		})

		expect(
			JSON.parse(argsFor("ecs_posnext.api.reports.run_pos_report").filters),
		).not.toHaveProperty("branch")
	})

	it("prints with the report's own HTML layout", async () => {
		respondWith()

		await printBranchExpenses({
			posProfile: "الحجاز",
			periodStartDate: "2026-09-20 17:00:00",
		})

		expect(
			argsFor("ecs_posnext.api.reports.get_print_template").print_layout,
		).toBe("__report_html__")

		const [html] = openPrintWindow.mock.calls[0]
		// the branch the server pinned, not the filters the caller built
		expect(html).toContain("الحجاز - 2026-09-20")
		expect(html).toContain("سلفة شهرية = 500.00")
		// an 80mm roll, not an A4 sheet the printer then shrinks
		expect(html).toContain("@page { size: 80mm auto; margin: 0; }")
	})

	it("still prints when the shift had no expenses", async () => {
		respondWith({ rows: [] })

		const result = await printBranchExpenses({
			posProfile: "الحجاز",
			periodStartDate: "2026-09-20 17:00:00",
		})

		expect(result).toEqual({ ok: true })
		expect(openPrintWindow).toHaveBeenCalledOnce()
	})

	it("falls back to the hidden frame when the pop-up is blocked, and says so", async () => {
		respondWith()
		openPrintWindow.mockReturnValue(false)

		const result = await printBranchExpenses({
			posProfile: "الحجاز",
			periodStartDate: "2026-09-20 17:00:00",
		})

		expect(result).toEqual({ ok: true, popupBlocked: true })
		expect(printHtmlString).toHaveBeenCalledOnce()
	})

	it("prints nothing when the shift start cannot be read", async () => {
		respondWith()

		const result = await printBranchExpenses({
			posProfile: "الحجاز",
			periodStartDate: null,
		})

		expect(result).toEqual({ ok: false, reason: "no-shift-day" })
		expect(call).not.toHaveBeenCalled()
		expect(openPrintWindow).not.toHaveBeenCalled()
	})

	it("reports an empty layout instead of printing a blank page", async () => {
		respondWith({ template: "" })

		const result = await printBranchExpenses({
			posProfile: "الحجاز",
			periodStartDate: "2026-09-20 17:00:00",
		})

		expect(result).toEqual({ ok: false, reason: "no-layout" })
		expect(openPrintWindow).not.toHaveBeenCalled()
	})

	it("swallows a failed run so the Z-report behind it still stands", async () => {
		call.mockRejectedValue(new Error("no permission"))

		const result = await printBranchExpenses({
			posProfile: "الحجاز",
			periodStartDate: "2026-09-20 17:00:00",
		})

		expect(result).toEqual({ ok: false, reason: "error" })
		expect(openPrintWindow).not.toHaveBeenCalled()
	})
})
