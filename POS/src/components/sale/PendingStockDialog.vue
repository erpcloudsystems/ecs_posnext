<template>
	<Dialog v-model="show" :options="{ title: __('Pending Stock (Backorders)'), size: '5xl' }">
		<template #body-content>
			<div class="flex items-center justify-between mb-3">
				<p class="text-xs text-gray-500">
					{{ __("Sales held as drafts because submitting them failed. Fix the reason shown, then Finalize. The shift can't be closed while any remain.") }}
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
							</div>
						</div>

						<div class="mb-2 rounded-lg border border-red-200 bg-red-50 px-2 py-1.5">
							<p class="text-[11px] font-semibold text-red-700 uppercase">{{ __("Reason") }}</p>
							<p class="text-xs text-red-800 whitespace-pre-line break-words">{{ inv.reason || __("No reason recorded") }}</p>
						</div>

						<div class="grid grid-cols-1 lg:grid-cols-2 gap-1 mb-2">
							<div
								v-for="(it, i) in inv.items"
								:key="i"
								class="flex items-center justify-between text-xs rounded px-2 py-1 bg-gray-50"
							>
								<span class="truncate">{{ it.item_name || it.item_code }}</span>
								<span class="flex-shrink-0 ms-2 text-gray-500">× {{ fmtQty(it.qty) }}</span>
							</div>
						</div>

						<div class="flex justify-end">
							<button
								type="button"
								class="h-9 px-4 text-xs font-semibold rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
								:disabled="inv._busy"
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
	} catch (e) {
		console.error("Load pending stock failed", e)
		showError(parseError(e).message || __("Failed to load pending stock"))
		invoices.value = []
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
		inv._busy = false
		await load()
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
