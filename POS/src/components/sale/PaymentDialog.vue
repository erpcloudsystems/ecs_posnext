<template>
	<Dialog v-model="show" :options="{ title: isSalesOrder ? __('Complete Sales Order') : __('Complete Payment'), size: dynamicDialogSize }">
		<template #body-content>
			<div class="relative w-full h-full min-h-0 flex flex-col">
				<!-- Submission Progress Bar -->
				<div v-if="isSubmitting || submissionProgress > 0" class="absolute top-0 left-0 w-full h-1.5 bg-gray-100 z-[100] overflow-hidden">
					<div 
						class="h-full bg-blue-600 transition-all duration-300 ease-out shadow-[0_0_8px_rgba(37,99,235,0.5)]" 
						:style="{ width: `${submissionProgress}%` }"
					></div>
				</div>

				<!-- Submission Overlay -->
				<div v-if="isSubmitting" class="absolute inset-0 bg-white/40 backdrop-blur-[1px] z-[90] flex items-center justify-center transition-all duration-300">
					<div class="bg-white/90 p-4 rounded-2xl shadow-xl border border-gray-100 flex flex-col items-center gap-3 scale-110">
						<div class="relative w-12 h-12">
							<svg class="animate-spin w-full h-full text-blue-600" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
						</div>
						<span class="text-sm font-black text-gray-700 uppercase tracking-widest">{{ __('Processing...') }}</span>
					</div>
				</div>

				<!-- Two Column Layout - auto-sized on mobile, constrained on desktop -->
				<div
					:class="[
						'grid grid-cols-1 lg:grid-cols-5 items-stretch relative',
						dynamicGap,
						isMobileView ? '' : 'overflow-hidden'
					]"
					:style="isMobileView ? {} : { maxHeight: dialogContentMaxHeight }"
				>
				<!-- Left Column (2/5): Invoice Summary -->
				<div
					:class="[
						'lg:col-span-2 flex flex-col min-h-0',
						isSmallMobile ? 'gap-1' : 'gap-1.5',
						isMobileView ? 'overflow-visible' : 'overflow-hidden'
					]"
					:style="{ maxHeight: isMobileView ? 'none' : dynamicLeftColumnHeight }"
				>
					<!-- Order Type Selection -->
					<div v-if="customer" class="bg-white border border-gray-200 rounded-lg p-2.5 flex flex-col gap-2 flex-shrink-0">
						<div class="flex items-center bg-gray-100 rounded-xl p-1 gap-1">
							<!-- === Non-Call Center: Pickup / Dine In === -->
							<template v-if="!isCallCenterInvoice">
								<!-- Pickup -->
								<button
									type="button"
									@click="cartStore.setOrderType('Pickup')"
									class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all duration-200 touch-manipulation"
									:class="cartStore.orderType === 'Pickup'
										? 'bg-white text-blue-600 shadow-sm border border-gray-200/10'
										: 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
									</svg>
									<span>{{ __("Pickup") }}</span>
								</button>
								<!-- Dine In -->
								<button
									type="button"
									@click="handleDineInClick"
									class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all duration-200 touch-manipulation"
									:class="cartStore.orderType === 'Dine In'
										? 'bg-white text-purple-600 shadow-sm border border-gray-200/10'
										: 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
									</svg>
									<span>{{ __("Dine In") }}</span>
								</button>
							</template>
							<!-- === Call Center: Pickup / Delivery / Talabat === -->
							<template v-else>
								<!-- Pickup -->
								<button
									v-if="cartStore.resumedInvoiceName ? cartStore.orderType === 'Pickup' : (currentPriceList !== 'Talabat')"
									type="button"
									:disabled="!!cartStore.resumedInvoiceName"
									@click="cartStore.setOrderType('Pickup')"
									class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all duration-200 touch-manipulation disabled:opacity-85 disabled:cursor-not-allowed"
									:class="cartStore.orderType === 'Pickup'
										? 'bg-white text-blue-600 shadow-sm border border-gray-200/10'
										: 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
									</svg>
									<span>{{ __("Pickup") }}</span>
								</button>
								<!-- Delivery -->
								<button
									v-if="cartStore.resumedInvoiceName ? cartStore.orderType === 'Delivery' : (currentPriceList !== 'Talabat')"
									type="button"
									:disabled="!!cartStore.resumedInvoiceName"
									@click="handleDeliveryClick"
									class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all duration-200 touch-manipulation disabled:opacity-85 disabled:cursor-not-allowed"
									:class="cartStore.orderType === 'Delivery'
										? 'bg-white text-green-600 shadow-sm border border-gray-200/10'
										: 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
									</svg>
									<span>{{ __("Delivery") }}</span>
								</button>
								<!-- Talabat -->
								<button
									v-if="cartStore.resumedInvoiceName ? cartStore.orderType === 'Talabat' : (currentPriceList === 'Talabat')"
									type="button"
									:disabled="!!cartStore.resumedInvoiceName"
									@click="cartStore.setOrderType('Talabat')"
									class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all duration-200 touch-manipulation disabled:opacity-85 disabled:cursor-not-allowed"
									:class="cartStore.orderType === 'Talabat'
										? 'bg-white text-orange-600 shadow-sm border border-gray-200/10'
										: 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
									</svg>
									<span>{{ __("Talabat") }}</span>
								</button>
							</template>
						</div>
 
						<!-- Delivery Address Summary / Trigger -->
						<div v-if="cartStore.orderType === 'Delivery' && customer" class="mt-1">
							<div
								v-if="cartStore.customerAddress"
								@click="!cartStore.resumedInvoiceName && (showAddressSelector = true)"
								class="p-2.5 rounded-xl border border-blue-100 bg-blue-50/50 hover:bg-blue-50 transition-colors group"
								:class="cartStore.resumedInvoiceName ? 'cursor-not-allowed opacity-80' : 'cursor-pointer'"
							>
								<div class="flex items-center gap-2">
									<div class="w-8 h-8 rounded bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
										<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
										</svg>
									</div>
									<div class="flex-1 min-w-0">
										<p class="text-[9px] font-bold text-blue-700 uppercase tracking-tighter mb-0.5">{{ __("Delivery to") }}</p>
										<p class="text-[10px] font-semibold text-gray-900 truncate">{{ cartStore.customerAddress }}</p>
									</div>
								</div>
							</div>
							<button
								v-else
								type="button"
								@click="showAddressSelector = true"
								:disabled="!!cartStore.resumedInvoiceName"
								class="w-full flex items-center justify-center gap-1.5 p-2 rounded-xl border border-dashed border-gray-300 bg-gray-50 text-gray-600 hover:bg-gray-100 hover:border-gray-400 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
							>
								<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
								</svg>
								<span class="text-xs font-bold">{{ __("Select Delivery Address") }}</span>
							</button>
						</div>
 
						<!-- Branch Selector (for Call Center) -->
						<div v-if="isCallCenterInvoice" class="mt-1">
							<div class="flex items-center gap-1 mb-1">
								<svg class="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
								</svg>
								<span class="text-[10px] font-semibold text-gray-700 uppercase tracking-wider">
									{{ __("Target Branch") }}
									<span class="text-red-500 font-bold ml-0.5">*</span>
								</span>
							</div>
							<select
								:value="cartStore.selectedBranch"
								@change="handleBranchChange"
								:disabled="!!cartStore.resumedInvoiceName"
								class="w-full text-xs border-gray-200 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 py-1 transition-colors disabled:opacity-80 disabled:cursor-not-allowed"
								:class="!cartStore.selectedBranch ? 'border-red-200 ring-1 ring-red-50' : ''"
							>
								<option :value="null">{{ __("Select Branch...") }}</option>
								<option v-for="b in branches" :key="b.name" :value="b.name">
									{{ b.name }}
								</option>
							</select>
						</div>
 
						<!-- Territory Selector -->
						<div v-if="cartStore.orderType === 'Delivery'" class="mt-1">
							<div class="flex items-center gap-1 mb-1">
								<svg class="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
								</svg>
								<span class="text-[10px] font-semibold text-gray-700 uppercase tracking-wider">{{ __("Delivery Zone / Territory") }}</span>
							</div>
							<select
								v-model="selectedTerritory"
								@change="handleTerritoryChange"
								:disabled="!!cartStore.resumedInvoiceName"
								class="w-full text-xs border-gray-200 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 py-1 disabled:opacity-80 disabled:cursor-not-allowed"
							>
								<option :value="null">{{ __("Select Territory...") }}</option>
								<option v-for="t in territories" :key="t.name" :value="t.name">
									{{ t.name }}
								</option>
							</select>
						</div>
						
						<!-- Table Selector -->
						<div v-if="cartStore.orderType === 'Dine In'" class="mt-1">
							<div class="flex items-center gap-1 mb-1">
								<svg class="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
								</svg>
								<span class="text-[10px] font-semibold text-gray-700 uppercase tracking-wider">
									{{ __("Table Number") }}
									<span class="text-red-500 font-bold ml-0.5">*</span>
								</span>
							</div>
							<button
								type="button"
								@click="showTableDialog = true"
								:disabled="!!cartStore.resumedInvoiceName"
								class="w-full flex items-center justify-between px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors border"
								:class="cartStore.selectedTable 
									? 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100'
									: 'bg-white border-red-300 text-gray-600 hover:bg-gray-50 ring-1 ring-red-50'"
							>
								<span class="truncate">{{ cartStore.selectedTable || __("Select Table...") }}</span>
								<svg class="w-4 h-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
								</svg>
							</button>
						</div>
					</div>
 
					<AddressSelector
						v-if="customer"
						v-model="showAddressSelector"
						:customer="customer.name || customer"
						:selected-address="cartStore.customerAddress"
						@select="handleAddressSelect"
					/>
					<!-- Delivery Date for Sales Orders -->
					<div v-if="isSalesOrder" class="bg-orange-50 border border-orange-200 rounded-lg p-2">
						<div class="flex items-center gap-2">
							<svg class="w-4 h-4 text-orange-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
							</svg>
							<label class="text-xs font-medium text-orange-700 flex-shrink-0">{{ __("Delivery Date") }}</label>
							<input
								type="date"
								v-model="deliveryDate"
								:min="today"
								class="flex-1 h-8 border border-orange-300 rounded-lg px-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white"
							/>
						</div>
					</div>

					<!-- Outstanding Balance Row (full width, two columns) -->
					<div v-if="customerCreditEnabled && totalAvailableCredit !== 0" :class="[
						'rounded-lg border p-2 flex items-center justify-between',
						totalAvailableCredit < 0
							? 'bg-red-50 border-red-200'
							: 'bg-emerald-50 border-emerald-200'
					]">
						<span :class="[
							'text-xs font-semibold',
							totalAvailableCredit < 0 ? 'text-red-700' : 'text-emerald-700'
						]">
							{{ totalAvailableCredit < 0 ? __('Outstanding Balance') : __('Credit Balance') }}
						</span>
						<!-- Show remaining credit (after used amount is deducted) for positive balance -->
						<span :class="[
							'text-base font-bold',
							totalAvailableCredit < 0 ? 'text-red-600' : 'text-emerald-600'
						]">
							{{ totalAvailableCredit < 0 ? formatCurrency(Math.abs(totalAvailableCredit)) : formatCurrency(remainingAvailableCredit) }}
						</span>
					</div>

					<!-- Invoice Summary -->
					<div class="bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col flex-1 min-h-0">
						<!-- Header -->
						<div :class="['px-3 border-b border-gray-200 bg-gray-50', isCompactMode ? 'py-1.5' : 'py-2']">
							<div class="flex items-center justify-between">
								<h3 :class="['text-gray-900 font-semibold text-start', dynamicTextSize.header]">{{ __('Invoice Summary') }}</h3>
								<span class="text-gray-500 text-xs text-end">{{ items.length === 1 ? __('1 item') : __('{0} items', [items.length]) }}</span>
							</div>
							<div v-if="customer" class="text-gray-600 text-xs mt-0.5 text-start">
								{{ customer?.customer_name || customer?.name || customer }}
							</div>
						</div>

						<!-- Items List (scrollable, takes available space) -->
						<div v-if="items.length > 0" class="flex-1 overflow-y-auto divide-y divide-gray-100 min-h-0">
							<div
								v-for="(item, index) in items"
								:key="index"
								class="px-3 py-2 hover:bg-gray-50"
							>
								<div class="flex items-start justify-between gap-2">
									<div class="flex-1 min-w-0 text-start">
										<div class="font-medium text-sm text-gray-900 truncate">{{ item.item_name || item.item_code }}</div>

										<!-- Exclusions and Notes -->
										<div v-if="item.removed_ingredient_names?.length > 0 || item.notes" class="mt-0.5 space-y-0.5">
											<div v-if="item.removed_ingredient_names?.length > 0" class="flex items-start gap-1">
												<span class="text-[9px] font-bold text-red-600 uppercase flex-shrink-0">{{ __("No:") }}</span>
												<span class="text-[9px] text-gray-500 leading-tight">{{ item.removed_ingredient_names.join(", ") }}</span>
											</div>
											<div v-if="item.notes" class="flex items-start gap-1">
												<span class="text-[9px] font-bold text-blue-600 uppercase flex-shrink-0">{{ __("Note:") }}</span>
												<span class="text-[9px] text-gray-500 leading-tight italic">"{{ item.notes }}"</span>
											</div>
											<!-- Main Item Addons -->
											<div v-if="item.selected_addons?.length > 0" class="mt-0.5 space-y-0.5">
												<div v-for="addon in item.selected_addons" :key="addon.item_code" class="flex items-start gap-1">
													<span class="text-[9px] font-bold text-green-600 uppercase flex-shrink-0">{{ __("Add:") }}</span>
													<span class="text-[9px] text-gray-500 leading-tight">{{ addon.item_name }}</span>
												</div>
											</div>
										</div>

										<!-- Combo Components -->
										<div v-if="item.components?.length > 0" class="mt-1 space-y-0.5 pl-2 border-l-2 border-gray-100">
											<div v-for="comp in item.components" :key="comp.item_code" class="text-[10px]">
												<div class="flex items-center gap-1">
													<span class="font-bold text-gray-700">{{ comp.quantity }}x</span>
													<span class="text-gray-600">{{ comp.item_name }}</span>
												</div>
												<!-- Component customizations -->
												<div v-if="comp.removed_ingredient_names?.length > 0" class="flex items-start gap-1 ml-2">
													<span class="text-[8px] font-bold text-red-400 uppercase flex-shrink-0">{{ __("No:") }}</span>
													<span class="text-[8px] text-gray-400 leading-tight">{{ comp.removed_ingredient_names.join(", ") }}</span>
												</div>
												<div v-if="comp.selected_addons?.length > 0" class="flex items-start gap-1 ml-2">
													<span class="text-[8px] font-bold text-green-500 uppercase flex-shrink-0">{{ __("Add:") }}</span>
													<span class="text-[8px] text-gray-400 leading-tight">{{ comp.selected_addons.map(a => a.item_name).join(", ") }}</span>
												</div>
											</div>
										</div>
										<div class="text-xs text-gray-500 mt-0.5">
											{{ formatCurrency(item.rate || item.price_list_rate) }} × {{ item.qty || item.quantity }}
										</div>
									</div>
									<div class="text-sm font-semibold text-gray-900 text-end">
										{{ formatCurrency(item.amount || ((item.qty || item.quantity) * (item.rate || item.price_list_rate))) }}
									</div>
								</div>
							</div>
						</div>
						<div v-else class="flex-1 px-3 py-4 text-center text-gray-400 text-sm flex items-center justify-center">
							{{ __('No items') }}
						</div>

						<!-- Amounts Breakdown -->
						<div class="border-t border-gray-200 bg-gray-50 px-3 py-2 space-y-1">
							<!-- Additional Discount Row -->
							<div v-if="settingsStore.allowAdditionalDiscount || localAdditionalDiscount > 0" class="pb-1.5 mb-1 border-b border-dashed border-orange-200">
								<!-- Label with calculated amount -->
								<div class="flex items-center justify-between gap-2 mb-1.5">
									<div class="flex items-center gap-1.5 min-w-0">
										<svg class="w-3.5 h-3.5 text-orange-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
										</svg>
										<span class="text-xs font-medium text-orange-700">{{ __('Additional Discount') }}</span>
									</div>
									<span v-if="localAdditionalDiscount > 0" class="text-xs font-bold text-red-600">
										-{{ formatCurrency(calculatedAdditionalDiscount) }}
									</span>
								</div>
								<!-- Percentage Select: 0% to 100% in steps of 10 -->
								<select
									v-model.number="localAdditionalDiscount"
									@change="handleAdditionalDiscountChange"
									:disabled="!!cartStore.resumedInvoiceName"
									class="w-full h-9 px-3 text-sm font-semibold text-orange-700 bg-white border border-orange-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-400 cursor-pointer disabled:bg-gray-50 disabled:text-orange-600/70 disabled:cursor-not-allowed"
								>
									<option v-for="pct in getDiscountOptions(localAdditionalDiscount)" :key="pct" :value="pct">{{ pct }}%</option>
								</select>
							</div>
							<!-- Subtotal -->
							<div class="flex items-center justify-between text-sm">
								<span class="text-gray-600 text-start">{{ __('Subtotal') }}</span>
								<span class="font-medium text-gray-900 text-end">{{ formatCurrency(subtotal) }}</span>
							</div>
							<!-- Tax -->
							<div v-if="taxAmount > 0" class="flex items-center justify-between text-sm">
								<span class="text-gray-600 text-start">{{ __('Tax') }}</span>
								<span class="font-medium text-gray-900 text-end">{{ formatCurrency(taxAmount) }}</span>
							</div>
							<!-- Discount (shows the calculated additional discount amount) -->
							<div v-if="discountAmount > 0" class="flex items-center justify-between text-sm">
								<span class="text-gray-600 text-start">{{ __('Discount') }}</span>
								<span class="font-medium text-red-600 text-end">-{{ formatCurrency(discountAmount) }}</span>
							</div>
							<!-- Delivery Fee -->
							<div v-if="cartStore.orderType === 'Delivery' && cartStore.deliveryCharge && !cartStore.deliveryCharge.is_dummy && (cartStore.deliveryCharge.rate > 0 || cartStore.deliveryCharge.free_delivery)" class="flex items-center justify-between text-sm">
								<span class="text-gray-600 text-start flex items-center gap-1">
									<svg class="w-3.5 h-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
									</svg>
									{{ __('Delivery Fee') }}
								</span>
								<span class="font-medium text-green-600 text-end">{{ (cartStore.deliveryCharge.free_delivery || !cartStore.deliveryCharge.rate) ? __('Free') : ('+' + formatCurrency(cartStore.deliveryCharge.rate)) }}</span>
							</div>
							<!-- Grand Total -->
							<div class="flex items-center justify-between pt-2 mt-1 border-t border-gray-300">
								<span :class="['font-bold text-gray-900 text-start', isCompactMode ? 'text-sm' : 'text-base']">{{ __('Grand Total') }}</span>
								<span :class="['font-bold text-gray-900 text-end', dynamicTextSize.grandTotal]">{{ formatCurrency(grandTotal) }}</span>
							</div>
						</div>

						<!-- Payment Status - Two Equal Halves -->
						<div class="border-t border-gray-200">
							<div class="grid grid-cols-2 divide-x divide-gray-200">
								<!-- Paid (Left Half) -->
								<div :class="['bg-blue-50 text-center', isCompactMode ? 'p-2' : 'p-3']">
									<div class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">{{ __('Paid') }}</div>
									<div :class="['font-bold text-blue-600', dynamicTextSize.amount]">{{ formatCurrency(totalPaid) }}</div>
								</div>
								<!-- Remaining / Change (Right Half) -->
								<div v-if="remainingAmount > 0 && !applyWriteOff" :class="['bg-orange-50 text-center', isCompactMode ? 'p-2' : 'p-3']">
									<div class="text-xs font-medium text-orange-600 uppercase tracking-wide mb-1">{{ __('Remaining') }}</div>
									<div :class="['font-bold text-orange-600', dynamicTextSize.amount]">{{ formatCurrency(remainingAmount) }}</div>
								</div>
								<!-- Write-off Applied -->
								<div v-else-if="applyWriteOff && canWriteOff" :class="['bg-purple-50 text-center', isCompactMode ? 'p-2' : 'p-3']">
									<div class="text-xs font-medium text-purple-600 uppercase tracking-wide mb-1">{{ __('Write Off') }}</div>
									<div :class="['font-bold text-purple-600', dynamicTextSize.amount]">{{ formatCurrency(writeOffAmount) }}</div>
								</div>
								<div v-else-if="changeAmount > 0 && allowsOverpayment" :class="['bg-green-50 text-center', isCompactMode ? 'p-2' : 'p-3']">
									<div class="text-xs font-medium text-green-600 uppercase tracking-wide mb-1">{{ __('Change Due') }}</div>
									<div :class="['font-bold text-green-600', dynamicTextSize.amount]">{{ formatCurrency(changeAmount) }}</div>
								</div>
								<!-- Exact Amount Warning (when overpayment not allowed) -->
								<div v-else-if="changeAmount > 0 && !allowsOverpayment" :class="['bg-red-50 text-center', isCompactMode ? 'p-2' : 'p-3']">
									<div class="text-xs font-medium text-red-600 uppercase tracking-wide mb-1">{{ __('Overpayment') }}</div>
									<div :class="['font-bold text-red-600', dynamicTextSize.amount]">{{ formatCurrency(changeAmount) }}</div>
								</div>
								<div v-else :class="['bg-green-50 flex flex-col items-center justify-center', isCompactMode ? 'p-2' : 'p-3']">
									<svg class="w-5 h-5 text-green-600 mb-1" fill="currentColor" viewBox="0 0 20 20">
										<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
									</svg>
									<span :class="['font-bold text-green-600', dynamicTextSize.body]">{{ __('Fully Paid') }}</span>
								</div>
							</div>
						</div>

						<!-- Write-Off Toggle -->
						<div v-if="canWriteOff" class="border-t border-gray-200 px-4 py-3 bg-white">
							<div class="flex items-center justify-between mb-1.5">
								<span class="text-xs font-medium text-gray-500 uppercase tracking-wider">{{ __('Write Off') }}</span>
								<span class="text-xs text-gray-400">{{ __('Max') }}: {{ formatCurrency(writeOffLimit) }}</span>
							</div>
							<div
								class="relative h-12 rounded-lg overflow-hidden select-none cursor-pointer border"
								:class="applyWriteOff ? 'bg-teal-500 border-teal-500' : 'bg-gray-100 border-gray-200'"
								@click="applyWriteOff = !applyWriteOff"
								style="transition: all 0.25s ease"
							>
								<!-- Center Text -->
								<div class="absolute inset-0 flex items-center justify-center z-10">
									<span
										class="text-base font-semibold tracking-wide"
										:class="applyWriteOff ? 'text-white' : 'text-gray-700'"
									>
										{{ formatCurrency(remainingAmount) }}
									</span>
								</div>

								<!-- Toggle Handle -->
								<div
									class="absolute top-1.5 bottom-1.5 w-11 rounded-md flex items-center justify-center z-20 bg-white border border-gray-200"
									:style="{
										left: applyWriteOff ? 'calc(100% - 3rem)' : '0.375rem',
										transition: 'left 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
										boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
									}"
								>
									<svg v-if="applyWriteOff" class="w-5 h-5 text-teal-500" fill="currentColor" viewBox="0 0 20 20">
										<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
									</svg>
									<svg v-else class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
									</svg>
								</div>
							</div>
						</div>
					</div>
				</div>
				<!-- End Left Column -->

				<!-- Right Column (3/5): Sales Person + Payment Methods + Quick Amounts + Numpad -->
				<div
					ref="rightColumnRef"
					:class="[
						'lg:col-span-3 bg-gray-50 rounded-lg border border-gray-200 flex flex-col',
						isSmallMobile ? 'p-1.5' : 'p-2 lg:p-3'
					]"
					:style="isMobileView ? {} : { minHeight: rightColumnMinHeight }"
				>
					<!-- Sales Person Selection (top of right column) -->
					<div v-if="settingsStore.enableSalesPersons" :class="[
						'rounded-lg p-2 mb-1.5 lg:mb-2',
						!isSalesPersonValid ? 'bg-red-50 border-2 border-red-300' : 'bg-purple-50 border border-purple-200'
					]">
						<!-- Single Mode: Show selected person or dropdown -->
						<template v-if="settingsStore.isSingleSalesPerson">
							<!-- Show selected person as a nice display -->
							<div v-if="selectedSalesPersons.length > 0" class="flex items-center justify-between">
								<div class="flex items-center gap-2">
									<svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
									</svg>
									<span class="text-sm font-medium text-gray-900">{{ selectedSalesPersons[0].sales_person_name || selectedSalesPersons[0].sales_person }}</span>
								</div>
								<button
									@click="clearSalesPersons"
									class="text-purple-500 hover:text-purple-700 p-1 rounded hover:bg-purple-100"
									:title="__('Change sales person')"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>
									</svg>
								</button>
							</div>
							<!-- Show dropdown when no selection -->
							<div v-else ref="salesPersonDropdownRef">
								<label class="text-xs font-medium text-purple-700 flex items-center gap-1 mb-1">
									<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
									</svg>
									{{ __('Sales Person') }}
									<span class="text-red-500">*</span>
								</label>
								<div class="relative">
									<input
										v-model="salesPersonSearch"
										type="text"
										:placeholder="__('Select sales person...')"
										@focus="salesPersonDropdownOpen = true"
										@blur="handleSalesPersonBlur"
										class="w-full px-3 py-2 ps-3 pe-8 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white"
										:class="!isSalesPersonValid ? 'border-red-300' : 'border-purple-300'"
									/>
									<svg
										class="w-4 h-4 text-purple-500 absolute end-2 top-1/2 -translate-y-1/2 pointer-events-none transition-transform"
										:class="{ 'rotate-180': salesPersonDropdownOpen }"
										fill="none" stroke="currentColor" viewBox="0 0 24 24"
									>
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
									</svg>
									<!-- Dropdown -->
									<div
										v-if="salesPersonDropdownOpen && availableSalesPersons.length > 0"
										class="absolute z-50 mt-1 w-full max-h-40 overflow-y-auto border border-purple-200 rounded-lg bg-white shadow-lg"
									>
										<div
											v-for="person in availableSalesPersons"
											:key="person.name"
											@mousedown.prevent="addSalesPerson(person)"
											class="flex items-center justify-between p-2 hover:bg-purple-50 cursor-pointer border-b border-purple-100 last:border-b-0 text-xs"
										>
											<span class="font-medium text-gray-900">{{ person.sales_person_name || person.name }}</span>
											<span v-if="person.commission_rate" class="text-purple-500 text-[10px]">
												{{ person.commission_rate }}% {{ __('comm.') }}
											</span>
										</div>
									</div>
									<!-- No Results -->
									<div
										v-if="salesPersonDropdownOpen && availableSalesPersons.length === 0 && !loadingSalesPersons"
										class="absolute z-50 mt-1 w-full border border-purple-200 rounded-lg bg-white shadow-lg"
									>
										<div class="text-center py-3 text-xs text-gray-500">
											{{ __('No sales persons available') }}
										</div>
									</div>
								</div>
								<!-- Validation message -->
								<div v-if="!isSalesPersonValid" class="mt-1 text-xs text-red-600 flex items-center gap-1">
									<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
										<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
									</svg>
									{{ __('Sales person is required') }}
								</div>
							</div>
						</template>

						<!-- Multiple Mode: Show label, dropdown, and chips -->
						<template v-else>
							<!-- Label with required indicator -->
							<div class="flex items-center justify-between mb-1.5">
								<label class="text-xs font-medium text-purple-700 flex items-center gap-1">
									<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
									</svg>
									{{ __('Sales Persons') }}
									<span class="text-red-500">*</span>
								</label>
								<span v-if="selectedSalesPersons.length > 0" class="text-[10px] text-purple-600">
									{{ __('Total: {0}%', [Math.round(totalSalesAllocation)]) }}
								</span>
							</div>

							<!-- Search Input with dropdown -->
							<div class="relative" ref="salesPersonDropdownRef">
								<input
									v-model="salesPersonSearch"
									type="text"
									:placeholder="selectedSalesPersons.length > 0
										? __('Add another...')
										: __('Select sales person...')"
									@focus="salesPersonDropdownOpen = true"
									@blur="handleSalesPersonBlur"
									class="w-full px-3 py-2 ps-3 pe-8 text-xs border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white"
									:class="!isSalesPersonValid ? 'border-red-300' : 'border-purple-300'"
								/>
								<svg
									class="w-4 h-4 text-purple-500 absolute end-2 top-1/2 -translate-y-1/2 pointer-events-none transition-transform"
									:class="{ 'rotate-180': salesPersonDropdownOpen }"
									fill="none" stroke="currentColor" viewBox="0 0 24 24"
								>
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
								</svg>

								<!-- Dropdown Results -->
								<div
									v-if="salesPersonDropdownOpen && availableSalesPersons.length > 0"
									class="absolute z-50 mt-1 w-full max-h-40 overflow-y-auto border border-purple-200 rounded-lg bg-white shadow-lg"
								>
									<div
										v-for="person in availableSalesPersons"
										:key="person.name"
										@mousedown.prevent="addSalesPerson(person)"
										class="flex items-center justify-between p-2 hover:bg-purple-50 cursor-pointer border-b border-purple-100 last:border-b-0 text-xs"
									>
										<span class="font-medium text-gray-900">{{ person.sales_person_name || person.name }}</span>
										<span v-if="person.commission_rate" class="text-purple-500 text-[10px]">
											{{ person.commission_rate }}% {{ __('comm.') }}
										</span>
									</div>
								</div>

								<!-- No Results -->
								<div
									v-if="salesPersonDropdownOpen && availableSalesPersons.length === 0 && !loadingSalesPersons"
									class="absolute z-50 mt-1 w-full border border-purple-200 rounded-lg bg-white shadow-lg"
								>
									<div class="text-center py-3 text-xs text-gray-500">
										{{ salesPersons.length === 0 ? __('No sales persons available') : __('All sales persons selected') }}
									</div>
								</div>
							</div>

							<!-- Validation messages -->
							<div v-if="!isSalesPersonValid" class="mt-1 text-xs text-red-600 flex items-center gap-1">
								<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
								</svg>
								<span v-if="selectedSalesPersons.length === 0">{{ __('Sales person is required') }}</span>
								<span v-else>{{ __('At least one salesperson must have commission enabled') }}</span>
							</div>

							<!-- Selected Sales Persons (chips with commission checkboxes) -->
							<div v-if="selectedSalesPersons.length > 0" class="mt-2 flex flex-wrap gap-1">
								<div
									v-for="person in selectedSalesPersons"
									:key="person.sales_person"
									class="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 border border-purple-300 rounded text-xs"
									:class="{ 'opacity-50': person.include_in_commission === 0 }"
								>
									<!-- Commission Checkbox -->
									<input
										type="checkbox"
										:checked="person.include_in_commission !== 0"
										@change="toggleCommissionInclusion(person.sales_person)"
										class="w-3.5 h-3.5 rounded border-purple-300 text-purple-600 focus:ring-purple-500 cursor-pointer"
									/>
									<span class="font-medium text-gray-900 truncate max-w-[100px]" :class="{ 'line-through text-gray-500': person.include_in_commission === 0 }">
										{{ person.sales_person_name || person.sales_person }}
									</span>
									<span class="text-purple-600 font-semibold" :class="{ 'text-gray-400': person.include_in_commission === 0 }">
										{{ Math.round(person.allocated_percentage) }}%
									</span>
									<button
										@click="removeSalesPerson(person.sales_person)"
										class="text-purple-500 hover:text-purple-700"
									>
										<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
											<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
										</svg>
									</button>
								</div>
								<!-- Clear all button -->
								<button
									v-if="selectedSalesPersons.length > 1"
									@click="clearSalesPersons"
									class="inline-flex items-center gap-1 px-2 py-1 text-xs text-red-600 hover:text-red-700"
								>
									<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
										<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
									</svg>
									{{ __('Clear all') }}
								</button>
							</div>
						</template>
					</div>

					<!-- Payment Methods -->
					<div :class="isSmallMobile ? 'mb-1' : 'mb-1.5 lg:mb-3'">
						<div :class="['flex items-center justify-between', isSmallMobile ? 'mb-0.5' : 'mb-1 lg:mb-2']">
							<div :class="['text-start font-semibold text-gray-500 uppercase tracking-wide', isSmallMobile ? 'text-[10px]' : 'text-xs']">{{ __('Payment Method') }}</div>
							<!-- Clear All Payments Button -->
							<button
								v-if="paymentEntries.length > 0"
								@click="clearAll"
								:class="['text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors', isSmallMobile ? 'p-1' : 'p-1.5']"
								:title="__('Clear all payments')"
							>
								<svg :class="isSmallMobile ? 'w-4 h-4' : 'w-5 h-5'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
								</svg>
							</button>
						</div>
						<div v-if="loadingPaymentMethods" class="flex items-center gap-2">
							<div :class="['animate-spin rounded-full border-b-2 border-blue-500', isSmallMobile ? 'h-4 w-4' : 'h-5 w-5']"></div>
							<span :class="['text-gray-500', isSmallMobile ? 'text-xs' : 'text-sm']">{{ __('Loading...') }}</span>
						</div>
						<div v-else-if="filteredPaymentMethods.length > 0" :class="['flex flex-wrap', isSmallMobile ? 'gap-1' : 'gap-1.5 lg:gap-2']">
							<button
								v-for="method in filteredPaymentMethods"
								:key="method.mode_of_payment"
								@pointerdown="onPaymentMethodDown(method, $event)"
								@pointerup="onPaymentMethodUp(method)"
								@pointerleave="onPaymentMethodCancel"
								@pointercancel="onPaymentMethodCancel"
								:disabled="isWalletPaymentMethod(method.mode_of_payment) && availableWalletBalance <= 0 && getMethodTotal(method.mode_of_payment) === 0"
								:class="[
									'rounded-lg border-2 transition-all font-medium select-none touch-none',
									isCashPaymentMethod(method)
										? 'flex flex-col items-center justify-center w-[200px] h-[200px] text-center'
										: [
											'inline-flex items-center',
											isSmallMobile ? 'gap-0.5 px-1.5 h-7 text-[10px]' : 'gap-1 lg:gap-2 px-2.5 lg:px-4 h-8 text-xs lg:h-11 lg:text-sm',
										],
									lastSelectedMethod?.mode_of_payment === method.mode_of_payment
										? isWalletPaymentMethod(method.mode_of_payment)
											? 'border-amber-500 bg-amber-50 text-amber-700'
											: 'border-blue-500 bg-blue-50 text-blue-700'
										: isWalletPaymentMethod(method.mode_of_payment)
											? availableWalletBalance > 0
												? 'border-amber-300 bg-amber-50 hover:border-amber-500 hover:bg-amber-100 text-amber-700'
												: 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed opacity-60'
											: 'border-gray-200 bg-white hover:border-blue-400 hover:bg-blue-50 text-gray-700'
								]"
							>
								<span :class="isCashPaymentMethod(method) ? 'text-4xl mb-2' : (isSmallMobile ? 'text-xs' : 'text-sm lg:text-lg')">{{ isWalletPaymentMethod(method.mode_of_payment) ? '🎁' : getPaymentIcon(method.type) }}</span>
								<span :class="isCashPaymentMethod(method) ? 'text-base font-bold' : 'truncate max-w-[80px] lg:max-w-none'">{{ __(method.mode_of_payment) }}</span>
								<!-- Wallet Balance Badge -->
								<span v-if="isWalletPaymentMethod(method.mode_of_payment) && walletInfo.wallet_enabled"
									:class="['font-bold rounded', isSmallMobile ? 'text-[8px] px-1 py-0.5' : 'text-[10px] px-1.5 py-0.5', availableWalletBalance > 0 ? 'text-amber-700 bg-amber-100' : 'text-gray-500 bg-gray-200']">
									{{ formatCurrency(availableWalletBalance) }}
								</span>
								<!-- Payment Amount Badge -->
								<span v-if="getMethodTotal(method.mode_of_payment) > 0"
									:class="['font-bold rounded', isCashPaymentMethod(method) ? 'text-sm px-2 py-1 mt-2' : (isSmallMobile ? 'text-[8px] px-0.5 py-0.5' : 'text-xs px-1 py-0.5'), isWalletPaymentMethod(method.mode_of_payment) ? 'text-amber-600 bg-amber-200' : 'text-blue-600 bg-blue-100']">
									{{ formatCurrency(getMethodTotal(method.mode_of_payment)) }}
								</span>
							</button>
							<!-- Credit Balance as Payment Method -->
							<button
								v-if="customerCreditEnabled && (remainingAvailableCredit > 0 || getMethodTotal('Customer Credit') > 0)"
								@click="applyCustomerCredit"
								:disabled="remainingAmount === 0 || remainingAvailableCredit === 0"
								:class="[
									'inline-flex items-center rounded-lg border-2 transition-all font-medium',
									isSmallMobile ? 'gap-0.5 px-1.5 h-7 text-[10px]' : 'gap-1 lg:gap-2 px-2.5 lg:px-4 h-8 text-xs lg:h-11 lg:text-sm',
									remainingAmount === 0 || remainingAvailableCredit === 0 ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
									getMethodTotal('Customer Credit') > 0
										? 'border-emerald-500 bg-emerald-50 text-emerald-700'
										: 'border-emerald-300 bg-emerald-50 hover:border-emerald-500 hover:bg-emerald-100 text-emerald-700'
								]"
							>
								<span :class="isSmallMobile ? 'text-xs' : 'text-sm lg:text-lg'">💳</span>
								<span class="truncate">{{ __('Credit Balance') }}</span>
								<span v-if="getMethodTotal('Customer Credit') > 0"
									:class="['font-bold text-emerald-600 bg-emerald-100 rounded', isSmallMobile ? 'text-[8px] px-0.5 py-0.5' : 'text-xs px-1 py-0.5']">
									{{ formatCurrency(getMethodTotal('Customer Credit')) }}
								</span>
							</button>
						</div>
						<div v-else :class="['text-gray-500', isSmallMobile ? 'text-xs' : 'text-sm']">{{ __('No payment methods available') }}</div>

						<!-- Exact Amount Mode Info Banner -->
						<div v-if="isExactAmountModeActive && paymentEntries.length > 0 && hasNonCashPayment"
							:class="['mt-2 p-2 rounded-lg border', !isExactAmountValid ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200']">
							<div class="flex items-center gap-2">
								<svg v-if="!isExactAmountValid" class="w-4 h-4 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
								</svg>
								<svg v-else class="w-4 h-4 flex-shrink-0 text-green-500" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
								</svg>
								<span :class="['text-xs font-medium', !isExactAmountValid ? 'text-red-700' : 'text-green-700']">
									{{ !isExactAmountValid ? __('Total must equal invoice amount') : __('Payment amount is correct') }}
								</span>
							</div>
						</div>
					</div>

				<!-- Added Payment Entries List -->
				<div v-if="paymentEntries.length > 0" class="mt-3 space-y-1">
					<div class="flex items-center justify-between">
						<span :class="['font-semibold text-gray-700', isSmallMobile ? 'text-xs' : 'text-sm']">{{ __('Payment Entries') }}</span>
						<button
							v-if="paymentEntries.length > 1"
							@click="clearAll"
							class="text-xs text-red-500 hover:text-red-700 font-medium"
						>
							{{ __('Clear All') }}
						</button>
					</div>
					<div class="rounded-lg border border-gray-200 bg-gray-50 divide-y divide-gray-200">
						<div v-for="(entry, idx) in paymentEntries" :key="idx"
							class="flex items-center justify-between px-3"
							:class="isSmallMobile ? 'py-1.5' : 'py-2'"
						>
							<div class="flex items-center gap-2 min-w-0">
								<span :class="['flex-shrink-0', isSmallMobile ? 'text-xs' : 'text-sm']">
									{{ getPaymentIcon(entry.type) }}
								</span>
								<span :class="['truncate font-medium text-gray-700', isSmallMobile ? 'text-xs' : 'text-sm']">
									{{ __(entry.mode_of_payment) }}
								</span>
							</div>
							<div class="flex items-center gap-2 flex-shrink-0">
								<span :class="['font-semibold text-gray-900', isSmallMobile ? 'text-xs' : 'text-sm']">
									{{ formatCurrency(entry.amount) }}
								</span>
								<button
									@click="removePaymentEntry(idx)"
									class="p-0.5 rounded hover:bg-red-100 text-gray-400 hover:text-red-500 transition-colors"
									:title="__('Remove')"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
									</svg>
								</button>
							</div>
						</div>
					</div>
				</div>

				<!-- Extra Fields Section (Receipt/Talabat) -->
				<div v-if="needsReceipt || isTalabat" class="mt-3 p-3 bg-white rounded-lg border border-gray-200 space-y-3">
					<!-- Receipt Number -->
					<div v-if="needsReceipt" class="space-y-1">
						<label class="text-xs font-semibold text-gray-600 flex items-center gap-1">
							{{ __('Receipt Number') }} <span class="text-red-500">*</span>
						</label>
						<input
							v-model="receiptNumber"
							type="text"
							:placeholder="__('Enter Receipt Number')"
							:disabled="!!cartStore.resumedInvoiceName"
							class="w-full h-9 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed"
						/>
					</div>

					<!-- Talabat Fields -->
					<template v-if="isTalabat">
						<div class="space-y-1">
							<label class="text-xs font-semibold text-gray-600 uppercase tracking-wider">{{ __('Unique Number') }}</label>
							<input
								v-model="uniqueNumber"
								type="text"
								:placeholder="__('Enter Unique Number')"
								:disabled="!!cartStore.resumedInvoiceName"
								class="w-full h-9 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed"
							/>
						</div>
						<div class="space-y-1">
							<label class="text-xs font-semibold text-gray-600 uppercase tracking-wider flex items-center gap-1">
								{{ __('Reference Number') }} <span v-if="isTalabat" class="text-red-500">*</span>
							</label>
							<input
								v-model="referenceNumber"
								type="text"
								:placeholder="__('Enter Reference Number')"
								:disabled="!!cartStore.resumedInvoiceName"
								class="w-full h-9 px-3 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed"
							/>
						</div>
					</template>
				</div>

				<!-- Desktop Payment Input Section (hidden on mobile) -->
				<div class="hidden lg:block mt-3">
					<!-- Custom Amount Row -->
					<div v-if="lastSelectedMethod && remainingAmount > 0" class="space-y-2">
							<div class="flex gap-2">
								<div class="relative flex-1">
									<span class="absolute start-3 top-1/2 -translate-y-1/2 text-sm text-gray-400">{{ currencySymbol }}</span>
									<input
										v-model="desktopCustomAmount"
										type="number"
										inputmode="decimal"
										:placeholder="isExactAmountModeActive && !isCashPaymentMethod(lastSelectedMethod) ? __('Exact amount only') : __('Enter amount')"
										min="0"
										step="0.01"
										:disabled="isExactAmountModeActive && !isCashPaymentMethod(lastSelectedMethod)"
										@keyup.enter="addDesktopCustomPayment"
										class="w-full h-11 ps-8 pe-3 text-sm font-semibold border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white border-gray-200"
									/>
								</div>
								<button
									@click="addDesktopCustomPayment"
									:disabled="(isExactAmountModeActive && !isCashPaymentMethod(lastSelectedMethod)) || !desktopCustomAmount || desktopCustomAmount <= 0"
									class="h-11 px-4 text-sm font-semibold rounded-lg transition-all bg-blue-500 text-white hover:bg-blue-600 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed"
								>
									{{ __('Add') }}
								</button>
								<button
									@click="payFullRemaining"
									class="h-11 px-4 text-sm font-semibold rounded-lg transition-all bg-green-500 text-white hover:bg-green-600"
								>
									{{ formatCurrency(remainingAmount) }}
								</button>
							</div>
							<p class="text-xs text-gray-500">
								{{ __('Selected') }}: <span class="font-medium text-blue-600">{{ __(lastSelectedMethod.mode_of_payment) }}</span>
								· {{ __('Long press a method to pay full remaining') }}
							</p>
						</div>
						<!-- No method selected prompt -->
						<div v-else-if="!lastSelectedMethod && remainingAmount > 0" class="bg-blue-50 rounded-lg p-3 text-center">
							<p class="text-sm text-blue-600">{{ __('Select a payment method above') }}</p>
						</div>
					</div>

					<!-- Expected Payment Type for Call Center Partial/Zero Payments -->
					<div v-if="isCallCenterInvoice && remainingAmount > 0" :class="isSmallMobile ? 'mt-1 mb-1' : 'mt-2 mb-2'">
						<label :class="['block font-semibold text-gray-600 mb-1', isSmallMobile ? 'text-[10px]' : 'text-xs']">{{ __('Expected Payment Type') }} <span class="text-red-500">*</span></label>
						<select
							v-model="customPaymentType"
							:disabled="!!cartStore.resumedInvoiceName"
							:class="[
								'w-full border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white border-gray-200 disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
								isSmallMobile ? 'text-xs p-1.5 h-7' : 'text-sm p-2 h-9'
							]"
						>
							<option :value="null" disabled>{{ __('Select Payment Type') }}</option>
							<option value="Cash on delivery">{{ __('Cash on delivery') }}</option>
							<option value="Credit Card">{{ __('Credit Card') }}</option>
							<option value="Cash Talabat">{{ __('Cash Talabat') }}</option>
							<option value="Credit Card on delivary">{{ __('Credit Card on delivary') }}</option>
							<option value="Cash">{{ __('Cash') }}</option>
						</select>
					</div>

					<!-- Mobile Payment Section - Dynamic & Responsive -->
					<div class="lg:hidden flex flex-col" :class="isSmallMobile ? 'gap-1' : 'gap-1.5'">
						<!-- Mobile Custom Input -->
						<div v-if="lastSelectedMethod && remainingAmount > 0" :class="['space-y-1 flex-shrink-0', isSmallMobile ? 'mb-1' : 'mb-1.5']">
							<!-- Custom Amount Row (disabled for non-cash when exact amount mode is active) -->
							<div :class="['flex', isSmallMobile ? 'gap-0.5' : 'gap-1']">
								<div class="relative flex-1">
									<span :class="[
										'absolute start-2 top-1/2 -translate-y-1/2',
										isSmallMobile ? 'text-[10px]' : 'text-xs',
										isExactAmountModeActive && !isCashPaymentMethod(lastSelectedMethod) ? 'text-gray-300' : 'text-gray-400'
									]">{{ currencySymbol }}</span>
									<input
										v-model="mobileCustomAmount"
										type="number"
										inputmode="decimal"
										:placeholder="isExactAmountModeActive && !isCashPaymentMethod(lastSelectedMethod) ? __('Exact amount only') : __('Custom')"
										min="0"
										step="0.01"
										:disabled="isExactAmountModeActive && !isCashPaymentMethod(lastSelectedMethod)"
										:class="[
											'w-full border rounded focus:outline-none font-semibold',
											isSmallMobile ? 'h-7 ps-5 pe-1.5 text-xs' : 'h-8 ps-6 pe-2 text-sm',
											isExactAmountModeActive && !isCashPaymentMethod(lastSelectedMethod)
												? 'bg-gray-50 border-gray-100 text-gray-300 cursor-not-allowed'
												: 'bg-white border-gray-200 focus:ring-1 focus:ring-blue-500'
										]"
									/>
								</div>
								<button
									@click="addMobileCustomPayment"
									:disabled="(isExactAmountModeActive && !isCashPaymentMethod(lastSelectedMethod)) || !mobileCustomAmount || mobileCustomAmount <= 0"
									:class="[
										'font-semibold rounded transition-all flex-shrink-0',
										isSmallMobile ? 'h-7 px-2 text-[10px]' : 'h-8 px-3 text-xs',
										(isExactAmountModeActive && !isCashPaymentMethod(lastSelectedMethod)) || !mobileCustomAmount || mobileCustomAmount <= 0
											? 'bg-gray-100 text-gray-400'
											: 'bg-blue-500 text-white active:bg-blue-600'
									]"
								>
									{{ __('Add') }}
								</button>
							</div>
						</div>

						<!-- Mobile: Select payment method prompt -->
						<div v-else-if="!lastSelectedMethod && remainingAmount > 0"
							:class="['bg-blue-50 rounded text-center', isSmallMobile ? 'p-1.5 mb-1' : 'p-2 mb-1.5']">
							<p :class="isSmallMobile ? 'text-[10px]' : 'text-xs'" class="text-blue-600">{{ __('Select a payment method') }}</p>
						</div>

						<!-- Mobile Action Buttons - Always visible at bottom -->
						<div :class="['flex-shrink-0', isSmallMobile ? 'space-y-1' : 'space-y-1.5']">
							<!-- Pay Full / Pay Remaining button -->
							<button
								v-if="lastSelectedMethod && remainingAmount > 0"
								@click="addCustomPayment(lastSelectedMethod, remainingAmount)"
								:disabled="isSubmitting"
								:class="[
									'w-full font-bold rounded-lg flex items-center justify-center',
									isSubmitting
										? 'bg-green-300 text-white cursor-not-allowed'
										: 'bg-green-500 text-white active:bg-green-600',
									mobileButtonSize.height, mobileButtonSize.text, mobileButtonSize.gap
								]"
							>
								<svg :class="mobileButtonSize.icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"/>
								</svg>
								<span>{{ __('Pay') }} {{ formatCurrency(remainingAmount) }}</span>
							</button>

							<!-- Complete Payment Button (visible when any payment has been added OR method selected) -->
							<button
								v-if="totalPaid > 0 || (lastSelectedMethod && remainingAmount > 0) || roundCurrency(props.grandTotal) <= 0"
								@click="completePayment"
								:disabled="isSubmitting || !canComplete"
								:class="[
									'w-full font-bold rounded-lg flex items-center justify-center',
									isSubmitting || !canComplete
										? 'bg-blue-300 text-white cursor-not-allowed'
										: 'bg-blue-500 text-white active:bg-blue-600',
									mobileButtonSize.height, mobileButtonSize.text, mobileButtonSize.gap
								]"
							>
								<svg v-if="isSubmitting" :class="mobileButtonSize.icon" class="animate-spin" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
								</svg>
								<svg v-else :class="mobileButtonSize.icon" fill="currentColor" viewBox="0 0 20 20">
									<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
								</svg>
								<span>{{ isSubmitting ? __('Processing...') : paymentButtonText }}</span>
							</button>
							<!-- Mobile Pay on Account (allow fully unpaid or partial) -->
							<button
								v-if="allowCreditSale && remainingAmount > 0"
								@click="addCreditAccountPayment"
								:disabled="isSubmitting"
								:class="[
									'w-full font-semibold rounded-lg flex items-center justify-center',
									isSubmitting
										? 'bg-orange-300 text-white cursor-not-allowed'
										: 'bg-orange-500 text-white active:bg-orange-600',
									mobileButtonSize.height, mobileButtonSize.text, mobileButtonSize.gap
								]"
							>
								<svg :class="mobileButtonSize.icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
								</svg>
								<span>{{ totalPaid > 0 ? __('Remaining on Account') : __('Full Amount on Account') }} ({{ formatCurrency(remainingAmount) }})</span>
							</button>
						</div>
					</div>
					<!-- End Mobile Payment Section -->

					<!-- Action Buttons (Desktop only) -->
					<div :class="['hidden lg:flex items-center gap-2', isCompactMode ? 'mt-2' : 'mt-4']">
						<!-- Pay on Account Button (if credit sales enabled, allows fully unpaid) -->
						<button
						v-if="allowCreditSale && remainingAmount > 0"
						@click="addCreditAccountPayment"
						:disabled="isSubmitting"
						:class="[
							'flex-1 inline-flex items-center justify-center gap-2 transition-colors focus:outline-none',
							dynamicButtonHeight, 'text-sm font-semibold px-4 rounded-lg',
							isSubmitting
								? 'bg-orange-300 text-white cursor-not-allowed'
								: 'bg-orange-500 text-white hover:bg-orange-600 active:bg-orange-700 focus-visible:ring-2 focus-visible:ring-orange-400'
						]"
						>
							<svg v-if="isSubmitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							<svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
							</svg>
							<span>{{ isSubmitting ? __('Processing...') : (totalPaid > 0 ? __('Pay on Account') : __('Full Amount on Account')) }}</span>
						</button>

						<!-- Complete/Partial Payment Button -->
						<button
							@click="completePayment"
							:disabled="!canComplete || isSubmitting"
							:class="[
								'flex-1 inline-flex items-center justify-center gap-2 transition-colors focus:outline-none',
								dynamicButtonHeight, 'text-sm font-semibold px-5 rounded-lg',
								!canComplete || isSubmitting
									? 'bg-blue-300 text-white cursor-not-allowed'
									: 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 focus-visible:ring-2 focus-visible:ring-blue-400'
							]"
						>
							<svg v-if="isSubmitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							<svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
								<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
							</svg>
							<span>{{ isSubmitting ? __('Processing...') : paymentButtonText }}</span>
						</button>
					</div>
				</div>
				<!-- End Right Column -->
			</div>
			<!-- End Two Column Layout -->
			</div>
		</template>
	</Dialog>

	<TableSelectionDialog 
		v-model="showTableDialog"
		:currency="currency"
		@select-table="onTableSelect"
		@reopen-invoice="onReopenInvoice"
	/>
