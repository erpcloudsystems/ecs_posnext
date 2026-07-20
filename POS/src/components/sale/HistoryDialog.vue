<template>
	<Dialog
		v-model="show"
		:options="{ title: __('History'), size: '5xl' }"
	>
		<template #body-content>
			<div class="flex flex-col gap-4">
				<!-- Tabs -->
				<div class="flex items-center gap-1 border-b border-gray-200">
					<button
						type="button"
						@click="activeTab = 'invoices'"
						:class="[
							'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
							activeTab === 'invoices'
								? 'border-indigo-600 text-indigo-600'
								: 'border-transparent text-gray-500 hover:text-gray-700'
						]"
					>
						{{ __('Invoices') }}
					</button>
					<button
						type="button"
						@click="activeTab = 'orders'"
						:class="[
							'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
							activeTab === 'orders'
								? 'border-indigo-600 text-indigo-600'
								: 'border-transparent text-gray-500 hover:text-gray-700'
						]"
					>
						{{ __('Orders') }}
					</button>
				</div>

				<!-- Filters -->
				<div class="flex items-center gap-2">
					<div class="flex-1">
						<Input
							v-model="searchTerm"
							type="text"
							:placeholder="activeTab === 'invoices' ? __('Search by invoice number or customer...') : __('Search by order number or customer...')"
						>
							<template #prefix>
								<svg class="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
								</svg>
							</template>
						</Input>
					</div>
					<Button
						variant="subtle"
						@click="reloadActiveTab"
						:loading="activeResource.loading"
						:title="__('Refresh')"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
						</svg>
					</Button>
				</div>

				<!-- List -->
				<div v-if="activeResource.loading" class="text-center py-8">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
					<p class="mt-3 text-xs text-gray-500">{{ activeTab === 'invoices' ? __('Loading invoices...') : __('Loading orders...') }}</p>
				</div>

				<div v-else-if="activeList.length === 0" class="text-center py-8">
					<svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
					</svg>
					<p class="mt-2 text-sm text-gray-500">{{ activeTab === 'invoices' ? __('No invoices found') : __('No orders found') }}</p>
				</div>

				<!-- Invoices Tab -->
				<div v-else-if="activeTab === 'invoices'" class="flex flex-col gap-2 max-h-96 overflow-y-auto pe-4">
					<div
						v-for="invoice in activeList"
						:key="invoice.name"
						class="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-all"
					>
						<div class="flex items-start justify-between gap-3">
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2 mb-1 flex-wrap">
									<h4 class="text-sm font-semibold text-gray-900">{{ invoice.name }}</h4>
									<span
										v-if="invoice.is_return"
										class="text-xs px-2 py-0.5 rounded-full font-medium bg-red-100 text-red-800"
									>
										{{ __('Return') }}
									</span>
									<span
										v-else
										:class="['text-xs px-2 py-0.5 rounded-full font-medium', getInvoiceStatusColor(invoice)]"
									>
										{{ __(invoice.status) }}
									</span>
								</div>
								<p class="text-xs text-gray-600 text-start">
									{{ invoice.customer_name }}
									<span v-if="invoice.customer_mobile" class="font-semibold text-gray-600">· {{ invoice.customer_mobile }}</span>
								</p>
								<p class="text-xs text-gray-500 text-start">{{ formatDateTime(invoice.posting_date, invoice.posting_time) }}</p>
							</div>
							<div class="flex-shrink-0 flex flex-col items-end">
								<p class="text-sm font-bold text-gray-900 text-end">{{ formatCurrency(invoice.grand_total) }}</p>
								<div class="flex items-center gap-1 mt-2">
									<button
										@click="viewInvoice(invoice)"
										class="p-1.5 hover:bg-blue-50 rounded transition-colors"
										:title="__('View Details')"
									>
										<svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
										</svg>
									</button>
									<button
										@click="printInvoice(invoice)"
										class="p-1.5 hover:bg-green-50 rounded transition-colors"
										:title="__('Print')"
									>
										<svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
										</svg>
									</button>
									<button
										v-if="canCreateReturn(invoice)"
										@click="openReturnModal(invoice)"
										class="p-1.5 hover:bg-orange-50 rounded transition-colors"
										:title="__('Create Return')"
									>
										<svg class="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"/>
										</svg>
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Orders Tab -->
				<div v-else class="flex flex-col gap-2 max-h-96 overflow-y-auto pe-4">
					<div
						v-for="order in activeList"
						:key="order.name"
						class="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-all"
					>
						<div class="flex items-start justify-between gap-3">
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2 mb-1 flex-wrap">
									<h4 class="text-sm font-semibold text-gray-900">{{ order.name }}</h4>
									<span :class="['text-xs px-2 py-0.5 rounded-full font-medium', getSalesOrderStatusColor(order)]">
										{{ __(order.status) }}
									</span>
								</div>
								<p class="text-xs text-gray-600 text-start">
									{{ order.customer_name }}
									<span v-if="order.customer_mobile" class="font-semibold text-gray-600">· {{ order.customer_mobile }}</span>
								</p>
								<p class="text-xs text-gray-500 text-start">{{ formatDate(order.transaction_date) }}</p>
							</div>
							<div class="flex-shrink-0 flex flex-col items-end">
								<p class="text-sm font-bold text-gray-900 text-end">{{ formatCurrency(order.grand_total) }}</p>
								<div class="flex items-center gap-1 mt-2">
									<button
										@click="viewOrder(order)"
										class="p-1.5 hover:bg-blue-50 rounded transition-colors"
										:title="__('View Details')"
									>
										<svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
										</svg>
									</button>
									<button
										@click="printOrder(order)"
										class="p-1.5 hover:bg-green-50 rounded transition-colors"
										:title="__('Print')"
									>
										<svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
										</svg>
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Load More -->
				<div v-if="activeHasMore && !activeResource.loading" class="text-center">
					<Button variant="subtle" @click="loadMore">
						{{ __('Load More') }}
					</Button>
				</div>
			</div>
		</template>
		<template #actions>
			<Button variant="subtle" @click="show = false">
				{{ __('Close') }}
			</Button>
		</template>
	</Dialog>

	<!-- Return Invoice Dialog -->
	<ReturnInvoiceDialog
		v-model="showReturnDialog"
		:pos-profile="posProfile"
		:pos-opening-shift="posOpeningShift"
		:currency="currency"
		:preselected-invoice="selectedInvoiceForReturn"
		@return-created="handleReturnCreated"
	/>
