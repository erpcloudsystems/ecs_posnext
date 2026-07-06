<template>
	<Dialog v-model="show" :options="{ title: __('Card Approval'), size: 'sm' }">
		<template #body-content>
			<p class="text-xs text-gray-500 mb-3">
				{{ __("Complete the payment on the card terminal. Approval is checked automatically.") }}
			</p>

			<div class="space-y-2 mb-3">
				<div
					v-for="(row, idx) in rows"
					:key="idx"
					class="flex items-center justify-between rounded-lg border px-3 py-2"
					:class="rowClass(row.state)"
				>
					<div class="flex flex-col">
						<span class="text-sm font-medium text-gray-800">
							{{ __("Transaction {0}", [idx + 1]) }} · {{ formatCurrency(row.amount) }}
						</span>
						<span v-if="row.approval_code" class="text-[11px] text-green-700">
							{{ __("Approval code") }}: {{ row.approval_code }}
						</span>
						<span v-else class="text-[11px] text-gray-500">{{ stateLabel(row.state) }}</span>
					</div>
					<span class="text-lg">
						<span v-if="row.state === 'approved'">✅</span>
						<span v-else-if="row.state === 'failed'">❌</span>
						<span v-else-if="row.state === 'polling' || row.state === 'sending'" class="animate-pulse">⏳</span>
						<span v-else>•</span>
					</span>
				</div>
			</div>

			<p v-if="error" class="text-xs text-red-600 mb-2">{{ error }}</p>

			<div class="flex items-center gap-2">
				<button
					type="button"
					class="flex-1 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg py-2 hover:bg-gray-50"
					@click="cancel"
				>
					{{ __("Cancel") }}
				</button>
				<button
					v-if="hasFailed"
					type="button"
					class="flex-1 text-sm font-semibold text-white bg-blue-600 rounded-lg py-2 hover:bg-blue-700"
					@click="start"
				>
					{{ __("Retry") }}
				</button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Dialog } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { formatCurrency } from "@/utils/currency"

const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
	// Array of card payment amounts (one terminal transaction each).
	cardAmounts: { type: Array, default: () => [] },
	referenceName: String,
	referenceDoctype: { type: String, default: "Sales Invoice" },
})

const emit = defineEmits(["update:modelValue", "approved"])

const POLL_INTERVAL_MS = 3000
const POLL_TIMEOUT_MS = 90000
const FAILED_STATUSES = new Set([
	"DECLINED",
	"FAILED",
	"CANCELLED",
	"CANCELED",
	"REVERSED",
	"ERROR",
	"VOIDED",
	"REJECTED",
	"EXPIRED",
])

const rows = ref([])
const error = ref("")
let cancelled = false

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

const hasFailed = computed(() => rows.value.some((r) => r.state === "failed"))

function rowClass(state) {
	if (state === "approved") return "border-green-200 bg-green-50"
	if (state === "failed") return "border-red-200 bg-red-50"
	if (state === "polling" || state === "sending")
		return "border-blue-200 bg-blue-50"
	return "border-gray-200"
}

function stateLabel(state) {
	if (state === "sending") return __("Sending to terminal...")
	if (state === "polling") return __("Waiting for approval...")
	if (state === "failed") return __("Declined or timed out")
	if (state === "pending") return __("Queued")
	return ""
}

const sleep = (ms) =>
	new Promise((resolve) => {
		setTimeout(resolve, ms)
	})

async function processRow(row) {
	row.state = "sending"
	row.approval_code = null
	let checkout
	try {
		checkout = await call("ecs_posnext.api.payments.card_checkout", {
			pos_profile: props.posProfile,
			amount: row.amount,
			reference_name: props.referenceName || undefined,
			reference_doctype: props.referenceDoctype,
		})
	} catch (e) {
		console.error("card_checkout failed", e)
		row.state = "failed"
		error.value = __("Could not reach the card terminal.")
		return false
	}

	const tx = (checkout?.message || checkout)?.transaction
	if (!tx) {
		row.state = "failed"
		error.value = __("Card terminal did not return a transaction.")
		return false
	}

	row.state = "polling"
	const deadline = Date.now() + POLL_TIMEOUT_MS
	while (!cancelled && Date.now() < deadline) {
		await sleep(POLL_INTERVAL_MS)
		if (cancelled) return false
		let status
		try {
			const res = await call("ecs_posnext.api.payments.card_status", {
				tx_name: tx,
			})
			status = res?.message || res
		} catch (e) {
			console.error("card_status failed", e)
			continue
		}
		const s = (status?.status || "").toUpperCase()
		if (s === "APPROVED") {
			row.approval_code = status.approval_code || ""
			row.state = "approved"
			return true
		}
		if (FAILED_STATUSES.has(s)) {
			row.state = "failed"
			error.value = __("Transaction {0} was declined.", [
				rows.value.indexOf(row) + 1,
			])
			return false
		}
	}
	if (!cancelled) {
		row.state = "failed"
		error.value = __("Timed out waiting for card approval.")
	}
	return false
}

async function start() {
	error.value = ""
	cancelled = false
	rows.value = props.cardAmounts.map((amount) => ({
		amount,
		state: "pending",
		approval_code: null,
	}))

	for (const row of rows.value) {
		if (cancelled) return
		const ok = await processRow(row)
		if (!ok) return // stop on first failure; user can Retry or Cancel
	}

	if (!cancelled && rows.value.every((r) => r.state === "approved")) {
		emit("approved", rows.value.map((r) => r.approval_code).filter(Boolean))
	}
}

function cancel() {
	cancelled = true
	emit("update:modelValue", false)
}

watch(
	() => props.modelValue,
	(open) => {
		if (open) {
			start()
		} else {
			cancelled = true
		}
	},
)
</script>