</template>

<script setup>
import { usePOSSettingsStore } from "@/stores/posSettings"
import { usePOSCartStore } from "@/stores/posCart"
import { usePOSShiftStore } from "@/stores/posShift"
import { useItemSearchStore } from "@/stores/itemSearch"
import AddressSelector from "./AddressSelector.vue"
import TableSelectionDialog from "./TableSelectionDialog.vue"
import {
	DEFAULT_CURRENCY,
	formatCurrency as formatCurrencyUtil,
	getCurrencySymbol,
	roundCurrency,
} from "@/utils/currency"
import { getPaymentIcon } from "@/utils/payment"
import { offlineWorker } from "@/utils/offline/workerClient"
import { logger } from "@/utils/logger"
import { Dialog, createResource, call } from "frappe-ui"
import { computed, ref, watch, nextTick, onMounted } from "vue"
import { useToast } from "@/composables/useToast"
import { useLongPress } from "@/composables/useLongPress"
import { usePaymentNumpad } from "@/composables/usePaymentNumpad"
import { useResponsivePayment } from "@/composables/useResponsivePayment"

const log = logger.create("PaymentDialog")
const settingsStore = usePOSSettingsStore()
const cartStore = usePOSCartStore()
const shiftStore = usePOSShiftStore()
const itemSearchStore = useItemSearchStore()
const { showWarning, showInfo } = useToast()

