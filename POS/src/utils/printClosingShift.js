/**
 * Printing the Z-report of a POS Closing Shift.
 *
 * Shared by the closing dialog, which prints the report the moment a shift is
 * closed, and by the no-shift screen's reprint button, which prints the last
 * closing again when that first window was blocked, the roll jammed, or the
 * receipt was thrown away.
 */

import { call } from "@/utils/apiWrapper"
import { logger } from "@/utils/logger"
import { printBranchExpenses } from "@/utils/printBranchExpenses"

const log = logger.create("printClosingShift")

const CLOSING_SHIFT_DOCTYPE = "POS Closing Shift"
const CLOSING_SHIFT_FORMAT = "POS Closing Shift"

/**
 * Open /printview for a closing shift in its own window, set to print itself.
 *
 * @returns false when the browser refused the window, so the caller can tell
 *          the cashier to allow pop-ups rather than silently print nothing.
 */
export function openClosingShiftPrintView(name) {
	const params = new URLSearchParams({
		doctype: CLOSING_SHIFT_DOCTYPE,
		name,
		format: CLOSING_SHIFT_FORMAT,
		no_letterhead: 1,
		_lang: "en",
		trigger_print: 1,
		_t: Date.now(),
	})

	const win = window.open(
		`/printview?${params.toString()}`,
		"_blank",
		"width=800,height=600",
	)
	if (!win) {
		log.error("Closing shift print window was blocked by the browser")
		return false
	}
	return true
}

/**
 * Reprint the cashier's most recent closing shift.
 *
 * Which closing that is, is decided on the server from the POS Profiles the
 * user is assigned to — the till has no shift open at this point, so the
 * client has no profile left to go on.
 *
 * The shift day's branch expenses print behind it, off the same click: the
 * cashier has no shift open here, so the POS Reports screen - the only other way
 * to that report - is out of reach, and the expenses belong to the handover the
 * Z-report documents. Its outcome is reported separately in `expenses` rather
 * than folded into `ok`, because the Z-report is out either way and a second
 * receipt that failed is not a reprint that failed.
 *
 * @param {string|null} posProfile narrows the lookup to one till; ignored by
 *        the server when the user is not assigned to it.
 * @returns {Promise<{ok: boolean, reason?: "none"|"blocked"|"error", closing?: object, expenses?: object}>}
 */
export async function printLastClosingShift(posProfile = null) {
	try {
		const closing = await call(
			"ecs_posnext.api.shifts.get_last_closing_shift",
			{ pos_profile: posProfile || null },
		)

		if (!closing?.name) return { ok: false, reason: "none" }

		if (!openClosingShiftPrintView(closing.name)) {
			return { ok: false, reason: "blocked", closing }
		}

		const expenses = await printBranchExpenses({
			posProfile: closing.pos_profile,
			periodStartDate: closing.period_start_date,
		})

		return { ok: true, closing, expenses }
	} catch (error) {
		log.error("Error reprinting last closing shift:", error)
		return { ok: false, reason: "error" }
	}
}
