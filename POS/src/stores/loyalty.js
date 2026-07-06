import { defineStore } from "pinia"
import { computed, ref } from "vue"
import { call } from "@/utils/apiWrapper"

/**
 * Loyalty wallet (points + cashback) bridge to the loyalty_engine app.
 * Loads the selected customer's balance + the loyalty settings the POS needs to
 * offer redemption at the payment screen.
 */
export const useLoyaltyStore = defineStore("loyalty", () => {
	const info = ref(null)
	const loading = ref(false)

	const enabled = computed(() => !!info.value?.enabled)
	const exchangeRate = computed(
		() => Number(info.value?.points_exchange_rate) || 1,
	)
	const availablePoints = computed(
		() => Number(info.value?.available_points) || 0,
	)
	const availablePointsValue = computed(
		() => Number(info.value?.available_points_value) || 0,
	)
	const availableCashback = computed(
		() => Number(info.value?.available_cashback) || 0,
	)
	const maxPointsPercent = computed(
		() => Number(info.value?.max_points_redemption_percent) || 100,
	)
	const maxCashbackPercent = computed(
		() => Number(info.value?.max_cashback_usage_percent) || 100,
	)
	const modeOfPayment = computed(
		() => info.value?.default_mode_of_payment || null,
	)
	const hasBalance = computed(
		() => availablePointsValue.value > 0 || availableCashback.value > 0,
	)

	// Reward card details
	const customerCategory = computed(() => info.value?.customer_category || null)
	const visits = computed(() => info.value?.visits || 0)
	const mobileNo = computed(() => info.value?.mobile_no || null)
	const pointsExpiring = computed(
		() => Number(info.value?.points_expiring) || 0,
	)
	const pointsExpiryDate = computed(
		() => info.value?.points_expiry_date || null,
	)
	const cashbackExpiring = computed(
		() => Number(info.value?.cashback_expiring) || 0,
	)
	const cashbackExpiryDate = computed(
		() => info.value?.cashback_expiry_date || null,
	)

	/** Load wallet + settings for a customer. Pass null to clear. */
	async function loadLoyalty(customer) {
		if (!customer) {
			info.value = null
			return
		}
		loading.value = true
		try {
			const res = await call("ecs_posnext.api.loyalty.get_loyalty_info", {
				customer,
			})
			info.value = res?.message || res || null
		} catch (e) {
			console.error("Failed to load loyalty info", e)
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
		enabled,
		exchangeRate,
		availablePoints,
		availablePointsValue,
		availableCashback,
		maxPointsPercent,
		maxCashbackPercent,
		modeOfPayment,
		hasBalance,
		customerCategory,
		visits,
		mobileNo,
		pointsExpiring,
		pointsExpiryDate,
		cashbackExpiring,
		cashbackExpiryDate,
		loadLoyalty,
		reset,
	}
})