const props = defineProps({
	modelValue: Boolean,
	grandTotal: {
		type: Number,
		default: 0,
	},
	subtotal: {
		type: Number,
		default: 0,
	},
	discountEligibleSubtotal: {
		type: Number,
		default: 0,
	},
	posProfile: String,
	currency: {
		type: String,
		default: DEFAULT_CURRENCY,
	},
	isOffline: {
		type: Boolean,
		default: false,
	},
	allowPartialPayment: {
		type: Boolean,
		default: false,
	},
	allowCreditSale: {
		type: Boolean,
		default: false,
	},
	allowCustomerCreditPayment: {
		type: Boolean,
		default: false,
	},
	customer: {
		type: [String, Object],
		default: null,
	},
	items: {
		type: Array,
		default: () => [],
	},
	taxAmount: {
		type: Number,
		default: 0,
	},
	discountAmount: {
		type: Number,
		default: 0,
	},
	company: {
		type: String,
		default: "",
	},
	additionalDiscount: {
		type: Number,
		default: 0,
	},
	targetDoctype: {
		type: String,
		default: "Sales Invoice",
	},
	isSubmitting: {
		type: Boolean,
		default: false,
	},
	writeOffLimit: {
		type: Number,
		default: 0,
	},
	allowWriteOff: {
		type: Boolean,
		default: false,
	},
})

