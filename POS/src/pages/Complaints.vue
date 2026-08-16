<template>
	<div class="flex flex-col h-full bg-gray-50">
		<!-- Header -->
		<div class="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200 shadow-sm flex-shrink-0">
			<div class="flex items-center gap-3">
				<button
					@click="router.push({ name: 'POSSale' })"
					class="p-2 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
					:title="__('Back to POS')"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
					</svg>
				</button>
				<div>
					<h1 class="text-lg font-bold text-gray-900">{{ __("Customer Complaints") }}</h1>
					<p class="text-xs text-gray-500">{{ filteredComplaints.length }} {{ __("complaint(s)") }}</p>
				</div>
			</div>

			<div class="flex items-center gap-2">
				<!-- View toggle -->
				<div class="flex bg-gray-100 rounded-lg p-0.5">
					<button
						@click="activeView = 'list'"
						:class="activeView === 'list' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
						class="px-3 h-7 text-xs font-bold rounded-md transition-all"
					>{{ __("All") }}</button>
					<button
						@click="activeView = 'report'; loadDailyReport()"
						:class="activeView === 'report' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
						class="px-3 h-7 text-xs font-bold rounded-md transition-all flex items-center gap-1"
					>
						<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
						{{ __("Daily Report") }}
					</button>
				</div>

				<template v-if="activeView === 'list'">
					<!-- Status filter -->
					<select
						v-model="filterStatus"
						class="h-9 px-3 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
					>
						<option value="">{{ __("All Status") }}</option>
						<option v-for="s in COMPLAINT_STATUSES" :key="s" :value="s">{{ __(s) }}</option>
					</select>

					<!-- Search -->
					<div class="relative">
						<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
						<input
							v-model="search"
							type="text"
							:placeholder="__('Search customer or number...')"
							class="h-9 pl-9 pr-3 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-400 w-52"
						/>
					</div>
				</template>

				<template v-if="activeView === 'report'">
					<!-- Date picker for report -->
					<input
						v-model="reportDate"
						type="date"
						@change="loadDailyReport"
						class="h-9 px-3 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-400"
					/>
				</template>

				<!-- New Complaint -->
				<button
					v-if="!isCashier"
					@click="openNewDialog"
					class="h-9 px-4 bg-blue-600 text-white text-sm font-bold rounded-lg hover:bg-blue-700 transition-all flex items-center gap-2 active:scale-95"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
					{{ __("New Complaint") }}
				</button>
			</div>
		</div>

		<!-- Loading -->
		<div v-if="loading || reportLoading" class="flex items-center justify-center flex-1">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
		</div>

		<!-- ===== DAILY REPORT VIEW ===== -->
		<div v-else-if="activeView === 'report' && report" class="flex-1 overflow-auto px-6 py-4 space-y-4">
			<!-- Report date title -->
			<div class="flex items-center gap-2">
				<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
				</svg>
				<h2 class="text-sm font-bold text-gray-700">{{ __("Report for") }}: {{ formatDateFull(report.date) }}</h2>
			</div>

			<!-- Summary cards -->
			<div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-9 gap-3">
				<div class="bg-white rounded-xl border border-gray-200 p-4 text-center shadow-sm">
					<p class="text-2xl font-bold text-gray-900">{{ report.summary.total }}</p>
					<p class="text-xs text-gray-500 mt-1">{{ __("Total") }}</p>
				</div>
				<div v-for="s in COMPLAINT_STATUSES" :key="s" class="bg-gray-50 rounded-xl border border-gray-200 p-4 text-center shadow-sm">
					<p class="text-2xl font-bold" :class="statusTextClass(s)">{{ report.summary[s] || 0 }}</p>
					<p class="text-xs mt-1 text-gray-500">{{ __(s) }}</p>
				</div>
			</div>

			<!-- By type breakdown -->
			<div v-if="report.by_type.length > 0" class="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
				<p class="text-xs font-bold text-gray-500 uppercase mb-3">{{ __("By Problem Type") }}</p>
				<div class="space-y-2">
					<div v-for="item in report.by_type" :key="item.type" class="flex items-center gap-3">
						<span class="text-xs text-gray-700 w-32 truncate">{{ item.type }}</span>
						<div class="flex-1 bg-gray-100 rounded-full h-2">
							<div
								class="bg-blue-500 h-2 rounded-full transition-all"
								:style="{ width: (report.summary.total ? (item.count / report.summary.total) * 100 : 0) + '%' }"
							></div>
						</div>
						<span class="text-xs font-bold text-gray-600 w-6 text-right">{{ item.count }}</span>
					</div>
				</div>
			</div>

			<!-- Daily complaints list -->
			<div v-if="report.complaints.length > 0" class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
				<div class="px-4 py-3 border-b border-gray-100 bg-gray-50">
					<p class="text-xs font-bold text-gray-500 uppercase">{{ __("Complaint Details") }}</p>
				</div>
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-gray-100">
							<th class="px-4 py-2 text-left text-xs font-bold text-gray-500">{{ __("Number") }}</th>
							<th class="px-4 py-2 text-left text-xs font-bold text-gray-500">{{ __("Customer") }}</th>
							<th class="px-4 py-2 text-left text-xs font-bold text-gray-500">{{ __("Type") }}</th>
							<th class="px-4 py-2 text-left text-xs font-bold text-gray-500">{{ __("Response By") }}</th>
							<th class="px-4 py-2 text-left text-xs font-bold text-gray-500">{{ __("Status") }}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-50">
						<tr v-for="c in report.complaints" :key="c.name" class="hover:bg-gray-50">
							<td class="px-4 py-2 text-xs font-bold text-gray-700">{{ c.custom_complaint_number || c.name }}</td>
							<td class="px-4 py-2">
								<p class="text-xs font-medium text-gray-800">{{ c.customer_name || c.customer }}</p>
								<p v-if="c.custome_phone" class="text-[10px] text-gray-400">{{ c.custome_phone }}</p>
							</td>
							<td class="px-4 py-2">
								<span v-if="c.type" class="px-2 py-0.5 bg-blue-50 text-blue-700 text-[10px] font-bold rounded-full">{{ c.type }}</span>
								<span v-else class="text-gray-300 text-xs">—</span>
							</td>
							<td class="px-4 py-2">
								<span v-if="c.custom_response_by" class="text-xs" :class="isOverdue(c.custom_response_by) ? 'text-red-600 font-bold' : 'text-gray-600'">
									{{ formatDateTime(c.custom_response_by) }}
								</span>
								<span v-else class="text-gray-300 text-xs">—</span>
							</td>
							<td class="px-4 py-2">
								<span class="px-2 py-0.5 text-[10px] font-bold rounded-full" :class="statusBadgeClass(c.status)">{{ c.status }}</span>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div v-else class="text-center py-8 text-gray-400">
				<p class="text-sm">{{ __("No complaints on this date") }}</p>
			</div>
		</div>

		<!-- Empty (list view) -->
		<div v-else-if="activeView === 'list' && filteredComplaints.length === 0" class="flex flex-col items-center justify-center flex-1 text-gray-400">
			<svg class="w-16 h-16 mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
			</svg>
			<p class="text-sm">{{ __("No complaints found") }}</p>
		</div>

		<!-- Table (list view) -->
		<div v-else-if="activeView === 'list'" class="flex-1 overflow-auto px-6 py-4">
			<div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
				<table class="w-full text-sm">
					<thead>
						<tr class="bg-gray-50 border-b border-gray-200">
							<th class="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Number") }}</th>
							<th class="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Customer") }}</th>
							<th class="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Type") }}</th>
							<th class="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Details") }}</th>
							<th class="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Created By") }}</th>
							<th class="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Branch") }}</th>
							<th class="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Response By") }}</th>
							<th class="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Status") }}</th>
							<th class="px-4 py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-wide">{{ __("Actions") }}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-100">
						<tr
							v-for="c in filteredComplaints"
							:key="c.name"
							class="hover:bg-gray-50 transition-colors cursor-pointer"
							@click="openDetail(c)"
						>
							<!-- Number -->
							<td class="px-4 py-3">
								<span class="font-bold text-gray-900 text-sm">{{ c.custom_complaint_number || c.name }}</span>
							</td>

							<!-- Customer -->
							<td class="px-4 py-3">
								<p class="font-medium text-gray-900 text-sm">{{ c.customer_name || c.customer }}</p>
								<p v-if="c.custome_phone" class="text-xs text-gray-500">{{ c.custome_phone }}</p>
							</td>

							<!-- Type -->
							<td class="px-4 py-3">
								<span v-if="c.type" class="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-bold rounded-full">{{ c.type }}</span>
								<span v-else class="text-gray-300 text-sm">—</span>
							</td>

							<!-- Details -->
							<td class="px-4 py-3 max-w-[200px]">
								<p class="text-sm text-gray-700 truncate">{{ c.complaint_details }}</p>
							</td>

							<!-- Created By -->
							<td class="px-4 py-3">
								<p class="text-sm text-gray-900 truncate max-w-[120px]" :title="c.owner">{{ (c.owner || '').split('@')[0] || '—' }}</p>
							</td>

							<!-- Branch -->
							<td class="px-4 py-3">
								<span v-if="c.branch" class="text-sm text-gray-900 font-medium">{{ c.branch }}</span>
								<span v-else class="text-gray-300 text-sm">—</span>
							</td>

							<!-- Response By -->
							<td class="px-4 py-3">
								<div v-if="c.custom_response_by">
									<p class="text-sm font-medium" :class="isOverdue(c.custom_response_by) && c.status === 'New' ? 'text-red-600' : 'text-gray-700'">
										{{ formatDateTime(c.custom_response_by) }}
									</p>
									<p v-if="isOverdue(c.custom_response_by) && c.status === 'New'" class="text-xs text-red-500 font-bold">{{ __("Overdue") }}</p>
									<p v-else-if="c.status === 'New'" class="text-xs text-gray-400">{{ timeUntil(c.custom_response_by) }}</p>
								</div>
								<span v-else class="text-gray-300 text-sm">—</span>
							</td>

							<!-- Status badge -->
							<td class="px-4 py-3">
								<span class="px-2 py-0.5 text-xs font-bold rounded-full" :class="statusBadgeClass(c.status)">{{ c.status }}</span>
							</td>

							<!-- Open -->
							<td class="px-4 py-3 text-center" @click.stop>
								<button
									@click="openDetail(c)"
									class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
									:title="__('Open Details')"
								>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
									</svg>
								</button>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>

		<!-- New Complaint Dialog -->
		<Teleport to="body">
			<div v-if="dialog.show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
				<div class="bg-white rounded-2xl shadow-2xl w-full max-w-md">
					<!-- Dialog Header -->
					<div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
						<h2 class="text-base font-bold text-gray-900">{{ __("New Customer Complaint") }}</h2>
						<button @click="dialog.show = false" class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>

					<!-- Dialog Body -->
					<div class="px-6 py-4 space-y-4">
						<!-- Customer Search -->
						<div>
							<label class="block text-xs font-bold text-gray-600 mb-1">{{ __("Customer") }} <span class="text-red-500">*</span></label>
							<div class="relative">
								<input
									v-model="dialog.customerSearch"
									type="text"
									:placeholder="__('Search by name or mobile...')"
									class="w-full h-9 px-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
									@input="searchCustomers"
									@focus="dialog.showCustomerDropdown = true"
								/>
								<div
									v-if="dialog.showCustomerDropdown && dialog.customerResults.length > 0"
									class="absolute top-full left-0 right-0 z-10 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
								>
									<button
										v-for="cust in dialog.customerResults"
										:key="cust.name"
										@click="selectCustomer(cust)"
										class="w-full text-left px-3 py-2 hover:bg-blue-50 transition-colors"
									>
										<p class="text-sm font-medium text-gray-800">{{ cust.customer_name }}</p>
										<p v-if="cust.mobile_no" class="text-xs text-gray-400">{{ cust.mobile_no }}</p>
									</button>
								</div>
							</div>
							<p v-if="dialog.selectedCustomer" class="mt-1 text-xs text-green-600 font-medium">
								✓ {{ dialog.selectedCustomer.customer_name }}
							</p>
						</div>

						<!-- Related Order (optional) -->
						<div>
							<label class="block text-xs font-bold text-gray-600 mb-1">{{ __("Related Order") }} <span class="text-gray-400 font-normal">({{ __("optional") }})</span></label>
							<div class="flex gap-2">
								<input
									v-model="dialog.orderReference"
									type="text"
									:placeholder="__('Sales Invoice number...')"
									class="flex-1 h-9 px-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
									@keyup.enter="loadOrderContext"
								/>
								<button
									type="button"
									@click="loadOrderContext"
									:disabled="!dialog.orderReference || dialog.loadingOrder"
									class="px-3 h-9 text-xs font-bold bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
								>{{ dialog.loadingOrder ? __("Loading...") : __("Load") }}</button>
							</div>
							<div v-if="dialog.orderContext" class="mt-2 p-3 bg-gray-50 border border-gray-100 rounded-lg text-[11px] text-gray-600 grid grid-cols-2 gap-x-3 gap-y-1">
								<span>{{ __("Order Number") }}: <b>{{ dialog.orderContext.order_number || "—" }}</b></span>
								<span>{{ __("Customer") }}: <b>{{ dialog.orderContext.customer || "—" }}</b></span>
								<span>{{ __("Branch") }}: <b>{{ dialog.orderContext.branch || "—" }}</b></span>
								<span>{{ __("Order Status") }}: <b>{{ dialog.orderContext.order_status || "—" }}</b></span>
								<span>{{ __("Order Date & Time") }}: <b>{{ formatDateTime(dialog.orderContext.order_datetime) || "—" }}</b></span>
								<span>{{ __("Delivery Type") }}: <b>{{ dialog.orderContext.delivery_type || "—" }}</b></span>
								<span>{{ __("Business Day") }}: <b>{{ dialog.orderContext.pos_business_day || "—" }}</b></span>
								<span>{{ __("Cashier Shift") }}: <b>{{ dialog.orderContext.pos_cashier_shift || "—" }}</b></span>
								<span>{{ __("Assigned Delivery") }}: <b>{{ dialog.orderContext.assigned_delivery || "—" }}</b></span>
							</div>
						</div>

						<!-- Complaint Type -->
						<div>
							<label class="block text-xs font-bold text-gray-600 mb-1">{{ __("Problem Type") }} <span class="text-red-500">*</span></label>
							<select
								v-model="dialog.type"
								class="w-full h-9 px-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
							>
								<option value="">{{ __("Select type...") }}</option>
								<option v-for="ct in complaintTypes" :key="ct.name" :value="ct.name">{{ ct.name }}</option>
							</select>
						</div>

						<!-- Branch -->
						<div>
							<label class="block text-xs font-bold text-gray-600 mb-1">{{ __("Branch") }} <span class="text-red-500">*</span></label>
							<select
								v-model="dialog.branch"
								class="w-full h-9 px-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
							>
								<option value="">{{ __("Select branch...") }}</option>
								<option v-for="b in branches" :key="b.name" :value="b.name">{{ b.name }}</option>
							</select>
						</div>

						<!-- Response By -->
						<div>
							<label class="block text-xs font-bold text-gray-600 mb-1">{{ __("Response Deadline") }} <span class="text-red-500">*</span></label>
							<input
								v-model="dialog.responseBy"
								type="datetime-local"
								class="w-full h-9 px-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
							/>
						</div>

						<!-- Details -->
						<div>
							<label class="block text-xs font-bold text-gray-600 mb-1">{{ __("Complaint Details") }}</label>
							<textarea
								v-model="dialog.details"
								:placeholder="__('Describe the issue...')"
								rows="3"
								class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
							/>
						</div>
					</div>

					<!-- Dialog Footer -->
					<div class="flex justify-end gap-3 px-6 py-4 border-t border-gray-100">
						<button
							@click="dialog.show = false"
							class="px-4 h-9 text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors font-medium"
						>
							{{ __("Cancel") }}
						</button>
						<button
							@click="submitNewComplaint"
							:disabled="!canSubmit || dialog.submitting"
							class="px-5 h-9 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-all font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
						>
							<svg v-if="dialog.submitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
							</svg>
							{{ dialog.submitting ? __("Saving...") : __("Save Complaint") }}
						</button>
					</div>
				</div>
			</div>
		</Teleport>

		<!-- ===== DETAIL DRAWER ===== -->
		<Teleport to="body">
			<Transition name="fade">
				<div v-if="drawer.show" class="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" @click="closeDrawer" />
			</Transition>
			<Transition name="slide-right">
				<div v-if="drawer.show" class="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-white shadow-2xl flex flex-col">

					<!-- Header -->
					<div class="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gray-50 flex-shrink-0">
						<div class="flex items-center gap-2 min-w-0">
							<span class="text-xs font-bold text-gray-400 uppercase shrink-0">{{ __("Complaint") }}</span>
							<span class="text-sm font-bold text-gray-900 truncate">{{ drawer.data?.custom_complaint_number || drawer.data?.name }}</span>
							<span
								class="px-2 py-0.5 text-[10px] font-bold rounded-full shrink-0"
								:class="statusBadgeClass(drawer.form.status)"
							>{{ drawer.form.status }}</span>
						</div>
						<button @click="closeDrawer" class="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-200 rounded-lg transition-colors shrink-0">
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					</div>

					<!-- Loading -->
					<div v-if="drawer.loading" class="flex items-center justify-center flex-1">
						<div class="animate-spin rounded-full h-7 w-7 border-b-2 border-blue-500"></div>
					</div>

					<!-- Body -->
					<div v-else class="flex-1 overflow-y-auto pb-4">

						<!-- Customer card -->
						<div class="mx-5 mt-4 p-4 bg-blue-50 rounded-xl border border-blue-100">
							<div class="flex items-start justify-between gap-3">
								<div>
									<p class="text-sm font-bold text-gray-900">{{ drawer.data?.customer_name }}</p>
									<p v-if="drawer.data?.custome_phone" class="text-xs text-gray-500 mt-0.5">{{ drawer.data.custome_phone }}</p>
								</div>
								<div class="text-right text-[10px] text-gray-400 shrink-0">
									<p>{{ formatDateTime(drawer.data?.complaint_date) }}</p>
									<p class="mt-0.5">{{ drawer.data?.owner }}</p>
								</div>
							</div>
						</div>

						<!-- Approved compensation coupons — any agent can read these out and apply at checkout -->
						<div v-if="drawer.compensationCoupons.length" class="mx-5 mt-4 space-y-2">
							<p class="text-[10px] font-bold text-emerald-700 uppercase">{{ __("Available Compensation Coupon(s)") }}</p>
							<div
								v-for="cc in drawer.compensationCoupons"
								:key="cc.name"
								class="flex items-center justify-between gap-3 p-3 bg-emerald-50 border border-emerald-200 rounded-xl"
							>
								<div class="min-w-0">
									<p class="text-sm font-bold text-emerald-800 tracking-wide">{{ cc.coupon_code }}</p>
									<p class="text-[10px] text-emerald-600">
										{{ cc.discount_type === 'Percentage' ? `${cc.discount_percentage}%` : formatCurrency(cc.discount_amount) }}
										<span v-if="cc.valid_upto"> · {{ __("Expires") }} {{ formatDate(cc.valid_upto) }}</span>
										<span v-if="cc.complaint_number"> · {{ cc.complaint_number }}</span>
									</p>
								</div>
								<button
									@click="copyCode(cc.coupon_code)"
									class="px-2.5 h-7 text-[10px] font-bold text-emerald-700 bg-white border border-emerald-300 rounded-lg hover:bg-emerald-100 transition-colors shrink-0"
								>{{ __("Copy Code") }}</button>
							</div>
						</div>

						<!-- Linked Order -->
						<div v-if="drawer.data?.custom_order_reference" class="mx-5 mt-4">
							<p class="text-[10px] font-bold text-gray-500 uppercase mb-1.5">{{ __("Linked Order") }}</p>
							<div class="bg-indigo-50 border border-indigo-100 rounded-lg p-3 text-[11px] text-gray-700 grid grid-cols-2 gap-x-3 gap-y-1.5">
								<span>{{ __("Order Number") }}: <b>{{ drawer.data.custom_order_reference }}</b></span>
								<span>{{ __("Customer") }}: <b>{{ drawer.data.order_context?.customer || drawer.data.customer_name || "—" }}</b></span>
								<span>{{ __("Branch") }}: <b>{{ drawer.data.order_context?.branch || "—" }}</b></span>
								<span>{{ __("Order Status") }}: <b>{{ drawer.data.order_context?.order_status || "—" }}</b></span>
								<span>{{ __("Order Date & Time") }}: <b>{{ formatDateTime(drawer.data.order_context?.order_datetime) || "—" }}</b></span>
								<span>{{ __("Delivery Type") }}: <b>{{ drawer.data.order_context?.delivery_type || "—" }}</b></span>
								<span>{{ __("Business Day") }}: <b>{{ drawer.data.custom_pos_business_day || "—" }}</b></span>
								<span>{{ __("Cashier Shift") }}: <b>{{ drawer.data.custom_pos_cashier_shift || "—" }}</b></span>
								<span>{{ __("Assigned Delivery") }}: <b>{{ drawer.data.custom_assigned_delivery || "—" }}</b></span>
							</div>
						</div>

						<!-- Original complaint text -->
						<div class="mx-5 mt-4">
							<p class="text-[10px] font-bold text-gray-500 uppercase mb-1.5">{{ __("Complaint Details") }}</p>
							<p class="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 border border-gray-100 leading-relaxed whitespace-pre-wrap">{{ drawer.data?.complaint_details || "—" }}</p>
						</div>

						<div class="mx-5 mt-5 space-y-4">

							<!-- Status buttons -->
							<div>
								<label class="block text-[10px] font-bold text-gray-500 uppercase mb-2">{{ __("Status") }}</label>
								<div class="flex flex-wrap gap-2">
									<button
										v-for="s in COMPLAINT_STATUSES"
										:key="s"
										@click="drawer.form.status = s"
										:class="drawer.form.status === s ? statusActiveClass(s) : 'bg-gray-100 text-gray-500 hover:bg-gray-200'"
										class="px-3 py-1.5 text-xs font-bold rounded-lg transition-all"
									>{{ s }}</button>
								</div>
							</div>

							<!-- Assign to -->
							<div>
								<label class="block text-[10px] font-bold text-gray-500 uppercase mb-1.5">{{ __("Assign To") }}</label>
								<select
									v-model="drawer.form.assigned_to"
									:disabled="isCashier"
									:class="['w-full h-9 px-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white', isCashier ? 'opacity-50 cursor-not-allowed' : '']"
								>
									<option value="">{{ __("Unassigned") }}</option>
									<option v-for="u in users" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
								</select>
							</div>

							<!-- Problem type -->
							<div>
								<label class="block text-[10px] font-bold text-gray-500 uppercase mb-1.5">{{ __("Problem Type") }}</label>
								<select
									v-model="drawer.form.type"
									class="w-full h-9 px-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
								>
									<option value="">{{ __("Select type...") }}</option>
									<option v-for="ct in complaintTypes" :key="ct.name" :value="ct.name">{{ ct.name }}</option>
								</select>
							</div>

							<!-- Response deadline -->
							<div>
								<label class="block text-[10px] font-bold text-gray-500 uppercase mb-1.5">{{ __("Response Deadline") }}</label>
								<input
									v-model="drawer.form.response_by"
									type="datetime-local"
									class="w-full h-9 px-3 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
								/>
								<p v-if="drawer.form.response_by && isOverdue(drawer.form.response_by)" class="mt-1 text-[10px] text-red-500 font-bold">
									⚠ {{ __("Deadline already passed") }}
								</p>
							</div>

							<!-- Resolution notes -->
							<div>
								<label class="block text-[10px] font-bold text-gray-500 uppercase mb-1.5">{{ __("Resolution Notes") }}</label>
								<textarea
									v-model="drawer.form.resolution_notes"
									:placeholder="__('Add resolution notes or follow-up actions...')"
									rows="3"
									class="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
								/>
							</div>

							<!-- ===== COUPON SECTION ===== -->
							<div
								:class="isMissingType
									? 'border-2 border-dashed border-orange-300 bg-orange-50'
									: 'border border-gray-200 bg-gray-50'"
								class="rounded-xl p-3 space-y-3"
							>
								<!-- Suggestion banner for a Missing-item complaint -->
								<div v-if="isMissingType" class="flex items-start gap-2">
									<svg class="w-4 h-4 text-orange-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
									</svg>
									<p class="text-xs text-orange-700 font-medium">{{ __("Missing-item complaint — compensate the customer with a coupon (needs manager approval).") }}</p>
								</div>

								<div class="flex items-center justify-between">
									<p class="text-[10px] font-bold text-gray-600 uppercase">{{ __("Give Coupon to Customer") }}</p>
									<button
										type="button"
										@click="drawer.couponOpen = !drawer.couponOpen"
										class="text-xs font-bold text-blue-600 hover:text-blue-800 transition-colors"
									>{{ drawer.couponOpen ? __("Hide") : __("+ Add Coupon") }}</button>
								</div>

								<!-- Coupon form -->
								<div v-if="drawer.couponOpen" class="space-y-3">
									<div class="grid grid-cols-2 gap-3">
										<!-- Discount type -->
										<div>
											<label class="block text-[10px] text-gray-500 font-bold mb-1">{{ __("Discount Type") }}</label>
											<select
												v-model="drawer.coupon.discount_type"
												class="w-full h-8 px-2 text-xs border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-blue-400"
											>
												<option value="Percentage">{{ __("Percentage %") }}</option>
												<option value="Amount">{{ __("Fixed Amount") }}</option>
											</select>
										</div>
										<!-- Discount value -->
										<div>
											<label class="block text-[10px] text-gray-500 font-bold mb-1">
												{{ drawer.coupon.discount_type === 'Percentage' ? __("Percentage (%)") : __("Amount") }}
											</label>
											<input
												v-model.number="drawer.coupon.discount_value"
												type="number"
												min="1"
												:max="drawer.coupon.discount_type === 'Percentage' ? 100 : undefined"
												:placeholder="drawer.coupon.discount_type === 'Percentage' ? '10' : '50'"
												class="w-full h-8 px-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-400"
											/>
										</div>
										<!-- Valid until -->
										<div>
											<label class="block text-[10px] text-gray-500 font-bold mb-1">{{ __("Valid Until") }}</label>
											<input
												v-model="drawer.coupon.valid_upto"
												type="date"
												class="w-full h-8 px-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-400"
											/>
										</div>
										<!-- Max uses -->
										<div>
											<label class="block text-[10px] text-gray-500 font-bold mb-1">{{ __("Max Uses") }}</label>
											<input
												v-model.number="drawer.coupon.max_uses"
												type="number"
												min="1"
												class="w-full h-8 px-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-400"
											/>
										</div>
									</div>

									<!-- Delivery fees option (Amount type only) -->
									<div v-if="drawer.coupon.discount_type === 'Amount'" class="space-y-2">
										<label class="flex items-center gap-2 cursor-pointer select-none">
											<input
												v-model="drawer.coupon.include_fees"
												type="checkbox"
												class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-400"
											/>
											<span class="text-xs font-bold text-gray-700">{{ __("Include Delivery Fees") }}</span>
										</label>
										<input
											v-if="drawer.coupon.include_fees"
											v-model.number="drawer.coupon.fees_amount"
											type="number"
											min="0"
											:placeholder="__('Delivery fees amount')"
											class="w-full h-8 px-2 text-xs border border-blue-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-400 bg-blue-50"
										/>
									</div>

									<!-- Request submitted for approval -->
									<div v-if="drawer.coupon.requested" class="flex items-center gap-2 p-2 bg-amber-50 border border-amber-200 rounded-lg">
										<svg class="w-4 h-4 text-amber-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
										</svg>
										<div class="flex-1 min-w-0">
											<p class="text-xs text-amber-800 font-bold">{{ __("Sent for Approval") }}</p>
											<p class="text-[10px] text-amber-600">{{ __("A manager will review this coupon in Need My Action.") }}</p>
										</div>
									</div>

									<button
										v-if="!drawer.coupon.requested"
										@click="issueCoupon"
										:disabled="!drawer.coupon.discount_value || drawer.coupon.issuing || (drawer.coupon.include_fees && !drawer.coupon.fees_amount)"
										class="w-full h-8 text-xs font-bold bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
									>
										<svg v-if="drawer.coupon.issuing" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
											<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
											<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
										</svg>
										<svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
										</svg>
										{{ drawer.coupon.issuing ? __("Submitting...") : __("Submit for Approval") }}
									</button>
									<button
										v-else
										@click="resetCoupon"
										class="w-full h-8 text-xs font-bold bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-all"
									>{{ __("Request Another Coupon") }}</button>
								</div>
							</div>
						</div>

						<!-- Meta -->
						<div class="mx-5 mt-4 flex gap-4 text-[10px] text-gray-400">
							<span>{{ __("Created") }}: {{ formatDateTime(drawer.data?.creation) }}</span>
							<span>{{ __("Updated") }}: {{ formatDateTime(drawer.data?.modified) }}</span>
						</div>
					</div>

					<!-- Footer -->
					<div class="px-5 py-4 border-t border-gray-100 flex-shrink-0 flex items-center justify-between gap-3">
						<div class="flex gap-2">
							<button
								v-if="drawer.form.status !== 'Closed'"
								@click="quickAction('Closed')"
								:disabled="drawer.saving"
								class="px-3 h-8 text-xs font-bold bg-green-100 text-green-700 hover:bg-green-200 rounded-lg transition-all disabled:opacity-50"
							>✓ {{ __("Close Complaint") }}</button>
							<button
								v-if="drawer.form.status === 'New'"
								@click="quickAction('Under Review')"
								:disabled="drawer.saving"
								class="px-3 h-8 text-xs font-bold bg-yellow-100 text-yellow-700 hover:bg-yellow-200 rounded-lg transition-all disabled:opacity-50"
							>▶ {{ __("Start Review") }}</button>
						</div>
						<div class="flex gap-2">
							<button @click="closeDrawer" class="px-4 h-9 text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-colors">
								{{ __("Cancel") }}
							</button>
							<button
								@click="saveDrawer"
								:disabled="drawer.saving"
								class="px-5 h-9 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-bold transition-all disabled:opacity-50 flex items-center gap-2"
							>
								<svg v-if="drawer.saving" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
								</svg>
								{{ drawer.saving ? __("Saving...") : __("Save Changes") }}
							</button>
						</div>
					</div>
				</div>
			</Transition>
		</Teleport>
	</div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-right-enter-active, .slide-right-leave-active { transition: transform 0.25s ease; }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); }
