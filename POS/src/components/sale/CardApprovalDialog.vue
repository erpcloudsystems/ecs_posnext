<template>
	<Dialog v-model="show" :options="{ title: __('Card Approval'), size: 'sm' }">
		<template #body-content>
			<p class="text-xs text-gray-500 mb-3">
				{{ __("Complete the payment on the card terminal. Approval is captured automatically.") }}
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
						<span v-else class="text-[11px] text-gray-500">
							{{ row.state === "running" && terminalAction ? terminalAction : stateLabel(row.state) }}
						</span>
					</div>
					<span class="text-lg">
						<span v-if="row.state === 'approved'">✅</span>
						<span v-else-if="row.state === 'failed'">❌</span>
						<span v-else-if="row.state === 'running'" class="animate-pulse">⏳</span>
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
import { computed, onBeforeUnmount, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { formatCurrency } from "@/utils/currency"
import {
	GeideaEcrClient,
	buildEcrNumber,
	extractSamaCode,
	isApproved,
} from "@/utils/geideaEcr"
import { logger } from "@/utils/logger"

const log = logger.create("CardApprovalDialog")

const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
	// Array of card payment amounts (one terminal transaction each).
	cardAmounts: { type: Array, default: () => [] },
})

const emit = defineEmits(["update:modelValue", "approved"])

const rows = ref([])
const error = ref("")
const terminalAction = ref("")
let cancelled = false
let client = null

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

const hasFailed = computed(() => rows.value.some((r) => r.state === "failed"))

function rowClass(state) {
	if (state === "approved") return "border-green-200 bg-green-50"
	if (state === "failed") return "border-red-200 bg-red-50"
	if (state === "running") return "border-blue-200 bg-blue-50"
	return "border-gray-200"
}

function stateLabel(state) {
	if (state === "running") return __("Sending to terminal...")
	if (state === "failed") return __("Declined or timed out")
	if (state === "pending") return __("Queued")
	return ""
}

/** Pull the approval code out of a terminal response, tolerating key variations. */
function readApprovalCode(result) {
	return (
		result?.TransactionAuthCode ||
		result?.AuthorizationCode ||
		result?.ApprovalCode ||
		""
	)
}

function teardownClient() {
	if (!client) return
	try {
		client.close()
	} catch (e) {
		log.debug("Client close failed", e)
	}
	client = null
}

async function start() {
	error.value = ""
	terminalAction.value = ""
	cancelled = false
	rows.value = props.cardAmounts.map((amount) => ({
		amount,
		state: "pending",
		approval_code: null,
	}))

	// Fetch the terminal's connection settings, then drive it from the browser.
	let terminal
	try {
		const res = await call("ecs_posnext.api.payments.get_card_terminal", {
			pos_profile: props.posProfile,
		})
		terminal = res?.message ?? res
	} catch (e) {
		log.error("get_card_terminal failed", e)
		error.value = __("Could not load the card terminal settings.")
		markAllFailed()
		return
	}

	if (!terminal) {
		error.value = __(
			"No active Geidea terminal is configured for this POS Profile.",
		)
		markAllFailed()
		return
	}

	teardownClient()
	client = new GeideaEcrClient(terminal)
	client.onMessage((event) => {
		if (event.type === "action") terminalAction.value = event.label
		if (event.type === "disconnected") terminalAction.value = ""
	})

	try {
		await client.ensureReady()
	} catch (e) {
		log.error("Terminal connect failed", e)
		error.value = e.message
		markAllFailed()
		return
	}

	for (const row of rows.value) {
		if (cancelled) return
		const ok = await processRow(row)
		if (!ok) return // stop on first failure; the cashier can Retry or Cancel
	}

	if (!cancelled && rows.value.every((r) => r.state === "approved")) {
		teardownClient()
		emit(
			"approved",
			rows.value.map((r) => ({
				approval_code: r.approval_code,
				amount: r.amount,
			})),
		)
	}
}

function markAllFailed() {
	for (const row of rows.value) {
		if (row.state !== "approved") row.state = "failed"
	}
}

async function processRow(row) {
	row.state = "running"
	row.approval_code = null
	terminalAction.value = ""

	let result
	try {
		result = await client.purchase(row.amount, buildEcrNumber())
	} catch (e) {
		log.error("Purchase failed", e)
		row.state = "failed"
		error.value = e.message
		return false
	}

	if (cancelled) return false

	if (!isApproved(result)) {
		row.state = "failed"
		const code = extractSamaCode(result)
		error.value = __("Transaction {0} was declined{1}.", [
			rows.value.indexOf(row) + 1,
			code ? ` (${code})` : "",
		])
		return false
	}

	const approvalCode = readApprovalCode(result)
	if (!approvalCode) {
		// Approved with no auth code means nothing to store on the invoice, which
		// is exactly what this gate exists to capture — treat it as a failure so
		// the cashier retries rather than closing an unverifiable sale.
		row.state = "failed"
		error.value = __(
			"The terminal approved the payment but returned no approval code.",
		)
		return false
	}

	row.approval_code = approvalCode
	row.state = "approved"
	terminalAction.value = ""
	return true
}

function cancel() {
	cancelled = true
	teardownClient()
	emit("update:modelValue", false)
}

watch(
	() => props.modelValue,
	(open) => {
		if (open) {
			start()
		} else {
			cancelled = true
			teardownClient()
		}
	},
)

onBeforeUnmount(() => {
	cancelled = true
	teardownClient()
})
</script>
