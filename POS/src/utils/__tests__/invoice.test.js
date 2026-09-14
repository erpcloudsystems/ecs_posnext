import { describe, expect, it } from "vitest"

import { canUpdatePaymentMode } from "@/utils/invoice"

describe("canUpdatePaymentMode", () => {
	const paidInvoice = {
		name: "ACC-SINV-2026-00385",
		docstatus: 1,
		is_return: 0,
		status: "Paid",
	}

	it("offers the correction on a submitted POS sale", () => {
		expect(canUpdatePaymentMode(paidInvoice)).toBe(true)
	})

	it("hides it on drafts and cancelled invoices", () => {
		expect(canUpdatePaymentMode({ ...paidInvoice, docstatus: 0 })).toBe(false)
		expect(canUpdatePaymentMode({ ...paidInvoice, docstatus: 2 })).toBe(false)
	})

	it("hides it on return invoices", () => {
		expect(
			canUpdatePaymentMode({ ...paidInvoice, is_return: 1, status: "Return" }),
		).toBe(false)
	})

	// Cancelling an invoice that a credit note points at would orphan the note,
	// so the server refuses it - do not offer the button either.
	it("hides it once a return has been issued against the invoice", () => {
		expect(
			canUpdatePaymentMode({ ...paidInvoice, status: "Credit Note Issued" }),
		).toBe(false)
	})

	it("handles a missing invoice", () => {
		expect(canUpdatePaymentMode(null)).toBe(false)
		expect(canUpdatePaymentMode({})).toBe(false)
	})
})
