<template>
	<div class="flex flex-col h-screen bg-gray-50">
		<!-- Header -->
		<div class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm">
			<div class="flex items-center gap-3">
				<button
					@click="goBack"
					class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
					</svg>
					{{ __("Back") }}
				</button>
				<div>
					<h1 class="text-xl font-bold text-gray-900">{{ __("Need My Action") }}</h1>
					<p class="text-xs text-gray-500 mt-0.5">{{ __("Draft invoices from Call Center awaiting cashier checkout") }}</p>
				</div>
			</div>
			<div class="flex items-center gap-3">
				<span class="text-sm text-gray-500 mr-2" v-if="filteredOrders.length">
					{{ __("{0} Pending Orders", { 0: String(filteredOrders.length) }) }}
				</span>
				<button
					@click="fetchOrders"
					:disabled="loading"
					class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
		</div>

		<!-- Filters -->
		<div class="bg-white border-b border-gray-200 px-6 py-4 flex flex-wrap items-center gap-4">
			<!-- Search input -->
			<div class="relative flex-1 min-w-[300px] max-w-md">
				<svg class="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
				</svg>
				<input
					v-model="search"
					type="text"
					:placeholder="__('Search by order #, customer, branch or items...')"
					class="w-full ps-10 pe-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
				/>
			</div>

			<!-- Order Type filter -->
			<div class="flex items-center gap-2">
				<label class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Order Type:") }}</label>
				<select v-model="orderTypeFilter" class="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white font-medium text-gray-700">
					<option value="all">{{ __("All Types") }}</option>
					<option v-for="type in orderTypes" :key="type" :value="type">{{ type }}</option>
				</select>
			</div>
		</div>

		<!-- Main content -->
		<div class="flex-1 overflow-auto p-6">
			<!-- Loading state -->
			<div v-if="loading && !orders.length && !failedDeliveries.length" class="flex flex-col items-center justify-center py-32 bg-white rounded-2xl border border-gray-200 shadow-sm">
				<svg class="w-12 h-12 animate-spin text-blue-600 mb-4" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
				</svg>
				<p class="text-gray-600 font-semibold">{{ __("Loading pending actions...") }}</p>
			</div>

			<!-- Failed Delivery Orders Section -->
			<div v-if="failedDeliveries.length" class="mb-8">
				<div class="flex items-center gap-2 mb-4">
					<span class="w-3 h-3 rounded-full bg-red-500 animate-pulse"></span>
					<h2 class="text-base font-bold text-red-700">{{ __("Failed Deliveries — Pending Cancellation") }}</h2>
					<span class="ml-1 px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs font-bold">{{ failedDeliveries.length }}</span>
				</div>
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					<div
						v-for="d in failedDeliveries"
						:key="d.name"
						class="bg-white rounded-2xl border-2 border-red-200 shadow-sm overflow-hidden flex flex-col"
					>
						<div class="px-5 py-4 border-b border-red-100 flex items-start justify-between bg-red-50">
							<div>
								<div class="text-sm font-bold text-red-900 flex items-center gap-1.5">
									❌ {{ d.custom_number_order || d.order_reference }}
								</div>
								<div class="text-xs text-red-600 mt-0.5">{{ d.custom_order_type || "Delivery" }} — {{ d.branch }}</div>
							</div>
							<span class="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-red-100 text-red-700">Failed</span>
						</div>
						<div class="p-4 flex-1 space-y-2">
							<div class="text-sm font-semibold text-gray-900">{{ d.customer }}</div>
							<div v-if="d.delivery_address" class="text-xs text-gray-500">📍 {{ d.delivery_address }}</div>
							<div class="text-xs text-gray-400">{{ __("Driver:") }} {{ d.driver }}</div>
							<div v-if="d.delivery_notes" class="mt-2 p-2.5 bg-red-50 rounded-lg border border-red-100">
								<div class="text-xs font-bold text-red-600 mb-0.5">{{ __("Failure Reason:") }}</div>
								<div class="text-sm text-red-800">{{ d.delivery_notes }}</div>
							</div>
						</div>
						<div class="px-4 py-3 border-t border-red-100 flex items-center justify-between bg-gray-50">
							<div class="text-sm font-bold text-gray-900">{{ formatNumber(d.grand_total) }}</div>
							<button
								@click="deleteDeliveryOrder(d)"
								class="flex items-center gap-1.5 px-4 py-2 text-sm font-bold text-white bg-red-600 hover:bg-red-700 active:bg-red-800 rounded-xl transition-all active:scale-95"
							>
								🗑 {{ __("Cancel Order") }}
							</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Customer Status Requests (VIP / Blacklist) -->
			<div v-if="statusRequests.length" class="mb-8">
				<div class="flex items-center gap-2 mb-4">
					<span class="w-3 h-3 rounded-full bg-amber-500 animate-pulse"></span>
					<h2 class="text-base font-bold text-amber-700">{{ __("Customer Status Requests") }}</h2>
					<span class="ml-1 px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs font-bold">{{ statusRequests.length }}</span>
				</div>
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					<div v-for="r in statusRequests" :key="r.name"
						:class="['bg-white rounded-2xl border-2 shadow-sm overflow-hidden flex flex-col', r.request_type === 'Blacklist' ? 'border-red-200' : 'border-amber-200']">
						<div :class="['px-5 py-4 border-b flex items-start justify-between', r.request_type === 'Blacklist' ? 'bg-red-50 border-red-100' : 'bg-amber-50 border-amber-100']">
							<div>
								<div class="text-sm font-bold text-gray-900">{{ r.customer_name || r.customer }}</div>
								<div class="text-xs text-gray-500 mt-0.5">{{ r.mobile || '' }}<span v-if="r.branch"> — {{ r.branch }}</span></div>
							</div>
							<span :class="['px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider', r.request_type === 'Blacklist' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-800']">
								{{ r.request_type === 'Blacklist' ? '🚫' : '⭐' }} {{ __(r.request_type) }}
							</span>
						</div>
						<div class="p-4 flex-1 text-sm text-gray-700">
							{{ r.enable ? __('Request to set {0}', [__(r.request_type)]) : __('Request to remove {0}', [__(r.request_type)]) }}
							<div class="text-xs text-gray-400 mt-1">{{ __('By') }}: {{ r.requested_by }}</div>
						</div>
						<div class="px-4 py-3 border-t border-gray-100 flex items-center gap-2 bg-gray-50">
							<button @click="rejectStatusRequest(r)" :disabled="statusBusy === r.name" class="flex-1 px-3 py-2 text-sm font-bold text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-100 disabled:opacity-50">{{ __("Reject") }}</button>
							<button @click="approveStatusRequest(r)" :disabled="statusBusy === r.name" class="flex-1 px-3 py-2 text-sm font-bold text-white bg-green-600 rounded-xl hover:bg-green-700 disabled:opacity-50">{{ __("Approve") }}</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Compensation Coupon Requests -->
			<div v-if="couponRequests.length" class="mb-8">
				<div class="flex items-center gap-2 mb-4">
					<span class="w-3 h-3 rounded-full bg-green-500 animate-pulse"></span>
					<h2 class="text-base font-bold text-green-700">{{ __("Compensation Coupon Requests") }}</h2>
					<span class="ml-1 px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-bold">{{ couponRequests.length }}</span>
				</div>
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					<div v-for="r in couponRequests" :key="r.name"
						class="bg-white rounded-2xl border-2 border-green-200 shadow-sm overflow-hidden flex flex-col">
						<div class="px-5 py-4 border-b border-green-100 bg-green-50 flex items-start justify-between">
							<div>
								<div class="text-sm font-bold text-gray-900">{{ r.customer_name || r.customer }}</div>
								<div class="text-xs text-gray-500 mt-0.5">{{ r.mobile || '' }}<span v-if="r.branch"> — {{ r.branch }}</span></div>
							</div>
							<span class="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-green-100 text-green-800">
								🎟️ {{ r.discount_type === 'Percentage' ? (r.discount_value + '%') : r.discount_value }}
							</span>
						</div>
						<div class="p-4 flex-1 text-sm text-gray-700 space-y-1">
							<div>
								{{ r.discount_type === 'Percentage'
									? __('{0}% discount coupon', [r.discount_value])
									: __('Amount coupon: {0}', [r.discount_value]) }}
								<span v-if="r.include_fees && r.fees_amount"> + {{ __('fees') }} {{ r.fees_amount }}</span>
							</div>
							<div v-if="r.complaint_number" class="text-xs text-gray-400">{{ __('Complaint') }}: {{ r.complaint_number }}</div>
							<div class="text-xs text-gray-400">
								<span v-if="r.max_uses">{{ __('Max uses') }}: {{ r.max_uses }}</span>
								<span v-if="r.valid_upto"> · {{ __('Valid until') }}: {{ r.valid_upto }}</span>
							</div>
							<div class="text-xs text-gray-400">{{ __('By') }}: {{ r.requested_by }}</div>
						</div>
						<div class="px-4 py-3 border-t border-gray-100 flex items-center gap-2 bg-gray-50">
							<button @click="rejectCouponRequest(r)" :disabled="couponBusy === r.name" class="flex-1 px-3 py-2 text-sm font-bold text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-100 disabled:opacity-50">{{ __("Reject") }}</button>
							<button @click="approveCouponRequest(r)" :disabled="couponBusy === r.name" class="flex-1 px-3 py-2 text-sm font-bold text-white bg-green-600 rounded-xl hover:bg-green-700 disabled:opacity-50">{{ __("Approve") }}</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Orders Grid -->
			<div v-else-if="!filteredOrders.length && !failedDeliveries.length && !statusRequests.length && !couponRequests.length" class="flex flex-col items-center justify-center py-24 bg-white rounded-2xl border border-gray-200 shadow-sm text-center px-4">
				<div class="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mb-6">
					<svg class="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
					</svg>
				</div>
				<h2 class="text-xl font-bold text-gray-900 mb-2">{{ __("All Caught Up!") }}</h2>
				<p class="text-gray-500 max-w-sm mx-auto mb-6">{{ __("No pending actions at the moment.") }}</p>
				<button @click="fetchOrders" class="px-5 py-2 text-sm font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors">
					{{ __("Check Again") }}
				</button>
			</div>

			<!-- Call Center Orders Grid -->
			<div v-if="filteredOrders.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				<div
					v-for="order in filteredOrders"
					:key="order.name"
					class="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md hover:border-blue-300 transition-all overflow-hidden flex flex-col"
				>
					<!-- Top Banner -->
					<div class="px-5 py-4 border-b border-gray-100 flex items-start justify-between bg-gradient-to-r from-gray-50 to-white">
						<div>
							<div class="text-sm font-bold text-gray-900 flex items-center gap-1.5">
								<span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
								{{ order.custom_number_order || order.name }}
							</div>
							<div class="text-xs text-gray-400 mt-1 flex items-center gap-1">
								<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
								{{ formatTimeAgo(order.posting_date, order.posting_time) }}
							</div>
						</div>
						<span :class="getOrderTypeClass(order.custom_order_type)" class="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
							{{ order.custom_order_type || "Pickup" }}
						</span>
					</div>

					<!-- Details Section -->
					<div class="p-5 flex-1 space-y-4">
						<!-- Customer Info -->
						<div class="flex items-start gap-3">
							<div class="w-8 h-8 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0 text-blue-600 font-bold text-sm">
								{{ (order.customer_name || "C").charAt(0).toUpperCase() }}
							</div>
							<div>
								<div class="text-sm font-semibold text-gray-900">{{ order.customer_name }}</div>
								<div class="text-xs text-gray-400 mt-0.5">{{ order.customer }}</div>
							</div>
						</div>

						<!-- Branch Info -->
						<div class="flex items-center gap-2 text-xs text-gray-500 bg-gray-50 rounded-lg p-2.5">
							<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
							</svg>
							<span><strong>{{ __("Branch:") }}</strong> {{ order.branch }}</span>
						</div>

						<!-- Items List Preview -->
						<div class="border-t border-gray-100 pt-3">
							<div class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">{{ __("Items Summary") }}</div>
							<div class="space-y-1.5 max-h-32 overflow-y-auto pr-1">
								<div v-for="(item, idx) in order.items" :key="idx" class="flex justify-between items-center text-sm">
									<span class="text-gray-700 truncate max-w-[200px]" :title="item.item_name || item.item_code">
										{{ item.item_name || item.item_code }}
									</span>
									<span class="text-gray-900 font-semibold bg-gray-100 px-2 py-0.5 rounded text-xs">
										x{{ item.qty }}
									</span>
								</div>
							</div>
						</div>
					</div>

					<!-- Bottom Action Area -->
					<div class="px-5 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
						<div>
							<div class="text-xs text-gray-400">{{ __("Total Value") }}</div>
							<div class="text-base font-bold text-gray-900">{{ formatNumber(order.grand_total) }}</div>
						</div>
						<div class="flex items-center gap-2">
							<button
								@click="openRejectDialog(order)"
								class="flex items-center gap-1.5 px-4 py-2 text-sm font-bold text-red-600 bg-red-50 hover:bg-red-100 active:bg-red-200 border border-red-200 rounded-xl transition-all active:scale-95"
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
								</svg>
								{{ __("Reject") }}
							</button>
							<button
								@click="takeAction(order)"
								class="flex items-center gap-1.5 px-4 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 active:bg-blue-800 rounded-xl transition-all shadow-sm shadow-blue-200 active:scale-95"
							>
								{{ __("Take Action") }}
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
								</svg>
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Reject Order Dialog -->
		<div v-if="rejectDialog.show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
			<div class="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
				<div class="px-6 py-5 border-b border-gray-100 flex items-center gap-3">
					<div class="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center flex-shrink-0">
						<svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
						</svg>
					</div>
					<div>
						<h3 class="text-base font-bold text-gray-900">{{ __("Reject Order Payment") }}</h3>
						<p class="text-xs text-gray-500 mt-0.5">{{ rejectDialog.order?.custom_number_order || rejectDialog.order?.name }}</p>
					</div>
				</div>
				<div class="px-6 py-5 space-y-4">
					<p class="text-sm text-gray-600">{{ __("Are you sure you want to reject this order? The invoice will be flagged and removed from the pending list.") }}</p>
					<div>
						<label class="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{{ __("Rejection Reason") }} <span class="text-gray-400 font-normal normal-case">({{ __("optional") }})</span></label>
						<textarea
							v-model="rejectDialog.reason"
							rows="3"
							:placeholder="__('Enter reason for rejecting this order...')"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-red-400 focus:border-red-400 outline-none resize-none transition-all"
						></textarea>
					</div>
				</div>
				<div class="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-3 bg-gray-50">
					<button
						@click="rejectDialog.show = false"
						:disabled="rejectDialog.loading"
						class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg transition-colors disabled:opacity-50"
					>
						{{ __("Cancel") }}
					</button>
					<button
						@click="confirmReject"
						:disabled="rejectDialog.loading"
						class="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50"
					>
						<svg v-if="rejectDialog.loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
						</svg>
						{{ __("Confirm Reject") }}
					</button>
				</div>
			</div>
		</div>

		<!-- Password Confirmation Dialog -->
		<div v-if="showPasswordDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="cancelDelete">
			<div class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
				<div class="px-6 py-4 border-b border-gray-200">
					<h3 class="text-lg font-semibold text-gray-900">{{ __("Confirm Password") }}</h3>
					<p v-if="orderToDelete" class="text-xs text-gray-500 mt-0.5">{{ orderToDelete.custom_number_order || orderToDelete.order_reference }}</p>
				</div>
				<div class="p-6">
					<div class="relative">
						<input
							:ref="el => passwordInputRef = el"
							v-model="passwordInput"
							type="password"
							autocomplete="off"
							:placeholder="__('Enter Password')"
							class="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
							@keyup.enter="confirmDelete"
						/>
					</div>
					<p v-if="passwordError" class="mt-2 text-sm text-red-600">{{ passwordError }}</p>
				</div>
				<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
					<button @click="cancelDelete" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">{{ __("Cancel") }}</button>
					<button @click="confirmDelete" class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700">{{ __("Confirm") }}</button>
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
					<button @click="cancelWastageQuestion" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">{{ __("Cancel") }}</button>
					<button @click="handleNotWastage" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">{{ __("No") }}</button>
					<button @click="handleWastage" class="px-4 py-2 text-sm font-medium text-white bg-amber-500 rounded-lg hover:bg-amber-600">{{ __("Yes, Wastage") }}</button>
				</div>
			</div>
		</div>

		<!-- Wastage Items Dialog -->
		<div v-if="showWastageItems" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="cancelWastageItems">
			<div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
				<div class="px-6 py-4 border-b border-gray-200">
					<h3 class="text-lg font-semibold text-gray-900">{{ __("Select Items for Stock Return") }}</h3>
				</div>
				<div class="p-6 overflow-auto max-h-[60vh] space-y-4">
					<div class="flex items-center gap-6 pb-2">
						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<input type="radio" v-model="wastageStockEntryType" value="Consumptions" class="w-4 h-4 text-amber-600" />
							<span class="font-medium">{{ __("Consumptions") }}</span>
						</label>
						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<input type="radio" v-model="wastageStockEntryType" value="Loaded" class="w-4 h-4 text-blue-600" />
							<span class="font-medium">{{ __("Loaded") }}</span>
						</label>
					</div>
					<div v-if="wastageStockEntryType === 'Loaded'" class="space-y-2 pb-2">
						<label class="block text-xs font-bold text-gray-600 uppercase tracking-wider">{{ __("Select Employee") }} <span class="text-red-500">*</span></label>
						<div class="relative">
							<input v-model="employeeSearch" type="text" :placeholder="__('Search employee...')"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
								@input="searchEmployees" />
							<div v-if="employees.length" class="absolute z-[60] left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-xl max-h-48 overflow-auto">
								<button v-for="emp in employees" :key="emp.name"
									@click="selectedEmployee = emp.name; employeeSearch = emp.employee_name; employees = []"
									class="w-full text-start px-3 py-2 text-sm hover:bg-blue-50 border-b border-gray-50 last:border-0">
									<span class="font-medium text-gray-900">{{ emp.employee_name }}</span>
									<span class="text-xs text-gray-400 ms-2">{{ emp.name }}</span>
								</button>
							</div>
						</div>
					</div>
					<p class="text-sm text-gray-600">{{ __("Select items to return to stock. Unselected items will be marked as wastage.") }}</p>
					<table class="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
						<thead class="bg-gray-50">
							<tr>
								<th class="px-3 py-2 text-start text-xs font-semibold text-gray-600"><input type="checkbox" @change="toggleAllWastageItems($event)" class="rounded" /></th>
								<th class="px-3 py-2 text-start text-xs font-semibold text-gray-600">{{ __("Item") }}</th>
								<th class="px-3 py-2 text-center text-xs font-semibold text-gray-600">{{ __("Original Qty") }}</th>
								<th class="px-3 py-2 text-center text-xs font-semibold text-gray-600">{{ __("Return Qty") }}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<tr v-for="(item, idx) in wastageItems" :key="idx">
								<td class="px-3 py-2"><input type="checkbox" v-model="item.selected" class="rounded" /></td>
								<td class="px-3 py-2 text-gray-700">{{ item.item_name || item.item_code }}</td>
								<td class="px-3 py-2 text-center text-gray-700">{{ item.original_qty }}</td>
								<td class="px-3 py-2 text-center">
									<input v-model.number="item.return_qty" type="number" :max="item.original_qty" :min="0"
										class="w-20 px-2 py-1 border border-gray-300 rounded text-sm text-center focus:ring-2 focus:ring-blue-500 outline-none" />
								</td>
							</tr>
						</tbody>
					</table>
				</div>
				<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
					<button @click="cancelWastageItems" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">{{ __("Cancel") }}</button>
					<button @click="confirmWastageItems" class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700">{{ __("Confirm Cancellation") }}</button>
				</div>
			</div>
		</div>

		<!-- Charge Driver Fee Dialog -->
		<div v-if="showChargeDriverDialog" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
			<div class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
				<div class="px-6 py-4 border-b border-gray-200">
					<h3 class="text-lg font-semibold text-gray-900">{{ __("Charge Driver Fee?") }}</h3>
					<p v-if="orderToDelete?.driver" class="text-xs text-gray-500 mt-0.5">{{ orderToDelete.driver }}</p>
				</div>
				<div class="p-6 space-y-4">
					<p class="text-sm text-gray-700">{{ __("Do you want to charge the driver a fee for this failed delivery?") }}</p>
					<div>
						<label class="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-1">{{ __("Charge Amount") }}</label>
						<input v-model.number="chargeDriverAmount" type="number" min="0" step="0.01"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-red-500 outline-none" />
					</div>
					<div>
						<label class="block text-xs font-bold text-gray-600 uppercase tracking-wider mb-1">{{ __("Notes") }}</label>
						<textarea v-model="chargeDriverNotes" rows="2"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-red-500 outline-none resize-none" />
					</div>
				</div>
				<div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
					<button @click="skipChargeDriver" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
						{{ __("No Charge") }}
					</button>
					<button @click="confirmChargeDriver(true)" :disabled="!chargeDriverAmount || chargeDriverAmount <= 0"
						class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50">
						{{ __("Charge Driver") }}
					</button>
				</div>
			</div>
		</div>

		<!-- Payment Dialog -->
		<PaymentDialog
			v-model="showPaymentDialog"
			:grand-total="cartStore.grandTotal"
			:subtotal="cartStore.subtotal"
			:discount-eligible-subtotal="cartStore.discountEligibleSubtotal"
			:pos-profile="shiftStore.profileName"
			:currency="shiftStore.profileCurrency"
			:is-offline="offlineStore.isOffline"
			:allow-partial-payment="posSettingsStore.allowPartialPayment"
			:allow-credit-sale="posSettingsStore.allowCreditSale"
			:allow-customer-credit-payment="posSettingsStore.allowCustomerCreditPayment"
			:allow-write-off="posSettingsStore.allowWriteOffChange"
			:write-off-limit="shiftStore.writeOffLimit"
			:customer="cartStore.customer"
			:company="shiftStore.profileCompany"
			:additional-discount="cartStore.additionalDiscount"
			:items="cartStore.invoiceItems"
			:tax-amount="cartStore.totalTax"
			:discount-amount="cartStore.totalDiscount"
			:target-doctype="cartStore.targetDoctype"
			:is-submitting="cartStore.isSubmitting"
			@payment-completed="handlePaymentCompleted"
			@update-additional-discount="handleAdditionalDiscountUpdate"
		/>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { useRouter } from "vue-router"
