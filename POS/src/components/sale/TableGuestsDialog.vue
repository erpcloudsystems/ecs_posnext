<template>
	<Dialog
		v-model="show"
		:options="{ title: dialogTitle, size: 'lg' }"
	>
		<template #body-content>
			<div class="flex flex-col gap-4 py-1">
				<!-- Offline: seating still works, it just syncs later -->
				<div
					v-if="isOffline"
					class="flex items-start gap-2 p-3 rounded-lg bg-blue-50 border border-blue-200"
				>
					<svg class="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072M3 3l8.293 8.293"/>
					</svg>
					<p class="text-xs text-blue-800">
						{{
							usingCachedTables
								? __("Offline - showing the last known table list. The table will sync when the connection returns.")
								: __("Offline - the table will sync when the connection returns.")
						}}
					</p>
				</div>

				<!-- No tables configured at all: explain the setup gap -->
				<div
					v-if="hasNoTables"
					class="flex items-start gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200"
				>
					<svg class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
					</svg>
					<p class="text-xs text-amber-800">
						{{ __("No tables are set up yet. Ask an administrator to add Table records, or turn off \"Require Table & Guest Count\" in POS Settings.") }}
					</p>
				</div>

				<!-- Table -->
				<div>
					<label class="text-sm font-medium text-gray-700 block mb-1.5">
						{{ __("Table") }}<span class="text-red-500 ms-0.5">*</span>
					</label>
					<div class="relative">
						<!-- Selected table -->
						<div v-if="selectedTable" class="relative">
							<div
								class="w-full min-h-12 px-3.5 pe-10 py-2.5 text-base border rounded-lg flex items-center gap-2"
								:class="
									selectedTableOccupied
										? 'border-amber-300 bg-amber-50'
										: 'border-blue-300 bg-blue-50'
								"
							>
								<span
									class="text-base font-semibold truncate"
									:class="selectedTableOccupied ? 'text-amber-900' : 'text-blue-800'"
								>
									{{ selectedTable.table_number }}
								</span>
								<span
									v-if="selectedTable.area"
									class="text-xs"
									:class="selectedTableOccupied ? 'text-amber-700' : 'text-blue-600'"
								>
									· {{ selectedTable.area }}
								</span>
								<span
									v-if="selectedTableOccupied"
									class="ms-auto text-[10px] font-bold uppercase tracking-wide text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded"
								>
									{{ __("Occupied") }}
								</span>
							</div>
							<button
								type="button"
								:aria-label="__('Clear table')"
								@mousedown.prevent="clearTable"
								class="absolute end-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 p-1"
							>
								<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2.5"
										d="M6 18L18 6M6 6l12 12"
									/>
								</svg>
							</button>
						</div>

						<!-- Search -->
						<div v-else>
							<input
								ref="searchInputRef"
								v-model="searchTerm"
								type="text"
								:placeholder="__('Search table...')"
								@focus="openDropdown"
								@blur="closeDropdown"
								@input="onSearchInput"
								class="w-full h-12 px-3.5 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
							/>
							<div
								v-if="dropdownOpen"
								class="absolute z-50 mt-1 w-full max-h-72 overflow-y-auto border border-gray-200 rounded-lg bg-white shadow-lg"
							>
								<div v-if="loadingTables" class="px-3 py-3 text-xs text-gray-500 text-center">
									{{ __("Loading...") }}
								</div>
								<template v-else-if="tables.length > 0">
									<div
										v-for="t in tables"
										:key="t.name"
										@mousedown.prevent="selectTable(t)"
										class="flex items-center gap-2 px-3.5 py-2.5 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
									>
										<span class="text-base font-medium text-gray-900">{{ t.table_number }}</span>
										<span v-if="t.area" class="text-sm text-gray-500">· {{ t.area }}</span>
										<span
											v-if="t.occupied"
											class="ms-auto text-[10px] font-bold uppercase tracking-wide text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded flex-shrink-0"
										>
											{{ __("Occupied") }}
										</span>
										<span
											v-else-if="t.seating_capacity"
											class="ms-auto text-[10px] text-gray-400 flex-shrink-0"
										>
											{{ __("Seats {0}", [t.seating_capacity]) }}
										</span>
									</div>
								</template>
								<div v-else class="px-3 py-3 text-xs text-gray-500 text-center">
									{{ __("No tables found") }}
								</div>
							</div>
						</div>
					</div>

					<!-- Resuming an order already open on this table -->
					<p v-if="selectedTableOccupied" class="text-xs text-amber-700 mt-1.5">
						{{ __("This table already has an open order - it will be resumed.") }}
					</p>
				</div>

				<!-- Guests -->
				<div>
					<label class="text-sm font-medium text-gray-700 block mb-1.5">
						{{ __("Number of Guests") }}<span class="text-red-500 ms-0.5">*</span>
					</label>
					<div class="flex items-center gap-2">
						<button
							type="button"
							:aria-label="__('Decrease guests')"
							:disabled="guestCount <= 1"
							@click="stepGuests(-1)"
							class="w-14 h-14 flex-shrink-0 rounded-lg border border-gray-300 text-gray-700 text-2xl font-semibold hover:bg-gray-50 active:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed touch-manipulation"
						>
							&minus;
						</button>
						<input
							v-model.number="guestCount"
							type="number"
							inputmode="numeric"
							min="1"
							:max="MAX_GUESTS"
							@blur="normalizeGuestCount"
							class="flex-1 h-14 px-3 text-center text-2xl font-semibold border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
						<button
							type="button"
							:aria-label="__('Increase guests')"
							:disabled="guestCount >= MAX_GUESTS"
							@click="stepGuests(1)"
							class="w-14 h-14 flex-shrink-0 rounded-lg border border-gray-300 text-gray-700 text-2xl font-semibold hover:bg-gray-50 active:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed touch-manipulation"
						>
							+
						</button>
					</div>

					<!-- Quick picks -->
					<div class="flex flex-wrap gap-1.5 mt-2">
						<button
							v-for="n in QUICK_GUESTS"
							:key="n"
							type="button"
							@click="guestCount = n"
							:class="[
								'px-4 py-2 text-sm font-semibold rounded-md border transition-colors touch-manipulation',
								guestCount === n
									? 'bg-blue-600 border-blue-600 text-white'
									: 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50',
							]"
						>
							{{ n }}
						</button>
					</div>

					<!-- Over capacity is allowed, but say so -->
					<p
						v-if="exceedsCapacity"
						class="text-xs text-amber-700 mt-1.5"
					>
						{{
							__("Table {0} seats {1}", [
								selectedTable.table_number,
								selectedTable.seating_capacity,
							])
						}}
					</p>
				</div>

				<p v-if="errorMessage" class="text-xs text-red-600">{{ errorMessage }}</p>
			</div>
		</template>

		<template #actions>
			<div class="flex gap-2 w-full">
				<Button
					class="flex-1"
					variant="subtle"
					:disabled="saving"
					@click="show = false"
				>
					{{ __("Cancel") }}
				</Button>
				<Button
					class="flex-1"
					variant="solid"
					theme="blue"
					:loading="saving"
					:disabled="!canConfirm"
					@click="confirm"
				>
					{{ isEditMode ? __("Update") : __("Start Order") }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { logger } from "@/utils/logger"
import { offlineState } from "@/utils/offline/offlineState"
import { generateUUID } from "@/utils/offline/uuid"
import { Button, Dialog } from "frappe-ui"
import { computed, nextTick, ref, watch } from "vue"

const log = logger.create("TableGuestsDialog")
const { showError } = useToast()

/**
 * Tables are cached so a table can still be seated with no network. The list is
 * tiny (a handful of rows per venue) and changes rarely, which makes
 * localStorage the right home for it.
 */
const TABLES_CACHE_KEY = "pos_tables_cache"

/**
 * Marks a session id that only exists on this device. Anything carrying it has
 * not reached the server yet, so the sync path knows to create it.
 */
const OFFLINE_SESSION_PREFIX = "pos_offline_session_"

const MAX_GUESTS = 999
const QUICK_GUESTS = [1, 2, 4, 6, 8, 10]
const SEARCH_DEBOUNCE_MS = 250

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	posProfile: { type: String, default: null },
	posOpeningShift: { type: String, default: null },
	/** Existing session being edited (from the header chip), if any. */
	session: { type: String, default: null },
	currentTable: { type: String, default: null },
	currentGuestCount: { type: Number, default: 0 },
})