const emit = defineEmits([
	"update:modelValue",
	"payment-completed",
	"update-additional-discount",
	"reopen-invoice",
])

const territories = ref([])
const allTerritories = ref([])
const branches = ref([])
const tables = ref([])
const selectedTerritory = ref(null)
const showAddressSelector = ref(false)
const showTableDialog = ref(false)

const currentPriceList = computed(() => {
	return (
		itemSearchStore.selectedPriceList ||
		cartStore.selectedBranchPriceList ||
		shiftStore.currentProfile?.selling_price_list
	)
})

const activePosProfile = computed(() => {
	return cartStore.resumedInvoicePosProfile || props.posProfile
})

const isCallCenterInvoice = computed(() => {
	return activePosProfile.value?.trim() === "Call Center"
})

const loadCallCenterData = async () => {
	if (isCallCenterInvoice.value) {
		try {
			const branchRes = await call("ecs_posnext.api.customers.get_branches")
			branches.value = branchRes || []

			// Fetch all territories for mapping in Call Center mode
			const allRes = await call("ecs_posnext.api.customers.get_territories")
			allTerritories.value = allRes || []
		} catch (err) {
			console.error("Error fetching Call Center data in PaymentDialog:", err)
		}
	}
}

async function updateBranchAndData(branchName) {
	if (!branchName) {
		cartStore.setBranch(null, null, null, null)
		return
	}

	const branch = branches.value.find((b) => b.name === branchName)

	if (branch) {
		cartStore.setBranch(
			branchName,
			branch.warehouse,
			branch.pos_profile,
			branch.selling_price_list,
		)

		// Refresh items list to reflect new warehouse stock and price list
		await itemSearchStore.loadAllItems(activePosProfile.value, true)

		// Refresh territories for the new branch
		try {
			const res = await call("ecs_posnext.api.customers.get_territories", {
				branch: branchName || shiftStore.profileBranch,
			})
			territories.value = res || []
			
			// Refresh tables for the new branch
			tablesResource.reload()

			// Validate current territory selection against the new branch's territories
			if (selectedTerritory.value) {
				const stillValid = territories.value.find(
					(t) => t.name === selectedTerritory.value,
				)
				if (!stillValid) {
					selectedTerritory.value = null
					cartStore.setDeliveryCharge(null)
				} else {
					// Refresh the delivery charge rate using the new branch's POS Profile
					await cartStore.setDeliveryCharge(selectedTerritory.value)
				}
			}
		} catch (err) {
			console.error(
				"Error fetching territories for branch in PaymentDialog:",
				err,
			)
		}
	} else {
		console.warn(
			`Branch ${branchName} not found in available branches list in PaymentDialog.`,
		)
	}
}