</style>

<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"
import { useBootstrapStore } from "@/stores/bootstrap"

const router = useRouter()
const { showSuccess, showError } = useToast()
const bootstrapStore = useBootstrapStore()

// Role checks
const isCashier = computed(() => bootstrapStore.hasRole("Cashier"))

// Page state
const complaints = ref([])
const loading = ref(true)
const filterStatus = ref("")
const search = ref("")
const complaintTypes = ref([])
const branches = ref([])
const users = ref([])
const activeView = ref("list")

// Daily report state
const report = ref(null)
const reportLoading = ref(false)
const reportDate = ref(new Date().toISOString().slice(0, 10))

// Detail drawer state
const drawer = ref({
	show: false,
	loading: false,
	saving: false,
	data: null,
	form: { status: "", assigned_to: "", type: "", response_by: "", resolution_notes: "" },
	couponOpen: false,
	coupon: { discount_type: "Percentage", discount_value: null, valid_upto: "", max_uses: 1, include_fees: false, fees_amount: null, generated: null, requested: false, issuing: false },
	compensationCoupons: [],
})

// The full configurable complaint lifecycle
const COMPLAINT_STATUSES = ["New", "Under Review", "Pending Approval", "Approved", "Rejected", "Coupon Issued", "Coupon Redeemed", "Closed"]

