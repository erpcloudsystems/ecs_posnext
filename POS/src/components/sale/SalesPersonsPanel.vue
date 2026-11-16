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

			<!-- Search -->
			<div class="relative">
				<input
					v-model="search"
					type="text"
					:placeholder="__('Search sales person...')"
					:disabled="store.loading"
					class="w-full h-9 ps-8 pe-3 text-xs border border-gray-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent shadow-sm"
				/>
				<svg class="w-4 h-4 text-gray-400 absolute start-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
				</svg>
			</div>
		</div>

		<!-- Grid of sales persons -->
		<div class="flex-1 overflow-y-auto p-2">
			<!-- Loading -->
			<div v-if="store.loading" class="flex items-center justify-center py-10">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>
			</div>

			<!-- Empty -->
			<div v-else-if="filteredPersons.length === 0" class="flex flex-col items-center justify-center text-center px-3 py-10">
				<div class="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center mb-2">
					<svg class="w-6 h-6 text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
					</svg>
				</div>
				<p class="text-xs font-semibold text-gray-700">
					{{ store.salesPersons.length === 0 ? __("No sales persons available") : __("No matches") }}
				</p>
				<p class="text-[11px] text-gray-500 mt-0.5">{{ __("Tap a card to select, then add their items") }}</p>
			</div>

			<!-- Tiles -->
			<div v-else class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-2 xl:grid-cols-3 gap-1.5">
				<button
					v-for="person in filteredPersons"
					:key="person.name"
					type="button"
					@click="onTileClick(person)"
					:class="[
						'relative flex flex-col items-center text-center rounded-xl border p-2 transition-all touch-manipulation active:scale-[0.97]',
						isActive(person.name)
							? 'border-purple-500 bg-purple-50 ring-2 ring-purple-300 shadow-sm'
							: isSelected(person.name)
								? 'border-purple-300 bg-purple-50/40'
								: 'border-gray-200 bg-white hover:border-purple-300',
					]"
				>
					<!-- Remove (selected only) -->
					<span
						v-if="isSelected(person.name)"
						@click.stop="store.removeSalesPerson(person.name)"
						class="absolute top-1 end-1 w-5 h-5 flex items-center justify-center text-gray-400 hover:text-red-600 rounded-full hover:bg-red-50"
						:title="__('Remove from selection')"
					>
						<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="3">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</span>

					<!-- Item count badge (selected only) -->
					<span
						v-if="isSelected(person.name) && stats[person.name]?.count"
						class="absolute top-1 start-1 min-w-[18px] h-[18px] px-1 flex items-center justify-center text-[10px] font-bold text-white bg-purple-600 rounded-full"
					>
						{{ stats[person.name].count }}
					</span>

					<!-- Invoices this sales person is on in the current shift. Physical
					     top-left; shifted over when that corner already holds the remove
					     button (RTL) or the cart item count (LTR) of a selected tile. -->
					<span
						v-if="invoiceCounts[person.name]"
						:class="[
							'absolute top-1 inline-flex items-center gap-0.5 h-[18px] px-1 rounded-full text-[10px] font-bold tabular-nums leading-none text-green-700 bg-green-100 border border-green-200',
							invoiceBadgeShifted(person.name) ? 'left-7' : 'left-1',
						]"
						:title="__('Invoices in this shift: {0}', [invoiceCounts[person.name]])"
					>
						<svg class="w-2.5 h-2.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 3h12v18l-3-2-3 2-3-2-3 2V3z" />
							<path stroke-linecap="round" stroke-linejoin="round" d="M9 8h6M9 12h6" />
						</svg>
						{{ invoiceCounts[person.name] }}
					</span>

					<!-- Nickname — no avatar above it, so the name gets the whole tile
					     and reads at a larger size. Selected tiles pad the sides to stay
					     clear of the corner remove/count badges. -->
					<div
						:class="[
							'w-full min-h-[42px] flex items-center justify-center',
							isSelected(person.name) ? 'px-4' : 'px-0.5',
							invoiceCounts[person.name] ? 'pt-4' : '',
						]"
					>
						<span class="text-[13px] font-bold text-gray-900 leading-tight line-clamp-3">
							{{ getNickname(person) }}
						</span>
					</div>

					<!-- Footer row, in normal flow under the name so nothing overlaps it -->
					<div
						v-if="isActive(person.name) || (isSelected(person.name) && stats[person.name]?.amount)"
						class="mt-1 flex flex-wrap items-center justify-center gap-1"
					>
						<!-- Active label -->
						<span
							v-if="isActive(person.name)"
							class="inline-flex items-center h-5 text-[9px] font-bold text-white bg-purple-600 rounded-md px-1.5"
						>
							{{ __("ACTIVE") }}
						</span>
						<!-- Amount (selected, non-active) -->
						<span
							v-else-if="isSelected(person.name) && stats[person.name]?.amount"
							class="text-[10px] font-semibold text-purple-600"
						>
							{{ formatCurrency(stats[person.name].amount) }}
						</span>
					</div>
				</button>
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { call } from "frappe-ui"
import { isOffline } from "@/utils/offline/sync"
import { useLocale } from "@/composables/useLocale"
import { usePOSSalesPersonStore } from "@/stores/posSalesPerson"
import { usePOSCartStore } from "@/stores/posCart"
import { usePOSShiftStore } from "@/stores/posShift"
import { formatCurrency as formatCurrencyUtil, DEFAULT_CURRENCY } from "@/utils/currency"

