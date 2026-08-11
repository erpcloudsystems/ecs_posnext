import { defineStore } from "pinia"
import { computed, ref } from "vue"

/**
 * Shared state for the POS 'Build' catalog booking flow: one reservation
 * (branch/room/visit date/customer) that can carry multiple items (the main
 * package plus any add-ons) before being submitted as a single Sales Order.
 */
export const useBuildReservationStore = defineStore("buildReservation", () => {
	const parentBranch = ref(null)
	const room = ref(null)
	const visitDate = ref(null)

	const phone = ref("")
	const customerName = ref("")
	const customerLookup = ref({ checked: false, found: false, customerName: "" })

	// POS Coupon applied at "Review & Book" checkout. Two shapes, set by
	// ReservationCheckoutDialog's applyCoupon:
	//   - { code, scope: "total", amount, apply_on } - whole-cart discount
	//     (mirrors the main POS cart's coupon handling in posCart.js). `amount`
	//     is the pre-computed discount, subtracted from `total` for display.
	//   - { code, scope: "items", itemCodes } - coupon linked to a POS Offer with
	//     "Apply Rule On Item Code"; the discount is already baked into the
	//     matching items' `rate` (see applyItemCodeDiscount), so `total` above is
	//     already post-discount.
	const appliedCoupon = ref(null)

	const items = ref([])

	const itemCount = computed(() => items.value.reduce((sum, i) => sum + i.qty, 0))
	// `rate` already reflects any active item-code-scoped coupon discount (see
	// applyItemCodeDiscount) - `total` is therefore the post-discount total.
	const total = computed(() => items.value.reduce((sum, i) => sum + i.qty * i.rate, 0))
	// Pre-discount total, for displaying "Subtotal" alongside an item-scoped coupon.
	const subtotalBeforeDiscount = computed(() =>
		items.value.reduce((sum, i) => sum + i.qty * (i.original_rate ?? i.rate), 0),
	)

	function addItem(item) {
		const existing = items.value.find(
			(i) => i.item_code === item.item_code && i.uom === item.uom && i.slot === item.slot,
		)
		if (existing) {
			existing.qty += item.qty
		} else {
			items.value.push(item)
		}
	}

	function removeItem(index) {
		items.value.splice(index, 1)
	}

	function updateQty(index, qty) {
		if (qty <= 0) {
			removeItem(index)
			return
		}
		items.value[index].qty = qty
	}

	// Applies a proportional rate cut (0-1) to the given item codes' rows, mirroring
	// posawesome's "Apply Rule On Item Code" Item Price offers - unlike the
	// Grand-Total coupon path, this bakes the discount directly into item.rate so
	// only matching items are discounted. `original_rate` is preserved so
	// clearItemCodeDiscount can undo it.
	function applyItemCodeDiscount(itemCodes, ratio) {
		items.value.forEach((item) => {
			if (!itemCodes.includes(item.item_code)) return
			if (item.original_rate === undefined) {
				item.original_rate = item.rate
			}
			item.rate = item.original_rate * (1 - ratio)
		})
	}

	// Restores original_rate on the given item codes (or all discounted items if
	// itemCodes is omitted), undoing applyItemCodeDiscount.
	function clearItemCodeDiscount(itemCodes = null) {
		items.value.forEach((item) => {
			if (item.original_rate === undefined) return
			if (itemCodes && !itemCodes.includes(item.item_code)) return
			item.rate = item.original_rate
			delete item.original_rate
		})
	}

	function clear() {
		items.value = []
		parentBranch.value = null
		room.value = null
		visitDate.value = null
		phone.value = ""
		customerName.value = ""
		customerLookup.value = { checked: false, found: false, customerName: "" }
		appliedCoupon.value = null
	}

	return {
		parentBranch,
		room,
		visitDate,
		phone,
		customerName,
		customerLookup,
		appliedCoupon,
		items,
		itemCount,
		total,
		subtotalBeforeDiscount,
		addItem,
		removeItem,
		updateQty,
		applyItemCodeDiscount,
		clearItemCodeDiscount,
		clear,
	}
})
