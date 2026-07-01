<template>
	<div class="min-h-screen bg-gray-900 text-white flex flex-col" style="height: 100vh; overflow: hidden">

		<!-- Branch selector -->
		<div v-if="!selectedBranch" class="flex flex-col items-center justify-center flex-1 gap-8 p-8">
			<div class="text-center">
				<div class="text-5xl mb-4">📊</div>
				<h1 class="text-4xl font-bold">Live Orders</h1>
				<p class="text-gray-400 text-xl mt-2">Select a branch</p>
			</div>
			<div v-if="branchesLoading" class="text-gray-500 text-lg animate-pulse">Loading…</div>
			<div class="grid gap-4 w-full max-w-md">
				<button
					v-for="branch in branches"
					:key="branch"
					@click="selectBranch(branch)"
					class="py-5 px-8 rounded-xl text-2xl font-semibold bg-gray-700 hover:bg-indigo-600 active:scale-95 transition-all text-white shadow-lg"
				>
					{{ branch }}
				</button>
			</div>
			<button @click="$router.push('/')" class="text-gray-600 hover:text-gray-400 text-sm mt-4">← Back to POS</button>
		</div>

		<!-- Main view -->
		<template v-else>

			<!-- Header -->
			<header class="bg-gray-900 border-b border-gray-700 px-6 py-3 flex items-center justify-between shrink-0">
				<div class="flex items-center gap-4">
					<button @click="clearBranch" class="text-gray-400 hover:text-white text-sm px-3 py-1.5 rounded bg-gray-700 hover:bg-gray-600 transition-colors">
						← {{ __('Change Branch') }}
					</button>
					<div>
						<h1 class="text-2xl font-bold leading-none">{{ selectedBranch }} — {{ __('Live Orders') }}</h1>
					</div>
				</div>
				<div class="flex items-center gap-3">
					<div class="text-sm text-gray-400">
						{{ orders.length }} {{ __('orders') }}
						<span v-if="lateCount > 0" class="ml-1 text-red-400 font-bold animate-pulse">· {{ lateCount }} late</span>
					</div>
					<button @click="refresh" :disabled="loading" class="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50">
						<svg :class="['w-4 h-4', loading ? 'animate-spin' : '']" fill="none" viewBox="0 0 24 24">
							<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
						</svg>
						{{ __('Refresh') }}
					</button>
				</div>
			</header>

			<!-- Filter tab bar -->
			<div class="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center gap-2 shrink-0 overflow-x-auto">
				<button
					v-for="tab in tabs"
					:key="tab.key"
					@click="activeFilter = tab.key"
					class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors shrink-0"
					:class="activeFilter === tab.key
						? 'bg-white text-gray-900'
						: 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
				>
					{{ tab.label }}
					<span class="text-xs rounded-full px-1.5 py-0.5 font-bold"
						:class="activeFilter === tab.key ? 'bg-gray-200 text-gray-700' : 'bg-gray-600 text-gray-300'">
						{{ tab.count }}
					</span>
				</button>
			</div>

			<!-- Orders grid -->
			<div class="flex-1 overflow-y-auto p-4">
				<div v-if="gridItems.length === 0 && !loading" class="flex flex-col items-center justify-center h-64 text-gray-500">
					<div class="text-5xl mb-3">📋</div>
					<p class="text-xl">{{ __('No live orders') }}</p>
					<p class="text-sm mt-1 text-gray-600">{{ __('Orders will appear here as they are placed') }}</p>
				</div>

				<div class="grid gap-3 items-start" style="grid-template-columns: repeat(auto-fill, minmax(260px, 1fr))">
					<template v-for="item in gridItems" :key="item._key">

						<!-- ── Driver bundle card ── -->
						<div v-if="item._type === 'bundle'" class="rounded-xl overflow-hidden shadow-xl bg-gray-900 ring-1 ring-gray-600 flex flex-col">
							<!-- Bundle header -->
							<div class="bg-indigo-900 px-3 py-2 flex items-center justify-between">
								<div class="flex items-center gap-2">
									<div class="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center shrink-0">
										<span class="text-white font-black text-xs">{{ initials(item.driver_name) }}</span>
									</div>
									<div>
										<div class="text-white font-bold text-sm leading-none">{{ item.driver_name }}</div>
										<div class="text-indigo-300 text-xs mt-0.5">{{ item.orders.length }} orders · {{ daStatusLabel(item) }}</div>
									</div>
								</div>
								<div class="text-indigo-200 font-mono text-sm font-bold">{{ bundleTimer(item) }}</div>
							</div>
							<!-- Orders inside bundle -->
							<div class="divide-y divide-gray-800">
								<div
									v-for="order in item.orders"
									:key="order.name"
									class="px-3 py-2.5 flex items-start gap-2 cursor-pointer hover:bg-gray-800 transition-colors"
									@click="selectedOrder = order"
								>
									<!-- Status stripe -->
									<div class="w-1 self-stretch rounded-full shrink-0 mt-0.5" :class="cardHeaderClass(order)"></div>
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-1.5">
											<span class="text-white font-black text-lg leading-none">{{ order.custom_number_order || order.name }}</span>
											<span class="text-xs bg-gray-700 text-gray-300 rounded px-1 py-0.5">{{ order.custom_order_type }}</span>
											<span v-if="order.is_cod" class="text-xs text-amber-400 font-bold">💵</span>
											<span v-else class="text-xs text-green-400">✓</span>
										</div>
										<div class="text-gray-300 text-sm mt-0.5 truncate">{{ order.customer_name || order.customer }}</div>
										<div class="flex gap-1 mt-1 flex-wrap">
											<span class="text-xs px-1.5 py-0.5 rounded-full" :class="kdsChipClass(order.kds_status)">{{ order.kds_status }}</span>
										</div>
									</div>
									<div class="text-right shrink-0">
										<div class="text-sm font-mono font-bold" :class="isLate(order) ? 'text-red-300' : 'text-gray-400'">
											{{ elapsedLabel(order) }}
										</div>
										<div class="text-xs font-mono text-gray-400">{{ fmtCurrency(order.grand_total) }}</div>
									</div>
								</div>
							</div>
						</div>

						<!-- ── Single order card ── -->
						<div
							v-else
							@click="selectedOrder = item"
							class="rounded-xl overflow-hidden shadow-xl bg-gray-800 flex flex-col cursor-pointer transition-all hover:scale-[1.01]"
							:class="isLate(item) && ['kds_pending','kds_preparing'].includes(item.unified_status)
								? 'ring-2 ring-red-500' : 'ring-1 ring-gray-700'"
						>
							<!-- Color-coded header -->
							<div class="px-3 py-2.5 flex items-start justify-between gap-2" :class="cardHeaderClass(item)">
								<div class="min-w-0">
									<div class="text-2xl font-black tracking-tighter leading-none">
										{{ item.custom_number_order || item.name }}
									</div>
									<div class="text-xs opacity-80 mt-0.5">{{ unifiedStatusLabel(item) }}</div>
									<div class="text-sm font-medium mt-0.5 truncate opacity-90">{{ item.customer_name || item.customer }}</div>
								</div>
								<div class="text-right shrink-0">
									<span v-if="item.is_cod" class="text-xs font-bold bg-black/30 rounded px-1.5 py-0.5">💵 COD</span>
									<span v-else class="text-xs font-bold bg-black/30 rounded px-1.5 py-0.5">✓ Paid</span>
									<div class="text-lg font-mono font-bold mt-0.5 leading-none"
										:class="isLate(item) ? 'text-red-300' : 'text-white'">
										{{ elapsedLabel(item) }}
									</div>
									<div v-if="item.target_minutes" class="text-xs opacity-60">/ {{ item.target_minutes }}:00</div>
								</div>
							</div>

							<!-- Type + phone -->
							<div class="px-3 pt-2 flex flex-wrap gap-1">
								<span class="text-xs bg-gray-700 text-gray-300 rounded px-1.5 py-0.5 font-medium">{{ item.custom_order_type }}</span>
								<span v-if="item.contact_mobile" class="text-xs text-gray-500">📞 {{ item.contact_mobile }}</span>
							</div>
							<!-- Status chips -->
							<div class="px-3 pt-1 pb-1 flex flex-wrap gap-1">
								<span class="text-xs px-2 py-0.5 rounded-full font-medium" :class="kdsChipClass(item.kds_status)">
									KDS: {{ item.kds_status }}
								</span>
								<span v-if="item.da_status" class="text-xs px-2 py-0.5 rounded-full font-medium" :class="daChipClass(item.da_status)">
									{{ item.da_status }}
								</span>
							</div>

							<!-- Items preview -->
							<div class="flex-1 px-3 pb-2 space-y-0.5">
								<div v-for="(it, i) in (item.items || []).slice(0, 3)" :key="i"
									class="flex items-center justify-between">
									<span class="text-xs text-gray-300 truncate">{{ it.item_name }}</span>
									<span class="text-xs text-yellow-300 font-bold shrink-0 ml-1">×{{ it.qty }}</span>
								</div>
								<div v-if="(item.items || []).length > 3" class="text-xs text-gray-600">
									+{{ item.items.length - 3 }} more…
								</div>
							</div>
						</div>

					</template>
				</div>
			</div>

			<!-- ── Detail Modal ──────────────────────────────────────────────── -->
			<div v-if="selectedOrder"
				class="fixed inset-0 bg-black/70 flex items-end sm:items-center justify-center z-50"
				@click.self="selectedOrder = null">
				<div class="bg-gray-800 rounded-t-2xl sm:rounded-2xl shadow-2xl w-full max-w-lg mx-0 sm:mx-4 max-h-[90vh] overflow-y-auto text-white">

					<div class="px-5 pt-5 pb-3 border-b border-gray-700 flex items-start justify-between sticky top-0 bg-gray-800 z-10">
						<div>
							<div class="flex items-center gap-2 flex-wrap">
								<span class="text-3xl font-black">{{ selectedOrder.custom_number_order || selectedOrder.name }}</span>
								<span class="text-sm bg-gray-700 px-2 py-0.5 rounded font-medium">{{ selectedOrder.custom_order_type }}</span>
								<span v-if="selectedOrder.is_cod" class="text-xs bg-amber-900 text-amber-300 rounded px-2 py-0.5 font-bold">💵 COD</span>
								<span v-else class="text-xs bg-green-900 text-green-300 rounded px-2 py-0.5 font-bold">✓ Paid</span>
							</div>
							<div class="text-sm text-gray-400 mt-0.5">{{ selectedOrder.name }} · {{ fmtDateTime(selectedOrder.posting_datetime) }}</div>
						</div>
						<button @click="selectedOrder = null" class="text-gray-500 hover:text-white text-xl ml-3 shrink-0">✕</button>
					</div>

					<div class="px-5 py-4 space-y-5">

						<!-- Customer -->
						<div>
							<div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{{ __('Customer') }}</div>
							<div class="text-white font-medium text-lg">{{ selectedOrder.customer_name || selectedOrder.customer }}</div>
							<div v-if="selectedOrder.contact_mobile" class="text-gray-400 text-sm mt-0.5">📞 {{ selectedOrder.contact_mobile }}</div>
							<div class="text-gray-500 text-xs mt-1">{{ __('Created by') }}: {{ selectedOrder.owner_name || selectedOrder.owner }}</div>
						</div>

						<!-- Payment -->
						<div>
							<div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{{ __('Payment') }}</div>
							<div v-if="selectedOrder.is_cod" class="flex items-center gap-2">
								<span class="text-amber-400 font-bold">💵 COD</span>
								<span class="text-white font-mono font-bold">{{ fmtCurrency(selectedOrder.outstanding_amount) }}</span>
								<span class="text-gray-500 text-xs">({{ __('unpaid') }})</span>
							</div>
							<div v-else>
								<div class="text-green-400 text-xs font-semibold mb-1">✓ {{ __('Paid') }}</div>
								<div v-for="(p, i) in (selectedOrder.payments || [])" :key="i"
									class="flex justify-between text-sm text-gray-300 py-0.5">
									<span>{{ p.mode_of_payment }}</span>
									<span class="font-mono">{{ fmtCurrency(p.amount) }}</span>
								</div>
								<div v-if="!(selectedOrder.payments || []).length" class="text-sm text-gray-500">—</div>
							</div>
						</div>

						<!-- Items -->
						<div>
							<div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{{ __('Items') }}</div>
							<div v-for="(it, i) in (selectedOrder.items || [])" :key="i"
								class="flex items-center justify-between py-1 border-b border-gray-700 last:border-0">
								<span class="text-gray-200 text-sm">{{ it.item_name }}</span>
								<span class="text-yellow-300 font-bold text-sm ml-2">×{{ it.qty }}</span>
							</div>
						</div>

						<!-- Kitchen -->
						<div v-if="selectedOrder.kds_status !== 'No KDS'">
							<div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{{ __('Kitchen') }}</div>
							<div class="flex items-center gap-2 mb-2 flex-wrap">
								<span class="text-sm px-2 py-0.5 rounded font-medium" :class="kdsChipClass(selectedOrder.kds_status)">
									{{ kdsStatusIcon(selectedOrder.kds_status) }} {{ selectedOrder.kds_status }}
								</span>
								<span class="text-xs text-gray-500">
									{{ elapsedLabel(selectedOrder) }} elapsed
									<span v-if="selectedOrder.target_minutes"> / {{ selectedOrder.target_minutes }}:00 target</span>
								</span>
							</div>
							<div v-if="stationSummary(selectedOrder).length" class="space-y-1">
								<div v-for="(s, i) in stationSummary(selectedOrder)" :key="i"
									class="flex items-center justify-between text-xs bg-gray-700 rounded px-3 py-1.5">
									<span class="text-gray-300">{{ s.station }}</span>
									<span :class="s.all_ready ? 'text-green-400' : 'text-amber-400'">
										{{ s.all_ready ? '✓ Ready' : '⏳ Pending' }}
									</span>
								</div>
							</div>
						</div>

						<!-- Delivery -->
						<div v-if="selectedOrder.da_status">
							<div class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{{ __('Delivery') }}</div>
							<div class="space-y-1.5 text-sm">
								<div class="flex justify-between">
									<span class="text-gray-400">{{ __('Driver') }}</span>
									<span class="text-white font-medium">{{ selectedOrder.driver_name || '—' }}</span>
								</div>
								<div class="flex justify-between items-center">
									<span class="text-gray-400">{{ __('Status') }}</span>
									<span class="text-xs px-2 py-0.5 rounded-full font-bold" :class="daChipClass(selectedOrder.da_status)">{{ selectedOrder.da_status }}</span>
								</div>
								<div v-if="selectedOrder.delivery_address" class="flex justify-between gap-4">
									<span class="text-gray-400 shrink-0">{{ __('Address') }}</span>
									<span class="text-white text-right text-xs leading-snug">{{ selectedOrder.delivery_address }}</span>
								</div>
								<div v-if="selectedOrder.is_cod" class="flex justify-between">
									<span class="text-gray-400">{{ __('To Collect') }}</span>
									<span class="text-amber-300 font-mono font-bold">{{ fmtCurrency(selectedOrder.amount_to_collect) }}</span>
								</div>
							</div>
						</div>

						<!-- Grand total -->
						<div class="pt-1 border-t border-gray-700 flex justify-between items-center">
							<span class="text-gray-400 text-sm">{{ __('Total') }}</span>
							<span class="text-white font-mono font-bold text-lg">{{ fmtCurrency(selectedOrder.grand_total) }}</span>
						</div>
					</div>
				</div>
			</div>

		</template>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { useRoute } from "vue-router"
