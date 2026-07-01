<template>
	<Dialog v-model="isOpen" :options="{ title: dialogTitle, size: '5xl' }">
		<template #body-content>
			<div class="py-4 px-2 flex flex-col md:flex-row gap-6 max-h-[75vh] overflow-hidden">
				<!-- Left Column: Selection Options -->
				<div ref="scrollContainer" class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
					<!-- Item Header (Simplified) -->
					<div v-if="item" class="mb-6 border-b border-gray-100 pb-4">
						<div class="flex items-center gap-4">
							<div class="w-14 h-14 bg-gray-100 rounded-xl flex items-center justify-center overflow-hidden flex-shrink-0 border border-gray-200">
								<img v-if="item.image" :src="item.image" loading="lazy" :alt="item.item_name" class="w-full h-full object-cover" />
								<svg v-else class="h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
								</svg>
							</div>
							<div class="flex-1 text-start">
								<h3 class="text-lg font-black text-gray-900 uppercase tracking-tight">{{ item.item_name }}</h3>
								<p class="text-xs text-gray-500 font-medium">{{ item.item_code }}</p>
							</div>
						</div>
					</div>

					<!-- Loading State -->
					<div v-if="loading" class="flex items-center justify-center py-20">
						<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
						<p class="ms-4 text-lg text-gray-500 font-bold">{{ __('Loading options...') }}</p>
					</div>

					<!-- Content Area -->
					<div v-else-if="options.length > 0" class="flex flex-col gap-8 pb-4">
						<!-- Variant/UOM Selection Section -->
						<div v-if="mode === 'variant'" class="flex flex-col gap-6">
							<div v-for="(values, attrName) in variantAttributesMap" :key="attrName" class="flex flex-col gap-3">
								<label class="text-sm font-black text-gray-400 uppercase tracking-widest text-start block px-1">{{ attrName }}</label>
								<div class="flex flex-wrap gap-3">
									<button
										v-for="value in values"
										:key="value"
										@click="selectAttribute(attrName, value)"
										:class="[
											'px-6 py-3 rounded-xl border-2 text-sm font-bold transition-all duration-200',
											selectedAttributes[attrName] === value
												? 'border-blue-600 bg-blue-600 text-white shadow-lg scale-105'
												: 'border-gray-200 bg-white text-gray-600 hover:border-blue-300 hover:bg-blue-50/30'
										]"
									>
										{{ value }}
									</button>
								</div>
							</div>

							<!-- Selected Variant Info -->
							<div v-if="matchedVariant" class="p-4 bg-blue-50 rounded-xl border border-blue-100">
								<div class="flex items-center justify-between">
									<div class="text-start">
										<p class="text-sm font-bold text-gray-900">{{ matchedVariant.label }}</p>
										<p class="text-xs text-gray-500">{{ matchedVariant.description }}</p>
									</div>
									<div class="text-end">
										<p class="text-lg font-bold text-blue-600">{{ formatCurrency(matchedVariant.rate || 0) }}</p>
										<p class="text-xs" :class="(matchedVariant.stock) > 0 ? 'text-green-600' : 'text-red-600'">
											{{ __('Stock: {0}', [Math.floor(matchedVariant.stock)]) }}
										</p>
									</div>
								</div>
							</div>
							<div v-else-if="allAttributesSelected" class="p-3 bg-orange-50 border border-orange-200 rounded-lg text-center">
								<p class="text-xs text-orange-700 font-medium">{{ __('This combination is not available') }}</p>
							</div>
						</div>

						<!-- UOM Selection Section -->
						<div v-else-if="mode === 'uom'" class="flex flex-col gap-6">
							<label class="block text-sm font-black text-gray-400 uppercase tracking-widest text-start px-1">{{ __('Unit of Measure') }}</label>
							<div class="grid gap-4 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
								<button
									v-for="(option, index) in options"
									:key="index"
									@click="selectOption(option)"
									:class="[
										'px-6 py-5 rounded-2xl font-black text-sm transition-all duration-200 flex flex-col items-center justify-center min-h-[80px] border-2',
										selectedOption === option
											? 'border-blue-600 bg-blue-600 text-white shadow-lg scale-105'
											: 'bg-white text-gray-700 hover:border-blue-300 hover:bg-blue-50/30 border-gray-200 shadow-sm'
									]"
								>
									<span class="uppercase tracking-tight">{{ option.label }}</span>
									<span :class="['text-xs mt-1.5 font-bold', selectedOption === option ? 'text-blue-100' : 'text-blue-600']">
										{{ formatCurrency(option.rate || 0) }}
									</span>
								</button>
							</div>
						</div>

						<!-- Ingredients Section -->
						<div v-if="selectedOption?.ingredients?.length > 0" class="flex flex-col gap-3">
							<div class="flex items-center justify-between border-b border-gray-100 pb-2">
								<label class="text-[11px] font-black text-gray-400 uppercase tracking-widest">{{ __('Ingredients') }}</label>
								<span class="text-[10px] text-gray-400 font-bold italic">{{ __('Tap to remove') }}</span>
							</div>
							<div class="flex flex-wrap gap-2">
								<button
									v-for="ing in selectedOption.ingredients"
									:key="ing.item_code"
									@click="toggleIngredient(ing.item_code)"
									:class="[
										'px-4 py-2 rounded-full text-xs font-bold transition-all flex items-center gap-2 border-2',
										isIngredientRemoved(ing.item_code)
											? 'bg-gray-100 text-gray-400 border-gray-200 line-through opacity-60'
											: 'bg-white text-gray-700 border-gray-100 hover:border-orange-200 hover:bg-orange-50'
									]"
								>
									<svg v-if="!isIngredientRemoved(ing.item_code)" class="w-3.5 h-3.5 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
										<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
									</svg>
									{{ ing.item_name }}
								</button>
							</div>
						</div>

						<!-- Addons Section -->
						<div v-if="availableAddons.length > 0" class="flex flex-col gap-4">
							<label class="text-[11px] font-black text-gray-400 uppercase tracking-widest text-start px-1 border-b border-gray-100 pb-2">
								{{ selectedOption?.addons_label || __('Add-ons') }}
							</label>
							<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
								<button
									v-for="addon in availableAddons"
									:key="addon.item_code"
									@click="toggleAddon(addon)"
									:class="[
										'p-4 rounded-2xl text-start transition-all border-2 flex flex-col gap-1.5 shadow-sm',
										isAddonSelected(addon.item_code)
											? 'border-blue-600 bg-blue-50 ring-2 ring-blue-100'
											: 'border-gray-100 bg-white hover:border-blue-200'
									]"
								>
									<div class="flex items-center justify-between">
										<span class="text-sm font-black text-gray-900 line-clamp-1 uppercase tracking-tight">{{ addon.item_name }}</span>
										<div v-if="isAddonSelected(addon.item_code)" class="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center shadow-sm">
											<svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
											</svg>
										</div>
									</div>
									<span class="text-xs font-bold text-blue-600">+ {{ formatCurrency(addon.price) }}</span>
								</button>
							</div>
						</div>
					</div>

					<!-- No Options State -->
					<div v-else-if="!loading" class="text-center py-20 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
						<div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-orange-100 mb-4">
							<svg class="h-8 w-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
							</svg>
						</div>
						<h3 class="text-lg font-black text-gray-900 uppercase tracking-tight mb-2">
							{{ mode === 'variant' ? __('No Variants Available') : __('No Units Available') }}
						</h3>
						<p class="text-sm text-gray-500 max-w-xs mx-auto font-medium">
							{{ mode === 'variant' 
								? __('This item template does not have any variants configured.') 
								: __('No additional units of measurement found for this item.') }}
						</p>
					</div>
				</div>

				<!-- Right Column: Summary Sidebar -->
				<div v-if="!loading && options.length > 0" class="w-full md:w-80 bg-gray-50 rounded-2xl p-5 border border-gray-200 flex flex-col">
					<h4 class="text-[11px] font-black text-gray-900 mb-4 flex items-center gap-2 uppercase tracking-widest border-b border-gray-200 pb-2">
						<svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
						</svg>
						{{ __('Your Selection') }}
					</h4>

					<div class="flex-1 overflow-y-auto mb-4 pr-1 custom-scrollbar space-y-4">
						<!-- Selection Detail -->
						<div v-if="selectedOption" class="bg-white p-3 rounded-xl border border-gray-200 shadow-sm">
							<p class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">{{ mode === 'variant' ? __('Variant') : __('Unit') }}</p>
							<p class="text-sm font-bold text-gray-900">{{ selectedOption.label }}</p>
						</div>

						<!-- Removed Ingredients -->
						<div v-if="removedIngredients.length > 0" class="bg-orange-50/50 p-3 rounded-xl border border-orange-100">
							<p class="text-[10px] font-black text-orange-400 uppercase tracking-widest mb-1">{{ __('Removed') }}</p>
							<div class="flex flex-wrap gap-1.5">
								<span v-for="ingCode in removedIngredients" :key="ingCode" class="text-[10px] font-bold text-orange-700 bg-white px-2 py-0.5 rounded-full border border-orange-200">
									{{ getIngredientName(ingCode) }}
								</span>
							</div>
						</div>

						<!-- Selected Addons -->
						<div v-if="selectedAddons.length > 0" class="bg-blue-50/50 p-3 rounded-xl border border-blue-100">
							<p class="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-1">{{ __('Add-ons') }}</p>
							<div class="space-y-1.5">
								<div v-for="addon in selectedAddons" :key="addon.item_code" class="flex justify-between items-center">
									<span class="text-[10px] font-bold text-blue-700 leading-tight flex-1">• {{ addon.item_name }}</span>
									<span class="text-[10px] font-black text-blue-600 ml-2">+{{ formatCurrency(addon.price) }}</span>
								</div>
							</div>
						</div>

						<!-- Notes Input -->
						<div class="flex flex-col gap-2 pt-2 border-t border-gray-200">
							<label class="text-[10px] font-black text-gray-400 uppercase tracking-widest">{{ __('Special Instructions') }}</label>
							<textarea
								v-model="notes"
								rows="3"
								:placeholder="__('Add a note...')"
								class="w-full rounded-xl border border-gray-200 bg-white p-3 text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none custom-scrollbar"
							></textarea>
						</div>
					</div>

					<!-- Bottom Sidebar: Qty and Price -->
					<div class="pt-4 border-t border-gray-200 space-y-4">
						<!-- Quantity Control -->
						<div class="flex flex-col gap-2">
							<label class="text-[10px] font-black text-gray-400 uppercase tracking-widest">{{ __('Quantity') }}</label>
							<div class="flex items-center bg-white rounded-xl overflow-hidden h-10 border border-gray-200 shadow-sm">
								<button @click="decrementQuantity" class="w-10 h-full flex items-center justify-center hover:bg-gray-50 active:bg-gray-100 transition-colors font-black text-gray-600">−</button>
								<input v-model.number="quantity" type="number" class="flex-1 text-center bg-transparent border-0 focus:ring-0 text-sm font-black h-full" @blur="validateQuantity" />
								<button @click="incrementQuantity" class="w-10 h-full flex items-center justify-center hover:bg-gray-50 active:bg-gray-100 transition-colors font-black text-gray-600">+</button>
							</div>
						</div>

						<!-- Total Price Summary -->
						<div class="bg-gray-900 rounded-2xl p-4 text-white shadow-lg border border-gray-800">
							<div class="flex justify-between items-center mb-1.5">
								<span class="text-[10px] text-gray-400 uppercase tracking-widest font-black">{{ __('Summary') }}</span>
								<span class="text-[10px] text-gray-400 font-bold">{{ quantity }} × {{ formatCurrency(totalPrice) }}</span>
							</div>
							<div class="flex justify-between items-end">
								<span class="text-xs text-blue-400 font-black uppercase tracking-tight">{{ __('Total') }}</span>
								<span class="text-xl font-black text-blue-400 leading-none">
									{{ formatCurrency(totalPrice * quantity) }}
								</span>
							</div>
						</div>
					</div>
				</div>
			</div>
		</template>

		<template #actions>
			<div class="flex gap-2 w-full">
				<Button class="flex-1" variant="subtle" @click="cancel">
					{{ __('Cancel') }}
				</Button>
				<Button class="flex-1" variant="solid" theme="blue" @click="confirm" :disabled="!selectedOption">
					{{ confirmButtonText }}
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { DEFAULT_CURRENCY, formatCurrency as formatCurrencyUtil } from "@/utils/currency"
import { Button, Dialog } from "frappe-ui"
import { createResource } from "frappe-ui"
import { computed, nextTick, ref, watch } from "vue"
import TranslatedHTML from "../common/TranslatedHTML.vue"
import { offlineState } from "@/utils/offline/offlineState"
import { getCachedVariants, cacheItems } from "@/utils/offline/items"
import { usePOSCartStore } from "@/stores/posCart"
import { useItemSearchStore } from "@/stores/itemSearch"