// Dialog state
const dialog = ref({
	show: false,
	submitting: false,
	customerSearch: "",
	customerResults: [],
	showCustomerDropdown: false,
	selectedCustomer: null,
	type: "",
	branch: "",
	responseBy: "",
	details: "",
	orderReference: "",
	orderContext: null,
	loadingOrder: false,
})

let customerSearchTimer = null

const canSubmit = computed(() =>
	dialog.value.selectedCustomer &&
	dialog.value.type &&
	dialog.value.branch &&
	dialog.value.responseBy
)

// A "Missing" complaint type is the primary case for compensation coupons.
const isMissingType = computed(() => (drawer.value.form?.type || "") === "Missing")

const filteredComplaints = computed(() => {
	let list = complaints.value
	if (filterStatus.value) {
		list = list.filter(c => c.status === filterStatus.value)
	}
	if (search.value.trim()) {
		const q = search.value.trim().toLowerCase()
		list = list.filter(c =>
			(c.customer_name || "").toLowerCase().includes(q) ||
			(c.customer || "").toLowerCase().includes(q) ||
			(c.custom_complaint_number || "").toLowerCase().includes(q) ||
			(c.custome_phone || "").includes(q)
		)
	}
	return list
})

function isOverdue(dateStr) {
	if (!dateStr) return false
	return new Date(dateStr) < new Date()
}

