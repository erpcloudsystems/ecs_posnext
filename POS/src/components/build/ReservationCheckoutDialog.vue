<template>
	<Dialog v-model="show" :options="{ title: __('Review Reservation'), size: 'lg' }">
		<template #body-content>
			<div class="flex flex-col gap-4">
				<div class="bg-gray-50 rounded-lg p-3 text-sm text-gray-700 flex flex-col gap-1">
					<div><span class="text-gray-500">{{ __('Branch') }}:</span> {{ store.room || '-' }}</div>
					<div><span class="text-gray-500">{{ __('Visit Date') }}:</span> {{ store.visitDate || '-' }}</div>
				</div>

				<div class="flex flex-col divide-y divide-gray-100 border border-gray-200 rounded-lg">
					<div
						v-for="(item, index) in store.items"
						:key="index"
						class="flex items-center justify-between gap-2 px-3 py-2"
					>
						<div class="min-w-0">
							<div class="text-sm font-medium text-gray-900 truncate">{{ item.item_name }}</div>
							<div class="text-xs text-gray-500 truncate">
								{{ item.uom }}
								<span v-if="item.slot"> · {{ item.slot }}</span>
							</div>
						</div>
						<div class="flex items-center gap-2 flex-shrink-0">
							<input
								type="number"
								min="1"
								:value="item.qty"
								@change="store.updateQty(index, Number($event.target.value))"
								class="w-14 text-center text-sm border border-gray-300 rounded-lg px-1 py-1"
							/>
							<div class="text-sm font-semibold text-gray-900 w-20 text-end">
								{{ formatCurrencyCode(item.qty * item.rate, currency) }}
							</div>
							<button
								type="button"
								@click="store.removeItem(index)"
								class="text-gray-400 hover:text-red-600 p-1"
								:aria-label="__('Remove item')"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
							</button>
						</div>
					</div>
				</div>

				<div>
					<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Coupon Code') }}</label>
					<div v-if="!store.appliedCoupon" class="flex gap-2">
						<input
							v-model="couponCode"
							type="text"
							:placeholder="__('Enter coupon code')"
							@keyup.enter="applyCoupon"
							:disabled="applyingCoupon"
							class="flex-1 text-sm border border-gray-300 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
						<Button variant="outline" :loading="applyingCoupon" @click="applyCoupon">
							{{ __('Apply') }}
						</Button>
					</div>
					<div v-else class="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg px-3 py-2">
						<div class="text-sm text-green-800">
							<span class="font-semibold">{{ store.appliedCoupon.code }}</span>
							<span class="text-green-600"> -{{ formatCurrencyCode(store.appliedCoupon.amount, currency) }}</span>
						</div>
						<button type="button" @click="removeCoupon" class="text-green-700 hover:text-red-600 text-xs font-medium">
							{{ __('Remove') }}
						</button>
					</div>
					<div v-if="couponError" class="text-xs text-red-600 mt-1">{{ couponError }}</div>
				</div>

				<div class="flex flex-col gap-1 px-1">
					<div v-if="store.appliedCoupon" class="flex justify-between text-xs text-gray-500">
						<span>{{ __('Subtotal') }}</span>
						<span>{{ formatCurrencyCode(store.total, currency) }}</span>
					</div>
					<div v-if="store.appliedCoupon" class="flex justify-between text-xs text-green-600">
						<span>{{ __('Discount') }}</span>
						<span>-{{ formatCurrencyCode(store.appliedCoupon.amount, currency) }}</span>
					</div>
					<div class="flex justify-between text-sm font-semibold text-gray-900">
						<span>{{ __('Total') }}</span>
						<span>{{ formatCurrencyCode(netTotal, currency) }}</span>
					</div>
				</div>

				<div>
					<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Customer Phone Number') }}</label>
					<input
						v-model="store.phone"
						@blur="lookupCustomer"
						type="tel"
						:placeholder="__('Customer Phone Number')"
						class="w-full text-sm border border-gray-300 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
					<div v-if="store.customerLookup.checked" class="mt-1 text-xs">
						<span v-if="store.customerLookup.found" class="text-green-600">
							{{ __('Customer') }}: {{ store.customerLookup.customerName }}
						</span>
						<span v-else class="text-amber-600">{{ __('New customer — enter a name below') }}</span>
					</div>
				</div>

				<div v-if="store.customerLookup.checked && !store.customerLookup.found">
					<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Customer Name') }}</label>
					<input
						v-model="store.customerName"
						type="text"
						:placeholder="__('Full name')"
						class="w-full text-sm border border-gray-300 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
					/>
				</div>

				<div v-if="bookingError" class="text-xs text-red-600 bg-red-50 rounded px-2 py-1.5">
					{{ bookingError }}
				</div>
				<div v-if="bookingResult" class="text-xs rounded px-2 py-1.5" :class="bookingResult.submitted ? 'text-green-700 bg-green-50' : 'text-amber-700 bg-amber-50'">
					<template v-if="bookingResult.submitted">
						{{ __('Booked') }}: {{ bookingResult.sales_order }}
					</template>
					<template v-else>
						{{ __('Reservation {0} created — pending branch manager approval before it can be closed at the register.', [bookingResult.sales_order]) }}
					</template>
				</div>

				<Button variant="solid" :loading="booking" :disabled="!canBook" @click="confirmBooking">
					{{ __('Confirm Booking') }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { Button, Dialog } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { useBuildReservationStore } from "@/stores/buildReservation"
import { useInvoice } from "@/composables/useInvoice"
import { useToast } from "@/composables/useToast"
import { call } from "@/utils/apiWrapper"
import { formatCurrencyCode } from "@/utils/currency"
import { __ } from "@/utils/translation"

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	currency: { type: String, default: "SAR" },
})
const emit = defineEmits(["update:modelValue"])

