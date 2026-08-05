<template>
	<div class="flex flex-col h-screen bg-gray-50">
		<!-- Returned / Cancelled / Needs-approval order alarm (Call Center) -->
		<div v-if="reversalAlert" class="fixed top-0 inset-x-0 z-[100] text-white px-6 py-4 flex items-center justify-between shadow-2xl animate-pulse" :class="reversalAlert.kind === 'needs_action' ? 'bg-amber-500' : 'bg-red-600'">
			<div class="text-xl font-extrabold flex items-center">
				{{ reversalAlert.kind === 'returned' ? '↩ مرتجع من الكول سنتر' : reversalAlert.kind === 'cancelled' ? '❌ إلغاء من الكول سنتر' : '⚠ طلب مرتجع يحتاج موافقتك' }}
				<span v-if="reversalAlert.number" class="ml-2 px-3 py-0.5 bg-white/25 rounded-lg">{{ reversalAlert.number }}</span>
			</div>
			<div class="flex items-center gap-2">
				<button v-if="reversalAlert.kind === 'needs_action'" @click="goToNeedMyAction" class="px-4 py-1.5 bg-white/25 hover:bg-white/40 rounded-lg font-bold text-lg">مراجعة</button>
				<button @click="dismissReversalAlert" class="px-4 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg font-bold text-lg">✕</button>
			</div>
		</div>
		<!-- Header -->
		<div class="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3 shadow-sm">
			<button
				@click="goBack"
				class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				</svg>
				{{ __("Back") }}
			</button>
			<h1 class="text-lg font-semibold text-gray-900">{{ __("All Orders") }}</h1>
			<span class="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-full">
				<span class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
				{{ __("Live") }}
			</span>
			<div class="flex-1"></div>
			<!-- Order Number Limit settings (System Manager only) -->
			<button
				v-if="isSystemManager"
				@click="openLimitSettings"
				class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
				:title="__('Order Number Limit')"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
				</svg>
				<span class="hidden sm:inline">{{ __("Order Limit") }}</span>
				<span class="bg-blue-100 text-blue-700 text-xs font-bold px-1.5 py-0.5 rounded">{{ orderNumberLimit || __("∞") }}</span>
			</button>
			<button
				@click="fetchOrders"
				:disabled="loading"
				class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition-colors"
			>
				<svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
				</svg>
				<svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
				{{ __("Refresh") }}
			</button>
		</div>

		<!-- Filters -->
		<div class="bg-white border-b border-gray-200 px-4 py-3">
			<!-- Search + Toggle -->
			<div class="flex items-center gap-3 mb-3">
				<div class="flex-1 relative">
					<svg class="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					<input
						v-model="search"
						type="text"
						:placeholder="__('Search by order #, customer, mobile, branch...')"
						class="w-full ps-10 pe-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
					/>
				</div>
				<button
					@click="showFilters = !showFilters"
					:class="[
						'flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border transition-colors',
						showFilters
							? 'bg-blue-50 text-blue-700 border-blue-300'
							: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
					]"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
					</svg>
					{{ showFilters ? __("Hide Filters") : __("Show Filters") }}
					<span v-if="activeFilterCount > 0" class="bg-blue-600 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[20px] text-center">
						{{ activeFilterCount }}
					</span>
				</button>
			</div>

			<!-- Filter Panel -->
			<transition
				enter-active-class="transition-all duration-200 ease-out"
				leave-active-class="transition-all duration-150 ease-in"
				enter-from-class="opacity-0 -translate-y-2 max-h-0"
				enter-to-class="opacity-100 translate-y-0 max-h-96"
				leave-from-class="opacity-100 translate-y-0 max-h-96"
				leave-to-class="opacity-0 -translate-y-2 max-h-0"
			>
				<div v-if="showFilters" class="bg-gray-50 rounded-lg p-4 border border-gray-200 overflow-hidden">
					<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
						<!-- Invoice No -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Invoice No.") }}</label>
							<input v-model="filters.invoice_name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
						</div>
						<!-- Customer / Mobile -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Customer / Mobile") }}</label>
							<input v-model="filters.customer" type="text" :placeholder="__('Name or mobile number')" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
						</div>
						<!-- Status -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Status") }}</label>
							<select v-model="filters.status" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white">
								<option value="">{{ __("All") }}</option>
								<option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
							</select>
						</div>
						<!-- POS Source -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Source") }}</label>
							<select v-model="filters.pos_source" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white">
								<option value="">{{ __("All") }}</option>
								<option value="cashier">{{ __("Cashier") }}</option>
								<option value="call_center">{{ __("Call Center") }}</option>
							</select>
						</div>
						<!-- Branch -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Branch") }}</label>
							<select v-model="filters.branch" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white">
								<option value="">{{ __("All") }}</option>
								<option v-for="b in branchOptions" :key="b" :value="b">{{ b }}</option>
							</select>
						</div>
						<!-- From Date (only if user has permission) -->
						<div v-if="canSelectDates">
							<label class="block text-xs font-medium text-gray-600 mb-1">
								{{ __("From Date") }}
								<span v-if="maxDays > 0" class="text-gray-400 font-normal">({{ __("last {0} days", [maxDays]) }})</span>
							</label>
							<input v-model="filters.date_from" @change="onDateRangeChange" type="date" :min="minAllowedDate" :max="todayStr" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
						</div>
						<!-- To Date (only if user has permission) -->
						<div v-if="canSelectDates">
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("To Date") }}</label>
							<input v-model="filters.date_to" @change="onDateRangeChange" type="date" :min="minAllowedDate" :max="todayStr" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
						</div>
						<!-- Shift date info (shown when dates are locked) -->
						<div v-if="!canSelectDates" class="sm:col-span-2 flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
							<svg class="w-4 h-4 text-amber-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							<span class="text-xs text-amber-700">
								{{ __("Showing orders for shift period: {0} to {1}", [formatShiftDateTime(shiftStart), formatShiftDateTime(shiftEnd)]) }}
							</span>
						</div>
						<!-- Order Type -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Order Type") }}</label>
							<select v-model="filters.order_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white">
								<option value="">{{ __("All") }}</option>
								<option v-for="t in orderTypeOptions" :key="t" :value="t">{{ t }}</option>
							</select>
						</div>
						<!-- Return filter -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Type") }}</label>
							<select v-model="filters.invoice_type" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white">
								<option value="">{{ __("All") }}</option>
								<option value="regular">{{ __("Regular") }}</option>
								<option value="return">{{ __("Return") }}</option>
							</select>
						</div>
						<!-- Order Number -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Order No.") }}</label>
							<input v-model="filters.order_number" type="text" :placeholder="__('e.g. P-5')" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
						</div>
						<!-- Driver -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Driver") }}</label>
							<select v-model="filters.driver" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white">
								<option value="">{{ __("All") }}</option>
								<option v-for="d in activeDrivers" :key="d.name" :value="d.name">{{ d.full_name || d.name }}</option>
							</select>
						</div>
						<!-- Unique Number -->
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Unique No.") }}</label>
							<input v-model="filters.unique_number" type="text" :placeholder="__('Talabat unique no.')" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
						</div>
					</div>
					<div class="flex justify-end gap-2 mt-3">
						<button @click="resetFilters" class="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors">
							{{ __("Clear Filters") }}
						</button>
						<button @click="showFilters = false" class="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
							{{ __("Collapse") }}
						</button>
					</div>
				</div>
			</transition>
		</div>

		<!-- Table -->
		<div class="flex-1 overflow-auto px-4 py-3">
			<!-- Loading -->
			<div v-if="loading && !orders.length" class="flex items-center justify-center py-20">
				<div class="text-center">
					<svg class="w-10 h-10 animate-spin text-blue-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
					</svg>
					<p class="text-sm text-gray-500">{{ __("Loading orders...") }}</p>
				</div>
			</div>

			<!-- Empty State -->
			<div v-else-if="!filteredOrders.length && !loading" class="flex items-center justify-center py-20">
				<div class="text-center">
					<svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
					<p class="text-gray-500 font-medium">{{ __("No orders found") }}</p>
					<p class="text-sm text-gray-400 mt-1">{{ __("Try adjusting your filters or date range") }}</p>
				</div>
			</div>

			<!-- Orders Table -->
			<div v-else class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="bg-gray-50 border-b border-gray-200">
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider"></th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:text-gray-900" @click="sortBy('name')">
									{{ __("Invoice") }}
									<span v-if="sortField === 'name'" class="ms-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:text-gray-900" @click="sortBy('customer_name')">
									{{ __("Customer") }}
									<span v-if="sortField === 'customer_name'" class="ms-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("Mobile") }}
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:text-gray-900" @click="sortBy('posting_date')">
									{{ __("Date") }}
									<span v-if="sortField === 'posting_date'" class="ms-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("POS Profile") }}
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:text-gray-900" @click="sortBy('branch')">
									{{ __("Branch") }}
									<span v-if="sortField === 'branch'" class="ms-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("Created By") }}
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("Order Type") }}
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("Driver") }}
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("Status") }}
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("KDS") }}
								</th>
								<th class="px-4 py-3 text-start text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("Delivery") }}
								</th>
								<th class="px-4 py-3 text-end text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:text-gray-900" @click="sortBy('grand_total')">
									{{ __("Total") }}
									<span v-if="sortField === 'grand_total'" class="ms-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
								</th>
								<th class="px-4 py-3 text-end text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("Outstanding") }}
								</th>
								<th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
									{{ __("Actions") }}
								</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<template v-for="order in paginatedOrders" :key="order.name">
								<tr class="hover:bg-gray-50 transition-colors">
									<!-- Expand toggle -->
									<td class="px-4 py-3">
										<button @click="toggleExpand(order.name)" class="text-gray-400 hover:text-gray-600">
											<svg :class="['w-4 h-4 transition-transform', expanded[order.name] ? 'rotate-90' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
											</svg>
										</button>
									</td>
									<!-- Invoice -->
									<td class="px-4 py-3">
										<div class="font-medium text-blue-600">
											{{ order.custom_number_order || order.name }}
											<span v-if="order.supplements && order.supplements.length" class="ms-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700">+{{ order.supplements.length }}</span>
										</div>
										<div v-if="order.custom_number_order" class="text-xs text-gray-400 mt-0.5">{{ order.name }}</div>
									</td>
									<!-- Customer -->
									<td class="px-4 py-3 text-gray-900 font-medium">{{ order.customer_name || order.customer }}</td>
									<!-- Mobile -->
									<td class="px-4 py-3 text-gray-900 text-sm">
										<div class="flex items-center gap-1.5">
											<div class="min-w-0">
												<div v-if="order.mobile_no">{{ order.mobile_no }}</div>
												<div v-if="order.other_mobile_no" class="text-gray-600">{{ order.other_mobile_no }}</div>
												<span v-if="!order.mobile_no && !order.other_mobile_no" class="text-gray-300">-</span>
											</div>
											<button v-if="order.customer" @click.stop="openMobileDialog(order)" :title="__('Add/Edit second mobile')" class="p-1 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-colors shrink-0">
												<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
											</button>
										</div>
									</td>
									<!-- Date -->
									<td class="px-4 py-3 text-gray-900">{{ order.posting_date }}</td>
									<!-- POS Profile -->
									<td class="px-4 py-3 text-gray-900">{{ order.pos_profile || '-' }}</td>
									<!-- Branch -->
									<td class="px-4 py-3 text-gray-900 font-medium">{{ order.branch || '-' }}</td>
									<!-- Created By -->
									<td class="px-4 py-3 text-gray-900 text-sm">{{ order.owner_name || order.owner || '-' }}</td>
									<!-- Order Type -->
									<td class="px-4 py-3 text-gray-900 font-medium">{{ order.custom_order_type || '-' }}</td>
									<!-- Driver -->
									<td class="px-4 py-3 text-gray-900">
										<span v-if="order.driver" class="inline-flex items-center gap-1 text-sm">
											<svg class="w-3.5 h-3.5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
											{{ getDriverDisplayName(order.driver) }}
										</span>
										<span v-else class="text-gray-400">-</span>
									</td>
									<!-- Status -->
									<td class="px-4 py-3">
										<span :class="getStatusClasses(order.display_status)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
											{{ order.display_status }}
										</span>
									</td>
									<!-- KDS Status -->
									<td class="px-4 py-3">
										<span v-if="order.kds_status" :class="getKdsStatusClasses(order.kds_status)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
											{{ order.kds_status }}
										</span>
										<span v-else class="text-gray-300">-</span>
									</td>
									<!-- Delivery Status -->
									<td class="px-4 py-3">
										<span v-if="order.delivery_status" :class="getDeliveryStatusClasses(order.delivery_status)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
											{{ order.delivery_status }}
										</span>
										<span v-else class="text-gray-300">-</span>
									</td>
									<!-- Total (hidden once the order is Paid) -->
									<td class="px-4 py-3 text-end font-medium text-gray-900">
										<span v-if="order.display_status !== 'Paid'">{{ formatNumber(order._combined_total !== undefined ? order._combined_total : order.grand_total) }}</span>
										<span v-else class="text-gray-300">-</span>
									</td>
									<!-- Outstanding -->
									<td class="px-4 py-3 text-end" :class="(order._combined_outstanding !== undefined ? order._combined_outstanding : order.outstanding_amount) > 0 ? 'text-red-600 font-medium' : 'text-gray-400'">
										{{ formatNumber(order._combined_outstanding !== undefined ? order._combined_outstanding : order.outstanding_amount) }}
									</td>
									<!-- Actions -->
									<td class="px-4 py-3">
										<div class="flex items-center justify-center gap-1">
											<!-- Edit Order (draft) / Add to Order (submitted) -->
											<button
												v-if="order.docstatus === 0 || order.docstatus === 1"
												@click="editOrder(order)"
												:disabled="editLoading === order.name"
												:class="order.docstatus === 1
													? 'p-1.5 text-green-600 hover:text-green-800 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50'
													: 'p-1.5 text-amber-600 hover:text-amber-800 hover:bg-amber-50 rounded-lg transition-colors disabled:opacity-50'"
												:title="order.docstatus === 1 ? __('Add to Order') : __('Edit Order')"
											>
												<svg v-if="editLoading === order.name" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
													<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
													<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
												</svg>
												<svg v-else-if="order.docstatus === 1" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
												</svg>
												<svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
												</svg>
											</button>
											<!-- View -->
											<button @click="viewInvoice(order.name)" class="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" :title="__('View')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
												</svg>
											</button>
											<!-- Print -->
											<button @click="printInvoice(order.name)" class="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors" :title="__('Print')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
												</svg>
											</button>
											<!-- Kitchen Print -->
											<button @click="printKitchen(order.name)" class="p-1.5 text-gray-500 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors" :title="__('Kitchen Print')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
												</svg>
											</button>
											<!-- Assign Driver (Delivery orders only) -->
											<button v-if="order.custom_order_type === 'Delivery'" @click="openAssignDriverDialog(order)" class="p-1.5 text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-colors" :title="order.driver ? __('Change Driver') : __('Assign Driver')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
												</svg>
											</button>
											<!-- ===== Call Center: convert between Pickup and Delivery ===== -->
											<!-- Convert to Delivery (Pickup orders only) -->
											<button v-if="isCallCenter && order.custom_order_type === 'Pickup' && order.docstatus === 1" @click.stop="convertOrderType(order, 'Delivery')" class="p-1.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-colors" :title="__('Convert to Delivery')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1.5 9.5A2 2 0 008.5 19h7a2 2 0 001.99-1.5L19 8" />
												</svg>
											</button>
											<!-- Convert to Pickup (Delivery orders only) -->
											<button v-if="isCallCenter && order.custom_order_type === 'Delivery' && order.docstatus === 1" @click.stop="convertOrderType(order, 'Pickup')" class="p-1.5 text-orange-600 hover:text-orange-800 hover:bg-orange-50 rounded-lg transition-colors" :title="__('Convert to Pickup')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
												</svg>
											</button>
											<!-- ===== Cashier (non-Call-Center): convert between Dine In and Takeaway ===== -->
											<!-- Convert to Takeaway (Dine In orders only) -->
											<button v-if="!isCallCenter && order.custom_order_type === 'Dine In' && order.docstatus === 1" @click.stop="convertOrderType(order, 'Pickup')" class="p-1.5 text-orange-600 hover:text-orange-800 hover:bg-orange-50 rounded-lg transition-colors" :title="__('Convert to Takeaway')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1.5 9.5A2 2 0 008.5 19h7a2 2 0 001.99-1.5L19 8" />
												</svg>
											</button>
											<!-- Convert to Dine In (Takeaway/Pickup orders only) -->
											<button v-if="!isCallCenter && order.custom_order_type === 'Pickup' && order.docstatus === 1" @click.stop="convertOrderType(order, 'Dine In')" class="p-1.5 text-purple-600 hover:text-purple-800 hover:bg-purple-50 rounded-lg transition-colors" :title="__('Convert to Dine In')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 10l2-6h14l2 6M3 10v10a1 1 0 001 1h16a1 1 0 001-1V10" />
												</svg>
											</button>
											<!-- Pay Outstanding -->
											<button v-if="order.outstanding_amount > 0" @click="payOrder(order)" class="p-1.5 text-green-600 hover:text-green-800 hover:bg-green-50 rounded-lg transition-colors" :title="__('Pay Outstanding')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
												</svg>
											</button>
											<!-- Return to Need My Action (Call Center only, rejected drafts) -->
											<button v-if="isCallCenter && order.docstatus === 0 && order.custom_is_rejected" @click="openReturnDialog(order)" class="p-1.5 text-amber-600 hover:text-amber-800 hover:bg-amber-50 rounded-lg transition-colors" :title="__('Return to Need My Action')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a5 5 0 015 5v2m-8-7l-4-4m0 0l4-4m-4 4h4" />
												</svg>
											</button>
											<!-- Cancel/Delete -->
											<button @click="deleteOrder(order)" class="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" :title="__('Cancel')">
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
												</svg>
											</button>
										</div>
									</td>
								</tr>
								<!-- Expanded Items Row -->
								<tr v-if="expanded[order.name]">
									<td colspan="13" class="px-8 py-3 bg-gray-50">
										<!-- Main order items -->
										<div class="text-xs font-semibold text-gray-500 uppercase mb-2">
											{{ __("Items") }}
											<span v-if="order.supplements && order.supplements.length" class="text-gray-400 normal-case">— {{ order.custom_number_order || order.name }}</span>
										</div>
										<table class="w-full text-sm">
											<thead>
												<tr class="text-xs text-gray-500">
													<th class="text-start pb-1">{{ __("Item") }}</th>
													<th class="text-start pb-1">{{ __("Item Name") }}</th>
													<th class="text-center pb-1">{{ __("Qty") }}</th>
													<th class="text-end pb-1">{{ __("Rate") }}</th>
													<th class="text-end pb-1">{{ __("Amount") }}</th>
												</tr>
											</thead>
											<tbody>
												<tr v-for="(item, idx) in order.items" :key="idx" class="border-t border-gray-100">
													<td class="py-1 text-gray-700">{{ item.item_code }}</td>
													<td class="py-1 text-gray-600">{{ item.item_name }}</td>
													<td class="py-1 text-center text-gray-700">{{ item.qty }} {{ item.uom }}</td>
													<td class="py-1 text-end text-gray-600">{{ formatNumber(item.rate) }}</td>
													<td class="py-1 text-end text-gray-900 font-medium">{{ formatNumber(item.amount) }}</td>
												</tr>
											</tbody>
										</table>
										<!-- Supplement items -->
										<template v-if="order.supplements && order.supplements.length">
											<div v-for="sup in order.supplements" :key="sup.name" class="mt-3 pt-3 border-t border-gray-200">
												<div class="text-xs font-semibold text-indigo-600 uppercase mb-2">
													{{ __("Supplement") }}: {{ sup.custom_number_order }}
													<span class="text-gray-400 normal-case font-normal ms-2">{{ sup.name }}</span>
													<span class="ms-2 text-gray-500 normal-case font-normal">{{ formatNumber(sup.grand_total) }}</span>
												</div>
												<table class="w-full text-sm">
													<tbody>
														<tr v-for="(item, idx) in sup.items" :key="idx" class="border-t border-gray-100">
															<td class="py-1 text-gray-700">{{ item.item_code }}</td>
															<td class="py-1 text-gray-600">{{ item.item_name }}</td>
															<td class="py-1 text-center text-gray-700">{{ item.qty }} {{ item.uom }}</td>
															<td class="py-1 text-end text-gray-600">{{ formatNumber(item.rate) }}</td>
															<td class="py-1 text-end text-gray-900 font-medium">{{ formatNumber(item.amount) }}</td>
														</tr>
													</tbody>
												</table>
											</div>
										</template>
									</td>
								</tr>
							</template>
						</tbody>
					</table>
				</div>

				<!-- Pagination -->
				<div class="bg-gray-50 border-t border-gray-200 px-4 py-3 flex items-center justify-between">
					<div class="text-sm text-gray-500">
						{{ __("Showing {0} to {1} of {2}", { 0: String(paginationStart), 1: String(paginationEnd), 2: String(filteredOrders.length) }) }}
					</div>
					<div class="flex items-center gap-2">
						<select v-model="perPage" class="px-2 py-1 border border-gray-300 rounded text-sm bg-white">
							<option :value="10">10</option>
							<option :value="20">20</option>
							<option :value="50">50</option>
							<option :value="100">100</option>
						</select>
						<button
							@click="currentPage = Math.max(1, currentPage - 1)"
							:disabled="currentPage <= 1"
							class="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{{ __("Prev") }}
						</button>
						<span class="text-sm text-gray-600">{{ currentPage }} / {{ totalPages }}</span>
						<button
							@click="currentPage = Math.min(totalPages, currentPage + 1)"
							:disabled="currentPage >= totalPages"
							class="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{{ __("Next") }}
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- Item Details Dialog -->
		<teleport to="body">
			<div v-if="showItemDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="showItemDialog = false">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
					<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">{{ selectedInvoiceName }}</h3>
						<button @click="showItemDialog = false" class="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<div class="p-6 overflow-auto max-h-[60vh]">
						<div v-if="dialogLoading" class="flex items-center justify-center py-8">
							<svg class="w-8 h-8 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
							</svg>
						</div>
						<table v-else class="w-full text-sm">
							<thead>
								<tr class="border-b border-gray-200">
									<th class="text-start py-2 text-xs font-semibold text-gray-600">{{ __("Item Code") }}</th>
									<th class="text-start py-2 text-xs font-semibold text-gray-600">{{ __("Item Name") }}</th>
									<th class="text-center py-2 text-xs font-semibold text-gray-600">{{ __("Qty") }}</th>
									<th class="text-end py-2 text-xs font-semibold text-gray-600">{{ __("Rate") }}</th>
									<th class="text-end py-2 text-xs font-semibold text-gray-600">{{ __("Amount") }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								<tr v-for="(item, idx) in dialogItems" :key="idx">
									<td class="py-2 text-gray-700">{{ item.item_code }}</td>
									<td class="py-2 text-gray-600">{{ item.item_name }}</td>
									<td class="py-2 text-center text-gray-700">{{ item.qty }} {{ item.uom }}</td>
									<td class="py-2 text-end text-gray-600">{{ formatNumber(item.rate) }}</td>
									<td class="py-2 text-end text-gray-900 font-medium">{{ formatNumber(item.amount) }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- Payment Dialog -->
			<div v-if="showPaymentDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="closePaymentDialog">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
					<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">
							{{ __("Payment Outstanding") }}: {{ formatNumber(paymentOutstanding) }}
						</h3>
						<button @click="closePaymentDialog" class="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<div class="p-6 space-y-4">
						<div v-for="(method, idx) in paymentMethods" :key="idx" class="space-y-3">
							<div class="flex items-center gap-3">
								<label class="text-sm font-medium text-gray-700 w-40 flex-shrink-0">{{ method.mode_of_payment }}</label>
								<input
									v-model.number="method.amount"
									type="number"
									step="0.01"
									min="0"
									class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
								/>
							</div>
						</div>
						<!-- Extra Fields Section -->
						<div class="pt-4 mt-4 border-t border-gray-100 space-y-4">
							<!-- Receipt Number (Visible if any payment mode is of type Visa) -->
							<div v-if="paymentMethods.some(m => m.custom_required_receipt  && m.amount > 0)" class="flex items-center gap-3">
								<label class="text-sm font-medium text-gray-700 w-40 flex-shrink-0">
									{{ __("Receipt Number") }} <span class="text-red-500">*</span>
								</label>
								<input
									v-model="receiptNumber"
									type="text"
									class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
									:placeholder="__('Enter Receipt Number')"
								/>
							</div>
							
							<!-- Talabat Fields (Visible if order type is Talabat) -->
							<template v-if="selectedInvoiceToPayType === 'Talabat'">
								<div class="flex items-center gap-3">
									<label class="text-sm font-medium text-gray-700 w-40 flex-shrink-0">{{ __("Unique Number") }}</label>
									<input
										v-model="uniqueNumber"
										type="text"
										class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
										:placeholder="__('Unique Talabat Number')"
									/>
								</div>
								<div class="flex items-center gap-3">
									<label class="text-sm font-medium text-gray-700 w-40 flex-shrink-0">{{ __("Reference Number") }} <span class="text-red-500">*</span></label>
									<input
										v-model="referenceNumber"
										type="text"
										class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
										:placeholder="__('Third Party Referance Number')"
									/>
								</div>
							</template>
						</div>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
						<button @click="closePaymentDialog" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
							{{ __("Cancel") }}
						</button>
						<button @click="submitPayment" :disabled="isSubmitting" class="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50">
							{{ isSubmitting ? __("Processing...") : __("Confirm") }}
						</button>
					</div>
				</div>
			</div>

			<!-- Password Confirmation Dialog -->
			<div v-if="showPasswordDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="cancelDelete">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
					<div class="px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">{{ __("Confirm Password") }}</h3>
					</div>
					<div class="p-6">
						<div class="relative">
							<svg class="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2zM7 9h2v6H7V9zm4 0h2v6h-2V9zm4 0h2v6h-2V9z" />
							</svg>
							<input
								ref="passwordInputRef"
								v-model="passwordInput"
								type="password"
								autocomplete="off"
								:placeholder="__('Enter Password or Scan Barcode')"
								class="w-full ps-10 pe-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
								@keyup.enter="confirmDelete"
							/>
						</div>
						<p v-if="passwordError" class="mt-2 text-sm text-red-600">{{ passwordError }}</p>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
						<button @click="cancelDelete" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
							{{ __("Cancel") }}
						</button>
						<button @click="confirmDelete" class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700">
							{{ __("Confirm") }}
						</button>
					</div>
				</div>
			</div>

			<!-- Wastage Question Dialog -->
			<div v-if="showWastageQuestion" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="cancelWastageQuestion">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
					<div class="px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">{{ __("Order Cancellation") }}</h3>
					</div>
					<div class="p-6">
						<p class="text-sm text-gray-700">{{ __("Is this order a wastage?") }}</p>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
						<button @click="cancelWastageQuestion" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
							{{ __("Cancel") }}
						</button>
						<button @click="handleNotWastage" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
							{{ __("No") }}
						</button>
						<button @click="handleWastage" class="px-4 py-2 text-sm font-medium text-white bg-amber-500 rounded-lg hover:bg-amber-600">
							{{ __("Yes, Wastage") }}
						</button>
					</div>
				</div>
			</div>

			<!-- Wastage Items Selection Dialog -->
			<div v-if="showWastageItems" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="cancelWastageItems">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
					<div class="px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">{{ __("Select Items for Stock Return") }}</h3>
					</div>
					<div class="p-6 overflow-auto max-h-[60vh] space-y-4">
						<!-- Stock Entry Type Selection -->
						<div class="flex items-center gap-6 pb-2">
							<label class="flex items-center gap-2 text-sm cursor-pointer group">
								<input type="radio" v-model="wastageStockEntryType" value="Consumptions" class="w-4 h-4 text-amber-600 focus:ring-amber-500 border-gray-300" />
								<span class="text-gray-700 group-hover:text-gray-900 transition-colors font-medium">{{ __("Consumptions") }}</span>
							</label>
							<label class="flex items-center gap-2 text-sm cursor-pointer group">
								<input type="radio" v-model="wastageStockEntryType" value="Loaded" class="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300" />
								<span class="text-gray-700 group-hover:text-gray-900 transition-colors font-medium">{{ __("Loaded") }}</span>
							</label>
						</div>

						<!-- Employee selector for Loaded type -->
						<div v-if="wastageStockEntryType === 'Loaded'" class="space-y-2 pb-2">
							<label class="block text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Select Employee") }} <span class="text-red-500">*</span></label>
							<div class="relative">
								<input
									v-model="employeeSearch"
									type="text"
									:placeholder="__('Search employee by ID or name...')"
									class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
									@input="searchEmployees"
								/>
								<div v-if="employees.length" class="absolute z-[60] left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-xl max-h-48 overflow-auto">
									<button
										v-for="emp in employees"
										:key="emp.name"
										@click="selectedEmployee = emp.name; employeeSearch = emp.employee_name; employees = []"
										class="w-full text-start px-3 py-2 text-sm hover:bg-blue-50 border-b border-gray-50 last:border-0 transition-colors"
									>
										<span class="font-medium text-gray-900">{{ emp.employee_name }}</span>
										<span class="text-xs text-gray-400 ms-2">{{ emp.name }}</span>
									</button>
								</div>
							</div>
						</div>

						<p class="text-sm text-gray-600">{{ __("Select items to return to stock. Unselected items will be marked as wastage.") }}</p>
						<!-- Items table -->
						<table class="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
							<thead class="bg-gray-50">
								<tr>
									<th class="px-3 py-2 text-start text-xs font-semibold text-gray-600">
										<input type="checkbox" @change="toggleAllWastageItems($event)" class="rounded" />
									</th>
									<th class="px-3 py-2 text-start text-xs font-semibold text-gray-600">{{ __("Item Code") }}</th>
									<th class="px-3 py-2 text-start text-xs font-semibold text-gray-600">{{ __("Item Name") }}</th>
									<th class="px-3 py-2 text-center text-xs font-semibold text-gray-600">{{ __("Original Qty") }}</th>
									<th class="px-3 py-2 text-center text-xs font-semibold text-gray-600">{{ __("Return Qty") }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								<tr v-for="(item, idx) in wastageItems" :key="idx">
									<td class="px-3 py-2">
										<input type="checkbox" v-model="item.selected" class="rounded" />
									</td>
									<td class="px-3 py-2 text-gray-700">{{ item.item_code }}</td>
									<td class="px-3 py-2 text-gray-600">{{ item.item_name }}</td>
									<td class="px-3 py-2 text-center text-gray-700">{{ item.original_qty }}</td>
									<td class="px-3 py-2 text-center">
										<input
											v-model.number="item.return_qty"
											type="number"
											:max="item.original_qty"
											:min="0"
											class="w-20 px-2 py-1 border border-gray-300 rounded text-sm text-center focus:ring-2 focus:ring-blue-500 outline-none"
										/>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
						<button @click="cancelWastageItems" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
							{{ __("Cancel") }}
						</button>
						<button 
							@click="confirmWastageItems" 
							:disabled="wastageStockEntryType === 'Loaded' && !selectedEmployee"
							class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{{ __("Confirm") }}
						</button>
					</div>
				</div>
			</div>

			<!-- Assign Driver Dialog -->
			<div v-if="showDriverDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="closeDriverDialog">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
					<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">
							{{ __("Assign Driver") }}
						</h3>
						<button @click="closeDriverDialog" class="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<div class="p-6 space-y-4">
						<div class="text-sm text-gray-600">
							{{ __("Order") }}: <span class="font-medium text-gray-900">{{ driverDialogInvoiceName }}</span>
						</div>
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Driver") }}</label>
							<select v-model="driverDialogSelected" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white">
								<option value="">{{ __("-- No Driver --") }}</option>
								<option v-for="d in activeDrivers" :key="d.name" :value="d.name">{{ d.full_name || d.name }}</option>
							</select>
						</div>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
						<button @click="closeDriverDialog" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
							{{ __("Cancel") }}
						</button>
						<button @click="confirmAssignDriver" :disabled="driverAssigning" class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50">
							{{ driverAssigning ? __("Saving...") : __("Assign") }}
						</button>
					</div>
				</div>
			</div>
		</teleport>

		<!-- Add/Edit Second Mobile Dialog -->
		<teleport to="body">
			<div v-if="showMobileDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="closeMobileDialog">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
					<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">
							{{ __("Second Mobile Number") }}
						</h3>
						<button @click="closeMobileDialog" class="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<div class="p-6 space-y-4">
						<div class="text-sm text-gray-600">
							{{ __("Customer") }}: <span class="font-medium text-gray-900">{{ mobileDialogCustomerName }}</span>
						</div>
						<div>
							<label class="block text-xs font-medium text-gray-600 mb-1">{{ __("Second Mobile Number") }}</label>
							<input v-model="mobileDialogValue" type="tel" dir="ltr" :placeholder="__('e.g. 01000000000')" @keyup.enter="confirmMobile" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-white" />
						</div>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
						<button @click="closeMobileDialog" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
							{{ __("Cancel") }}
						</button>
						<button @click="confirmMobile" :disabled="mobileSaving" class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50">
							{{ mobileSaving ? __("Saving...") : __("Save") }}
						</button>
					</div>
				</div>
			</div>
		</teleport>

		<!-- Return to Need My Action Dialog (Call Center) -->
		<teleport to="body">
			<div v-if="showReturnDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="closeReturnDialog">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
					<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
						<div>
							<h3 class="text-lg font-semibold text-gray-900">{{ __("Return to Need My Action") }}</h3>
							<p v-if="returnOrder" class="text-xs text-gray-500 mt-0.5">{{ returnOrder.custom_number_order || returnOrder.name }}</p>
						</div>
						<button @click="closeReturnDialog" class="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<div class="p-6 space-y-4">
						<!-- Rejection reason -->
						<div v-if="returnOrder?.custom_rejection_reason" class="p-3 bg-red-50 rounded-lg border border-red-100">
							<div class="text-xs font-bold text-red-600 uppercase tracking-wider mb-0.5">{{ __("Rejection Reason") }}</div>
							<div class="text-sm text-red-800">{{ returnOrder.custom_rejection_reason }}</div>
						</div>
						<div v-else class="text-xs text-gray-400 italic">{{ __("No rejection reason recorded.") }}</div>

						<!-- Payment type -->
						<div>
							<label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{{ __("Payment Type") }}</label>
							<select v-model="returnPaymentType" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none bg-white">
								<option :value="null">{{ __("Select Payment Type") }}</option>
								<option value="Cash on delivery">{{ __("Cash on delivery") }}</option>
								<option value="Credit Card">{{ __("Credit Card") }}</option>
								<option value="Cash Talabat">{{ __("Cash Talabat") }}</option>
								<option value="Credit Card on delivary">{{ __("Credit Card on delivary") }}</option>
								<option value="Cash">{{ __("Cash") }}</option>
							</select>
						</div>

						<!-- Receipt number -->
						<div>
							<label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{{ __("Receipt Number") }}</label>
							<input v-model="returnReceiptNumber" type="text" :placeholder="__('Enter receipt number')" @keyup.enter="confirmReturnToNeedMyAction" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none bg-white" />
						</div>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
						<button @click="closeReturnDialog" :disabled="returnSubmitting" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50">{{ __("Cancel") }}</button>
						<button @click="confirmReturnToNeedMyAction" :disabled="returnSubmitting" class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors disabled:opacity-50">
							<svg v-if="returnSubmitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
							{{ __("Return to Need My Action") }}
						</button>
					</div>
				</div>
			</div>
		</teleport>

		<!-- Order Number Limit Settings Dialog -->
		<teleport to="body">
			<div v-if="limitDialog.show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
				<div class="bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 overflow-hidden">
					<div class="px-6 py-5 border-b border-gray-100 flex items-center gap-3">
						<div class="w-9 h-9 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
							<svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
							</svg>
						</div>
						<div>
							<h3 class="text-base font-bold text-gray-900">{{ __("Order Number Limit") }}</h3>
							<p class="text-xs text-gray-500 mt-0.5">{{ limitDialog.posProfileName }}</p>
						</div>
					</div>
					<div class="px-6 py-5 space-y-3">
						<p class="text-sm text-gray-600">{{ __("Order numbers cycle back to 1 after reaching this limit. Set 0 to disable cycling.") }}</p>
						<div>
							<label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{{ __("Limit") }}</label>
							<input
								v-model.number="limitDialog.value"
								type="number"
								min="0"
								step="1"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
								:placeholder="__('e.g. 50  (0 = no limit)')"
							/>
						</div>
					</div>
					<div class="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-3 bg-gray-50">
						<button @click="limitDialog.show = false" :disabled="limitDialog.saving" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg transition-colors disabled:opacity-50">
							{{ __("Cancel") }}
						</button>
						<button @click="saveLimitSettings" :disabled="limitDialog.saving" class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50">
							<svg v-if="limitDialog.saving" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
							{{ __("Save") }}
						</button>
					</div>
				</div>
			</div>
		</teleport>

		<!-- Return dialog reused from the sale screen (opened after manager approval) -->
		<ReturnInvoiceDialog
			v-model="showReturnInvoiceDialog"
			:pos-profile="shiftStore.profileName || posProfile?.name || posProfile"
			:pos-opening-shift="shiftStore.currentShift?.name || posOpeningShift?.name || posOpeningShift"
			:currency="returnTarget?.currency || shiftStore.profileCurrency"
			:preselected-invoice="returnPreselected"
			return-source="User"
			@return-created="handleReturnInvoiceCreated"
		/>
	</div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from "vue"
import { useRouter } from "vue-router"
import { call } from "@/utils/apiWrapper"
import { __ } from "@/utils/translation"
import { useBootstrapStore } from "@/stores/bootstrap"
import { useRealtimeOrders } from "@/composables/useRealtimeOrders"
import { initSocket } from "@/socket"
import { usePOSCartStore } from "@/stores/posCart"
import { usePOSShiftStore } from "@/stores/posShift"
import ReturnInvoiceDialog from "@/components/sale/ReturnInvoiceDialog.vue"

const router = useRouter()
const cartStore = usePOSCartStore()
const shiftStore = usePOSShiftStore()

// ── System Manager check (for showing limit settings button) ─────────────────
const isSystemManager = ref(false)
if (window.frappe?.user?.has_role) {
	isSystemManager.value = window.frappe.user.has_role("System Manager")
} else {
	// Fallback: check session roles
	const roles = window.frappe?.boot?.user?.roles || []
	isSystemManager.value = roles.includes("System Manager")
}

// ── Order Number Limit dialog ────────────────────────────────────────────────
const orderNumberLimit = ref(0)
const limitDialog = ref({ show: false, value: 0, saving: false, posProfileName: "" })

function openLimitSettings() {
	limitDialog.value = {
		show: true,
		value: orderNumberLimit.value,
		saving: false,
		posProfileName: posProfile.value?.name || posProfile.value || "",
	}
}

async function saveLimitSettings() {
	limitDialog.value.saving = true
	try {
		const profileName = posProfile.value?.name || posProfile.value
		const result = await call("ecs_posnext.api.invoices.update_order_number_limit", {
			pos_profile: profileName,
			limit: limitDialog.value.value,
		})
		orderNumberLimit.value = result.limit
		limitDialog.value.show = false
		window.frappe?.show_alert?.({ message: __("Order Number Limit saved"), indicator: "green" })
	} catch (error) {
		window.frappe?.show_alert?.({ message: __("Failed to save limit"), indicator: "red" })
	} finally {
		limitDialog.value.saving = false
	}
}

// ── Edit Draft Order ─────────────────────────────────────────────────────────
const editLoading = ref(null)

async function editOrder(order) {
	editLoading.value = order.name
	try {
		const fullInvoice = await call("ecs_posnext.api.invoices.get_invoice", {
			invoice_name: order.name,
		})
		if (fullInvoice) {
			if (order.docstatus === 1) {
				// Submitted order: start a fresh cart that will produce a suffixed order number
				cartStore.beginSupplement(fullInvoice)
			} else {
				// Draft order: load existing items for direct editing
				await cartStore.resumeInvoice(fullInvoice)
			}
			// Ensure cart store has correct POS Profile context AFTER beginSupplement/resumeInvoice
			// (beginSupplement calls clearCart which may affect state)
			if (!cartStore.posProfile) {
				cartStore.posProfile = shiftStore.profileName || fullInvoice.pos_profile
				cartStore.posOpeningShift = shiftStore.currentShift?.name || fullInvoice.posa_pos_opening_shift
			}
			router.push({ name: "POSSale" })
		} else {
			window.frappe?.show_alert?.({ message: __("Could not load order details"), indicator: "red" })
		}
	} catch (error) {
		console.error("Failed to load order for editing:", error)
		window.frappe?.show_alert?.({ message: __("Failed to open order for editing"), indicator: "red" })
	} finally {
		editLoading.value = null
	}
}

// State
const orders = ref([])
const loading = ref(false)
const configLoading = ref(true)
const canSelectDates = ref(false)
// True once the user manually edits the date range — then search stays inside that range.
const dateRangeTouched = ref(false)
// Max past days the user may browse (0 = unlimited). Constrains the date pickers.
const maxDays = ref(0)
const todayStr = new Date().toISOString().slice(0, 10)
// Earliest date the user is allowed to pick (today − maxDays); empty when unlimited.
const minAllowedDate = computed(() => {
	if (!maxDays.value || maxDays.value <= 0) return ""
	const d = new Date()
	d.setDate(d.getDate() - maxDays.value)
	return d.toISOString().slice(0, 10)
})
const shiftStart = ref("")
const shiftEnd = ref("")
const search = ref("")
const showFilters = ref(true)
const expanded = ref({})
const currentPage = ref(1)
const perPage = ref(50)
const sortField = ref("posting_date")
const sortDir = ref("desc")

// Dialog state — Item details
const showItemDialog = ref(false)
const dialogLoading = ref(false)
const dialogItems = ref([])
const selectedInvoiceName = ref("")

// POS Profile & Opening Shift (needed for payment methods)
const posProfile = ref(null)
const posOpeningShift = ref(null)

// Call Center users convert between Pickup and Delivery.
// Cashier / non-Call-Center users convert between Dine In and Takeaway (Pickup).
const isCallCenter = computed(() => {
	const name = posProfile.value?.name || posProfile.value
	return typeof name === "string" && name.trim() === "Call Center"
})

// Payment dialog state
const showPaymentDialog = ref(false)
const paymentMethods = ref([])
const paymentOutstanding = ref(0)
const selectedInvoiceToPay = ref(null)
const selectedInvoiceToPayType = ref(null)
const receiptNumber = ref("")
const uniqueNumber = ref("")
const referenceNumber = ref("")
const isSubmitting = ref(false)

// Password / Cancel dialog state
const showPasswordDialog = ref(false)
const passwordInput = ref("")
const passwordError = ref("")
const orderToDelete = ref(null)
const approvedManager = ref(null)
const passwordInputRef = ref(null)

// Return dialog (reused from the sale screen) + the created return we run wastage against
const showReturnInvoiceDialog = ref(false)
const returnPreselected = ref(null)   // { name } passed to ReturnInvoiceDialog
const returnTarget = ref(null)        // the original order row (for currency)
const wastageTargetInvoice = ref(null) // the created RETURN invoice name

// Wastage dialog state
const showWastageQuestion = ref(false)
const showWastageItems = ref(false)
const wastageItems = ref([])
const wastageStockEntryType = ref("Loaded")
const selectedEmployee = ref(null)
const employees = ref([])
const employeeSearch = ref("")

// Active drivers list (fetched from API)
const activeDrivers = ref([])

// Assign driver dialog state
const showDriverDialog = ref(false)
const driverDialogInvoiceName = ref("")
const driverDialogSelected = ref("")
const driverAssigning = ref(false)

// Return to Need My Action dialog (Call Center)
const showReturnDialog = ref(false)
const returnOrder = ref(null)
const returnPaymentType = ref(null)
const returnReceiptNumber = ref("")
const returnSubmitting = ref(false)

// Add/Edit customer second mobile number
const showMobileDialog = ref(false)
const mobileDialogCustomer = ref("")
const mobileDialogCustomerName = ref("")
const mobileDialogValue = ref("")
const mobileSaving = ref(false)

// Filters — date_from/date_to will be set by config
const filters = ref({
	invoice_name: "",
	customer: "",
	status: "",
	pos_source: "",
	date_from: "",
	date_to: "",
	order_type: "",
	invoice_type: "",
	branch: "",
	order_number: "",
	driver: "",
	unique_number: "",
})

// Derived options from data
const statusOptions = computed(() => {
	const set = new Set(orders.value.map(o => o.display_status).filter(Boolean))
	return Array.from(set).sort()
})

const posProfileOptions = computed(() => {
	const set = new Set(orders.value.map(o => o.pos_profile).filter(Boolean))
	return Array.from(set).sort()
})

const orderTypeOptions = computed(() => {
	const set = new Set(orders.value.map(o => o.custom_order_type).filter(Boolean))
	return Array.from(set).sort()
})

const branchOptions = computed(() => {
	const set = new Set(orders.value.map(o => o.branch).filter(Boolean))
	return Array.from(set).sort()
})

const driverOptions = computed(() => {
	return activeDrivers.value.map(d => d.name)
})

// Active filter count
const activeFilterCount = computed(() => {
	const f = filters.value
	let count = 0
	if (f.invoice_name) count++
	if (f.customer) count++
	if (f.status) count++
	if (f.pos_source) count++
	if (f.order_type) count++
	if (f.invoice_type) count++
	if (f.branch) count++
	if (f.date_from) count++
	if (f.date_to) count++
	if (f.order_number) count++
	if (f.driver) count++
	if (f.unique_number) count++
	return count
})

// ── Supplement grouping helpers ──────────────────────────────────────────────
function isSupplementOrder(orderNum) {
	if (!orderNum) return false
	// Supplements have 2+ hyphens: P-5-1, DI-3-2, etc.
	return (orderNum.split('-').length >= 3)
}

function getParentOrderNum(orderNum) {
	if (!isSupplementOrder(orderNum)) return null
	// P-5-1 → P-5, DI-3-2 → DI-3
	return orderNum.substring(0, orderNum.lastIndexOf('-'))
}

// Group supplements under their parent orders
const groupedOrders = computed(() => {
	const all = orders.value
	const parentMap = {} // parentOrderNum → parent order
	const result = []
	const supplementSet = new Set()

	// Reset any previously attached supplements (prevents duplicates on re-computation)
	for (const order of all) {
		order.supplements = []
		order._combined_total = undefined
		order._combined_outstanding = undefined
	}

	// First pass: identify parents
	for (const order of all) {
		const num = order.custom_number_order
		if (num && !isSupplementOrder(num)) {
			parentMap[num] = order
		}
	}

	// Second pass: attach supplements to parents
	for (const order of all) {
		const num = order.custom_number_order
		if (num && isSupplementOrder(num)) {
			const parentNum = getParentOrderNum(num)
			const parent = parentMap[parentNum]
			if (parent) {
				if (!parent.supplements) parent.supplements = []
				parent.supplements.push(order)
				// Add supplement totals to parent
				if (parent._combined_total === undefined) {
					parent._combined_total = parseFloat(parent.grand_total || 0)
					parent._combined_outstanding = parseFloat(parent.outstanding_amount || 0)
				}
				parent._combined_total += parseFloat(order.grand_total || 0)
				parent._combined_outstanding += parseFloat(order.outstanding_amount || 0)
				supplementSet.add(order.name)
			}
		}
	}

	// Build result: exclude supplements that were attached to a parent
	for (const order of all) {
		if (!supplementSet.has(order.name)) {
			result.push(order)
		}
	}

	return result
})

// Filtered orders
const filteredOrders = computed(() => {
	let data = groupedOrders.value.slice()
	const f = filters.value
	const ci = (v) => (v ?? "").toString().toLowerCase()
	const has = (val, needle) => ci(val).includes(ci(needle))

	if (search.value) {
		const s = search.value.toLowerCase()
		data = data.filter(o =>
			ci(o.name).includes(s) ||
			ci(o.customer_name).includes(s) ||
			ci(o.customer).includes(s) ||
			ci(o.mobile_no).includes(s) ||
			ci(o.other_mobile_no).includes(s) ||
			ci(o.pos_profile).includes(s) ||
			ci(o.branch).includes(s) ||
			ci(o.custom_number_order).includes(s) ||
			ci(o.driver).includes(s) ||
			ci(o.custom_unique_talbat_number).includes(s)
		)
	}

	if (f.invoice_name) data = data.filter(o => has(o.name, f.invoice_name))
	if (f.customer) data = data.filter(o =>
		has(o.customer_name, f.customer) ||
		has(o.customer, f.customer) ||
		has(o.mobile_no, f.customer) ||
		has(o.other_mobile_no, f.customer)
	)
	if (f.status) data = data.filter(o => o.display_status === f.status)
	if (f.pos_source === "call_center") data = data.filter(o => o.pos_profile === "Call Center")
	else if (f.pos_source === "cashier") data = data.filter(o => o.pos_profile !== "Call Center")
	if (f.branch) data = data.filter(o => o.branch === f.branch)
	if (f.order_type) data = data.filter(o => o.custom_order_type === f.order_type)
	if (f.invoice_type === "return") data = data.filter(o => o.is_return)
	if (f.invoice_type === "regular") data = data.filter(o => !o.is_return)
	if (f.order_number) data = data.filter(o => has(o.custom_number_order, f.order_number) || has(o.name, f.order_number))
	if (f.driver) data = data.filter(o => o.driver === f.driver)
	if (f.unique_number) data = data.filter(o => has(o.custom_unique_talbat_number, f.unique_number))

	// Sort
	data.sort((a, b) => {
		let valA = a[sortField.value]
		let valB = b[sortField.value]
		if (typeof valA === "string") valA = valA.toLowerCase()
		if (typeof valB === "string") valB = valB.toLowerCase()
		if (valA < valB) return sortDir.value === "asc" ? -1 : 1
		if (valA > valB) return sortDir.value === "asc" ? 1 : -1
		return 0
	})

	return data
})

// Pagination
const totalPages = computed(() => Math.max(1, Math.ceil(filteredOrders.value.length / perPage.value)))
const paginationStart = computed(() => Math.min((currentPage.value - 1) * perPage.value + 1, filteredOrders.value.length))
const paginationEnd = computed(() => Math.min(currentPage.value * perPage.value, filteredOrders.value.length))
const paginatedOrders = computed(() => {
	const start = (currentPage.value - 1) * perPage.value
	return filteredOrders.value.slice(start, start + perPage.value)
})

// Reset page on filter change
watch([search, filters, perPage], () => {
	currentPage.value = 1
}, { deep: true })

// Autofocus password input when dialog opens
watch(showPasswordDialog, (val) => {
	if (val) {
		nextTick(() => {
			passwordInputRef.value?.focus()
		})
	}
})

// Methods
function sortBy(field) {
	if (sortField.value === field) {
		sortDir.value = sortDir.value === "asc" ? "desc" : "asc"
	} else {
		sortField.value = field
		sortDir.value = "desc"
	}
}

function toggleExpand(name) {
	expanded.value[name] = !expanded.value[name]
}

function resetFilters() {
	dateRangeTouched.value = false
	const keepFrom = canSelectDates.value ? "" : filters.value.date_from
	const keepTo = canSelectDates.value ? "" : filters.value.date_to
	filters.value = {
		invoice_name: "",
		customer: "",
		status: "",
		pos_source: "",
		date_from: keepFrom,
		date_to: keepTo,
		order_type: "",
		invoice_type: "",
		branch: "",
		order_number: "",
		driver: "",
		unique_number: "",
	}
}

async function loadConfig() {
	configLoading.value = true
	try {
		const config = await call("ecs_posnext.api.invoices.get_all_orders_config", {})
		canSelectDates.value = config.can_select_dates || false
		maxDays.value = config.days || 0
		filters.value.date_from = config.date_from || ""
		filters.value.date_to = config.date_to || ""
		shiftStart.value = config.shift_start || ""
		shiftEnd.value = config.shift_end || ""
		orderNumberLimit.value = config.order_number_limit || 0
	} catch (error) {
		console.error("Failed to load All Orders config:", error)
		// Fallback to today
		const today = new Date().toISOString().slice(0, 10)
		filters.value.date_from = today
		filters.value.date_to = today
		canSelectDates.value = false
	} finally {
		configLoading.value = false
	}
}

// Changing the date range reloads immediately (so it's not "nothing happened" until Refresh).
function onDateRangeChange() {
	dateRangeTouched.value = true
	currentPage.value = 1
	fetchOrders()
}

async function fetchOrders() {
	loading.value = true
	try {
		// A search term makes the backend look across the user's full allowed range
		// (not just the loaded window), so older orders for a customer number are found.
		const term = (search.value || filters.value.customer || "").trim()
		const result = await call("ecs_posnext.api.invoices.get_all_orders", {
			date_from: filters.value.date_from || null,
			date_to: filters.value.date_to || null,
			limit: term ? 2000 : 500,
			search: term || null,
			// When the user has picked a date range, keep the search inside it.
			respect_dates: dateRangeTouched.value ? 1 : 0,
		})
		orders.value = result || []
	} catch (error) {
		console.error("Failed to fetch orders:", error)
		orders.value = []
	} finally {
		loading.value = false
	}
}

// Debounced server-side search — refetch across the allowed range as the user types a
// customer number / name / order #, so results aren't limited to the loaded window.
let _searchTimer = null
watch([search, () => filters.value.customer], () => {
	if (_searchTimer) clearTimeout(_searchTimer)
	_searchTimer = setTimeout(() => fetchOrders(), 400)
})

function viewInvoice(name) {
	// Open in new tab in Frappe desk
	window.open(`/app/sales-invoice/${name}`, "_blank")
}

function printInvoice(name) {
	window.open(
		`/printview?doctype=Sales Invoice&name=${name}&trigger_print=1&format=print format sales&no_letterhead=0`,
		"_blank"
	)
}

function printKitchen(name) {
	window.open(
		`/printview?doctype=Sales Invoice&name=${name}&trigger_print=1&format=Kitchen%20Receipt&no_letterhead=0`,
		"_blank"
	)
}

// ===== PAY OUTSTANDING =====
async function payOrder(order) {
	selectedInvoiceToPay.value = order.name
	selectedInvoiceToPayType.value = order.custom_order_type
	paymentOutstanding.value = parseFloat(order.outstanding_amount || 0)

	// Pre-fill fields if they exist
	receiptNumber.value = order.custom_receipt_number || ""
	uniqueNumber.value = order.custom_unique_talbat_number || ""
	referenceNumber.value = order.custom_third_party_referance_number || ""

	// Make sure the cashier's POS Profile is resolved before building the
	// payment method list, otherwise we fall back to a generic "Cash".
	if (!(posProfile.value?.name || posProfile.value)) {
		await loadPosProfile()
	}

	await setupPaymentMethods()
	showPaymentDialog.value = true
}

async function setupPaymentMethods() {
	// Fast path: payment methods already preloaded by the main POS bootstrap.
	const bootstrapStore = useBootstrapStore()
	const methods = bootstrapStore.getPreloadedPaymentMethods()
	if (methods && methods.length > 0) {
		paymentMethods.value = methods.map(m => ({
			mode_of_payment: m.mode_of_payment,
			type: m.type,
			custom_required_receipt: m.custom_required_receipt,
			amount: 0,
		}))
		return
	}

	// This page does not run the POS bootstrap, so fetch the real payment
	// methods for the current cashier's POS Profile (money follows the
	// cashier's shift). Never hardcode "Cash" — profiles use per-branch
	// modes like "Cash Smouha".
	const profileName = posProfile.value?.name || posProfile.value
	if (profileName) {
		try {
			const fetched = await call("ecs_posnext.api.pos_profile.get_payment_methods", {
				pos_profile: profileName,
			})
			if (fetched && fetched.length > 0) {
				paymentMethods.value = fetched.map(m => ({
					mode_of_payment: m.mode_of_payment,
					type: m.type,
					custom_required_receipt: m.custom_required_receipt,
					amount: 0,
				}))
				return
			}
		} catch (error) {
			console.error("Failed to load payment methods for", profileName, error)
		}
	}

	// Last-resort fallback only if the profile could not be resolved.
	paymentMethods.value = [{ mode_of_payment: "Cash", amount: 0 }]
}

function closePaymentDialog() {
	showPaymentDialog.value = false
	selectedInvoiceToPay.value = null
	paymentOutstanding.value = 0
	paymentMethods.value.forEach(m => { m.amount = 0 })
}

async function submitPayment() {
	if (isSubmitting.value) return
	isSubmitting.value = true
	try {
		const totalPaid = paymentMethods.value.reduce((sum, m) => sum + (parseFloat(m.amount) || 0), 0)
		if (totalPaid <= 0) {
			window.frappe?.show_alert?.({ message: __("Please enter a payment amount"), indicator: "orange" })
			return
		}

		// Validation: Receipt Number is mandatory if any payment mode requires it
		const needsReceipt = paymentMethods.value.some(m => m.custom_required_receipt && (parseFloat(m.amount) || 0) > 0)
		if (needsReceipt && !receiptNumber.value) {
			window.frappe?.show_alert?.({ message: __("Receipt Number is mandatory"), indicator: "orange" })
			return
		}

		if (selectedInvoiceToPayType.value === "Talabat" && !referenceNumber.value) {
			window.frappe?.show_alert?.({ message: __("Third Party Reference Number is mandatory for Talabat orders"), indicator: "orange" })
			return
		}

		if (totalPaid > paymentOutstanding.value) {
			window.frappe?.show_alert?.({ message: __("Total payment exceeds outstanding amount"), indicator: "orange" })
			return
		}
		const payments = paymentMethods.value
			.filter(m => (parseFloat(m.amount) || 0) > 0)
			.map(m => ({ mode_of_payment: m.mode_of_payment, amount: parseFloat(m.amount) }))

		await call("ecs_posnext.api.partial_payments.add_payment_to_partial_invoice", {
			invoice_name: selectedInvoiceToPay.value,
			payments: JSON.stringify(payments),
			receipt_number: receiptNumber.value,
			unique_number: uniqueNumber.value,
			reference_number: referenceNumber.value,
		})
		window.frappe?.show_alert?.({ message: __("Payment successful"), indicator: "green" })
		closePaymentDialog()
		fetchOrders()
	} catch (error) {
		console.error("Payment failed:", error)
		window.frappe?.show_alert?.({ message: __("Payment failed"), indicator: "red" })
	} finally {
		isSubmitting.value = false
	}
}

// ===== DELETE / CANCEL ORDER =====
function deleteOrder(order) {
	// Ask for the manager password BEFORE opening the return dialog. On success
	// confirmDelete() opens the ReturnInvoiceDialog preselected to this order.
	orderToDelete.value = order
	approvedManager.value = null
	passwordInput.value = ""
	passwordError.value = ""
	showPasswordDialog.value = true
}

async function confirmDelete() {
	passwordError.value = ""
	try {
		const res = await call("ecs_posnext.api.kitchen_order.verify_cancel_manager", {
			pos_profile: posProfile.value?.name || posProfile.value || "",
			password: passwordInput.value,
		})
		if (res && res.valid) {
			approvedManager.value = res.manager || null
			showPasswordDialog.value = false
			// Manager approved → open the rich ReturnInvoiceDialog, preselected to this
			// order. It creates a forward credit-note return on the current open shift.
			returnTarget.value = orderToDelete.value
			returnPreselected.value = { name: orderToDelete.value?.name }
			showReturnInvoiceDialog.value = true
		} else {
			passwordError.value = __("Password is incorrect. Please try again.")
		}
	} catch (error) {
		console.error("Manager verification failed:", error)
		passwordError.value = __("Password is incorrect. Please try again.")
	}
}

// The return dialog created a credit-note return. Offer the wastage step on the
// items that were actually returned (so wasted food is consumed out of stock).
function handleReturnInvoiceCreated(returnInvoice) {
	wastageTargetInvoice.value = returnInvoice?.name || null
	showReturnInvoiceDialog.value = false
	if (wastageTargetInvoice.value) {
		showWastageQuestion.value = true
	} else {
		fetchOrders()
	}
}

function cancelDelete() {
	showPasswordDialog.value = false
	passwordInput.value = ""
	passwordError.value = ""
	orderToDelete.value = null
}

// ===== WASTAGE FLOW =====
function cancelWastageQuestion() {
	showWastageQuestion.value = false
	orderToDelete.value = null
}

function handleNotWastage() {
	showWastageQuestion.value = false
	// Return already created by the dialog; nothing to waste.
	orderToDelete.value = null
	wastageTargetInvoice.value = null
	fetchOrders()
}

async function handleWastage() {
	showWastageQuestion.value = false
	await loadOrderItemsForWastage()
}

async function loadOrderItemsForWastage() {
	try {
		const result = await call("ecs_posnext.api.kitchen_order.get_stock_items_for_wastage", {
			sales_invoice: wastageTargetInvoice.value,
		})
		const items = result || []
		wastageItems.value = items.map(i => ({
			item_code: i.item_code || "",
			item_name: i.item_name || i.item_code || "",
			qty: i.qty || 0,
			original_qty: i.original_qty || i.qty || 0,
			return_qty: i.qty || 0,
			uom: i.uom || "Nos",
			warehouse: i.warehouse || "",
			selected: false,
		}))
		wastageStockEntryType.value = "Consumptions"
		selectedEmployee.value = null
		showWastageItems.value = true
	} catch (error) {
		console.error("Failed to load wastage items:", error)
		window.frappe?.show_alert?.({ message: __("Failed to load items for wastage"), indicator: "red" })
	}
}

function cancelWastageItems() {
	showWastageItems.value = false
	wastageItems.value = []
	orderToDelete.value = null
}

function toggleAllWastageItems(event) {
	const checked = event.target.checked
	wastageItems.value.forEach(item => { item.selected = checked })
}

async function confirmWastageItems() {
	const selectedItems = wastageItems.value.filter(i => i.selected)
	const selectedCodes = new Set(selectedItems.map(i => i.item_code))

	// Wastage items = items NOT selected for return
	const wastageItemsList = wastageItems.value
		.filter(item => !selectedCodes.has(item.item_code))
		.map(item => ({
			item_code: item.item_code,
			qty: item.qty,
			uom: item.uom,
			warehouse: item.warehouse,
		}))

	// Add partial wastage for selected items
	selectedItems.forEach(item => {
		const wastageQty = item.original_qty - (item.return_qty || 0)
		if (wastageQty > 0) {
			wastageItemsList.push({
				item_code: item.item_code,
				qty: wastageQty,
				uom: item.uom,
				warehouse: item.warehouse,
			})
		}
	})

	showWastageItems.value = false

	// The return already exists (created by ReturnInvoiceDialog). Now consume the
	// wasted items out of stock so they are not re-shelved.
	try {
		if (wastageItemsList.length && wastageTargetInvoice.value) {
			await call("ecs_posnext.api.kitchen_order.create_wastage_stock_entry_for_invoice", {
				sales_invoice: wastageTargetInvoice.value,
				wastage_items: JSON.stringify(wastageItemsList),
				stock_entry_type: wastageStockEntryType.value,
				employee: selectedEmployee.value,
				cancelled_by_manager: approvedManager.value,
			})
			window.frappe?.show_alert?.({ message: __("Wastage stock entry created."), indicator: "green" })
		}
		fetchOrders()
	} catch (error) {
		console.error("Wastage failed:", error)
		window.frappe?.show_alert?.({ message: __("Error creating wastage stock entry."), indicator: "red" })
	} finally {
		wastageItems.value = []
		orderToDelete.value = null
		wastageTargetInvoice.value = null
		approvedManager.value = null
		wastageStockEntryType.value = "Loaded"
		selectedEmployee.value = null
	}
}

async function proceedWithCancellation(isWastage, itemsToReturn = [], wastageItemsList = []) {
	try {
		// Forward-only reversal: create a Return / Credit Note on the CURRENT open
		// shift instead of cancelling the original sale, so the refund is owned by
		// today's cashier and the original invoice stays on the books.
		const shiftName = posOpeningShift.value?.name || shiftStore.currentShift?.name || null
		const res = await call("ecs_posnext.api.kitchen_order.return_sales_invoice_with_wastage", {
			sales_invoice: orderToDelete.value?.name,
			is_wastage: isWastage,
			items_to_return: JSON.stringify(itemsToReturn),
			wastage_items: JSON.stringify(wastageItemsList),
			stock_entry_type: wastageStockEntryType.value,
			employee: selectedEmployee.value,
			cancelled_by_manager: approvedManager.value,
			pos_opening_shift: shiftName,
		})

		let msg = __("Return created successfully.")
		if (res?.return_invoice) {
			msg = __("Return") + " " + res.return_invoice + " — " + __("refunded") + " " + res.refunded_amount
		}
		if (isWastage && wastageItemsList.length > 0) {
			msg += " " + __("Stock entry created for wastage items.")
		}
		window.frappe?.msgprint?.(msg)
		fetchOrders()
	} catch (error) {
		console.error("Return failed:", error)
		window.frappe?.show_alert?.({ message: __("Error creating return."), indicator: "red" })
	} finally {
		wastageItems.value = []
		orderToDelete.value = null
		approvedManager.value = null
		wastageStockEntryType.value = "Consumptions"
		selectedEmployee.value = null
	}
}


// ===== EMPLOYEE SEARCH (for wastage Loaded type) =====
async function searchEmployees() {
	if (!employeeSearch.value || employeeSearch.value.length < 2) {
		employees.value = []
		return
	}
	try {
		const result = await call("frappe.desk.search.search_link", {
			txt: employeeSearch.value,
			doctype: "Employee",
			ignore_user_permissions: 0,
			reference_doctype: "Sales Invoice",
			filters: JSON.stringify({ status: "Active" }),
			page_length: 20,
		})
		// search_link returns list of { value, description }
		employees.value = (result || []).map(r => ({
			name: r.value,
			employee_name: r.description || r.value
		}))
	} catch (e) {
		employees.value = []
	}
}

// ===== LOAD POS PROFILE & OPENING SHIFT =====
async function loadPosProfile() {
	try {
		const result = await call("ecs_posnext.api.shifts.check_opening_shift", {
			user: window.frappe?.session?.user || "",
		})
		if (result && result.pos_profile) {
			posProfile.value = result.pos_profile
			posOpeningShift.value = result.pos_opening_shift
		}
	} catch (error) {
		console.error("Failed to load POS Profile:", error)
	}
}

function getStatusClasses(status) {
	switch (status) {
		case "Paid":
			return "bg-green-100 text-green-800"
		case "Unpaid":
			return "bg-red-100 text-red-800"
		case "Return":
			return "bg-purple-100 text-purple-800"
		case "Draft":
			return "bg-yellow-100 text-yellow-800"
		case "Overdue":
			return "bg-orange-100 text-orange-800"
		case "Cancelled":
			return "bg-gray-100 text-gray-800"
		default:
			return "bg-blue-100 text-blue-800"
	}
}

function getKdsStatusClasses(status) {
	switch (status) {
		case "Pending":   return "bg-gray-100 text-gray-700"
		case "Preparing": return "bg-blue-100 text-blue-700"
		case "Ready":     return "bg-green-100 text-green-700"
		case "Completed": return "bg-emerald-100 text-emerald-700"
		case "Cancelled": return "bg-red-100 text-red-700"
		default:          return "bg-gray-100 text-gray-600"
	}
}

function getDeliveryStatusClasses(status) {
	switch (status) {
		case "Assigned":         return "bg-indigo-100 text-indigo-700"
		case "Picked Up":        return "bg-blue-100 text-blue-700"
		case "Out for Delivery": return "bg-amber-100 text-amber-700"
		case "Delivered":        return "bg-emerald-100 text-emerald-700"
		case "Returned":         return "bg-gray-200 text-gray-700"
		case "Failed":           return "bg-red-100 text-red-700"
		default:                 return "bg-gray-100 text-gray-600"
	}
}

function formatNumber(val) {
	return parseFloat(val || 0).toFixed(2)
}

function formatShiftDateTime(datetimeStr) {
	if (!datetimeStr) return ""
	// Input: "YYYY-MM-DD HH:MM:SS" → Display: "YYYY-MM-DD HH:MM"
	return datetimeStr.substring(0, 16)
}

function goBack() {
	router.push({ name: "POSSale" })
}

// Watch date filters to auto-refresh
watch(
	() => [filters.value.date_from, filters.value.date_to],
	([newFrom, newTo], [oldFrom, oldTo]) => {
		if (newFrom !== oldFrom || newTo !== oldTo) {
			fetchOrders()
		}
	}
)

watch(wastageStockEntryType, () => {
	selectedEmployee.value = null
	employeeSearch.value = ""
	employees.value = []
})

// ── Realtime ──────────────────────────────────────────────────────────────────
const { onOrderChanged, playNewOrderSound } = useRealtimeOrders()

// Debounce rapid-fire events into a single refresh
let realtimeRefreshTimer = null
function scheduleRealtimeRefresh(data) {
	if (data?.action === "create") {
		playNewOrderSound()
	}
	clearTimeout(realtimeRefreshTimer)
	realtimeRefreshTimer = setTimeout(() => {
		fetchOrders()
	}, 800)
}

let unsubscribeOrders = null

// ===== RETURNED / CANCELLED ORDER ALARM (Call Center) =====
const reversalAlert = ref(null)
let reversalTimer = null
let returnAlarmTimer = null

function onKdsUpdate(data) {
	if (!data) return
	if (data.action === "order_returned" || data.action === "order_cancelled" || data.action === "order_needs_action") {
		showReversalAlert(data)
		clearTimeout(realtimeRefreshTimer)
		realtimeRefreshTimer = setTimeout(() => fetchOrders(), 800)
	}
}

function showReversalAlert(data) {
	if (!data?.is_call_center) return
	const kind = data.action === "order_returned"
		? "returned"
		: data.action === "order_cancelled"
			? "cancelled"
			: "needs_action"
	reversalAlert.value = {
		kind,
		number: data.number || data.invoice,
		approval: data.approval || null,
	}
	startReturnAlarm()
	if (reversalTimer) clearTimeout(reversalTimer)
	reversalTimer = setTimeout(() => { reversalAlert.value = null }, 30000)
}

function goToNeedMyAction() {
	dismissReversalAlert()
	router.push({ name: "NeedMyAction" }).catch(() => router.push("/need-my-action"))
}

function startReturnAlarm() {
	stopReturnAlarm()
	let elapsed = 0
	try { playNewOrderSound() } catch {}
	returnAlarmTimer = setInterval(() => {
		elapsed += 1
		if (elapsed >= 30) { stopReturnAlarm(); return }
		try { playNewOrderSound() } catch {}
	}, 1000)
}
function stopReturnAlarm() {
	if (returnAlarmTimer) { clearInterval(returnAlarmTimer); returnAlarmTimer = null }
}
function dismissReversalAlert() {
	stopReturnAlarm()
	if (reversalTimer) { clearTimeout(reversalTimer); reversalTimer = null }
	reversalAlert.value = null
}

onMounted(async () => {
	await loadConfig()
	fetchOrders()
	loadPosProfile()
	loadActiveDrivers()
	unsubscribeOrders = onOrderChanged(scheduleRealtimeRefresh)
	const socket = initSocket()
	if (socket) {
		socket.connect()
		socket.on("kds_update", onKdsUpdate)
	}
})

onUnmounted(() => {
	unsubscribeOrders?.()
	clearTimeout(realtimeRefreshTimer)
	stopReturnAlarm()
	const socket = initSocket()
	if (socket) socket.off("kds_update", onKdsUpdate)
})

// ===== ACTIVE DRIVERS =====
async function loadActiveDrivers() {
	try {
		const result = await call("ecs_posnext.api.invoices.get_active_drivers", {})
		activeDrivers.value = result || []
	} catch (error) {
		console.error("Failed to load active drivers:", error)
		activeDrivers.value = []
	}
}

function getDriverDisplayName(driverName) {
	if (!driverName) return "-"
	const found = activeDrivers.value.find(d => d.name === driverName)
	return found ? (found.full_name || found.name) : driverName
}

// ===== ASSIGN DRIVER DIALOG =====
function openAssignDriverDialog(order) {
	driverDialogInvoiceName.value = order.custom_number_order || order.name
	driverDialogSelected.value = order.driver || ""
	showDriverDialog.value = true
	// Store the invoice name for the API call
	showDriverDialog._invoiceName = order.name
}

function closeDriverDialog() {
	showDriverDialog.value = false
	driverDialogInvoiceName.value = ""
	driverDialogSelected.value = ""
	driverAssigning.value = false
}

function openMobileDialog(order) {
	mobileDialogCustomer.value = order.customer
	mobileDialogCustomerName.value = order.customer_name || order.customer
	mobileDialogValue.value = order.other_mobile_no || ""
	showMobileDialog.value = true
}

function closeMobileDialog() {
	showMobileDialog.value = false
	mobileDialogCustomer.value = ""
	mobileDialogCustomerName.value = ""
	mobileDialogValue.value = ""
}

async function confirmMobile() {
	if (mobileSaving.value || !mobileDialogCustomer.value) return
	mobileSaving.value = true
	try {
		const val = (mobileDialogValue.value || "").trim()
		await call("frappe.client.set_value", {
			doctype: "Customer",
			name: mobileDialogCustomer.value,
			fieldname: "custom_other_mobile_no",
			value: val,
		})
		// Reflect the new number on every order for this customer in the list
		orders.value.forEach((o) => {
			if (o.customer === mobileDialogCustomer.value) o.other_mobile_no = val
		})
		window.frappe?.show_alert?.({ message: __("Second mobile saved"), indicator: "green" })
		closeMobileDialog()
	} catch (error) {
		console.error("Failed to save second mobile:", error)
		window.frappe?.show_alert?.({ message: __("Failed to save second mobile"), indicator: "red" })
	} finally {
		mobileSaving.value = false
	}
}

async function confirmAssignDriver() {
	if (driverAssigning.value) return
	driverAssigning.value = true
	try {
		await call("ecs_posnext.api.invoices.assign_driver_to_invoice", {
			invoice_name: showDriverDialog._invoiceName,
			driver: driverDialogSelected.value,
		})
		window.frappe?.show_alert?.({ message: __("Driver assigned successfully"), indicator: "green" })
		closeDriverDialog()
		fetchOrders()
	} catch (error) {
		console.error("Failed to assign driver:", error)
		window.frappe?.show_alert?.({ message: __("Failed to assign driver"), indicator: "red" })
	} finally {
		driverAssigning.value = false
	}
}

async function convertOrderType(order, newType) {
	try {
		await call("ecs_posnext.api.invoices.convert_order_type", {
			invoice_name: order.name,
			order_type: newType,
		})
		window.frappe?.show_alert?.({ message: __("Order type updated to ") + newType, indicator: "green" })
		fetchOrders()
	} catch (error) {
		console.error("Failed to convert order type:", error)
		window.frappe?.show_alert?.({ message: __("Failed to update order type"), indicator: "red" })
	}
}

function openReturnDialog(order) {
	returnOrder.value = order
	returnPaymentType.value = order.custom_payment_type || null
	returnReceiptNumber.value = order.custom_receipt_number || ""
	showReturnDialog.value = true
}

function closeReturnDialog() {
	showReturnDialog.value = false
	returnOrder.value = null
	returnPaymentType.value = null
	returnReceiptNumber.value = ""
}

async function confirmReturnToNeedMyAction() {
	if (returnSubmitting.value || !returnOrder.value) return
	returnSubmitting.value = true
	try {
		await call("ecs_posnext.api.invoices.return_order_to_need_my_action", {
			invoice_name: returnOrder.value.name,
			payment_type: returnPaymentType.value || "",
			receipt_number: returnReceiptNumber.value || "",
		})
		window.frappe?.show_alert?.({ message: __("Order returned to Need My Action"), indicator: "green" })
		closeReturnDialog()
		fetchOrders()
	} catch (error) {
		console.error("Failed to return order to Need My Action:", error)
		window.frappe?.show_alert?.({ message: __("Failed to return order to Need My Action"), indicator: "red" })
	} finally {
		returnSubmitting.value = false
	}
}
</script>