</template>

<script setup>
import { useToast } from "@/composables/useToast"
import { DEFAULT_CURRENCY, DEFAULT_LOCALE, formatCurrency as formatCurrencyUtil } from "@/utils/currency"
import { getInvoiceStatusColor, getSalesOrderStatusColor } from "@/utils/invoice"
import { Button, Dialog, Input, createResource } from "frappe-ui"
import { computed, ref, watch } from "vue"
import ReturnInvoiceDialog from "./ReturnInvoiceDialog.vue"

const { showError } = useToast()

const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
	posOpeningShift: String,
	company: String,
	currency: {
		type: String,
		default: DEFAULT_CURRENCY,
	},
})

function formatCurrency(amount) {
	return formatCurrencyUtil(Number.parseFloat(amount || 0), props.currency)
}

const emit = defineEmits([
	"update:modelValue",
	"view-invoice",
	"print-invoice",
	"return-created",
	"view-order",
	"print-order",
])

const show = ref(props.modelValue)
const activeTab = ref("invoices")
const searchTerm = ref("")
const pageSize = 20

// Return dialog state (invoices only)
const showReturnDialog = ref(false)
const selectedInvoiceForReturn = ref(null)

// ============================================================================
// Invoices tab state
// ============================================================================
const invoices = ref([])
const invoicePage = ref(0)
const invoiceHasMore = ref(true)
const isLoadingMoreInvoices = ref(false)

const invoicesResource = createResource({
	url: "frappe.client.get_list",
	makeParams() {
		return {
			doctype: "Sales Invoice",
			filters: {
				is_pos: 1,
				...(props.posProfile && { pos_profile: props.posProfile }),
			},
			fields: [
				"name",
				"customer",
				"customer_name",
				"customer.mobile_no as customer_mobile",
				"posting_date",
				"posting_time",
				"grand_total",
				"status",
				"docstatus",
				"is_return",
			],
			order_by: "`tabSales Invoice`.modified desc",
			start: invoicePage.value * pageSize,
			page_length: pageSize,
		}
	},
	auto: false,
	onSuccess(data) {
		if (data && Array.isArray(data)) {
			const newInvoices = data.map((inv) => ({ ...inv, items_count: 0 }))
			invoices.value = isLoadingMoreInvoices.value ? [...invoices.value, ...newInvoices] : newInvoices
			invoiceHasMore.value = data.length === pageSize
			isLoadingMoreInvoices.value = false
		}
	},
	onError(error) {
		console.error("Error loading invoices:", error)
		showError(__("Failed to load invoices"))
		isLoadingMoreInvoices.value = false
	},
})