function timeUntil(dateStr) {
	const diff = new Date(dateStr) - new Date()
	if (diff <= 0) return ""
	const hours = Math.floor(diff / 3600000)
	const mins = Math.floor((diff % 3600000) / 60000)
	if (hours >= 24) return `${Math.floor(hours / 24)}d`
	if (hours > 0) return `${hours}h ${mins}m`
	return `${mins}m`
}

function formatDate(dateStr) {
	if (!dateStr) return ""
	return new Date(dateStr).toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

function formatDateFull(dateStr) {
	if (!dateStr) return ""
	return new Date(dateStr).toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" })
}

function formatDateTime(dateStr) {
	if (!dateStr) return ""
	return new Date(dateStr).toLocaleString(undefined, {
		month: "short", day: "numeric",
		hour: "2-digit", minute: "2-digit"
	})
}

async function loadDailyReport() {
	reportLoading.value = true
	try {
		report.value = await call("ecs_posnext.api.customers.get_daily_complaints_report", {
			report_date: reportDate.value,
		})
	} catch (err) {
		showError(__("Failed to load report"))
	} finally {
		reportLoading.value = false
	}
}

async function loadComplaints() {
	loading.value = true
	try {
		complaints.value = await call("ecs_posnext.api.customers.get_all_complaints", { limit: 200 }) || []
	} catch (err) {
		showError(__("Failed to load complaints"))
	} finally {
		loading.value = false
	}
}

async function loadComplaintTypes() {
	try {
		complaintTypes.value = await call("ecs_posnext.api.customers.get_complaint_types") || []
	} catch {}
}

async function loadBranches() {
	try {
		const result = await call("ecs_posnext.api.customers.get_branches") || []
		const seen = new Set()
		branches.value = result.filter(b => {
			if (seen.has(b.name)) return false
			seen.add(b.name)
			return true
		})
	} catch {}
}

function openNewDialog() {
	dialog.value = {
		show: true,
		submitting: false,
		customerSearch: "",
		customerResults: [],
		showCustomerDropdown: false,
		selectedCustomer: null,
		type: "",
		branch: "",
		responseBy: "",
		details: "",
		orderReference: "",
		orderContext: null,
		loadingOrder: false,
	}
}

async function loadOrderContext() {
	if (!dialog.value.orderReference) return
	dialog.value.loadingOrder = true
	try {
		const context = await call("ecs_posnext.api.customers.get_order_context_for_complaint", {
			order_doctype: "Sales Invoice",
			order_reference: dialog.value.orderReference,
		})
		dialog.value.orderContext = context
		if (context.branch) dialog.value.branch = context.branch
	} catch (err) {
		showError(err.message || __("Order not found"))
		dialog.value.orderContext = null
	} finally {
		dialog.value.loadingOrder = false
	}
}

function searchCustomers() {
	clearTimeout(customerSearchTimer)
	dialog.value.selectedCustomer = null
	const q = dialog.value.customerSearch.trim()
	if (!q) {
		dialog.value.customerResults = []
		return
	}
	customerSearchTimer = setTimeout(async () => {
		try {
			const results = await call("ecs_posnext.api.customers.get_customers", {
				search_term: q,
				limit: 10,
			})
			dialog.value.customerResults = results || []
			dialog.value.showCustomerDropdown = true
		} catch {}
	}, 300)
}

function selectCustomer(cust) {
	dialog.value.selectedCustomer = cust
	dialog.value.customerSearch = cust.customer_name
	dialog.value.showCustomerDropdown = false
	dialog.value.customerResults = []
}

async function submitNewComplaint() {
	if (!canSubmit.value) return
	dialog.value.submitting = true
	try {
		// Convert datetime-local value to Frappe format (YYYY-MM-DD HH:MM:SS)
		const responseBy = dialog.value.responseBy
			? dialog.value.responseBy.replace("T", " ") + ":00"
			: null

		const result = await call("ecs_posnext.api.customers.create_customer_complaint", {
			customer: dialog.value.selectedCustomer.name,
			complaint_details: dialog.value.details || "",
			complaint_type: dialog.value.type || null,
			branch: dialog.value.branch || null,
			response_by: responseBy,
			order_doctype: dialog.value.orderContext ? "Sales Invoice" : null,
			order_reference: dialog.value.orderContext ? dialog.value.orderReference : null,
		})
		if (result) {
			complaints.value.unshift(result)
			showSuccess(__("Complaint {0} created", [result.custom_complaint_number]))
			dialog.value.show = false
		}
	} catch (err) {
		showError(err.message || __("Failed to create complaint"))
	} finally {
		dialog.value.submitting = false
	}
}

async function changeStatus(complaint, newStatus) {
	try {
		await call("ecs_posnext.api.customers.update_complaint_status", {
			complaint_name: complaint.name,
			status: newStatus,
		})
		complaint.status = newStatus
		showSuccess(__("Status updated"))
	} catch (err) {
		showError(__("Failed to update status"))
	}
}

const STATUS_COLORS = {
	"New": { badge: "bg-red-100 text-red-700", text: "text-red-600", active: "bg-red-500 text-white" },
	"Under Review": { badge: "bg-yellow-100 text-yellow-700", text: "text-yellow-600", active: "bg-yellow-500 text-white" },
	"Pending Approval": { badge: "bg-amber-100 text-amber-700", text: "text-amber-600", active: "bg-amber-500 text-white" },
	"Approved": { badge: "bg-blue-100 text-blue-700", text: "text-blue-600", active: "bg-blue-500 text-white" },
	"Rejected": { badge: "bg-gray-100 text-gray-600", text: "text-gray-500", active: "bg-gray-500 text-white" },
	"Coupon Issued": { badge: "bg-purple-100 text-purple-700", text: "text-purple-600", active: "bg-purple-500 text-white" },
	"Coupon Redeemed": { badge: "bg-teal-100 text-teal-700", text: "text-teal-600", active: "bg-teal-500 text-white" },
	"Closed": { badge: "bg-green-100 text-green-700", text: "text-green-600", active: "bg-green-500 text-white" },
}

function statusBadgeClass(s) {
	return (STATUS_COLORS[s] || STATUS_COLORS["Rejected"]).badge
}

function statusTextClass(s) {
	return (STATUS_COLORS[s] || STATUS_COLORS["Rejected"]).text
}

function statusActiveClass(s) {
	return (STATUS_COLORS[s] || STATUS_COLORS["Rejected"]).active
}

function formatCurrency(value) {
	if (!value) return ""
	return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })
}

