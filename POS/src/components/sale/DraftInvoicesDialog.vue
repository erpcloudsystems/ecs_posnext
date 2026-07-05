<template>
	<!-- Main Dialog -->
	<Dialog
		v-model="show"
		:options="{ title: __('Draft Invoices'), size: 'lg' }"
	>
		<template #body-content>
			<div class="flex flex-col gap-3">
				<!-- Empty State -->
				<div v-if="drafts.length === 0" class="text-center py-8">
					<div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
						<svg class="h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
						</svg>
					</div>
					<p class="text-sm font-medium text-gray-900">{{ __('No draft invoices') }}</p>
					<p class="text-xs text-gray-500 mt-1">{{ __('Save invoices as drafts to continue later') }}</p>
				</div>

				<!-- Drafts List -->
				<div v-else class="flex flex-col gap-2 max-h-96 overflow-y-auto">
					<div
						v-for="draft in drafts"
						:key="draft.draft_id"
						class="bg-white border border-gray-200 rounded-lg p-3 hover:border-blue-400 transition-all cursor-pointer"
						@click="$emit('load-draft', draft)"
					>
						<div class="flex items-start justify-between mb-2">
							<div class="flex-1">
								<h4 class="text-sm font-semibold text-gray-900">
									{{ draft.draft_id }}
								</h4>
								<p v-if="draft.customer" class="text-xs text-gray-500 mt-0.5">
									{{ __('Customer: {0}', [(draft.customer?.customer_name || draft.customer?.name || draft.customer)]) }}
								</p>
								<p class="text-xs text-gray-400 mt-0.5">
									{{ formatDateTime(draft.created_at) }}
								</p>
								<p v-if="getTableDisplay(draft)" class="text-xs text-green-600 font-medium mt-0.5">
									{{ __('Table: {0}', [getTableDisplay(draft)]) }}
								</p>
							</div>
							<button
								@click.stop="handlePrintDraft(draft)"
								class="text-gray-400 hover:text-blue-600 transition-colors p-1"
								:title="__('Print draft')"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
								</svg>
							</button>
						</div>

						<!-- Items Preview -->
						<div class="flex items-center justify-between text-xs">
							<span class="text-gray-600">
								{{ __('{0} item(s)', [draft.items?.length || 0]) }}
							</span>
							<span class="font-bold text-blue-600">
								{{ formatCurrency(calculateTotal(draft.items)) }}
							</span>
						</div>

						<!-- Items List (condensed) -->
						<div v-if="draft.items && draft.items.length > 0" class="mt-2 pt-2 border-t border-gray-100">
							<div class="flex flex-wrap gap-1">
								<span
									v-for="(item, idx) in draft.items.slice(0, 3)"
									:key="idx"
									class="text-[10px] bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded"
								>
									{{ item.item_name }} ({{ item.quantity || item.qty }})
								</span>
								<span
									v-if="draft.items.length > 3"
									class="text-[10px] text-gray-500 px-1.5 py-0.5"
								>
									{{ __('+{0} more', [draft.items.length - 3]) }}
								</span>
							</div>
						</div>
					</div>
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end items-center w-full">
				<Button variant="subtle" @click="show = false">
					{{ __('Close') }}
				</Button>
			</div>
		</template>
	</Dialog>


</template>

<script setup>
import {
	DEFAULT_CURRENCY,
	DEFAULT_LOCALE,
	formatCurrency as formatCurrencyUtil,
	roundCurrency,
} from "@/utils/currency"
import { call } from "@/utils/apiWrapper"
import { printInvoiceCustom } from "@/utils/printInvoice"
import { useToast } from "@/composables/useToast"
import { usePOSShiftStore } from "@/stores/posShift"
import { Button, Dialog } from "frappe-ui"
import { onMounted, onUnmounted, ref, watch } from "vue"

const { showSuccess, showError } = useToast()
const shiftStore = usePOSShiftStore()

const props = defineProps({
	modelValue: Boolean,
	currency: {
		type: String,
		default: DEFAULT_CURRENCY,
	},
})

const emit = defineEmits(["update:modelValue", "load-draft", "drafts-updated"])

const show = ref(props.modelValue)
const drafts = ref([])

watch(
	() => props.modelValue,
	(val) => {
		show.value = val
		if (val) {
			loadDrafts()
		}
	},
)

watch(show, (val) => {
	emit("update:modelValue", val)
	if (!val) {
		// Dialog closed: drop the cached drafts so a stale or already-submitted
		// draft can't be rendered or re-loaded before the next fresh loadDrafts().
		drafts.value = []
	}
})

onMounted(() => {
	loadDrafts()
})

onUnmounted(() => {
	// Component destroyed: clear the cached drafts.
	drafts.value = []
})

async function loadDrafts() {
	try {
		const openingShift = shiftStore.currentShift?.name
		if (!openingShift) {
			drafts.value = []
			return
		}
		const result = await call("ecs_posnext.api.invoices.get_draft_invoices", {
			pos_opening_shift: openingShift,
		})
		// Map server invoice format to dialog expected format
		drafts.value = (result || []).map((inv) => ({
			draft_id: inv.name,
			customer: inv.customer_name || inv.customer,
			created_at: inv.creation,
			order_type: inv.custom_so_type || "",
			items: (inv.items || []).map((item) => ({
				item_code: item.item_code,
				item_name: item.item_name,
				quantity: item.qty,
				qty: item.qty,
				rate: item.rate,
				amount: item.amount,
			})),
			table_numbers: inv.custom_table_number
				? inv.custom_table_number.split(",").map((t) => t.trim()).filter(Boolean)
				: [],
			server_draft_name: inv.name,
		}))
	} catch (error) {
		console.error("Error loading drafts:", error)
		showError(__("Failed to load draft invoices"))
	}
}

function handlePrintDraft(draft) {
	try {
		const invoiceData = {
			name: draft.draft_id,
			company: shiftStore.profileCompany,
			items: draft.items,
			payments: [],
			grand_total: calculateTotal(draft.items),
			posting_date: draft.created_at,
			customer_name:
				draft.customer?.customer_name || draft.customer?.name || draft.customer,
			status: "Draft",
		}
		printInvoiceCustom(invoiceData)
	} catch (error) {
		console.error("Error printing draft:", error)
		showError(__("Failed to print draft"))
	}
}



function formatDateTime(dateStr) {
	const date = new Date(dateStr)
	return date.toLocaleString(DEFAULT_LOCALE, {
		month: "short",
		day: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	})
}

function formatCurrency(amount) {
	return formatCurrencyUtil(Number.parseFloat(amount || 0), props.currency)
}

function calculateTotal(items) {
	if (!items || items.length === 0) return 0
	return roundCurrency(
		items.reduce((sum, item) => {
			const qty = item.quantity || item.qty || 1
			const rate = item.rate || 0
			return sum + roundCurrency(qty * roundCurrency(rate))
		}, 0),
	)
}

function getTableDisplay(draft) {
	if (draft.table_numbers && draft.table_numbers.length > 0) {
		return draft.table_numbers.join(", ")
	}
	if (draft.table_number) {
		return draft.table_number
	}
	return ""
}
</script>
