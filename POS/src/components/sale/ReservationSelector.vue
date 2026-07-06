<template>
	<div class="bg-white border border-gray-200 rounded-xl p-2 shadow-sm">
		<div class="flex items-center gap-2">
			<!-- Visit date -->
			<div class="flex flex-col">
				<label class="text-[9px] font-medium text-gray-500 leading-none mb-0.5">{{ __("Visit Date") }}</label>
				<input
					type="date"
					v-model="visitDate"
					class="text-[11px] border border-gray-300 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-orange-500"
				/>
			</div>
			<!-- Status / count -->
			<div class="flex-1 text-[10px] text-gray-500 self-end pb-1">
				<span v-if="loading">{{ __("Loading reservations...") }}</span>
				<span v-else-if="visitDate && !salesOrders.length">{{ __("No reservations for this date") }}</span>
				<span v-else-if="salesOrders.length">{{ __("{0} reservation(s)", [salesOrders.length]) }}</span>
				<span v-else>{{ __("Pick a visit date to find party reservations") }}</span>
			</div>
		</div>

		<!-- Sales Order list -->
		<div v-if="salesOrders.length" class="mt-2 flex flex-col gap-1 max-h-48 overflow-y-auto">
			<div
				v-for="so in salesOrders"
				:key="so.name"
				role="button"
				tabindex="0"
				class="text-start border rounded-lg p-1.5 transition-colors touch-manipulation cursor-pointer"
				:class="selected === so.name
					? 'border-orange-500 bg-orange-50'
					: 'border-gray-200 hover:border-orange-300 hover:bg-gray-50'"
				@click="select(so)"
			>
				<div class="flex items-center justify-between gap-2">
					<span class="text-[11px] font-semibold text-gray-800 truncate">{{ so.select_event || so.name }}</span>
					<span class="text-[10px] font-medium text-orange-600 whitespace-nowrap">{{ formatCurrency(so.grand_total) }}</span>
				</div>
				<div class="flex items-center justify-between gap-2 mt-0.5">
					<div class="flex items-center gap-2 text-[9px] text-gray-500 min-w-0">
						<span v-if="so.select_slot" class="truncate">{{ so.select_slot }}</span>
						<span v-if="so.total_deposit" class="text-green-600 font-medium whitespace-nowrap">
							✓ {{ __("Deposited") }}: {{ formatCurrency(so.total_deposit) }}
						</span>
					</div>
					<!-- Add a (partial) deposit; multiple deposits are allowed -->
					<button
						type="button"
						class="text-[9px] font-semibold text-blue-600 hover:text-blue-800 whitespace-nowrap"
						@click.stop="openDepositDialog(so)"
					>
						{{ so.total_deposit ? __("Add deposit") : __("Create deposit invoice") }}
					</button>
				</div>
			</div>
		</div>

		<!-- Deposit payment dialog -->
		<div
			v-if="depositDialog.open"
			class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
			@click.self="closeDepositDialog"
		>
			<div class="bg-white rounded-xl shadow-xl w-full max-w-xs p-3">
				<div class="flex items-center justify-between mb-3">
					<h3 class="text-sm font-semibold text-gray-800">{{ __("Deposit Payment") }}</h3>
					<button type="button" class="text-gray-400 hover:text-gray-600" @click="closeDepositDialog">✕</button>
				</div>

				<label class="block text-[10px] font-medium text-gray-500 mb-1">{{ __("Amount") }}</label>
				<input
					type="number"
					v-model.number="depositDialog.amount"
					min="0"
					class="w-full text-sm border border-gray-300 rounded-lg px-2 py-1.5 mb-3 focus:outline-none focus:ring-2 focus:ring-orange-500"
				/>

				<label class="block text-[10px] font-medium text-gray-500 mb-1">{{ __("Payment Method") }}</label>
				<select
					v-model="depositDialog.modeOfPayment"
					class="w-full text-sm border border-gray-300 rounded-lg px-2 py-1.5 mb-4 focus:outline-none focus:ring-2 focus:ring-orange-500"
				>
					<option v-for="pm in paymentMethods" :key="pm.mode_of_payment" :value="pm.mode_of_payment">
						{{ __(pm.mode_of_payment) }}
					</option>
				</select>

				<div class="flex items-center gap-2">
					<button
						type="button"
						class="flex-1 text-xs font-medium text-gray-600 border border-gray-300 rounded-lg py-2 hover:bg-gray-50"
						@click="closeDepositDialog"
					>
						{{ __("Cancel") }}
					</button>
					<button
						type="button"
						class="flex-1 text-xs font-semibold text-white bg-orange-600 rounded-lg py-2 hover:bg-orange-700 disabled:opacity-50"
						:disabled="savingDeposit || !depositDialog.amount || !depositDialog.modeOfPayment"
						@click="confirmDeposit"
					>
						{{ savingDeposit ? __("Saving...") : __("Confirm") }}
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import {
	formatCurrency as formatCurrencyUtil,
	DEFAULT_CURRENCY,
} from "@/utils/currency"
import { useToast } from "@/composables/useToast"

