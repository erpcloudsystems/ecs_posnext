<template>
	<!-- Full Page Overlay -->
	<Transition name="fade">
		<div
			v-if="show"
			class="fixed inset-0 bg-black bg-opacity-50 z-[300]"
			@click.self="handleClose"
		>
			<!-- Main Container -->
			<div class="fixed inset-0 flex items-center justify-center p-4">
				<div class="w-full h-full max-w-[95vw] max-h-[95vh] bg-white rounded-lg shadow-2xl overflow-hidden flex flex-col">

					<!-- Header -->
					<div class="flex items-center justify-between px-6 py-5 border-b bg-gradient-to-r from-emerald-50 to-teal-50">
						<div class="flex items-center gap-3">
							<div class="p-2 bg-emerald-100 rounded-lg">
								<svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/>
								</svg>
							</div>
							<div>
								<div class="flex flex-wrap items-center gap-2">
									<h2 class="text-xl font-bold text-gray-900">{{ __('Daily Payment') }}</h2>
									<div v-if="branch" class="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg border text-xs font-semibold"
										:class="loadingBranchBalance ? 'bg-white/70 border-gray-200 text-gray-600' : 'bg-white/80 border-emerald-200 text-emerald-800'">
										<svg v-if="loadingBranchBalance" class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
										</svg>
										<span>{{ __('Balance') }}:</span>
										<span>{{ branchBalanceDisplay }}</span>
									</div>
								</div>
								<p class="text-sm text-gray-600 mt-0.5">
									{{ branch ? __('Branch: {0}', [branch]) : __('Manage daily payment records') }}
								</p>
							</div>
						</div>
						<div class="flex items-center gap-2">
							<!-- Create New Button -->
							<button
								@click="openCreateForm"
								style="background-color:#16a34a" class="flex items-center gap-2 px-4 py-2 text-white rounded-lg transition-colors text-sm font-semibold shadow-sm hover:opacity-90"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
								</svg>
								{{ __('New Daily Payment') }}
							</button>
							<!-- Refresh Button -->
							<button
								@click="loadRecords"
								:disabled="loading"
								class="flex items-center gap-2 px-3 py-2 text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
							>
								<svg
									class="w-4 h-4"
									:class="{ 'animate-spin': loading }"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
								</svg>
								{{ __('Refresh') }}
							</button>
							<!-- Close Button -->
							<button
								@click="handleClose"
								class="p-2 hover:bg-white/50 rounded-lg transition-colors"
							>
								<svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
								</svg>
							</button>
						</div>
					</div>

					<!-- Search / Filter Bar -->
					<div class="px-6 py-4 bg-white border-b border-gray-200 flex flex-wrap items-end gap-3">
						<!-- General Search -->
						<div class="flex-1 min-w-[220px]">
							<div class="relative">
								<div class="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
									<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
									</svg>
								</div>
								<input
									v-model="searchEmployee"
									type="text"
									:placeholder="__('Search by ID, employee name...')"
									class="w-full ps-9 pe-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
									@input="onFilterChange"
								/>
							</div>
						</div>

						<!-- From Date -->
						<div class="min-w-[150px]">
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('From Date') }}</label>
							<input
								v-model="fromDate"
								type="date"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
								@change="onFilterChange"
							/>
						</div>

						<!-- To Date -->
						<div class="min-w-[150px]">
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('To Date') }}</label>
							<input
								v-model="toDate"
								type="date"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
								@change="onFilterChange"
							/>
						</div>

						<!-- Search Button -->
						<button
							@click="loadRecords"
							class="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-semibold"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
							</svg>
							{{ __('Search') }}
						</button>

						<!-- Clear Filters -->
						<button
							v-if="searchEmployee || fromDate || toDate"
							@click="clearFilters"
							class="flex items-center gap-1 px-3 py-2 text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
							</svg>
							{{ __('Clear') }}
						</button>
					</div>

					<!-- Content Area -->
					<div class="flex-1 overflow-y-auto bg-gray-50 p-6">

						<!-- Loading State -->
						<div v-if="loading" class="flex flex-col items-center justify-center py-16">
							<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mb-4"></div>
							<p class="text-sm font-medium text-gray-600">{{ __('Loading daily payments...') }}</p>
						</div>

						<!-- Empty State -->
						<div v-else-if="records.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
							<div class="p-4 bg-emerald-50 rounded-full mb-4">
								<svg class="w-12 h-12 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/>
								</svg>
							</div>
							<p class="text-gray-600 font-medium text-lg">{{ __('No daily payments found') }}</p>
							<p class="text-gray-500 text-sm mt-1">
								{{ searchEmployee || fromDate || toDate
									? __('Try adjusting your search filters')
									: __('Create a new daily payment to get started') }}
							</p>
							<button
								@click="openCreateForm"
								class="mt-4 flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-semibold"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
								</svg>
								{{ __('New Daily Payment') }}
							</button>
						</div>

						<!-- Records Grid -->
						<div v-else class="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
							<div
								v-for="record in records"
								:key="record.name"
								class="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all overflow-hidden"
							>
								<!-- Card Header -->
								<div class="bg-gradient-to-r from-emerald-50 to-teal-50 px-5 py-4 border-b border-gray-200">
									<div class="flex items-start justify-between">
										<div class="flex-1">
											<h3 class="text-base font-bold text-gray-900">{{ record.name }}</h3>
											<div class="flex items-center gap-2 mt-1">
												<span
													:class="[
														'text-xs px-2.5 py-0.5 rounded-full font-semibold',
														getDocStatusClass(record.docstatus)
													]"
												>
													{{ getDocStatusLabel(record.docstatus) }}
												</span>
											</div>
										</div>
										<div class="text-end ms-3">
											<div class="text-xs text-gray-500 mb-1">{{ __('Date') }}</div>
											<div class="text-sm font-bold text-emerald-700">{{ formatDate(record.date) }}</div>
										</div>
									</div>
								</div>

								<!-- Card Body -->
								<div class="px-5 py-4 flex flex-col gap-3">

									<!-- Employee -->
									<div v-if="record.employee" class="flex items-start">
										<svg class="w-4 h-4 text-gray-400 me-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
										</svg>
										<div class="flex-1 min-w-0">
											<div class="text-xs text-gray-500">{{ __('Employee') }}</div>
											<div class="text-sm font-semibold text-gray-900 truncate">
												{{ record.employee_name || record.employee }}
											</div>
										</div>
									</div>

									<!-- Branch -->
									<div v-if="record.branch" class="flex items-start">
										<svg class="w-4 h-4 text-gray-400 me-2 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
										</svg>
										<div class="flex-1 min-w-0">
											<div class="text-xs text-gray-500">{{ __('Branch') }}</div>
											<div class="text-sm font-semibold text-gray-900 truncate">{{ record.branch }}</div>
										</div>
									</div>

									<!-- Amount & Mode of Payment -->
									<div class="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100">
										<div v-if="getRecordAmount(record)">
											<div class="text-xs text-gray-500 mb-0.5">{{ __('Amount') }}</div>
											<div class="text-sm font-bold text-emerald-700">{{ formatAmount(getRecordAmount(record)) }}</div>
										</div>
										<div v-if="record.mode_of_payment">
											<div class="text-xs text-gray-500 mb-0.5">{{ __('Mode of Payment') }}</div>
											<div class="text-sm font-semibold text-gray-800 truncate">{{ record.mode_of_payment }}</div>
										</div>
									</div>

									<!-- Type badges -->
									<div class="flex items-center gap-2 pt-1">
										<span v-if="record.payment_to_employees" class="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-medium">
											{{ __('Employee Payment') }}
										</span>
										<span v-if="record.expenses" class="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full font-medium">
											{{ __('Expenses') }}
										</span>
										<span v-if="record.deduction" class="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full font-medium">
											{{ __('Deduction') }}
										</span>
									</div>
								</div>

								<!-- Card Footer -->
								<div class="px-5 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-end gap-2">
									<button
										@click="openRecord(record.name)"
										class="px-3 py-1.5 text-xs font-semibold text-emerald-600 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-colors flex items-center gap-1"
										:title="__('Open Record')"
									>
										<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
										</svg>
										{{ __('Open') }}
									</button>
								</div>
							</div>
						</div>

						<!-- Results count -->
						<div v-if="!loading && records.length > 0" class="mt-4 text-center text-xs text-gray-500">
							{{ __('Showing {0} record(s)', [records.length]) }}
						</div>
					</div>
				</div>
			</div>
		</div>
	</Transition>

	<!-- Create / New Daily Payment Form -->
	<DailyPaymentForm
		v-model="showCreateForm"
		:branch="branch"
		:payment-methods="paymentMethods"
		:pos-opening-shift="posOpeningShift"
		@saved="onRecordSaved"
	/>