const store = usePOSSalesPersonStore()
const cartStore = usePOSCartStore()
const shiftStore = usePOSShiftStore()

const search = ref("")

// All sales persons (master list), filtered by search term
const filteredPersons = computed(() => {
	const term = (search.value || "").toLowerCase()
	const list = store.salesPersons
	if (!term) return list
	return list.filter((p) =>
		(getNickname(p) || "").toLowerCase().includes(term),
	)
})

const selectedSet = computed(() => new Set(store.selected.map((p) => p.sales_person)))

function isSelected(id) {
	return selectedSet.value.has(id)
}
function isActive(id) {
	return store.activeSalesPerson === id
}

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

function getNickname(person) {
	// Try multiple possible field names for the nickname
	// The custom field might be named differently in the database
	return (
		person.custom_nickname ||
		person.nickname ||
		person.sales_person_name ||
		person.name ||
		"?"
	)
}

function formatCurrency(value) {
	return formatCurrencyUtil(value || 0, shiftStore.profileCurrency || DEFAULT_CURRENCY)
}

// Tap a tile: select+activate if new, otherwise just make it active
function onTileClick(person) {
	const id = person.name
	if (!isSelected(id)) {
		store.addSalesPerson(person)
	}
	store.setActive(id)
}

const { isRTL } = useLocale()

// Is the physical top-left corner of this tile already taken?
function invoiceBadgeShifted(id) {
	if (!isSelected(id)) return false
	return isRTL.value ? true : !!stats.value[id]?.count
}

// {sales_person: number of submitted invoices in the current shift}
const invoiceCounts = ref({})
let refreshTimer = null

async function loadInvoiceCounts() {
	const shift = shiftStore.currentShift?.name
	if (!shift || isOffline()) return
	try {
		invoiceCounts.value =
			(await call("ecs_posnext.api.pos_profile.get_sales_person_invoice_counts", {
				pos_opening_shift: shift,
			})) || {}
	} catch {
		// Badge is informational; keep the last known counts
	}
}

// The cart empties after each completed sale, so refresh then (with a short
// delay for the submit to land), and when the shift changes
watch(
	() => cartStore.invoiceItems.length,
	(len, prev) => {
		if (len === 0 && prev > 0) setTimeout(loadInvoiceCounts, 1500)
	},
)
watch(() => shiftStore.currentShift?.name, loadInvoiceCounts)

onMounted(() => {
	store.loadSalesPersons(shiftStore.profileName)
	loadInvoiceCounts()
	// Catch invoices made on other terminals in the same shift
	refreshTimer = setInterval(loadInvoiceCounts, 60000)
})

onBeforeUnmount(() => clearInterval(refreshTimer))
</script>