const props = defineProps({
	modelValue: Boolean,
	item: Object,
	mode: {
		type: String, // 'uom' or 'variant'
		default: "uom",
	},
	posProfile: String,
	currency: {
		type: String,
		default: DEFAULT_CURRENCY,
	},
})

const emit = defineEmits(["update:modelValue", "option-selected"])

const isOpen = computed({
	get: () => props.modelValue,
	set: (value) => emit("update:modelValue", value),
})

const loading = ref(false)
const options = ref([])
const selectedOption = ref(null)
const quantity = ref(1)
const selectedAttributes = ref({}) // For variant attribute selection
const selectedAddons = ref([])
const removedIngredients = ref([])
const notes = ref("")

const scrollContainer = ref(null)

const cartStore = usePOSCartStore()
const itemSearchStore = useItemSearchStore()

// Computed properties for dialog customization
const dialogTitle = computed(() => {
	if (props.mode === "uom") return __("Select Unit of Measure")
	return selectedOption.value ? selectedOption.value.label : __("Select Item Variant")
})

const availableAddons = computed(() => {
	if (!selectedOption.value || !selectedOption.value.addons) return []
	
	return selectedOption.value.addons.filter(addon => {
		if (!addon.applicable_attribute || !addon.applicable_value) return true
		return selectedAttributes.value[addon.applicable_attribute] === addon.applicable_value
	})
})

