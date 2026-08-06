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

	// POS Coupon applied at "Review & Book" checkout: { code, amount, apply_on }.
	// amount is the pre-computed discount (see ReservationCheckoutDialog's
	// applyCoupon, mirrors the main POS cart's coupon handling in posCart.js).
	const appliedCoupon = ref(null)

	const items = ref([])

	const itemCount = computed(() => items.value.reduce((sum, i) => sum + i.qty, 0))
	const total = computed(() => items.value.reduce((sum, i) => sum + i.qty * i.rate, 0))

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
		addItem,
		removeItem,
		updateQty,
		clear,
	}
})
