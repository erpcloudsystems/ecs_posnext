<template>
	<Dialog
		v-model="showDialog"
		:options="{ title: __('Update Mode of Payment'), size: 'lg' }"
	>
		<template #body-content>
			<div class="flex flex-col gap-4">
				<div v-if="optionsResource.loading" class="text-center py-8">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
					<p class="mt-3 text-xs text-gray-500">{{ __('Loading payment details...') }}</p>
				</div>

				<template v-else>
					<!-- Invoice summary -->
					<div class="bg-gray-50 border border-gray-200 rounded-lg p-3 flex items-start justify-between gap-3">
						<div class="min-w-0">
							<p class="text-sm font-semibold text-gray-900 text-start">{{ invoiceName }}</p>
							<p class="text-xs text-gray-600 text-start">
								{{ __('Paid by') }}: {{ currentModesLabel || __('No payment') }}
							</p>
						</div>
						<p class="text-sm font-bold text-gray-900 text-end flex-shrink-0">
							{{ formatCurrency(options.grand_total) }}
						</p>
					</div>

					<!-- Server said this invoice cannot be corrected -->
					<div
						v-if="blockReason"
						class="bg-orange-50 border border-orange-200 rounded-lg p-3 text-xs text-orange-800 text-start"
					>
						{{ blockReason }}
					</div>

					<template v-else>
						<p class="text-xs text-gray-500 text-start">
							{{ __('The invoice is cancelled and re-issued with the selected mode of payment. Its payment entry and bank commission entry are rebuilt accordingly.') }}
						</p>

						<div class="flex flex-col gap-2">
							<label
								v-for="mode in selectableModes"
								:key="mode.mode_of_payment"
								class="flex items-center gap-3 border rounded-lg p-3 cursor-pointer transition-colors"
								:class="selectedMode === mode.mode_of_payment
									? 'border-blue-500 bg-blue-50'
									: 'border-gray-200 hover:border-gray-300'"
							>
								<input
									type="radio"
									name="mode-of-payment"
									class="text-blue-600"
									:value="mode.mode_of_payment"
									v-model="selectedMode"
								/>
								<span class="text-sm font-medium text-gray-900">{{ mode.mode_of_payment }}</span>
							</label>

							<p v-if="selectableModes.length === 0" class="text-xs text-gray-500 text-start">
								{{ __('No other mode of payment is available on this POS Profile') }}
							</p>
						</div>

						<div
							v-if="submitError"
							class="bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-800 text-start"
						>
							{{ submitError }}
						</div>
					</template>
				</template>
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button variant="subtle" @click="showDialog = false">
					{{ __('Cancel') }}
				</Button>
				<Button
					v-if="!blockReason"
					variant="solid"
					:disabled="!selectedMode || isSubmitting"
					:loading="isSubmitting"
					@click="confirmUpdate"
				>
					{{ __('Update') }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { useToast } from "@/composables/useToast"
import {
	DEFAULT_CURRENCY,
	formatCurrency as formatCurrencyUtil,
} from "@/utils/currency"
import { Button, Dialog, createResource } from "frappe-ui"
import { computed, ref, watch } from "vue"

const { showSuccess } = useToast()

const props = defineProps({
	modelValue: Boolean,
	invoice: { type: Object, default: null },
	currency: { type: String, default: DEFAULT_CURRENCY },
})

const emit = defineEmits(["update:modelValue", "payment-mode-updated"])

const showDialog = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

const options = ref({})
const selectedMode = ref("")
const submitError = ref("")
const isSubmitting = ref(false)

const invoiceName = computed(
	() => props.invoice?.name || options.value.invoice || "",
)
const blockReason = computed(() =>
	options.value.allowed === false ? options.value.reason : "",
)

const currentModes = computed(() =>
	(options.value.current_payments || []).map((p) => p.mode_of_payment),
)
const currentModesLabel = computed(() => currentModes.value.join(", "))

// A single-mode invoice cannot be "switched" to the mode it already uses; a
// split payment can collapse onto any of them, so only exact matches are cut.
const selectableModes = computed(() =>
	(options.value.modes || []).filter(
		(mode) =>
			!(
				currentModes.value.length === 1 &&
				currentModes.value[0] === mode.mode_of_payment
			),
	),
)

function formatCurrency(amount) {
	return formatCurrencyUtil(Number.parseFloat(amount || 0), props.currency)
}

const optionsResource = createResource({
	url: "ecs_posnext.api.invoices.get_payment_mode_update_options",
	auto: false,
	onSuccess(data) {
		options.value = data || {}
		selectedMode.value = selectableModes.value[0]?.mode_of_payment || ""
	},
	onError(error) {
		options.value = { allowed: false, reason: extractErrorMessage(error) }
	},
})

const updateResource = createResource({
	url: "ecs_posnext.api.invoices.update_invoice_payment_mode",
	auto: false,
	onSuccess(data) {
		isSubmitting.value = false
		showSuccess(
			__("Invoice {0} re-issued as {1} paid by {2}", [
				data.cancelled_invoice,
				data.new_invoice,
				data.mode_of_payment,
			]),
		)
		emit("payment-mode-updated", data)
		showDialog.value = false
	},
	onError(error) {
		isSubmitting.value = false
		submitError.value = extractErrorMessage(error)
	},
})

watch(
	() => props.modelValue,
	(val) => {
		if (!val) return
		options.value = {}
		selectedMode.value = ""
		submitError.value = ""
		isSubmitting.value = false
		if (props.invoice?.name) {
			optionsResource.fetch({ invoice_name: props.invoice.name })
		}
	},
)

function confirmUpdate() {
	if (!selectedMode.value || isSubmitting.value) return
	submitError.value = ""
	isSubmitting.value = true
	updateResource.fetch({
		invoice_name: invoiceName.value,
		mode_of_payment: selectedMode.value,
	})
}

function extractErrorMessage(
	error,
	fallbackMessage = __("Failed to update mode of payment"),
) {
	if (!error) return fallbackMessage
	if (error.messages?.length) return error.messages.join(", ")

	if (error._server_messages) {
		try {
			const serverMessages = JSON.parse(error._server_messages)
			const firstMessage = serverMessages[0] && JSON.parse(serverMessages[0])
			if (firstMessage?.message) return firstMessage.message
		} catch (parseError) {
			// Ignore JSON parse errors, continue to other extraction methods
		}
	}

	if (error.message && error.message !== "ValidationError") return error.message
	return fallbackMessage
}
</script>