const totalPrice = computed(() => {
	let total = selectedOption.value?.rate || options.value[0]?.rate || 0
	
	selectedAddons.value.forEach(addon => {
		total += addon.price || 0
	})
	
	return total
})

const dialogDescription = computed(() => {
	return props.mode === "variant"
		? __("Choose a variant of this item:")
		: __("Select the unit of measure for this item:")
})

const confirmButtonText = computed(() => {
	return props.mode === "variant" ? __("Add to Cart") : __("Add to Cart")
})

// Computed: Stock warning when quantity exceeds available stock
const stockWarning = computed(() => {
	if (props.mode !== "uom" || !selectedOption.value) return null

	const availableStock = selectedOption.value.stock_qty ?? selectedOption.value.actual_qty ?? null
	if (availableStock === null) return null

	if (quantity.value > availableStock) {
		return __("Requested quantity ({0}) exceeds available stock ({1})", [quantity.value, Math.floor(availableStock)])
	}
	return null
})

/**
 * Validates quantity input ensuring it's a valid positive integer
 */
function validateQuantity() {
	// Handle invalid, negative, or decimal values
	if (!quantity.value || isNaN(quantity.value) || quantity.value < 1) {
		quantity.value = 1
	} else {
		// Round to nearest integer for UOM quantities
		quantity.value = Math.max(1, Math.round(quantity.value))
	}
}

