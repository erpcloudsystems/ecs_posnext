// POS Offer engine (ported from posawesome's custom POS Offer doctype).
//
// Serves the richer posawesome promotions that the ERPNext Pricing-Rule based
// `posOffers` store does NOT cover: day-of-week + time scheduling, customer-group
// targeting, item-code lists, Give Product / replace-cheapest, coupon-based.
//
// Runs ALONGSIDE the existing pricing-rule offers (additive — does not replace them).
//
// Flow:
//   1. loadPosOffers(posProfile)  -> fetch candidate POS Offers (api.offers.get_pos_offers)
//   2. updateSnapshot({...})      -> feed current cart state for eligibility
//   3. eligibleOffers / autoOffers (computed)
//   4. applyPosOffer / removePosOffer -> mutate the cart (discount / free product)

import { defineStore } from "pinia"
import { computed, ref } from "vue"
import { call } from "@/utils/apiWrapper"
import { usePOSCartStore } from "@/stores/posCart"

function num(v) {
	const n = Number.parseFloat(v)
	return Number.isFinite(n) ? n : 0
}

// Hardcoded special offer (ported from posawesome Invoice.vue): this offer only
// applies when the customer counts as an "employee".
const EMPLOYEE_OFFER_NAME = "30% discount for employees"

export const usePOSOfferEngineStore = defineStore("posOfferEngine", () => {
	const posOffers = ref([])
	const appliedPosOffers = ref([]) // names of currently-applied POS Offers
	const snapshot = ref({
		items: [],
		total: 0,
		subtotal: 0,
		customerGroup: null,
		// "employee" gate (posawesome: truthy when the selected customer has a mobile).
		employee: false,
	})
	const hasFetched = ref(false)

	function updateSnapshot(snap = {}) {
		snapshot.value = {
			items: snap.items || [],
			total: num(snap.total),
			subtotal: num(snap.subtotal),
			customerGroup: snap.customerGroup || null,
			employee: Boolean(snap.employee),
		}
	}

	// ---- eligibility helpers ----

	function isScheduleOk(offer) {
		const now = new Date()
		// Day-of-week (empty `days` = every day). posawesome maps Sun=0..Sat=6.
		if (
			Array.isArray(offer.days) &&
			offer.days.length &&
			!offer.days.includes(now.getDay())
		) {
			return false
		}
		// Time window (HH:MM:SS strings)
		if (offer.from_time || offer.to_time) {
			const cur = now.toTimeString().slice(0, 8)
			if (offer.from_time && cur < String(offer.from_time).slice(0, 8))
				return false
			if (offer.to_time && cur > String(offer.to_time).slice(0, 8)) return false
		}
		return true
	}

	function matchingItems(offer) {
		const items = snapshot.value.items || []
		switch (offer.apply_on) {
			case "Transaction":
				return items
			case "Item Code": {
				const codes = new Set()
				if (offer.item) codes.add(offer.item)
				;(offer.applied_items || []).forEach(
					(r) => r.item_code && codes.add(r.item_code),
				)
				return items.filter((i) => codes.has(i.item_code))
			}
			case "Item Group":
				return items.filter((i) => i.item_group === offer.item_group)
			case "Brand":
				return items.filter((i) => i.brand === offer.brand)
			default:
				return []
		}
	}

	function qtyOf(items) {
		return items.reduce((s, i) => s + num(i.quantity ?? i.qty), 0)
	}
	function amtOf(items) {
		return items.reduce(
			(s, i) => s + num(i.amount ?? num(i.quantity ?? i.qty) * num(i.rate)),
			0,
		)
	}

	/**
	 * Returns { eligible, reason }. Mirrors posawesome's condition checks.
	 */
	// Is this the hardcoded employee offer? (match by docname or title)
	function isEmployeeOffer(offer) {
		return (
			offer.name === EMPLOYEE_OFFER_NAME || offer.title === EMPLOYEE_OFFER_NAME
		)
	}

	function checkEligibility(offer) {
		if (offer.disable) return { eligible: false, reason: "Disabled" }
		if (!isScheduleOk(offer))
			return { eligible: false, reason: "Not in schedule" }

		if (offer.apply_on === "Transaction") {
			const total = snapshot.value.total
			if (offer.min_amt && total < num(offer.min_amt)) {
				return { eligible: false, reason: `Min amount ${offer.min_amt}` }
			}
			if (num(offer.max_amt) > 0 && total > num(offer.max_amt)) {
				return { eligible: false, reason: `Max amount ${offer.max_amt}` }
			}
			return { eligible: true, reason: null }
		}

		const matched = matchingItems(offer)
		if (!matched.length) return { eligible: false, reason: "No matching items" }

		const q = qtyOf(matched)
		const a = amtOf(matched)
		if (offer.min_qty && q < num(offer.min_qty)) {
			return { eligible: false, reason: `Min qty ${offer.min_qty}` }
		}
		if (num(offer.max_qty) > 0 && q > num(offer.max_qty)) {
			return { eligible: false, reason: `Max qty ${offer.max_qty}` }
		}
		if (offer.min_amt && a < num(offer.min_amt)) {
			return { eligible: false, reason: `Min amount ${offer.min_amt}` }
		}
		if (num(offer.max_amt) > 0 && a > num(offer.max_amt)) {
			return { eligible: false, reason: `Max amount ${offer.max_amt}` }
		}

		// Hardcoded gating for Item Code offers (ported from posawesome Invoice.vue):
		//   - the employee offer applies only when the customer is an employee
		//   - a customer_group offer applies only when the group matches
		//   - otherwise normal offers apply
		if (offer.apply_on === "Item Code") {
			if (isEmployeeOffer(offer)) {
				if (!snapshot.value.employee) {
					return { eligible: false, reason: "Employees only" }
				}
			} else if (offer.customer_group) {
				if (offer.customer_group !== snapshot.value.customerGroup) {
					return { eligible: false, reason: "Customer group mismatch" }
				}
			}
		} else if (
			offer.customer_group &&
			snapshot.value.customerGroup &&
			offer.customer_group !== snapshot.value.customerGroup
		) {
			// Group/Brand: keep a light customer-group guard (only on explicit mismatch).
			return { eligible: false, reason: "Customer group mismatch" }
		}

		return { eligible: true, reason: null }
	}

	// Eligible, non-coupon offers (coupon_based offers require a coupon flow that is
	// not wired yet, so they are excluded to avoid applying them without a coupon).
	const eligibleOffers = computed(() =>
		posOffers.value.filter(
			(o) => !o.coupon_based && checkEligibility(o).eligible,
		),
	)

	// Eligible coupon-gated offers (exposed for a future coupon flow).
	const couponOffers = computed(() =>
		posOffers.value.filter(
			(o) => o.coupon_based && checkEligibility(o).eligible,
		),
	)

	// Auto offers that are eligible and not coupon-gated -> applied automatically.
	const autoOffers = computed(() => eligibleOffers.value.filter((o) => o.auto))

	const appliedCount = computed(() => appliedPosOffers.value.length)

	// ---- application ----

	function applyPosOffer(offer) {
		const cart = usePOSCartStore()
		if (offer.offer === "Grand Total") {
			cart.applyDiscountToCart({
				name: offer.name,
				code: offer.name,
				percentage: num(offer.discount_percentage),
				amount: num(offer.discount_amount),
				apply_on: "Grand Total",
			})
		} else if (offer.offer === "Give Product") {
			const giveCode = offer.give_item || offer.apply_item_code
			if (giveCode) {
				cart.addItem(
					{
						item_code: giveCode,
						item_name: giveCode,
						rate: num(offer.rate_give_item),
						price_list_rate: num(offer.rate_give_item),
						uom: offer.uom,
						is_free_item: !num(offer.rate_give_item),
					},
					num(offer.given_qty) || 1,
					true,
				)
			}
		} else if (offer.offer === "Item Price") {
			// Item-level discount on matching items.
			const pct = num(offer.discount_percentage)
			if (pct > 0) {
				matchingItems(offer).forEach((it) => {
					it.discount_percentage = pct
					cart.recalculateItem?.(it)
				})
			}
		}
		// "Loyalty Point" offers are handled by loyalty_engine on submit.

		if (!appliedPosOffers.value.includes(offer.name)) {
			appliedPosOffers.value.push(offer.name)
		}
	}

	function removePosOffer(offer) {
		const cart = usePOSCartStore()
		if (offer.offer === "Grand Total") {
			cart.removeDiscountFromCart?.()
		}
		appliedPosOffers.value = appliedPosOffers.value.filter(
			(n) => n !== offer.name,
		)
	}

	function isApplied(offer) {
		return appliedPosOffers.value.includes(offer.name)
	}

	// Auto-apply eligible auto offers that aren't applied yet.
	// SAFETY: "Give Product" offers are NOT auto-applied — adding free items to the
	// cart automatically (financial impact) requires an explicit cashier action via
	// the offers dialog. Only discount-type offers auto-apply.
	function applyAutoOffers() {
		autoOffers.value.forEach((o) => {
			if (o.offer === "Give Product") return
			if (!isApplied(o)) applyPosOffer(o)
		})
	}

	async function loadPosOffers(posProfile) {
		if (!posProfile) return
		try {
			const res = await call("ecs_posnext.api.offers.get_pos_offers", {
				pos_profile: posProfile,
			})
			posOffers.value = (res?.message || res || []).map((o) => ({ ...o }))
			hasFetched.value = true
		} catch (e) {
			console.error("Failed to load POS Offers", e)
			posOffers.value = []
		}
	}

	function clear() {
		posOffers.value = []
		appliedPosOffers.value = []
		hasFetched.value = false
	}

	return {
		posOffers,
		appliedPosOffers,
		hasFetched,
		eligibleOffers,
		couponOffers,
		autoOffers,
		appliedCount,
		updateSnapshot,
		checkEligibility,
		matchingItems,
		applyPosOffer,
		removePosOffer,
		isApplied,
		applyAutoOffers,
		loadPosOffers,
		clear,
	}
})
