<template>
	<Dialog v-model="show" :options="{ title: __('Split Check'), size: '4xl' }">
		<template #body-content>
			<div class="flex flex-col gap-3 py-1">
				<!-- Header: table + reconciliation state -->
				<div class="flex flex-wrap items-center justify-between gap-2">
					<p class="text-sm text-gray-600">
						{{ __("Table {0}", [table]) }}
						<span class="text-gray-400">·</span>
						{{ __("total {0}", [money(sourceTotal)]) }}
					</p>
					<div
						class="px-3 py-1.5 rounded-lg text-xs font-bold"
						:class="
							unassignedCount > 0
								? 'bg-amber-50 text-amber-800 border border-amber-300'
								: 'bg-emerald-50 text-emerald-800 border border-emerald-300'
						"
					>
						{{
							unassignedCount > 0
								? __("{0} items still unassigned", [formatQty(unassignedCount)])
								: __("All items assigned")
						}}
					</div>
				</div>

				<div class="flex flex-col lg:flex-row gap-3">
					<!-- Unassigned pool -->
					<div class="lg:w-1/3 flex-shrink-0 border-2 border-gray-200 rounded-xl overflow-hidden flex flex-col">
						<div class="px-3 py-2 bg-gray-50 border-b border-gray-200">
							<p class="text-xs font-bold text-gray-700 uppercase tracking-wide">
								{{ __("Unassigned") }}
							</p>
						</div>
						<div class="p-2 flex flex-col gap-1.5 max-h-[45vh] overflow-y-auto">
							<p
								v-if="unassignedLines.length === 0"
								class="text-xs text-gray-400 text-center py-6"
							>
								{{ __("Everything is assigned") }}
							</p>
							<button
								v-for="line in unassignedLines"
								:key="line.key"
								@click="assignOne(line.key)"
								:disabled="activeCheck === null"
								class="flex items-center gap-2 p-2 rounded-lg border border-gray-200 bg-white hover:border-blue-400 hover:bg-blue-50 active:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed text-start transition-colors touch-manipulation"
							>
								<span class="w-8 h-8 rounded-md bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-700 flex-shrink-0">
									{{ formatQty(line.remaining) }}
								</span>
								<span class="min-w-0 flex-1">
									<span class="block text-xs font-semibold text-gray-900 truncate">
										{{ line.item_name || line.item_code }}
									</span>
									<span class="block text-[10px] text-gray-500">
										{{ money(line.rate) }} · {{ line.uom }}
									</span>
								</span>
							</button>
						</div>
						<p
							v-if="activeCheck === null && unassignedLines.length > 0"
							class="px-3 py-2 text-[10px] text-amber-700 bg-amber-50 border-t border-amber-200"
						>
							{{ __("Pick a check on the right first, then tap items to add them.") }}
						</p>
					</div>

					<!-- Checks -->
					<div class="flex-1 min-w-0">
						<div class="flex items-center justify-between mb-2">
							<p class="text-xs font-bold text-gray-700 uppercase tracking-wide">
								{{ __("Checks") }}
							</p>
							<Button variant="subtle" @click="addCheck">
								<template #prefix>
									<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
									</svg>
								</template>
								{{ __("Add check") }}
							</Button>
						</div>

						<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2 max-h-[45vh] overflow-y-auto">
							<div
								v-for="(check, index) in checks"
								:key="index"
								@click="activeCheck = index"
								class="border-2 rounded-xl overflow-hidden flex flex-col cursor-pointer transition-colors"
								:class="
									activeCheck === index
										? 'border-blue-500 bg-blue-50/40'
										: 'border-gray-200 bg-white hover:border-gray-300'
								"
							>
								<div
									class="px-3 py-2 flex items-center justify-between gap-2 border-b"
									:class="activeCheck === index ? 'bg-blue-100/60 border-blue-200' : 'bg-gray-50 border-gray-200'"
								>
									<span class="text-xs font-bold text-gray-900">
										{{ __("Check {0}", [index + 1]) }}
									</span>
									<div class="flex items-center gap-1">
										<span class="text-xs font-bold text-gray-900">
											{{ money(checkTotal(check)) }}
										</span>
										<button
											v-if="checks.length > 2"
											@click.stop="removeCheck(index)"
											class="p-0.5 text-gray-400 hover:text-red-600"
											:aria-label="__('Remove check')"
										>
											<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
											</svg>
										</button>
									</div>
								</div>

								<!-- Room this check is charged to -->
								<div class="px-2 py-2 border-b border-gray-100">
									<AutocompleteSelect
										:model-value="check.room || ''"
										:options="roomOptions"
										:placeholder="__('Charge to room...')"
										@update:model-value="(v) => (check.room = v || null)"
										@click.stop
									/>
								</div>

								<div class="p-2 flex flex-col gap-1 min-h-[70px]">
									<p v-if="check.lines.length === 0" class="text-[10px] text-gray-400 text-center py-3">
										{{ __("Tap items on the left") }}
									</p>
									<div
										v-for="line in check.lines"
										:key="line.key"
										class="flex items-center gap-1.5 text-xs"
									>
										<button
											@click.stop="unassignOne(index, line.key)"
											class="w-5 h-5 rounded flex-shrink-0 bg-gray-100 hover:bg-red-100 hover:text-red-600 text-gray-600 flex items-center justify-center font-bold"
											:aria-label="__('Remove one')"
										>
											&minus;
										</button>
										<span class="font-bold text-gray-700 w-6 text-center flex-shrink-0">
											{{ formatQty(line.qty) }}
										</span>
										<span class="truncate flex-1 text-gray-800">
											{{ line.item_name || line.item_code }}
										</span>
									</div>
								</div>
							</div>
						</div>
					</div>
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
					theme="blue"
					:loading="saving"
					:disabled="!canSplit"
					@click="confirm"
				>
					{{ __("Split into {0} checks", [checks.length]) }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import AutocompleteSelect from "@/components/common/AutocompleteSelect.vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { formatCurrency } from "@/utils/currency"
import { logger } from "@/utils/logger"
import { Button, Dialog } from "frappe-ui"
import { computed, reactive, ref, watch } from "vue"

const log = logger.create("SplitCheckDialog")
const { showSuccess, showError } = useToast()

const props = defineProps({
	modelValue: Boolean,
	/** The POS Table Order being split. */
	order: { type: String, default: null },
	table: { type: String, default: null },
	currency: { type: String, default: null },
})

const emit = defineEmits(["update:modelValue", "split"])

const show = computed({
	get: () => props.modelValue,
	set: (value) => emit("update:modelValue", value),
})

/**
 * The source order's lines, keyed by item+uom.
 *
 * Quantities are tracked as a remaining pool rather than by moving objects
 * around: the server requires the split to reconcile exactly, so the UI has to
 * be able to prove nothing is left over.
 */
const sourceLines = ref([])
const checks = ref([])
const activeCheck = ref(null)
const loading = ref(false)
const saving = ref(false)
const errorMessage = ref("")
const roomOptions = ref([])

const sourceTotal = computed(() =>
	sourceLines.value.reduce((sum, l) => sum + l.qty * l.rate, 0),
)

/** How much of each line is still unassigned. */
const unassignedLines = computed(() =>
	sourceLines.value
		.map((line) => {
			const assigned = checks.value.reduce((sum, check) => {
				const found = check.lines.find((l) => l.key === line.key)
				return sum + (found ? found.qty : 0)
			}, 0)
			return { ...line, remaining: line.qty - assigned }
		})
		.filter((line) => line.remaining > 0.0000001),
)

const unassignedCount = computed(() =>
	unassignedLines.value.reduce((sum, l) => sum + l.remaining, 0),
)

const canSplit = computed(
	() =>
		!saving.value &&
		checks.value.length >= 2 &&
		unassignedCount.value <= 0.0000001 &&
		// An empty check would be rejected by the server anyway
		checks.value.every((c) => c.lines.length > 0),
)

function money(value) {
	return formatCurrency(Number(value) || 0, props.currency || undefined)
}

function formatQty(value) {
	const qty = Number(value) || 0
	return Number.isInteger(qty) ? String(qty) : qty.toFixed(2)
}

function checkTotal(check) {
	return check.lines.reduce((sum, l) => {
		const source = sourceLines.value.find((s) => s.key === l.key)
		return sum + l.qty * (source ? source.rate : 0)
	}, 0)
}

function addCheck() {
	checks.value.push(reactive({ room: null, lines: [] }))
	activeCheck.value = checks.value.length - 1
}

function removeCheck(index) {
	// Its lines return to the pool rather than vanishing
	checks.value.splice(index, 1)
	if (activeCheck.value >= checks.value.length) {
		activeCheck.value = checks.value.length ? checks.value.length - 1 : null
	}
}

function assignOne(key) {
	if (activeCheck.value === null) return

	const pool = unassignedLines.value.find((l) => l.key === key)
	if (!pool || pool.remaining <= 0) return

	const check = checks.value[activeCheck.value]
	const existing = check.lines.find((l) => l.key === key)
	if (existing) {
		existing.qty += 1 > pool.remaining ? pool.remaining : 1
	} else {
		check.lines.push({
			key,
			item_code: pool.item_code,
			item_name: pool.item_name,
			uom: pool.uom,
			qty: 1 > pool.remaining ? pool.remaining : 1,
		})
	}
	errorMessage.value = ""
}

function unassignOne(checkIndex, key) {
	const check = checks.value[checkIndex]
	const line = check.lines.find((l) => l.key === key)
	if (!line) return

	line.qty -= 1
	if (line.qty <= 0.0000001) {
		check.lines = check.lines.filter((l) => l.key !== key)
	}
	errorMessage.value = ""
}

async function loadOrder() {
	loading.value = true
	errorMessage.value = ""
	try {
		const [order, rooms] = await Promise.all([
			call("ecs_posnext.api.table_orders.get_table_order", { order: props.order }),
			call("frappe.client.get_list", {
				doctype: "Room",
				fields: ["name"],
				filters: { is_active: 1 },
				limit_page_length: 0,
				order_by: "name asc",
			}).catch(() => []),
		])

		roomOptions.value = (rooms || []).map((r) => ({ label: r.name, value: r.name }))

		sourceLines.value = (order?.items || []).map((item) => ({
			key: `${item.item_code}::${item.uom || ""}`,
			item_code: item.item_code,
			item_name: item.item_name,
			uom: item.uom,
			qty: Number(item.qty) || 0,
			rate: Number(item.rate) || 0,
		}))

		// Start with two checks, which is the smallest split there is
		checks.value = [reactive({ room: null, lines: [] }), reactive({ room: null, lines: [] })]
		activeCheck.value = 0
	} catch (error) {
		log.error("Failed to load the order", error)
		errorMessage.value =
			error?.messages?.[0] || error?.message || __("Failed to load the order")
	} finally {
		loading.value = false
	}
}

async function confirm() {
	saving.value = true
	errorMessage.value = ""
	try {
		const payload = checks.value.map((check) => ({
			room: check.room || null,
			items: check.lines.map((l) => ({
				item_code: l.item_code,
				uom: l.uom,
				qty: l.qty,
			})),
		}))

		const result = await call("ecs_posnext.api.table_orders.split_table_order", {
			order: props.order,
			checks: JSON.stringify(payload),
		})

		showSuccess(__("Split into {0} checks", [result.checks.length]))
		emit("split", result)
		show.value = false
	} catch (error) {
		log.error("Failed to split the order", error)
		const message =
			error?.messages?.[0] || error?.message || __("Failed to split the order")
		errorMessage.value = message
		showError(message)
	} finally {
		saving.value = false
	}
}

watch(
	() => props.modelValue,
	(isOpen) => {
		if (isOpen && props.order) loadOrder()
	},
	{ immediate: true },
)
</script>