const emit = defineEmits(["update:modelValue", "confirmed"])

const show = computed({
	get: () => props.modelValue,
	set: (value) => emit("update:modelValue", value),
})

const isEditMode = computed(() => Boolean(props.session))
const dialogTitle = computed(() =>
	isEditMode.value ? __("Table & Guests") : __("New Order"),
)

// -----------------------------------------------------------------------------
// State
// -----------------------------------------------------------------------------

const isOffline = ref(offlineState.isOffline)
const usingCachedTables = ref(false)

const tables = ref([])
const selectedTable = ref(null)
const guestCount = ref(1)
const searchTerm = ref("")
const searchInputRef = ref(null)
const dropdownOpen = ref(false)
const loadingTables = ref(false)
const tablesFetched = ref(false)
const saving = ref(false)
const errorMessage = ref("")

let searchTimer = null
let blurTimer = null

const selectedTableOccupied = computed(() => {
	if (!selectedTable.value) return false
	// Re-seating the table this order is already on isn't "occupied"
	if (selectedTable.value.name === props.currentTable) return false
	return Boolean(selectedTable.value.occupied)
})

const exceedsCapacity = computed(() => {
	const capacity = Number(selectedTable.value?.seating_capacity) || 0
	return capacity > 0 && guestCount.value > capacity
})

