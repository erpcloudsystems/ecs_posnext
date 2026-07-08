<template>
	<Dialog v-model="show" :options="{ title: guestStep ? __('Number of Guests') : __('Select Table'), size: '2xl' }">
		<template #body-content>
			<div class="flex flex-col h-full min-h-[400px]">

			<!-- Guest count step -->
			<div v-if="guestStep" class="flex flex-col items-center justify-center flex-1 gap-6 p-8">
				<svg class="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
				</svg>
				<div class="text-center">
					<p class="text-sm font-bold text-gray-800 mb-1">{{ pendingTable?.name }}</p>
					<p class="text-xs text-gray-500">{{ __('How many guests?') }}</p>
				</div>
				<!-- Quick select buttons -->
				<div class="grid grid-cols-4 gap-3 w-full max-w-xs">
					<button
						v-for="n in [1,2,3,4,5,6,7,8]"
						:key="n"
						@click="guestCount = n"
						class="h-12 rounded-xl border-2 text-lg font-bold transition-all"
						:class="guestCount === n ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300'"
					>{{ n }}</button>
				</div>
				<!-- Custom input -->
				<div class="flex items-center gap-2">
					<button @click="guestCount = Math.max(1, (guestCount||1) - 1)" class="w-9 h-9 rounded-full border border-gray-300 flex items-center justify-center text-lg font-bold text-gray-600 hover:bg-gray-100">−</button>
					<input
						v-model.number="guestCount"
						type="number"
						min="1"
						class="w-16 h-9 text-center text-lg font-bold border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
					/>
					<button @click="guestCount = (guestCount||1) + 1" class="w-9 h-9 rounded-full border border-gray-300 flex items-center justify-center text-lg font-bold text-gray-600 hover:bg-gray-100">+</button>
				</div>
				<!-- Confirm / Back -->
				<div class="flex gap-3 w-full max-w-xs">
					<button @click="guestStep = false; pendingTable = null" class="flex-1 h-10 border border-gray-300 rounded-xl text-sm font-bold text-gray-600 hover:bg-gray-100">
						{{ __('Back') }}
					</button>
					<button @click="confirmTableWithGuests" class="flex-1 h-10 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 disabled:opacity-50" :disabled="!guestCount || guestCount < 1">
						{{ __('Confirm') }}
					</button>
				</div>
			</div>

			<!-- Table grid (hidden while guest step is shown) -->
			<template v-else>
				<div v-if="loading" class="flex items-center justify-center flex-1">
					<svg class="animate-spin w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
					</svg>
				</div>
				<div v-else-if="tables.length === 0" class="flex flex-col items-center justify-center flex-1 text-gray-500">
					<svg class="w-12 h-12 mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
					</svg>
					<span class="text-sm">{{ __('No tables available') }}</span>
				</div>
				<div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 p-4 overflow-y-auto content-start">
					<div 
						v-for="table in tablesWithStatus" 
						:key="table.name" 
						@click="handleTableSelect(table)"
						class="relative flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all cursor-pointer hover:shadow-md h-32"
						:class="[
							table.isOccupied 
								? 'border-orange-200 bg-orange-50 hover:border-orange-300'
								: 'border-green-200 bg-green-50 hover:border-green-300',
							cartStore.selectedTable === table.name ? 'ring-2 ring-blue-500 shadow-md scale-[1.02]' : ''
						]"
					>
						<div class="absolute top-2 right-2 flex">
							<span 
								class="px-2 py-0.5 text-[10px] font-bold rounded-full"
								:class="table.isOccupied ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'"
							>
								{{ table.isOccupied ? __('Occupied') : __('Free') }}
							</span>
						</div>
						
						<svg 
							class="w-10 h-10 mb-2"
							:class="table.isOccupied ? 'text-orange-400' : 'text-green-500'"
							fill="none" stroke="currentColor" viewBox="0 0 24 24"
						>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
						</svg>
						
						<span class="font-bold text-gray-800 text-center truncate w-full">{{ table.no }}</span>
						
						<div v-if="table.isOccupied" class="mt-1 flex flex-col items-center">
							<span v-if="table.invoice" class="text-xs font-semibold text-gray-700">{{ formatCurrency(table.invoice.grand_total) }}</span>
							<div class="mt-1 px-3 py-1 bg-white border border-gray-200 rounded-md text-[10px] font-bold text-gray-700 hover:bg-gray-50 flex items-center gap-1 shadow-sm">
								<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
								{{ __('Reopen') }}
							</div>
						</div>
					</div>
				</div>
			</template><!-- end v-else table grid -->

			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { usePOSCartStore } from '@/stores/posCart'
