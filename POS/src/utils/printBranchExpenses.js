/**
 * Printing the shift day's branch expenses receipt (Report: مصاريف الفروع).
 *
 * It goes out with the Z-report when the last closing is reprinted: the cashier
 * reaching for that button has no shift open, so the POS Reports screen - the
 * only other way to this report - is out of reach, and the expenses belong to
 * the same handover the Z-report documents.
 *
 * Goes through the POS report endpoints so the branch scope and the permission
 * checks are the ones Reports already applies: `run_pos_report` pins the report's
 * `branch` filter to the Branch of the shift's POS Profile and discards whatever
 * the client asked for, so the branch is deliberately not sent from here.
 */

import { call } from "@/utils/apiWrapper"
import { logger } from "@/utils/logger"
import { openPrintWindow, printHtmlString } from "@/utils/reportOutput"
import {
	RECEIPT_PAGE,
	renderReportPrintFormat,
} from "@/utils/reportPrintFormat"
import { shiftDayOf } from "@/utils/shiftDay"

const log = logger.create("printBranchExpenses")

const BRANCH_EXPENSES_REPORT = "مصاريف الفروع"

// The report has no Print Format of its own - it prints with the `<report>.html`
// layout that ships beside its script, which the POS report API names with this
// constant (`ecs_posnext.api.reports.REPORT_LAYOUT`).
const REPORT_LAYOUT = "__report_html__"

// The report's `view_by` filter: "شيفت" reads `shift_date`, "مدة" reads the date
// range instead. It has to be sent even though the report defaults it, because a
// Query Report binds its filters straight into the SQL and nothing fills in a
// default for a value the caller left out - `%(view_by)s` would bind NULL, and
// `NULL = 'شيفت'` is NULL, so every expense falls out of the WHERE and the
// receipt prints empty.
const VIEW_BY_SHIFT = "شيفت"

/**
 * Print the branch expenses of the shift day `periodStartDate` falls in.
 *
 * A shift with no expenses still prints. The receipt saying zero is what shows
 * the till had none, and it is also the only answer the cashier gets from the
 * button: a print that silently does nothing reads as a button that did not work.
 *
 * Never throws - it is a second receipt printed behind a first one, so a failure
 * here must not read as the closing itself having failed.
 *
 * @returns {Promise<{ok: boolean, reason?: "no-shift-day"|"no-layout"|"error", popupBlocked?: boolean}>}
 */
export async function printBranchExpenses({
	posProfile = null,
	periodStartDate,
} = {}) {
	const shiftDate = shiftDayOf(periodStartDate)
	if (!shiftDate) {
		log.error(
			"Cannot print branch expenses: unreadable shift start",
			periodStartDate,
		)
		return { ok: false, reason: "no-shift-day" }
	}

	const filters = { view_by: VIEW_BY_SHIFT, shift_date: shiftDate }

	try {
		const [report, layout] = await Promise.all([
			call("ecs_posnext.api.reports.run_pos_report", {
				report_name: BRANCH_EXPENSES_REPORT,
				filters: JSON.stringify(filters),
				pos_profile: posProfile,
			}),
			call("ecs_posnext.api.reports.get_print_template", {
				report_name: BRANCH_EXPENSES_REPORT,
				print_layout: REPORT_LAYOUT,
				pos_profile: posProfile,
			}),
		])

		if (!layout?.template) {
			log.error("Branch expenses print layout is empty")
			return { ok: false, reason: "no-layout" }
		}

		const html = renderReportPrintFormat({
			...RECEIPT_PAGE,
			template: layout.template,
			letterhead: layout.letterhead,
			orientation: "Portrait",
			reportName: BRANCH_EXPENSES_REPORT,
			title: BRANCH_EXPENSES_REPORT,
			columns: report?.columns || [],
			rows: report?.result || [],
			// What the server ran with, which carries the branch it pinned - the
			// layout prints the branch and the shift day in the receipt header
			// from these.
			filters: report?.filters || filters,
		})

		// The Z-report window has already spent the one pop-up a browser allows
		// per click, so this is the one that gets refused. Print it from the
		// hidden frame rather than lose the receipt, and say so upwards, because
		// a window that never appears looks like nothing happened.
		if (!openPrintWindow(html)) {
			printHtmlString(html)
			return { ok: true, popupBlocked: true }
		}

		return { ok: true }
	} catch (error) {
		log.error("Error printing branch expenses:", error)
		return { ok: false, reason: "error" }
	}
}
