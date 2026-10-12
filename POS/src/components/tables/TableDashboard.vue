<template>
	<!-- Full Page Overlay -->
	<Transition name="fade">
		<div
			v-if="show"
			class="fixed inset-0 bg-black bg-opacity-50 z-[300]"
			@click.self="handleClose"
		>
			<div class="fixed inset-0 flex items-center justify-center p-4">
				<div
					class="w-full h-full max-w-[95vw] max-h-[95vh] bg-white rounded-lg shadow-2xl overflow-hidden flex flex-col"
				>
					<!-- Header -->
					<div
						class="flex items-center justify-between px-6 py-5 border-b bg-gradient-to-r from-emerald-50 to-teal-50"
					>
						<div class="flex items-center gap-3">
							<div class="p-2 bg-emerald-100 rounded-lg">
								<svg
									class="w-6 h-6 text-emerald-600"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M4 10h16M6 10v9M18 10v9M3 10l1.5-4h15L21 10"
									/>
								</svg>
							</div>
							<div>
								<h2 class="text-xl font-bold text-gray-900">
									{{ __("Open Tables") }}
								</h2>
								<p class="text-xs text-gray-600 mt-0.5">
									{{
										pickerMode
											? __("Pick a free table to seat, or open a table that is already ordering")
											: __("Live view of seated tables and what they have ordered")
									}}
								</p>
							</div>
						</div>

						<div class="flex items-center gap-2">
							<span
								v-if="lastRefreshedLabel"
								class="hidden sm:inline text-[11px] text-gray-500"
							>
								{{ lastRefreshedLabel }}
							</span>
							<button
								@click="refresh(true)"
								:disabled="loading"
								class="p-2 rounded-lg hover:bg-white/70 active:bg-white text-gray-600 disabled:opacity-50 transition-colors touch-manipulation"
								:title="__('Refresh')"
								:aria-label="__('Refresh')"
							>
								<svg
									class="w-5 h-5"
									:class="{ 'animate-spin': loading }"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
									/>
								</svg>
							</button>
							<button
								@click="handleClose"
								class="p-2 rounded-lg hover:bg-white/70 active:bg-white text-gray-600 transition-colors touch-manipulation"
								:aria-label="__('Close')"
							>
								<svg
									class="w-5 h-5"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									viewBox="0 0 24 24"
								>
									<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>
					</div>

					<!-- Summary strip -->
					<div class="px-6 py-3 border-b bg-gray-50 flex flex-wrap items-center gap-2 sm:gap-3">
						<div
							v-for="stat in summaryStats"
							:key="stat.key"
							class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border"
							:class="stat.border"
						>
							<span
								v-if="stat.dot"
								class="w-2.5 h-2.5 rounded-full flex-shrink-0"
								:class="stat.dot"
							></span>
							<span class="text-[11px] text-gray-600">{{ stat.label }}</span>
							<span class="text-sm font-bold" :class="stat.text">{{ stat.value }}</span>
						</div>

						<!-- Legend: explains what the colours mean -->
						<div
							v-if="thresholds.warning || thresholds.late"
							class="ms-auto flex items-center gap-3 text-[10px] text-gray-500"
						>
							<span v-if="thresholds.warning" class="flex items-center gap-1">
								<span class="w-2 h-2 rounded-full bg-amber-500"></span>
								{{ __("no order {0}m+", [thresholds.warning]) }}
							</span>
							<span v-if="thresholds.late" class="flex items-center gap-1">
								<span class="w-2 h-2 rounded-full bg-red-500"></span>
								{{ __("no order {0}m+", [thresholds.late]) }}
							</span>
						</div>
					</div>

					<!-- Body -->
					<div class="flex-1 overflow-y-auto p-4 sm:p-6">
						<!-- Loading (first load only) -->
						<div v-if="loading && tables.length === 0" class="flex items-center justify-center py-16">
							<div class="text-center">
								<div
									class="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-500 mx-auto"
								></div>
								<p class="mt-3 text-sm text-gray-500">{{ __("Loading tables...") }}</p>
							</div>
						</div>

						<!-- Error -->
						<div v-else-if="errorMessage" class="flex items-center justify-center py-16">
							<div class="text-center max-w-sm">
								<svg
									class="mx-auto h-10 w-10 text-red-400"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
									/>
								</svg>
								<p class="mt-3 text-sm text-red-700">{{ errorMessage }}</p>
								<Button class="mt-4" variant="subtle" @click="refresh(true)">
									{{ __("Try again") }}
								</Button>
							</div>
						</div>

						<!-- Empty -->
						<div v-else-if="tables.length === 0" class="flex items-center justify-center py-16">
							<div class="text-center">
								<svg
									class="mx-auto h-12 w-12 text-gray-300"
									fill="none"
									stroke="currentColor"
									stroke-width="1.6"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M4 10h16M6 10v9M18 10v9M3 10l1.5-4h15L21 10"
									/>
								</svg>
								<p class="mt-3 text-sm font-medium text-gray-700">
									{{ __("No open tables") }}
								</p>
								<p class="mt-1 text-xs text-gray-500">
									{{ __("Seated tables will appear here as soon as an order is started") }}
								</p>
							</div>
						</div>

						<!-- Table cards -->
						<div
							v-else
							class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4"
						>
							<div
								v-for="table in sortedTables"
								:key="table.session"
								class="rounded-xl border-2 bg-white overflow-hidden flex flex-col transition-colors"
								:class="cardClasses(table).border"
							>
								<!-- Card header: table + idle badge -->
								<div class="px-4 py-3 flex items-start justify-between gap-2" :class="cardClasses(table).header">
									<div class="min-w-0">
										<div class="flex items-center gap-2">
											<span class="text-lg font-bold text-gray-900 truncate">
												{{ table.table_number }}
											</span>
											<span
												v-if="table.area"
												class="text-[10px] text-gray-500 truncate"
											>
												{{ table.area }}
											</span>
										</div>
										<div class="flex items-center gap-1 mt-0.5 text-xs text-gray-600">
											<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"
												/>
											</svg>
											<span class="font-semibold">{{ table.guest_count }}</span>
											<span class="text-gray-400">{{ __("guests") }}</span>
										</div>
									</div>

									<span
										class="flex-shrink-0 inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-bold"
										:class="cardClasses(table).badge"
									>
										<svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
										</svg>
										{{ formatMinutes(liveIdleMinutes(table)) }}
									</span>
								</div>

								<!-- Free table: seating happens inline, on this same screen -->
								<div v-if="!table.seated" class="px-4 py-3 border-t border-gray-100 flex-1 flex flex-col gap-2">
									<template v-if="seatingTable !== table.table">
										<p class="text-xs text-gray-500">
											{{
												table.seating_capacity
													? __("Free · seats {0}", [table.seating_capacity])
													: __("Free")
											}}
										</p>
										<Button
											class="w-full"
											variant="solid"
											theme="green"
											@click="startSeating(table)"
										>
											{{ __("Seat table") }}
										</Button>
									</template>

									<template v-else>
										<label class="text-[11px] font-semibold text-gray-700">
											{{ __("Number of guests") }}
										</label>
										<div class="flex items-center gap-1.5">
											<button
												type="button"
												:disabled="seatGuests <= 1"
												@click="stepSeatGuests(-1)"
												class="w-10 h-10 flex-shrink-0 rounded-lg border border-gray-300 text-gray-700 text-xl font-semibold hover:bg-gray-50 active:bg-gray-100 disabled:opacity-40 touch-manipulation"
												:aria-label="__('Decrease guests')"
											>&minus;</button>
											<input
												v-model.number="seatGuests"
												type="number"
												inputmode="numeric"
												min="1"
												@blur="normalizeSeatGuests"
												class="flex-1 min-w-0 h-10 px-2 text-center text-lg font-bold border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
											/>
											<button
												type="button"
												@click="stepSeatGuests(1)"
												class="w-10 h-10 flex-shrink-0 rounded-lg border border-gray-300 text-gray-700 text-xl font-semibold hover:bg-gray-50 active:bg-gray-100 touch-manipulation"
												:aria-label="__('Increase guests')"
											>+</button>
										</div>
										<div class="flex flex-wrap gap-1">
											<button
												v-for="n in QUICK_GUESTS"
												:key="n"
												type="button"
												@click="seatGuests = n"
												:class="[
													'px-2.5 py-1 text-[11px] font-bold rounded border transition-colors touch-manipulation',
													seatGuests === n
														? 'bg-emerald-600 border-emerald-600 text-white'
														: 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50',
												]"
											>{{ n }}</button>
										</div>
									</template>
								</div>

								<!-- Card body: the order -->
								<div v-else class="px-4 py-3 border-t border-gray-100 flex-1">
									<template v-if="table.has_order">
										<div class="flex items-baseline justify-between gap-2">
											<span class="text-xs text-gray-500">
												{{ __("{0} items", [formatQty(table.item_qty)]) }}
											</span>
											<span class="text-base font-bold text-gray-900">
												{{ formatCurrency(table.total_amount) }}
											</span>
										</div>
										<!-- Split bills are paid check by check, so say so plainly -->
										<button
											v-if="table.is_split"
											@click="handleViewChecks(table)"
											class="mt-1.5 w-full flex items-center justify-between gap-2 px-2 py-1.5 rounded-md bg-indigo-50 border border-indigo-200 hover:bg-indigo-100 transition-colors touch-manipulation"
										>
											<span class="text-[11px] font-bold text-indigo-800">
												{{ __("{0} separate checks", [table.open_checks]) }}
											</span>
											<span v-if="table.rooms?.length" class="text-[10px] text-indigo-600 truncate">
												{{ __("rooms {0}", [table.rooms.join(", ")]) }}
											</span>
										</button>
										<p v-if="table.customer_name" class="mt-1 text-[11px] text-gray-500 truncate">
											{{ table.customer_name }}
										</p>
									</template>
									<template v-else>
										<div
											class="flex items-center gap-1.5 text-xs font-semibold"
											:class="table.idle_state === 'ok' ? 'text-gray-500' : cardClasses(table).text"
										>
											<svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
											</svg>
											{{ __("Nothing ordered yet") }}
										</div>
									</template>

									<!-- Seated + cashier -->
									<div class="mt-2 flex flex-col gap-0.5 text-[10px] text-gray-400">
										<div class="flex items-center justify-between gap-2">
											<span>{{ __("seated {0}", [formatMinutes(liveSeatedMinutes(table))]) }}</span>
											<span v-if="table.order_cashier" class="truncate" :title="__('Opened by')">
												{{ table.order_cashier }}
											</span>
										</div>
										<!-- Only worth showing when a different waiter added the last round -->
										<div
											v-if="table.last_order_by && table.last_order_by !== table.order_cashier"
											class="flex items-center justify-end"
										>
											<span class="truncate" :title="__('Last order by')">
												{{ __("last: {0}", [table.last_order_by]) }}
											</span>
										</div>
									</div>
								</div>

								<!-- Free table actions: confirm or back out of seating -->
								<div
									v-if="!table.seated && seatingTable === table.table"
									class="px-3 py-2.5 bg-gray-50 border-t border-gray-100 flex gap-2"
								>
									<Button class="flex-1" variant="subtle" @click="cancelSeating">
										{{ __("Cancel") }}
									</Button>
									<Button
										class="flex-1"
										variant="solid"
										theme="green"
										:loading="seatingBusy"
										@click="confirmSeating(table)"
									>
										{{ __("Start order") }}
									</Button>
								</div>

								<!--
									Freeing a table is deliberate and confirmed: it throws away an
									unpaid order, so it must never be a one-tap mistake.
								-->
								<div
									v-else-if="table.seated && freeingTable === table.session"
									class="px-3 py-2.5 bg-red-50 border-t border-red-200 flex flex-col gap-2"
								>
									<p class="text-[11px] text-red-800">
										{{
											table.has_order
												? __("Discard this table's unpaid order of {0}?", [formatCurrency(table.total_amount)])
												: __("Free this table?")
										}}
									</p>
									<div class="flex gap-2">
										<Button class="flex-1" variant="subtle" @click="freeingTable = null">
											{{ __("Keep") }}
										</Button>
										<Button
											class="flex-1"
											variant="solid"
											theme="red"
											:loading="freeingBusy"
											@click="confirmFreeTable(table)"
										>
											{{ __("Free table") }}
										</Button>
									</div>
								</div>

								<!-- Card actions -->
								<div
									v-else-if="table.seated"
									class="px-3 py-2.5 bg-gray-50 border-t border-gray-100 flex gap-2"
								>
									<Button
										class="flex-1"
										variant="solid"
										theme="blue"
										:loading="openingSession === table.session"
										@click="table.is_split ? handleViewChecks(table) : handleOpenTable(table)"
									>
										{{
											table.is_split
												? __("Pay checks")
												: table.has_order
													? __("Open order")
													: __("Take order")
										}}
									</Button>
									<Button
										v-if="table.has_order && !table.is_split"
										variant="subtle"
										:title="__('Split the check')"
										:aria-label="__('Split the check')"
										@click="handleSplitTable(table)"
									>
										<template #icon>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3M4 11h16M6 21h12a2 2 0 002-2V7a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
											</svg>
										</template>
									</Button>
									<Button
										variant="subtle"
										:title="__('Free this table without charging')"
										:aria-label="__('Free this table without charging')"
										@click="freeingTable = table.session"
									>
										<template #icon>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
											</svg>
										</template>
									</Button>
									<Button
										variant="subtle"
										:title="__('Move to another table')"
										:aria-label="__('Move to another table')"
										@click="handleMoveTable(table)"
									>
										<template #icon>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4M16 17H4m0 0l4 4m-4-4l4-4"/>
											</svg>
										</template>
									</Button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</Transition>

	<MoveTableDialog
		v-model="showMoveDialog"
		:pos-profile="posProfile"
		:source="moveSource"
		@moved="handleMoved"
	/>

	<SplitCheckDialog
		v-model="showSplitDialog"
		:order="splitOrder"
		:table="splitTable"
		:currency="currency"
		@split="handleSplit"
	/>

	<TableChecksDialog
		v-model="showChecksDialog"
		:session="checksSession"
		:table="checksTable"
		:currency="currency"
		@open-check="handleOpenCheck"
		@changed="refresh(true)"
	/>