const store = useBuildReservationStore()
const { calculateDiscountAmount } = useInvoice()
const { showSuccess, showError, showWarning } = useToast()

const show = computed({
	get: () => props.modelValue,
	set: (value) => emit("update:modelValue", value),
})

const booking = ref(false)
const bookingError = ref(null)
const bookingResult = ref(null)

const couponCode = ref("")
const applyingCoupon = ref(false)
const couponError = ref(null)

const netTotal = computed(() => Math.max(store.total - (store.appliedCoupon?.amount || 0), 0))

const canBook = computed(() => {
	if (booking.value || !store.items.length || !store.room || !store.visitDate || !store.phone) return false
	if (store.customerLookup.checked && !store.customerLookup.found && !store.customerName) return false
	return true
})

async function lookupCustomer() {
	if (!store.phone) {
		store.customerLookup = { checked: false, found: false, customerName: "" }
		return
	}
	const response = await call("ecs_posnext.api.build_booking.lookup_customer_by_phone", { phone: store.phone })
	const data = response?.message || response
	store.customerLookup = { checked: true, found: !!data, customerName: data?.customer_name || "" }
}

async function applyCoupon() {
	if (!couponCode.value.trim()) {
		couponError.value = __("Please enter a coupon code")
		return
	}

	applyingCoupon.value = true
	couponError.value = null
	try {
		const response = await call("ecs_posnext.api.build_booking.validate_build_coupon", {
			coupon_code: couponCode.value,
			phone: store.phone,
		})
		const validation = response?.message || response

		if (!validation?.valid) {
			couponError.value = validation?.message || __("The coupon code you entered is not valid")
			showError(couponError.value)
			return
		}

		const coupon = validation.coupon
		if (coupon.min_amount && store.total < coupon.min_amount) {
			couponError.value = __("This coupon requires a minimum purchase of {0}", [
				formatCurrencyCode(coupon.min_amount, props.currency),
			])
			showWarning(couponError.value)
			return
		}

		const discountObj = {
			percentage: coupon.discount_type === "Percentage" ? coupon.discount_percentage : 0,
			amount: coupon.discount_type === "Amount" ? coupon.discount_amount : 0,
		}
		let discountAmount = calculateDiscountAmount(discountObj, store.total)
		if (coupon.max_amount && discountAmount > coupon.max_amount) {
			discountAmount = coupon.max_amount
		}
		discountAmount = Math.min(discountAmount, store.total)

		store.appliedCoupon = {
			code: couponCode.value.toUpperCase(),
			amount: discountAmount,
			apply_on: coupon.apply_on,
		}
		couponCode.value = ""
		showSuccess(__("{0} applied successfully", [store.appliedCoupon.code]))
	} catch (err) {
		couponError.value = err?.messages?.[0] || err?.message || __("Failed to apply coupon")
		showError(couponError.value)
	} finally {
		applyingCoupon.value = false
	}
}

function removeCoupon() {
	store.appliedCoupon = null
	couponError.value = null
}

async function confirmBooking() {
	booking.value = true
	bookingError.value = null
	bookingResult.value = null
	try {
		const response = await call("ecs_posnext.api.build_booking.create_booking", {
			items: store.items.map((item) => ({
				item_code: item.item_code,
				qty: item.qty,
				uom: item.uom,
				slot: item.slot,
			})),
			branch: store.room,
			visit_date: store.visitDate,
			phone: store.phone,
			customer_name: store.customerLookup.found ? null : store.customerName,
			coupon_code: store.appliedCoupon?.code || null,
			discount_amount: store.appliedCoupon?.amount || 0,
		})
		bookingResult.value = response?.message || response
		if (bookingResult.value?.sales_order) {
			store.clear()
			window.location.href = `/app/sales-order/${bookingResult.value.sales_order}`
		}
	} catch (err) {
		bookingError.value = err?.messages?.[0] || err?.message || __("Could not create the booking")
	} finally {
		booking.value = false
	}
}

watch(show, (value) => {
	if (!value) {
		bookingError.value = null
		couponCode.value = ""
		couponError.value = null
	}
})
</script>
