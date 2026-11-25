<template>
	<Dialog v-model="show" :options="{ title: __('Payment Links'), size: '4xl' }">
		<template #body-content>
			<div class="flex items-center justify-between gap-2 mb-3 flex-wrap">
				<p class="text-xs text-gray-500">
					{{ __("Invoices waiting for a payment link (last 7 days). They are submitted automatically once paid.") }}
				</p>
				<div class="flex items-center gap-2">
					<select
						v-model="statusFilter"
						class="h-8 text-xs border border-gray-300 rounded-lg px-2 bg-white"
						:aria-label="__('Status')"
					>
						<option value="">{{ __("All") }}</option>
						<option value="Pending">{{ __("Pending") }}</option>
						<option value="Paid">{{ __("Paid") }}</option>
						<option value="Failed">{{ __("Failed") }}</option>
						<option value="Error">{{ __("Needs attention") }}</option>
					</select>
					<button
						type="button"
						class="h-8 px-3 text-xs font-semibold rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
						:disabled="loading"
						@click="load"
					>
						{{ loading ? __("Loading...") : __("Refresh") }}
					</button>
				</div>
			</div>

			<div v-if="loading && !rows.length" class="py-10 text-center text-sm text-gray-500">{{ __("Loading...") }}</div>
			<div v-else-if="error" class="py-6 text-center text-sm text-red-600">
				{{ error }}
				<button type="button" class="ms-2 underline" @click="load">{{ __("Retry") }}</button>
			</div>
			<div v-else-if="!filteredRows.length" class="py-10 text-center text-sm text-gray-500">
				{{ __("No payment links") }}
			</div>

			<div v-else class="max-h-[60vh] overflow-y-auto border border-gray-200 rounded-lg">
				<table class="min-w-full text-xs">
					<thead class="bg-gray-50 sticky top-0">
						<tr class="text-start text-gray-600">
							<th class="px-3 py-2 text-start font-semibold">{{ __("Invoice") }}</th>
							<th class="px-3 py-2 text-start font-semibold">{{ __("Customer") }}</th>
							<th class="px-3 py-2 text-end font-semibold">{{ __("Link Amount") }}</th>
							<th class="px-3 py-2 text-start font-semibold">{{ __("Created") }}</th>
							<th class="px-3 py-2 text-start font-semibold">{{ __("Status") }}</th>
							<th class="px-3 py-2 text-end font-semibold">{{ __("Actions") }}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100">
						<tr v-for="row in filteredRows" :key="row.name" class="align-top">
							<td class="px-3 py-2 font-medium text-gray-800 whitespace-nowrap">
								{{ row.name }}
								<div class="text-[10px] text-gray-400">{{ row.kind === "tabby" ? "Tabby" : __("Card / Apple Pay") }}</div>
							</td>
							<td class="px-3 py-2">
								<div class="text-gray-800">{{ row.customer_name || row.customer }}</div>
								<div v-if="row.mobile" class="text-[10px] text-gray-500" dir="ltr">{{ row.mobile }}</div>
							</td>
							<td class="px-3 py-2 text-end whitespace-nowrap">{{ formatAmount(row.link_amount) }}</td>
							<td class="px-3 py-2 whitespace-nowrap text-gray-600">{{ formatDate(row.creation) }}</td>
							<td class="px-3 py-2">
								<span :class="['inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold', statusClass(row.status)]">
									{{ statusLabel(row.status) }}
								</span>
							</td>
							<td class="px-3 py-2">
								<div class="flex flex-wrap justify-end gap-1">
									<button
										v-if="row.docstatus === 0"
										type="button"
										class="h-7 px-2 text-[11px] font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
										:disabled="row._busy"
										@click="checkStatus(row)"
									>
										{{ row._busy === "check" ? __("Checking...") : __("Check status") }}
									</button>
									<button
										v-if="row.docstatus === 0 && row.custom_url"
										type="button"
										class="h-7 px-2 text-[11px] font-semibold rounded-lg border border-gray-300 hover:bg-gray-50"
										@click="copyLink(row)"
									>
										{{ row._copied ? __("Copied") : __("Copy link") }}
									</button>
									<button
										v-if="row.docstatus === 0"
										type="button"
										class="h-7 px-2 text-[11px] font-semibold rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
										:disabled="row._busy"
										@click="resend(row, row.status === 'Failed')"
									>
										{{ row._busy === "resend" ? __("Sending...") : row.status === "Failed" ? __("New link") : __("Resend SMS") }}
									</button>
								</div>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Dialog } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { parseError } from "@/utils/errorHandler"

