<template>
	<Dialog v-model="show" :options="{ title: __('Customer Comments'), size: 'md' }">
		<template #body-content>
			<div v-if="loading" class="py-8 text-center text-sm text-gray-500">{{ __("Loading...") }}</div>
			<div v-else class="py-2 space-y-4">
				<p v-if="customerLabel" class="text-xs text-gray-500">{{ customerLabel }}</p>
				<div>
					<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Permanent Comment") }}</label>
					<textarea
						:value="permanentComment"
						readonly
						rows="3"
						:placeholder="__('No permanent comment')"
						class="w-full px-2 py-1.5 text-sm border border-gray-200 rounded-lg bg-gray-100 text-gray-700 resize-none focus:outline-none"
					></textarea>
				</div>
				<div>
					<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Temporary Comment") }}</label>
					<textarea
						v-model="temporaryComment"
						rows="3"
						:placeholder="__('Write a temporary comment')"
						class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
					></textarea>
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex gap-2 w-full">
				<Button class="flex-1" variant="subtle" @click="show = false">{{ __("Cancel") }}</Button>
				<Button
					class="flex-1"
					variant="solid"
					theme="blue"
					:loading="saving"
					:disabled="loading"
					@click="save"
				>
					{{ __("Save") }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Button, Dialog } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { parseError } from "@/utils/errorHandler"

const props = defineProps({
	modelValue: Boolean,
	// Customer name (ID)
	customer: String,
	customerLabel: String,
})
const emit = defineEmits(["update:modelValue", "saved"])
const { showSuccess, showError } = useToast()

const show = computed({
	get: () => props.modelValue,
	set: (v) => emit("update:modelValue", v),
})

const loading = ref(false)
const saving = ref(false)
const permanentComment = ref("")
const temporaryComment = ref("")

async function load() {
	permanentComment.value = ""
	temporaryComment.value = ""
	if (!props.customer) return
	loading.value = true
	try {
		const res = await call("ecs_posnext.api.customers.get_customer_comments", { customer: props.customer })
		const data = res?.message || res || {}
		permanentComment.value = data.permanent_comment || ""
		temporaryComment.value = data.temporary_comment || ""
	} catch (e) {
		console.error("Load customer comments failed", e)
		showError(parseError(e).message || __("Error fetching comments"))
	} finally {
		loading.value = false
	}
}

async function save() {
	if (!props.customer || saving.value) return
	saving.value = true
	try {
		const res = await call("ecs_posnext.api.customers.save_customer_temporary_comment", {
			customer: props.customer,
			comment: temporaryComment.value,
		})
		const saved = (res?.message || res)?.temporary_comment ?? temporaryComment.value.trim()
		showSuccess(__("Comment saved successfully"))
		emit("saved", { permanent_comment: permanentComment.value, temporary_comment: saved })
		show.value = false
	} catch (e) {
		console.error("Save customer comment failed", e)
		showError(parseError(e).message || __("Error saving comment"))
	} finally {
		saving.value = false
	}
}

watch(
	() => props.modelValue,
	(open) => {
		if (open) load()
	},
)
</script>