async function openDetail(row) {
	drawer.value.show = true
	drawer.value.loading = true
	drawer.value.data = null
	try {
		const detail = await call("ecs_posnext.api.customers.get_complaint_detail", {
			complaint_name: row.name,
		})
		drawer.value.data = detail
		// Pre-fill form
		const rb = detail.custom_response_by
		drawer.value.form = {
			status: detail.status,
			assigned_to: detail.assigned_to || "",
			type: detail.type || "",
			response_by: rb ? rb.replace(" ", "T").slice(0, 16) : "",
			resolution_notes: detail.resolution_notes || "",
		}
		drawer.value.couponOpen = false
		drawer.value.coupon = { discount_type: "Percentage", discount_value: null, valid_upto: "", max_uses: 1, include_fees: false, fees_amount: null, generated: null, issuing: false }
		drawer.value.compensationCoupons = []
		if (detail.customer) {
			try {
				const custDetail = await call("ecs_posnext.api.customers.get_customer_profile", {
					customer: detail.customer,
				})
				drawer.value.compensationCoupons = custDetail?.compensation_coupons || []
			} catch {}
		}
	} catch (err) {
		showError(__("Failed to load complaint details"))
		drawer.value.show = false
	} finally {
		drawer.value.loading = false
	}
}

function closeDrawer() {
	drawer.value.show = false
}