import { call } from "frappe-ui"
import { useToast } from "@/composables/useToast"
import { initSocket } from "@/socket"

const { showError } = useToast()
const route = useRoute()

const branches        = ref([])
const branchesLoading = ref(false)
const selectedBranch  = ref(route.query.branch || "")
const orders          = ref([])
const loading         = ref(false)
const timerTick       = ref(0)
const activeFilter    = ref("All")
const selectedOrder   = ref(null)

let timerInterval = null
let pollInterval  = null

function __(str) { return str }

// ── Branch selection ──────────────────────────────────────────────────────
async function loadBranches() {
	branchesLoading.value = true
	try {
		const result = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_branches")
		branches.value = (result || []).map(b => b.name)
	} catch { showError("Failed to load branches") }
	finally { branchesLoading.value = false }
}
function selectBranch(branch) { selectedBranch.value = branch }
function clearBranch() { selectedBranch.value = ""; orders.value = [] }

// ── Tabs ──────────────────────────────────────────────────────────────────
const ORDER_TYPES = ["Delivery", "Talabat", "Dine In", "Pickup"]

const filteredOrders = computed(() =>
	activeFilter.value === "All"
		? orders.value
		: orders.value.filter(o => o.custom_order_type === activeFilter.value)
)

const tabs = computed(() => [
	{ key: "All", label: "All", count: orders.value.length },
	...ORDER_TYPES.map(t => ({
		key: t, label: t,
		count: orders.value.filter(o => o.custom_order_type === t).length,
	})),
])