async function handleBranchChange(e) {
	await updateBranchAndData(e.target.value)
}

function handleTerritoryChange() {
	if (selectedTerritory.value) {
		cartStore.setDeliveryCharge(selectedTerritory.value)
	} else {
		cartStore.setDeliveryCharge(null)
	}
}

function handleDineInClick() {
	cartStore.setOrderType('Dine In')
	showTableDialog.value = true
}

function onTableSelect(tableName) {
	cartStore.selectedTable = tableName
}

function onReopenInvoice(invoice) {
	showTableDialog.value = false
	emit('update:modelValue', false) // Close payment dialog
	cartStore.resumeInvoice(invoice)
}

async function handleAddressSelect(addr) {
	await cartStore.setCustomerAddress(addr.name, addr.territory)

	// Update local territory dropdown
	if (addr.territory) {
		selectedTerritory.value = addr.territory
	}

	// For Call Center, automatically set the branch if the address or its territory is linked to one
	if (isCallCenterInvoice.value) {
		let branchName = addr.branch

		if (!branchName && addr.territory) {
			const territory =
				allTerritories.value.find((t) => t.name === addr.territory) ||
				territories.value.find((t) => t.name === addr.territory)
			branchName = territory?.branch
		}

		if (branchName && branchName !== cartStore.selectedBranch) {
			await updateBranchAndData(branchName)

			// Re-set selectedTerritory after territories list is updated for the new branch
			if (addr.territory) {
				selectedTerritory.value = addr.territory
			}
		}
	}
}

function handleDeliveryClick() {
	cartStore.setOrderType("Delivery")
	if (!cartStore.customerAddress && props.customer) {
		showAddressSelector.value = true
	}
}

watch(isCallCenterInvoice, loadCallCenterData, { immediate: true })

onMounted(async () => {
	try {
		await loadCallCenterData()

		const res = await call("ecs_posnext.api.customers.get_territories", {
			branch: cartStore.selectedBranch || shiftStore.profileBranch,
		})
		territories.value = res || []
	} catch (err) {
		console.error("Error fetching data in PaymentDialog onMounted:", err)
	}
})

watch(
	() => cartStore.deliveryCharge,
	(newVal) => {
		if (newVal?.territory) {
			selectedTerritory.value = newVal.territory
		} else if (!newVal) {
			selectedTerritory.value = null
		}
	},
	{ immediate: true },
)

watch(
	currentPriceList,
	(newList) => {
		if (cartStore.resumedInvoiceName) return
		if (newList === "Talabat") {
			cartStore.setOrderType("Talabat")
		} else if (cartStore.orderType === "Talabat") {
			cartStore.setOrderType("Pickup")
		}
	},
	{ immediate: true },
)

const show = computed({
	get: () => props.modelValue,
	set: (val) => emit("update:modelValue", val),
})

const paymentMethods = ref([])
const loadingPaymentMethods = ref(false)
const lastSelectedMethod = ref(null)
const customAmount = ref("")
const desktopCustomAmount = ref("")
const paymentEntries = ref([])
const receiptNumber = ref("")
const uniqueNumber = ref("")
const referenceNumber = ref("")
const customerCredit = ref([])
const customerBalance = ref({
	total_outstanding: 0,
	total_credit: 0,
	net_balance: 0,
})
const loadingCredit = ref(false)

const needsReceipt = computed(() => {
	return paymentEntries.value.some((e) => {
		const method = paymentMethods.value.find(
			(m) => m.mode_of_payment === e.mode_of_payment,
		)
		return method?.custom_required_receipt
	})
})

const isTalabat = computed(() => cartStore.orderType === "Talabat")

// Submission progress state
const submissionProgress = ref(0)
let progressInterval = null

watch(
	() => props.isSubmitting,
	(submitting) => {
		if (submitting) {
			submissionProgress.value = 0
			if (progressInterval) clearInterval(progressInterval)
			progressInterval = setInterval(() => {
				if (submissionProgress.value < 92) {
					// Fast at first, then slow down
					const increment =
						submissionProgress.value < 50
							? Math.random() * 15
							: Math.random() * 5
					submissionProgress.value += increment
				}
			}, 400)
		} else {
			if (progressInterval) {
				clearInterval(progressInterval)
				progressInterval = null
			}
			if (submissionProgress.value > 0) {
				submissionProgress.value = 100
				setTimeout(() => {
					submissionProgress.value = 0
				}, 1000)
			}
		}
	},
)

// Wallet state
const walletInfo = ref({
	wallet_enabled: false,
	wallet_exists: false,
	wallet_balance: 0,
	wallet_name: null,
})
const loadingWallet = ref(false)
const walletPaymentMethods = ref(new Set()) // Set of mode_of_payment names that are wallet payments

// Delivery date for Sales Orders
const deliveryDate = ref("")
const today = new Date().toISOString().split("T")[0]
const isSalesOrder = computed(() => props.targetDoctype === "Sales Order")

// Column refs for height matching
const rightColumnRef = ref(null)
const rightColumnMinHeight = ref("auto")

// Use responsive payment composable for viewport tracking and dynamic sizing
const {
	dynamicDialogSize,
	isMobileView,
	dialogContentMaxHeight,
	dynamicLeftColumnHeight,
	isCompactMode,
	isSmallMobile,
	dynamicGap,
	dynamicTextSize,
	dynamicButtonHeight,
	mobileButtonSize,
	dynamicNumpadSize,
} = useResponsivePayment()

// Calculate and sync column heights when dialog opens
function syncColumnHeights() {
	nextTick(() => {
		if (rightColumnRef.value) {
			const rightHeight = rightColumnRef.value.offsetHeight
			// Preserve initial height to prevent shrinking when Quick Amounts is hidden
			rightColumnMinHeight.value = `${rightHeight}px`
		}
	})
}

// Watch for dialog open to sync heights
watch(
	() => props.modelValue,
	(isOpen) => {
		if (isOpen) {
			// Reset min height when dialog opens so we can measure fresh
			rightColumnMinHeight.value = "auto"
			// Small delay to ensure DOM is rendered
			setTimeout(syncColumnHeights, 100)
		}
	},
)

// Handle Enter key from numpad keyboard input
function handleNumpadEnter(value) {
	if (value > 0 && lastSelectedMethod.value) {
		numpadAddPayment()
	} else if (
		remainingAmount.value === 0 &&
		totalPaid.value > 0 &&
		canComplete.value
	) {
		// If fully paid and can complete, trigger complete payment
		completePayment()
	}
}

// Use numpad composable for keypad input handling with keyboard support
const {
	numpadDisplay,
	numpadValue,
	numpadInput,
	numpadBackspace,
	numpadClear,
	setNumpadValue,
} = usePaymentNumpad({
	isEnabled: computed(() => props.modelValue), // Only enabled when dialog is open
	onEnter: handleNumpadEnter,
})

// Mobile custom amount state
const mobileCustomAmount = ref("")

function addMobileCustomPayment() {
	const amount = Number.parseFloat(mobileCustomAmount.value)
	if (amount > 0 && lastSelectedMethod.value) {
		addCustomPayment(lastSelectedMethod.value, amount)
		mobileCustomAmount.value = ""
	}
}

// Desktop custom amount payment
function addDesktopCustomPayment() {
	const amount = Number.parseFloat(desktopCustomAmount.value)
	if (amount > 0 && lastSelectedMethod.value) {
		addCustomPayment(lastSelectedMethod.value, amount)
		desktopCustomAmount.value = ""
	}
}

// Desktop: pay full remaining with selected method
function payFullRemaining() {
	if (remainingAmount.value > 0 && lastSelectedMethod.value) {
		addCustomPayment(lastSelectedMethod.value, remainingAmount.value)
		desktopCustomAmount.value = ""
	}
}

function numpadAddPayment() {
	if (numpadValue.value > 0 && lastSelectedMethod.value) {
		addCustomPayment(lastSelectedMethod.value, numpadValue.value)
		numpadClear()
	}
}

// Additional discount state
const localAdditionalDiscount = ref(0)
const additionalDiscountType = "percentage"

