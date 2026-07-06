<template>
	<Dialog v-model="show" :options="{ title: __('Tabby Payment Link'), size: 'sm' }">
		<template #body-content>
			<p class="text-xs text-gray-500 mb-3">
				{{ __("Ask the customer to scan the QR code or open the link to pay with Tabby.") }}
			</p>

			<div v-if="paymentUrl" class="flex flex-col items-center gap-3">
				<img
					:src="qrSrc"
					alt="Tabby QR"
					class="w-44 h-44 rounded-lg border border-gray-200 bg-white"
				/>

				<div class="w-full flex items-center gap-2">
					<input
						:value="paymentUrl"
						readonly
						class="flex-1 text-xs border border-gray-300 rounded-lg px-2 py-2 truncate bg-gray-50"
					/>
					<button
						type="button"
						class="text-xs font-semibold text-white bg-blue-600 rounded-lg px-3 py-2 hover:bg-blue-700"
						@click="copyLink"
					>
						{{ copied ? __("Copied") : __("Copy") }}
					</button>
				</div>

				<a
					:href="paymentUrl"
					target="_blank"
					rel="noopener"
					class="text-xs font-medium text-blue-600 hover:text-blue-800 underline"
				>
					{{ __("Open payment page") }}
				</a>

				<p v-if="smsSent" class="text-[11px] text-green-700">
					{{ __("Link sent by SMS to {0}", [mobile]) }}
				</p>
				<p v-else-if="mobile" class="text-[11px] text-amber-600">
					{{ __("SMS not sent — share the link manually.") }}
				</p>
			</div>

			<div class="mt-4">
				<button
					type="button"
					class="w-full text-sm font-semibold text-white bg-gray-800 rounded-lg py-2 hover:bg-gray-900"
					@click="close"
				>
					{{ __("Done") }}
				</button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Dialog } from "frappe-ui"
import { computed, ref } from "vue"

const props = defineProps({
	modelValue: Boolean,
	paymentUrl: String,
	smsSent: Boolean,
	mobile: String,
})

const emit = defineEmits(["update:modelValue"])

const copied = ref(false)

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

const qrSrc = computed(
	() =>
		`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(
			props.paymentUrl || "",
		)}`,
)

async function copyLink() {
	try {
		await navigator.clipboard.writeText(props.paymentUrl || "")
		copied.value = true
		setTimeout(() => {
			copied.value = false
		}, 1500)
	} catch (e) {
		console.error("Failed to copy link", e)
	}
}

function close() {
	emit("update:modelValue", false)
}
</script>
