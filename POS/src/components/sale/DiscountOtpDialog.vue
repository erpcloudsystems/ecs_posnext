<template>
	<Dialog v-model="show" :options="{ title: dialogTitle, size: 'sm' }">
		<template #body-content>
			<p class="text-xs text-gray-500 mb-3">
				{{ __("This action needs approval. Enter the OTP sent to the supervisors, or the authorization password.") }}
			</p>

			<input
				ref="otpInput"
				v-model="code"
				type="text"
				inputmode="numeric"
				autocomplete="one-time-code"
				:placeholder="__('Enter code')"
				class="w-full text-center tracking-widest text-lg border border-gray-300 rounded-lg px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
				@keyup.enter="submit"
			/>

			<p v-if="error" class="text-xs text-red-600 mb-2">{{ error }}</p>

			<div class="flex items-center justify-between mb-3">
				<button
					type="button"
					class="text-xs font-medium text-blue-600 hover:text-blue-800 disabled:opacity-50"
					:disabled="sending || cooldown > 0"
					@click="resend"
				>
					{{ cooldown > 0 ? __("Resend in {0}s", [cooldown]) : __("Resend code") }}
				</button>
				<span v-if="sending" class="text-[10px] text-gray-400">{{ __("Sending...") }}</span>
			</div>

			<div class="flex items-center gap-2">
				<button
					type="button"
					class="flex-1 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg py-2 hover:bg-gray-50"
					@click="close"
				>
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="flex-1 text-sm font-semibold text-white bg-blue-600 rounded-lg py-2 hover:bg-blue-700 disabled:opacity-50"
					:disabled="verifying || !code"
					@click="submit"
				>
					{{ verifying ? __("Checking...") : __("Authorize") }}
				</button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Dialog } from "frappe-ui"
import { computed, nextTick, ref, watch } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"

const props = defineProps({
	modelValue: Boolean,
	posProfile: String,
	// "discount" (default) or "return" — selects which OTP backend methods to call.
	context: { type: String, default: "discount" },
	// A short description (discount %/amount, or the return_against invoice) shown to
	// supervisors in the Telegram message.
	reference: [String, Number],
})

const emit = defineEmits(["update:modelValue", "authorized"])

const { showError } = useToast()

const isReturn = computed(() => props.context === "return")
const dialogTitle = computed(() =>
	isReturn.value ? __("Return Authorization") : __("Discount Authorization"),
)

const code = ref("")
const error = ref("")
const sending = ref(false)
const verifying = ref(false)
const cooldown = ref(0)
const otpInput = ref(null)
let cooldownTimer = null

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

function startCooldown(seconds = 30) {
	cooldown.value = seconds
	clearInterval(cooldownTimer)
	cooldownTimer = setInterval(() => {
		cooldown.value -= 1
		if (cooldown.value <= 0) clearInterval(cooldownTimer)
	}, 1000)
}

async function sendOtp() {
	sending.value = true
	try {
		const method = isReturn.value
			? "ecs_posnext.api.otp.send_return_otp"
			: "ecs_posnext.api.otp.send_discount_otp"
		const args = isReturn.value
			? { pos_profile: props.posProfile, return_against: props.reference }
			: { pos_profile: props.posProfile, discount: props.reference }
		const res = await call(method, args)
		const data = res?.message || res
		// Start the cooldown whether it was just sent or still within the cooldown window.
		startCooldown(30)
		return data
	} catch (e) {
		console.error("Failed to send discount OTP", e)
	} finally {
		sending.value = false
	}
}

function resend() {
	if (cooldown.value > 0 || sending.value) return
	sendOtp()
}

async function submit() {
	if (!code.value) return
	verifying.value = true
	error.value = ""
	try {
		const method = isReturn.value
			? "ecs_posnext.api.otp.verify_return_otp"
			: "ecs_posnext.api.otp.verify_discount_otp"
		const res = await call(method, {
			otp: code.value,
			pos_profile: props.posProfile,
		})
		const ok = res?.message ?? res
		if (ok) {
			emit("authorized")
		} else {
			error.value = __("Invalid or expired code")
		}
	} catch (e) {
		console.error("Failed to verify discount OTP", e)
		showError(__("Could not verify code"))
	} finally {
		verifying.value = false
	}
}

function close() {
	emit("update:modelValue", false)
}

// On open: reset + send the OTP automatically, then focus the input.
watch(
	() => props.modelValue,
	(open) => {
		if (open) {
			code.value = ""
			error.value = ""
			cooldown.value = 0
			sendOtp()
			nextTick(() => setTimeout(() => otpInput.value?.focus(), 100))
		}
	},
)
</script>