</template>

<script setup>
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { formatCurrency as fmtCurrency } from "@/utils/currency"
import { logger } from "@/utils/logger"
import MoveTableDialog from "@/components/tables/MoveTableDialog.vue"
import SplitCheckDialog from "@/components/tables/SplitCheckDialog.vue"
import TableChecksDialog from "@/components/tables/TableChecksDialog.vue"
import { Button } from "frappe-ui"
import { computed, onUnmounted, ref, watch } from "vue"

const log = logger.create("TableDashboard")
const { showError } = useToast()

/** How often the dashboard re-reads the floor from the server. */
const REFRESH_INTERVAL_MS = 30 * 1000
/** How often the on-card timers tick between refreshes. */
const TICK_INTERVAL_MS = 15 * 1000

const props = defineProps({
	modelValue: Boolean,
	posProfile: { type: String, default: null },
	currency: { type: String, default: null },
	/**
	 * Also list free tables, so this one screen can seat a table as well as watch
	 * the ones already ordering. Used when it stands in for the gate.
	 */
	pickerMode: { type: Boolean, default: false },
})

const emit = defineEmits([
	"update:modelValue",
	"open-table",
	"open-check",
	"seat-table",
	"free-table",
	"moved",
])

const show = computed({
	get: () => props.modelValue,
	set: (value) => emit("update:modelValue", value),
})