const paymentMethodsResource = createResource({
	url: "ecs_posnext.api.pos_profile.get_payment_methods",
	makeParams() {
		return {
			pos_profile: activePosProfile.value,
		}
	},
	auto: false,
	onSuccess(data) {
		paymentMethods.value = data?.message || data || []
		// Don't auto-select — let user choose payment method
		lastSelectedMethod.value = null
		// Identify wallet payment methods
		identifyWalletPaymentMethods()
	},
})

const customerCreditResource = createResource({
	url: "ecs_posnext.api.credit_sales.get_available_credit",
	makeParams() {
		const customerName = props.customer?.name || props.customer
		log.debug("[PaymentDialog] Fetching credit for customer:", customerName)
		return {
			customer: customerName,
			company: props.company,
			pos_profile: activePosProfile.value,
		}
	},
	auto: false,
	onSuccess(data) {
		log.debug("[PaymentDialog] Customer credit loaded:", data)
		customerCredit.value = data || []
		// Note: loadingCredit is managed by customerBalanceResource since it provides the net_balance for UI
		log.debug(
			"[PaymentDialog] Total available credit:",
			totalAvailableCredit.value,
		)
	},
	onError(error) {
		log.error("[PaymentDialog] Error loading customer credit:", error)
		customerCredit.value = []
		// Note: loadingCredit is managed by customerBalanceResource since it provides the net_balance for UI
	},
})

const customerBalanceResource = createResource({
	url: "ecs_posnext.api.credit_sales.get_customer_balance",
	makeParams() {
		const customerName = props.customer?.name || props.customer
		log.debug("[PaymentDialog] Fetching balance for customer:", customerName)
		return {
			customer: customerName,
			company: props.company,
		}
	},
	auto: false,
	onSuccess(data) {
		log.debug("[PaymentDialog] Customer balance loaded:", data)
		customerBalance.value = data || {
			total_outstanding: 0,
			total_credit: 0,
			net_balance: 0,
		}
		log.debug("[PaymentDialog] Net balance:", customerBalance.value.net_balance)
		loadingCredit.value = false
	},
	onError(error) {
		log.error("[PaymentDialog] Error loading customer balance:", error)
		customerBalance.value = {
			total_outstanding: 0,
			total_credit: 0,
			net_balance: 0,
		}
		loadingCredit.value = false
	},
})

const tablesResource = createResource({
	url: "frappe.client.get_list",
	makeParams() {
		return {
			doctype: "Table Number",
			filters: {
				branch: cartStore.selectedBranch || shiftStore.profileBranch || ""
			},
			fields: '["name"]',
			limit: 1000
		}
	},
	auto: false,
	onSuccess(data) {
		tables.value = data || []
	},
	onError(error) {
		console.error("Error loading tables:", error)
		tables.value = []
	}
})

// Wallet resource
const walletInfoResource = createResource({
	url: "ecs_posnext.api.wallet.get_wallet_info",
	makeParams() {
		const customerName = props.customer?.name || props.customer
		log.debug(
			"[PaymentDialog] Fetching wallet info for customer:",
			customerName,
		)
		return {
			customer: customerName,
			company: props.company,
			pos_profile: activePosProfile.value,
		}
	},
	auto: false,
	onSuccess(data) {
		log.debug("[PaymentDialog] Wallet info loaded:", data)
		walletInfo.value = data || {
			wallet_enabled: false,
			wallet_exists: false,
			wallet_balance: 0,
			wallet_name: null,
		}
		loadingWallet.value = false
	},
	onError(error) {
		log.error("[PaymentDialog] Error loading wallet info:", error)
		walletInfo.value = {
			wallet_enabled: false,
			wallet_exists: false,
			wallet_balance: 0,
			wallet_name: null,
		}
		loadingWallet.value = false
	},
})

// Identify which payment methods are wallet payments (batch query)
async function identifyWalletPaymentMethods() {
	walletPaymentMethods.value = new Set()

	if (paymentMethods.value.length === 0) return

	try {
		// Single batch API call instead of N individual calls
		const methodNames = paymentMethods.value.map((m) => m.mode_of_payment)
		const result = await call(
			"ecs_posnext.api.pos_profile.get_wallet_payment_flags",
			{
				methods: methodNames,
			},
		)

		if (result) {
			for (const [methodName, isWallet] of Object.entries(result)) {
				if (isWallet) {
					walletPaymentMethods.value.add(methodName)
					log.debug(
						"[PaymentDialog] Wallet payment method identified:",
						methodName,
					)
				}
			}
		}
	} catch (error) {
		log.error("[PaymentDialog] Error checking wallet payment methods:", error)
	}
}

// Check if a payment method is a wallet payment
function isWalletPaymentMethod(methodName) {
	return walletPaymentMethods.value.has(methodName)
}

// Check if a payment method is a cash payment (allows overpayment/change)
function isCashPaymentMethod(method) {
	if (!method) return false
	// Check by account_type first (most reliable - from linked Account)
	const accountType = (method.account_type || "").toLowerCase()
	if (accountType === "cash") return true
	// Fallback to Mode of Payment type
	const type = (method.type || "").toLowerCase()
	if (type === "cash") return true
	// Check by mode_of_payment name as fallback
	// const name = (method.mode_of_payment || "").toLowerCase()
	// return name.includes("cash") || name.includes("نقد") || name.includes("نقدي")
}

// Get available wallet balance for payment (considering already added wallet payments)
const availableWalletBalance = computed(() => {
	const totalWalletPayments = paymentEntries.value
		.filter((p) => isWalletPaymentMethod(p.mode_of_payment))
		.reduce((sum, p) => sum + (p.amount || 0), 0)
	return Math.max(0, walletInfo.value.wallet_balance - totalWalletPayments)
})

// Filter payment methods - hide wallet methods when loyalty is not enabled, and filter by invoice payments if resumed
const filteredPaymentMethods = computed(() => {
	let list = paymentMethods.value

	if (cartStore.resumedInvoiceName && cartStore.payments && cartStore.payments.length > 0) {
		const allowedMethods = cartStore.payments.map((p) => p.mode_of_payment)
		list = list.filter((method) => allowedMethods.includes(method.mode_of_payment))
	}

	return list.filter((method) => {
		// If it's a wallet payment method, only show when loyalty/wallet is enabled
		if (isWalletPaymentMethod(method.mode_of_payment)) {
			return walletInfo.value.wallet_enabled
		}
		return true
	})
})

// Sales Persons state
const salesPersons = ref([])
const selectedSalesPersons = ref([])
const salesPersonSearch = ref("")
const loadingSalesPersons = ref(false)
const salesPersonDropdownOpen = ref(false)
const salesPersonDropdownRef = ref(null)

const salesPersonsResource = createResource({
	url: "ecs_posnext.api.pos_profile.get_sales_persons",
	makeParams() {
		return {
			pos_profile: activePosProfile.value,
		}
	},
	auto: false,
	onSuccess(data) {
		log.debug("[PaymentDialog] Sales persons loaded:", data)
		salesPersons.value = data?.message || data || []
		loadingSalesPersons.value = false
	},
	onError(error) {
		log.error("[PaymentDialog] Error loading sales persons:", error)
		salesPersons.value = []
		loadingSalesPersons.value = false
	},
})

// Computed: Available sales persons (exclude already selected, filter by search)
const availableSalesPersons = computed(() => {
	const selectedIds = selectedSalesPersons.value.map((p) => p.sales_person)
	const searchLower = (salesPersonSearch.value || "").toLowerCase()

	return salesPersons.value
		.filter((person) => {
			// Exclude already selected
			if (selectedIds.includes(person.name)) {
				return false
			}
			// Filter by search term if provided
			if (searchLower) {
				const name = (
					person.sales_person_name ||
					person.name ||
					""
				).toLowerCase()
				return name.includes(searchLower)
			}
			return true
		})
		.slice(0, 10) // Limit to 10 results for performance
})

// Computed: Total allocation percentage
const totalSalesAllocation = computed(() => {
	return selectedSalesPersons.value.reduce(
		(sum, p) => sum + (p.allocated_percentage || 0),
		0,
	)
})

// Computed: Validation - sales person is required when enabled
const isSalesPersonValid = computed(() => {
	// If sales persons feature is disabled, always valid
	if (!settingsStore.enableSalesPersons) {
		return true
	}
	// At least one sales person must be selected
	if (selectedSalesPersons.value.length === 0) {
		return false
	}
	// At least one sales person must have include_in_commission === 1 (or not set to 0)
	const hasActivePerson = selectedSalesPersons.value.some(
		(p) => p.include_in_commission !== 0,
	)
	return hasActivePerson
})

// Helper functions for sales persons
function addSalesPerson(person) {
	// For Single mode, replace the existing selection with 100%
	if (settingsStore.isSingleSalesPerson) {
		selectedSalesPersons.value = [
			{
				sales_person: person.name,
				sales_person_name: person.sales_person_name || person.name,
				allocated_percentage: 100,
				commission_rate: person.commission_rate,
				include_in_commission: 1,
			},
		]
		// Close dropdown after single selection
		salesPersonSearch.value = ""
		salesPersonDropdownOpen.value = false
	} else {
		// For Multiple mode, add to the list and redistribute evenly
		selectedSalesPersons.value.push({
			sales_person: person.name,
			sales_person_name: person.sales_person_name || person.name,
			allocated_percentage: 0, // Will be recalculated
			commission_rate: person.commission_rate,
			include_in_commission: 1,
		})
		// Redistribute commission evenly among all selected
		redistributeCommission()
		// Keep dropdown open for multiple selection, just clear search
		salesPersonSearch.value = ""
		// Keep dropdown open so user can continue selecting
	}
}

function removeSalesPerson(personName) {
	const index = selectedSalesPersons.value.findIndex(
		(p) => p.sales_person === personName,
	)
	if (index > -1) {
		selectedSalesPersons.value.splice(index, 1)
		// Redistribute commission among remaining
		if (selectedSalesPersons.value.length > 0) {
			redistributeCommission()
		}
	}
}

function clearSalesPersons() {
	selectedSalesPersons.value = []
	salesPersonSearch.value = ""
}

// Redistribute commission evenly among all selected sales persons
function redistributeCommission() {
	const activePersons = selectedSalesPersons.value.filter(
		(p) => p.include_in_commission !== 0,
	)
	const count = activePersons.length
	if (count === 0) return

	const evenShare = 100 / count
	selectedSalesPersons.value.forEach((person) => {
		if (person.include_in_commission !== 0) {
			person.allocated_percentage = evenShare
		} else {
			person.allocated_percentage = 0
		}
	})
}

function toggleCommissionInclusion(personName) {
	const person = selectedSalesPersons.value.find(
		(p) => p.sales_person === personName,
	)
	if (!person) return

	// Toggle inclusion: 1 -> 0, or 0 -> 1
	person.include_in_commission = person.include_in_commission === 0 ? 1 : 0

	// Recalculate percentages after toggling
	redistributeCommission()
}

// Handle blur event for dropdown
function handleSalesPersonBlur() {
	// Delay closing to allow click events on dropdown items
	setTimeout(() => {
		salesPersonDropdownOpen.value = false
	}, 150)
}

// Load payment methods - from cache if offline, from server if online
async function loadPaymentMethods() {
	// Guard: Don't load if activePosProfile is not set or already loading
	if (!activePosProfile.value) {
		log.warn(
			"PaymentDialog: Cannot load payment methods - activePosProfile is not set",
		)
		return
	}

	// Skip if already loading or already loaded for this profile
	if (loadingPaymentMethods.value) {
		return
	}

	loadingPaymentMethods.value = true

	try {
		if (props.isOffline) {
			// Load from cache when offline using worker
			const cached = await offlineWorker.getCachedPaymentMethods(
				activePosProfile.value,
			)
			if (cached && cached.length > 0) {
				paymentMethods.value = cached
				lastSelectedMethod.value = null
			}
		} else {
			// Load from server when online
			await paymentMethodsResource.fetch()
		}
	} catch (error) {
		log.error("Error loading payment methods:", error)
	} finally {
		loadingPaymentMethods.value = false
	}
}

// Currency symbol for display
const currencySymbol = computed(() => getCurrencySymbol(props.currency))

const totalPaid = computed(() => {
	const sum = paymentEntries.value.reduce(
		(sum, entry) => sum + (entry.amount || 0),
		0,
	)
	return roundCurrency(sum)
})

// Customer credit payment is enabled if either:
// - allowCreditSale is enabled (allows going into debt AND using credit)
// - allowCustomerCreditPayment is enabled (only allows using positive credit)
const customerCreditEnabled = computed(() => {
	return props.allowCreditSale || props.allowCustomerCreditPayment
})

const totalAvailableCredit = computed(() => {
	// Use net_balance: negative means customer has credit, positive means they owe
	// Return negative of net_balance so positive = credit available, negative = outstanding
	return roundCurrency(-customerBalance.value.net_balance)
})

// Remaining credit after deducting what's already been applied as payment
const remainingAvailableCredit = computed(() => {
	const usedCredit = getMethodTotal("Customer Credit")
	const remaining = totalAvailableCredit.value - usedCredit
	return remaining > 0 ? roundCurrency(remaining) : 0
})

// Calculate the actual discount amount based on type (percentage or fixed amount)
// Use discount-eligible subtotal (excludes items with custom_not_included=1) as base
const discountBase = computed(
	() => props.discountEligibleSubtotal ?? props.subtotal,
)

const calculatedAdditionalDiscount = computed(() => {
	return roundCurrency(
		(discountBase.value * localAdditionalDiscount.value) / 100,
	)
})