const lateCount = computed(() => orders.value.filter(o => isLate(o)).length)

// ── Grid items: bundles + singles ─────────────────────────────────────────
const gridItems = computed(() => {
	const visible = filteredOrders.value

	// Group orders that share a driver into bundles
	const driverOrders = {}
	for (const o of visible) {
		if (o.driver_name) {
			if (!driverOrders[o.driver_name]) driverOrders[o.driver_name] = []
			driverOrders[o.driver_name].push(o)
		}
	}

	// Drivers with 2+ orders → bundle; 1 order → treat as individual
	const bundledDrivers = new Set(
		Object.entries(driverOrders)
			.filter(([, list]) => list.length >= 2)
			.map(([name]) => name)
	)

	const emittedDrivers = new Set()
	const result = []

	for (const o of visible) {
		if (o.driver_name && bundledDrivers.has(o.driver_name)) {
			if (!emittedDrivers.has(o.driver_name)) {
				emittedDrivers.add(o.driver_name)
				const bundleOrders = driverOrders[o.driver_name]
				// Earliest assigned_at for timer
				const earliest = bundleOrders.reduce((min, x) => {
					const t = x.kds_order_time || x.posting_datetime
					return (!min || t < min) ? t : min
				}, null)
				result.push({
					_type: "bundle",
					_key: "bundle-" + o.driver_name,
					driver_name: o.driver_name,
					orders: bundleOrders,
					earliest_time: earliest,
					da_status: bundleOrders[0]?.da_status,
				})
			}
		} else {
			result.push({ _type: "single", _key: o.name, ...o })
		}
	}
	return result
})