// -----------------------------------------------------------------------------
// State
// -----------------------------------------------------------------------------

const tables = ref([])
const thresholds = ref({ warning: 0, late: 0 })
const loading = ref(false)
const errorMessage = ref("")
const openingSession = ref(null)
const QUICK_GUESTS = [1, 2, 4, 6, 8]

// Which free table is mid-seating, so its card shows the guest counter instead
// of opening a second dialog on top of this one.
const seatingTable = ref(null)
const seatGuests = ref(1)
const seatingBusy = ref(false)

// Which seated card is asking to be freed
const freeingTable = ref(null)
const freeingBusy = ref(false)

const showMoveDialog = ref(false)
const moveSource = ref(null)
const showSplitDialog = ref(false)
const splitOrder = ref(null)
const splitTable = ref(null)
const showChecksDialog = ref(false)
const checksSession = ref(null)
const checksTable = ref(null)
const lastRefreshedAt = ref(null)

/**
 * Wall-clock reference for the live timers.
 *
 * The server sends each table's idle/seated minutes at fetch time; between
 * refreshes we add the time elapsed locally rather than re-deriving from
 * timestamps, which keeps the timers free of timezone and clock-skew bugs.
 */
const now = ref(Date.now())
let refreshTimer = null
let tickTimer = null

