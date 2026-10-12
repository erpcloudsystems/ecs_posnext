<template>
	<Dialog v-model="show" :options="{ title: __('Checks'), size: '2xl' }">
		<template #body-content>
			<div class="flex flex-col gap-3 py-1">
				<div class="flex flex-wrap items-center justify-between gap-2">
					<p class="text-sm text-gray-600">
						{{ __("Table {0}", [table]) }}
					</p>
					<div class="flex items-center gap-2 text-xs">
						<span class="px-2 py-1 rounded bg-gray-100 text-gray-700 font-semibold">
							{{ __("total {0}", [money(data?.total_amount)]) }}
						</span>
						<span
							class="px-2 py-1 rounded font-semibold"
							:class="
								data?.open_count
									? 'bg-amber-100 text-amber-800'
									: 'bg-emerald-100 text-emerald-800'
							"
						>
							{{
								data?.open_count
									? __("{0} unpaid", [data.open_count])
									: __("all paid")
							}}
						</span>
					</div>
				</div>

				<div v-if="loading" class="py-10 text-center text-sm text-gray-500">
					{{ __("Loading...") }}
				</div>

				<div v-else-if="!data || data.checks.length === 0" class="py-10 text-center text-sm text-gray-500">
					{{ __("No checks on this table") }}
				</div>

				<div v-else class="flex flex-col gap-2 max-h-[55vh] overflow-y-auto">
					<div
						v-for="check in data.checks"
						:key="check.name"
						class="border-2 rounded-xl overflow-hidden"
						:class="check.status === 'Settled' ? 'border-emerald-200 bg-emerald-50/30' : 'border-gray-200 bg-white'"
					>
						<div class="px-3 py-2 flex items-center justify-between gap-2 border-b border-gray-100">
							<div class="flex items-center gap-2 min-w-0">
								<span class="text-sm font-bold text-gray-900">
									{{ check.check_number ? __("Check {0}", [check.check_number]) : __("Order") }}
								</span>
								<span
									v-if="check.room"
									class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800"
								>
									{{ __("Room {0}", [check.room]) }}
								</span>
								<span
									v-else
									class="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-500"
								>
									{{ __("no room") }}
								</span>
							</div>
							<div class="flex items-center gap-2 flex-shrink-0">
								<span class="text-sm font-bold text-gray-900">{{ money(check.total_amount) }}</span>
								<span
									class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide"
									:class="
										check.status === 'Settled'
											? 'bg-emerald-100 text-emerald-700'
											: 'bg-amber-100 text-amber-700'
									"
								>
									{{ check.status === "Settled" ? __("Paid") : __("Unpaid") }}
								</span>
							</div>
						</div>

						<div class="px-3 py-2 flex flex-col gap-0.5">
							<div
								v-for="line in check.items"
								:key="line.name"
								class="flex items-center gap-2 text-xs text-gray-700"
							>
								<span class="font-bold w-6 text-center flex-shrink-0">{{ formatQty(line.qty) }}</span>
								<span class="truncate flex-1">{{ line.item_name || line.item_code }}</span>
								<span class="text-gray-500 flex-shrink-0">{{ money(line.amount) }}</span>
							</div>
						</div>

						<div
							v-if="check.status === 'Open'"
							class="px-3 py-2 bg-gray-50 border-t border-gray-100 flex gap-2"
						>
							<Button
								class="flex-1"
								variant="solid"
								theme="blue"
								@click="emit('open-check', check)"
							>
								{{ __("Pay this check") }}
							</Button>
							<Button
								variant="subtle"
								:loading="savingRoom === check.name"
								:title="__('Charge to a room')"
								@click="startEditRoom(check)"
							>
								<template #icon>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
									</svg>
								</template>
							</Button>
						</div>

						<!-- Inline room change, so a mis-typed room can be fixed before paying -->
						<div v-if="editingRoom === check.name" class="px-3 py-2 bg-white border-t border-gray-100 flex gap-2">
							<div class="flex-1">
								<AutocompleteSelect
									:model-value="roomDraft || ''"
									:options="roomOptions"
									:placeholder="__('Charge to room...')"
									@update:model-value="(v) => (roomDraft = v || null)"
								/>
							</div>
							<Button variant="subtle" @click="editingRoom = null">{{ __("Cancel") }}</Button>
							<Button variant="solid" theme="blue" @click="saveRoom(check)">
								{{ __("Save") }}
							</Button>
						</div>

						<p
							v-else-if="check.external_reference"
							class="px-3 py-1.5 text-[10px] text-gray-500 bg-gray-50 border-t border-gray-100"
						>
							{{ __("Posted as {0}", [check.external_reference]) }}
						</p>
					</div>
				</div>

				<p v-if="errorMessage" class="text-xs text-red-600">{{ errorMessage }}</p>
			</div>
		</template>

		<template #actions>
			<Button class="w-full" variant="subtle" @click="show = false">
				{{ __("Close") }}
			</Button>
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
import { computed, ref, watch } from "vue"

const log = logger.create("TableChecksDialog")
const { showSuccess, showError } = useToast()

const props = defineProps({
	modelValue: Boolean,
	session: { type: String, default: null },
	table: { type: String, default: null },
	currency: { type: String, default: null },
})

const emit = defineEmits(["update:modelValue", "open-check", "changed"])

const show = computed({
	get: () => props.modelValue,
	set: (value) => emit("update:modelValue", value),
})

const data = ref(null)
const loading = ref(false)
const errorMessage = ref("")
const roomOptions = ref([])
const editingRoom = ref(null)
const roomDraft = ref(null)
const savingRoom = ref(null)

function money(value) {
	return formatCurrency(Number(value) || 0, props.currency || undefined)
}

function formatQty(value) {
	const qty = Number(value) || 0
	return Number.isInteger(qty) ? String(qty) : qty.toFixed(2)
}

async function load() {
	loading.value = true
	errorMessage.value = ""
	editingRoom.value = null
	try {
		const [checks, rooms] = await Promise.all([
			call("ecs_posnext.api.table_orders.get_table_checks", { session: props.session }),
			roomOptions.value.length
				? Promise.resolve(null)
				: call("frappe.client.get_list", {
						doctype: "Room",
						fields: ["name"],
						filters: { is_active: 1 },
						limit_page_length: 0,
						order_by: "name asc",
					}).catch(() => []),
		])
		data.value = checks
		if (rooms) roomOptions.value = (rooms || []).map((r) => ({ label: r.name, value: r.name }))
	} catch (error) {
		log.error("Failed to load checks", error)
		errorMessage.value =
			error?.messages?.[0] || error?.message || __("Failed to load the checks")
	} finally {
		loading.value = false
	}
}

function startEditRoom(check) {
	editingRoom.value = check.name
	roomDraft.value = check.room || null
}

async function saveRoom(check) {
	savingRoom.value = check.name
	try {
		await call("ecs_posnext.api.table_orders.set_check_room", {
			order: check.name,
			room: roomDraft.value || null,
		})
		showSuccess(
			roomDraft.value
				? __("Check charged to room {0}", [roomDraft.value])
				: __("Room cleared"),
		)
		editingRoom.value = null
		await load()
		emit("changed")
	} catch (error) {
		log.error("Failed to set the room", error)
		showError(error?.messages?.[0] || error?.message || __("Failed to set the room"))
	} finally {
		savingRoom.value = null
	}
}

watch(
	() => props.modelValue,
	(isOpen) => {
		if (isOpen && props.session) load()
	},
	{ immediate: true },
)
</script>