// ============================================================================
// Orders tab state
// ============================================================================
const orders = ref([])
const orderPage = ref(0)
const orderHasMore = ref(true)
const isLoadingMoreOrders = ref(false)

const ordersResource = createResource({
	url: "frappe.client.get_list",
	makeParams() {
		return {
			doctype: "Sales Order",
			filters: {
				...(props.company && { company: props.company }),
			},
			fields: [
				"name",
				"customer",
				"customer_name",
				"customer.mobile_no as customer_mobile",
				"transaction_date",
				"grand_total",
				"status",
				"docstatus",
			],
			order_by: "`tabSales Order`.modified desc",
			start: orderPage.value * pageSize,
			page_length: pageSize,
		}
	},
	auto: false,
	onSuccess(data) {
		if (data && Array.isArray(data)) {
			const newOrders = data.map((order) => ({ ...order, doctype: "Sales Order" }))
			orders.value = isLoadingMoreOrders.value ? [...orders.value, ...newOrders] : newOrders
			orderHasMore.value = data.length === pageSize
			isLoadingMoreOrders.value = false
		}
	},
	onError(error) {
		console.error("Error loading orders:", error)
		showError(__("Failed to load orders"))
		isLoadingMoreOrders.value = false
	},
})

// ============================================================================
// Active-tab helpers
// ============================================================================
const activeResource = computed(() => (activeTab.value === "invoices" ? invoicesResource : ordersResource))
const activeHasMore = computed(() => (activeTab.value === "invoices" ? invoiceHasMore.value : orderHasMore.value))

const filteredInvoices = computed(() => {
	if (!searchTerm.value) return invoices.value
	const term = searchTerm.value.toLowerCase()
	return invoices.value.filter(
		(inv) => inv.name.toLowerCase().includes(term) || inv.customer_name?.toLowerCase().includes(term),
	)
})

const filteredOrders = computed(() => {
	if (!searchTerm.value) return orders.value
	const term = searchTerm.value.toLowerCase()
	return orders.value.filter(
		(order) => order.name.toLowerCase().includes(term) || order.customer_name?.toLowerCase().includes(term),
	)
})

const activeList = computed(() => (activeTab.value === "invoices" ? filteredInvoices.value : filteredOrders.value))

function loadInvoices() {
	invoicePage.value = 0
	isLoadingMoreInvoices.value = false
	invoicesResource.reload()
}

function loadOrders() {
	orderPage.value = 0
	isLoadingMoreOrders.value = false
	ordersResource.reload()
}

function reloadActiveTab() {
	if (activeTab.value === "invoices") loadInvoices()
	else loadOrders()
}

function loadMore() {
	if (activeTab.value === "invoices") {
		invoicePage.value++
		isLoadingMoreInvoices.value = true
		invoicesResource.reload()
	} else {
		orderPage.value++
		isLoadingMoreOrders.value = true
		ordersResource.reload()
	}
}

watch(
	() => props.modelValue,
	(val) => {
		show.value = val
		if (val) reloadActiveTab()
	},
)

watch(show, (val) => {
	emit("update:modelValue", val)
})

watch(activeTab, () => {
	searchTerm.value = ""
	reloadActiveTab()
})

// Clear selected invoice when return dialog closes
watch(showReturnDialog, (val) => {
	if (!val) selectedInvoiceForReturn.value = null
})

function viewInvoice(invoice) {
	emit("view-invoice", invoice)
}

function printInvoice(invoice) {
	emit("print-invoice", invoice)
}

function viewOrder(order) {
	emit("view-order", order)
}

function printOrder(order) {
	emit("print-order", order)
}

function canCreateReturn(invoice) {
	return invoice.docstatus === 1 && !invoice.is_return && invoice.status !== "Credit Note Issued"
}

function openReturnModal(invoice) {
	selectedInvoiceForReturn.value = invoice
	showReturnDialog.value = true
}

function handleReturnCreated(returnInvoice) {
	loadInvoices()
	emit("return-created", returnInvoice)
}

function formatDateTime(date, time) {
	const dateStr = new Date(date).toLocaleDateString(DEFAULT_LOCALE, { month: "short", day: "numeric", year: "numeric" })
	return time ? `${dateStr} ${time}` : dateStr
}

function formatDate(date) {
	return new Date(date).toLocaleDateString(DEFAULT_LOCALE, { month: "short", day: "numeric", year: "numeric" })
}
</script>