const sortedTables = computed(() =>
	// Always in table-number order, so a table sits where the cashier expects it
	// on the floor. Urgency is carried by the card colour and the counts in the
	// summary strip, which is what a sort by idle time used to convey - at the
	// cost of tables moving around between refreshes.
	[...tables.value].sort((a, b) =>
		String(a.table_number).localeCompare(String(b.table_number), undefined, {
			numeric: true,
		}),
	),
)

const summaryStats = computed(() => {
	// Free tables are choices, not activity - counting them would make every
	// figure on this strip wrong.
	const list = tables.value.filter((t) => t.seated)
	const guests = list.reduce((sum, t) => sum + (Number(t.guest_count) || 0), 0)
	const amount = list.reduce((sum, t) => sum + (Number(t.total_amount) || 0), 0)
	const noOrder = list.filter((t) => !t.has_order).length
	const late = list.filter((t) => t.idle_state === "late").length
	const warning = list.filter((t) => t.idle_state === "warning").length

	return [
		{
			key: "tables",
			label: __("Open tables"),
			value: list.length,
			border: "border-gray-200",
			text: "text-gray-900",
		},
		{
			key: "guests",
			label: __("Guests"),
			value: guests,
			border: "border-gray-200",
			text: "text-gray-900",
		},
		{
			key: "amount",
			label: __("Open total"),
			value: formatCurrency(amount),
			border: "border-gray-200",
			text: "text-gray-900",
		},
		{
			key: "no_order",
			label: __("No order"),
			value: noOrder,
			border: "border-gray-200",
			text: "text-gray-700",
			dot: "bg-gray-300",
		},
		{
			key: "warning",
			label: __("Waiting"),
			value: warning,
			border: "border-amber-200",
			text: "text-amber-700",
			dot: "bg-amber-500",
		},
		{
			key: "late",
			label: __("Late"),
			value: late,
			border: "border-red-200",
			text: "text-red-700",
			dot: "bg-red-500",
		},
	]
})

