import { describe, expect, it } from "vitest"

import { applyPaymentTopUp } from "@/utils/payment"

describe("applyPaymentTopUp", () => {
	const entry = (mode, amount, extra = {}) => ({
		mode_of_payment: mode,
		amount,
		type: "Cash",
		...extra,
	})

	it("adds the delta to the last regular payment entry", () => {
		const entries = [entry("CIB بنك فيزا", 750, { type: "Card" })]

		applyPaymentTopUp(entries, 800)

		expect(entries[0].amount).toBe(1550)
	})

	it("tops up the most recent entry when several methods were used", () => {
		const entries = [entry("Cash", 100), entry("Card", 400, { type: "Card" })]

		applyPaymentTopUp(entries, 50)

		expect(entries[0].amount).toBe(100)
		expect(entries[1].amount).toBe(450)
	})

	it("skips wallet and customer credit entries", () => {
		const entries = [
			entry("Loyalty Points", 200, { is_wallet_payment: true }),
			entry("Customer Credit", 100, { is_customer_credit: true }),
			entry("Cash", 450),
		]

		applyPaymentTopUp(entries, 100)

		expect(entries[0].amount).toBe(200)
		expect(entries[1].amount).toBe(100)
		expect(entries[2].amount).toBe(550)
	})

	it("leaves entries untouched when only wallet/credit payments exist", () => {
		const entries = [
			entry("Loyalty Points", 200, { is_wallet_payment: true }),
			entry("Customer Credit", 100, { is_customer_credit: true }),
		]

		applyPaymentTopUp(entries, 100)

		expect(entries[0].amount).toBe(200)
		expect(entries[1].amount).toBe(100)
	})

	it("is a no-op for zero/negative deltas or empty entries", () => {
		const entries = [entry("Cash", 750)]
		applyPaymentTopUp(entries, 0)
		applyPaymentTopUp(entries, -25)
		expect(entries[0].amount).toBe(750)

		expect(applyPaymentTopUp([], 100)).toEqual([])
		expect(applyPaymentTopUp(null, 100)).toBe(null)
	})

	it("rounds to currency precision", () => {
		const entries = [entry("Cash", 750.1)]

		applyPaymentTopUp(entries, 800.04)

		expect(entries[0].amount).toBe(1550.14)
	})
})
