<template>
	<Dialog v-model="show" :options="{ title: __('Ticket Redeem & Renewal'), size: '5xl' }">
		<template #body-content>
			<!-- Search bar (type or scan a ticket code / customer, Enter to search) -->
			<div class="flex items-center gap-2 mb-3">
				<div class="relative flex-1">
					<span class="absolute start-3 top-1/2 -translate-y-1/2 text-gray-400">🎫</span>
					<input
						ref="searchInput"
						v-model="query"
						type="text"
						:placeholder="__('Scan / enter ticket code or customer, then Enter')"
						class="w-full h-11 ps-9 pe-3 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						@keyup.enter="runSearch"
					/>
				</div>
				<button
					type="button"
					class="h-11 px-5 text-sm font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
					:disabled="searching || !query.trim()"
					@click="runSearch"
				>
					{{ searching ? __("Searching...") : __("Search") }}
				</button>
			</div>

			<div v-if="searching" class="py-10 text-center text-sm text-gray-500">{{ __("Searching...") }}</div>
			<div v-else-if="searched && tickets.length === 0" class="py-10 text-center text-sm text-gray-500">
				{{ __('No tickets found for "{0}"', [lastQuery]) }}
			</div>

			<!-- Ticket cards -->
			<div class="space-y-3 max-h-[65vh] overflow-y-auto">
				<div
					v-for="t in tickets"
					:key="t.name"
					class="border border-gray-200 rounded-xl p-4 bg-gray-50"
				>
					<div class="flex items-center gap-3 mb-2">
						<!-- Child photo -->
						<img
							v-if="t.image"
							:src="t.image"
							alt="ticket"
							class="w-14 h-14 rounded-lg object-cover border border-gray-200 bg-white flex-shrink-0"
							@error="t.image = ''"
						/>
						<div class="flex-1 min-w-0">
							<h3 class="text-sm font-bold text-gray-800 truncate">{{ __("Ticket") }} {{ t.name }}</h3>
							<p v-if="t.child_name" class="text-xs text-gray-600 truncate">👤 {{ t.child_name }}</p>
						</div>
						<span
							class="text-[11px] font-semibold px-2 py-0.5 rounded-full flex-shrink-0"
							:class="isExpired(t) ? 'bg-red-100 text-red-700' : (t.remaining_usage > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-600')"
						>
							{{ isExpired(t) ? __("Expired") : (t.remaining_usage > 0 ? __("Active") : __("No uses left")) }}
						</span>
					</div>

					<div class="grid grid-cols-2 lg:grid-cols-3 gap-x-4 gap-y-1 text-xs text-gray-700 mb-3">
						<div><span class="text-gray-500">{{ __("Code") }}:</span> {{ t.redeem_code }}</div>
						<div v-if="t.child_name"><span class="text-gray-500">{{ __("Child") }}:</span> {{ t.child_name }}</div>
						<div><span class="text-gray-500">{{ __("Customer") }}:</span> {{ t.vendor }}</div>
						<div><span class="text-gray-500">{{ __("Mobile") }}:</span> {{ t.vendor_mobile }}</div>
						<div><span class="text-gray-500">{{ __("Item") }}:</span> {{ t.item }}</div>
						<div><span class="text-gray-500">{{ __("Valid From") }}:</span> {{ t.valid_from }}</div>
						<div><span class="text-gray-500">{{ __("Valid To") }}:</span> {{ t.valid_to }}</div>
						<div><span class="text-gray-500">{{ __("Max") }}:</span> {{ t.global_maximum_usage }}</div>
						<div><span class="text-gray-500">{{ __("Used") }}:</span> {{ t.current_usage }}</div>
						<div class="font-semibold text-blue-700"><span class="text-gray-500 font-normal">{{ __("Remaining") }}:</span> {{ t.remaining_usage }}</div>
					</div>

					<!-- Redeem -->
					<div class="bg-white rounded-lg border border-gray-200 p-3 mb-2">
						<div class="flex flex-wrap items-end gap-3">
							<div v-if="t.show_ticket_details_in_pos" class="flex items-center gap-3 text-xs">
								<label class="flex items-center gap-1"><input type="checkbox" v-model="t._attend_event" /> {{ __("Attend Event") }}</label>
								<label class="flex items-center gap-1"><input type="checkbox" v-model="t._booklet" /> {{ __("Booklet") }}</label>
							</div>
							<div>
								<label class="block text-[10px] text-gray-500 mb-0.5">{{ __("Uses to redeem") }}</label>
								<input
									v-model.number="t._redeemQty"
									type="number"
									min="1"
									:max="t.remaining_usage"
									class="w-28 h-9 px-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
								/>
							</div>
							<button
								type="button"
								class="h-9 px-4 text-xs font-semibold rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
								:disabled="t._busy || !t._redeemQty || t._redeemQty < 1"
								@click="doRedeem(t, false)"
							>
								{{ __("Redeem") }}
							</button>
							<button
								type="button"
								class="h-9 px-4 text-xs font-semibold rounded-lg bg-green-500 text-white hover:bg-green-600 disabled:opacity-50"
								:disabled="t._busy || !t._redeemQty || t._redeemQty < 1"
								@click="doRedeem(t, true)"
							>
								{{ __("Redeem & Print") }}
							</button>
						</div>
					</div>

					<!-- Renew (recharge same ticket + paid invoice) -->
					<div class="bg-white rounded-lg border border-amber-200 p-3">
						<div class="text-[11px] font-semibold text-amber-700 mb-1.5">{{ __("Renew (recharge this ticket)") }}</div>
						<div class="flex flex-wrap items-end gap-3">
							<div>
								<label class="block text-[10px] text-gray-500 mb-0.5">{{ __("Add uses") }}</label>
								<input v-model.number="t._renewUses" type="number" min="1" max="1" @input="syncRenewAmount(t)"
									class="w-24 h-9 px-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500" />
							</div>
							<div>
								<label class="block text-[10px] text-gray-500 mb-0.5">{{ __("Amount") }}</label>
								<input v-model.number="t._renewAmount" type="number" min="0" step="0.01"
									class="w-28 h-9 px-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500" />
							</div>
							<div>
								<label class="block text-[10px] text-gray-500 mb-0.5">{{ __("Payment") }}</label>
								<select v-model="t._renewMop" class="h-9 px-2 text-sm border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-amber-500">
									<option v-for="m in paymentMethods" :key="m" :value="m">{{ __(m) }}</option>
								</select>
							</div>
							<button
								type="button"
								class="h-9 px-4 text-xs font-semibold rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
								:disabled="t._busy || !t._renewUses || t._renewUses < 1 || !t._renewAmount || t._renewAmount <= 0"
								@click="doRenew(t)"
							>
								{{ t._busy ? __("Processing...") : __("Renew") }}
							</button>
						</div>
					</div>
				</div>
			</div>
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
import { computed, nextTick, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { parseError } from "@/utils/errorHandler"

const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
	currency: String,
	company: String,
	branch: String,
	customer: [String, Object],
	paymentMethods: { type: Array, default: () => [] },
})