const lastRefreshedLabel = computed(() => {
	if (!lastRefreshedAt.value) return ""
	const seconds = Math.floor((now.value - lastRefreshedAt.value) / 1000)
	if (seconds < 10) return __("just now")
	if (seconds < 60) return __("{0}s ago", [seconds])
	return __("{0}m ago", [Math.floor(seconds / 60)])
})

// -----------------------------------------------------------------------------
// Live timers
// -----------------------------------------------------------------------------

/** Minutes elapsed locally since the last server read. */
function elapsedMinutes() {
	if (!lastRefreshedAt.value) return 0
	return Math.floor((now.value - lastRefreshedAt.value) / 60000)
}

function liveIdleMinutes(table) {
	return (Number(table.idle_minutes) || 0) + elapsedMinutes()
}

function liveSeatedMinutes(table) {
	return (Number(table.seated_minutes) || 0) + elapsedMinutes()
}

/**
 * Re-evaluate the colour band against the live timer, so a table crosses into
 * amber or red between refreshes instead of waiting for the next fetch.
 */
function liveIdleState(table) {
	const idle = liveIdleMinutes(table)
	const { warning, late } = thresholds.value
	if (late && idle >= late) return "late"
	if (warning && idle >= warning) return "warning"
	return "ok"
}

const CARD_STYLES = {
	late: {
		border: "border-red-300",
		header: "bg-red-50",
		badge: "bg-red-100 text-red-700",
		text: "text-red-700",
	},
	warning: {
		border: "border-amber-300",
		header: "bg-amber-50",
		badge: "bg-amber-100 text-amber-700",
		text: "text-amber-700",
	},
	ok: {
		border: "border-gray-200",
		header: "bg-white",
		badge: "bg-gray-100 text-gray-600",
		text: "text-gray-600",
	},
	free: {
		border: "border-dashed border-gray-300",
		header: "bg-gray-50/60",
		badge: "bg-emerald-50 text-emerald-700",
		text: "text-gray-500",
	},
}

function cardClasses(table) {
	if (!table.seated) return CARD_STYLES.free
	return CARD_STYLES[liveIdleState(table)] || CARD_STYLES.ok
}

function startSeating(table) {
	seatingTable.value = table.table
	// Capacity is the most likely head count, and is one tap to change
	seatGuests.value = Number(table.seating_capacity) > 0 ? Number(table.seating_capacity) : 1
}

function cancelSeating() {
	seatingTable.value = null
}

function stepSeatGuests(delta) {
	seatGuests.value = Math.max(1, (Number(seatGuests.value) || 0) + delta)
}

function normalizeSeatGuests() {
	seatGuests.value = Math.max(1, Math.floor(Number(seatGuests.value) || 0))
}

