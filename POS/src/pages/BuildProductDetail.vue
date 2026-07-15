<template>
	<div class="flex flex-col bg-gray-50" style="height: 100vh; max-height: 100vh">
		<!-- Header -->
		<div class="flex items-center gap-3 px-3 sm:px-4 py-2.5 sm:py-3 bg-white border-b border-gray-200">
			<button
				@click="router.push({ name: 'Build' })"
				class="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 active:bg-blue-200 touch-manipulation"
				:aria-label="__('Back to catalog')"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				</svg>
				<span>{{ __('Back') }}</span>
			</button>
			<h1 class="text-sm sm:text-base font-semibold text-gray-900 truncate">{{ __('Product Details') }}</h1>
		</div>

		<div class="flex-1 overflow-y-auto px-3 sm:px-4 py-4 pb-20">
			<div v-if="loading" class="flex items-center justify-center h-full text-gray-400 text-sm">
				{{ __('Loading product...') }}
			</div>
			<div v-else-if="error" class="flex flex-col items-center justify-center h-full text-gray-400 text-sm gap-2">
				<span>{{ error }}</span>
				<Button variant="outline" @click="router.push({ name: 'Build' })">{{ __('Back to catalog') }}</Button>
			</div>
			<div v-else-if="product" class="max-w-3xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
				<div>
					<div class="bg-white rounded-lg border border-gray-200 aspect-square overflow-hidden">
						<LazyImage
							v-if="product.image"
							:src="product.image"
							:alt="product.item_name"
							container-class="relative w-full h-full"
							img-class="w-full h-full object-cover"
						>
							<template #error>
								<PlaceholderIcon />
							</template>
						</LazyImage>
						<div v-else class="w-full h-full flex items-center justify-center">
							<PlaceholderIcon />
						</div>
					</div>

					<!-- Included Items (Product Bundle) -->
					<div v-if="bookingOptions?.bundle_items?.length" class="bg-white rounded-lg border border-gray-200 mt-3 p-3">
						<div class="text-xs font-semibold text-gray-500 uppercase mb-2">{{ __('Included Items') }}</div>
						<ul class="text-sm text-gray-700 divide-y divide-gray-100">
							<li
								v-for="bundleItem in bookingOptions.bundle_items"
								:key="bundleItem.item_code"
								class="flex justify-between py-1.5"
							>
								<span>{{ bundleItem.item_name || bundleItem.item_code }}</span>
								<span class="text-gray-500">{{ bundleItem.qty }} {{ bundleItem.uom }}</span>
							</li>
						</ul>
					</div>
				</div>

				<div class="flex flex-col gap-3">
					<div>
						<div class="text-xs text-gray-500">{{ __(product.item_group) }}</div>
						<h2 class="text-lg sm:text-xl font-semibold text-gray-900">
							{{ product.web_item_name || product.item_name }}
						</h2>
						<div v-if="product.brand" class="text-xs text-gray-500 mt-0.5">{{ __(product.brand) }}</div>
					</div>

					<div class="text-xl sm:text-2xl font-bold text-gray-900">
						{{ formatCurrencyCode(selectedRate, currency) }}
						<span v-if="selectedUom" class="text-sm font-normal text-gray-500">/ {{ __(selectedUom) }}</span>
					</div>

					<div v-if="product.on_backorder" class="text-xs font-medium text-amber-600 bg-amber-50 rounded px-2 py-1 w-fit">
						{{ __('On Backorder') }}
					</div>

					<p v-if="product.short_description" class="text-sm text-gray-600">
						{{ product.short_description }}
					</p>

					<div
						v-if="product.web_long_description"
						class="text-sm text-gray-700 prose prose-sm max-w-none"
						v-html="product.web_long_description"
					></div>

					<!-- Booking Form -->
					<div class="bg-white rounded-lg border border-gray-200 p-3 sm:p-4 flex flex-col gap-3 mt-2">
						<div class="text-sm font-semibold text-gray-900">{{ __('Book This') }}</div>

						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">
								{{ __('Quantity') }}
								<span v-if="minQty > 1" class="text-gray-400 font-normal">({{ __('min {0}', [minQty]) }})</span>
							</label>
							<div class="flex items-center gap-2">
								<button
									type="button"
									@click="qty = Math.max(minQty, qty - 1)"
									class="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 touch-manipulation"
								>−</button>
								<input
									v-model.number="qty"
									type="number"
									:min="minQty"
									@change="qty = Math.max(minQty, qty)"
									class="w-20 text-center text-sm border border-gray-300 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
								<button
									type="button"
									@click="qty = qty + 1"
									class="w-8 h-8 flex items-center justify-center rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 touch-manipulation"
								>+</button>
							</div>
						</div>

						<template v-if="bookingOptions?.requires_booking">
							<div>
								<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Branch') }}</label>
								<AutocompleteSelect
									v-model="store.parentBranch"
									:options="parentBranchOptions"
									:placeholder="__('Search branch...')"
									@update:modelValue="onParentBranchChange"
								/>
							</div>

							<div v-if="store.parentBranch">
								<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Room') }}</label>
								<AutocompleteSelect
									v-model="store.room"
									:options="roomOptions"
									:loading="roomsLoading"
									:placeholder="__('Search room...')"
								/>
							</div>

							<div>
								<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Visit Date') }}</label>
								<input
									v-model="store.visitDate"
									type="date"
									:min="todayStr"
									class="w-full text-sm border border-gray-300 rounded-lg px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
							</div>

							<!-- Weekday / Weekend (UOM-based) pricing option - auto-filtered from the
							     visit date: Thursday/Friday count as weekend, everything else weekday -->
							<div v-if="filteredUoms.length > 1">
								<label class="block text-xs font-medium text-gray-600 mb-1">
									{{ __('Weekday / Weekend') }}
									<span v-if="store.visitDate" class="text-gray-400 font-normal">({{ isWeekend ? __('Weekend') : __('Weekday') }})</span>
								</label>
								<AutocompleteSelect
									v-model="selectedUom"
									:options="uomOptions"
									:placeholder="__('Search pricing option...')"
								/>
							</div>

							<div v-if="bookingOptions?.non_sharable_slot">
								<label class="block text-xs font-medium text-gray-600 mb-1">{{ __('Slot') }}</label>
								<AutocompleteSelect
									v-model="slot"
									:options="slotOptions"
									:loading="slotsLoading"
									:placeholder="slots.length ? __('Search slot...') : __('Select room and date first')"
								/>
							</div>
						</template>

						<div class="text-sm text-gray-700">
							{{ __('Total') }}: <span class="font-semibold text-gray-900">{{ formatCurrencyCode(qty * selectedRate, currency) }}</span>
						</div>

						<div v-if="addError" class="text-xs text-red-600 bg-red-50 rounded px-2 py-1.5">
							{{ addError }}
						</div>
						<div v-if="added" class="text-xs text-green-700 bg-green-50 rounded px-2 py-1.5">
							{{ __('Added to reservation') }}
						</div>

						<Button variant="solid" @click="addToCart">
							{{ __('Add to Cart') }}
						</Button>
					</div>
				</div>
			</div>
		</div>

		<ReservationCartBar :currency="currency" />
	</div>
