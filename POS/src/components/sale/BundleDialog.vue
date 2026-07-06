<template>
	<Dialog v-model="show" :options="{ title: __('Choose Bundle Items'), size: 'lg' }">
		<template #body-content>
			<p class="text-xs text-gray-500 mb-3">
				{{ __("Select the components to include in {0}.", [bundleName]) }}
			</p>

			<div class="flex items-center justify-between mb-2">
				<button type="button" class="text-xs font-medium text-blue-600 hover:text-blue-800" @click="selectAll">
					{{ __("Select all") }}
				</button>
				<span class="text-[11px] text-gray-500">{{ selected.size }} / {{ components.length }} {{ __("selected") }}</span>
			</div>

			<div class="space-y-1.5 max-h-[55vh] overflow-y-auto">
				<label
					v-for="(c, i) in components"
					:key="c.item_code + ':' + i"
					class="flex items-center gap-3 rounded-lg border px-3 py-2 cursor-pointer"
					:class="selected.has(c.item_code) ? 'border-blue-300 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'"
				>
					<input type="checkbox" :checked="selected.has(c.item_code)" @change="toggle(c.item_code)" class="w-4 h-4" />
					<img v-if="c.image" :src="c.image" alt="" class="w-9 h-9 rounded object-cover border border-gray-200 bg-white flex-shrink-0" @error="c.image = ''" />
					<div class="flex-1 min-w-0">
						<div class="text-sm font-medium text-gray-800 truncate">{{ c.item_name || c.item_code }}</div>
						<div class="text-[11px] text-gray-500">{{ __("Qty") }}: {{ c.qty }} {{ c.uom || c.stock_uom }}</div>
					</div>
				</label>
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2 w-full">
				<Button variant="subtle" @click="cancel">{{ __("Cancel") }}</Button>
				<Button variant="solid" theme="blue" :disabled="selected.size === 0" @click="confirm">
					{{ __("Add to Cart") }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Button, Dialog } from "frappe-ui"
import { computed, ref, watch } from "vue"

const props = defineProps({
	modelValue: Boolean,
	bundleName: String,
	components: { type: Array, default: () => [] },
})

const emit = defineEmits(["update:modelValue", "confirm"])

const selected = ref(new Set())

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

function toggle(code) {
	const next = new Set(selected.value)
	if (next.has(code)) next.delete(code)
	else next.add(code)
	selected.value = next
}

function selectAll() {
	selected.value = new Set(props.components.map((c) => c.item_code))
}

function cancel() {
	emit("update:modelValue", false)
}

function confirm() {
	emit("confirm", [...selected.value])
	emit("update:modelValue", false)
}

// On open, pre-select components flagged default_item_in_pos (fallback: all).
watch(
	() => props.modelValue,
	(open) => {
		if (open) {
			const defaults = props.components.filter((c) => c.default_item_in_pos)
			const base = defaults.length ? defaults : props.components
			selected.value = new Set(base.map((c) => c.item_code))
		}
	},
)
</script>
