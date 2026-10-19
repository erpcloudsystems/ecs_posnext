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

			<div
				v-if="orphanCharges.length"
				class="text-xs text-amber-800 border border-amber-300 bg-amber-50 rounded-lg px-3 py-2 mb-2"
			>
				<p class="font-semibold mb-1">
					{{ __("These approved charges are no longer part of this payment. Void them on the terminal:") }}
				</p>
				<p v-for="(charge, idx) in orphanCharges" :key="idx">
					{{ formatCurrency(charge.amount) }} · {{ __("Approval code") }}: {{ charge.approval_code }}
				</p>
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
					v-if="allowSkip"
					type="button"
					class="flex-1 text-sm font-semibold text-amber-800 border border-amber-300 bg-amber-50 rounded-lg py-2 hover:bg-amber-100"
					@click="skipTerminal"
				>
					{{ __("Skip Terminal") }}
				</button>
				<button
					v-if="hasFailed"
					type="button"
					class="flex-1 text-sm font-semibold text-white bg-blue-600 rounded-lg py-2 hover:bg-blue-700"
					@click="start"
				>
					{{ __("Retry") }}
				</button>
				<button
					v-if="awaitingConfirm"
					type="button"
					class="flex-1 text-sm font-semibold text-white bg-blue-600 rounded-lg py-2 hover:bg-blue-700"
					@click="finish"
				>
					{{ __("Continue") }}
				</button>
			</div>
			<p v-if="allowSkip" class="text-[11px] text-gray-500 mt-2">
				{{ __("Skipping submits the invoice without a terminal approval code.") }}
			</p>
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
	// Charges the terminal already approved in this payment session, as
	// { approval_code, amount }. Owned by the parent so they survive Cancel and
	// re-opening; a card amount matching one of these is not charged again.
	approvedCharges: { type: Array, default: () => [] },
})

const emit = defineEmits(["update:modelValue", "approved", "charge-approved"])

const rows = ref([])
// Approved charges that no longer match any card amount (the cashier changed or
// removed that payment after it was charged). The money was still taken, so the
// cashier must void it on the terminal — never silently drop it.
const orphanCharges = ref([])
// All rows approved but orphan charges exist: wait for the cashier to
// acknowledge the warning instead of closing the dialog on them.
const awaitingConfirm = ref(false)
const error = ref("")
const terminalAction = ref("")
// Set from the Geidea Terminal doc ("Allow Cashier to Skip Terminal"): lets the
// cashier bypass the terminal and submit the invoice with no approval code.
const allowSkip = ref(false)
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

function sameAmount(a, b) {
	return Math.abs(Number(a) - Number(b)) < 0.005
}

/**
 * One row per card amount. A row whose amount matches a charge the terminal
 * already approved this session starts out approved with that code, so Retry
 * (or Cancel then Complete again) only charges the cards still unpaid. Each
 * approved charge is consumed by at most one row.
 */
function buildRows() {
	const unused = [...props.approvedCharges]
	rows.value = props.cardAmounts.map((amount) => {
		const idx = unused.findIndex((c) => sameAmount(c.amount, amount))
		if (idx === -1) {
			return { amount, state: "pending", approval_code: null }
		}
		const [charge] = unused.splice(idx, 1)
		return { amount, state: "approved", approval_code: charge.approval_code }
	})
	orphanCharges.value = unused
}

function finish() {
	teardownClient()
	emit(
		"approved",
		rows.value.map((r) => ({
			approval_code: r.approval_code,
			amount: r.amount,
		})),
	)
}

async function start() {
	error.value = ""
	terminalAction.value = ""
	awaitingConfirm.value = false
	cancelled = false
	buildRows()

	if (rows.value.every((r) => r.state === "approved")) {
		// Nothing left to charge — don't touch the terminal at all.
		if (orphanCharges.value.length) awaitingConfirm.value = true
		else finish()
		return
	}

	allowSkip.value = false

	// Fetch the terminal's connection settings, then drive it from the browser.
	let terminal
	try {
		const res = await call("ecs_posnext.api.payments.get_card_terminal", {
			pos_profile: props.posProfile,
		})
		terminal = res?.message ?? res
		allowSkip.value = Boolean(terminal?.allow_skip_terminal)
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
		if (row.state === "approved") continue // already charged this session
		const ok = await processRow(row)
		if (!ok) return // stop on first failure; the cashier can Retry or Cancel
	}

	if (!cancelled && rows.value.every((r) => r.state === "approved")) {
		if (orphanCharges.value.length) {
			teardownClient()
			awaitingConfirm.value = true
		} else {
			finish()
		}
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

	// Record the charge before checking `cancelled`: if the cashier cancelled
	// while the terminal was finishing, the card was still charged and a later
	// attempt must reuse this approval rather than charge it again.
	emit("charge-approved", { approval_code: approvalCode, amount: row.amount })
	row.approval_code = approvalCode
	row.state = "approved"
	terminalAction.value = ""
	return !cancelled
}

/** Bypass the terminal: keep any codes already approved, submit without the rest. */
function skipTerminal() {
	cancelled = true
	teardownClient()
	log.info("Terminal skipped by cashier")
	emit(
		"approved",
		rows.value
			.filter((r) => r.state === "approved" && r.approval_code)
			.map((r) => ({ approval_code: r.approval_code, amount: r.amount })),
	)
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