const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
})
const emit = defineEmits(["update:modelValue"])
const { showSuccess, showError, showWarning } = useToast()

const show = computed({
	get: () => props.modelValue,
	set: (v) => emit("update:modelValue", v),
})

const rows = ref([])
const loading = ref(false)
const error = ref("")
const statusFilter = ref("")

const filteredRows = computed(() =>
	statusFilter.value ? rows.value.filter((r) => r.status === statusFilter.value) : rows.value,
)

const STATUS_LABELS = {
	Pending: () => __("Pending"),
	Paid: () => __("Paid"),
	Failed: () => __("Failed"),
	Error: () => __("Paid - not submitted"),
}

function statusLabel(s) {
	return (STATUS_LABELS[s] || (() => s))()
}

function statusClass(s) {
	return (
		{
			Pending: "bg-amber-100 text-amber-800",
			Paid: "bg-green-100 text-green-700",
			Failed: "bg-red-100 text-red-700",
			Error: "bg-red-600 text-white",
		}[s] || "bg-gray-100 text-gray-700"
	)
}

function formatAmount(v) {
	return `${Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} SAR`
}

function formatDate(v) {
	return v ? String(v).slice(0, 16) : ""
}

async function load() {
	loading.value = true
	error.value = ""
	try {
		const res = await call("ecs_posnext.api.payment_links.get_payment_links", { pos_profile: props.posProfile })
		rows.value = (res?.message || res || []).map((r) => ({ ...r, _busy: null, _copied: false }))
	} catch (e) {
		error.value = parseError(e).message || __("Could not load payment links")
	} finally {
		loading.value = false
	}
}

async function checkStatus(row) {
	row._busy = "check"
	try {
		const res = await call("ecs_posnext.api.payment_links.check_payment_link_status", { invoice_name: row.name })
		const data = res?.message || res || {}
		if (data.submitted) showSuccess(__("{0} is paid and has been submitted", [row.name]))
		else if (data.status === "Failed") showWarning(__("The payment for {0} failed", [row.name]))
		else showWarning(__("{0} is not paid yet", [row.name]))
		await load()
	} catch (e) {
		showError(parseError(e).message || __("Could not check the payment status"))
	} finally {
		row._busy = null
	}
}

async function resend(row, newLink) {
	row._busy = "resend"
	try {
		const res = await call("ecs_posnext.api.payment_links.resend_payment_link", {
			invoice_name: row.name,
			new_link: newLink ? 1 : 0,
		})
		const data = res?.message || res || {}
		if (data.sms_sent) showSuccess(__("Link sent by SMS to {0}", [data.mobile]))
		else showWarning(__("SMS not sent - copy the link and share it manually"))
		await load()
	} catch (e) {
		showError(parseError(e).message || __("Could not send the payment link"))
	} finally {
		row._busy = null
	}
}

async function copyLink(row) {
	try {
		await navigator.clipboard.writeText(row.custom_url || "")
		row._copied = true
		setTimeout(() => (row._copied = false), 1500)
	} catch {
		showWarning(__("Copy failed - select the link manually"))
	}
}

watch(
	() => props.modelValue,
	(open) => {
		if (open) load()
	},
)
</script>