</template>

<script setup>
import { call } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { useFormatters } from "@/composables/useFormatters"
import { useToast } from "@/composables/useToast"
import { logger } from "@/utils/logger"
import DailyPaymentForm from "@/components/daily_payment/DailyPaymentForm.vue"

const log = logger.create("DailyPaymentManagement")
const { showError } = useToast()
const { formatDate } = useFormatters()

const props = defineProps({
	modelValue: Boolean,
	branch: {
		type: String,
		default: null,
	},
	paymentMethods: {
		type: Array,
		default: () => [],
	},
	posOpeningShift: {
		type: String,
		default: null,
	},
})

const emit = defineEmits(["update:modelValue"])

const show = ref(props.modelValue)
const loading = ref(false)
const records = ref([])
const showCreateForm = ref(false)
const loadingBranchBalance = ref(false)
const branchBalance = ref({
	branch: null,
	account: null,
	balance: 0,
	currency: null,
})

const searchEmployee = ref("")
const today = new Date().toISOString().split("T")[0]
const fromDate = ref(today)
const toDate = ref(today)

let debounceTimer = null

const branchBalanceDisplay = computed(() => {
	if (loadingBranchBalance.value) {
		return __("Loading...")
	}
	return new Intl.NumberFormat(undefined, {
		style: "currency",
		currency: branchBalance.value.currency || "USD",
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	}).format(Number(branchBalance.value.balance || 0))
})

