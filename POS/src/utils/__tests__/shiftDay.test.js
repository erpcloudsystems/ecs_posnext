import { describe, expect, it } from "vitest"

import { shiftDayOf } from "@/utils/shiftDay"

describe("shiftDayOf", () => {
	it("keeps a shift opened at or after 09:00 on its own date", () => {
		expect(shiftDayOf("2026-09-20 09:00:00")).toBe("2026-09-20")
		expect(shiftDayOf("2026-09-20 17:15:15.317939")).toBe("2026-09-20")
		expect(shiftDayOf("2026-09-20 23:59:59")).toBe("2026-09-20")
	})

	it("puts a shift opened before 09:00 on the day before", () => {
		expect(shiftDayOf("2026-09-21 02:30:00")).toBe("2026-09-20")
		expect(shiftDayOf("2026-09-21 08:59:59")).toBe("2026-09-20")
	})

	it("steps back across a month and a year boundary", () => {
		expect(shiftDayOf("2026-09-01 03:00:00")).toBe("2026-08-31")
		expect(shiftDayOf("2026-01-01 03:00:00")).toBe("2025-12-31")
		// a leap day, which naive month arithmetic gets wrong
		expect(shiftDayOf("2024-03-01 03:00:00")).toBe("2024-02-29")
	})

	it("reads an ISO datetime the same way", () => {
		expect(shiftDayOf("2026-09-21T02:30:00")).toBe("2026-09-20")
	})

	it("returns null rather than a guess when the start is unreadable", () => {
		expect(shiftDayOf("")).toBeNull()
		expect(shiftDayOf(null)).toBeNull()
		expect(shiftDayOf(undefined)).toBeNull()
		expect(shiftDayOf("20-09-2026 17:00")).toBeNull()
	})
})