const remainingAmount = computed(() => {
	const remaining = roundCurrency(props.grandTotal) - totalPaid.value
	return remaining > 0 ? roundCurrency(remaining) : 0
})

const changeAmount = computed(() => {
	const change = totalPaid.value - roundCurrency(props.grandTotal)
	return change > 0 ? roundCurrency(change) : 0
})

const customPaymentType = ref(null)

// ===========================================
// Write-Off Logic
// When enabled, allows small remaining amounts to be written off
// ===========================================

// Check if write-off is possible for the current remaining amount
const canWriteOff = computed(() => {
	// Write-off is only possible if:
	// 1. Write-off is allowed (setting enabled and limit > 0)
	// 2. There is a remaining amount to write off
	// 3. Remaining amount is within the write-off limit
	// 4. There is at least one payment entry
	return (
		props.allowWriteOff &&
		props.writeOffLimit > 0 &&
		remainingAmount.value > 0 &&
		remainingAmount.value <= props.writeOffLimit &&
		paymentEntries.value.length > 0
	)
})

// State to track if user wants to write off
const applyWriteOff = ref(false)

// Slide track ref for write-off slider
const slideTrack = ref(null)

// Slide position (0-100%)
const slidePosition = ref(0)
const isDragging = ref(false)

// Watch applyWriteOff to sync with slidePosition
watch(applyWriteOff, (newVal) => {
	if (!isDragging.value) {
		slidePosition.value = newVal ? 100 : 0
	}
})

// Smooth slide to activate write-off
const startSlide = (e) => {
	e.preventDefault()
	const track = slideTrack.value
	if (!track) return

	isDragging.value = true
	const rect = track.getBoundingClientRect()
	const trackWidth = rect.width
	const handleWidth = 48 // w-12 = 3rem = 48px

	const getX = (event) => {
		if (event.touches && event.touches.length > 0) {
			return event.touches[0].clientX - rect.left
		}
		return event.clientX - rect.left
	}

	const startX = getX(e)
	const startPosition = slidePosition.value

	const onMove = (event) => {
		event.preventDefault()
		const currentX = event.touches
			? event.touches[0].clientX - rect.left
			: event.clientX - rect.left
		const deltaX = currentX - startX
		const deltaPercent = (deltaX / (trackWidth - handleWidth)) * 100

		let newPosition = startPosition + deltaPercent
		newPosition = Math.max(0, Math.min(100, newPosition))
		slidePosition.value = newPosition
	}

	const onEnd = () => {
		isDragging.value = false

		// Snap to activated or deactivated based on threshold
		if (slidePosition.value > 40) {
			slidePosition.value = 100
			applyWriteOff.value = true
		} else {
			slidePosition.value = 0
			applyWriteOff.value = false
		}

		document.removeEventListener("mousemove", onMove)
		document.removeEventListener("mouseup", onEnd)
		document.removeEventListener("touchmove", onMove)
		document.removeEventListener("touchend", onEnd)
	}

	document.addEventListener("mousemove", onMove)
	document.addEventListener("mouseup", onEnd)
	document.addEventListener("touchmove", onMove, { passive: false })
	document.addEventListener("touchend", onEnd)
}

// The amount to be written off (0 if not applying write-off)
const writeOffAmount = computed(() => {
	if (canWriteOff.value && applyWriteOff.value) {
		return remainingAmount.value
	}
	return 0
})

// Effective remaining amount after write-off
const effectiveRemainingAmount = computed(() => {
	if (applyWriteOff.value && canWriteOff.value) {
		return 0
	}
	return remainingAmount.value
})

// ===========================================
// Exact Amount Validation Logic
// When useExactAmount is enabled:
// - Cash only: allows overpayment (change)
// - Non-cash only: must be exact amount
// - Mixed (cash + non-cash): must be exact total
// ===========================================

// Check if exact amount mode is active
// Note: Backend validation in POS Settings already prevents enabling use_exact_amount
// together with allow_credit_sale or allow_partial_payment
const isExactAmountModeActive = computed(() => {
	return settingsStore.useExactAmount
})

// Check if payment entries contain any cash payments
const hasCashPayment = computed(() => {
	return paymentEntries.value.some((entry) => {
		const method = paymentMethods.value.find(
			(m) => m.mode_of_payment === entry.mode_of_payment,
		)
		return isCashPaymentMethod(method)
	})
})

// Check if payment entries contain any non-cash payments
const hasNonCashPayment = computed(() => {
	return paymentEntries.value.some((entry) => {
		const method = paymentMethods.value.find(
			(m) => m.mode_of_payment === entry.mode_of_payment,
		)
		return method && !isCashPaymentMethod(method) && !entry.is_customer_credit
	})
})

// Check if current payment scenario allows overpayment (change)
const allowsOverpayment = computed(() => {
	// If exact amount mode is not active, allow overpayment
	if (!isExactAmountModeActive.value) return true

	// If no payments yet, default to allowing overpayment
	if (paymentEntries.value.length === 0) return true

	// Cash only: allows overpayment
	if (hasCashPayment.value && !hasNonCashPayment.value) return true

	// Non-cash or mixed: no overpayment allowed
	return false
})

// Check if current payment is valid according to exact amount rules
const isExactAmountValid = computed(() => {
	if (!isExactAmountModeActive.value) return true

	// If no payments, it's valid (nothing to validate yet)
	if (paymentEntries.value.length === 0) return true

	// Cash only: always valid (allows overpayment)
	if (hasCashPayment.value && !hasNonCashPayment.value) return true

	// Non-cash or mixed: total paid must not exceed grand total
	return totalPaid.value <= roundCurrency(props.grandTotal)
})

const canComplete = computed(() => {
	// Check Table Number validation for Dine In orders
	if (cartStore.orderType === "Dine In" && !cartStore.selectedTable) {
		return false
	}

	// Check sales person validation first (mandatory when enabled)
	if (!isSalesPersonValid.value) {
		return false
	}

	// Check exact amount validation
	if (!isExactAmountValid.value) {
		return false
	}

	// Order fully covered by coupon/discount — no payment entry required
	if (roundCurrency(props.grandTotal) <= 0) {
		return true
	}

	// For partial or zero payments (remaining amount exists)
	if (remainingAmount.value > 0) {
		// Enforce full payment for all profiles except Call Center
		if (!isCallCenterInvoice.value) {
			return false
		}
		// For Call Center, require selecting an Expected Payment Type
		if (!customPaymentType.value) {
			return false
		}
	}

	// Allow completing payment whenever there is at least one entry with amount > 0
	// This supports: multi-method split payments, partial payments, and full payments
	if (totalPaid.value > 0 && paymentEntries.value.length > 0) {
		return true
	}

	// Also allow when a method is selected and there is remaining to pay
	// (completePayment will auto-add the full remaining)
	if (lastSelectedMethod.value && remainingAmount.value > 0) {
		return true
	}

	// Allow Call Center to complete with 0 paid if they selected a payment type
	if (
		isCallCenterInvoice.value &&
		remainingAmount.value > 0 &&
		customPaymentType.value
	) {
		return true
	}

	return false
})

const paymentButtonText = computed(() => {
	// Show "Complete Payment" if fully paid or write-off covers remaining
	if (
		remainingAmount.value === 0 ||
		(applyWriteOff.value && canWriteOff.value)
	) {
		return __("Complete Payment")
	}
	// Show "Partial Payment" label when paying less than full amount
	if (totalPaid.value > 0 && remainingAmount.value > 0) {
		return __("Partial Payment")
	}
	return __("Complete Payment")
})

// Preload payment methods when posProfile is set (before dialog opens)
watch(
	() => activePosProfile.value,
	(newProfile) => {
		if (newProfile) {
			log.debug(
				"[PaymentDialog] Preloading payment methods for profile:",
				newProfile,
			)
			loadPaymentMethods()
			// Also preload sales persons if enabled
			if (settingsStore.enableSalesPersons && salesPersons.value.length === 0) {
				loadingSalesPersons.value = true
				salesPersonsResource.fetch()
			}
		}
	},
	{ immediate: true }, // Load immediately if posProfile is already set
)

// Pre-fetch customer balance when customer changes (before dialog opens)
// This ensures data is available immediately when dialog opens
watch(
	() => [
		props.customer,
		props.company,
		props.allowCreditSale,
		props.allowCustomerCreditPayment,
	],
	([customer, company, allowCreditSale, allowCustomerCreditPayment]) => {
		const creditEnabled = allowCreditSale || allowCustomerCreditPayment
		if (creditEnabled && customer && company) {
			log.debug("[PaymentDialog] Pre-fetching customer balance for:", customer)
			customerBalanceResource.fetch()
			customerCreditResource.fetch()
		}
	},
	{ immediate: true },
)

watch(show, (newVal) => {
	if (newVal) {
		// Reset state when dialog opens (but NOT customerBalance - it's pre-fetched)
		paymentEntries.value = []
		customAmount.value = ""
		numpadClear()
		mobileCustomAmount.value = ""
		desktopCustomAmount.value = ""
		lastSelectedMethod.value = null
		customerCredit.value = []
		// Note: Don't reset customerBalance here - it's pre-fetched when customer changes
		selectedSalesPersons.value = []
		salesPersonSearch.value = ""
		applyWriteOff.value = false // Reset write-off state
		// Set default delivery date to today for Sales Orders
		deliveryDate.value = isSalesOrder.value ? today : ""

		// Pre-populate custom fields and payments if they exist in cartStore (resumed draft invoice)
		receiptNumber.value = cartStore.customReceiptNumber || ""
		uniqueNumber.value = cartStore.customUniqueTalbatNumber || ""
		referenceNumber.value = cartStore.customThirdPartyReferanceNumber || ""
		customPaymentType.value = cartStore.customPaymentType || null

		if (cartStore.payments && cartStore.payments.length > 0) {
			paymentEntries.value = cartStore.payments.map((p) => ({
				mode_of_payment: p.mode_of_payment,
				amount: p.amount,
				type: p.type || "Cash",
			}))
		}

		// Debug logging
		log.debug("[PaymentDialog] Dialog opened with props:", {
			allowCreditSale: props.allowCreditSale,
			allowCustomerCreditPayment: props.allowCustomerCreditPayment,
			allowWriteOff: props.allowWriteOff,
			writeOffLimit: props.writeOffLimit,
			customer: props.customer,
			company: props.company,
			posProfile: activePosProfile.value,
		})

		// Don't auto-select — let user choose payment method
		lastSelectedMethod.value = null

		// Customer credit and balance is pre-fetched when customer changes (see watcher above)
		// Just log for debugging
		const creditEnabled =
			props.allowCreditSale || props.allowCustomerCreditPayment
		if (creditEnabled) {
			log.debug(
				"[PaymentDialog] Customer credit/balance should be pre-loaded, current balance:",
				customerBalance.value,
			)
		}

		if (
			settingsStore.enableSalesPersons &&
			activePosProfile.value &&
			salesPersons.value.length === 0
		) {
			loadingSalesPersons.value = true
			salesPersonsResource.fetch()
		}
		
		// Load tables if branch is selected
		if (cartStore.selectedBranch || shiftStore.profileBranch) {
			tablesResource.fetch()
		}

		// Load wallet info if customer is selected
		if (props.customer && props.company) {
			log.debug("[PaymentDialog] Loading wallet info...")
			loadingWallet.value = true
			walletInfoResource.fetch()
		} else {
			// Reset wallet info only if no customer
			walletInfo.value = {
				wallet_enabled: false,
				wallet_exists: false,
				wallet_balance: 0,
				wallet_name: null,
			}
		}
	}
})

watch(
	() => [settingsStore.enableSalesPersons, activePosProfile.value],
	([enabled, posProfile]) => {
		if (
			enabled &&
			posProfile &&
			salesPersons.value.length === 0 &&
			!loadingSalesPersons.value
		) {
			loadingSalesPersons.value = true
			salesPersonsResource.fetch()
		}
	},
	{ immediate: true },
)

// ===========================================
// Payment Method Press Handler (Long Press Support)
// Uses composable for clean, reusable press handling
// ===========================================

// Select payment method (tap action)
function selectPaymentMethod(method) {
	lastSelectedMethod.value = method
	log.debug("[PaymentDialog] Selected payment method:", method.mode_of_payment)
	if (remainingAmount.value > 0) {
		// Both desktop and mobile: just select method and pre-fill amount
		// User will use "Add" or "Pay Full" button to confirm
		const isCash = isCashPaymentMethod(method)
		const exactAmt = isCash
			? Math.ceil(remainingAmount.value)
			: roundCurrency(remainingAmount.value)
		setNumpadValue(exactAmt)
		desktopCustomAmount.value = exactAmt.toFixed(2)
		mobileCustomAmount.value = exactAmt.toFixed(2)
	}
}

// Helper to get default non-wallet payment method
function getDefaultNonWalletMethod() {
	// First try to find the default method that's not a wallet payment
	const defaultMethod = paymentMethods.value.find(
		(m) => m.default && !isWalletPaymentMethod(m.mode_of_payment),
	)
	if (defaultMethod) return defaultMethod

	// Otherwise, find any non-wallet method (preferably Cash)
	const cashMethod = paymentMethods.value.find(
		(m) =>
			!isWalletPaymentMethod(m.mode_of_payment) &&
			(m.mode_of_payment.toLowerCase().includes("cash") ||
				m.type?.toLowerCase() === "cash"),
	)
	if (cashMethod) return cashMethod

	// Fall back to first non-wallet method
	return paymentMethods.value.find(
		(m) => !isWalletPaymentMethod(m.mode_of_payment),
	)
}

