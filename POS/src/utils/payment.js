/**
 * Payment utility functions
 */

import { roundCurrency } from "@/utils/currency"

/**
 * Get emoji icon for payment method type
 * @param {string} type - Payment method type
 * @returns {string} Emoji icon
 */
export function getPaymentIcon(type) {
	const iconMap = {
		Cash: "💵",
		Card: "💳",
		Bank: "🏦",
		Phone: "📱",
		Wallet: "👛",
		Credit: "💚",
		"Credit Card": "💳",
		"Debit Card": "💳",
		"Mobile Money": "📱",
		Check: "🧾",
		"Gift Card": "🎁",
	}
	return iconMap[type] || "💰"
}

/**
 * Add an invoice-total increase (e.g. an item added after payments were
 * entered) onto the last regular payment entry so the invoice stays fully
 * paid. Wallet (points) and Customer Credit entries are never increased -
 * they are capped by balance/available credit - so if only those exist the
 * entries are returned unchanged and the difference stays as Remaining.
 *
 * Mutates and returns the given entries array. No-op unless delta > 0.
 * @param {Array} entries - Payment entries ({mode_of_payment, amount, ...})
 * @param {number} delta - Amount the grand total grew by
 * @returns {Array} The updated entries array
 */
export function applyPaymentTopUp(entries, delta) {
	const amount = roundCurrency(delta)
	if (!entries?.length || amount <= 0) return entries

	for (let i = entries.length - 1; i >= 0; i--) {
		const entry = entries[i]
		if (!entry.is_customer_credit && !entry.is_wallet_payment) {
			entry.amount = roundCurrency((entry.amount || 0) + amount)
			break
		}
	}
	return entries
}
