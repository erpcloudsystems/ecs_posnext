<template>
	<div v-if="priceLists.length > 1" class="flex items-center gap-1">
		<label class="text-[10px] font-medium text-gray-500 whitespace-nowrap">{{ __("Price List") }}</label>
		<select
			:value="current"
			class="text-[11px] border border-gray-300 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-[160px]"
			@change="onChange($event.target.value)"
		>
			<option v-for="pl in priceLists" :key="pl.name" :value="pl.name">
				{{ pl.name }}
			</option>
		</select>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import { call } from "@/utils/apiWrapper"
import { usePOSCartStore } from "@/stores/posCart"

const props = defineProps({
	posProfile: String,
})

const cartStore = usePOSCartStore()
const priceLists = ref([])
const profileDefault = ref(null)

// Currently selected price list (active override, else profile default).
const current = computed(
	() => cartStore.activePriceList || profileDefault.value || "",
)

async function loadPriceLists() {
	try {
		const res = await call("ecs_posnext.api.pos_profile.get_price_lists", {
			pos_profile: props.posProfile,
		})
		const data = res?.message || res || {}
		priceLists.value = Array.isArray(data) ? data : data.price_lists || []
		profileDefault.value = data.default || null
	} catch (e) {
		console.error("Failed to load price lists", e)
		priceLists.value = []
	}
}

async function onChange(name) {
	if (!name) return
	// Set the active price list and reprice the cart.
	await cartStore.setActivePriceList(name)
	// Apply the price list's default customer (explicit cashier choice → override).
	const pl = priceLists.value.find((p) => p.name === name)
	if (pl?.custom_default_customer) {
		cartStore.setCustomer({
			name: pl.custom_default_customer,
			customer_name: pl.default_customer_name || pl.custom_default_customer,
		})
	}
}

onMounted(loadPriceLists)
</script>