watch(
	() => props.modelValue,
	(val) => {
		show.value = val
		if (val) {
			loadBranchBalance()
			loadRecords()
		}
	},
)

watch(
	() => props.branch,
	() => {
		if (show.value) {
			loadBranchBalance()
		}
	},
)

watch(show, (val) => {
	emit("update:modelValue", val)
})

function handleClose() {
	show.value = false
}

function onFilterChange() {
	clearTimeout(debounceTimer)
	debounceTimer = setTimeout(() => {
		loadRecords()
	}, 500)
}

function clearFilters() {
	searchEmployee.value = ""
	fromDate.value = ""
	toDate.value = ""
	loadRecords()
}

async function loadBranchBalance() {
	if (!props.branch) {
		branchBalance.value = {
			branch: null,
			account: null,
			balance: 0,
			currency: null,
		}
		return
	}

	loadingBranchBalance.value = true
	try {
		const result = await call("ecs_posnext.api.daily_payment.get_branch_balance", {
			branch: props.branch,
		})
		branchBalance.value = result || {
			branch: props.branch,
			account: null,
			balance: 0,
			currency: null,
		}
	} catch (error) {
		log.error("Error loading branch balance:", error)
		branchBalance.value = {
			branch: props.branch,
			account: null,
			balance: 0,
			currency: null,
		}
	} finally {
		loadingBranchBalance.value = false
	}
}

async function loadRecords() {
	loading.value = true
	try {
		const result = await call("ecs_posnext.api.daily_payment.get_daily_payments", {
			employee: searchEmployee.value || null,
			from_date: fromDate.value || null,
			to_date: toDate.value || null,
			branch: props.branch || null,
			limit: 100,
		})
		records.value = result || []
	} catch (error) {
		log.error("Error loading daily payments:", error)
		showError(error.message || __("Failed to load daily payments"))
		records.value = []
	} finally {
		loading.value = false
	}
}

function openRecord(name) {
	const url = `/app/daily-payment/${name}`
	window.open(url, "_blank")
}

function openCreateForm() {
	showCreateForm.value = true
}

function onRecordSaved() {
	loadRecords()
}

function getDocStatusClass(docstatus) {
	switch (docstatus) {
		case 0:
			return "bg-yellow-100 text-yellow-800"
		case 1:
			return "bg-green-100 text-green-800"
		case 2:
			return "bg-red-100 text-red-800"
		default:
			return "bg-gray-100 text-gray-700"
	}
}

function getDocStatusLabel(docstatus) {
	switch (docstatus) {
		case 0:
			return __("Draft")
		case 1:
			return __("Submitted")
		case 2:
			return __("Cancelled")
		default:
			return __("Unknown")
	}
}

function getRecordAmount(record) {
	return record.expenses ? record.expenses_amount : record.amount
}

function formatAmount(amount) {
	if (!amount) return "—"
	return new Intl.NumberFormat(undefined, {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	}).format(amount)
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
