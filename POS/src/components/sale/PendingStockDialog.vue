<template>
	<Dialog v-model="show" :options="{ title: __('Pending Stock (Backorders)'), size: '5xl' }">
		<template #body-content>
			<div class="flex items-center justify-between mb-3">
				<p class="text-xs text-gray-500">
					{{ __("Sales held as drafts because stock was insufficient. Restock, then Finalize. The shift can't be closed while any remain.") }}
				</p>
				<button
					type="button"
					class="text-xs font-medium text-blue-600 hover:text-blue-800"
					:disabled="loading"
					@click="load"
				>
					{{ loading ? __("Loading...") : __("Refresh") }}
				</button>
			</div>

			<div v-if="loading" class="py-10 text-center text-sm text-gray-500">{{ __("Loading...") }}</div>
			<div v-else-if="invoices.length === 0" class="py-10 text-center text-sm text-gray-500">
				{{ __("No pending-stock invoices 🎉") }}
			</div>

			<template v-else>
				<!-- Aggregated items needing stock -->
				<div v-if="itemsNeeded.length" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
					<h4 class="text-xs font-semibold text-amber-700 uppercase mb-2">{{ __("Items needing stock") }}</h4>
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-1.5">
						<div v-for="n in itemsNeeded" :key="n.item_code + n.warehouse" class="flex items-center justify-between text-xs bg-white rounded px-2 py-1 border border-amber-100">
							<span class="truncate">{{ n.item_name || n.item_code }} <span class="text-gray-400">· {{ n.warehouse }}</span></span>
							<span class="font-semibold text-red-600 flex-shrink-0 ms-2">{{ __("short {0}", [fmtQty(n.shortage)]) }}</span>
						</div>
					</div>
				</div>

				<!-- Pending invoices -->
				<div class="space-y-3 max-h-[55vh] overflow-y-auto">
					<div v-for="inv in invoices" :key="inv.name" class="border border-gray-200 rounded-xl p-3">
						<div class="flex items-center justify-between mb-2">
							<div class="min-w-0">
								<h3 class="text-sm font-bold text-gray-800 truncate">{{ inv.name }}</h3>
								<p class="text-xs text-gray-500 truncate">{{ inv.customer_name || inv.customer }} · {{ inv.posting_date }}</p>
							</div>
							<div class="flex items-center gap-2 flex-shrink-0">
								<span class="text-sm font-bold text-blue-700">{{ formatCurrency(inv.grand_total, inv.currency) }}</span>
								<span
									class="text-[11px] font-semibold px-2 py-0.5 rounded-full"
									:class="inv.ready ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'"
								>
									{{ inv.ready ? __("Ready") : __("Waiting stock") }}
								</span>
							</div>
						</div>

						<div class="grid grid-cols-1 lg:grid-cols-2 gap-1 mb-2">
							<div
								v-for="(it, i) in inv.items"
								:key="i"
								class="flex items-center justify-between text-xs rounded px-2 py-1"
								:class="it.short ? 'bg-red-50' : 'bg-gray-50'"
							>
								<span class="truncate">{{ it.item_name || it.item_code }}</span>
								<span class="flex-shrink-0 ms-2" :class="it.short ? 'text-red-600 font-semibold' : 'text-gray-500'">
									{{ __("need {0} / have {1}", [fmtQty(it.required), fmtQty(it.available)]) }}
								</span>
							</div>
						</div>

						<div class="flex justify-end">
							<button
								type="button"
								class="h-9 px-4 text-xs font-semibold rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
								:disabled="!inv.ready || inv._busy"
								@click="finalize(inv)"
							>
								{{ inv._busy ? __("Finalizing...") : __("Finalize (Submit)") }}
							</button>
						</div>
					</div>
				</div>
			</template>
		</template>
		<template #actions>
			<div class="flex justify-end w-full">
				<Button variant="subtle" @click="show = false">{{ __("Close") }}</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Button, Dialog } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { parseError } from "@/utils/errorHandler"
import { formatCurrency } from "@/utils/currency"

const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
	posOpeningShift: String,
})

const emit = defineEmits(["update:modelValue", "finalized"])

const { showSuccess, showError } = useToast()

const invoices = ref([])
const itemsNeeded = ref([])
const loading = ref(false)

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

function fmtQty(v) {
	return Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })
}

async function load() {
	loading.value = true
	try {
		const res = await call(
			"ecs_posnext.api.pending_stock.get_pending_stock_invoices",
			{
				pos_profile: props.posProfile,
				pos_opening_shift: props.posOpeningShift || undefined,
			},
		)
		const data = res?.message || res || {}
		invoices.value = (data.invoices || []).map((i) => ({ ...i, _busy: false }))
		itemsNeeded.value = data.items_needed || []
	} catch (e) {
		console.error("Load pending stock failed", e)
		showError(parseError(e).message || __("Failed to load pending stock"))
		invoices.value = []
		itemsNeeded.value = []
	} finally {
		loading.value = false
	}
}

async function finalize(inv) {
	if (inv._busy) return
	inv._busy = true
	try {
		await call("ecs_posnext.api.pending_stock.finalize_pending_invoice", {
			invoice_name: inv.name,
		})
		showSuccess(__("Invoice {0} finalized", [inv.name]))
		await load()
		emit("finalized")
	} catch (e) {
		console.error("Finalize failed", e)
		showError(parseError(e).message || __("Finalize failed"))
	} finally {
		inv._busy = false
	}
}

watch(
	() => props.modelValue,
	(open) => {
		if (open) load()
	},
)
</script>