import { usePOSCartStore } from "@/stores/posCart"
import { usePOSUIStore } from "@/stores/posUI"
import { usePOSShiftStore } from "@/stores/posShift"
import { usePOSSettingsStore } from "@/stores/posSettings"
import { usePOSSyncStore } from "@/stores/posSync"
import { useItemSearchStore } from "@/stores/itemSearch"
import { useStockStore } from "@/stores/stock"
import { useToast } from "@/composables/useToast"
import PaymentDialog from "@/components/sale/PaymentDialog.vue"
import { call } from "@/utils/apiWrapper"
import { __ } from "@/utils/translation"
import {
	printInvoiceByName,
	printWithSilentFallback,
} from "@/utils/printInvoice"
import { parseError } from "@/utils/errorHandler"
import { useRealtimeOrders } from "@/composables/useRealtimeOrders"

const router = useRouter()
const cartStore = usePOSCartStore()
const uiStore = usePOSUIStore()
const shiftStore = usePOSShiftStore()
const posSettingsStore = usePOSSettingsStore()
const offlineStore = usePOSSyncStore()
const itemStore = useItemSearchStore()
const stockStore = useStockStore()
const { showSuccess, showError, showWarning } = useToast()

// State
const orders = ref([])
const failedDeliveries = ref([])
const statusRequests = ref([])
const statusBusy = ref(null)
const couponRequests = ref([])
const couponBusy = ref(null)
const loading = ref(false)
const search = ref("")
const orderTypeFilter = ref("all")
const showPaymentDialog = ref(false)
const isSubmittingSuccess = ref(false)
const rejectDialog = ref({ show: false, order: null, reason: "", loading: false })
const posProfile = ref(null)
// Cancel flow (mirrors AllOrders)
const orderToDelete = ref(null)
const approvedManager = ref(null)
const showPasswordDialog = ref(false)
const passwordInput = ref("")
const passwordError = ref("")
const passwordInputRef = ref(null)
const showWastageQuestion = ref(false)
const showWastageItems = ref(false)
const wastageItems = ref([])
const wastageStockEntryType = ref("Consumptions")
const selectedEmployee = ref(null)
const employeeSearch = ref("")
const employees = ref([])
const showChargeDriverDialog = ref(false)
const chargeDriverAmount = ref(0)
const chargeDriverNotes = ref("")
const pendingCancellationArgs = ref(null)