async function saveDrawer() {
	if (!drawer.value.data) return
	drawer.value.saving = true
	try {
		const rb = drawer.value.form.response_by
			? drawer.value.form.response_by.replace("T", " ") + ":00"
			: null
		const updated = await call("ecs_posnext.api.customers.update_complaint", {
			complaint_name: drawer.value.data.name,
			status: drawer.value.form.status,
			assigned_to: drawer.value.form.assigned_to || null,
			resolution_notes: drawer.value.form.resolution_notes,
			response_by: rb,
			complaint_type: drawer.value.form.type || null,
		})
		// Sync back to list
		const row = complaints.value.find(c => c.name === drawer.value.data.name)
		if (row) {
			row.status = updated.status
			row.assigned_to = updated.assigned_to
			row.type = updated.type
			row.custom_response_by = updated.custom_response_by
		}
		showSuccess(__("Complaint updated"))
		drawer.value.show = false
	} catch (err) {
		showError(err.message || __("Failed to save"))
	} finally {
		drawer.value.saving = false
	}
}

async function quickAction(status) {
	drawer.value.form.status = status
	await saveDrawer()
}

async function loadUsers() {
	try {
		users.value = await call("ecs_posnext.api.customers.get_users_for_assignment") || []
	} catch {}
}

async function issueCoupon() {
	if (!drawer.value.coupon.discount_value || !drawer.value.data) return
	drawer.value.coupon.issuing = true
	try {
		// Submit for manager approval — the POS Coupon is only minted once a Call
		// Center manager approves the request on the Need My Action page.
		await call("ecs_posnext.api.customers.request_complaint_coupon", {
			customer: drawer.value.data.customer,
			discount_type: drawer.value.coupon.discount_type,
			discount_value: drawer.value.coupon.discount_value,
			valid_upto: drawer.value.coupon.valid_upto || null,
			max_uses: drawer.value.coupon.max_uses || 1,
			branch: drawer.value.data.branch || null,
			complaint_name: drawer.value.data.name || null,
			include_fees: drawer.value.coupon.include_fees ? 1 : 0,
			fees_amount: drawer.value.coupon.include_fees ? (drawer.value.coupon.fees_amount || 0) : 0,
		})
		drawer.value.coupon.requested = true
		showSuccess(__("Coupon request sent for approval"))
	} catch (err) {
		showError(err.message || __("Failed to submit coupon request"))
	} finally {
		drawer.value.coupon.issuing = false
	}
}

function resetCoupon() {
	drawer.value.coupon.requested = false
	drawer.value.coupon.generated = null
	drawer.value.coupon.discount_value = null
	drawer.value.coupon.valid_upto = ""
	drawer.value.coupon.max_uses = 1
	drawer.value.coupon.discount_type = "Percentage"
	drawer.value.coupon.include_fees = false
	drawer.value.coupon.fees_amount = null
}

async function copyCode(code) {
	try {
		await navigator.clipboard.writeText(code)
		showSuccess(__("Code copied to clipboard"))
	} catch {
		showError(__("Failed to copy"))
	}
}

onMounted(() => {
	loadComplaints()
	loadComplaintTypes()
	loadBranches()
	loadUsers()
})
</script>