// Quantity counter functions
function incrementQuantity() {
	quantity.value = Math.max(1, quantity.value + 1)
}

function decrementQuantity() {
	if (quantity.value > 1) {
		quantity.value = quantity.value - 1
	}
}

// Computed: Build a map of all available attribute values
const variantAttributesMap = computed(() => {
	if (props.mode !== "variant" || options.value.length === 0) return {}

	const attrMap = {}
	options.value.forEach((option) => {
		Object.entries(option.attributes || {}).forEach(([key, value]) => {
			if (!attrMap[key]) {
				attrMap[key] = new Set()
			}
			attrMap[key].add(value)
		})
	})

	// Convert Sets to sorted Arrays and reverse keys
	const result = {}
	Object.keys(attrMap).reverse().forEach((key) => {
		result[key] = Array.from(attrMap[key]).sort()
	})

	return result
})

// Computed: Check if all attributes are selected
const allAttributesSelected = computed(() => {
	const attrKeys = Object.keys(variantAttributesMap.value)
	return (
		attrKeys.length > 0 &&
		attrKeys.every((key) => selectedAttributes.value[key])
	)
})

// Computed: Find variant that matches selected attributes
const matchedVariant = computed(() => {
	if (!allAttributesSelected.value) return null

	return options.value.find((option) => {
		return Object.entries(selectedAttributes.value).every(([key, value]) => {
			return option.attributes[key] === value
		})
	})
})