// Actions
const goBack = () => router.push("/")

const openRejectDialog = (order) => {
	rejectDialog.value = { show: true, order, reason: "", loading: false }
}

const confirmReject = async () => {
	rejectDialog.value.loading = true
	try {
		await call("ecs_posnext.api.invoices.reject_order_payment", {
			invoice_name: rejectDialog.value.order.name,
			reason: rejectDialog.value.reason,
		})
		rejectDialog.value.show = false
		showSuccess(__("Order {0} has been rejected", [rejectDialog.value.order.custom_number_order || rejectDialog.value.order.name]))
		await fetchOrders()
	} catch (error) {
		console.error("Failed to reject order:", error)
		showError(__("Failed to reject order"))
	} finally {
		rejectDialog.value.loading = false
	}
}

const fetchOrders = async () => {
	loading.value = true
	try {
		const [r, fd, sr, cr] = await Promise.all([
			call("ecs_posnext.api.invoices.get_need_my_action_orders"),
			call("ecs_posnext.ecs_posnext.api.dispatcher.get_failed_delivery_orders"),
			call("ecs_posnext.api.customer_status.get_pending_customer_status_requests"),
			call("ecs_posnext.api.customers.get_pending_coupon_requests"),
		])
		orders.value = r || []
		failedDeliveries.value = fd || []
		statusRequests.value = sr || []
		couponRequests.value = cr || []
	} catch (error) {
		console.error("Failed to fetch need action orders:", error)
		window.frappe?.show_alert?.({
			message: __("Failed to load pending actions"),
			indicator: "red",
		})
	} finally {
		loading.value = false
	}
}