async function confirmSeating(table) {
	normalizeSeatGuests()
	seatingBusy.value = true
	try {
		emit("seat-table", {
			table: table.table,
			tableNumber: table.table_number,
			guestCount: seatGuests.value,
		})
		seatingTable.value = null
		show.value = false
	} finally {
		seatingBusy.value = false
	}
}

// -----------------------------------------------------------------------------
// Formatting
// -----------------------------------------------------------------------------

function formatCurrency(value) {
	// Pass undefined rather than null when unset: the util's default parameter
	// only kicks in for undefined, and a null currency loses the symbol.
	return fmtCurrency(Number(value) || 0, props.currency || undefined)
}

function formatQty(value) {
	const qty = Number(value) || 0
	return Number.isInteger(qty) ? String(qty) : qty.toFixed(2)
}

function formatMinutes(minutes) {
	const total = Math.max(0, Math.floor(Number(minutes) || 0))
	if (total < 60) return __("{0}m", [total])
	const hours = Math.floor(total / 60)
	const rest = total % 60
	return rest ? __("{0}h {1}m", [hours, rest]) : __("{0}h", [hours])
}

// -----------------------------------------------------------------------------
// Data
// -----------------------------------------------------------------------------

async function refresh(showSpinner = false) {
	if (showSpinner || tables.value.length === 0) loading.value = true

	try {
		const data = await call("ecs_posnext.api.table_orders.get_open_tables", {
			pos_profile: props.posProfile,
			include_free: props.pickerMode ? 1 : 0,
		})
		tables.value = data?.tables || []
		thresholds.value = data?.thresholds || { warning: 0, late: 0 }
		lastRefreshedAt.value = Date.now()
		now.value = Date.now()
		errorMessage.value = ""
	} catch (error) {
		log.error("Failed to load open tables", error)
		// Keep the last good view on a transient failure; only a first-load
		// failure leaves the cashier with nothing, so surface it then.
		if (tables.value.length === 0) {
			errorMessage.value =
				error?.messages?.[0] || error?.message || __("Failed to load open tables")
		}
	} finally {
		loading.value = false
	}
}

function startPolling() {
	stopPolling()
	refreshTimer = setInterval(() => refresh(), REFRESH_INTERVAL_MS)
	tickTimer = setInterval(() => {
		now.value = Date.now()
	}, TICK_INTERVAL_MS)
}

function stopPolling() {
	if (refreshTimer) {
		clearInterval(refreshTimer)
		refreshTimer = null
	}
	if (tickTimer) {
		clearInterval(tickTimer)
		tickTimer = null
	}
}

function handleClose() {
	show.value = false
}

function handleSplitTable(table) {
	splitOrder.value = table.order
	splitTable.value = table.table_number || table.table
	showSplitDialog.value = true
}

function handleViewChecks(table) {
	checksSession.value = table.session
	checksTable.value = table.table_number || table.table
	showChecksDialog.value = true
}

async function handleSplit() {
	// Splitting replaces one order with several, so re-read rather than patching
	await refresh(true)
}

function handleOpenCheck(check) {
	emit("open-check", check)
	showChecksDialog.value = false
	show.value = false
}

async function confirmFreeTable(table) {
	freeingBusy.value = true
	try {
		emit("free-table", table)
		freeingTable.value = null
		await refresh(true)
	} finally {
		freeingBusy.value = false
	}
}

function handleMoveTable(table) {
	moveSource.value = table
	showMoveDialog.value = true
}

/**
 * A move changes which tables are open, so re-read rather than patching the
 * local rows - a merge closes one table and grows another.
 */
async function handleMoved(result) {
	await refresh(true)
	emit("moved", result)
}

async function handleOpenTable(table) {
	openingSession.value = table.session
	try {
		emit("open-table", table)
		show.value = false
	} catch (error) {
		log.error("Failed to open table", error)
		showError(error?.message || __("Failed to open the table"))
	} finally {
		openingSession.value = null
	}
}

// Poll only while the dashboard is actually on screen
watch(
	() => props.modelValue,
	(isOpen) => {
		if (isOpen) {
			seatingTable.value = null
			freeingTable.value = null
			refresh(true)
			startPolling()
		} else {
			stopPolling()
		}
	},
	{ immediate: true },
)

onUnmounted(stopPolling)

defineExpose({ refresh })
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