import { usePOSShiftStore } from '@/stores/posShift'
import { createResource } from 'frappe-ui'
import { call } from '@/utils/apiWrapper'
import { formatCurrency as formatCurrencyUtil, DEFAULT_CURRENCY } from '@/utils/currency'

const props = defineProps({
	modelValue: {
	type: Boolean,
		default: false
	},
	currency: {
		type: String,
		default: DEFAULT_CURRENCY
	}
})

const emit = defineEmits(['update:modelValue', 'select-table', 'reopen-invoice'])

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit('update:modelValue', val)
})

const cartStore = usePOSCartStore()
const shiftStore = usePOSShiftStore()

const tables = ref([])
const draftInvoices = ref([])
const loading = ref(false)
const guestStep = ref(false)
const pendingTable = ref(null)
const guestCount = ref(null)

const tablesResource = createResource({
	url: 'frappe.client.get_list',
	makeParams() {
		return {
			doctype: 'Table Number',
			filters: {
				branch: cartStore.selectedBranch || shiftStore.profileBranch || '',

			},

			fields: '["name", "status", "no"]',
			order_by: 'no asc',
			// frappe.client.get_list uses limit_page_length (default 20); 0 = no limit / all rows
			limit_page_length: 0
		}
	},
	auto: false,
	onSuccess(data) {
		tables.value = data || []
	}
})

const tablesWithStatus = computed(() => {
	return tables.value.map(table => {
		const invoice = draftInvoices.value.find(inv =>
			inv.custom_order_type === 'Dine In' &&
			inv.custom_table_number === table.name
		)

		return {
			...table,
			isOccupied: table.status === 'disabled' || table.status === 'Disabled' || !!invoice,
			invoice: invoice || null
		}
	}).sort((a, b) =>
		// Numeric-aware sort so table numbers order 1, 2, 3 … 10, 11 instead of 1, 10, 11, 2
		String(a.no ?? '').localeCompare(String(b.no ?? ''), undefined, { numeric: true, sensitivity: 'base' })
	)
})

async function fetchDraftInvoices() {
	try {
		const shiftName = shiftStore.shiftName
		if (!shiftName) return
		
		const data = await call('ecs_posnext.api.invoices.get_draft_invoices', {
			pos_opening_shift: shiftName
		})
		
		draftInvoices.value = data || []
	} catch (err) {
		console.error('Failed to fetch draft invoices:', err)
		draftInvoices.value = []
	}
}

async function loadData() {
	loading.value = true
	await Promise.all([
		tablesResource.fetch(),
		fetchDraftInvoices()
	])
	loading.value = false
}

watch(() => props.modelValue, (isOpen) => {
	if (isOpen) {
		guestStep.value = false
		pendingTable.value = null
		guestCount.value = null
		loadData()
	}
})

function formatCurrency(amount) {
	return formatCurrencyUtil(Number.parseFloat(amount || 0), props.currency)
}

async function handleTableSelect(table) {
	if (table.isOccupied) {
		if (table.invoice) {
			emit('reopen-invoice', table.invoice)
			show.value = false
		} else {
			try {
				loading.value = true
				const unpaidInvoice = await call('ecs_posnext.api.invoices.get_unpaid_invoice_for_table', {
					table_number: table.name
				})
				loading.value = false
				if (unpaidInvoice) {
					emit('reopen-invoice', unpaidInvoice)
					show.value = false
				} else {
					// Free table that was just cleared — ask for guests
					pendingTable.value = table
					guestCount.value = null
					guestStep.value = true
				}
			} catch (err) {
				loading.value = false
				console.error('Failed to fetch unpaid invoice:', err)
			}
		}
	} else {
		// Free table — ask for number of guests
		pendingTable.value = table
		guestCount.value = null
		guestStep.value = true
	}
}

function confirmTableWithGuests() {
	if (!pendingTable.value) return
	cartStore.selectedTable = pendingTable.value.name
	cartStore.numberOfGuests = guestCount.value || null
	emit('select-table', pendingTable.value.name)
	guestStep.value = false
	pendingTable.value = null
	show.value = false
}
</script>