async function approveStatusRequest(r) {
	if (statusBusy.value) return
	statusBusy.value = r.name
	try {
		await call("ecs_posnext.api.customer_status.approve_customer_status_request", { name: r.name })
		statusRequests.value = statusRequests.value.filter((x) => x.name !== r.name)
		window.frappe?.show_alert?.({ message: __("Approved"), indicator: "green" })
	} catch (e) {
		window.frappe?.show_alert?.({ message: e.message || __("Failed to approve"), indicator: "red" })
	} finally {
		statusBusy.value = null
	}
}

async function rejectStatusRequest(r) {
	if (statusBusy.value) return
	statusBusy.value = r.name
	try {
		await call("ecs_posnext.api.customer_status.reject_customer_status_request", { name: r.name })
		statusRequests.value = statusRequests.value.filter((x) => x.name !== r.name)
		window.frappe?.show_alert?.({ message: __("Rejected"), indicator: "orange" })
	} catch (e) {
		window.frappe?.show_alert?.({ message: e.message || __("Failed to reject"), indicator: "red" })
	} finally {
		statusBusy.value = null
	}
}

async function approveCouponRequest(r) {
	if (couponBusy.value) return
	couponBusy.value = r.name
	try {
		const res = await call("ecs_posnext.api.customers.approve_coupon_request", { name: r.name })
		couponRequests.value = couponRequests.value.filter((x) => x.name !== r.name)
		window.frappe?.show_alert?.({ message: __("Coupon approved: {0}", [res.coupon_code || ""]), indicator: "green" })
	} catch (e) {
		window.frappe?.show_alert?.({ message: e.message || __("Failed to approve"), indicator: "red" })
	} finally {
		couponBusy.value = null
	}
}

