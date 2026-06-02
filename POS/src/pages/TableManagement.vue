<template>
	<div class="flex flex-col bg-gray-50 h-screen overflow-hidden">
		<!-- Header -->
		<div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm flex-shrink-0">
			<div class="flex items-center gap-4">
				<router-link to="/" class="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500">
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
					</svg>
				</router-link>
				<div>
					<h1 class="text-xl font-bold text-gray-900">{{ __("Table Management") }}</h1>
					<p class="text-xs text-gray-500">{{ __("Monitor and manage restaurant table status") }}</p>
				</div>
			</div>
			<div class="flex items-center gap-3">
				<button 
					@click="fetchTables"
					:disabled="loading"
					class="p-2.5 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 active:scale-95 transition-all shadow-sm"
				>
					<svg class="w-5 h-5 text-gray-600" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
					</svg>
				</button>
			</div>
		</div>

		<!-- Main Content -->
		<div class="flex-1 overflow-y-auto p-6">
			<div v-if="loading && tables.length === 0" class="flex flex-col items-center justify-center h-full gap-4">
				<div class="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
				<p class="text-gray-500 font-medium">{{ __("Loading tables...") }}</p>
			</div>

			<div v-else-if="tables.length === 0" class="flex flex-col items-center justify-center h-full text-center">
				<div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
					<svg class="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
					</svg>
				</div>
				<h3 class="text-lg font-bold text-gray-900">{{ __("No Tables Found") }}</h3>
				<p class="text-gray-500">{{ __("Please ensure Table Numbers are configured in the system.") }}</p>
			</div>

			<div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
				<div 
					v-for="table in tables" 
					:key="table.name"
					class="bg-white rounded-2xl shadow-sm border-2 overflow-hidden transition-all duration-300 hover:shadow-md"
					:class="table.disabled ? 'border-red-100' : 'border-emerald-100'"
				>
					<!-- Card Header -->
					<div 
						class="px-4 py-3 flex items-center justify-between"
						:class="table.disabled ? 'bg-red-50/50' : 'bg-emerald-50/50'"
					>
						<div class="flex items-center gap-3">
							<div 
								class="w-10 h-10 rounded-xl flex items-center justify-center font-black text-lg"
								:class="table.disabled ? 'bg-red-500 text-white shadow-lg shadow-red-200' : 'bg-emerald-500 text-white shadow-lg shadow-emerald-200'"
							>
								{{ table.no }}
							</div>
							<div>
								<span class="text-xs font-bold uppercase tracking-wider" :class="table.disabled ? 'text-red-600' : 'text-emerald-600'">
									{{ table.disabled ? __('Occupied') : __('Available') }}
								</span>
							</div>
						</div>
						
						<!-- Status Indicator -->
						<div class="flex items-center gap-1.5">
							<div class="w-2 h-2 rounded-full animate-pulse" :class="table.disabled ? 'bg-red-500' : 'bg-emerald-500'"></div>
						</div>
					</div>

					<!-- Card Body -->
					<div class="p-4">
						<div v-if="table.draft" class="space-y-3">
							<div>
								<p class="text-[10px] font-bold text-gray-400 uppercase mb-1">{{ __("Active Order") }}</p>
								<div class="flex items-center justify-between">
									<p class="text-sm font-bold text-gray-900">{{ table.draft.name }}</p>
									<p class="text-sm font-black text-blue-600">{{ formatCurrency(table.draft.grand_total) }}</p>
								</div>
							</div>
							<div>
								<p class="text-[10px] font-bold text-gray-400 uppercase mb-1">{{ __("Customer") }}</p>
								<p class="text-sm font-medium text-gray-700 truncate">{{ table.draft.customer_name }}</p>
							</div>
							<div class="flex items-center justify-between pt-1">
								<span class="text-[10px] text-gray-500">{{ __("Since:") }} {{ formatTime(table.draft.creation) }}</span>
							</div>
						</div>
						<div v-else class="flex flex-col items-center justify-center py-6 text-gray-400 italic">
							<svg class="w-8 h-8 mb-2 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<circle cx="12" cy="12" r="10" stroke-width="2"/>
							</svg>
							<p class="text-xs font-medium">{{ __("Ready for new guest") }}</p>
						</div>
					</div>

					<!-- Card Actions -->
					<div class="px-4 py-3 bg-gray-50 border-t border-gray-100 flex gap-2">
						<button 
							v-if="table.draft"
							@click="viewDetails(table.draft.name)"
							class="flex-1 px-3 py-2 text-xs font-bold text-blue-600 bg-white border border-blue-100 rounded-lg hover:bg-blue-50 transition-colors shadow-sm active:scale-95"
						>
							{{ __("Details") }}
						</button>
						<button 
							v-if="table.disabled"
							@click="confirmReopen(table)"
							class="flex-1 px-3 py-2 text-xs font-bold text-red-600 bg-white border border-red-100 rounded-lg hover:bg-red-50 transition-colors shadow-sm active:scale-95"
						>
							{{ __("Reopen") }}
						</button>
						<div v-else class="flex-1 text-center text-[10px] font-bold text-gray-400 py-2 border border-dashed border-gray-200 rounded-lg">
							{{ __("No actions") }}
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Details Modal -->
		<Dialog v-model="showDetails" :options="{ title: __('Order Details'), size: 'lg' }" class="z-[300]">
			<template #body-content>
				<div v-if="loadingDetails" class="flex justify-center py-12">
					<div class="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
				</div>
				<div v-else-if="orderDetails" class="space-y-6">
					<!-- Modal Header -->
					<div class="flex items-center justify-between pb-4 border-b border-gray-100">
						<div>
							<p class="text-xs font-bold text-gray-400 uppercase mb-1">{{ __("Invoice") }}</p>
							<h3 class="text-lg font-black text-gray-900">{{ orderDetails.name }}</h3>
						</div>
						<div class="text-right">
							<p class="text-xs font-bold text-gray-400 uppercase mb-1">{{ __("Total Amount") }}</p>
							<p class="text-xl font-black text-blue-600">{{ formatCurrency(orderDetails.grand_total) }}</p>
						</div>
					</div>

					<!-- Customer Info -->
					<div class="bg-blue-50 rounded-xl p-4 flex items-center gap-4 border border-blue-100">
						<div class="w-12 h-12 bg-white rounded-full flex items-center justify-center text-blue-600 shadow-sm font-black text-xl">
							{{ orderDetails.customer_name?.charAt(0) }}
						</div>
						<div>
							<p class="text-sm font-bold text-gray-900">{{ orderDetails.customer_name }}</p>
							<p class="text-xs text-gray-500">{{ orderDetails.customer }}</p>
						</div>
					</div>

					<!-- Items List -->
					<div>
						<p class="text-xs font-bold text-gray-400 uppercase mb-3 flex items-center gap-2">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path d="M4 6h16M4 12h16m-7 6h7"/>
							</svg>
							{{ __("Items Ordered") }}
						</p>
						<div class="bg-gray-50 rounded-2xl border border-gray-200 overflow-hidden">
							<table class="w-full text-left text-sm border-collapse">
								<thead class="bg-gray-100 border-b border-gray-200">
									<tr>
										<th class="px-4 py-2 font-bold text-gray-600">{{ __("Item") }}</th>
										<th class="px-4 py-2 font-bold text-gray-600 text-center">{{ __("Qty") }}</th>
										<th class="px-4 py-2 font-bold text-gray-600 text-right">{{ __("Amount") }}</th>
									</tr>
								</thead>
								<tbody class="divide-y divide-gray-200">
									<tr v-for="item in orderDetails.items" :key="item.item_code" class="hover:bg-white transition-colors">
										<td class="px-4 py-3">
											<p class="font-bold text-gray-900">{{ item.item_name }}</p>
											<p class="text-[10px] text-gray-500">{{ item.item_code }}</p>
										</td>
										<td class="px-4 py-3 text-center">
											<span class="px-2 py-1 bg-white border border-gray-200 rounded-lg font-black text-gray-700">
												{{ item.qty }}
											</span>
										</td>
										<td class="px-4 py-3 text-right font-bold text-gray-900">
											{{ formatCurrency(item.amount) }}
										</td>
									</tr>
								</tbody>
							</table>
						</div>
					</div>
				</div>
			</template>
			<template #actions>
				<div class="flex gap-3 w-full">
					<button 
						@click="reopenFromDetails"
						class="flex-1 px-4 py-2.5 rounded-xl bg-red-600 text-white font-bold hover:bg-red-700 shadow-lg shadow-red-200 active:scale-95 transition-all"
					>
						{{ __("Reopen Table") }}
					</button>
					<button 
						@click="showDetails = false"
						class="flex-1 px-4 py-2.5 rounded-xl bg-gray-100 text-gray-700 font-bold hover:bg-gray-200 active:scale-95 transition-all"
					>
						{{ __("Close") }}
					</button>
				</div>
			</template>
		</Dialog>

		<!-- Confirmation Modal -->
		<Dialog v-model="showConfirm" :options="{ title: __ ('Confirm Reopen'), size: 'sm' }" class="z-[400]">
			<template #body-content>
				<div class="p-2 text-center">
					<div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-red-600 mx-auto mb-4 shadow-inner">
						<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
						</svg>
					</div>
					<h3 class="text-lg font-bold text-gray-900 mb-2">{{ __("Reopen Table {0}?", [pendingReopenTable?.no]) }}</h3>
					<p class="text-sm text-gray-500">
						{{ __("This will set the table to 'Available'. The active order will remain as a draft but the table will be freed.") }}
					</p>
				</div>
			</template>
			<template #actions>
				<div class="flex gap-3 w-full">
					<button 
						@click="executeReopen"
						class="flex-1 px-4 py-2.5 rounded-xl bg-red-600 text-white font-bold hover:bg-red-700 active:scale-95 transition-all"
					>
						{{ __("Reopen Now") }}
					</button>
					<button 
						@click="showConfirm = false"
						class="flex-1 px-4 py-2.5 rounded-xl bg-gray-100 text-gray-700 font-bold hover:bg-gray-200 active:scale-95 transition-all"
					>
						{{ __("Cancel") }}
					</button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { createResource, Dialog } from 'frappe-ui';
