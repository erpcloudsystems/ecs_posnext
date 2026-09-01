<template>
	<Dialog v-model="show" :options="{ title: __('POS Attendance'), size: 'sm' }">
		<template #body-content>
			<div class="flex flex-col gap-2">
				<label class="block text-start text-sm font-medium text-gray-700">
					{{ __("Entries to Add") }}
				</label>
				<Input
					v-model="numberOfEntries"
					type="number"
					min="0"
					step="1"
					:placeholder="__('Enter number of entries to add')"
				/>
				<p class="text-start text-xs text-gray-500">
					{{ __("Current total: {0}", [count]) }}
				</p>
			</div>
		</template>

		<template #actions>
			<div class="flex gap-2">
				<Button
					variant="solid"
					@click="handleSave"
					:loading="loading"
					:disabled="numberOfEntries === '' || numberOfEntries === null"
				>
					{{ __("Save") }}
				</Button>
				<Button variant="subtle" @click="show = false">
					{{ __("Cancel") }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { useToast } from "@/composables/useToast"
import { Button, Dialog, Input } from "frappe-ui"
import { computed, ref, watch } from "vue"

const { showError } = useToast()

const props = defineProps({
	modelValue: Boolean,
	count: {
		type: Number,
		default: 0,
	},
	loading: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits(["update:modelValue", "save"])

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

const numberOfEntries = ref(0)

watch(
	() => props.modelValue,
	(isOpen) => {
		if (isOpen) {
			numberOfEntries.value = 0
		}
	}
)

async function handleSave() {
	const value = Number(numberOfEntries.value)
	if (Number.isNaN(value) || value < 0) {
		showError(__("Please enter a valid number of entries"))
		return
	}
	emit("save", value)
}
</script>
