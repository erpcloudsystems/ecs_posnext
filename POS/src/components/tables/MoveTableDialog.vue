<template>
	<Dialog v-model="show" :options="{ title: __('Move Order'), size: 'lg' }">
		<template #body-content>
			<div class="flex flex-col gap-4 py-1">
				<!-- What is being moved -->
				<div class="flex items-center gap-3 p-3 rounded-lg bg-gray-50 border border-gray-200">
					<div class="w-11 h-11 rounded-lg bg-white border border-gray-200 flex items-center justify-center flex-shrink-0">
						<svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d="M4 10h16M6 10v9M18 10v9M3 10l1.5-4h15L21 10"/>
						</svg>
					</div>
					<div class="min-w-0">
						<p class="text-base font-bold text-gray-900 truncate">
							{{ __("Table {0}", [source?.table_number || source?.table]) }}
						</p>
						<p class="text-xs text-gray-500">
							{{ __("{0} guests", [source?.guest_count || 0]) }}
							<template v-if="source?.has_order">
								· {{ __("{0} items", [source.item_qty]) }}
							</template>
							<template v-else>· {{ __("no order yet") }}</template>
						</p>
					</div>
				</div>

				<!-- Destination -->
				<div>
					<label class="text-sm font-medium text-gray-700 block mb-1.5">
						{{ __("Move to") }}<span class="text-red-500 ms-0.5">*</span>
					</label>

					<input
						v-model="searchTerm"
						type="text"
						:placeholder="__('Search table...')"
						@input="onSearchInput"
						class="w-full h-12 px-3.5 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>

					<div v-if="loading" class="py-6 text-center text-sm text-gray-500">
						{{ __("Loading...") }}
					</div>

					<div
						v-else-if="selectableTables.length === 0"
						class="py-6 text-center text-sm text-gray-500"
					>
						{{ __("No other tables found") }}
					</div>

					<div v-else class="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-64 overflow-y-auto">
						<button
							v-for="t in selectableTables"
							:key="t.name"
							@click="target = t"
							:class="[
								'flex flex-col items-start p-3 rounded-lg border-2 text-start transition-colors touch-manipulation',
								target?.name === t.name
									? 'border-blue-500 bg-blue-50'
									: t.occupied
										? 'border-amber-200 bg-amber-50/40 hover:border-amber-400'
										: 'border-gray-200 bg-white hover:border-blue-300',
							]"
						>
							<span class="text-base font-bold text-gray-900 truncate w-full">
								{{ t.table_number }}
							</span>
							<span v-if="t.area" class="text-[10px] text-gray-500 truncate w-full">
								{{ t.area }}
							</span>
							<span
								v-if="t.occupied"
								class="mt-1 text-[10px] font-bold uppercase tracking-wide text-amber-700"
							>
								{{ __("Occupied") }}
							</span>
							<span v-else-if="t.seating_capacity" class="mt-1 text-[10px] text-gray-400">
								{{ __("Seats {0}", [t.seating_capacity]) }}
							</span>
						</button>
					</div>
				</div>

				<!-- Occupied destination: merging is a deliberate choice, not a default -->
				<div
					v-if="targetOccupied"
					class="flex flex-col gap-2 p-3 rounded-lg bg-amber-50 border border-amber-300"
				>
					<div class="flex items-start gap-2">
						<svg class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
						</svg>
						<p class="text-xs text-amber-800">
							{{
								__('Table {0} already has an open order. Moving here joins the two tables into one bill.', [
									target.table_number,
								])
							}}
						</p>
					</div>
					<label class="flex items-center gap-2 cursor-pointer">
						<input
							v-model="confirmMerge"
							type="checkbox"
							class="w-4 h-4 rounded border-amber-400 text-amber-600 focus:ring-amber-500"
						/>
						<span class="text-xs font-semibold text-amber-900">
							{{ __("Join the tables and combine the bills") }}
						</span>
					</label>
				</div>

				<p v-if="errorMessage" class="text-xs text-red-600">{{ errorMessage }}</p>
			</div>
		</template>

		<template #actions>
			<div class="flex gap-2 w-full">
				<Button class="flex-1" variant="subtle" :disabled="saving" @click="show = false">
					{{ __("Cancel") }}
				</Button>
				<Button
					class="flex-1"
					variant="solid"
					:theme="targetOccupied ? 'red' : 'blue'"
					:loading="saving"
					:disabled="!canMove"
					@click="confirm"
				>
					{{ targetOccupied ? __("Join Tables") : __("Move Order") }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { logger } from "@/utils/logger"
import { Button, Dialog } from "frappe-ui"
import { computed, ref, watch } from "vue"

const log = logger.create("MoveTableDialog")
const { showSuccess, showError } = useToast()

const SEARCH_DEBOUNCE_MS = 250

const props = defineProps({
	modelValue: Boolean,
	posProfile: { type: String, default: null },
	/** The dashboard row being moved. */
	source: { type: Object, default: null },
})

const emit = defineEmits(["update:modelValue", "moved"])

const show = computed({
	get: () => props.modelValue,
	set: (value) => emit("update:modelValue", value),
})

const tables = ref([])
const target = ref(null)
const searchTerm = ref("")
const loading = ref(false)
const saving = ref(false)
const confirmMerge = ref(false)
const errorMessage = ref("")

let searchTimer = null

/** Never offer the table the order is already on. */
const selectableTables = computed(() =>
	tables.value.filter((t) => t.name !== props.source?.table),
)

const targetOccupied = computed(() => Boolean(target.value?.occupied))

const canMove = computed(() => {
	if (!target.value || saving.value) return false
	// Joining bills must be ticked deliberately
	return targetOccupied.value ? confirmMerge.value : true
})

async function fetchTables(term = "") {
	loading.value = true
	try {
		const result = await call("ecs_posnext.api.table_sessions.get_tables", {
			pos_profile: props.posProfile,
			search_term: term || null,
			limit: 100,
		})
		tables.value = result || []
	} catch (error) {
		log.error("Failed to load tables", error)
		tables.value = []
	} finally {
		loading.value = false
	}
}

function onSearchInput() {
	clearTimeout(searchTimer)
	searchTimer = setTimeout(() => fetchTables(searchTerm.value), SEARCH_DEBOUNCE_MS)
}

async function confirm() {
	if (!target.value || !props.source?.session) return

	saving.value = true
	errorMessage.value = ""

	try {
		const result = await call("ecs_posnext.api.table_orders.move_table_session", {
			session: props.source.session,
			target_table: target.value.name,
			merge: targetOccupied.value && confirmMerge.value ? 1 : 0,
		})

		if (result?.status === "occupied") {
			// The destination filled up between loading the list and confirming
			errorMessage.value = __(
				"Table {0} now has an open order. Tick the join option to combine them.",
				[target.value.table_number],
			)
			target.value = { ...target.value, occupied: 1 }
			await fetchTables(searchTerm.value)
			return
		}

		if (result?.status === "merged") {
			showSuccess(
				__("Table {0} joined into table {1}", [
					result.source_table,
					result.target_table,
				]),
			)
		} else if (result?.status === "moved") {
			showSuccess(
				__("Order moved from table {0} to table {1}", [
					result.source_table,
					result.target_table,
				]),
			)
		}

		emit("moved", result)
		show.value = false
	} catch (error) {
		log.error("Failed to move the order", error)
		const message =
			error?.messages?.[0] || error?.message || __("Failed to move the order")
		errorMessage.value = message
		showError(message)
	} finally {
		saving.value = false
	}
}

watch(
	() => props.modelValue,
	(isOpen) => {
		if (!isOpen) {
			clearTimeout(searchTimer)
			return
		}
		target.value = null
		searchTerm.value = ""
		confirmMerge.value = false
		errorMessage.value = ""
		fetchTables()
	},
	{ immediate: true },
)

// Re-ticking is required for each new destination
watch(target, () => {
	confirmMerge.value = false
	errorMessage.value = ""
})
</script>
