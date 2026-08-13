import { defineStore } from "pinia"
import { computed, ref } from "vue"
import { call } from "@/utils/apiWrapper"

/**
 * Active membership (Subscription-ticket) badge bridge.
 * Loads whether the selected customer holds a still-valid, still-usable
 * Subscription ticket, for the small badge on the POS customer card.
 */
export const useMembershipStore = defineStore("membership", () => {
	const info = ref(null)
	const loading = ref(false)

	const count = computed(() => Number(info.value?.count) || 0)
	const tickets = computed(() => info.value?.tickets || [])
	const hasMembership = computed(() => count.value > 0)
	// Backend already orders tickets by valid_to ascending, so the first one is
	// the soonest-expiring active membership ticket — the one worth surfacing.
	const soonestTicket = computed(() => tickets.value[0] || null)

	/** Load membership summary for a customer. Pass null to clear. */
	async function loadMembership(customer) {
		if (!customer) {
			info.value = null
			return
		}
		loading.value = true
		try {
			const res = await call("ecs_posnext.api.tickets.get_customer_membership", {
				customer,
			})
			info.value = res?.message || res || null
		} catch (e) {
			console.error("Failed to load customer membership", e)
			info.value = null
		} finally {
			loading.value = false
		}
	}

	function reset() {
		info.value = null
	}

	return {
		info,
		loading,
		count,
		tickets,
		hasMembership,
		soonestTicket,
		loadMembership,
		reset,
	}
})
