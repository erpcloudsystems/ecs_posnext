<template>
	<div
		v-if="store.items.length"
		class="fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 shadow-lg px-3 sm:px-4 py-2.5 sm:py-3 flex items-center justify-between gap-3 z-40"
	>
		<div class="text-sm text-gray-700">
			<span class="font-semibold text-gray-900">{{ store.itemCount }}</span>
			{{ __('item(s)') }}
			<span class="mx-1 text-gray-300">|</span>
			<span class="font-semibold text-gray-900">{{ formatCurrencyCode(store.total, currency) }}</span>
		</div>
		<Button variant="solid" @click="showCheckout = true">
			{{ __('Review & Book') }}
		</Button>

		<ReservationCheckoutDialog v-model="showCheckout" :currency="currency" />
	</div>
</template>

<script setup>
import { Button } from "frappe-ui"
import { ref } from "vue"
import { useBuildReservationStore } from "@/stores/buildReservation"
import { formatCurrencyCode } from "@/utils/currency"
import { __ } from "@/utils/translation"
import ReservationCheckoutDialog from "./ReservationCheckoutDialog.vue"

defineProps({
	currency: { type: String, default: "SAR" },
})

const store = useBuildReservationStore()
const showCheckout = ref(false)
</script>