/**
 * True only when the Table doctype has no usable records at all - not merely when
 * a search came up empty. Surfaces a setup notice, so a profile with table service
 * on but no tables configured explains itself instead of looking broken.
 */
const hasNoTables = computed(
	() => tablesFetched.value && !searchTerm.value.trim() && tables.value.length === 0,
)

const canConfirm = computed(
	() => Boolean(selectedTable.value) && guestCount.value >= 1 && !saving.value,
)

// -----------------------------------------------------------------------------
// Table search
// -----------------------------------------------------------------------------

function cacheTables(rows) {
	try {
		localStorage.setItem(
			TABLES_CACHE_KEY,
			JSON.stringify(
				// Occupancy is a live fact - caching it would show stale "Occupied"
				// badges next time the cashier is offline, so it is stripped.
				rows.map(({ occupied, session, session_guest_count, ...rest }) => rest),
			),
		)
	} catch (error) {
		log.debug("Could not cache tables", error)
	}
}

function readCachedTables(term = "") {
	try {
		const cached = JSON.parse(localStorage.getItem(TABLES_CACHE_KEY) || "[]")
		if (!Array.isArray(cached)) return []
		const needle = term.trim().toLowerCase()
		if (!needle) return cached
		return cached.filter(
			(row) =>
				String(row.table_number || "").toLowerCase().includes(needle) ||
				String(row.area || "").toLowerCase().includes(needle),
		)
	} catch (error) {
		log.debug("Could not read cached tables", error)
		return []
	}
}

async function fetchTables(term = "") {
	loadingTables.value = true
	isOffline.value = offlineState.isOffline

	try {
		const result = await call("ecs_posnext.api.table_sessions.get_tables", {
			pos_profile: props.posProfile,
			search_term: term || null,
			limit: 50,
		})
		tables.value = result || []
		usingCachedTables.value = false
		tablesFetched.value = true
		if (!term) cacheTables(tables.value)
	} catch (error) {
		// Offline (or a server blip) must not block seating a table - fall back to
		// the cached list so the cashier can keep working.
		log.debug("Table fetch failed, falling back to cache", error)
		tables.value = readCachedTables(term)
		usingCachedTables.value = tables.value.length > 0
		tablesFetched.value = true
		isOffline.value = true
	} finally {
		loadingTables.value = false
	}
}

function onSearchInput() {
	dropdownOpen.value = true
	clearTimeout(searchTimer)
	searchTimer = setTimeout(() => fetchTables(searchTerm.value), SEARCH_DEBOUNCE_MS)
}

function openDropdown() {
	clearTimeout(blurTimer)
	dropdownOpen.value = true
	if (tables.value.length === 0) fetchTables(searchTerm.value)
}