</template>

<script setup>
import { Button } from "frappe-ui"
import { computed, h, onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import AutocompleteSelect from "@/components/common/AutocompleteSelect.vue"
import LazyImage from "@/components/common/LazyImage.vue"
import ReservationCartBar from "@/components/build/ReservationCartBar.vue"
import { useBuildReservationStore } from "@/stores/buildReservation"
import { call } from "@/utils/apiWrapper"
import { formatCurrencyCode } from "@/utils/currency"
import { __ } from "@/utils/translation"

const route = useRoute()
const router = useRouter()
const store = useBuildReservationStore()

const product = ref(null)
const bookingOptions = ref(null)
const currency = ref("SAR")
const loading = ref(false)
const error = ref(null)

const qty = ref(1)
const selectedUom = ref(null)
const rooms = ref([])
const roomsLoading = ref(false)
const slot = ref(null)
const slots = ref([])
const slotsLoading = ref(false)

const addError = ref(null)
const added = ref(false)

const todayStr = new Date().toISOString().slice(0, 10)

const minQty = computed(() => bookingOptions.value?.minimum_sales_quantity || 1)

const selectedRate = computed(() => {
	const match = bookingOptions.value?.uoms?.find((u) => u.uom === selectedUom.value)
	return match ? match.rate : product.value?.price_list_rate || 0
})

// Thursday/Friday count as the weekend for this business, everything else is a weekday.
const isWeekend = computed(() => {
	if (!store.visitDate) return false
	const day = new Date(`${store.visitDate}T00:00:00`).getDay()
	return day === 4 || day === 5
})

// Once a visit date is picked, only show the UOM variants matching that day type
// (weekday vs weekend) instead of making the cashier pick the day type manually.
const filteredUoms = computed(() => {
	const uoms = bookingOptions.value?.uoms || []
	if (!store.visitDate) return uoms

	const wantWord = isWeekend.value ? "weekend" : "weekday"
	const matches = uoms.filter((u) => u.uom.toLowerCase().includes(wantWord))
	return matches.length ? matches : uoms
})

watch(filteredUoms, (uoms) => {
	if (!uoms.some((u) => u.uom === selectedUom.value)) {
		selectedUom.value = uoms[0]?.uom || null
	}
})

// AutocompleteSelect expects {value, label[, subtitle]} options
const parentBranchOptions = computed(() =>
	(bookingOptions.value?.parent_branches || []).map((b) => ({ value: b, label: b })),
)
const roomOptions = computed(() =>
	rooms.value.map((r) => ({ value: r.name, label: r.is_group ? __("Whole Branch") : r.name })),
)
const uomOptions = computed(() =>
	filteredUoms.value.map((u) => ({
		value: u.uom,
		label: __(u.uom),
		subtitle: formatCurrencyCode(u.rate, currency.value),
	})),
)
const slotOptions = computed(() => slots.value.map((s) => ({ value: s.id, label: s.Name })))

const PlaceholderIcon = () =>
	h(
		"svg",
		{
			class: "h-16 w-16 text-gray-300",
			fill: "none",
			stroke: "currentColor",
			viewBox: "0 0 24 24",
		},
		[
			h("path", {
				"stroke-linecap": "round",
				"stroke-linejoin": "round",
				"stroke-width": "2",
				d: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z",
			}),
		],
	)

async function fetchProduct() {
	loading.value = true
	error.value = null
	product.value = null
	bookingOptions.value = null
	added.value = false
	addError.value = null

	try {
		const [productResponse, optionsResponse] = await Promise.all([
			call("ecs_posnext.api.items.get_product_detail", { item_code: route.params.item_code }),
			call("ecs_posnext.api.build_booking.get_booking_options", { item_code: route.params.item_code }),
		])
		product.value = productResponse?.message || productResponse
		bookingOptions.value = optionsResponse?.message || optionsResponse
		currency.value = product.value?.currency || bookingOptions.value?.currency || "SAR"
		selectedUom.value = bookingOptions.value?.uoms?.[0]?.uom || null
		qty.value = minQty.value

		// Simple add-ons (requires_booking=false) don't have a branch list of their
		// own and just attach to whatever reservation is already being built - leave
		// the shared branch/room selection untouched for them.
		if (bookingOptions.value?.requires_booking) {
			// store.parentBranch/room are shared across items (one reservation can span
			// several products), but each item's valid branch list differs by brand - a
			// selection made on a previous item may not exist in this item's list, which
			// left the <select> bound to a value with no matching <option> (looked like
			// the dropdown couldn't be selected at all). Reconcile against this item's
			// actual options; auto-pick when there's only one.
			const parentBranches = bookingOptions.value?.parent_branches || []
			if (!store.parentBranch || !parentBranches.includes(store.parentBranch)) {
				store.parentBranch = parentBranches.length === 1 ? parentBranches[0] : null
				store.room = null
			}

			if (store.parentBranch) {
				await fetchRooms()
			} else {
				rooms.value = []
			}
		}
	} catch (err) {
		error.value = err?.messages?.[0] || err?.message || __("Product not found")
	} finally {
		loading.value = false
	}
}

async function onParentBranchChange() {
	store.room = null
	await fetchRooms()
}

async function fetchRooms() {
	if (!store.parentBranch) {
		rooms.value = []
		return
	}
	roomsLoading.value = true
	try {
		const response = await call("ecs_posnext.api.build_booking.get_rooms", {
			item_code: route.params.item_code,
			parent_branch: store.parentBranch,
		})
		rooms.value = response?.message || response || []

		if (store.room && !rooms.value.some((r) => r.name === store.room)) {
			store.room = rooms.value.length === 1 ? rooms.value[0].name : null
		}
	} finally {
		roomsLoading.value = false
	}
}

async function fetchSlots() {
	if (!bookingOptions.value?.non_sharable_slot || !store.visitDate || !store.room) {
		slots.value = []
		return
	}
	slotsLoading.value = true
	slot.value = null
	try {
		const response = await call("ecs_posnext.api.build_booking.get_slots", {
			item_code: route.params.item_code,
			visit_date: store.visitDate,
			branch: store.room,
		})
		slots.value = response?.message || response || []
	} finally {
		slotsLoading.value = false
	}
}

function addToCart() {
	addError.value = null
	added.value = false

	// Simple add-ons (no dimension_brand, e.g. Party Additions) aren't tied to a
	// branch/room/date - they just attach to whatever reservation is already
	// being built, so skip straight to adding them.
	if (bookingOptions.value?.requires_booking) {
		if (!store.room) {
			addError.value = __("Select a branch and room first")
			return
		}
		if (!store.visitDate) {
			addError.value = __("Select a visit date first")
			return
		}
		if (bookingOptions.value?.non_sharable_slot && !slot.value) {
			addError.value = __("Select a slot first")
			return
		}
	}

	store.addItem({
		item_code: route.params.item_code,
		item_name: product.value.web_item_name || product.value.item_name,
		qty: Math.max(minQty.value, qty.value),
		uom: selectedUom.value,
		rate: selectedRate.value,
		slot: bookingOptions.value?.non_sharable_slot ? slot.value : null,
	})
	added.value = true
	qty.value = minQty.value
}

watch(() => store.room, fetchSlots)
watch(() => store.visitDate, fetchSlots)
watch(() => route.params.item_code, fetchProduct)
onMounted(fetchProduct)
</script>