// ── Card colors ───────────────────────────────────────────────────────────
const STATUS_HEADER_CLASS = {
	kds_pending:   "bg-gray-700",
	kds_preparing: "bg-amber-500",
	kds_ready:     "bg-blue-600",
	kds_completed: "bg-green-600",
	da_assigned:   "bg-blue-700",
	da_out:        "bg-indigo-600",
	da_problem:    "bg-red-700",
	no_kds:        "bg-green-700",
}
function cardHeaderClass(order) {
	return STATUS_HEADER_CLASS[order.unified_status] || "bg-gray-700"
}

const STATUS_LABEL = {
	kds_pending:   "⏳ Pending",
	kds_preparing: "🔥 Preparing",
	kds_ready:     "✓ Kitchen Ready",
	kds_completed: "✓ Completed",
	da_assigned:   "🚗 Driver Assigned",
	da_out:        "🏍 Out for Delivery",
	da_problem:    "⚠ Problem",
	no_kds:        "✓ Ready",
}
function unifiedStatusLabel(order) {
	return STATUS_LABEL[order.unified_status] || order.unified_status
}

function kdsChipClass(status) {
	return ({
		Completed: "bg-green-900 text-green-400",
		Ready:     "bg-blue-900 text-blue-300",
		Preparing: "bg-amber-900 text-amber-300",
		Pending:   "bg-gray-700 text-gray-400",
		"No KDS":  "bg-green-900 text-green-400",
	})[status] || "bg-gray-700 text-gray-400"
}
function daChipClass(status) {
	return ({
		"Assigned":           "bg-blue-900 text-blue-300",
		"Picked Up":          "bg-purple-900 text-purple-300",
		"Out for Delivery":   "bg-indigo-900 text-indigo-300",
		"Delivered":          "bg-green-900 text-green-300",
		"Returned":           "bg-red-900 text-red-300",
		"Failed":             "bg-red-900 text-red-300",
	})[status] || "bg-gray-700 text-gray-400"
}
function kdsStatusIcon(status) {
	return ({ Pending: "⏳", Preparing: "🔥", Ready: "✓", Completed: "✓" })[status] || ""
}

