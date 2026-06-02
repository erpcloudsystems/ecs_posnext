<template>
	<Dialog
		v-model="showDialog"
		:options="{ title: __('Password Required'), size: 'sm' }"
	>
		<template #body-content>
			<div class="flex flex-col items-center gap-4 py-2">
				<div class="w-14 h-14 rounded-full bg-amber-100 flex items-center justify-center">
					<svg class="w-7 h-7 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
					</svg>
				</div>
				<p class="text-sm text-gray-600 text-center">
					{{ __('Please enter your password to continue') }}
				</p>
				<div class="w-full">
					<input
						ref="passwordInput"
						v-model="password"
						type="password"
						:placeholder="__('Enter password')"
						class="w-full px-4 py-3 border border-gray-300 rounded-xl text-sm text-center focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						:class="{ 'border-red-400 focus:ring-red-500 focus:border-red-500': errorMessage }"
						@keydown.enter="verifyPassword"
						:disabled="isVerifying"
					/>
					<p v-if="errorMessage" class="text-xs text-red-600 mt-2 text-center">{{ errorMessage }}</p>
				</div>
			</div>
		</template>
		<template #actions>
			<div class="flex gap-2 w-full">
				<Button variant="subtle" @click="cancel" class="flex-1" :disabled="isVerifying">
					{{ __('Cancel') }}
				</Button>
				<Button
					variant="solid"
					theme="blue"
					@click="verifyPassword"
					:loading="isVerifying"
					:disabled="!password || isVerifying"
					class="flex-1"
				>
					{{ __('Confirm') }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Button, Dialog, createResource } from "frappe-ui"
import { computed, ref, watch, nextTick } from "vue"

const props = defineProps({
	modelValue: Boolean,
	posProfile: {
		type: String,
		default: "",
	},
})

const emit = defineEmits(["update:modelValue", "verified", "cancelled"])

const showDialog = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

const password = ref("")
const errorMessage = ref("")
const isVerifying = ref(false)
const passwordInput = ref(null)

const verifyResource = createResource({
	url: "ecs_posnext.api.utilities.verify_password",
	auto: false,
})

watch(
	() => props.modelValue,
	(val) => {
		if (val) {
			password.value = ""
			errorMessage.value = ""
			isVerifying.value = false
			nextTick(() => {
				passwordInput.value?.focus()
			})
		}
	},
)

async function verifyPassword() {
	if (!password.value || isVerifying.value) return

	isVerifying.value = true
	errorMessage.value = ""

	try {
		await verifyResource.submit({ password: password.value, pos_profile: props.posProfile })
		showDialog.value = false
		emit("verified")
	} catch (error) {
		errorMessage.value = __("Incorrect password")
		password.value = ""
		nextTick(() => {
			passwordInput.value?.focus()
		})
	} finally {
		isVerifying.value = false
	}
}

function cancel() {
	showDialog.value = false
	emit("cancelled")
}
</script>