/**
 * Transform raw variant data into option format for the UI
 */
function mapVariantsToOptions(variants) {
	return variants.map((v) => ({
		type: "variant",
		item_code: v.item_code,
		label: v.item_name,
		description: v.item_code,
		attributes: v.attributes || {},
		rate: v.rate || v.price_list_rate || 0,
		priceLabel: __('per {0}', [v.stock_uom]),
		stock: v.actual_qty ?? 0,
		ingredients: v.ingredients || [],
		addons: v.addons || [],
		addons_label: v.addons_label,
		is_bundle: v.enabled_item_bundle,
		data: v,
	}))
}

/**
 * Load variants from IndexedDB cache (for offline mode or API fallback)
 */
async function loadVariantsFromCache() {
	try {
		const cachedVariants = await getCachedVariants(props.item?.item_code)
		options.value = cachedVariants?.length > 0 ? mapVariantsToOptions(cachedVariants) : []
	} catch (error) {
		console.error("Error loading variants from cache:", error)
		options.value = []
	} finally {
		loading.value = false
	}
}

// Resource for fetching variants from API
const variantsResource = createResource({
	url: "ecs_posnext.api.items.get_item_variants",
	makeParams() {
		return {
			template_item: props.item?.item_code,
			pos_profile: props.posProfile,
			warehouse: cartStore.selectedBranchWarehouse,
			price_list: itemSearchStore.selectedPriceList || cartStore.selectedBranchPriceList,
		}
	},
	auto: false,
	async onSuccess(data) {
		const variants = data?.message || data || []
		options.value = mapVariantsToOptions(variants)
		loading.value = false

		// Cache variants for offline use
		if (variants.length > 0) {
			cacheItems(variants).catch((err) => console.error("Error caching variants:", err))
		}
	},
	async onError(error) {
		console.error("Error loading variants:", error)
		// Try cache as fallback (user might have just gone offline)
		await loadVariantsFromCache()
	},
})

// Load options when dialog opens
watch(
	() => props.modelValue,
	(isOpen) => {
		if (isOpen && props.item) {
			loadOptions()
			nextTick(() => {
				if (scrollContainer.value) {
					scrollContainer.value.scrollTop = 0
				}
			})
		}
	},
)

// Watch mode and item changes to reload options
watch([() => props.mode, () => props.item], ([, newItem]) => {
	if (props.modelValue && newItem) {
		loadOptions()
	}
})

/**
 * Load options based on mode (variant or UOM)
 */
async function loadOptions() {
	selectedOption.value = null
	quantity.value = props.item.resolved_qty || 1
	selectedAttributes.value = {} // Reset attribute selection
	selectedAddons.value = props.item?.selected_addons ? [...props.item.selected_addons] : []
	removedIngredients.value = props.item?.removed_ingredients ? [...props.item.removed_ingredients] : []
	notes.value = props.item?.notes || ""

	if (props.mode === "variant") {
		loading.value = true

		if (offlineState.isOffline) {
			await loadVariantsFromCache()
		} else {
			variantsResource.reload()
		}
	} else {
		// Load UOM options
		options.value = buildUomOptions()
		if (options.value.length > 0) {
			// Check if item has a single barcode UOM to auto-select
			const barcodeUoms = props.item?.barcode_uoms
				? props.item.barcode_uoms.split(",").filter(Boolean)
				: []

			if (barcodeUoms.length === 1) {
				// Find and select the matching UOM option
				const uom = props.item.resolved_uom || barcodeUoms[0]
				const matchingOption = options.value.find((opt) => opt.uom === uom)
				selectedOption.value = matchingOption || options.value[0]
			} else {
				// Default to first option (stock UOM)
				selectedOption.value = options.value[0]
			}
		}
		loading.value = false
	}
}

