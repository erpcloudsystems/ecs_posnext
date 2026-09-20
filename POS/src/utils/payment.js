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

/**
 * Pull an invoice-total decrease (e.g. an additional discount applied after
 * the payment method was already tapped) back off the payment entries, so the
 * cashier is not left tendering the pre-discount amount.
 *
 * `isReducible` decides which entries may be pulled down. Anything filled in
 * from the total - a tapped method, a Pay button, applied credit - was never a
 * tender and should follow the total; a cash amount the cashier typed in is
 * money physically handed over and stays put, visible as Change. Whatever
 * excess is left once every reducible entry sits at zero stays where it is.
 *
 * Mutates and returns the given entries array. No-op unless delta > 0.
 * @param {Array} entries - Payment entries ({mode_of_payment, amount, ...})
 * @param {number} delta - Amount to pull off the entries
 * @param {Function} isReducible - Predicate: entry => true when it may be cut
 * @returns {Array} The updated entries array
 */
export function applyPaymentReduction(entries, delta, isReducible) {
	let remaining = roundCurrency(delta)
	if (!entries?.length || remaining <= 0) return entries

	for (let i = entries.length - 1; i >= 0 && remaining > 0; i--) {
		const entry = entries[i]
		if (!isReducible(entry)) continue

		const amount = roundCurrency(entry.amount || 0)
		if (amount <= 0) continue

		const cut = Math.min(amount, remaining)
		entry.amount = roundCurrency(amount - cut)
		remaining = roundCurrency(remaining - cut)
	}
	return entries
}
