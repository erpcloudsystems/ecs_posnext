<template>
	<div class="flex flex-col bg-gray-50 min-h-screen">
		<!-- Header -->
		<header class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-20">
			<div class="flex items-center gap-3">
				<button @click="goBack" class="p-2 rounded-lg hover:bg-gray-100 active:bg-gray-200 transition-colors touch-manipulation">
					<svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
					</svg>
				</button>
				<div>
					<h1 class="text-base sm:text-lg font-bold text-gray-900">{{ __('Item Manager') }}</h1>
					<p class="text-[10px] sm:text-xs text-gray-500">{{ stepLabel }}</p>
				</div>
			</div>
			<!-- Step indicator -->
			<div v-if="step !== 'list'" class="flex items-center gap-1.5">
				<div
					v-for="s in totalSteps"
					:key="s"
					:class="[
						'w-2 h-2 rounded-full transition-colors',
						s <= currentStepIndex ? 'bg-blue-500' : 'bg-gray-300'
					]"
				/>
			</div>
		</header>

		<!-- Wizard Content -->
		<main class="flex-1 overflow-y-auto p-4 sm:p-6 max-w-4xl mx-auto w-full">

			<!-- ============ LIST VIEW ============ -->
			<div v-if="step === 'list'" class="space-y-4">
				<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
					<div>
						<h2 class="text-sm sm:text-base font-semibold text-gray-800">{{ __('Items') }}</h2>
						<p class="text-xs text-gray-500">{{ __('{0} item(s)', [listTotal]) }}</p>
					</div>
					<button
						@click="router.push({ name: 'ItemManager', params: { itemId: 'new' } })"
						class="px-4 py-2.5 rounded-xl bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 active:bg-blue-700 transition-colors touch-manipulation"
					>
						{{ __('New Item') }}
					</button>
				</div>

				<div class="relative">
					<div class="absolute inset-y-0 start-0 ps-3 flex items-center pointer-events-none">
						<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
						</svg>
					</div>
					<input
						v-model="listSearch"
						@input="searchListItems"
						type="text"
						:placeholder="__('Search item code or name...')"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 ps-10 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
				</div>

				<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
					<select
						v-model="filterGroup"
						@change="refreshList"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
					>
						<option value="">{{ __('All Groups') }}</option>
						<option v-for="g in itemGroups" :key="g.name" :value="g.name">{{ g.name }}</option>
					</select>
					<select
						v-model="filterClassification"
						@change="refreshList"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
					>
						<option value="">{{ __('All Classifications') }}</option>
						<option v-for="c in itemClassifications" :key="c.name" :value="c.name">{{ c.name }}</option>
					</select>
				</div>

				<div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
					<div v-if="listLoading" class="flex items-center justify-center py-12">
						<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
					</div>
					<div v-else-if="items.length === 0" class="text-center py-12 text-sm text-gray-500">
						{{ __('No items found') }}
					</div>
					<div v-else class="overflow-x-auto">
						<table class="w-full text-xs sm:text-sm">
							<thead class="bg-gray-50 text-gray-500">
								<tr>
									<th class="text-start font-semibold px-3 py-2">{{ __('Code') }}</th>
									<th class="text-start font-semibold px-3 py-2">{{ __('Name') }}</th>
									<th class="text-start font-semibold px-3 py-2">{{ __('Group') }}</th>
									<th class="text-start font-semibold px-3 py-2">{{ __('Classification') }}</th>
									<th class="text-start font-semibold px-3 py-2">{{ __('Type') }}</th>
									<th class="text-start font-semibold px-3 py-2">{{ __('Price Lists') }}</th>
									<th class="text-end font-semibold px-3 py-2">{{ __('Actions') }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								<tr v-for="item in items" :key="item.name" class="hover:bg-gray-50">
									<td class="px-3 py-2 font-medium text-blue-600">
										<a :href="`/app/item/${encodeURIComponent(item.name)}`" target="_top">{{ item.item_code }}</a>
									</td>
									<td class="px-3 py-2 text-gray-800">{{ item.item_name }}</td>
									<td class="px-3 py-2 text-gray-600">{{ item.item_group }}</td>
									<td class="px-3 py-2 text-gray-600">{{ item.custom_item_classification || '-' }}</td>
									<td class="px-3 py-2 text-gray-600">{{ itemTypeLabel(item) }}</td>
									<td class="px-3 py-2 text-gray-600">
										<div v-if="item.prices?.length" class="space-y-0.5">
											<div v-for="price in item.prices.slice(0, 3)" :key="`${item.name}-${price.price_list}`">
												<span class="font-medium">{{ price.price_list }}:</span>
												{{ price.price_list_rate }}
											</div>
										</div>
										<span v-else class="text-gray-400">{{ __('No price') }}</span>
									</td>
									<td class="px-3 py-2">
										<div class="flex justify-end gap-1">
											<button
												@click="router.push({ name: 'ItemManager', params: { itemId: item.item_code || item.name } })"
												class="px-2 py-1 rounded border border-gray-300 text-[11px] font-medium text-gray-700 hover:bg-gray-100"
											>
												{{ __('Edit') }}
											</button>
											<button
												@click="duplicateItem(item)"
												class="px-2 py-1 rounded border border-gray-300 text-[11px] font-medium text-gray-700 hover:bg-gray-100"
											>
												{{ __('Duplicate') }}
											</button>
											<button
												@click="viewBundle(item)"
												class="px-2 py-1 rounded border border-gray-300 text-[11px] font-medium text-gray-700 hover:bg-gray-100"
											>
												{{ __('Bundle') }}
											</button>
										</div>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
					<div class="px-3 py-2 bg-gray-50 border-t border-gray-200 flex items-center justify-between gap-3">
						<button
							@click="prevListPage"
							:disabled="listStart === 0"
							class="px-3 py-1.5 rounded-lg bg-white border border-gray-300 text-xs font-medium text-gray-700 disabled:opacity-50"
						>
							{{ __('Previous') }}
						</button>
						<span class="text-xs text-gray-500">
							{{ listTotal ? listStart + 1 : 0 }} - {{ Math.min(listStart + listPageLength, listTotal) }} / {{ listTotal }}
						</span>
						<button
							@click="nextListPage"
							:disabled="listStart + listPageLength >= listTotal"
							class="px-3 py-1.5 rounded-lg bg-white border border-gray-300 text-xs font-medium text-gray-700 disabled:opacity-50"
						>
							{{ __('Next') }}
						</button>
					</div>
				</div>
			</div>

			<!-- ============ STEP 1: Choose Type ============ -->
			<div v-else-if="step === 'type'" class="space-y-4">
				<h2 class="text-sm sm:text-base font-semibold text-gray-800 text-center">{{ __('What are you creating?') }}</h2>
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mt-4">
					<!-- Normal Meal -->
					<button
						@click="selectType('normal')"
						class="group flex flex-col items-center p-6 rounded-2xl border-2 border-gray-200 bg-white hover:border-blue-400 hover:shadow-lg active:scale-[0.98] transition-all duration-150 touch-manipulation"
					>
						<div class="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-3 group-hover:bg-blue-100 transition-colors">
							<svg class="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
							</svg>
						</div>
						<span class="text-sm font-semibold text-gray-800">{{ __('Normal Item') }}</span>
						<span class="text-[10px] sm:text-xs text-gray-500 mt-1 text-center">{{ __('Single item or item with variants') }}</span>
					</button>
					<!-- Combo -->
					<button
						@click="selectType('combo')"
						class="group flex flex-col items-center p-6 rounded-2xl border-2 border-gray-200 bg-white hover:border-purple-400 hover:shadow-lg active:scale-[0.98] transition-all duration-150 touch-manipulation"
					>
						<div class="w-16 h-16 rounded-2xl bg-purple-50 flex items-center justify-center mb-3 group-hover:bg-purple-100 transition-colors">
							<svg class="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
							</svg>
						</div>
						<span class="text-sm font-semibold text-gray-800">{{ __('Combo / Bundle') }}</span>
						<span class="text-[10px] sm:text-xs text-gray-500 mt-1 text-center">{{ __('Multiple items sold together as one') }}</span>
					</button>
				</div>
			</div>

			<!-- ============ STEP 2: Normal Sub-type ============ -->
			<div v-else-if="step === 'normal_subtype'" class="space-y-4">
				<h2 class="text-sm sm:text-base font-semibold text-gray-800 text-center">{{ __('What kind of item?') }}</h2>
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mt-4">
					<!-- Quick Sell -->
					<button
						@click="selectSubtype('quick_sell')"
						class="group flex flex-col items-center p-6 rounded-2xl border-2 border-gray-200 bg-white hover:border-emerald-400 hover:shadow-lg active:scale-[0.98] transition-all duration-150 touch-manipulation"
					>
						<div class="w-16 h-16 rounded-2xl bg-emerald-50 flex items-center justify-center mb-3 group-hover:bg-emerald-100 transition-colors">
							<svg class="w-8 h-8 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
							</svg>
						</div>
						<span class="text-sm font-semibold text-gray-800">{{ __('Quick Sell') }}</span>
						<span class="text-[10px] sm:text-xs text-gray-500 mt-1 text-center">{{ __('Simple item, no variants') }}</span>
					</button>
					<!-- Has Variants -->
					<button
						@click="selectSubtype('has_variants')"
						class="group flex flex-col items-center p-6 rounded-2xl border-2 border-gray-200 bg-white hover:border-amber-400 hover:shadow-lg active:scale-[0.98] transition-all duration-150 touch-manipulation"
					>
						<div class="w-16 h-16 rounded-2xl bg-amber-50 flex items-center justify-center mb-3 group-hover:bg-amber-100 transition-colors">
							<svg class="w-8 h-8 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/>
							</svg>
						</div>
						<span class="text-sm font-semibold text-gray-800">{{ __('Has Variants') }}</span>
						<span class="text-[10px] sm:text-xs text-gray-500 mt-1 text-center">{{ __('Item with sizes, colors, etc.') }}</span>
					</button>
				</div>
			</div>

			<!-- ============ STEP 3: Item Details Form ============ -->
			<div v-else-if="step === 'details'" class="space-y-4">
				<h2 class="text-sm sm:text-base font-semibold text-gray-800">{{ __('Item Details') }}</h2>
				<div v-if="editingItemCode" class="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-700">
					{{ __('Editing') }}: {{ editingItemCode }}
				</div>

				<!-- Item Code -->
				<div>
					<label class="block text-xs font-medium text-gray-700 mb-1">{{ __('Item Code') }} *</label>
					<input
						v-model="form.item_code"
						:disabled="!!editingItemCode"
						type="text"
						:placeholder="__('e.g. BURGER-001')"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500"
					/>
				</div>

				<!-- Item Name -->
				<div>
					<label class="block text-xs font-medium text-gray-700 mb-1">{{ __('Item Name') }} *</label>
					<input
						v-model="form.item_name"
						type="text"
						:placeholder="__('e.g. Cheese Burger')"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
				</div>

				<div>
					<label class="block text-xs font-medium text-gray-700 mb-1">{{ __('Arabic Name') }}</label>
					<input
						v-model="form.item_name_arabic"
						type="text"
						:placeholder="__('Optional Arabic item name')"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
				</div>

				<!-- Item Group -->
				<div>
					<label class="block text-xs font-medium text-gray-700 mb-1">{{ __('Item Group') }} *</label>
					<select
						v-model="form.item_group"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
					>
						<option value="">{{ __('Select group...') }}</option>
						<option v-for="g in itemGroups" :key="g.name" :value="g.name">{{ g.name }}</option>
					</select>
				</div>

				<div>
					<label class="block text-xs font-medium text-gray-700 mb-1">{{ __('Classification') }}</label>
					<select
						v-model="form.item_classification"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
					>
						<option value="">{{ __('Select classification...') }}</option>
						<option v-for="c in itemClassifications" :key="c.name" :value="c.name">{{ c.name }}</option>
					</select>
				</div>

				<!-- UOM -->
				<div>
					<label class="block text-xs font-medium text-gray-700 mb-1">{{ __('UOM') }} *</label>
					<select
						v-model="form.uom"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
					>
						<option value="">{{ __('Select UOM...') }}</option>
						<option v-for="u in uoms" :key="u.name" :value="u.name">{{ u.name }}</option>
					</select>
				</div>

				<div>
					<label class="block text-xs font-medium text-gray-700 mb-1">{{ __('Standard Rate') }}</label>
					<input
						v-model.number="form.standard_rate"
						type="number"
						min="0"
						step="0.01"
						:placeholder="__('0.00')"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
				</div>

				<div>
					<label class="block text-xs font-medium text-gray-700 mb-1">{{ __('Image') }}</label>
					<input
						v-model="form.image"
						type="text"
						:placeholder="__('/files/item.png')"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
				</div>

				<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
					<label class="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-700">
						<input v-model="form.is_stock_item" type="checkbox" class="rounded border-gray-300" />
						{{ __('Stock Item') }}
					</label>
					<label class="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-700">
						<input v-model="form.custom_fast_sell" type="checkbox" class="rounded border-gray-300" />
						{{ __('Fast Sell') }}
					</label>
				</div>

				<!-- Price Lists -->
				<div class="space-y-2">
					<div class="flex items-center justify-between">
						<label class="block text-xs font-medium text-gray-700">{{ __('Price Lists') }}</label>
						<button
							@click="addPriceRow"
							class="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-600 text-xs font-medium hover:bg-blue-100 transition-colors"
						>
							{{ __('Add') }}
						</button>
					</div>
					<div
						v-for="(price, pi) in form.price_lists"
						:key="pi"
						class="grid grid-cols-[1fr_120px_32px] gap-2 items-center"
					>
						<div>
							<select
								v-model="price.price_list"
								class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
							>
								<option value="">{{ __('Select...') }}</option>
								<option v-for="pl in priceLists" :key="pl.name" :value="pl.name">{{ pl.name }}</option>
							</select>
						</div>
						<div>
							<input
								v-model.number="price.rate"
								type="number"
								min="0"
								step="0.01"
								:placeholder="__('0.00')"
								class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>
						<button
							@click="removePriceRow(pi)"
							:disabled="form.price_lists.length === 1"
							class="p-2 rounded-lg text-red-500 hover:bg-red-50 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
							</svg>
						</button>
					</div>
				</div>

				<!-- Description -->
				<div>
					<label class="block text-xs font-medium text-gray-700 mb-1">{{ __('Description') }}</label>
					<textarea
						v-model="form.description"
						rows="2"
						:placeholder="__('Optional description...')"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
					/>
				</div>
			</div>

			<!-- ============ STEP 4a: Variants Builder ============ -->
			<div v-else-if="step === 'variants'" class="space-y-4">
				<h2 class="text-sm sm:text-base font-semibold text-gray-800">{{ __('Define Variants') }}</h2>
				<p class="text-xs text-gray-500">{{ __('Add attributes (e.g. Size, Color) and their values, then set prices.') }}</p>

				<!-- Attribute Selector -->
				<div v-for="(attr, ai) in variantAttributes" :key="ai" class="bg-white rounded-xl border border-gray-200 p-3 sm:p-4 space-y-3">
					<div class="flex items-center justify-between">
						<select
							v-model="attr.attribute"
							@change="onAttributeChange(ai)"
							class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
						>
							<option value="">{{ __('Select attribute...') }}</option>
							<option v-for="a in availableAttributes" :key="a.name" :value="a.name">{{ a.attribute_name }}</option>
						</select>
						<button
							@click="removeAttribute(ai)"
							class="ms-2 p-1.5 rounded-lg text-red-500 hover:bg-red-50 active:bg-red-100 transition-colors touch-manipulation"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
							</svg>
						</button>
					</div>
					<!-- Attribute Values as Chips -->
					<div v-if="attr.attribute" class="flex flex-wrap gap-1.5">
						<button
							v-for="val in getAttributeValues(attr.attribute)"
							:key="val.attribute_value"
							@click="toggleAttributeValue(ai, val.attribute_value)"
							:class="[
								'px-2.5 py-1 rounded-full text-xs font-medium border transition-all touch-manipulation',
								attr.selectedValues.includes(val.attribute_value)
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:border-blue-300'
							]"
						>
							{{ val.attribute_value }}
						</button>
					</div>
				</div>

				<!-- Add Attribute Button -->
				<button
					@click="addAttribute()"
					class="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-gray-300 rounded-xl text-sm font-medium text-gray-500 hover:text-blue-600 hover:border-blue-300 transition-colors touch-manipulation"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
					</svg>
					{{ __('Add Attribute') }}
				</button>

				<!-- Generated Variants Preview + Price -->
				<div v-if="generatedVariants.length > 0" class="mt-4 space-y-2">
					<h3 class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
						{{ __('Variants ({0})', [generatedVariants.length]) }}
					</h3>
					<div class="space-y-1.5 max-h-60 overflow-y-auto">
						<div
							v-for="(v, vi) in generatedVariants"
							:key="vi"
							class="bg-white rounded-lg border border-gray-200 px-3 py-2 space-y-2"
						>
							<span class="block text-xs font-medium text-gray-800 truncate">{{ v.label }}</span>
							<div v-if="validPriceRows.length" class="grid grid-cols-1 sm:grid-cols-2 gap-2">
								<label
									v-for="price in validPriceRows"
									:key="`${v.label}-${price.price_list}`"
									class="flex items-center gap-2"
								>
									<span class="w-24 text-[10px] text-gray-500 truncate">{{ price.price_list }}</span>
									<input
										:value="getVariantPrice(v, price)"
										@input="setVariantPrice(v, price, $event.target.value)"
										type="number"
										min="0"
										step="0.01"
										:placeholder="__('Rate')"
										class="flex-1 min-w-0 border border-gray-300 rounded-lg px-2 py-1.5 text-xs text-end focus:ring-2 focus:ring-blue-500 focus:border-transparent"
									/>
								</label>
							</div>
							<div v-else class="text-[10px] text-gray-500">{{ __('Add price lists in Item Details first.') }}</div>
						</div>
					</div>
					<!-- Bulk Set Rate -->
					<div v-if="validPriceRows.length" class="flex items-center gap-2 mt-2">
						<input
							v-model.number="bulkRate"
							type="number"
							min="0"
							step="0.01"
							:placeholder="__('Set all rates')"
							class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						/>
						<button
							@click="applyBulkRate"
							class="px-3 py-2 rounded-lg bg-blue-500 text-white text-xs font-medium hover:bg-blue-600 active:bg-blue-700 transition-colors touch-manipulation"
						>
							{{ __('Apply') }}
						</button>
					</div>
				</div>
			</div>

			<!-- ============ STEP 4b: Combo Components ============ -->
			<div v-else-if="step === 'components'" class="space-y-4">
				<h2 class="text-sm sm:text-base font-semibold text-gray-800">{{ __('Bundle Components') }}</h2>
				<p class="text-xs text-gray-500">{{ __('Search and add items that make up this combo.') }}</p>

				<!-- Search -->
				<div class="relative">
					<div class="absolute inset-y-0 start-0 ps-3 flex items-center pointer-events-none">
						<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
						</svg>
					</div>
					<input
						v-model="componentSearch"
						@input="searchComponents"
						type="text"
						:placeholder="__('Search items to add...')"
						class="w-full border border-gray-300 rounded-lg px-3 py-2.5 ps-10 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
				</div>

				<!-- Search Results -->
				<div v-if="componentSearchResults.length > 0" class="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100 max-h-40 overflow-y-auto">
					<button
						v-for="item in componentSearchResults"
						:key="item.item_code"
						@click="addComponent(item)"
						class="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-blue-50 transition-colors touch-manipulation text-start"
					>
						<div class="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden flex-shrink-0">
							<img v-if="item.image" :src="item.image" class="w-full h-full object-cover" />
							<svg v-else class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
							</svg>
						</div>
						<div class="flex-1 min-w-0">
							<p class="text-xs font-medium text-gray-800 truncate">{{ item.item_name }}</p>
							<p class="text-[10px] text-gray-500">{{ item.item_code }}</p>
						</div>
						<svg class="w-4 h-4 text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
						</svg>
					</button>
				</div>

				<!-- Added Components -->
				<div v-if="comboComponents.length > 0" class="space-y-2 mt-3">
					<h3 class="text-xs font-semibold text-gray-600 uppercase tracking-wide">
						{{ __('Components ({0})', [comboComponents.length]) }}
					</h3>
					<div
						v-for="(comp, ci) in comboComponents"
						:key="ci"
						class="flex items-center gap-2 bg-white rounded-lg border border-gray-200 px-3 py-2"
					>
						<div class="flex-1 min-w-0">
							<p class="text-xs font-medium text-gray-800 truncate">{{ comp.item_name }}</p>
							<p class="text-[10px] text-gray-500">{{ comp.item_code }}</p>
						</div>
						<div class="flex items-center gap-1">
							<label class="text-[10px] text-gray-500">{{ __('Qty') }}:</label>
							<input
								v-model.number="comp.qty"
								type="number"
								min="1"
								class="w-14 border border-gray-300 rounded px-2 py-1 text-xs text-center focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>
						<button
							@click="comboComponents.splice(ci, 1)"
							class="p-1 rounded text-red-500 hover:bg-red-50 transition-colors touch-manipulation"
						>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
							</svg>
						</button>
					</div>
				</div>
			</div>

			<!-- ============ STEP 5: Review ============ -->
			<div v-else-if="step === 'review'" class="space-y-4">
				<h2 class="text-sm sm:text-base font-semibold text-gray-800">{{ __('Review & Create') }}</h2>

				<div class="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
					<div v-if="editingItemCode" class="px-4 py-3 flex items-center justify-between">
						<span class="text-xs text-gray-500">{{ __('Mode') }}</span>
						<span class="text-xs font-medium text-blue-700">{{ __('Update existing item') }}</span>
					</div>
					<div class="px-4 py-3 flex items-center justify-between">
						<span class="text-xs text-gray-500">{{ __('Type') }}</span>
						<span class="text-xs font-medium text-gray-800">
							<template v-if="itemType === 'combo'">{{ __('Combo / Bundle') }}</template>
							<template v-else-if="subtype === 'quick_sell'">{{ __('Quick Sell') }}</template>
							<template v-else>{{ __('Template + Variants') }}</template>
						</span>
					</div>
					<div class="px-4 py-3 flex items-center justify-between">
						<span class="text-xs text-gray-500">{{ __('Item Code') }}</span>
						<span class="text-xs font-medium text-gray-800">{{ form.item_code }}</span>
					</div>
					<div class="px-4 py-3 flex items-center justify-between">
						<span class="text-xs text-gray-500">{{ __('Item Name') }}</span>
						<span class="text-xs font-medium text-gray-800">{{ form.item_name }}</span>
					</div>
					<div class="px-4 py-3 flex items-center justify-between">
						<span class="text-xs text-gray-500">{{ __('Group') }}</span>
						<span class="text-xs font-medium text-gray-800">{{ form.item_group }}</span>
					</div>
					<div class="px-4 py-3 flex items-center justify-between">
						<span class="text-xs text-gray-500">{{ __('UOM') }}</span>
						<span class="text-xs font-medium text-gray-800">{{ form.uom }}</span>
					</div>
					<div v-if="form.item_classification" class="px-4 py-3 flex items-center justify-between">
						<span class="text-xs text-gray-500">{{ __('Classification') }}</span>
						<span class="text-xs font-medium text-gray-800">{{ form.item_classification }}</span>
					</div>
					<div v-if="validPriceRows.length" class="px-4 py-3">
						<span class="text-xs text-gray-500">{{ __('Price Lists') }}</span>
						<div class="mt-1 space-y-1">
							<div v-for="price in validPriceRows" :key="price.price_list" class="flex justify-between text-xs">
								<span class="text-gray-700">{{ price.price_list }}</span>
								<span class="font-medium text-gray-800">{{ price.rate }}</span>
							</div>
						</div>
					</div>
					<!-- Variants summary -->
					<div v-if="subtype === 'has_variants' && generatedVariants.length" class="px-4 py-3">
						<span class="text-xs text-gray-500">{{ __('Variants') }}</span>
						<div class="mt-1 space-y-1">
							<div v-for="(v, vi) in generatedVariants" :key="vi" class="flex justify-between text-xs">
								<span class="text-gray-700">{{ v.label }}</span>
								<span class="font-medium text-gray-800">
									{{ formatVariantPrices(v) || '-' }}
								</span>
							</div>
						</div>
					</div>
					<!-- Combo components summary -->
					<div v-if="itemType === 'combo' && comboComponents.length" class="px-4 py-3">
						<span class="text-xs text-gray-500">{{ __('Components') }}</span>
						<div class="mt-1 space-y-1">
							<div v-for="(c, ci) in comboComponents" :key="ci" class="flex justify-between text-xs">
								<span class="text-gray-700">{{ c.item_name }}</span>
								<span class="font-medium text-gray-800">x{{ c.qty }}</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- ============ SUCCESS ============ -->
			<div v-else-if="step === 'success'" class="flex flex-col items-center justify-center py-12 space-y-4">
				<div class="w-20 h-20 rounded-full bg-emerald-100 flex items-center justify-center">
					<svg class="w-10 h-10 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
					</svg>
				</div>
				<h2 class="text-base sm:text-lg font-bold text-gray-900">
					{{ editingItemCode ? __('Item Updated!') : __('Item Created!') }}
				</h2>
				<p class="text-xs sm:text-sm text-gray-500 text-center">
					<span class="font-medium text-gray-800">{{ createdResult?.item_code || createdResult?.template?.item_code }}</span>
					{{ editingItemCode ? __('has been updated successfully.') : __('has been created successfully.') }}
				</p>
				<div class="flex gap-3 mt-4">
					<button
						@click="resetWizard"
						class="px-5 py-2.5 rounded-xl bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 active:bg-blue-700 transition-colors touch-manipulation"
					>
						{{ __('Create Another') }}
					</button>
					<button
						@click="goToList"
						class="px-5 py-2.5 rounded-xl bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200 active:bg-gray-300 transition-colors touch-manipulation"
					>
						{{ __('Back to List') }}
					</button>
				</div>
			</div>

		</main>

		<!-- Footer Actions -->
		<footer v-if="showFooter" class="bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-between sticky bottom-0 z-20">
			<button
				@click="goToPrevStep"
				class="px-4 py-2.5 rounded-xl bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200 active:bg-gray-300 transition-colors touch-manipulation"
			>
				{{ __('Back') }}
			</button>
			<button
				@click="goToNextStep"
				:disabled="!canProceed || submitting"
				:class="[
					'px-6 py-2.5 rounded-xl text-sm font-medium transition-colors touch-manipulation flex items-center gap-2',
					canProceed && !submitting
						? 'bg-blue-500 text-white hover:bg-blue-600 active:bg-blue-700'
						: 'bg-gray-200 text-gray-400 cursor-not-allowed'
				]"
			>
				<div v-if="submitting" class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
				{{ step === 'review' ? (editingItemCode ? __('Save Item') : __('Create Item')) : __('Next') }}
			</button>
		</footer>

		<div v-if="bundleDialog" class="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
			<div class="w-full max-w-2xl rounded-xl bg-white shadow-xl">
				<div class="flex items-center justify-between border-b border-gray-200 px-4 py-3">
					<div>
						<h2 class="text-sm font-semibold text-gray-900">{{ __('Product Bundle') }}</h2>
						<p class="text-xs text-gray-500">{{ bundleDialogTitle }}</p>
					</div>
					<button @click="bundleDialog = false" class="rounded-lg p-2 text-gray-500 hover:bg-gray-100">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
						</svg>
					</button>
				</div>
				<div class="max-h-[60vh] overflow-y-auto p-4">
					<div v-if="viewedBundleItems.length === 0" class="py-8 text-center text-sm text-gray-500">
						{{ __('No bundle items found') }}
					</div>
					<table v-else class="w-full text-xs sm:text-sm">
						<thead class="bg-gray-50 text-gray-500">
							<tr>
								<th class="px-3 py-2 text-start font-semibold">{{ __('Item') }}</th>
								<th class="px-3 py-2 text-center font-semibold">{{ __('Qty') }}</th>
								<th class="px-3 py-2 text-start font-semibold">{{ __('UOM') }}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<tr v-for="row in viewedBundleItems" :key="row.item_code">
								<td class="px-3 py-2">
									<div class="font-medium text-gray-800">{{ row.item_name || row.item_code }}</div>
									<div class="text-[10px] text-gray-500">{{ row.item_code }}</div>
								</td>
								<td class="px-3 py-2 text-center text-gray-700">{{ row.qty }}</td>
								<td class="px-3 py-2 text-gray-700">{{ row.uom || '-' }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { call } from "frappe-ui"
import { computed, onMounted, reactive, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"

const router = useRouter()
const route = useRoute()
const isDeskMode =
	new URLSearchParams(window.location.search).get("desk") === "1"
const queryItemId = new URLSearchParams(window.location.search).get("item_id")

// =========================================================================
// State
// =========================================================================
const step = ref("list") // list | type | normal_subtype | details | variants | components | review | success
const itemType = ref("") // normal | combo
const subtype = ref("") // quick_sell | has_variants
const submitting = ref(false)
const createdResult = ref(null)
const editingItemCode = ref("")
const listLoading = ref(false)
const items = ref([])
const listSearch = ref("")
const filterGroup = ref("")
const filterClassification = ref("")
const listStart = ref(0)
const listPageLength = ref(20)
const listTotal = ref(0)
const bundleDialog = ref(false)
const bundleDialogTitle = ref("")
const viewedBundleItems = ref([])

const form = reactive({
	item_code: "",
	item_name: "",
	item_name_arabic: "",
	item_group: "",
	item_classification: "",
	uom: "Nos",
	standard_rate: null,
	image: "",
	description: "",
	is_stock_item: true,
	custom_fast_sell: false,
	price_lists: [{ price_list: "", rate: null }],
})

// Variants state
const variantAttributes = ref([]) // [{attribute, selectedValues: []}]
const bulkRate = ref(null)

// Combo state
const comboComponents = ref([]) // [{item_code, item_name, qty, image}]
const componentSearch = ref("")
const componentSearchResults = ref([])
let searchTimer = null
let listSearchTimer = null

// Data from server
const itemGroups = ref([])
const uoms = ref([])
const priceLists = ref([])
const itemClassifications = ref([])
const allAttributes = ref([])

// =========================================================================
// Computed
// =========================================================================
const stepLabel = computed(() => {
	const labels = {
		list: __("List View"),
		type: __("Step 1 — Choose Type"),
		normal_subtype: __("Step 2 — Item Kind"),
		details: __("Step 3 — Item Details"),
		variants: __("Step 4 — Variants"),
		components: __("Step 4 — Components"),
		review: __("Final — Review"),
		success: __("Done"),
	}
	return labels[step.value] || ""
})

const totalSteps = computed(() => {
	if (step.value === "list") return 0
	if (itemType.value === "combo") return 4
	if (subtype.value === "has_variants") return 5
	return 4
})

const currentStepIndex = computed(() => {
	const steps = stepSequence.value
	const idx = steps.indexOf(step.value)
	return idx >= 0 ? idx + 1 : 1
})

const stepSequence = computed(() => {
	if (itemType.value === "combo")
		return ["type", "details", "components", "review"]
	if (subtype.value === "has_variants")
		return ["type", "normal_subtype", "details", "variants", "review"]
	if (subtype.value === "quick_sell")
		return ["type", "normal_subtype", "details", "review"]
	return ["type"]
})

const showFooter = computed(() => {
	return !["list", "type", "normal_subtype", "success"].includes(step.value)
})

const canProceed = computed(() => {
	if (step.value === "details") {
		return !!(form.item_code && form.item_name && form.item_group && form.uom)
	}
	if (step.value === "variants") {
		return generatedVariants.value.length > 0
	}
	if (step.value === "components") {
		return comboComponents.value.length > 0
	}
	if (step.value === "review") return true
	return true
})

const validPriceRows = computed(() => {
	const seen = new Set()
	return form.price_lists.filter((row) => {
		if (!row.price_list || row.rate == null || seen.has(row.price_list))
			return false
		seen.add(row.price_list)
		return true
	})
})

const availableAttributes = computed(() => {
	const usedNames = variantAttributes.value
		.map((a) => a.attribute)
		.filter(Boolean)
	return allAttributes.value.filter((a) => !usedNames.includes(a.name))
})

const generatedVariants = computed(() => {
	const attrs = variantAttributes.value.filter(
		(a) => a.attribute && a.selectedValues.length > 0,
	)
	if (attrs.length === 0) return []

	// Cartesian product of selected values
	let combos = [[]]
	for (const attr of attrs) {
		const newCombos = []
		for (const combo of combos) {
			for (const val of attr.selectedValues) {
				newCombos.push([...combo, { attribute: attr.attribute, value: val }])
			}
		}
		combos = newCombos
	}

	return combos.map((combo) => {
		const label = combo.map((c) => c.value).join(" / ")
		const attrs = {}
		for (const c of combo) {
			attrs[c.attribute] = c.value
		}
		// Preserve existing rate if same label exists
		const existing = _prevVariants.get(label)
		return reactive({
			label,
			attributes: attrs,
			prices: existing?.prices ? { ...existing.prices } : {},
		})
	})
})

// Keep a map of previous variant rates so they survive re-computation
const _prevVariants = new Map()
watch(
	generatedVariants,
	(newVal) => {
		_prevVariants.clear()
		for (const v of newVal) {
			_prevVariants.set(v.label, { prices: { ...v.prices } })
		}
	},
	{ deep: true },
)

// =========================================================================
// Actions
// =========================================================================
function startCreate() {
	resetWizard()
	step.value = "type"
}

function goToList() {
	if (route.params.itemId) {
		router.push({ name: "ItemManager" })
		return
	}
	resetWizard()
	step.value = "list"
	loadItems()
}

function selectType(type) {
	itemType.value = type
	if (type === "combo") {
		step.value = "details"
	} else {
		step.value = "normal_subtype"
	}
}

function selectSubtype(sub) {
	subtype.value = sub
	step.value = "details"
}

function goToPrevStep() {
	const seq = stepSequence.value
	const idx = seq.indexOf(step.value)
	if (idx > 0) {
		step.value = seq[idx - 1]
	}
}

function goToNextStep() {
	if (step.value === "review") {
		submitItem()
		return
	}
	const seq = stepSequence.value
	const idx = seq.indexOf(step.value)
	if (idx < seq.length - 1) {
		step.value = seq[idx + 1]
	}
}

function goBack() {
	if (step.value !== "list") {
		goToList()
		return
	}
	if (isDeskMode && window.top !== window.self) {
		window.top.location.href = "/app"
		return
	}
	router.push({ name: "POSSale" })
}

function resetWizard() {
	step.value = "list"
	itemType.value = ""
	subtype.value = ""
	editingItemCode.value = ""
	form.item_code = ""
	form.item_name = ""
	form.item_name_arabic = ""
	form.item_group = ""
	form.item_classification = ""
	form.uom = "Nos"
	form.standard_rate = null
	form.image = ""
	form.description = ""
	form.is_stock_item = true
	form.custom_fast_sell = false
	form.price_lists = [{ price_list: "", rate: null }]
	variantAttributes.value = []
	comboComponents.value = []
	componentSearch.value = ""
	componentSearchResults.value = []
	createdResult.value = null
	bulkRate.value = null
	_prevVariants.clear()
}

function addPriceRow() {
	form.price_lists.push({ price_list: "", rate: null })
}

function removePriceRow(index) {
	if (form.price_lists.length === 1) return
	form.price_lists.splice(index, 1)
}

// Watch for route changes to handle direct item editing via URL
watch(
	() => route.params.itemId,
	(newId) => {
		if (newId) {
			applyInitialItemRoute()
		} else if (step.value !== "list") {
			// If URL becomes empty and we are not in list view, go back to list
			goToList()
		}
	},
)

async function loadItems() {
	listLoading.value = true
	try {
		const result = await call(
			"ecs_posnext.api.item_manager.get_item_manager_items",
			{
				search_term: listSearch.value,
				item_group: filterGroup.value,
				item_classification: filterClassification.value,
				start: listStart.value,
				page_length: listPageLength.value,
			},
		)
		items.value = result?.items || []
		listTotal.value = result?.total || 0
	} catch (e) {
		console.error("Failed to load items:", e)
	} finally {
		listLoading.value = false
	}
}

function refreshList() {
	listStart.value = 0
	loadItems()
}

async function applyInitialItemRoute() {
	const itemId = route.params.itemId || queryItemId
	if (!itemId) {
		await loadItems()
		return
	}

	if (itemId === "new") {
		startCreate()
		return
	}

	await editItem({ item_code: itemId, name: itemId })
}

function searchListItems() {
	if (listSearchTimer) clearTimeout(listSearchTimer)
	listSearchTimer = setTimeout(() => {
		listStart.value = 0
		loadItems()
	}, 300)
}

function prevListPage() {
	listStart.value = Math.max(0, listStart.value - listPageLength.value)
	loadItems()
}

function nextListPage() {
	if (listStart.value + listPageLength.value >= listTotal.value) return
	listStart.value += listPageLength.value
	loadItems()
}

function itemTypeLabel(item) {
	if (item.has_variants) return __("Template")
	if (item.variant_of) return __("Variant")
	if (item.is_stock_item) return __("Stock Item")
	return __("Bundle / Service")
}

// ---- Attribute helpers ----
function addAttribute() {
	variantAttributes.value.push({ attribute: "", selectedValues: [] })
}

function removeAttribute(index) {
	variantAttributes.value.splice(index, 1)
}

function onAttributeChange(index) {
	variantAttributes.value[index].selectedValues = []
}

function getAttributeValues(attrName) {
	const attr = allAttributes.value.find((a) => a.name === attrName)
	return attr?.values || []
}

function toggleAttributeValue(attrIndex, value) {
	const vals = variantAttributes.value[attrIndex].selectedValues
	const idx = vals.indexOf(value)
	if (idx >= 0) {
		vals.splice(idx, 1)
	} else {
		vals.push(value)
	}
}

function applyBulkRate() {
	if (bulkRate.value == null) return
	for (const v of generatedVariants.value) {
		for (const price of validPriceRows.value) {
			v.prices[price.price_list] = bulkRate.value
		}
	}
}

function getVariantPrice(variant, price) {
	return variant.prices[price.price_list] ?? price.rate ?? ""
}

function setVariantPrice(variant, price, value) {
	if (value === "" || value == null) {
		delete variant.prices[price.price_list]
		return
	}
	const parsed = Number(value)
	if (!Number.isNaN(parsed)) {
		variant.prices[price.price_list] = parsed
	}
}

function formatVariantPrices(variant) {
	return validPriceRows.value
		.map((price) => {
			const rate = getVariantPrice(variant, price)
			return rate === "" ? null : `${price.price_list}: ${rate}`
		})
		.filter(Boolean)
		.join(", ")
}

// ---- Component helpers ----
function searchComponents() {
	if (searchTimer) clearTimeout(searchTimer)
	searchTimer = setTimeout(async () => {
		if (!componentSearch.value.trim()) {
			componentSearchResults.value = []
			return
		}
		try {
			const results = await call(
				"ecs_posnext.api.item_manager.search_items_for_bundle",
				{
					search_term: componentSearch.value.trim(),
				},
			)
			componentSearchResults.value = results || []
		} catch (e) {
			console.error("Search error:", e)
		}
	}, 300)
}

function addComponent(item) {
	const exists = comboComponents.value.find(
		(c) => c.item_code === item.item_code,
	)
	if (exists) {
		exists.qty += 1
	} else {
		comboComponents.value.push({
			item_code: item.item_code,
			item_name: item.item_name,
			image: item.image,
			qty: 1,
		})
	}
	componentSearch.value = ""
	componentSearchResults.value = []
}

function buildItemPayload() {
	return {
		item_code: form.item_code,
		item_name: form.item_name,
		item_name_arabic: form.item_name_arabic,
		item_group: form.item_group,
		item_classification: form.item_classification,
		uom: form.uom,
		standard_rate: form.standard_rate || 0,
		image: form.image,
		description: form.description,
		is_stock_item: form.is_stock_item ? 1 : 0,
		custom_fast_sell: form.custom_fast_sell ? 1 : 0,
		enabled_item_bundle: itemType.value === "combo" ? 1 : 0,
		price_lists: validPriceRows.value,
	}
}

function fillFormFromItem(payload, duplicate = false) {
	const item = payload.item || {}
	const bundle = payload.bundle || {}
	editingItemCode.value = duplicate ? "" : item.name || item.item_code
	form.item_code = duplicate
		? `${item.item_code || item.name}-COPY`
		: item.item_code
	form.item_name = duplicate
		? `${item.item_name || item.item_code} (Copy)`
		: item.item_name
	form.item_name_arabic = item.item_name_arabic || ""
	form.item_group = item.item_group || ""
	form.item_classification = item.item_classification || ""
	form.uom = item.stock_uom || "Nos"
	form.standard_rate = item.standard_rate || null
	form.image = item.image || ""
	form.description = item.description || ""
	form.is_stock_item = !!item.is_stock_item
	form.custom_fast_sell = !!item.custom_fast_sell
	form.price_lists = payload.prices?.length
		? payload.prices.map((price) => ({
				price_list: price.price_list,
				rate: price.price_list_rate,
				uom: price.uom,
			}))
		: [{ price_list: "", rate: null }]

	comboComponents.value = (bundle.items || []).map((row) => ({
		item_code: row.item_code,
		item_name: row.item_name,
		qty: row.qty || 1,
		uom: row.uom,
	}))
	itemType.value = bundle.exists ? "combo" : "normal"
	subtype.value = "quick_sell"
	step.value = "details"
}

async function editItem(item) {
	listLoading.value = true
	try {
		const result = await call(
			"ecs_posnext.api.item_manager.get_item_with_details",
			{
				item_code: item.name || item.item_code,
			},
		)
		resetWizard()
		fillFormFromItem(result, false)
	} catch (e) {
		console.error("Failed to load item:", e)
		listSearch.value = item.item_code || item.name || ""
		await loadItems()
	} finally {
		listLoading.value = false
	}
}

async function duplicateItem(item) {
	listLoading.value = true
	try {
		const result = await call(
			"ecs_posnext.api.item_manager.get_item_with_details",
			{
				item_code: item.name || item.item_code,
			},
		)
		resetWizard()
		fillFormFromItem(result, true)
	} catch (e) {
		console.error("Failed to duplicate item:", e)
	} finally {
		listLoading.value = false
	}
}

async function viewBundle(item) {
	bundleDialogTitle.value = item.item_name || item.item_code
	viewedBundleItems.value = []
	bundleDialog.value = true
	try {
		const result = await call(
			"ecs_posnext.api.item_manager.get_product_bundle",
			{
				item_code: item.name || item.item_code,
			},
		)
		viewedBundleItems.value = result?.items || []
	} catch (e) {
		console.error("Failed to load bundle:", e)
	}
}

// ---- Submit ----
async function submitItem() {
	submitting.value = true
	try {
		let result
		const basePayload = buildItemPayload()
		if (editingItemCode.value) {
			result = await call("ecs_posnext.api.item_manager.update_item", {
				item_code: editingItemCode.value,
				item_data: JSON.stringify({
					...basePayload,
					components:
						itemType.value === "combo"
							? comboComponents.value.map((c) => ({
									item_code: c.item_code,
									qty: c.qty,
								}))
							: null,
				}),
			})
		} else if (itemType.value === "combo") {
			result = await call("ecs_posnext.api.item_manager.create_combo_item", {
				item_data: JSON.stringify({
					...basePayload,
					components: comboComponents.value.map((c) => ({
						item_code: c.item_code,
						qty: c.qty,
					})),
				}),
			})
		} else if (subtype.value === "has_variants") {
			result = await call("ecs_posnext.api.item_manager.create_template_item", {
				item_data: JSON.stringify({
					...basePayload,
					attributes: variantAttributes.value
						.filter((a) => a.attribute && a.selectedValues.length)
						.map((a) => ({ attribute: a.attribute, values: a.selectedValues })),
					variants: generatedVariants.value.map((v) => ({
						attributes: v.attributes,
						price_lists: validPriceRows.value.map((price) => ({
							price_list: price.price_list,
							rate: getVariantPrice(v, price),
						})),
					})),
				}),
			})
		} else {
			result = await call("ecs_posnext.api.item_manager.create_simple_item", {
				item_data: JSON.stringify({
					...basePayload,
				}),
			})
		}
		createdResult.value = result
		step.value = "success"
	} catch (error) {
		console.error("Error creating item:", error)
		// frappe-ui shows error toasts automatically
	} finally {
		submitting.value = false
	}
}

// =========================================================================
// Load initial data
// =========================================================================
onMounted(async () => {
	try {
		const [groups, uomList, plists, attrs, classifications] = await Promise.all(
			[
				call("ecs_posnext.api.item_manager.get_item_groups"),
				call("ecs_posnext.api.item_manager.get_uoms"),
				call("ecs_posnext.api.item_manager.get_price_lists"),
				call("ecs_posnext.api.item_manager.get_item_attributes"),
				call("ecs_posnext.api.item_manager.get_item_classifications"),
			],
		)
		itemGroups.value = groups || []
		uoms.value = uomList || []
		priceLists.value = plists || []
		allAttributes.value = attrs || []
		itemClassifications.value = classifications || []
		await applyInitialItemRoute()
	} catch (e) {
		console.error("Failed to load initial data:", e)
	}
})
</script>
