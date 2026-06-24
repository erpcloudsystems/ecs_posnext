<template>
	<div class="flex flex-col h-full bg-white">
		<!-- Header -->
		<div class="px-2.5 py-2 border-b border-gray-200 bg-gray-50">
			<div class="flex items-center gap-1.5 mb-2">
				<svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-1.13a4 4 0 10-4 0m4 0a4 4 0 014 4M9 11a4 4 0 100-8 4 4 0 000 8z" />
				</svg>
				<h3 class="text-sm font-bold text-gray-900">{{ __("Sales Persons") }}</h3>
				<span v-if="store.selected.length" class="ms-auto text-[10px] font-semibold text-purple-600 bg-purple-50 border border-purple-200 rounded-full px-2 py-0.5">
					{{ store.selected.length }}
				</span>
			</div>

			<!-- Add sales person -->
			<div class="relative" ref="dropdownContainer">
				<input
					v-model="search"
					type="text"
					:placeholder="__('Add sales person...')"
					@focus="open = true"
					@blur="handleBlur"
					:disabled="store.loading"
					class="w-full h-9 ps-8 pe-3 text-xs border border-gray-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent shadow-sm"
				/>
				<svg class="w-4 h-4 text-gray-400 absolute start-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
				</svg>

				<!-- Dropdown -->
				<div
					v-if="open && filteredAvailable.length > 0"
					class="absolute z-50 mt-1 w-full max-h-56 overflow-y-auto border border-purple-200 rounded-xl bg-white shadow-lg"
				>
					<button
						v-for="person in filteredAvailable"
						:key="person.name"
						type="button"
						@mousedown.prevent="addPerson(person)"
						class="w-full flex items-center justify-between p-2.5 hover:bg-purple-50 cursor-pointer border-b border-gray-100 last:border-b-0 text-xs text-start"
					>
						<span class="font-medium text-gray-900 truncate">{{ person.sales_person_name || person.name }}</span>
						<span v-if="person.commission_rate" class="text-purple-500 text-[10px] flex-shrink-0 ms-2">
							{{ person.commission_rate }}%
						</span>
					</button>
				</div>
				<div
					v-else-if="open && !store.loading"
					class="absolute z-50 mt-1 w-full border border-purple-200 rounded-xl bg-white shadow-lg"
				>
					<div class="text-center py-3 text-xs text-gray-500">
						{{ store.salesPersons.length === 0 ? __('No sales persons available') : __('All sales persons added') }}
					</div>
				</div>
			</div>
		</div>

		<!-- Selected sales persons list -->
		<div class="flex-1 overflow-y-auto p-2 space-y-1.5">
			<!-- Empty state -->
			<div v-if="store.selected.length === 0" class="flex flex-col items-center justify-center text-center px-3 py-10">
				<div class="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center mb-2">
					<svg class="w-6 h-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
					</svg>
				</div>
				<p class="text-xs font-semibold text-gray-700">{{ __("No sales persons yet") }}</p>
				<p class="text-[11px] text-gray-500 mt-0.5">{{ __("Add a sales person, then select items for them") }}</p>
			</div>

			<!-- Cards -->
			<div
				v-for="person in store.selected"
				:key="person.sales_person"
				@click="store.setActive(person.sales_person)"
				:class="[
					'rounded-xl border p-2 cursor-pointer transition-all',
					person.sales_person === store.activeSalesPerson
						? 'border-purple-500 bg-purple-50 ring-1 ring-purple-300 shadow-sm'
						: 'border-gray-200 bg-white hover:border-purple-300',
				]"
			>
				<div class="flex items-center gap-2">
					<!-- Active radio dot -->
					<span
						:class="[
							'w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center',
							person.sales_person === store.activeSalesPerson ? 'border-purple-600' : 'border-gray-300',
						]"
					>
						<span v-if="person.sales_person === store.activeSalesPerson" class="w-2 h-2 rounded-full bg-purple-600"></span>
					</span>

					<div class="min-w-0 flex-1">
						<p class="text-xs font-bold text-gray-900 truncate leading-tight">
							{{ person.sales_person_name || person.sales_person }}
						</p>
						<p class="text-[10px] text-gray-500 leading-tight">
							{{ __("{0} item(s)", [stats[person.sales_person]?.count || 0]) }}
							<span v-if="stats[person.sales_person]?.amount" class="text-purple-600 font-semibold">
								· {{ formatCurrency(stats[person.sales_person].amount) }}
							</span>
						</p>
					</div>

					<!-- Active badge -->
					<span
						v-if="person.sales_person === store.activeSalesPerson"
						class="text-[9px] font-bold text-white bg-purple-600 rounded-full px-1.5 py-0.5 flex-shrink-0"
					>
						{{ __("ACTIVE") }}
					</span>

					<button
						type="button"
						@click.stop="store.removeSalesPerson(person.sales_person)"
						class="w-6 h-6 flex items-center justify-center text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50 flex-shrink-0"
						:title="__('Remove sales person')"
					>
						<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
			</div>
		</div>

		<!-- Hint footer -->
		<div v-if="store.activeSalesPerson" class="px-2.5 py-2 border-t border-gray-200 bg-purple-50">
			<p class="text-[11px] text-purple-700 leading-snug">
				<svg class="w-3.5 h-3.5 inline -mt-0.5 me-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				{{ __("Items you add go to {0}", [store.nameFor(store.activeSalesPerson)]) }}
			</p>
		</div>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import { usePOSSalesPersonStore } from "@/stores/posSalesPerson"
import { usePOSCartStore } from "@/stores/posCart"
import { usePOSShiftStore } from "@/stores/posShift"
import { formatCurrency as formatCurrencyUtil, DEFAULT_CURRENCY } from "@/utils/currency"

const store = usePOSSalesPersonStore()
const cartStore = usePOSCartStore()
const shiftStore = usePOSShiftStore()

const search = ref("")
const open = ref(false)
const dropdownContainer = ref(null)

const filteredAvailable = computed(() => {
	const term = (search.value || "").toLowerCase()
	const list = store.availableSalesPersons
	if (!term) return list.slice(0, 20)
	return list
		.filter((p) => (p.sales_person_name || p.name || "").toLowerCase().includes(term))
		.slice(0, 20)
})

// Per-person item count + amount, derived from cart items
const stats = computed(() => {
	const map = {}
	for (const item of cartStore.invoiceItems) {
		const sp = item.sales_person
		if (!sp) continue
		if (!map[sp]) map[sp] = { count: 0, amount: 0 }
		map[sp].count += 1
		map[sp].amount += item.amount || 0
	}
	return map
})

function formatCurrency(value) {
	return formatCurrencyUtil(value || 0, shiftStore.profileCurrency || DEFAULT_CURRENCY)
}

function addPerson(person) {
	store.addSalesPerson(person)
	search.value = ""
}

function handleBlur() {
	setTimeout(() => {
		open.value = false
	}, 150)
}

onMounted(() => {
	store.loadSalesPersons(shiftStore.profileName)
})
</script>