import { formatCurrency as formatCurrencyUtil, DEFAULT_CURRENCY } from '@/utils/currency';
import { useSocket } from '@/socket';

const tables = ref([]);
const loading = ref(false);

const showDetails = ref(false);
const loadingDetails = ref(false);
const orderDetails = ref(null);

const showConfirm = ref(false);
const pendingReopenTable = ref(null);

const socket = useSocket();

const tablesResource = createResource({
	url: 'ecs_posnext.api.invoices.get_tables_with_draft_info',
	auto: false,
	onSuccess(data) {
		tables.value = data || [];
		loading.value = false;
	},
	onError() {
		loading.value = false;
	}
});

// Direct fetch fallback using frappe.call (bypasses createResource caching)
async function directFetchTables() {
	try {
		const response = await fetch('/api/method/ecs_posnext.api.invoices.get_tables_with_draft_info', {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				'X-Frappe-CSRF-Token': window.csrf_token || '',
			},
			credentials: 'include',
		});
		const result = await response.json();
		if (result.message) {
			tables.value = result.message;
		}
	} catch (err) {
		console.error('[TableManagement] Direct fetch failed:', err);
	}
}

const detailsResource = createResource({
	url: 'ecs_posnext.api.invoices.get_draft_invoice_details',
	auto: false,
	onSuccess(data) {
		orderDetails.value = data;
		loadingDetails.value = false;
	},
	onError() {
		loadingDetails.value = false;
	}
});

