<template>
	<Dialog v-model="isOpen" :options="{ title: dialogTitle, size: '5xl' }">
		<template #body-content>
			<div class="py-4 flex flex-col md:flex-row gap-6 max-h-[70vh] overflow-hidden">
				<!-- Left: Sections and Options -->
				<div class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
					<div v-if="loading" class="flex items-center justify-center py-12">
						<div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
						<p class="ms-3 text-gray-500">{{ __('Loading combo details...') }}</p>
					</div>

					<div v-else-if="sections.length > 0" class="space-y-8 relative">
						<!-- Group Variant Picker Overlay -->
						<transition
							enter-active-class="transition duration-200 ease-out"
							enter-from-class="opacity-0 translate-y-4"
							enter-to-class="opacity-100 translate-y-0"
							leave-active-class="transition duration-150 ease-in"
							leave-from-class="opacity-100 translate-y-0"
							leave-to-class="opacity-0 translate-y-4"
						>
							<div v-if="activeGroup" class="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/50" @click.self="activeGroup = null">
								<div class="bg-white p-6 rounded-2xl shadow-2xl border border-gray-100 w-full max-w-2xl max-h-[85vh] overflow-y-auto">
								<div class="flex items-center justify-between mb-6 sticky top-0 bg-white py-2 z-10">
									<div>
										<h3 class="text-xl font-extrabold text-gray-900">{{ groupedSections[activeGroup.sectionIdx].groups[activeGroup.groupIdx].name }}</h3>
										<!-- Selected / limit counter (always shown) -->
										<p class="text-xs font-bold mt-1">
											<span :class="groupSelectedTotal >= activeGroupQtyLimit ? 'text-green-600' : 'text-blue-600'">
												{{ groupSelectedTotal }}
											</span>
											<span class="text-gray-400"> / {{ activeGroupQtyLimit }} {{ __('selected') }}</span>
										</p>
									</div>
									<div class="flex items-center gap-2">
										<!-- Done button: only for multi-quantity sections. Single-quantity
										     picks auto-close the overlay, so Done would be redundant. -->
										<button
											v-if="activeGroupQtyLimit > 1"
											@click="activeGroup = null"
											class="px-4 py-1.5 bg-blue-600 text-white text-sm font-bold rounded-lg hover:bg-blue-700 transition-colors"
										>
											{{ __('Done') }}
										</button>
										<button @click="activeGroup = null" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
											<svg class="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
											</svg>
										</button>
									</div>
								</div>

								<!-- Attribute Filters -->
								<div v-if="activeGroupAttributes.length > 0" class="mb-10 space-y-8">
									<div v-for="attr in activeGroupAttributes" :key="attr.name" class="bg-gray-50/50 p-4 rounded-2xl border border-gray-100">
										<p class="text-[11px] font-black text-gray-400 uppercase tracking-widest mb-4 flex items-center">
											<span class="w-1.5 h-1.5 bg-blue-500 rounded-full me-2"></span>
											{{ attr.name }}
										</p>
										<div class="flex flex-wrap gap-2.5">
											<button 
												v-for="val in attr.values" 
												:key="val"
												@click="selectAttribute(attr.name, val)"
												:class="[
													'px-5 py-2.5 rounded-xl text-sm font-bold border-2 transition-all duration-200',
													activeGroupFilters[attr.name] === val 
														? 'border-blue-600 bg-blue-600 text-white shadow-lg scale-105' 
														: 'border-white bg-white text-gray-600 hover:border-gray-200 hover:shadow-sm'
												]"
											>
												{{ val }}
											</button>
										</div>
									</div>
								</div>
								
								<div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
									<div
										v-for="v in filteredVariants"
										:key="v.item_code"
										@click="!isVariantDisabled(v) && handleGroupVariantClick(sections[activeGroup.sectionIdx], v)"
										:class="[
											'p-5 rounded-2xl border-2 transition-all text-center flex flex-col items-center justify-center min-h-[100px]',
											isOptionSelected(v)
												? 'border-blue-600 bg-blue-50 ring-4 ring-blue-100/50 cursor-pointer'
												: isVariantDisabled(v)
													? 'border-gray-100 bg-gray-50 opacity-35 cursor-not-allowed'
													: 'border-gray-100 bg-gray-50 hover:border-gray-300 hover:bg-white cursor-pointer'
										]"
									>
										<p :class="['text-sm font-bold leading-tight', isOptionSelected(v) ? 'text-blue-700' : 'text-gray-800']">{{ v.variant_name }}</p>
										<p :class="['text-[11px] mt-2 font-black', isOptionSelected(v) ? 'text-blue-600' : 'text-gray-500']">
											{{ v.extra_price > 0 ? '+' + formatCurrency(v.extra_price) : __('Included') }}
										</p>

										<!-- Variant Selection Indicator -->
										<div v-if="isOptionSelected(v)" class="mt-3 flex items-center gap-3" @click.stop>
											<div class="bg-blue-600 text-white rounded-full p-0.5">
												<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
												</svg>
											</div>

											<!-- Quantity Control inside Overlay (always visible when selected) -->
											<div class="flex items-center gap-2 bg-white rounded-lg border border-blue-200 p-1 shadow-sm">
												<button @click.stop="decreaseQty(v)" class="w-6 h-6 flex items-center justify-center bg-gray-50 rounded hover:bg-gray-100">-</button>
												<span class="text-xs font-black text-blue-700 w-4 text-center">{{ getOptionQty(v) }}</span>
												<button
													@click.stop="increaseQty(sections[activeGroup.sectionIdx], v)"
													:disabled="groupSelectedTotal >= activeGroupQtyLimit"
													class="w-6 h-6 flex items-center justify-center bg-blue-50 text-blue-600 rounded hover:bg-blue-100 disabled:opacity-40 disabled:cursor-not-allowed"
												>+</button>
											</div>
										</div>
									</div>
								</div>
								</div>
							</div>
						</transition>

						<div v-for="(section, sIdx) in groupedSections" :key="sIdx" class="section-container bg-gray-50 rounded-xl p-4 border border-gray-100">
							<div class="flex items-center justify-between mb-4 border-b border-gray-200 pb-2">
								<div>
									<h3 class="text-lg font-bold text-gray-900">{{ section.name }}</h3>
									<div class="flex gap-2 mt-1">
										<span v-if="section.is_required" class="px-2 py-0.5 bg-red-100 text-red-700 text-[10px] font-bold rounded-full uppercase tracking-wider">
											{{ __('Required') }}
										</span>
										<!-- Live counter for multi-choice sections -->
										<span v-if="section.max_qty > 1" class="text-[11px] font-bold">
											<span :class="getSectionSelectedCount(section) >= (section.min_qty || 1) ? 'text-green-600' : 'text-blue-600'">
												{{ getSectionSelectedCount(section) }}
											</span>
											<span class="text-gray-400"> / {{ section.max_qty }}</span>
										</span>
										<!-- Single-choice: show selected qty / item max qty when an item with qty>1 is picked -->
										<span v-else-if="getSectionSelectedCount(section) > 0" class="text-[11px] font-bold">
											<span :class="getSectionSelectedCount(section) >= (section.options.find(o => selections[o.item_code])?.qty || 1) ? 'text-green-600' : 'text-blue-600'">
												{{ getSectionSelectedCount(section) }}
											</span>
											<span class="text-gray-400"> / {{ section.options.find(o => selections[o.item_code])?.qty || 1 }}</span>
										</span>
										<span v-else class="text-[11px] text-gray-500 font-medium">
											{{ section.min_qty > 0 ? __('Min: {0}', [section.min_qty]) : '' }}
										</span>
									</div>
								</div>
								<div v-if="isSectionComplete(section)" class="text-green-600">
									<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
										<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
									</svg>
								</div>
							</div>

							<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
								<div
									v-for="(group, gIdx) in section.groups"
									:key="gIdx"
									@click="!isTileDisabled(sections[sIdx], group) && handleGroupClick(sIdx, gIdx, group)"
									:class="[
										'relative group rounded-xl border-2 transition-all duration-200 overflow-hidden bg-white shadow-sm',
										isGroupSelected(group)
											? 'border-blue-600 ring-2 ring-blue-100 cursor-pointer'
											: isTileDisabled(sections[sIdx], group)
												? 'border-gray-100 opacity-35 cursor-not-allowed'
												: 'border-transparent hover:border-gray-300 cursor-pointer'
									]"
								>
									<!-- Selection Checkmark -->
									<div v-if="isGroupSelected(group)" class="absolute top-2 right-2 z-10">
										<div class="bg-blue-600 text-white rounded-full p-0.5">
											<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
											</svg>
										</div>
									</div>

									<div class="aspect-square w-full bg-gray-100 flex items-center justify-center overflow-hidden">
										<img v-if="group.image" :src="group.image" class="w-full h-full object-cover" />
										<svg v-else class="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
										</svg>
									</div>

									<div class="p-3.5">
										<p class="text-sm font-black text-gray-900 line-clamp-2 min-h-[2.5rem] uppercase tracking-tight">{{ group.name || group.item_name }}</p>
										
										<!-- Variant Indicator -->
										<div v-if="group.is_group" class="mt-1">
											<div v-if="!isGroupSelected(group)" class="flex items-center gap-1">
												<span class="text-xs text-gray-500 font-bold italic">{{ __('Choose flavor') }}</span>
												<svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
												</svg>
											</div>
											<!-- Multi-choice: show all selected variants with counts -->
											<div v-else-if="section.max_qty > 1" class="space-y-0.5">
												<div v-for="opt in group.options.filter(o => selections[o.item_code])" :key="opt.item_code" class="flex items-center justify-between gap-1">
													<span class="text-[10px] font-bold text-blue-700 truncate">
														{{ selections[opt.item_code].quantity }}x {{ opt.variant_name || opt.item_name }}
													</span>
												</div>
											</div>
											<!-- Single-choice: show selected variant + qty controls if item qty > 1 -->
											<div v-else class="flex items-center justify-between gap-1">
												<span class="text-xs font-black text-blue-700 truncate">
													{{ getOptionQty(getSelectedVariantInGroup(group)) }}x {{ getSelectedVariantInGroup(group).variant_name || getSelectedVariantInGroup(group).item_name }}
												</span>
												<div v-if="getSelectedVariantInGroup(group).qty > 1" class="flex items-center gap-1" @click.stop>
													<button @click="decreaseQty(getSelectedVariantInGroup(group))" class="w-5 h-5 flex items-center justify-center bg-gray-100 rounded hover:bg-gray-200 font-bold text-xs">-</button>
													<button @click="increaseQty(section, getSelectedVariantInGroup(group))" class="w-5 h-5 flex items-center justify-center bg-blue-100 text-blue-600 rounded hover:bg-blue-200 font-bold text-xs">+</button>
												</div>
											</div>
										</div>

										<div v-if="!group.is_group" class="flex items-center justify-between mt-2">
											<span class="text-xs font-black text-blue-700">
												{{ group.extra_price > 0 ? '+' + formatCurrency(group.extra_price) : __('Included') }}
											</span>
											
											<!-- Quantity Control if section allows multi or item has qty > 1 -->
											<div v-if="(section.max_qty > 1 || group.qty > 1) && isOptionSelected(group)" class="flex items-center gap-2" @click.stop>
												<button @click="decreaseQty(group)" class="w-6 h-6 flex items-center justify-center bg-gray-100 rounded hover:bg-gray-200 active:scale-95 transition-all font-bold">-</button>
												<span class="text-xs font-black w-4 text-center">{{ getOptionQty(group) }}</span>
												<button @click="increaseQty(section, group)" class="w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-600 rounded hover:bg-blue-200 active:scale-95 transition-all font-bold">+</button>
											</div>
										</div>
									</div>

									<!-- Variant Selection Overlay if Template (Existing Logic) -->
									<div v-if="group.has_variants && isOptionSelected(group)" class="border-t border-gray-100 p-2 bg-blue-50/50">
										<button 
											@click.stop="openVariantSelector(group)"
											class="w-full py-1 text-[10px] font-bold text-blue-700 bg-white border border-blue-200 rounded hover:bg-blue-50 transition-colors uppercase tracking-tight"
										>
											{{ group.selected_variant ? group.selected_variant.item_name : __('Select Style') }}
										</button>
									</div>
								</div>
							</div>
						</div>
					</div>

					<div v-else class="text-center py-12">
						<div class="bg-gray-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
							<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
							</svg>
						</div>
						<p class="text-gray-600 font-medium">{{ __('No components configured for this combo.') }}</p>
					</div>
				</div>

				<!-- Right: Summary Sidebar -->
				<div class="w-full md:w-72 bg-gray-50 rounded-2xl p-5 border border-gray-200 flex flex-col">
					<div class="flex-1 overflow-y-auto mb-4 pr-1 custom-scrollbar">
						<h4 class="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2">
							<svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
							</svg>
							{{ __('Your Selection') }}
						</h4>
						
						<ul class="space-y-3">
							<li v-if="selectedOptions.length === 0" class="text-xs text-gray-500 italic py-4 text-center">
								{{ __('No items selected yet') }}
							</li>
							<li v-for="(sel, idx) in selectedOptions" :key="idx" class="flex justify-between items-start group">
								<div class="flex-1">
									<div class="flex items-center gap-2">
										<span class="text-xs font-bold text-gray-800">{{ sel.quantity }}x</span>
										<span class="text-xs font-medium text-gray-700 leading-tight">{{ sel.variant_name || sel.item_name }}</span>
									</div>
									<div v-if="sel.selected_variant" class="text-[10px] text-gray-500 mt-0.5 ml-6">
										• {{ sel.selected_variant.variant_name || sel.selected_variant.item_name }}
									</div>
								</div>
								<span v-if="sel.extra_price > 0" class="text-[10px] font-bold text-blue-600 whitespace-nowrap ml-2">
									+{{ formatCurrency(sel.extra_price * sel.quantity) }}
								</span>
							</li>
						</ul>
					</div>

					<div class="pt-4 border-t border-gray-200 space-y-4">
						<div class="space-y-1.5">
							<div class="flex justify-between items-center text-xs text-gray-500">
								<span>{{ __('Base Price') }}</span>
								<span>{{ formatCurrency(item?.rate || 0) }}</span>
							</div>
							<div class="flex justify-between items-center text-xs text-blue-600 font-medium">
								<span>{{ __('Extras') }}</span>
								<span>+{{ formatCurrency(totalExtras) }}</span>
							</div>
							<div class="flex justify-between items-center pt-2">
								<span class="text-sm font-bold text-gray-900">{{ __('Total Price') }}</span>
								<span class="text-lg font-black text-blue-600">{{ formatCurrency(grandTotal) }}</span>
							</div>
						</div>

						<div class="flex gap-2">
							<div class="flex-1 h-10 border border-gray-300 rounded-lg flex items-center overflow-hidden bg-white">
								<button @click="comboQty = Math.max(1, comboQty - 1)" class="w-8 h-full bg-gray-50 hover:bg-gray-100 active:bg-gray-200 transition-colors border-r">-</button>
								<div class="flex-1 text-center text-sm font-bold">{{ comboQty }}</div>
								<button @click="comboQty++" class="w-8 h-full bg-gray-50 hover:bg-gray-100 active:bg-gray-200 transition-colors border-l">+</button>
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
				<Button 
					class="flex-1" 
					variant="solid" 
					theme="blue" 
					@click="confirm" 
					:disabled="!isValid"
					:loading="submitting"
				>
					{{ __('Add {0} to Order', [comboQty]) }}
				</Button>
			</div>
		</template>
	</Dialog>

	<!-- Nested Variant Selector -->
	<ItemSelectionDialog
		v-model="showVariantDialog"
		v-if="currentTemplateItem"
		:item="currentTemplateItem"
		mode="variant"
		:pos-profile="posProfile"
		:currency="currency"
		@option-selected="handleVariantSelected"
	/>

	<!-- Recursive Combo Selector for Nested Bundles -->
	<ComboSelectionDialog
		v-model="showNestedComboDialog"
		v-if="currentNestedItem"
		:item="currentNestedItem"
		:pos-profile="posProfile"
		:price-list="priceList"
		:currency="currency"
		@option-selected="handleNestedComboSelected"
	/>