// Helper to switch to next payment method after partial wallet payment
function switchToNextPaymentMethod(partialAmount) {
	const nextMethod = getDefaultNonWalletMethod()
	if (nextMethod) {
		lastSelectedMethod.value = nextMethod
		// Pre-fill numpad with remaining amount for convenience
		const newRemaining = roundCurrency(remainingAmount.value)
		if (newRemaining > 0) {
			setNumpadValue(newRemaining)
			// Also set mobile custom amount
			mobileCustomAmount.value = newRemaining.toFixed(2)
		}
		showInfo(
			__("Points applied: {0}. Please pay remaining {1} with {2}", [
				formatCurrency(partialAmount),
				formatCurrency(newRemaining),
				__(nextMethod.mode_of_payment),
			]),
		)
	}
}

// Add payment for the full remaining amount on method click
function addPayment(method) {
	quickAddPayment(method)
}

// Quick add payment (long press action)
function quickAddPayment(method) {
	if (remainingAmount.value <= 0) return

	lastSelectedMethod.value = method

	let amt = remainingAmount.value
	let isPartialWalletPayment = false

	// Wallet payment validation: limit to available balance
	if (isWalletPaymentMethod(method.mode_of_payment)) {
		const walletAvailable = availableWalletBalance.value
		if (walletAvailable <= 0) {
			showWarning(__("No redeemable points available"))
			return
		}
		if (amt > walletAvailable) {
			// Limit payment to available redeemable points
			amt = walletAvailable
			isPartialWalletPayment = true
		}
	}

	// Exact amount validation for non-cash payments
	if (isExactAmountModeActive.value && !isCashPaymentMethod(method)) {
		const currentNonCashTotal = paymentEntries.value
			.filter((entry) => {
				const m = paymentMethods.value.find(
					(pm) => pm.mode_of_payment === entry.mode_of_payment,
				)
				return m && !isCashPaymentMethod(m) && !entry.is_customer_credit
			})
			.reduce((sum, entry) => sum + (entry.amount || 0), 0)

		const maxAllowed = roundCurrency(props.grandTotal) - currentNonCashTotal

		if (maxAllowed <= 0) {
			showWarning(
				__("Cannot add more non-cash payments. Use cash for overpayment."),
			)
			return
		}

		// For quick add (long press), always use exact remaining amount
		amt = maxAllowed
	}

	// For mixed payments in exact amount mode, validate total doesn't exceed grand total
	if (
		isExactAmountModeActive.value &&
		hasNonCashPayment.value &&
		isCashPaymentMethod(method)
	) {
		const maxAllowed = roundCurrency(props.grandTotal) - totalPaid.value
		if (maxAllowed <= 0) {
			showInfo(__("Invoice fully paid. No additional payment needed."))
			return
		}
		// For quick add (long press), use exact remaining to complete payment
		amt = maxAllowed
	}

	paymentEntries.value.push({
		mode_of_payment: method.mode_of_payment,
		amount: roundCurrency(amt),
		type: method.type || __("Cash"),
		is_wallet_payment: isWalletPaymentMethod(method.mode_of_payment),
	})
	log.debug("[PaymentDialog] Long press payment added:", method.mode_of_payment)

	// If this was a partial wallet payment, switch to another payment method
	if (isPartialWalletPayment) {
		nextTick(() => {
			switchToNextPaymentMethod(amt)
		})
	}
}

// Initialize long press composable with callbacks
const {
	onPointerDown: handlePointerDown,
	onPointerUp: handlePointerUp,
	onPointerCancel: handlePointerCancel,
} = useLongPress({
	duration: 500,
	onTap: selectPaymentMethod,
	onLongPress: quickAddPayment,
})

// Wrapper handlers to pass method to composable
function onPaymentMethodDown(method, event) {
	handlePointerDown(event, method)
}

function onPaymentMethodUp(method) {
	handlePointerUp(method)
}

function onPaymentMethodCancel() {
	handlePointerCancel()
}

// Add custom amount for a method
function addCustomPayment(method, amount) {
	log.debug("[PaymentDialog] Add custom payment:", {
		method: method.mode_of_payment,
		amount: amount,
		currentEntries: paymentEntries.value.length,
	})

	let amt = Number.parseFloat(amount)
	if (!amt || amt <= 0) return
	amt = roundCurrency(amt)
	if (amt <= 0) return

	let isPartialWalletPayment = false

	// Wallet payment validation: limit to available balance
	if (isWalletPaymentMethod(method.mode_of_payment)) {
		const walletAvailable = availableWalletBalance.value
		if (walletAvailable <= 0) {
			showWarning(__("No redeemable points available"))
			return
		}
		if (amt > walletAvailable) {
			// Limit payment to available redeemable points
			amt = walletAvailable
			isPartialWalletPayment = true
		}
	}

	// Exact amount validation for non-cash payments
	if (isExactAmountModeActive.value && !isCashPaymentMethod(method)) {
		// Calculate the remaining amount after ALL existing payments (cash + non-cash)
		// Non-cash payments in exact amount mode must equal the remaining balance exactly
		const maxAllowed = roundCurrency(props.grandTotal - totalPaid.value)

		if (maxAllowed <= 0) {
			showWarning(
				__("Cannot add more non-cash payments. Use cash for overpayment."),
			)
			return
		}

		// Warn and reject if amount doesn't match exact remaining (use rounded comparison to avoid floating-point issues)
		if (roundCurrency(amt) !== maxAllowed) {
			showWarning(
				__("Non-cash payment must equal {0} exactly", [
					formatCurrency(maxAllowed),
				]),
			)
			return
		}

		// Use the maxAllowed value to ensure exact match
		amt = maxAllowed
	}

	// For mixed payments in exact amount mode, validate total doesn't exceed grand total
	if (
		isExactAmountModeActive.value &&
		hasNonCashPayment.value &&
		isCashPaymentMethod(method)
	) {
		const newTotal = totalPaid.value + amt
		if (newTotal > roundCurrency(props.grandTotal)) {
			showWarning(
				__("Mixed payment cannot exceed invoice total. Limit: {0}", [
					formatCurrency(roundCurrency(props.grandTotal) - totalPaid.value),
				]),
			)
			return
		}
	}

	paymentEntries.value.push({
		mode_of_payment: method.mode_of_payment,
		amount: amt,
		type: method.type || __("Cash"),
		is_wallet_payment: isWalletPaymentMethod(method.mode_of_payment),
	})

	log.debug("[PaymentDialog] Payment added, new entries:", paymentEntries.value)
	customAmount.value = ""

	// If this was a partial wallet payment, switch to another payment method
	if (isPartialWalletPayment) {
		nextTick(() => {
			switchToNextPaymentMethod(amt)
		})
	}
}

// Apply existing customer credit to payment
function applyCustomerCredit() {
	log.debug("[PaymentDialog] Apply customer credit:", {
		totalCredit: totalAvailableCredit.value,
		remainingAmount: remainingAmount.value,
		currentEntries: paymentEntries.value.length,
	})

	if (remainingAmount.value === 0 || totalAvailableCredit.value === 0) return

	// Calculate how much credit to apply (min of remaining amount and available credit)
	const creditToApply = Math.min(
		remainingAmount.value,
		totalAvailableCredit.value,
	)

	// Add credit as a payment entry
	paymentEntries.value.push({
		mode_of_payment: "Customer Credit",
		amount: roundCurrency(creditToApply),
		type: "Credit",
		is_customer_credit: true,
		credit_details: customerCredit.value.map((credit) => ({
			...credit,
			credit_to_redeem: 0, // Will be calculated on backend
		})),
	})

	log.debug(
		"[PaymentDialog] Existing credit applied, new entries:",
		paymentEntries.value,
	)
}

// Add "Pay on Account" - Credit Sale (invoice with outstanding amount)
// Supports fully unpaid invoices (paid_amount = 0) and partial payments
function addCreditAccountPayment() {
	log.debug("[PaymentDialog] Add credit account payment (Pay Later):", {
		grandTotal: props.grandTotal,
		currentPaid: totalPaid.value,
		remainingAmount: remainingAmount.value,
	})

	// Allow fully unpaid invoices (paid_amount = 0) - the entire amount goes on account

	// Complete with whatever has been paid so far, remainder goes on account
	const paymentData = {
		payments: paymentEntries.value.length > 0 ? paymentEntries.value : [],
		change_amount: 0,
		is_partial_payment: totalPaid.value < props.grandTotal,
		is_credit_sale: true, // Mark as credit sale
		paid_amount: totalPaid.value,
		outstanding_amount: remainingAmount.value > 0 ? remainingAmount.value : 0,
		custom_payment_type: customPaymentType.value,
	}

	log.debug(
		"[PaymentDialog] Emitting credit sale payment-completed:",
		paymentData,
	)
	emit("payment-completed", paymentData)
	show.value = false
}

function removePaymentEntry(index) {
	if (index >= 0 && index < paymentEntries.value.length) {
		paymentEntries.value.splice(index, 1)
	}
}

function clearAll() {
	paymentEntries.value = []
	customAmount.value = ""
}

function completePayment() {
	log.debug("[PaymentDialog] Complete payment called:", {
		canComplete: canComplete.value,
		totalPaid: totalPaid.value,
		grandTotal: props.grandTotal,
		allowPartialPayment: props.allowPartialPayment,
		paymentEntries: paymentEntries.value,
		salesPersons: selectedSalesPersons.value,
		writeOff: {
			canWriteOff: canWriteOff.value,
			applyWriteOff: applyWriteOff.value,
			writeOffAmount: writeOffAmount.value,
		},
	})

	if (!canComplete.value) {
		log.warn("[PaymentDialog] Cannot complete - validation failed")
		return
	}

	// Calculate if this is a partial or fully unpaid payment
	const effectivePaid = totalPaid.value + writeOffAmount.value
	const isPartial = effectivePaid < props.grandTotal
	const isFullyUnpaid = effectivePaid === 0 && props.grandTotal > 0

	if (needsReceipt.value && !receiptNumber.value) {
		showWarning({
			message: __("Receipt Number is mandatory"),
		})
		return
	}

	if (isCallCenterInvoice.value && !cartStore.selectedBranch) {
		showWarning({
			message: __("Please select a Target Branch"),
		})
		return
	}

	if (isTalabat.value && !referenceNumber.value) {
		showWarning({
			message: __(
				"Third Party Reference Number is mandatory for Talabat orders",
			),
		})
		return
	}

	const paymentData = {
		payments: paymentEntries.value,
		change_amount: changeAmount.value,
		is_partial_payment: isPartial,
		is_credit_sale: isFullyUnpaid || isPartial,
		paid_amount: totalPaid.value,
		outstanding_amount: isPartial
			? remainingAmount.value - writeOffAmount.value
			: 0,
		sales_team:
			selectedSalesPersons.value.length > 0 ? selectedSalesPersons.value : null,
		delivery_date: isSalesOrder.value ? deliveryDate.value : null,
		// Custom Fields
		custom_receipt_number: receiptNumber.value,
		custom_unique_talbat_number: uniqueNumber.value,
		custom_third_party_referance_number: referenceNumber.value,
		// Write-off data
		write_off_amount: writeOffAmount.value,
		is_write_off: writeOffAmount.value > 0,
		custom_payment_type: customPaymentType.value,
	}

	log.debug("[PaymentDialog] Emitting payment-completed:", paymentData)

	emit("payment-completed", paymentData)
	// We don't close the dialog here anymore, we let the parent close it after submission
	// so the user can see the progress bar and processing overlay.
}

function formatCurrency(amount) {
	return formatCurrencyUtil(Number.parseFloat(amount || 0), props.currency)
}

// Get total amount for a specific payment method
function getMethodTotal(methodName) {
	return paymentEntries.value
		.filter((entry) => entry.mode_of_payment === methodName)
		.reduce((sum, entry) => sum + (entry.amount || 0), 0)
}

function getDiscountOptions(currentVal) {
	const baseOptions = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
	if (currentVal !== undefined && currentVal !== null && !baseOptions.includes(currentVal)) {
		const newOptions = [...baseOptions, currentVal]
		newOptions.sort((a, b) => a - b)
		return newOptions
	}
	return baseOptions
}

// Additional discount handlers
function handleAdditionalDiscountChange() {
	let discountValue = localAdditionalDiscount.value

	// Clamp to max allowed
	if (
		settingsStore.maxDiscountAllowed > 0 &&
		discountValue > settingsStore.maxDiscountAllowed
	) {
		localAdditionalDiscount.value = settingsStore.maxDiscountAllowed
		discountValue = settingsStore.maxDiscountAllowed
		showWarning(
			__("Maximum allowed discount is {0}%", [
				settingsStore.maxDiscountAllowed,
			]),
		)
	}

	if (discountValue > 100) {
		localAdditionalDiscount.value = 100
		discountValue = 100
	}

	if (discountValue < 0) {
		localAdditionalDiscount.value = 0
		discountValue = 0
	}

	const discountAmount = roundCurrency(
		(discountBase.value * discountValue) / 100,
	)
	emit("update-additional-discount", discountAmount)
}

// Watch for dialog open to sync additional discount from parent
watch(
	() => props.modelValue,
	(isOpen) => {
		if (isOpen) {
			// Only sync when dialog opens, not continuously
			if (props.additionalDiscount && discountBase.value > 0) {
				localAdditionalDiscount.value = Math.round(
					(props.additionalDiscount * 100) / discountBase.value,
				)
			} else {
				localAdditionalDiscount.value = 0
			}
		}
	},
)
</script>