async function rejectCouponRequest(r) {
	if (couponBusy.value) return
	couponBusy.value = r.name
	try {
		await call("ecs_posnext.api.customers.reject_coupon_request", { name: r.name })
		couponRequests.value = couponRequests.value.filter((x) => x.name !== r.name)
		window.frappe?.show_alert?.({ message: __("Rejected"), indicator: "orange" })
	} catch (e) {
		window.frappe?.show_alert?.({ message: e.message || __("Failed to reject"), indicator: "red" })
	} finally {
		couponBusy.value = null
	}
}

const loadPosProfile = async () => {
	try {
		const result = await call("ecs_posnext.api.shifts.check_opening_shift", {
			user: window.frappe?.session?.user || "",
		})
		if (result && result.pos_profile) posProfile.value = result.pos_profile
	} catch {}
}

// Cancel flow — mirrors AllOrders exactly
const deleteDeliveryOrder = (delivery) => {
	orderToDelete.value = delivery
	passwordInput.value = ""
	passwordError.value = ""
	showPasswordDialog.value = true
}

const confirmDelete = async () => {
	passwordError.value = ""
	try {
		const res = await call("ecs_posnext.api.kitchen_order.verify_cancel_manager", {
			pos_profile: posProfile.value?.name || posProfile.value || "",
			password: passwordInput.value,
		})
		if (res && res.valid) {
			approvedManager.value = res.manager || null
			showPasswordDialog.value = false
			showWastageQuestion.value = true
		} else {
			passwordError.value = __("Password is incorrect. Please try again.")
		}
	} catch (error) {
		console.error("Manager verification failed:", error)
		passwordError.value = __("Password is incorrect. Please try again.")
	}
}

