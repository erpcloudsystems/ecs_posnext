<template>
	<Dialog
		:modelValue="state.open"
		@update:modelValue="(open) => !open && cancel()"
		:options="{ title: __('Supervisor Approval'), size: 'sm' }"
	>
		<template #body-content>
			<div class="flex flex-col gap-3 py-1">
				<div class="flex items-start gap-3 p-3 rounded-lg bg-amber-50 border border-amber-200">
					<svg class="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
					</svg>
					<div class="min-w-0">
						<p class="text-sm font-semibold text-amber-900">{{ state.reason }}</p>
						<p class="text-xs text-amber-700 mt-0.5">
							{{ __("This change needs the supervisor password.") }}
						</p>
					</div>
				</div>

				<div>
					<label class="text-sm font-medium text-gray-700 block mb-1.5">
						{{ __("Password") }}
					</label>
					<input
						ref="passwordInput"
						v-model="password"
						type="password"
						autocomplete="off"
						:disabled="state.verifying"
						:placeholder="__('Supervisor password')"
						@keyup.enter="confirm"
						class="w-full h-12 px-3.5 text-base border rounded-lg focus:outline-none focus:ring-2"
						:class="
							state.error
								? 'border-red-400 focus:ring-red-500'
								: 'border-gray-300 focus:ring-blue-500'
						"
					/>
					<p v-if="state.error" class="text-xs text-red-600 mt-1.5">{{ state.error }}</p>
				</div>
			</div>
		</template>

		<template #actions>
			<div class="flex gap-2 w-full">
				<Button class="flex-1" variant="subtle" :disabled="state.verifying" @click="cancel">
					{{ __("Cancel") }}
				</Button>
				<Button
					class="flex-1"
					variant="solid"
					theme="blue"
					:loading="state.verifying"
					@click="confirm"
				>
					{{ __("Approve") }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { useCheckEditApproval } from "@/composables/useCheckEditApproval"
import { Button, Dialog } from "frappe-ui"
import { nextTick, ref, watch } from "vue"

const { state, submit, cancel } = useCheckEditApproval()

const password = ref("")
const passwordInput = ref(null)

async function confirm() {
	if (state.verifying) return
	await submit(password.value)
	// A rejected attempt keeps the dialog open; clearing the box saves the
	// supervisor deleting it before trying again.
	if (state.open) password.value = ""
}

watch(
	() => state.open,
	async (open) => {
		if (!open) {
			password.value = ""
			return
		}
		await nextTick()
		passwordInput.value?.focus()
	},
)
</script>