const props = defineProps({
	posProfile: String,
	customer: Object,
	currency: { type: String, default: DEFAULT_CURRENCY },
})

const emit = defineEmits(["select-order"])

const { showError, showSuccess } = useToast()

const visitDate = ref("")
const salesOrders = ref([])
const selected = ref(null)
const loading = ref(false)
const paymentMethods = ref([])
const savingDeposit = ref(false)
const depositDialog = ref({
	open: false,
	so: null,
	amount: 0,
	modeOfPayment: "",
})

function formatCurrency(value) {
	return formatCurrencyUtil(value || 0, props.currency)
}

async function ensurePaymentMethods() {
	if (paymentMethods.value.length) return
	try {
		const res = await call("ecs_posnext.api.pos_profile.get_payment_methods", {
			pos_profile: props.posProfile,
		})
		paymentMethods.value = Array.isArray(res) ? res : res?.message || []
	} catch (e) {
		console.error("Failed to load payment methods", e)
		paymentMethods.value = []
	}
}

async function openDepositDialog(so) {
	await ensurePaymentMethods()
	const defaultMethod =
		paymentMethods.value.find((m) => m.default) || paymentMethods.value[0]
	depositDialog.value = {
		open: true,
		so,
		amount: so.advance_amount || 0,
		modeOfPayment: defaultMethod?.mode_of_payment || "",
	}
}

function closeDepositDialog() {
	depositDialog.value = { open: false, so: null, amount: 0, modeOfPayment: "" }
}

async function confirmDeposit() {
	const { so, amount, modeOfPayment } = depositDialog.value
	if (!so || !amount || !modeOfPayment) return
	savingDeposit.value = true
	try {
		await call("ecs_posnext.api.reservations.create_deposit_invoice", {
			pos_profile: props.posProfile,
			sales_order: so.name,
			amount,
			payments: JSON.stringify([{ mode_of_payment: modeOfPayment, amount }]),
		})
		showSuccess(__("Deposit invoice created"))
		closeDepositDialog()
		await fetchOrders()
	} catch (e) {
		console.error("Failed to create deposit invoice", e)
		showError(e?.message || __("Could not create deposit invoice"))
	} finally {
		savingDeposit.value = false
	}
}

async function fetchOrders() {
	if (!visitDate.value) {
		salesOrders.value = []
		return
	}
	loading.value = true
	try {
		const res = await call(
			"ecs_posnext.api.reservations.get_reservation_sales_orders",
			{
				pos_profile: props.posProfile,
				visit_date: visitDate.value,
				customer: props.customer?.name || props.customer || undefined,
			},
		)
		salesOrders.value = Array.isArray(res) ? res : res?.message || []
	} catch (e) {
		console.error("Failed to fetch reservation sales orders", e)
		showError(__("Could not load reservations"))
		salesOrders.value = []
	} finally {
		loading.value = false
	}
}

function select(so) {
	selected.value = so.name
	emit("select-order", so)
}

// Refetch when the visit date or the selected customer changes.
watch([visitDate, () => props.customer?.name], fetchOrders)
</script>