function daStatusLabel(bundle) {
	const s = bundle.da_status
	return s || ""
}

// ── Station summary ───────────────────────────────────────────────────────
function stationSummary(order) {
	const map = {}
	for (const item of order.kds_items || []) {
		if (!item.kds_station) continue
		if (!map[item.kds_station]) map[item.kds_station] = { station: item.kds_station, all_ready: true }
		if (item.station_status !== "Ready") map[item.kds_station].all_ready = false
	}
	return Object.values(map)
}

// ── Timer ─────────────────────────────────────────────────────────────────
function isLate(order) {
	timerTick.value
	const ot = order.kds_order_time || order.posting_datetime
	if (!ot || !order.target_minutes) return false
	return (Date.now() - new Date(ot)) / 60000 > order.target_minutes
}
function elapsedLabel(orderOrBundle) {
	timerTick.value
	const ot = orderOrBundle.kds_order_time || orderOrBundle.posting_datetime || orderOrBundle.earliest_time
	if (!ot) return "—"
	const elapsed = Date.now() - new Date(ot)
	const target  = ((orderOrBundle.target_minutes || 0)) * 60000
	const over = target && elapsed > target
	const src  = over ? elapsed - target : elapsed
	const mm = String(Math.floor(src / 60000)).padStart(2, "0")
	const ss = String(Math.floor((src % 60000) / 1000)).padStart(2, "0")
	return `${over ? "+" : ""}${mm}:${ss}`
}
function bundleTimer(bundle) { return elapsedLabel(bundle) }