// Watch matched variant and auto-select it
watch(matchedVariant, (variant) => {
	if (variant) {
		selectedOption.value = variant
	} else {
		selectedOption.value = null
	}
})

function getIngredientName(itemCode) {
	if (!selectedOption.value?.ingredients) return itemCode
	const ing = selectedOption.value.ingredients.find(i => i.item_code === itemCode)
	return ing ? ing.item_name : itemCode
}

function buildUomOptions() {
	if (!props.item) return []

	const uomOptions = []

	// Stock UOM option
	uomOptions.push({
		type: "uom",
		uom: props.item.stock_uom,
		conversion_factor: 1,
		label: props.item.stock_uom,
		rate: props.item.rate || 0,
		ingredients: props.item.ingredients || [],
		addons: props.item.addons || [],
		addons_label: props.item.addons_label,
	})

	// Add other UOMs if available
	if (props.item.uoms && Array.isArray(props.item.uoms)) {
		props.item.uoms.forEach((uom) => {
			if (uom.uom !== props.item.stock_uom) {
				uomOptions.push({
					type: "uom",
					uom: uom.uom,
					conversion_factor: uom.conversion_factor || 1,
					label: uom.uom,
					rate: uom.rate || 0,
					ingredients: props.item.ingredients || [],
					addons: props.item.addons || [],
					addons_label: props.item.addons_label,
				})
			}
		})
	}

	return uomOptions
}

function selectAttribute(attrName, value) {
	selectedAttributes.value[attrName] = value
	// Force reactivity
	selectedAttributes.value = { ...selectedAttributes.value }
}

function selectOption(option) {
	selectedOption.value = option
}

function isAddonSelected(itemCode) {
	return selectedAddons.value.some((a) => a.item_code === itemCode)
}

function toggleAddon(addon) {
	const idx = selectedAddons.value.findIndex((a) => a.item_code === addon.item_code)
	if (idx >= 0) {
		selectedAddons.value.splice(idx, 1)
	} else {
		selectedAddons.value.push({
			item_code: addon.item_code,
			item_name: addon.item_name,
			price: addon.price || 0,
			is_stock_item: addon.is_stock_item || 0,
			uom: addon.uom || "Unit",
		})
	}
}

function isIngredientRemoved(itemCode) {
	return removedIngredients.value.includes(itemCode)
}

function toggleIngredient(itemCode) {
	const idx = removedIngredients.value.indexOf(itemCode)
	if (idx >= 0) {
		removedIngredients.value.splice(idx, 1)
	} else {
		removedIngredients.value.push(itemCode)
	}
}

function confirm() {
	if (selectedOption.value) {
		const option = { ...selectedOption.value }
		
		// Add new customization fields
		option.quantity = quantity.value
		option.selected_addons = selectedAddons.value
		option.removed_ingredients = removedIngredients.value
		// Get ingredients from option or fallback to main item
		const ingredients = (selectedOption.value.ingredients && selectedOption.value.ingredients.length > 0)
			? selectedOption.value.ingredients
			: (props.item?.ingredients || [])

		option.removed_ingredient_names = ingredients
			?.filter(ing => removedIngredients.value.includes(ing.item_code))
			.map(ing => ing.item_name) || []
		option.notes = notes.value
		option.total_price = totalPrice.value
		
		emit("option-selected", option)
	}
}

function cancel() {
	selectedOption.value = null
	selectedAttributes.value = {}
	isOpen.value = false
}

function formatCurrency(amount) {
	return formatCurrencyUtil(Number.parseFloat(amount || 0), props.currency)
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
	width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
	background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
	background: #cbd5e1;
	border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
	background: #94a3b8;
}

/* Hide spin buttons for number input */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
	-webkit-appearance: none;
	appearance: none;
	margin: 0;
}
input[type=number] {
	-moz-appearance: textfield;
	appearance: textfield;
}
</style>
