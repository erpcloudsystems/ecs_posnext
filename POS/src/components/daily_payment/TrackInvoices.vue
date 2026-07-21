<template>
	<Transition name="fade">
		<div
			v-if="show"
			class="fixed inset-0 bg-black bg-opacity-50 z-[300]"
			@click.self="handleClose"
		>
			<div class="fixed inset-0 flex items-center justify-center p-4">
				<div class="w-full max-w-lg bg-white rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">

					<!-- Header -->
					<div class="flex items-center justify-between px-6 py-5 border-b bg-gradient-to-r from-blue-50 to-indigo-50 flex-shrink-0">
						<div class="flex items-center gap-3">
							<div class="p-2 bg-blue-100 rounded-lg">
								<svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
								</svg>
							</div>
							<div>
								<h2 class="text-xl font-bold text-gray-900">{{ __('Track Invoices') }}</h2>
								<p v-if="branch" class="text-sm text-gray-600 mt-0.5">{{ __('Branch: {0}', [branch]) }}</p>
							</div>
						</div>
						<button @click="handleClose" class="p-2 hover:bg-white/50 rounded-lg transition-colors">
							<svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
							</svg>
						</button>
					</div>

					<!-- Filter Bar -->
					<div class="px-6 py-4 border-b bg-white flex flex-wrap items-end gap-3 flex-shrink-0">
						<!-- From Date -->
						<div class="min-w-[145px]">
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('From Date') }}</label>
							<input
								v-model="fromDate"
								type="date"
								:min="props.posOpeningShiftDate"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
							/>
						</div>

						<!-- To Date -->
						<div class="min-w-[145px]">
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('To Date') }}</label>
							<input
								v-model="toDate"
								type="date"
								:min="props.posOpeningShiftDate"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
							/>
						</div>

						<!-- Search Button -->
						<button
							@click="loadCounts"
							:disabled="loading"
							class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-semibold disabled:opacity-60"
						>
							<svg
								class="w-4 h-4"
								:class="{ 'animate-spin': loading }"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path v-if="loading" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
								<path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
							</svg>
							{{ loading ? __('Loading...') : __('Search') }}
						</button>

					</div>

					<!-- Content -->
					<div class="flex-1 overflow-y-auto p-6 bg-gray-50">

						<!-- Loading -->
						<div v-if="loading" class="flex flex-col items-center justify-center py-12">
							<div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mb-3"></div>
							<p class="text-sm font-medium text-gray-600">{{ __('Loading invoice counts...') }}</p>
						</div>

						<!-- Stats Cards -->
						<div v-else class="flex flex-col gap-4">

							<!-- Cash -->
							<div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex items-center gap-5">
								<div class="p-3 bg-green-100 rounded-xl flex-shrink-0">
									<svg class="w-7 h-7 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/>
									</svg>
								</div>
								<div class="flex-1">
									<div class="text-sm font-medium text-gray-500">{{ __('Cash Invoices') }}</div>
									<div class="text-4xl font-black text-green-700 mt-0.5">{{ counts.cash }}</div>
								</div>
								<div class="text-xs text-gray-400 font-medium">
									{{ counts.total > 0 ? Math.round(counts.cash / counts.total * 100) : 0 }}%
								</div>
							</div>

							<!-- Visa -->
							<div class="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex items-center gap-5">
								<div class="p-3 bg-purple-100 rounded-xl flex-shrink-0">
									<svg class="w-7 h-7 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
									</svg>
								</div>
								<div class="flex-1">
									<div class="text-sm font-medium text-gray-500">{{ __('Visa Invoices') }}</div>
									<div class="text-4xl font-black text-purple-700 mt-0.5">{{ counts.visa }}</div>
								</div>
								<div class="text-xs text-gray-400 font-medium">
									{{ counts.total > 0 ? Math.round(counts.visa / counts.total * 100) : 0 }}%
								</div>
							</div>

							<!-- Total -->
							<div class="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl shadow-sm p-5 flex items-center gap-5">
								<div class="p-3 bg-white/20 rounded-xl flex-shrink-0">
									<svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
									</svg>
								</div>
								<div class="flex-1">
									<div class="text-sm font-medium text-white/80">{{ __('Total Invoices') }}</div>
									<div class="text-4xl font-black text-white mt-0.5">{{ counts.total }}</div>
								</div>
							</div>

							<!-- Footer note -->
							<p v-if="lastLoaded" class="text-center text-xs text-gray-400 mt-1">
								{{ __('Last updated: {0}', [lastLoaded]) }}
							</p>
						</div>
					</div>

				</div>
			</div>
		</div>
	</Transition>
</template>

<script setup>
import { call } from "frappe-ui"
import { ref, watch } from "vue"
import { useToast } from "@/composables/useToast"
import { logger } from "@/utils/logger"

const log = logger.create("TrackInvoices")
const { showError } = useToast()

const props = defineProps({
	modelValue: Boolean,
	branch: {
		type: String,
		default: null,
	},
	posOpeningShift: {
		type: String,
		default: null,
	},
	posOpeningShiftDate: {
		type: String,
		default: null,
	},
})

const emit = defineEmits(["update:modelValue"])

const show = ref(props.modelValue)
const loading = ref(false)
const lastLoaded = ref("")

const today = new Date().toISOString().split("T")[0]
const fromDate = ref(props.posOpeningShiftDate || today)
const toDate = ref(props.posOpeningShiftDate || today)

const counts = ref({ cash: 0, visa: 0, total: 0 })

watch(
	() => props.modelValue,
	(val) => {
		show.value = val
		if (val) {
			fromDate.value = props.posOpeningShiftDate || today
			toDate.value = props.posOpeningShiftDate || today
			loadCounts()
		}
	},
)

watch(show, (val) => {
	emit("update:modelValue", val)
})

function handleClose() {
	show.value = false
}

async function loadCounts() {
	loading.value = true
	try {
		const result = await call("ecs_posnext.api.daily_payment.get_invoice_counts", {
			branch: props.branch || null,
			from_date: fromDate.value || null,
			to_date: toDate.value || null,
		})
		counts.value = result || { cash: 0, visa: 0, total: 0 }
		const now = new Date()
		lastLoaded.value = now.toLocaleTimeString()
	} catch (error) {
		log.error("Error loading invoice counts:", error)
		showError(error.message || __("Failed to load invoice counts"))
	} finally {
		loading.value = false
	}
}
</script>