// ── Helpers ───────────────────────────────────────────────────────────────
function initials(name) {
	if (!name) return "?"
	return name.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase()
}
function fmtCurrency(val) {
	if (val == null) return "—"
	return new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val)
}
function fmtDateTime(dt) {
	if (!dt) return ""
	try { return new Date(dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }
	catch { return "" }
}

// ── Data loading ──────────────────────────────────────────────────────────
async function loadOrders() {
	if (!selectedBranch.value) return
	try {
		orders.value = await call(
			"ecs_posnext.ecs_posnext.api.dispatcher.get_live_orders",
			{ branch: selectedBranch.value }
		) || []
	} catch (e) {
		showError(e?.messages?.[0] || e?.message || "Failed to load live orders")
		orders.value = []
	}
}
async function refresh() {
	loading.value = true
	try { await loadOrders() }
	finally { loading.value = false }
}

// ── Live tracking lifecycle ───────────────────────────────────────────────
function startLive() {
	stopLive()
	refresh()
	timerInterval = setInterval(() => { timerTick.value++ }, 1000)
	pollInterval  = setInterval(loadOrders, 30000)
	const socket = initSocket()
	if (socket) {
		socket.connect()
		socket.on("kds_update",            loadOrders)
		socket.on("dispatch_desk_refresh", loadOrders)
		socket.on("pos_order_changed",     loadOrders)
	}
}
function stopLive() {
	clearInterval(timerInterval)
	clearInterval(pollInterval)
	const socket = initSocket()
	if (socket) {
		socket.off("kds_update",            loadOrders)
		socket.off("dispatch_desk_refresh", loadOrders)
		socket.off("pos_order_changed",     loadOrders)
	}
}

watch(selectedBranch, val => { if (val) startLive(); else stopLive() })

onMounted(async () => {
	await loadBranches()
	if (selectedBranch.value) startLive()
})
onUnmounted(stopLive)
</script>