const reopenResource = createResource({
	url: 'ecs_posnext.api.invoices.reopen_table',
	auto: false,
	onSuccess() {
		showConfirm.value = false;
		showDetails.value = false;
		fetchTables();
	}
});

function fetchTables(silent = false) {
	if (!silent) loading.value = true;
	tablesResource.reload();
}

function viewDetails(invoiceName) {
	orderDetails.value = null;
	showDetails.value = true;
	loadingDetails.value = true;
	detailsResource.fetch({ invoice_name: invoiceName });
}

function confirmReopen(table) {
	pendingReopenTable.value = table;
	showConfirm.value = true;
}

function reopenFromDetails() {
	if (!orderDetails.value) return;
	// Find the table that has this draft
	const table = tables.value.find(t => t.draft?.name === orderDetails.value.name);
	if (table) {
		confirmReopen(table);
	}
}

function executeReopen() {
	if (!pendingReopenTable.value) return;
	reopenResource.fetch({ table_name: pendingReopenTable.value.name });
}

function formatCurrency(value) {
	return formatCurrencyUtil(value, DEFAULT_CURRENCY);
}

function formatTime(timestamp) {
	if (!timestamp) return '';
	const date = new Date(timestamp);
	return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Periodic poll interval handle
let pollInterval = null;

onMounted(() => {
	fetchTables();

	// Periodic poll every 15s as safety net for missed socket events
	pollInterval = setInterval(() => {
		directFetchTables();
	}, 15000);

	if (socket) {
		socket.connect();

		const subscribe = () => {
			console.log('[Socket] Connected, subscribing to Table Number events');
			socket.emit('doctype_subscribe', 'Table Number');
		};

		if (socket.connected) {
			subscribe();
		}

		socket.on('connect', subscribe);

		const handleUpdate = (event, data) => {
			console.log(`[TableManagement] Realtime update [${event}] received:`, data);
			// Use direct fetch to bypass any createResource caching
			setTimeout(() => {
				directFetchTables();
			}, 800);
		};

		socket.on('table_status_changed', (data) => handleUpdate('table_status_changed', data));
		socket.on('pos_invoice_created', (data) => handleUpdate('pos_invoice_created', data));

		// Frappe wraps events inside list_update / doc_update for doctype subscriptions
		socket.on('list_update', (data) => {
			if (data?.doctype === 'Table Number') {
				console.log('[TableManagement] list_update for Table Number:', data);
				handleUpdate('list_update', data);
			}
		});

		// Fallback for some Frappe versions/configurations
		socket.on('msg', (data) => {
			const event = data?.event || data?.message?.event;
			if (data && (event === 'table_status_changed' || event === 'pos_invoice_created')) {
				console.log(`[TableManagement] Realtime update [${event}] received via msg:`, data);
				handleUpdate(event, data);
			}
		});
	}
});

onUnmounted(() => {
	if (pollInterval) {
		clearInterval(pollInterval);
		pollInterval = null;
	}
	if (socket) {
		socket.emit('doctype_unsubscribe', 'Table Number');
		socket.off('table_status_changed');
		socket.off('pos_invoice_created');
		socket.off('list_update');
		socket.off('msg');
		socket.off('connect');
	}
});
</script>