const cancelDelete = () => {
	showPasswordDialog.value = false
	passwordInput.value = ""
	passwordError.value = ""
	orderToDelete.value = null
}

const cancelWastageQuestion = () => {
	showWastageQuestion.value = false
	orderToDelete.value = null
}

const handleNotWastage = () => {
	showWastageQuestion.value = false
	pendingCancellationArgs.value = { isWastage: false, itemsToReturn: [], wastageItemsList: [] }
	chargeDriverAmount.value = 0
	chargeDriverNotes.value = ""
	showChargeDriverDialog.value = true
}

const handleWastage = async () => {
	showWastageQuestion.value = false
	await loadOrderItemsForWastage()
}

const loadOrderItemsForWastage = async () => {
	try {
		const result = await call("ecs_posnext.api.kitchen_order.get_stock_items_for_wastage", {
			sales_invoice: orderToDelete.value?.order_reference,
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
	} catch {
		showError(__("Failed to load items for wastage"))
	}
}

const cancelWastageItems = () => {
	showWastageItems.value = false
	wastageItems.value = []
	orderToDelete.value = null
}

const toggleAllWastageItems = (event) => {
	wastageItems.value.forEach(item => { item.selected = event.target.checked })
}

const confirmWastageItems = async () => {
	const selectedItems = wastageItems.value.filter(i => i.selected)
	const selectedCodes = new Set(selectedItems.map(i => i.item_code))
	const wastageItemsList = wastageItems.value
		.filter(item => !selectedCodes.has(item.item_code))
		.map(item => ({ item_code: item.item_code, qty: item.qty, uom: item.uom, warehouse: item.warehouse }))
	selectedItems.forEach(item => {
		const wastageQty = item.original_qty - (item.return_qty || 0)
		if (wastageQty > 0) wastageItemsList.push({ item_code: item.item_code, qty: wastageQty, uom: item.uom, warehouse: item.warehouse })
	})
	const itemsToReturn = selectedItems
		.map(item => ({ item_code: item.item_code, qty: item.return_qty || item.qty, uom: item.uom }))
		.filter(item => item.qty > 0)
	showWastageItems.value = false
	pendingCancellationArgs.value = { isWastage: true, itemsToReturn, wastageItemsList }
	chargeDriverAmount.value = 0
	chargeDriverNotes.value = ""
	showChargeDriverDialog.value = true
}

const confirmChargeDriver = async (charge) => {
	showChargeDriverDialog.value = false
	const assignmentName = orderToDelete.value?.name
	const { isWastage, itemsToReturn, wastageItemsList } = pendingCancellationArgs.value
	await proceedWithCancellation(isWastage, itemsToReturn, wastageItemsList)
	if (charge && chargeDriverAmount.value > 0 && assignmentName) {
		try {
			await call("ecs_posnext.ecs_posnext.api.dispatcher.record_driver_charge", {
				assignment: assignmentName,
				amount: chargeDriverAmount.value,
				notes: chargeDriverNotes.value,
			})
		} catch {}
	}
	pendingCancellationArgs.value = null
}

const skipChargeDriver = () => {
	showChargeDriverDialog.value = false
	confirmChargeDriver(false)
}

const proceedWithCancellation = async (isWastage, itemsToReturn = [], wastageItemsList = []) => {
	try {
		await call("ecs_posnext.api.kitchen_order.cancel_sales_invoice_with_wastage", {
			sales_invoice: orderToDelete.value?.order_reference,
			is_wastage: isWastage,
			items_to_return: JSON.stringify(itemsToReturn),
			wastage_items: JSON.stringify(wastageItemsList),
			stock_entry_type: wastageStockEntryType.value,
			employee: selectedEmployee.value,
			cancelled_by_manager: approvedManager.value,
		})
		// Mark the Delivery Assignment as Returned
		await call("ecs_posnext.ecs_posnext.api.dispatcher.mark_assignment_returned", {
			assignment: orderToDelete.value?.name,
		})
		let msg = __("Order cancelled successfully.")
		if (isWastage && wastageItemsList.length > 0) msg += " " + __("Stock entry created for wastage items.")
		window.frappe?.msgprint?.(msg)
		await fetchOrders()
	} catch (error) {
		showError(__("Error cancelling order."))
	} finally {
		wastageItems.value = []
		orderToDelete.value = null
		approvedManager.value = null
		wastageStockEntryType.value = "Consumptions"
		selectedEmployee.value = null
	}
}

const searchEmployees = async () => {
	if (!employeeSearch.value || employeeSearch.value.length < 2) { employees.value = []; return }
	try {
		const result = await call("frappe.desk.search.search_link", {
			txt: employeeSearch.value, doctype: "Employee", ignore_user_permissions: 0,
			reference_doctype: "Sales Invoice", filters: JSON.stringify({ status: "Active" }), page_length: 20,
		})
		employees.value = (result || []).map(r => ({ name: r.value, employee_name: r.description || r.value }))
	} catch { employees.value = [] }
}

const takeAction = async (order) => {
	loading.value = true
	try {
		// Fetch full invoice details from backend to ensure we have all values
		const fullInvoice = await call("ecs_posnext.api.invoices.get_invoice", {
			invoice_name: order.name,
		})

		if (fullInvoice) {
			await cartStore.resumeInvoice(fullInvoice)
			showPaymentDialog.value = true
		} else {
			window.frappe?.show_alert?.({
				message: __("Could not fetch draft details"),
				indicator: "red",
			})
		}
	} catch (error) {
		console.error("Failed to resume invoice:", error)
		window.frappe?.show_alert?.({
			message: __("Failed to resume invoice"),
			indicator: "red",
		})
	} finally {
		loading.value = false
	}
}

const handlePaymentCompleted = async (paymentData) => {
	try {
		const customerValue = cartStore.customer?.name || cartStore.customer
		if (!customerValue && !shiftStore.profileCustomer) {
			showWarning(__("Please select a customer before proceeding"))
			showPaymentDialog.value = false
			return
		}

		cartStore.payments = []
		if (paymentData.payments && Array.isArray(paymentData.payments)) {
			paymentData.payments.forEach((p) => {
				cartStore.payments.push({
					mode_of_payment: p.mode_of_payment,
					amount: p.amount,
					type: p.type,
				})
			})
		}

		// Store sales team data if provided
		if (paymentData.sales_team && Array.isArray(paymentData.sales_team)) {
			cartStore.salesTeam = paymentData.sales_team
		} else {
			cartStore.salesTeam = []
		}

		// Set delivery date for Sales Orders
		if (paymentData.delivery_date) {
			cartStore.setDeliveryDate(paymentData.delivery_date)
		}

		// Set write-off amount if provided
		if (paymentData.write_off_amount && paymentData.write_off_amount > 0) {
			cartStore.setWriteOffAmount(paymentData.write_off_amount)
		}

		// Custom Fields
		cartStore.setCustomReceiptNumber(paymentData.custom_receipt_number || "")
		cartStore.setCustomUniqueTalbatNumber(
			paymentData.custom_unique_talbat_number || "",
		)
		cartStore.setCustomThirdPartyReferanceNumber(
			paymentData.custom_third_party_referance_number || "",
		)
		cartStore.setCustomPaymentType(paymentData.custom_payment_type || "")

		// Get item codes from cart before clearing
		const soldItemCodes = cartStore.invoiceItems.map((item) => item.item_code)

		isSubmittingSuccess.value = true
		const result = await cartStore.submitInvoice(true)

		if (result) {
			const invoiceName = result.name || result.message?.name || __("Unknown")
			const invoiceTotal = result.grand_total || result.total || 0
			const paidAmount = paymentData.paid_amount || invoiceTotal

			showPaymentDialog.value = false
			cartStore.clearCart()

			// Refresh stock
			try {
				await stockStore.refresh(soldItemCodes, shiftStore.profileWarehouse)
			} catch (stockErr) {
				console.error("Failed to refresh stock:", stockErr)
			}

			// Print if auto-print or silent print is enabled
			if (shiftStore.autoPrintEnabled || posSettingsStore.silentPrint) {
				try {
					await handlePrintInvoice({ name: invoiceName })
					showSuccess(
						__("Invoice {0} created and sent to printer", [invoiceName]),
					)
				} catch (error) {
					console.error("Auto-print error:", error)
					showWarning(__("Invoice {0} created but print failed", [invoiceName]))
				}
			} else {
				showSuccess(__("Invoice {0} created successfully", [invoiceName]))
			}

			// Refresh the pending actions list
			await fetchOrders()
		}
	} catch (error) {
		console.error("Error submitting invoice:", error)
		showPaymentDialog.value = false
		cartStore.clearCart()

		const errorContext = parseError(error)
		if (errorContext.type === "error") {
			showError(errorContext.message)
		} else if (errorContext.type === "warning") {
			showWarning(errorContext.message)
		} else {
			showWarning(errorContext.message)
		}
	} finally {
		isSubmittingSuccess.value = false
	}
}

const handleAdditionalDiscountUpdate = (discountAmount) => {
	cartStore.additionalDiscount = discountAmount
	cartStore.rebuildIncrementalCache()
}

const handlePrintInvoice = async (invoiceData) => {
	try {
		if (posSettingsStore.silentPrint) {
			await printWithSilentFallback(invoiceData)
			return
		}
		await printInvoiceByName(invoiceData.name)
	} catch (error) {
		console.error("Error printing invoice:", error)
		window.frappe?.msgprint({
			title: "Error",
			message: "Failed to print invoice",
			indicator: "red",
		})
	}
}

watch(showPaymentDialog, (val) => {
	if (!val && !isSubmittingSuccess.value) {
		cartStore.clearCart()
	}
})

// Filters & Helpers
const filteredOrders = computed(() => {
	let data = orders.value.slice()

	if (orderTypeFilter.value !== "all") {
		data = data.filter((o) => o.custom_order_type === orderTypeFilter.value)
	}

	if (search.value) {
		const s = search.value.toLowerCase()
		data = data.filter(
			(o) =>
				(o.custom_number_order || o.name).toLowerCase().includes(s) ||
				(o.customer_name || "").toLowerCase().includes(s) ||
				(o.customer || "").toLowerCase().includes(s) ||
				(o.branch || "").toLowerCase().includes(s) ||
				o.items.some((item) =>
					(item.item_name || item.item_code || "").toLowerCase().includes(s),
				),
		)
	}

	return data
})

const orderTypes = computed(() => {
	const set = new Set(
		orders.value.map((o) => o.custom_order_type).filter(Boolean),
	)
	return Array.from(set).sort()
})

const getOrderTypeClass = (type) => {
	const t = (type || "").toLowerCase()
	if (t.includes("delivery")) return "bg-teal-100 text-teal-800"
	if (t.includes("talabat")) return "bg-pink-100 text-pink-800"
	return "bg-blue-100 text-blue-800"
}

const formatNumber = (val) => {
	return new Intl.NumberFormat(undefined, {
		style: "currency",
		currency: "EGP",
	}).format(val)
}

const formatTimeAgo = (dateStr, timeStr) => {
	if (!dateStr || !timeStr) return ""
	try {
		const dateObj = new Date(`${dateStr}T${timeStr}`)
		const diffMs = new Date() - dateObj
		const diffMins = Math.floor(diffMs / 60000)

		if (diffMins < 1) return __("Just now")
		if (diffMins < 60) return __("{0}m ago", { 0: String(diffMins) })

		const diffHours = Math.floor(diffMins / 60)
		if (diffHours < 24) return __("{0}h ago", { 0: String(diffHours) })

		return dateStr
	} catch (e) {
		return `${dateStr} ${timeStr}`
	}
}

// ── New-action alert (sound + notification) ────────────────────────────────────
// Total number of items currently awaiting the cashier's action.
const pendingCount = computed(
	() => orders.value.length + failedDeliveries.value.length + statusRequests.value.length,
)

function playNewActionSound() {
	try {
		const ctx = new (window.AudioContext || window.webkitAudioContext)()
		;[{ freq: 880, start: 0, dur: 0.12 }, { freq: 1100, start: 0.13, dur: 0.12 }, { freq: 1320, start: 0.26, dur: 0.2 }].forEach(({ freq, start, dur }) => {
			const osc = ctx.createOscillator(), gain = ctx.createGain()
			osc.connect(gain); gain.connect(ctx.destination)
			osc.type = "sine"; osc.frequency.value = freq
			gain.gain.setValueAtTime(0.4, ctx.currentTime + start)
			gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + dur)
			osc.start(ctx.currentTime + start); osc.stop(ctx.currentTime + start + dur + 0.05)
		})
	} catch {}
}

// Watch the pending count; alert (sound + toast) whenever new work arrives so
// orders are not left waiting. First load (prev = -1) is silent.
let prevPendingCount = -1
watch(pendingCount, (count) => {
	if (prevPendingCount >= 0 && count > prevPendingCount) {
		playNewActionSound()
		const added = count - prevPendingCount
		showWarning(
			added > 1
				? __("{0} new orders need your action", [String(added)])
				: __("New order needs your action"),
		)
	}
	prevPendingCount = count
})

// ── Realtime ──────────────────────────────────────────────────────────────────
const { onOrderChanged } = useRealtimeOrders()

const COUPON_EVENT = "coupon_request_changed"
let realtimeRefreshTimer = null
let unsubscribeOrders = null
let couponListenerBound = false
let couponRetryTimer = null

function scheduleRealtimeRefresh() {
	clearTimeout(realtimeRefreshTimer)
	realtimeRefreshTimer = setTimeout(() => fetchOrders(), 800)
}

// Compensation coupon requests aren't part of pos_order_changed, so subscribe
// to their own broadcast event. Retry until the socket is ready (bootstrap is
// async, exactly like useRealtimeOrders does for orders).
function bindCouponListener() {
	if (couponListenerBound) return
	if (!window.frappe?.realtime) {
		clearTimeout(couponRetryTimer)
		couponRetryTimer = setTimeout(bindCouponListener, 400)
		return
	}
	clearTimeout(couponRetryTimer)
	couponRetryTimer = null
	window.frappe.realtime.on(COUPON_EVENT, scheduleRealtimeRefresh)
	couponListenerBound = true
}

onMounted(async () => {
	await shiftStore.checkShift()
	fetchOrders()
	loadPosProfile()
	if (!cartStore.posProfile && shiftStore.profileName) {
		cartStore.posProfile = shiftStore.profileName
		cartStore.posOpeningShift = shiftStore.currentShift?.name
	}
	unsubscribeOrders = onOrderChanged(scheduleRealtimeRefresh)
	bindCouponListener()
})

onUnmounted(() => {
	unsubscribeOrders?.()
	clearTimeout(realtimeRefreshTimer)
	clearTimeout(couponRetryTimer)
	try { window.frappe?.realtime?.off?.(COUPON_EVENT, scheduleRealtimeRefresh) } catch { /* noop */ }
})
</script>

<style scoped>
.grid {
	display: grid;
}
.transition-all {
	transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
