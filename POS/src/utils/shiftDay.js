/**
 * Which day a POS shift's figures belong to.
 *
 * Shift-scoped reports group by a day that runs 09:00 -> 09:00, so a shift
 * opened after midnight still belongs to the calendar date before it. The rule
 * lives here rather than in one caller because the closing dialog and the
 * reprint of a closing both have to land on the same day for the same shift:
 * two answers would print two different receipts for one closing.
 *
 * Kept in step with the CASE that buckets the day in the report queries
 * (Reports: POS Item Sales Summary, مصاريف الفروع).
 */
export const SHIFT_DAY_START_HOUR = 9

/**
 * The shift day `periodStartDate` falls in, as YYYY-MM-DD.
 *
 * Read off the string rather than a Date so the day is the one the server
 * stamped, whatever timezone the browser is in. Returns null if unparseable.
 */
export function shiftDayOf(periodStartDate) {
	const parts = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2})/.exec(
		String(periodStartDate || ""),
	)
	if (!parts) return null

	const [year, month, day, hour] = parts.slice(1).map(Number)
	if (hour >= SHIFT_DAY_START_HOUR) return parts[0].slice(0, 10)

	// UTC arithmetic so subtracting the day cannot land on a DST boundary
	return new Date(Date.UTC(year, month - 1, day - 1)).toISOString().slice(0, 10)
}