</template>

<script setup>
import { computed, ref, watch, onMounted } from "vue"
import { Dialog, Button } from "frappe-ui"
import { call } from "@/utils/apiWrapper"
import { DEFAULT_CURRENCY, formatCurrency as formatCurrencyUtil } from "@/utils/currency"
import ItemSelectionDialog from "./ItemSelectionDialog.vue"

const props = defineProps({
	modelValue: Boolean,
	item: Object,
	posProfile: String,
	priceList: String,
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
const submitting = ref(false)
const sections = ref([])
const selections = ref({}) // key: item_code, value: selection object
const comboQty = ref(1)

const dialogTitle = computed(() => {
	return props.item?.item_name || __('Customize Combo')
})

// Variant Selection State
const showVariantDialog = ref(false)
const currentTemplateItem = ref(null)
const currentOptionForVariant = ref(null)

// Grouping State
const activeGroup = ref(null) // { sectionIdx, groupIdx }
const activeGroupFilters = ref({}) // attribute: value

const activeGroupAttributes = computed(() => {
	if (!activeGroup.value) return []
	const group = groupedSections.value[activeGroup.value.sectionIdx].groups[activeGroup.value.groupIdx]
	const attrs = {}
	group.options.forEach(opt => {
		opt.attributes?.forEach(a => {
			if (!attrs[a.attribute]) attrs[a.attribute] = new Set()
			attrs[a.attribute].add(a.value)
		})
	})
	return Object.entries(attrs).map(([name, values]) => ({
		name,
		values: Array.from(values)
	}))
})

const filteredVariants = computed(() => {
	if (!activeGroup.value) return []
	const group = groupedSections.value[activeGroup.value.sectionIdx].groups[activeGroup.value.groupIdx]
	return group.options.filter(opt => {
		return Object.entries(activeGroupFilters.value).every(([attr, val]) => {
			return opt.attributes?.some(a => a.attribute === attr && a.value === val)
		})
	})
})

// Total qty currently selected across all variants in the active group
const groupSelectedTotal = computed(() => {
	if (!activeGroup.value) return 0
	const group = groupedSections.value[activeGroup.value.sectionIdx].groups[activeGroup.value.groupIdx]
	return group.options.reduce((sum, opt) => sum + (selections.value[opt.item_code]?.quantity || 0), 0)
})

// Max qty allowed inside the active group's overlay
const activeGroupQtyLimit = computed(() => {
	if (!activeGroup.value) return Infinity
	const section = sections.value[activeGroup.value.sectionIdx]
	if (section.max_qty > 1) return section.max_qty
	// Single-choice section: use the currently selected variant's qty, fallback to first variant
	const group = groupedSections.value[activeGroup.value.sectionIdx].groups[activeGroup.value.groupIdx]
	const selectedOpt = group.options.find(o => selections.value[o.item_code])
	return (selectedOpt || group.options[0])?.qty || 1
})

// The lock_group value of the first selected variant in the active group (or "" if none)
const activeLockGroupValue = computed(() => {
	if (!activeGroup.value) return ""
	const group = groupedSections.value[activeGroup.value.sectionIdx]?.groups[activeGroup.value.groupIdx]
	if (!group) return ""
	const firstSelected = group.options.find(o => selections.value[o.item_code])
	return firstSelected?.lock_group || ""
})

// Attributes that must match across all selections in a multi-choice group (e.g. النوع=ريجويلر)
const lockedGroupAttributes = computed(() => {
	if (!activeGroup.value) return {}
	const section = sections.value[activeGroup.value.sectionIdx]
	if (section.max_qty <= 1) return {}
	const group = groupedSections.value[activeGroup.value.sectionIdx]?.groups[activeGroup.value.groupIdx]
	if (!group) return {}
	const selected = group.options.filter(o => selections.value[o.item_code])
	if (selected.length === 0) return {}

	// If the group has explicit locked_attributes configured in the product editor, use those
	const configuredLocked = group.locked_attributes || []
	if (configuredLocked.length > 0) {
		const locked = {}
		const firstSelected = selected[0]
		configuredLocked.forEach(attrName => {
			const match = firstSelected.attributes?.find(a => a.attribute === attrName)
			if (match) locked[attrName] = match.value
		})
		return locked
	}

	// Fallback: auto-detect by finding attributes identical across ALL selected variants
	// Requires at least 2 selections — 1 selection trivially matches everything and would wrongly lock all
	if (selected.length < 2) return {}
	const locked = {}
	const firstAttrs = selected[0].attributes || []
	firstAttrs.forEach(a => {
		const allSame = selected.every(opt =>
			opt.attributes?.some(attr => attr.attribute === a.attribute && attr.value === a.value)
		)
		if (allSame) locked[a.attribute] = a.value
	})
	return locked
})

// Nested Combo State
const showNestedComboDialog = ref(false)
const currentNestedItem = ref(null)
const currentOptionForNested = ref(null)

const groupedSections = computed(() => {
	return sections.value.map((section, sIdx) => {
		const groups = []
		const groupMap = {}

		section.options.forEach(opt => {
			// Only group non-standalone variants that belong to a template
			const groupKey = !opt.is_standalone && opt.variant_of ? opt.variant_of : null

			if (groupKey) {
				const baseName = opt.template_name || opt.variant_of

				// Build a clean variant label from attributes, fallback to stripping template name
				let variantName = opt.item_name
				if (opt.attributes && opt.attributes.length > 0) {
					variantName = opt.attributes.map(a => a.value).join(" - ")
				} else if (opt.template_name && variantName.startsWith(opt.template_name)) {
					variantName = variantName.slice(opt.template_name.length).replace(/^[\s(-]+/, "").replace(/\)+$/, "")
				}

				if (!groupMap[groupKey]) {
					// Parse locked_attributes from the first variant in this group
					let lockedAttrs = []
					if (opt.locked_attributes) {
						try { lockedAttrs = Array.isArray(opt.locked_attributes) ? opt.locked_attributes : JSON.parse(opt.locked_attributes) } catch {}
					}
					groupMap[groupKey] = {
						id: groupKey,
						name: baseName,
						image: opt.image,
						is_group: true,
						sectionIdx: sIdx,
						locked_attributes: lockedAttrs,
						options: []
					}
					groups.push(groupMap[groupKey])
				}
				groupMap[groupKey].options.push({
					...opt,
					variant_name: variantName,
				})
			} else {
				groups.push({
					...opt,
					is_group: false,
				})
			}
		})

		return { ...section, groups }
	})
})

/**
 * Load combo components from API
 */
async function loadComboData() {
	if (!props.item?.item_code) return
	
	loading.value = true
	sections.value = []
	try {
		const res = await call("ecs_posnext.api.items.get_combo_components", {
			item_code: props.item.item_code,
			pos_profile: props.posProfile,
			price_list: props.priceList
		})
		sections.value = res?.message || res || []
		
		// Reset selections and apply defaults
		selections.value = {}
		sections.value.forEach(section => {
			section.options.forEach(opt => {
				if (opt.default_selected) {
					selections.value[opt.item_code] = {
						...opt,
						quantity: opt.qty || 1,
						selected_variant: null
					}
				}
			})
		})
	} catch (error) {
		console.error("Error loading combo components:", error)
	} finally {
		loading.value = false
	}
}

// Watch for dialog open to load data
watch(() => props.modelValue, (val) => {
	if (val) {
		loadComboData()
		comboQty.value = 1
		activeGroup.value = null
	} else {
		activeGroup.value = null
	}
})

onMounted(() => {
	if (props.modelValue) {
		loadComboData()
	}
})

function isOptionSelected(opt) {
	return !!selections.value[opt.item_code]
}

// A variant is disabled when it conflicts with the current selection's locked attributes or lock_group
function isVariantDisabled(variant) {
	if (isOptionSelected(variant)) return false
	if (!activeGroup.value) return false
	const section = sections.value[activeGroup.value.sectionIdx]

	if (section.max_qty > 1) {
		// lock_group: if this variant has a group tag, disable variants with a DIFFERENT group tag
		if (variant.lock_group) {
			const activeLockGroup = activeLockGroupValue.value
			if (activeLockGroup && activeLockGroup !== variant.lock_group) return true
		}
		// Fallback: attribute-level locking (for templates with multiple attributes)
		const locked = lockedGroupAttributes.value
		if (Object.keys(locked).length === 0) return false
		return Object.entries(locked).some(([attr, val]) =>
			variant.attributes?.some(a => a.attribute === attr && a.value !== val)
		)
	}

	// Single-choice: only disable others when the selected variant has qty > 1
	// (user used + to commit to a quantity — switching would lose that intent)
	// When qty === 1, allow clicking another variant to switch selection
	const selectedOpt = groupedSections.value[activeGroup.value.sectionIdx]?.groups[activeGroup.value.groupIdx]?.options.find(o => selections.value[o.item_code])
	if (!selectedOpt) return false
	return (selections.value[selectedOpt.item_code]?.quantity || 0) > 1
}

function getOptionQty(opt) {
	return selections.value[opt.item_code]?.quantity || 0
}

function isGroupSelected(group) {
	if (!group.is_group) return isOptionSelected(group)
	return group.options.some(opt => isOptionSelected(opt))
}

// For standalone (non-overlay) tiles in multi-choice sections:
// disable if any SELECTED item in the section has a DIFFERENT lock_group
function isTileDisabled(section, group) {
	if (isGroupSelected(group)) return false
	if (section.max_qty <= 1) return false
	const tileLockGroup = group.is_group ? null : group.lock_group
	if (!tileLockGroup) return false
	return section.options.some(o => {
		if (!selections.value[o.item_code]) return false
		return o.lock_group && o.lock_group !== tileLockGroup
	})
}

function getSelectedVariantInGroup(group) {
	if (!group.is_group) return null
	return group.options.find(opt => isOptionSelected(opt))
}

function handleGroupClick(sIdx, gIdx, group) {
	if (group.is_group) {
		activeGroup.value = { sectionIdx: sIdx, groupIdx: gIdx }
	} else if (group.has_variants || (group.addons && group.addons.length > 0)) {
		// Items with variants or addons → open picker dialog
		openVariantSelector(group)
	} else if (group.is_bundle && group.show_bundle_in_pos) {
		// Bundles that should be expanded → nested combo dialog
		openNestedComboSelector(group)
	} else {
		// Simple items and bundles with show_bundle_in_pos=false → select directly
		toggleOption(sections.value[sIdx], group)
	}
}

function openNestedComboSelector(opt) {
	currentOptionForNested.value = opt
	currentNestedItem.value = {
		item_code: opt.item_code,
		item_name: opt.item_name,
		rate: opt.extra_price || 0,
		image: opt.image
	}
	showNestedComboDialog.value = true
}

function handleNestedComboSelected(payload) {
	if (currentOptionForNested.value) {
		const opt = currentOptionForNested.value
		// Select the parent option if not already selected
		if (!isOptionSelected(opt)) {
			// Find section
			const section = sections.value.find(s => s.options.some(o => o.item_code === opt.item_code))
			if (section) toggleOption(section, opt)
		}
		
		if (selections.value[opt.item_code]) {
			selections.value[opt.item_code].components = payload.components
			// Update extra price if the nested combo added more extras
			if (payload.extra_price) {
				selections.value[opt.item_code].extra_price = (opt.extra_price || 0) + payload.extra_price
			}
		}
	}
	showNestedComboDialog.value = false
}

function handleGroupVariantClick(section, variant) {
	const isMultiChoice = section.max_qty > 1

	if (variant.has_variants) {
		openVariantSelector(variant)
		return
	} else if (variant.is_bundle) {
		openNestedComboSelector(variant)
		return
	}

	if (!isMultiChoice && activeGroup.value !== null) {
		// Single-choice section with a group overlay open:
		// Allow multiple variants within this group (up to the group's qty cap),
		// but clear any selections that belong to OTHER groups in the section.
		const currentGroup = groupedSections.value[activeGroup.value.sectionIdx].groups[activeGroup.value.groupIdx]
		const currentGroupCodes = new Set(currentGroup.options.map(o => o.item_code))

		// Evict selections from other groups
		section.options.forEach(o => {
			if (!currentGroupCodes.has(o.item_code)) delete selections.value[o.item_code]
		})

		if (isOptionSelected(variant)) {
			// Already selected — user uses + button to increase qty
		} else {
			// Single-flavor rule: clear any OTHER variant in this group first
			currentGroup.options.forEach(o => {
				if (o.item_code !== variant.item_code) delete selections.value[o.item_code]
			})
			selections.value[variant.item_code] = { ...variant, quantity: 1, selected_variant: null }
			// Single-quantity item: nothing more to do here, auto-close the overlay
			// so the user doesn't need a Done button.
			if ((variant.qty || 1) <= 1) {
				activeGroup.value = null
				return
			}
		}
		// Keep the overlay open so user can increase qty with the + button
	} else if (isMultiChoice && isOptionSelected(variant)) {
		// Multi-choice: clicking a selected variant does nothing — use +/− buttons
	} else {
		toggleOption(section, variant)
		// Auto-close only for a direct single-choice pick (no group overlay)
		if (!isMultiChoice) activeGroup.value = null
	}
}

function selectAttribute(name, val) {
	activeGroupFilters.value[name] = val

	// Check if selection results in unique variant
	const section = sections.value[activeGroup.value.sectionIdx]
	const group = groupedSections.value[activeGroup.value.sectionIdx].groups[activeGroup.value.groupIdx]

	const filtered = group.options.filter(opt => {
		return Object.entries(activeGroupFilters.value).every(([attr, v]) => {
			return opt.attributes?.some(a => a.attribute === attr && a.value === v)
		})
	})

	if (filtered.length === 1) {
		handleGroupVariantClick(section, filtered[0])
		// Reset attribute filters after auto-select so the full variant list shows again
		activeGroupFilters.value = {}
	}
}

function toggleOption(section, opt) {
	const alreadySelected = isOptionSelected(opt)
	
	if (alreadySelected) {
		// Deselect if not required or if min_qty is met
		const currentCount = getSectionSelectedCount(section)
		if (!section.is_required || currentCount > section.min_qty) {
			delete selections.value[opt.item_code]
		}
	} else {
		// Select
		const currentCount = getSectionSelectedCount(section)
		if (section.max_qty === 1) {
			// Single choice: deselect others in section, start at 1 (user counts up to opt.qty)
			section.options.forEach(o => delete selections.value[o.item_code])
			selections.value[opt.item_code] = {
				...opt,
				quantity: 1,
				selected_variant: null
			}
		} else if (currentCount < section.max_qty) {
			// Multi choice: block if lock_group conflicts with any already-selected item
			if (opt.lock_group) {
				const conflicting = section.options.some(o =>
					selections.value[o.item_code] && o.lock_group && o.lock_group !== opt.lock_group
				)
				if (conflicting) return
			}
			selections.value[opt.item_code] = {
				...opt,
				quantity: 1,
				selected_variant: null
			}
		}
	}
}

function getSectionSelectedCount(section) {
	return section.options.reduce((sum, opt) => {
		return sum + (selections.value[opt.item_code]?.quantity || 0)
	}, 0)
}

function getSectionDistinctCount(section) {
	return section.options.filter(o => selections.value[o.item_code]).length
}

function isSectionComplete(section) {
	if (!section.is_required) return true
	const min = section.min_qty || 1
	const max = section.max_qty

	if (section.max_qty === 1) {
		// Single-choice: validate by number of distinct options, not total qty
		const distinct = getSectionDistinctCount(section)
		return distinct >= min
	}

	const count = getSectionSelectedCount(section)
	if (max) {
		return count >= min && count <= max
	}
	return count >= min
}

function increaseQty(section, opt) {
	if (!selections.value[opt.item_code]) return

	const sel = selections.value[opt.item_code]
	const maxPerItem = sel.qty || Infinity

	if (section.max_qty === 1) {
		// Single-choice section: use the group qty limit (activeGroupQtyLimit)
		// rather than section.max_qty=1 which only means "1 distinct group"
		const qtyLimit = activeGroupQtyLimit.value < Infinity ? activeGroupQtyLimit.value : maxPerItem
		const groupTotal = activeGroup.value
			? (groupedSections.value[activeGroup.value.sectionIdx]?.groups[activeGroup.value.groupIdx]?.options || [])
				.reduce((sum, o) => sum + (selections.value[o.item_code]?.quantity || 0), 0)
			: sel.quantity
		if (groupTotal < qtyLimit && sel.quantity < maxPerItem) sel.quantity++
	} else {
		// Multi-choice: cap only by section total; per-item qty field is a default/unit hint,
		// not a hard limit — the section max_qty is the real ceiling for each item type too.
		const sectionTotalQty = section.options.reduce((sum, o) => {
			return sum + (selections.value[o.item_code]?.quantity || 0)
		}, 0)
		const perItemMax = Math.max(section.max_qty || 1, maxPerItem)
		if (sectionTotalQty < (section.max_qty || 999) && sel.quantity < perItemMax) {
			sel.quantity++
		}
	}
}

function decreaseQty(opt) {
	if (!selections.value[opt.item_code]) return
	if (selections.value[opt.item_code].quantity > 1) {
		selections.value[opt.item_code].quantity--
	} else {
		// qty would reach 0 — deselect the variant entirely
		delete selections.value[opt.item_code]
	}
}

function openVariantSelector(opt) {
	currentOptionForVariant.value = opt
	currentTemplateItem.value = {
		...opt,
		has_variants: opt.has_variants || 1
	}
	showVariantDialog.value = true
}

function handleVariantSelected(variant) {
	if (!currentOptionForVariant.value) return
	
	const itemCode = currentOptionForVariant.value.item_code
	
	// If not already selected, select it first
	if (!selections.value[itemCode]) {
		// Find the section this option belongs to
		const section = sections.value.find(s => 
			s.options.some(o => o.item_code === itemCode)
		)
		if (section) {
			toggleOption(section, currentOptionForVariant.value)
		}
	}
	
	if (selections.value[itemCode]) {
		selections.value[itemCode].selected_variant = {
			...variant,
			// Ensure we have labels for the summary
			label: variant.item_name || variant.label
		}
	}
	showVariantDialog.value = false
}

const selectedOptions = computed(() => {
	return Object.values(selections.value)
})

const totalExtras = computed(() => {
	return selectedOptions.value.reduce((sum, opt) => {
		return sum + (opt.extra_price * opt.quantity)
	}, 0)
})

const grandTotal = computed(() => {
	return (props.item?.rate || 0) + totalExtras.value
})

const isValid = computed(() => {
	if (loading.value) return false
	// All required sections must be complete
	return sections.value.every(section => isSectionComplete(section))
})

function confirm() {
	if (!isValid.value) return
	
	const components = selectedOptions.value.map(opt => ({
		item_code: opt.selected_variant ? opt.selected_variant.item_code : opt.item_code,
		item_name: opt.selected_variant ? opt.selected_variant.label : opt.item_name,
		quantity: opt.quantity,
		extra_price: opt.extra_price,
		is_standalone: opt.is_standalone,
		stock_uom: opt.stock_uom,
		is_stock_item: opt.is_stock_item,
		selected_addons: opt.selected_variant?.selected_addons || [],
		removed_ingredients: opt.selected_variant?.removed_ingredients || [],
		removed_ingredient_names: opt.selected_variant?.removed_ingredient_names || [],
		ingredients: opt.selected_variant?.ingredients || opt.ingredients || [],
		notes: opt.selected_variant?.notes || ""
	}))

	const payload = {
		type: "combo",
		item_code: props.item.item_code,
		quantity: comboQty.value,
		components: components,
		extra_price: totalExtras.value,
		rate: grandTotal.value
	}

	emit("option-selected", payload)
}

function cancel() {
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
	background: #f1f1f1;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
	background: #cbd5e1;
	border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
	background: #94a3b8;
}

.section-container:last-child {
	margin-bottom: 2rem;
}
</style>