function closeDropdown() {
	blurTimer = setTimeout(() => {
		dropdownOpen.value = false
	}, 150)
}

function selectTable(table) {
	selectedTable.value = table
	searchTerm.value = ""
	dropdownOpen.value = false
	errorMessage.value = ""

	// Picking an occupied table resumes its order, so show its head count
	if (table.occupied && table.session_guest_count) {
		guestCount.value = table.session_guest_count
	} else if (!isEditMode.value && table.seating_capacity > 0 && guestCount.value === 1) {
		// Seating capacity is the most likely head count for a fresh order
		guestCount.value = table.seating_capacity
	}
}

function clearTable() {
	selectedTable.value = null
	searchTerm.value = ""
	nextTick(() => searchInputRef.value?.focus())
}

// -----------------------------------------------------------------------------
// Guest count
// -----------------------------------------------------------------------------

function stepGuests(delta) {
	const next = (Number(guestCount.value) || 0) + delta
	guestCount.value = Math.min(MAX_GUESTS, Math.max(1, next))
}

function normalizeGuestCount() {
	const value = Math.floor(Number(guestCount.value) || 0)
	guestCount.value = Math.min(MAX_GUESTS, Math.max(1, value))
}

// -----------------------------------------------------------------------------
// Confirm
// -----------------------------------------------------------------------------

async function confirm() {
	normalizeGuestCount()

	if (!selectedTable.value) {
		errorMessage.value = __("Please select a table")
		return
	}

	saving.value = true
	errorMessage.value = ""

	try {
		// ---------------------------------------------------------------------
		// Offline: seat the table locally.
		//
		// The session gets a client-generated id and is created on the server
		// later, when the held order syncs. `opened_at` is stamped now so the
		// dashboard eventually shows how long the guests have really been seated.
		// ---------------------------------------------------------------------
		if (offlineState.isOffline) {
			const offlineSession = props.session?.startsWith(OFFLINE_SESSION_PREFIX)
				? props.session
				: `${OFFLINE_SESSION_PREFIX}${generateUUID()}`

			emit("confirmed", {
				session: offlineSession,
				table: selectedTable.value.name,
				tableNumber: selectedTable.value.table_number || selectedTable.value.name,
				guestCount: guestCount.value,
				resumed: false,
				offline: true,
				openedAt: new Date().toISOString(),
			})

			show.value = false
			return
		}

		let session

		if (isEditMode.value) {
			session = await call("ecs_posnext.api.table_sessions.update_table_session", {
				session: props.session,
				table: selectedTable.value.name,
				guest_count: guestCount.value,
			})
		} else {
			session = await call("ecs_posnext.api.table_sessions.start_table_session", {
				table: selectedTable.value.name,
				guest_count: guestCount.value,
				pos_profile: props.posProfile,
				pos_opening_shift: props.posOpeningShift,
			})
		}

		emit("confirmed", {
			session: session.name,
			table: session.table,
			tableNumber: selectedTable.value.table_number || session.table,
			guestCount: session.guest_count,
			resumed: Boolean(session.resumed),
		})

		show.value = false
	} catch (error) {
		log.error("Failed to save table session", error)
		const message =
			error?.messages?.[0] || error?.message || __("Failed to start the order")
		errorMessage.value = message
		showError(message)
	} finally {
		saving.value = false
	}
}

// -----------------------------------------------------------------------------
// Open / close
// -----------------------------------------------------------------------------

watch(
	() => props.modelValue,
	async (isOpen) => {
		if (!isOpen) {
			dropdownOpen.value = false
			clearTimeout(searchTimer)
			clearTimeout(blurTimer)
			return
		}

		errorMessage.value = ""
		searchTerm.value = ""
		tablesFetched.value = false
		guestCount.value = props.currentGuestCount > 0 ? props.currentGuestCount : 1

		await fetchTables()

		// Pre-select the order's current table when editing
		selectedTable.value = props.currentTable
			? tables.value.find((t) => t.name === props.currentTable) || {
					name: props.currentTable,
					table_number: props.currentTable,
				}
			: null

		if (!selectedTable.value) {
			nextTick(() => searchInputRef.value?.focus())
		}
	},
	{ immediate: true },
)
</script>