const emit = defineEmits(["update:modelValue"])

const { showSuccess, showError } = useToast()

const query = ref("")
const lastQuery = ref("")
const tickets = ref([])
const searching = ref(false)
const searched = ref(false)
const searchInput = ref(null)

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

function isExpired(t) {
	if (!t.valid_to) return false
	return new Date(t.valid_to) < new Date(new Date().toDateString())
}

function decorate(rows) {
	return (rows || [])
		.map((t) => ({
			...t,
			_redeemQty: t.remaining_usage > 0 ? 1 : 0,
			_attend_event: !!t.attend_event,
			_booklet: !!t.booklet,
			_renewUses: 1,
			_renewAmount: Number(t.rate) || 0,
			_renewMop: props.paymentMethods[0] || "",
			_busy: false,
		}))
		// Valid tickets first (soonest expiry first), expired ones last.
		.sort((a, b) => {
			const ax = isExpired(a) ? 1 : 0
			const bx = isExpired(b) ? 1 : 0
			if (ax !== bx) return ax - bx
			return String(a.valid_to || "").localeCompare(String(b.valid_to || ""))
		})
}

function syncRenewAmount(t) {
	// Suggest amount = rate * added uses (cashier can still override).
	t._renewAmount = Number(
		((Number(t.rate) || 0) * (Number(t._renewUses) || 0)).toFixed(2),
	)
}

async function runSearch() {
	const q = query.value.trim()
	if (!q) return
	searching.value = true
	searched.value = true
	lastQuery.value = q
	try {
		// Try by ticket/redeem code first; fall back to customer.
		let rows = await call("ecs_posnext.api.tickets.search_tickets", {
			search_keys: { ticket_name: q },
		})
		rows = rows?.message || rows || []
		if (!rows.length) {
			const byCust = await call("ecs_posnext.api.tickets.search_tickets", {
				search_keys: { customer: q },
			})
			rows = byCust?.message || byCust || []
		}
		tickets.value = decorate(rows)
	} catch (e) {
		console.error("Ticket search failed", e)
		showError(parseError(e).message || __("Ticket search failed"))
		tickets.value = []
	} finally {
		searching.value = false
	}
}

async function refresh() {
	if (lastQuery.value) {
		query.value = lastQuery.value
		await runSearch()
	}
}

function printTicket(name) {
	const base = window.location.origin
	const url = `${base}/printview?doctype=Ticket&name=${encodeURIComponent(name)}&trigger_print=1&format=${encodeURIComponent("NEW Ticket receipt")}`
	window.open(url, "_blank")
}

async function doRedeem(t, print) {
	if (t._busy) return
	t._busy = true
	try {
		await call("ecs_posnext.api.tickets.redeem_ticket", {
			ticket_name: t.name,
			customer: t.vendor,
			number_of_redeems: t._redeemQty,
			// branch omitted on purpose → backend resolves the POS Profile's Dimension Branch.
			pos_profile: props.posProfile,
			attend_event: t._attend_event ? 1 : 0,
			booklet: t._booklet ? 1 : 0,
		})
		showSuccess(__("Redeemed {0} use(s) from {1}", [t._redeemQty, t.name]))
		if (print) printTicket(t.name)
		await refresh()
	} catch (e) {
		console.error("Redeem failed", e)
		showError(parseError(e).message || __("Redeem failed"))
	} finally {
		t._busy = false
	}
}

async function doRenew(t) {
	if (t._busy) return
	t._busy = true
	try {
		const res = await call("ecs_posnext.api.tickets.renew_ticket", {
			ticket_name: t.name,
			added_uses: t._renewUses,
			amount: t._renewAmount,
			pos_profile: props.posProfile,
			mode_of_payment: t._renewMop || undefined,
		})
		const data = res?.message || res
		showSuccess(
			__("Renewed {0}: +{1} uses, valid to {2}", [
				t.name,
				t._renewUses,
				data?.valid_to || "",
			]),
		)
		await refresh()
	} catch (e) {
		console.error("Renew failed", e)
		showError(parseError(e).message || __("Renew failed"))
	} finally {
		t._busy = false
	}
}

// Focus search on open; reset on close.
watch(
	() => props.modelValue,
	(open) => {
		if (open) {
			nextTick(() => setTimeout(() => searchInput.value?.focus(), 100))
		} else {
			query.value = ""
			tickets.value = []
			searched.value = false
			lastQuery.value = ""
		}
	},
)
</script>
