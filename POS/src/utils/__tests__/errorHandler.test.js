import { beforeAll, describe, expect, it } from "vitest"

beforeAll(() => {
	globalThis.__ = (text, args) =>
		args ? text.replace(/\{(\d+)\}/g, (_, i) => args[i]) : text
})

const ALERT = "Payment methods refreshed. Please review before proceeding."
const REAL = "User don't have permissions to select/read this account."

describe("parseError", () => {
	it("shows the raised error, not a leading alert (frappe-ui messages)", async () => {
		const { parseError } = await import("@/utils/errorHandler")
		const ctx = parseError({ exc_type: "PermissionError", messages: [ALERT, REAL] })
		expect(ctx.message).toBe(REAL)
	})

	it("prefers the raise_exception message from _server_messages", async () => {
		const { parseError } = await import("@/utils/errorHandler")
		const ctx = parseError({
			exc_type: "PermissionError",
			_server_messages: JSON.stringify([
				JSON.stringify({ message: ALERT, alert: 1, indicator: "orange" }),
				JSON.stringify({ message: REAL, title: "Not permitted", raise_exception: 1 }),
			]),
		})
		expect(ctx.message).toBe(REAL)
	})

	it("still handles a single message", async () => {
		const { parseError } = await import("@/utils/errorHandler")
		expect(parseError({ messages: [REAL] }).message).toBe(REAL)
	})
})
