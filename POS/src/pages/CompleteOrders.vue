<template>
	<div class="flex flex-col h-screen bg-gray-50">
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
			<h1 class="text-lg font-semibold text-gray-900">{{ __("Complete Orders") }}</h1>
			<div class="flex-1"></div>
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

		<!-- Filters and Status Row -->
		<div class="bg-white border-b border-gray-200 px-4 py-3 space-y-3">
			<div class="flex flex-wrap items-center gap-3">
				<!-- Search -->
				<div class="relative flex-1 min-w-[200px] max-w-md">
					<svg class="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
					</svg>
					<input
						v-model="search"
						type="text"
						:placeholder="__('Search orders...')"
						class="w-full ps-10 pe-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
					/>
				</div>
				<!-- Date Filter -->
				<div class="flex items-center gap-2">
					<label class="text-xs font-medium text-gray-600">{{ __("Date:") }}</label>
					<input
						v-model="filterDate"
						type="date"
						class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white"
					/>
				</div>
				<!-- Mobile Filter -->
				<div class="flex items-center gap-2">
					<label class="text-xs font-medium text-gray-600">{{ __("Mobile:") }}</label>
					<input
						v-model="filterMobile"
						type="text"
						:placeholder="__('Customer mobile')"
						class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none w-36"
					/>
				</div>
				<!-- Unique Number Filter -->
				<div class="flex items-center gap-2">
					<label class="text-xs font-medium text-gray-600">{{ __("Unique No.:") }}</label>
					<input
						v-model="filterUniqueNumber"
						type="text"
						:placeholder="__('Talabat unique no.')"
						class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none w-36"
					/>
				</div>
				<!-- Branch Filter -->
				<div class="flex items-center gap-2">
					<label class="text-xs font-medium text-gray-600">{{ __("Branch:") }}</label>
					<select
						v-model="filterBranch"
						class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white text-gray-700"
					>
						<option value="">{{ __("All Branches") }}</option>
						<option v-for="b in branchOptions" :key="b" :value="b">{{ b }}</option>
					</select>
				</div>
			</div>

			<!-- Status Chips -->
			<div class="flex flex-wrap gap-2">
				<button
					v-for="chip in statusSummary"
					:key="chip.value"
					@click="statusFilter = chip.value"
					:class="[
						'px-3 py-1.5 rounded-full text-xs font-semibold transition-all flex items-center gap-2',
						statusFilter === chip.value
							? 'bg-blue-600 text-white shadow-md'
							: 'bg-gray-100 text-gray-600 hover:bg-gray-200'
					]"
				>
					{{ chip.label }}
					<span :class="[
						'px-1.5 py-0.5 rounded-full text-[10px]',
						statusFilter === chip.value ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'
					]">
						{{ chip.count }}
					</span>
				</button>
			</div>
		</div>

		<!-- Table -->
		<div class="flex-1 overflow-auto px-4 py-3">
			<div v-if="loading && !orders.length" class="flex items-center justify-center py-20">
				<div class="text-center">
					<svg class="w-10 h-10 animate-spin text-blue-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
					</svg>
					<p class="text-sm text-gray-500">{{ __("Loading orders...") }}</p>
				</div>
			</div>

			<div v-else-if="!filteredOrders.length && !loading" class="flex items-center justify-center py-20">
				<div class="text-center">
					<svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
					<p class="text-gray-500 font-medium">{{ __("No orders found") }}</p>
				</div>
			</div>

			<div v-else class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="bg-gray-50 border-b border-gray-200">
								<th class="px-4 py-3 text-start text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Order") }}</th>
								<th class="px-4 py-3 text-start text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Time") }}</th>
								<th class="px-4 py-3 text-start text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Customer") }}</th>
								<th class="px-4 py-3 text-start text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Branch") }}</th>
								<th class="px-4 py-3 text-start text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Type") }}</th>
								<th class="px-4 py-3 text-start text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Unique No.") }}</th>
								<th class="px-4 py-3 text-start text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Driver") }}</th>
								<th class="px-4 py-3 text-start text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Status") }}</th>
								<th class="px-4 py-3 text-start text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("KDS") }}</th>
								<th class="px-4 py-3 text-end text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Total") }}</th>
								<th class="px-4 py-3 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Actions") }}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<template v-for="order in paginatedOrders" :key="order.name">
							<tr class="hover:bg-gray-50 transition-colors">
								<td class="px-4 py-3 font-medium text-blue-600">
									{{ order.custom_number_order || order.name }}
									<span v-if="order.supplements && order.supplements.length" class="ms-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-700">+{{ order.supplements.length }}</span>
								</td>
								<td class="px-4 py-3 text-gray-600 whitespace-nowrap">{{ fmtOrderTime(order.order_time) }}</td>
								<td class="px-4 py-3">
									<div class="text-gray-900 font-medium">{{ order.customer_name }}</div>
									<div class="text-xs text-gray-400">{{ order.contact_mobile }}</div>
								</td>
								<td class="px-4 py-3 text-gray-600">{{ order.branch }}</td>
								<td class="px-4 py-3">
									<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
										{{ order.custom_so_type }}
									</span>
								</td>
								<td class="px-4 py-3 text-xs text-gray-600">{{ order.custom_unique_talbat_number || '-' }}</td>
								<td class="px-4 py-3">
									<div v-if="order.driver_name" class="flex flex-col">
										<span class="text-gray-900 font-medium">{{ order.driver_name }}</span>
										<span class="text-xs text-gray-400">{{ order.cell_number }}</span>
									</div>
									<span v-else class="text-gray-400">-</span>
								</td>
								<td class="px-4 py-3">
									<span :class="getStatusClasses(order.status_name)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
										{{ order.status_name }}
									</span>
								</td>
								<td class="px-4 py-3">
									<span v-if="order.kds_status" :class="getKdsStatusClasses(order.kds_status)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
										{{ order.kds_status }}
									</span>
									<span v-else class="text-gray-300">-</span>
								</td>
								<td class="px-4 py-3 text-end font-bold text-gray-900">{{ formatNumber(order._combined_total !== undefined ? order._combined_total : order.grand_total) }}</td>
								<td class="px-4 py-3">
									<div class="flex items-center justify-center gap-2">
										<!-- View Items -->
										<button @click="viewOrderItems(order.name)" class="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" :title="__('View Items')">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
											</svg>
										</button>
										<!-- Print -->
										<button @click="printOrder(order.name)" class="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors" :title="__('Print Receipt')">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
											</svg>
										</button>
										<!-- Kitchen Print -->
										<button @click="printOrderKitchen(order.name)" class="p-1.5 text-gray-500 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors" :title="__('Kitchen Print')">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
											</svg>
										</button>
										<!-- Assign Driver / Complete -->
										<button 
											v-if="order.status_name.toLowerCase() !== 'completed'"
											@click="handleOrderAction(order)"
											:class="[
												'p-1.5 rounded-lg transition-colors',
												order.custom_so_type === 'Delivery' ? 'text-teal-600 hover:bg-teal-50' : 'text-green-600 hover:bg-green-50'
											]"
											:title="order.custom_so_type === 'Delivery' ? __('Assign Driver') : __('Mark as Completed')"
										>
											<svg v-if="order.custom_so_type === 'Delivery'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
											</svg>
											<svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
											</svg>
										</button>
										<!-- Cancel (hidden on Completed Orders) -->
										<button v-if="false" @click="deleteOrder(order.name)" class="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" :title="__('Cancel')">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
											</svg>
										</button>
									</div>
								</td>
							</tr>

							<!-- Supplement rows (additions on the same order) stacked under the parent -->
							<tr v-for="sup in order.supplements" :key="sup.name" class="bg-indigo-50/40 hover:bg-indigo-50 transition-colors">
								<td class="px-4 py-2 ps-8 font-medium text-indigo-700">↳ {{ sup.custom_number_order || sup.name }}</td>
								<td class="px-4 py-2 text-gray-500 whitespace-nowrap">{{ fmtOrderTime(sup.order_time) }}</td>
								<td class="px-4 py-2 text-xs text-gray-400">{{ __("إضافة") }}</td>
								<td class="px-4 py-2 text-gray-500">{{ sup.branch }}</td>
								<td class="px-4 py-2">
									<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">{{ sup.custom_so_type }}</span>
								</td>
								<td class="px-4 py-2 text-xs text-gray-500">{{ sup.custom_unique_talbat_number || '-' }}</td>
								<td class="px-4 py-2 text-gray-400">-</td>
								<td class="px-4 py-2">
									<span :class="getStatusClasses(sup.status_name)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">{{ sup.status_name }}</span>
								</td>
								<td class="px-4 py-2">
									<span v-if="sup.kds_status" :class="getKdsStatusClasses(sup.kds_status)" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">{{ sup.kds_status }}</span>
									<span v-else class="text-gray-300">-</span>
								</td>
								<td class="px-4 py-2 text-end font-semibold text-gray-700">{{ formatNumber(sup.grand_total) }}</td>
								<td class="px-4 py-2">
									<div class="flex items-center justify-center gap-2">
										<button @click="viewOrderItems(sup.name)" class="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" :title="__('View Items')">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
											</svg>
										</button>
										<button @click="printOrder(sup.name)" class="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors" :title="__('Print Receipt')">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
											</svg>
										</button>
									</div>
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
							class="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-100 disabled:opacity-50"
						>
							{{ __("Prev") }}
						</button>
						<span class="text-sm text-gray-600">{{ currentPage }} / {{ totalPages }}</span>
						<button
							@click="currentPage = Math.min(totalPages, currentPage + 1)"
							:disabled="currentPage >= totalPages"
							class="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-100 disabled:opacity-50"
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
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-hidden">
					<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">{{ __("Order Items") }}</h3>
						<button @click="showItemDialog = false" class="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>
					<div class="p-6 overflow-auto max-h-[60vh]">
						<div v-if="itemLoading" class="flex items-center justify-center py-8">
							<svg class="w-8 h-8 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
							</svg>
						</div>
						<table v-else class="w-full text-sm">
							<thead>
								<tr class="border-b border-gray-200">
									<th class="text-start py-2 text-xs font-semibold text-gray-600">{{ __("Item") }}</th>
									<th class="text-end py-2 text-xs font-semibold text-gray-600">{{ __("Qty") }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								<tr v-for="(item, idx) in selectedItems" :key="idx">
									<td class="py-3 text-gray-700 font-medium">
										<div class="flex items-center gap-2">
											<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
											</svg>
											{{ item.item_code }}
										</div>
									</td>
									<td class="py-3 text-end text-gray-900 font-bold">{{ item.qty }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>

			<!-- Driver Assignment Dialog -->
			<div v-if="showDriverDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="showDriverDialog = false">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
					<div class="px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">{{ __("Select Driver") }}</h3>
					</div>
					<div class="p-6">
						<label class="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">{{ __("Choose a Driver") }}</label>
						<select v-model="selectedDriver" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white">
							<option :value="null">{{ __("Select Driver...") }}</option>
							<option v-for="driver in drivers" :key="driver" :value="driver">{{ driver }}</option>
						</select>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
						<button @click="showDriverDialog = false" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
							{{ __("Cancel") }}
						</button>
						<button 
							@click="submitDriver" 
							:disabled="!selectedDriver"
							class="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50"
						>
							{{ __("Assign") }}
						</button>
					</div>
				</div>
			</div>

			<!-- Password Confirmation Dialog -->
			<div v-if="showPasswordDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="showPasswordDialog = false">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
					<div class="px-6 py-4 border-b border-gray-200">
						<h3 class="text-lg font-semibold text-gray-900">{{ __("Confirm Cancellation") }}</h3>
					</div>
					<div class="p-6">
						<label class="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">{{ __("Supervisor Password") }}</label>
						<input
							v-model="passwordInput"
							type="password"
							autocomplete="off"
							:placeholder="__('Enter password')"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
							@keyup.enter="confirmDelete"
						/>
						<p v-if="passwordError" class="mt-2 text-xs text-red-600 font-medium">{{ passwordError }}</p>
					</div>
					<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
						<button @click="showPasswordDialog = false" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
							{{ __("Cancel") }}
						</button>
						<button @click="confirmDelete" class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700">
							{{ __("Confirm") }}
						</button>
					</div>
				</div>
			</div>
		</teleport>
	</div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import { call } from "@/utils/apiWrapper"
import { __ } from "@/utils/translation"

const router = useRouter()

// State
const orders = ref([])
const loading = ref(false)
const search = ref("")
const statusFilter = ref("all")
const filterDate = ref(new Date().toISOString().substr(0, 10))
const filterMobile = ref("")
const filterUniqueNumber = ref("")
const filterBranch = ref("")
const currentPage = ref(1)
const perPage = ref(50)
const posProfile = ref(null)

// Dialog states
const showItemDialog = ref(false)
const itemLoading = ref(false)
const selectedItems = ref([])
const showDriverDialog = ref(false)
const selectedDriver = ref(null)
const drivers = ref([])
const activeOrder = ref(null)
const showPasswordDialog = ref(false)
const passwordInput = ref("")
const passwordError = ref("")
const orderToDelete = ref(null)

// Format the order time (HH:MM) so the chronological order reads clearly
const fmtOrderTime = (dt) => {
	if (!dt) return "-"
	try {
		return new Date(String(dt).replace(" ", "T")).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
	} catch {
		return "-"
	}
}

// Actions
const goBack = () => router.push("/")

const fetchOrders = async () => {
	loading.value = true
	try {
		const r = await call("ecs_posnext.api.kitchen_order.get_sales_order2")
		// Completed Orders shows only submitted invoices — hide drafts and cancelled orders
		orders.value = (r || []).filter(o =>
			o.docstatus === 1 && (o.status_name || "").toLowerCase() !== "cancelled"
		)
	} catch (error) {
		console.error("Failed to fetch orders:", error)
		window.frappe?.show_alert?.({ message: __("Failed to load orders"), indicator: "red" })
	} finally {
		loading.value = false
	}
}

const checkOpeningShift = async () => {
	try {
		const r = await call("ecs_posnext.api.shifts.check_opening_shift", {
			user: window.frappe?.session?.user || ""
		})
		if (r) {
			posProfile.value = r.pos_profile
		}
	} catch (error) {
		console.error("Failed to check opening shift:", error)
	}
}

// ── Supplement grouping (mirror All Orders) ──────────────────────────────────
// Supplement order numbers have 2+ hyphens: M-1-1 is a supplement of M-1.
function isSupplementOrder(orderNum) {
	if (!orderNum) return false
	return String(orderNum).split("-").length >= 3
}
function getParentOrderNum(orderNum) {
	if (!isSupplementOrder(orderNum)) return null
	const s = String(orderNum)
	return s.substring(0, s.lastIndexOf("-"))
}

// Group supplements under their parent order (adds a +N badge + combined total)
const groupedOrders = computed(() => {
	const all = orders.value
	const parentMap = {}
	const supplementSet = new Set()
	const result = []

	// Reset any previously attached supplements (prevents duplicates on re-compute)
	for (const order of all) {
		order.supplements = []
		order._combined_total = undefined
	}

	// First pass: index parent orders by their number
	for (const order of all) {
		const num = order.custom_number_order
		if (num && !isSupplementOrder(num)) parentMap[num] = order
	}

	// Second pass: attach each supplement to its parent (if the parent is present)
	for (const order of all) {
		const num = order.custom_number_order
		if (num && isSupplementOrder(num)) {
			const parent = parentMap[getParentOrderNum(num)]
			if (parent) {
				parent.supplements.push(order)
				if (parent._combined_total === undefined) parent._combined_total = parseFloat(parent.grand_total || 0)
				parent._combined_total += parseFloat(order.grand_total || 0)
				supplementSet.add(order.name)
			}
		}
	}

	// Keep parents + any supplement whose parent isn't in the current result set
	for (const order of all) {
		if (!supplementSet.has(order.name)) result.push(order)
	}
	return result
})

// Filters
const filteredOrders = computed(() => {
	let data = groupedOrders.value.slice()
	
	if (statusFilter.value !== "all") {
		data = data.filter(o => (o.status_name || "").toLowerCase() === statusFilter.value.toLowerCase())
	}
	
	if (filterDate.value) {
		data = data.filter(o => o.transaction_date === filterDate.value)
	}
	
	if (search.value) {
		const s = search.value.toLowerCase()
		data = data.filter(o =>
			(o.custom_number_order || o.name).toLowerCase().includes(s) ||
			(o.customer_name || "").toLowerCase().includes(s) ||
			(o.contact_mobile || "").toLowerCase().includes(s) ||
			(o.custom_unique_talbat_number || "").toLowerCase().includes(s) ||
			(o.branch || "").toLowerCase().includes(s)
		)
	}

	if (filterMobile.value) {
		const m = filterMobile.value.toLowerCase()
		data = data.filter(o =>
			(o.contact_mobile || "").toLowerCase().includes(m) ||
			(o.other_mobile_no || "").toLowerCase().includes(m)
		)
	}

	if (filterUniqueNumber.value) {
		const u = filterUniqueNumber.value.toLowerCase()
		data = data.filter(o => (o.custom_unique_talbat_number || "").toLowerCase().includes(u))
	}

	if (filterBranch.value) {
		data = data.filter(o => o.branch === filterBranch.value)
	}

	return data
})

const branchOptions = computed(() =>
	[...new Set(orders.value.map(o => o.branch).filter(Boolean))].sort()
)

const statusSummary = computed(() => {
	const summary = {}
	orders.value.forEach(o => {
		const key = (o.status_name || "unknown").toLowerCase()
		summary[key] = (summary[key] || 0) + 1
	})
	
	const options = ["all", "pending", "preparing", "dining", "packing", "delivery", "completed", "cancelled"]
	return options.map(v => ({
		value: v,
		label: v === "all" ? __("All") : __(v.charAt(0).toUpperCase() + v.slice(1)),
		count: v === "all" ? orders.value.length : (summary[v] || 0)
	})).filter(c => c.value === "all" || c.count > 0)
})

// Pagination
const totalPages = computed(() => Math.max(1, Math.ceil(filteredOrders.value.length / perPage.value)))
const paginationStart = computed(() => Math.min((currentPage.value - 1) * perPage.value + 1, filteredOrders.value.length))
const paginationEnd = computed(() => Math.min(currentPage.value * perPage.value, filteredOrders.value.length))
const paginatedOrders = computed(() => {
	const start = (currentPage.value - 1) * perPage.value
	return filteredOrders.value.slice(start, start + perPage.value)
})

// Reset to page 1 whenever any filter changes
watch([filterMobile, () => filteredOrders.value.length], () => { currentPage.value = 1 })

// Status colors
const getStatusClasses = (status) => {
	const s = (status || "").toLowerCase()
	switch (s) {
		case "pending": return "bg-orange-100 text-orange-700"
		case "preparing": return "bg-blue-100 text-blue-700"
		case "dining": return "bg-purple-100 text-purple-700"
		case "packing": return "bg-amber-100 text-amber-700"
		case "delivery": return "bg-teal-100 text-teal-700"
		case "completed": return "bg-green-100 text-green-700"
		case "cancelled": return "bg-red-100 text-red-700"
		default: return "bg-gray-100 text-gray-700"
	}
}

const getKdsStatusClasses = (status) => {
	switch (status) {
		case "Pending":   return "bg-gray-100 text-gray-700"
		case "Preparing": return "bg-blue-100 text-blue-700"
		case "Ready":     return "bg-green-100 text-green-700"
		case "Completed": return "bg-emerald-100 text-emerald-700"
		case "Cancelled": return "bg-red-100 text-red-700"
		default:          return "bg-gray-100 text-gray-600"
	}
}

// Order Actions
const viewOrderItems = async (name) => {
	activeOrder.value = name
	showItemDialog.value = true
	itemLoading.value = true
	try {
		const r = await call("ecs_posnext.api.kitchen_order.get_items_sales_order", { name })
		if (r && r[1]) {
			selectedItems.value = r[1].map(i => ({
				item_code: i.item_code || i.item_name || "",
				qty: i.qty || 0
			}))
		}
	} catch (error) {
		console.error("Failed to fetch order items:", error)
	} finally {
		itemLoading.value = false
	}
}

const printOrder = async (name) => {
	try {
		const r = await call("ecs_posnext.api.kitchen_order.get_sales_invoice_from_order", { sales_order: name })
		const invoice = r?.[0]?.parent
		if (invoice) {
			const fmt = encodeURIComponent("print format sales")
			window.open(`/printview?doctype=Sales Invoice&name=${encodeURIComponent(invoice)}&trigger_print=1&format=${fmt}&no_letterhead=0`, "_blank")
		} else {
			window.frappe?.show_alert?.({ message: __("No linked Sales Invoice found"), indicator: "orange" })
		}
	} catch (error) {
		console.error("Print error:", error)
	}
}

const printOrderKitchen = async (name) => {
	try {
		const r = await call("ecs_posnext.api.kitchen_order.get_sales_invoice_from_order", { sales_order: name })
		const invoice = r?.[0]?.parent
		if (invoice) {
			window.open(`/printview?doctype=Sales Invoice&name=${invoice}&trigger_print=1&format=Kitchen%20Receipt&no_letterhead=0`, "_blank")
		} else {
			window.frappe?.show_alert?.({ message: __("No linked Sales Invoice found"), indicator: "orange" })
		}
	} catch (error) {
		console.error("Kitchen Print error:", error)
	}
}

const handleOrderAction = (order) => {
	activeOrder.value = order
	if (order.custom_so_type === "Delivery") {
		showDriverDialog.value = true
		fetchDrivers(order.branch)
	} else {
		completeOrder(order.name)
	}
}

const fetchDrivers = async (branch) => {
	try {
		const r = await call("ecs_posnext.api.kitchen_order.get_drivers_by_branch", { branch })
		drivers.value = r ? r.map(d => d.name) : []
	} catch (error) {
		console.error("Failed to fetch drivers:", error)
	}
}

const submitDriver = async () => {
	if (!selectedDriver.value) return
	try {
		await call("ecs_posnext.api.kitchen_order.update_sales_order_driver", {
			name: activeOrder.value.name,
			status: "Delivery",
			driver: selectedDriver.value
		})
		window.frappe?.show_alert?.({ message: __("Driver assigned successfully"), indicator: "green" })
		showDriverDialog.value = false
		fetchOrders()
	} catch (error) {
		console.error("Failed to assign driver:", error)
	}
}

const completeOrder = async (name) => {
	try {
		await call("ecs_posnext.api.kitchen_order.update_sales_order", {
			name: name,
			status: "Completed",
			driver: null
		})
		window.frappe?.show_alert?.({ message: __("Order marked as Completed"), indicator: "green" })
		fetchOrders()
	} catch (error) {
		console.error("Failed to complete order:", error)
	}
}

const deleteOrder = (name) => {
	orderToDelete.value = name
	passwordInput.value = ""
	passwordError.value = ""
	showPasswordDialog.value = true
}

const confirmDelete = async () => {
	passwordError.value = ""
	let manager = null
	try {
		const res = await call("ecs_posnext.api.kitchen_order.verify_cancel_manager", {
			pos_profile: posProfile.value?.name || posProfile.value || "",
			password: passwordInput.value,
		})
		if (!res || !res.valid) {
			passwordError.value = __("Incorrect supervisor password")
			return
		}
		manager = res.manager || null
	} catch (error) {
		console.error("Manager verification failed:", error)
		passwordError.value = __("Incorrect supervisor password")
		return
	}

	try {
		await call("ecs_posnext.api.kitchen_order.cancel_sales_order_and_invoices", {
			sales_order: orderToDelete.value,
			cancelled_by_manager: manager,
		})
		window.frappe?.show_alert?.({ message: __("Order cancelled successfully"), indicator: "green" })
		showPasswordDialog.value = false
		fetchOrders()
	} catch (error) {
		console.error("Failed to cancel order:", error)
	}
}

const formatNumber = (val) => {
	return new Intl.NumberFormat(undefined, { minimumFractionDigits: 2 }).format(val)
}

// Real-time
const setupRealtime = () => {
	if (!window.frappe?.realtime) return
	window.frappe.realtime.on("sales_order_created", fetchOrders)
	window.frappe.realtime.on("sales_order_updated", fetchOrders)
}

const cleanupRealtime = () => {
	if (!window.frappe?.realtime) return
	window.frappe.realtime.off("sales_order_created", fetchOrders)
	window.frappe.realtime.off("sales_order_updated", fetchOrders)
}

onMounted(() => {
	checkOpeningShift()
	fetchOrders()
	setupRealtime()
})

onUnmounted(() => {
	cleanupRealtime()
})
</script>

<style scoped>
/* Custom transitions for a premium feel */
.transition-all {
	transition-property: all;
	transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
	transition-duration: 200ms;
}
</style>
