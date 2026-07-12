<template>
	<div class="min-h-screen bg-gray-900 text-white flex flex-col" style="height: 100vh; overflow: hidden">

		<!-- Header -->
		<header class="bg-gray-900 border-b border-gray-700 px-6 py-3 flex items-center justify-between shrink-0">
			<div class="flex items-center gap-4">
				<button @click="$router.push('/')" class="text-gray-400 hover:text-white text-sm px-3 py-1.5 rounded bg-gray-700 hover:bg-gray-600 transition-colors">
					← Back
				</button>
				<div>
					<h1 class="text-2xl font-bold leading-none">{{ __('Dispatch Desk') }}</h1>
					<div v-if="currentShift" class="text-xs text-gray-400 mt-0.5">
						🟢 {{ currentShift.name }}
						<span v-if="currentShift.opening_time" class="ml-1 opacity-60">· {{ fmtTime(currentShift.opening_time) }}</span>
					</div>
					<div v-else class="flex items-center gap-2 mt-0.5">
						<span class="text-xs text-amber-500">⚠ {{ __('No open POS shift') }}</span>
						<!-- Open Shift button hidden: shifts are not opened from the Dispatcher screen -->
					</div>
				</div>
			</div>
			<button @click="refresh" :disabled="loading" class="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50">
				<svg :class="['w-4 h-4', loading ? 'animate-spin' : '']" fill="none" viewBox="0 0 24 24">
					<path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
				{{ __('Refresh') }}
			</button>
		</header>

		<!-- No shift placeholder -->
		<div v-if="!currentShift" class="flex flex-col flex-1 items-center justify-center gap-6 text-gray-500">
			<div class="text-6xl">🔒</div>
			<div class="text-center">
				<p class="text-2xl font-bold text-gray-300 mb-1">{{ __('No open POS shift') }}</p>
				<p class="text-sm text-gray-500">{{ __('Open a shift to start dispatching orders') }}</p>
			</div>
			<!-- Open Shift button hidden: shifts are not opened from the Dispatcher screen -->
		</div>

		<!-- Driver menu bar -->
		<div v-if="currentShift" class="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center gap-3 overflow-x-auto shrink-0">
			<span class="text-xs text-gray-500 uppercase tracking-wider shrink-0 font-semibold">
				{{ __('Drivers') }}
				<span class="ml-1 bg-gray-700 text-gray-300 rounded-full px-1.5 py-0.5 text-xs font-bold">{{ drivers.length }}</span>
			</span>
			<div v-if="drivers.length === 0" class="text-gray-600 text-sm italic">{{ __('No available drivers') }}</div>

			<button
				v-for="driver in drivers"
				:key="driver.name"
				@click="assignToDriver(driver)"
				:disabled="selectedOrders.length > 0 && !driverCanTake(driver)"
				class="flex items-center gap-2 px-3 py-1.5 rounded-xl transition-all shrink-0 border-2 disabled:opacity-40 disabled:cursor-not-allowed"
				:class="selectedOrders.length > 0
					? (driverCanTake(driver) ? 'bg-indigo-700 border-indigo-400 hover:bg-indigo-600 text-white' : 'bg-gray-800 border-gray-700 text-gray-400')
					: 'bg-gray-700 border-gray-600 hover:bg-gray-600 text-gray-200'"
			>
				<div class="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
					:class="driver.dispatch_current_status === 'On Delivery' ? 'bg-amber-600' : 'bg-green-700'">
					<span class="font-black text-xs" :class="driver.dispatch_current_status === 'On Delivery' ? 'text-amber-50' : 'text-green-100'">{{ initials(driver.full_name) }}</span>
				</div>
				<div class="text-left">
					<div class="font-bold text-sm leading-none">{{ driver.full_name }}</div>
					<div class="text-xs opacity-60 mt-0.5">
						<span v-if="driver.dispatch_current_status === 'On Delivery'" class="text-amber-300 font-semibold">🛵 {{ __('بره') }}</span>
						<span v-else-if="driver.cell_number">{{ driver.cell_number }}</span>
					</div>
				</div>
				<div class="ml-1 text-xs rounded-full px-2 py-0.5 font-black shrink-0"
					:class="(driver.active_load || 0) >= maxDriverOrders ? 'bg-red-500 text-white' : 'bg-gray-900/40 text-gray-200'">
					{{ driver.active_load || 0 }}/{{ maxDriverOrders }}
				</div>
				<div v-if="selectedOrders.length > 0 && driverCanTake(driver)" class="text-xs bg-white text-indigo-900 rounded-full px-2 py-0.5 font-black shrink-0">
					+{{ selectedOrders.length }}
				</div>
			</button>

			<div v-if="selectedOrders.length > 0" class="ml-auto flex items-center gap-2 shrink-0">
				<span class="text-indigo-300 text-sm font-medium">{{ selectedOrders.length }} {{ __('selected') }}</span>
				<button @click="selectedOrders = []" class="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 bg-gray-700 rounded">✕ Clear</button>
			</div>
		</div>

		<!-- Main: orders grid + assignments sidebar -->
		<div v-if="currentShift" class="flex flex-1 overflow-hidden">

			<!-- Talabat orders panel — handed to the Talabat platform's own driver -->
			<div class="flex flex-col overflow-hidden border-r border-gray-700" style="flex: 1 1 0; min-width: 0">
				<div class="flex items-center gap-3 px-4 pt-4 pb-3 shrink-0">
					<h2 class="font-bold text-sm text-orange-400 uppercase tracking-wider">🛵 {{ __('أوردرات طلبات') }}</h2>
					<span class="bg-orange-900 text-orange-300 rounded-full px-2 py-0.5 text-xs font-bold">{{ talabatOrders.length }}</span>
				</div>
				<div class="flex-1 overflow-y-auto px-4 pb-4">
					<div v-if="talabatOrders.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-600">
						<div class="text-5xl mb-3">🛵</div>
						<p class="text-lg">{{ __('لا يوجد أوردرات طلبات') }}</p>
					</div>

					<div class="grid gap-3" style="grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))">
						<div
							v-for="order in talabatOrders"
							:key="order.name"
							class="rounded-xl overflow-hidden shadow-xl bg-gray-800 flex flex-col ring-2 transition-all"
							:class="isUrgentOrder(order) ? 'ring-red-500' : 'ring-transparent'"
						>
							<!-- Color-coded header by KDS status -->
							<div class="px-3 py-2.5 flex items-start justify-between" :class="orderHeaderClass(order)">
								<div class="flex-1 min-w-0">
									<div class="text-2xl font-black tracking-tighter leading-none">
										{{ order.custom_number_order || order.name }}
									</div>
									<div class="text-xs opacity-75 mt-0.5">{{ order.name }}</div>
									<div class="text-xs opacity-75">{{ kdsLabel(order) }}</div>
								</div>
								<div class="text-right shrink-0 ml-2">
									<div class="mb-0.5">
										<span v-if="order.outstanding_amount > 0" class="text-xs font-bold bg-black/30 rounded px-1.5 py-0.5">💵 COD</span>
										<span v-else class="text-xs font-bold bg-black/30 rounded px-1.5 py-0.5">✓ Paid</span>
									</div>
									<div class="text-lg font-mono font-bold leading-none">
										{{ order.outstanding_amount > 0 ? fmtCurrency(order.outstanding_amount) : fmtCurrency(order.grand_total) }}
									</div>
									<div class="text-xs opacity-75 truncate max-w-[100px]">{{ order.customer }}</div>
								</div>
							</div>

							<!-- Order type + contact -->
							<div class="px-3 pt-2 flex items-center gap-1.5 flex-wrap">
								<span class="text-xs rounded px-1.5 py-0.5 font-bold text-white" :style="{ backgroundColor: catOf(order).color }">{{ catOf(order).emoji }} {{ catOf(order).labelAr }}</span>
								<span v-if="order.contact_mobile" class="text-xs text-gray-500">📞 {{ order.contact_mobile }}</span>
							</div>

							<!-- Waiting timer -->
							<div v-if="isDeliveryOrder(order) && order.kds_ready && order.kitchen_ready_at"
								class="mx-3 mt-1.5 px-2 py-1.5 rounded-lg flex items-center justify-between"
								:class="waitingUrgencyClass(order)">
								<span class="text-xs font-semibold">⏱ {{ __('Waiting') }}</span>
								<span class="text-sm font-black font-mono">{{ waitingLabel(order) }}</span>
							</div>

							<!-- Delivery location (territory + address) + print invoice -->
							<div class="flex-1 px-3 pt-1.5 pb-2 flex items-start justify-between gap-2">
								<div v-if="order.territory" class="text-xs text-gray-400 leading-snug flex-1 min-w-0">
									📍 {{ order.territory }}
								</div>
								<div v-else class="flex-1"></div>
								<button @click.stop="printOrder(order.name)" :title="__('Print invoice')"
									class="shrink-0 text-gray-300 hover:text-white p-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors">
									<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
								</button>
							</div>

							<!-- Talabat payment status + window number -->
							<div class="px-3 pb-1 flex items-center justify-between gap-2">
								<span class="text-xs px-2 py-0.5 rounded font-bold"
									:class="talabatPaid(order) ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'">
									{{ talabatPaid(order) ? '✓ ' + __('مدفوع') : '✗ ' + __('غير مدفوع') }}
								</span>
								<span class="text-xs text-gray-400 font-mono">{{ __('شباك طلبات') }} #{{ talabatNumber(order) }}</span>
							</div>

							<!-- Talabat handover — only once the kitchen is ready -->
							<div class="px-3 pb-3">
								<button v-if="!order.kds_ready" disabled
									class="w-full py-2 bg-amber-900/40 border border-amber-700 text-amber-400 rounded-lg text-xs font-bold">
									⏳ {{ __('في انتظار المطبخ') }}
								</button>
								<button v-else @click="handoverTalabat(order)" :disabled="statusLoading"
									class="w-full py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg text-xs font-bold transition-colors active:scale-95 disabled:opacity-50">
									🛵 {{ __('تسليم لطيار طلبات') }}
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Other orders panel — assigned to our own drivers -->
			<div class="flex flex-col overflow-hidden" style="flex: 1 1 0; min-width: 0">
				<div class="flex items-center gap-3 px-4 pt-4 pb-3 shrink-0">
					<h2 class="font-bold text-sm text-gray-400 uppercase tracking-wider">{{ __('Unassigned Orders') }}</h2>
					<span class="bg-gray-700 text-gray-300 rounded-full px-2 py-0.5 text-xs font-bold">{{ otherOrders.length }}</span>
				</div>
				<div class="flex-1 overflow-y-auto px-4 pb-4">
					<div v-if="otherOrders.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-500">
						<div class="text-5xl mb-3">📋</div>
						<p class="text-xl">{{ __('No unassigned orders') }}</p>
					</div>

					<div class="grid gap-3" style="grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))">
						<div
							v-for="order in otherOrders"
							:key="order.name"
							class="rounded-xl overflow-hidden shadow-xl bg-gray-800 flex flex-col cursor-pointer ring-2 transition-all"
							:class="selectedOrders.includes(order.name) ? 'ring-white' : isUrgentOrder(order) ? 'ring-red-500' : 'ring-transparent hover:ring-gray-600'"
							@click="toggleOrder(order.name)"
						>
							<!-- Color-coded header by KDS status -->
							<div class="px-3 py-2.5 flex items-start justify-between" :class="orderHeaderClass(order)">
								<div class="flex-1 min-w-0">
									<div class="text-2xl font-black tracking-tighter leading-none">
										{{ order.custom_number_order || order.name }}
									</div>
									<div class="text-xs opacity-75 mt-0.5">{{ order.name }}</div>
									<div class="text-xs opacity-75">{{ kdsLabel(order) }}</div>
								</div>
								<div class="text-right shrink-0 ml-2">
									<div class="mb-0.5">
										<span v-if="order.outstanding_amount > 0" class="text-xs font-bold bg-black/30 rounded px-1.5 py-0.5">💵 COD</span>
										<span v-else class="text-xs font-bold bg-black/30 rounded px-1.5 py-0.5">✓ Paid</span>
									</div>
									<div class="text-lg font-mono font-bold leading-none">
										{{ order.outstanding_amount > 0 ? fmtCurrency(order.outstanding_amount) : fmtCurrency(order.grand_total) }}
									</div>
									<div class="text-xs opacity-75 truncate max-w-[100px]">{{ order.customer }}</div>
								</div>
							</div>

							<!-- Order type + contact -->
							<div class="px-3 pt-2 flex items-center gap-1.5 flex-wrap">
								<span class="text-xs rounded px-1.5 py-0.5 font-bold text-white" :style="{ backgroundColor: catOf(order).color }">{{ catOf(order).emoji }} {{ catOf(order).labelAr }}</span>
								<span v-if="order.contact_mobile" class="text-xs text-gray-500">📞 {{ order.contact_mobile }}</span>
							</div>

							<!-- Waiting timer -->
							<div v-if="isDeliveryOrder(order) && order.kds_ready && order.kitchen_ready_at"
								class="mx-3 mt-1.5 px-2 py-1.5 rounded-lg flex items-center justify-between"
								:class="waitingUrgencyClass(order)">
								<span class="text-xs font-semibold">⏱ {{ __('Waiting') }}</span>
								<span class="text-sm font-black font-mono">{{ waitingLabel(order) }}</span>
							</div>

							<!-- Delivery location (territory + address) + print invoice -->
							<div class="flex-1 px-3 pt-1.5 pb-2 flex items-start justify-between gap-2">
								<div v-if="order.territory" class="text-xs text-gray-400 leading-snug flex-1 min-w-0">
									📍 {{ order.territory }}
								</div>
								<div v-else class="flex-1"></div>
								<button @click.stop="printOrder(order.name)" :title="__('Print invoice')"
									class="shrink-0 text-gray-300 hover:text-white p-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors">
									<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
								</button>
							</div>

							<!-- Payment method -->
							<div class="px-3 pb-1">
								<span class="text-xs px-2 py-0.5 rounded font-bold bg-gray-700 text-gray-200">{{ paymentLabel(order) }}</span>
							</div>

							<!-- Select indicator -->
							<div class="px-3 pb-3">
								<div class="w-full py-2 rounded-lg text-sm font-bold text-center"
									:class="selectedOrders.includes(order.name) ? 'bg-white text-gray-900' : 'bg-gray-700 text-gray-400'">
									{{ selectedOrders.includes(order.name) ? '✓ Selected' : 'Tap to select' }}
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Active Assignments sidebar -->
			<div class="flex flex-col bg-gray-800 border-l border-gray-700 shrink-0 overflow-hidden" style="width: 320px">
				<div class="px-4 py-3 border-b border-gray-700 shrink-0">
					<h2 class="font-bold text-sm text-gray-400 uppercase tracking-wider">
						{{ __('Active Assignments') }}
						<span class="ml-2 bg-gray-700 text-gray-300 rounded-full px-2 py-0.5 text-xs font-bold">{{ activeAssignments.length }}</span>
					</h2>
				</div>

				<div class="flex-1 overflow-y-auto p-3 space-y-3">
					<div v-if="groupedAssignments.length === 0" class="flex flex-col items-center justify-center h-full text-gray-500">
						<div class="text-4xl mb-2">🚗</div>
						<p class="text-sm">{{ __('No active assignments') }}</p>
					</div>

					<div v-for="bundle in groupedAssignments" :key="bundle.key" class="rounded-xl bg-gray-900 overflow-hidden shadow-lg flex flex-col">

						<!-- Bundle header -->
						<div class="px-3 py-2.5 flex items-center justify-between" :class="bundle.is_talabat ? 'bg-orange-800' : 'bg-gray-700'">
							<div class="flex items-center gap-2">
								<div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0" :class="bundle.is_talabat ? 'bg-orange-600' : 'bg-green-700'">
									<span class="font-black text-xs" :class="bundle.is_talabat ? 'text-orange-50' : 'text-green-100'">{{ bundle.is_talabat ? '🛵' : initials(bundle.driver_name) }}</span>
								</div>
								<div>
									<div class="font-bold text-white text-sm">{{ bundle.driver_name }}</div>
									<div class="text-xs text-gray-300">
										{{ bundle.assignments.length }} order(s)
										<span v-if="bundle.total_cod > 0" class="ml-1 text-amber-300 font-bold">· {{ fmtCurrency(bundle.total_cod) }}</span>
									</div>
								</div>
							</div>
							<div class="text-right">
								<div class="text-lg font-mono font-bold text-amber-300">{{ bundleTimer(bundle) }}</div>
								<span :class="statusBadge(bundle.bundle_status)">{{ bundle.bundle_status }}</span>
							</div>
						</div>

						<!-- Orders in bundle — each order acts independently -->
						<div class="divide-y divide-gray-800">
							<div v-for="a in bundle.assignments" :key="a.name" class="px-3 py-2">
								<div class="flex items-center gap-2">
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-1.5">
											<span class="text-blue-400 font-medium text-xs">{{ a.custom_number_order || a.order_reference }}</span>
											<span class="text-gray-400 text-xs truncate">{{ a.customer }}</span>
										</div>
										<div v-if="a.delivery_address" class="text-xs text-gray-600 truncate">📍 {{ a.delivery_address }}</div>
										<div class="text-xs mt-0.5">
											<span class="text-xs px-1.5 py-0.5 rounded font-medium"
												:class="a.kds_ready ? 'bg-green-900 text-green-400' : 'bg-amber-900 text-amber-400'">
												{{ a.kds_ready ? '✓ Kitchen' : '⏳ ' + a.kds_status }}
											</span>
										</div>
									</div>
									<div class="text-right shrink-0">
										<div v-if="a.payment_mode === 'Cash (COD)'" class="text-yellow-300 font-bold font-mono text-xs">{{ fmtCurrency(a.amount_to_collect) }}</div>
										<div v-else class="text-xs text-green-400">Paid</div>
										<span :class="statusBadge(a.status)">{{ a.status }}</span>
									</div>
								</div>

								<!-- Per-order actions -->
								<div class="flex gap-1.5 mt-2">
									<!-- Talabat: paid → Done; cash → collect money from the Talabat driver -->
									<template v-if="bundle.is_talabat">
										<button v-if="a.payment_mode === 'Cash (COD)'" @click="orderCollect(a)" :disabled="statusLoading" class="flex-1 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded-lg text-xs font-bold transition-colors active:scale-95 disabled:opacity-50">
											💰 {{ __('استلام الفلوس من طيار طلبات') }}
										</button>
										<button v-else @click="orderTalabatReceived(a)" :disabled="statusLoading" class="flex-1 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded-lg text-xs font-bold transition-colors active:scale-95 disabled:opacity-50">
											✅ {{ __('Done') }}
										</button>
									</template>
									<!-- Internal, not yet out for delivery -->
									<template v-else-if="a.status === 'Assigned' || a.status === 'Picked Up'">
										<button v-if="a.kds_ready === false" disabled class="flex-1 py-1.5 bg-amber-900/40 border border-amber-700 text-amber-400 rounded-lg text-xs">
											⏳ {{ __('Waiting for kitchen…') }}
										</button>
										<button v-else @click="orderGoDeliver(a)" :disabled="statusLoading" class="flex-1 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-colors active:scale-95 disabled:opacity-50">
											🚀 {{ __('Go to Deliver') }}
										</button>
										<button @click="orderReturn(a)" :disabled="statusLoading" class="py-1.5 px-2.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-xs transition-colors disabled:opacity-50">
											{{ __('Return') }}
										</button>
									</template>
									<!-- Internal, out for delivery -->
									<template v-else>
										<button @click="orderCollect(a)" :disabled="statusLoading" class="flex-1 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded-lg text-xs font-bold transition-colors active:scale-95 disabled:opacity-50">
											💰 {{ __('Collect & Deliver') }}
										</button>
										<button @click="orderFailed(a)" :disabled="statusLoading" class="py-1.5 px-2.5 bg-red-800 hover:bg-red-700 text-red-200 rounded-lg text-xs font-bold transition-colors disabled:opacity-50">
											❌ {{ __('Failed') }}
										</button>
									</template>
									<!-- Print invoice — always available once assigned -->
									<button @click.stop="printOrder(a.order_reference)" :title="__('Print invoice')"
										class="shrink-0 text-gray-300 hover:text-white p-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors">
										<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
									</button>
								</div>
							</div>
						</div>

						<!-- Bundle-level convenience: send the whole internal bundle out at once -->
						<div v-if="!bundle.is_talabat && bundle.bundle_status !== 'Out for Delivery' && bundle.assignments.length > 1 && bundle.bundle_kds_ready" class="px-3 pb-3 pt-2 border-t border-gray-800">
							<button @click="bundleGoDeliver(bundle)" :disabled="statusLoading" class="w-full py-2 bg-blue-700 hover:bg-blue-600 text-white rounded-lg text-xs font-bold transition-colors active:scale-95 disabled:opacity-50">
								🚀 {{ __('Go to Deliver — All') }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- ── MODALS ─────────────────────────────────────────────── -->

		<!-- Bundle Collect modal -->
		<div v-if="bundleCollectModal" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
			<div class="bg-gray-800 rounded-xl shadow-2xl p-6 w-full max-w-lg mx-4 text-white">
				<h3 class="text-xl font-bold mb-1">💰 {{ __('Collect & Deliver') }}</h3>
				<p class="text-gray-400 text-sm mb-5">{{ bundleCollectModal.driver_name }} — {{ bundleCollectModal.assignments.length }} order(s)</p>
				<div class="space-y-3 mb-5">
					<div v-for="row in bundleCollectRows" :key="row.name" class="bg-gray-900 rounded-lg p-3">
						<div class="flex items-center justify-between mb-2">
							<div>
								<span class="text-blue-400 font-medium text-sm">{{ row.custom_number_order || row.order_reference }}</span>
								<span class="text-gray-400 text-xs ml-2">{{ row.customer }}</span>
							</div>
							<span v-if="row.payment_mode === 'Cash (COD)'" class="text-xs bg-amber-900 text-amber-300 rounded px-1.5 py-0.5 font-bold">COD</span>
							<span v-else class="text-xs bg-green-900 text-green-300 rounded px-1.5 py-0.5 font-bold">Paid</span>
						</div>
						<div v-if="row.payment_mode === 'Cash (COD)'" class="space-y-2">
							<div class="text-gray-400 text-xs">{{ __('Expected') }}: <span class="text-yellow-300 font-mono font-bold">{{ fmtCurrency(row.amount_to_collect) }}</span></div>
							<div v-for="(line, li) in row.payments" :key="li" class="flex items-center gap-2">
								<select v-model="line.mode_of_payment" :disabled="isTalabatCollect"
									class="bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-60"
									style="flex: 1 1 0; min-width: 0">
									<option v-for="m in selectablePaymentModes" :key="m.mode_of_payment" :value="m.mode_of_payment">{{ m.mode_of_payment }}</option>
								</select>
								<input v-model.number="line.amount" type="number" step="0.01"
									class="w-28 bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-white text-sm text-right focus:outline-none focus:ring-2 focus:ring-green-500"
									placeholder="0.00" />
								<button v-if="row.payments.length > 1" @click="row.payments.splice(li, 1)"
									class="text-red-400 hover:text-red-300 px-1 text-xl leading-none shrink-0" title="Remove">×</button>
							</div>
							<div class="flex items-center justify-between">
								<button v-if="!isTalabatCollect" @click="row.payments.push({ mode_of_payment: defaultPaymentMode, amount: 0 })"
									class="text-xs text-indigo-400 hover:text-indigo-300 font-medium">+ {{ __('طريقة دفع أخرى') }}</button>
								<span v-else></span>
								<div class="text-xs font-mono"
									:class="rowCollected(row) === row.amount_to_collect ? 'text-green-400' : (rowCollected(row) > row.amount_to_collect ? 'text-blue-400' : 'text-red-400')">
									{{ __('Collected') }}: {{ fmtCurrency(rowCollected(row)) }}
								</div>
							</div>
						</div>
					</div>
				</div>
				<div class="bg-gray-900 rounded-lg p-3 mb-5 flex justify-between items-center">
					<span class="text-gray-400 font-medium">Total COD</span>
					<div class="text-right">
						<div class="text-xs text-gray-500">Expected: {{ fmtCurrency(bundleCollectModal.total_cod) }}</div>
						<div class="text-xl font-mono font-bold text-yellow-300">{{ fmtCurrency(bundleCollectTotal) }}</div>
					</div>
				</div>
				<div v-if="collectError" class="mb-4 p-3 bg-red-900/50 text-red-300 text-sm rounded-lg border border-red-700">{{ collectError }}</div>
				<div class="flex gap-2">
					<button @click="bundleCollectModal = null; collectError = null" class="flex-1 py-2.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm font-medium transition-colors">{{ __('Cancel') }}</button>
					<button @click="confirmBundleDeliver" :disabled="statusLoading" class="flex-1 py-2.5 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-bold disabled:opacity-50 transition-colors active:scale-95">
						{{ statusLoading ? __('Saving…') : __('Deliver All ✓') }}
					</button>
				</div>
			</div>
		</div>

		<!-- Open Shift modal -->
		<div v-if="openShiftModal" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
			<div class="bg-gray-800 rounded-xl shadow-2xl p-6 max-w-sm w-full mx-4 text-white">
				<h3 class="text-xl font-bold mb-1">🔓 {{ __('Open POS Shift') }}</h3>
				<p class="text-gray-400 text-sm mb-5">{{ __('Select a POS profile to start your shift') }}</p>
				<div class="mb-5">
					<label class="block text-xs text-gray-400 mb-1 uppercase tracking-wider">{{ __('POS Profile') }}</label>
					<select v-model="openShiftProfile"
						class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500">
						<option value="" disabled>{{ __('Select POS Profile…') }}</option>
						<option v-for="p in posProfiles" :key="p.name" :value="p.name">
							{{ p.name }}<span v-if="p.branch"> · {{ p.branch }}</span>
						</option>
					</select>
				</div>
				<div v-if="openShiftError" class="mb-4 p-3 bg-red-900/50 text-red-300 text-sm rounded-lg border border-red-700">{{ openShiftError }}</div>
				<div class="flex gap-3">
					<button @click="openShiftModal = false; openShiftError = null" class="flex-1 py-2.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm transition-colors">{{ __('Cancel') }}</button>
					<button @click="doOpenShift" :disabled="!openShiftProfile || openShiftLoading"
						class="flex-1 py-2.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-bold disabled:opacity-50 transition-colors active:scale-95">
						{{ openShiftLoading ? __('Opening…') : __('Open Shift') }}
					</button>
				</div>
			</div>
		</div>

		<!-- Delivery Failed modal -->
		<div v-if="deliveryFailedModal" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
			<div class="bg-gray-800 rounded-xl shadow-2xl p-6 max-w-sm w-full mx-4 text-white">
				<h3 class="text-xl font-bold mb-1 text-red-400">❌ {{ __('Delivery Failed') }}</h3>
				<p class="text-gray-400 text-sm mb-4">{{ deliveryFailedModal.driver_name }} — {{ deliveryFailedModal.assignments.length }} order(s)</p>
				<div class="mb-4">
					<label class="block text-xs text-gray-400 mb-1 uppercase tracking-wider">{{ __('Failure Reason') }}</label>
					<textarea v-model="deliveryFailedReason" rows="3"
						class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
						:placeholder="__('Enter reason for delivery failure…')" />
				</div>
				<div v-if="deliveryFailedError" class="mb-4 p-3 bg-red-900/50 text-red-300 text-sm rounded-lg border border-red-700">{{ deliveryFailedError }}</div>
				<p class="text-xs text-amber-400 mb-4">{{ __('Orders will appear in Need My Action for cancellation review.') }}</p>
				<div class="flex gap-3">
					<button @click="deliveryFailedModal = null; deliveryFailedReason = ''; deliveryFailedError = null" class="flex-1 py-2.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm transition-colors">{{ __('Cancel') }}</button>
					<button @click="confirmDeliveryFailed" :disabled="!deliveryFailedReason.trim() || statusLoading"
						class="flex-1 py-2.5 bg-red-700 hover:bg-red-600 text-white rounded-lg text-sm font-bold disabled:opacity-50 transition-colors active:scale-95">
						{{ statusLoading ? __('Saving…') : __('Mark as Failed') }}
					</button>
				</div>
			</div>
		</div>

		<!-- Assign confirm modal -->
		<div v-if="pendingAssign" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
			<div class="bg-gray-800 rounded-xl shadow-2xl p-6 max-w-sm w-full mx-4 text-white">
				<h3 class="text-xl font-bold mb-4">{{ __('Confirm Assignment') }}</h3>
				<div class="space-y-2 mb-6 text-gray-300">
					<div>Driver: <span class="font-bold text-white">{{ pendingAssign.driver.full_name }}</span></div>
					<div>Orders: <span class="font-bold text-white">{{ pendingAssign.orders.length }}</span></div>
				</div>
				<div class="flex gap-3 justify-end">
					<button @click="pendingAssign = null" class="px-4 py-2.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm transition-colors">{{ __('Cancel') }}</button>
					<button @click="doAssign" :disabled="assignLoading" class="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg disabled:opacity-50 text-sm font-bold transition-colors active:scale-95">
						{{ assignLoading ? __('Assigning…') : __('Assign') }}
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue"
import { call } from "frappe-ui"
import { useToast } from "@/composables/useToast"
import { initSocket } from "@/socket"
import { orderCategory } from "@/utils/orderCategory"

// Order-type category (icon + colour + label) shared with KDS and the print format
function catOf(order) {
	return orderCategory({
		order_type: order.custom_order_type,
		payment_type: order.custom_payment_type,
		outstanding: order.outstanding_amount,
	})
}

const { showSuccess, showError } = useToast()

const orders = ref([])
const drivers = ref([])
const activeAssignments = ref([])
const selectedOrders = ref([])
const currentShift = ref(null)
const loading = ref(false)
const assignLoading = ref(false)
const statusLoading = ref(false)
const pendingAssign = ref(null)
const collectError = ref(null)
const bundleCollectModal = ref(null)
const bundleCollectRows = ref([])
const paymentModes = ref([])
const timerTick = ref(0)
const openShiftModal = ref(false)
const openShiftProfile = ref("")
const openShiftLoading = ref(false)
const openShiftError = ref(null)
const posProfiles = ref([])
const deliveryFailedModal = ref(null)
const deliveryFailedReason = ref("")
const deliveryFailedError = ref(null)

let timerInterval = null

function __(str) { return str }

function fmtTime(dt) {
	if (!dt) return ""
	try { return new Date(dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }
	catch { return "" }
}

// ── Split unassigned orders: Talabat (platform driver) vs. our own drivers ──
const talabatOrders = computed(() => orders.value.filter(o => o.custom_order_type === "Talabat"))
const otherOrders = computed(() => orders.value.filter(o => o.custom_order_type !== "Talabat"))

// ── Driver capacity (max concurrent orders, set on the POS Profile) ─────────
const maxDriverOrders = computed(() => currentShift.value?.max_driver_orders || 2)
function driverCanTake(driver) {
	return (driver.active_load || 0) + selectedOrders.value.length <= maxDriverOrders.value
}

// ── Group assignments by driver ────────────────────────────────────────────
const groupedAssignments = computed(() => {
	const map = {}
	for (const a of activeAssignments.value) {
		const isTalabat = a.delivery_channel === "Talabat"
		const key = isTalabat ? "__talabat__" : a.driver
		if (!map[key]) {
			map[key] = {
				key,
				driver: a.driver,
				is_talabat: isTalabat,
				driver_name: isTalabat ? "طيار طلبات" : a.driver_name,
				assignments: [],
				earliest_assigned_at: a.assigned_at,
				earliest_out_at: a.out_for_delivery_time || null,
				total_cod: 0,
				bundle_status: a.status,
				bundle_kds_ready: a.kds_ready !== false,
			}
		}
		const g = map[key]
		g.assignments.push(a)
		if (a.payment_mode === "Cash (COD)") g.total_cod += (a.amount_to_collect || 0)
		if (a.assigned_at && (!g.earliest_assigned_at || a.assigned_at < g.earliest_assigned_at))
			g.earliest_assigned_at = a.assigned_at
		if (a.out_for_delivery_time && (!g.earliest_out_at || a.out_for_delivery_time < g.earliest_out_at))
			g.earliest_out_at = a.out_for_delivery_time
		const priority = { "Assigned": 0, "Picked Up": 1, "Out for Delivery": 2 }
		if ((priority[a.status] ?? 99) < (priority[g.bundle_status] ?? 99))
			g.bundle_status = a.status
		if (a.kds_ready === false) g.bundle_kds_ready = false
	}
	return Object.values(map)
})

// Sum of all payment lines on a COD row
function rowCollected(row) {
	return (row.payments || []).reduce((s, p) => s + (Number(p.amount) || 0), 0)
}
const bundleCollectTotal = computed(() =>
	(bundleCollectRows.value || []).reduce((sum, r) =>
		sum + (r.payment_mode === "Cash (COD)" ? rowCollected(r) : 0), 0)
)
// Default mode = first Cash-type mode, else first available, else "Cash"
const defaultPaymentMode = computed(() => {
	const modes = paymentModes.value || []
	const cash = modes.find(m => (m.type || "").toLowerCase() === "cash")
	return (cash || modes[0])?.mode_of_payment || "Cash"
})
// Talabat orders are collected in cash only — no split, no card.
const isTalabatCollect = computed(() => !!bundleCollectModal.value?.talabatOrder)
const selectablePaymentModes = computed(() => {
	if (!isTalabatCollect.value) return paymentModes.value || []
	const cash = (paymentModes.value || []).filter(m => (m.type || "").toLowerCase() === "cash")
	return cash.length ? cash : [{ mode_of_payment: defaultPaymentMode.value, type: "Cash" }]
})

// ── KDS helpers ──────────────────────────────────────────────────────────
function orderHeaderClass(order) {
	if (!order.kds_status || order.kds_status === "No KDS" || order.kds_status === "Completed") return "bg-green-600"
	return { "Ready": "bg-blue-600", "Preparing": "bg-amber-500", "Pending": "bg-gray-700" }[order.kds_status] || "bg-gray-700"
}
function kdsLabel(order) {
	if (!order.kds_status || order.kds_status === "No KDS" || order.kds_status === "Completed") return "✓ Kitchen Ready"
	return { "Pending": "⏳ Pending", "Preparing": "🔥 Preparing", "Ready": "✓ Ready" }[order.kds_status] || order.kds_status
}

// ── Timer ─────────────────────────────────────────────────────────────────
function elapsedLabel(ts) {
	timerTick.value
	if (!ts) return "—"
	const elapsed = Date.now() - new Date(ts)
	const mm = String(Math.floor(elapsed / 60000)).padStart(2, "0")
	const ss = String(Math.floor((elapsed % 60000) / 1000)).padStart(2, "0")
	return `${mm}:${ss}`
}
// While the driver is out, count from when they left; otherwise count waiting-at-branch time.
function bundleTimer(bundle) {
	if (bundle.bundle_status === "Out for Delivery" && bundle.earliest_out_at)
		return elapsedLabel(bundle.earliest_out_at)
	return elapsedLabel(bundle.earliest_assigned_at)
}

// ── Waiting timer helpers ─────────────────────────────────────────────────
function isDeliveryOrder(order) {
	return order.custom_order_type === "Delivery" || order.custom_order_type === "Talabat"
}
function waitingSeconds(order) {
	timerTick.value
	if (!order.kitchen_ready_at) return 0
	return Math.max(0, Math.floor((Date.now() - new Date(order.kitchen_ready_at)) / 1000))
}
function waitingLabel(order) {
	const secs = waitingSeconds(order)
	const mm = String(Math.floor(secs / 60)).padStart(2, "0")
	const ss = String(secs % 60).padStart(2, "0")
	return `${mm}:${ss}`
}
function waitingUrgencyClass(order) {
	const secs = waitingSeconds(order)
	if (secs >= 7 * 60) return "bg-red-900/70 text-red-300"
	if (secs >= 3 * 60) return "bg-amber-900/70 text-amber-300"
	return "bg-blue-900/50 text-blue-300"
}
function isUrgentOrder(order) {
	return isDeliveryOrder(order) && order.kds_ready && order.kitchen_ready_at && waitingSeconds(order) >= 7 * 60
}

// Print the Sales Invoice using the "print format sales" template
function printOrder(name) {
	if (!name) return
	const fmt = encodeURIComponent("print format sales")
	window.open(
		`/printview?doctype=Sales Invoice&name=${encodeURIComponent(name)}&trigger_print=1&format=${fmt}&no_letterhead=0`,
		"_blank",
	)
}

// ── Payment + Talabat display helpers ──────────────────────────────────────
function paymentLabel(o) {
	const t = (o.custom_payment_type || "").toLowerCase()
	if (t.includes("credit") || t.includes("card") || t.includes("visa")) return "💳 فيزا"
	if (t.includes("cash")) return "💵 كاش"
	return o.outstanding_amount > 0 ? "💵 كاش" : "✓ مدفوع"
}
function talabatNumber(o) {
	return o.custom_unique_talbat_number || o.custom_third_party_referance_number || "—"
}
function talabatPaid(o) {
	return !(o.outstanding_amount > 0)
}

// ── Bundle actions ────────────────────────────────────────────────────────
async function bundleGoDeliver(bundle) {
	statusLoading.value = true
	try {
		for (const a of bundle.assignments) {
			if (a.status === "Assigned" || a.status === "Picked Up") {
				await call("ecs_posnext.ecs_posnext.api.dispatcher.update_assignment_status", {
					assignment: a.name, status: "Out for Delivery",
				})
			}
		}
		showSuccess(__("Bundle sent Out for Delivery"))
		await Promise.all([loadDrivers(), loadActiveAssignments()])
	} catch (e) {
		console.error("[Dispatcher] bundleGoDeliver error:", e)
		showError(errMsg(e))
	} finally { statusLoading.value = false }
}

// ── Per-order actions (one order, never the whole bundle) ───────────────────
async function orderStatus(a, status, successMsg) {
	statusLoading.value = true
	try {
		await call("ecs_posnext.ecs_posnext.api.dispatcher.update_assignment_status", { assignment: a.name, status })
		if (successMsg) showSuccess(successMsg)
		await Promise.all([loadOrders(), loadDrivers(), loadActiveAssignments()])
	} catch (e) { showError(errMsg(e)) }
	finally { statusLoading.value = false }
}
function orderGoDeliver(a) { return orderStatus(a, "Out for Delivery", __("Out for Delivery")) }
function orderReturn(a) { return orderStatus(a, "Returned", __("Order returned")) }
function orderTalabatReceived(a) { return orderStatus(a, "Delivered", __("تم تأكيد استلام العميل")) }

function orderCollect(a) {
	const isCod = a.payment_mode === "Cash (COD)"
	bundleCollectRows.value = [{
		...a,
		payments: isCod ? [{ mode_of_payment: defaultPaymentMode.value, amount: a.amount_to_collect || 0 }] : [],
	}]
	bundleCollectModal.value = {
		driver_name: a.driver_name,
		assignments: [a],
		total_cod: isCod ? (a.amount_to_collect || 0) : 0,
	}
	collectError.value = null
}

function orderFailed(a) {
	deliveryFailedModal.value = { driver_name: a.driver_name, assignments: [a] }
	deliveryFailedReason.value = ""
	deliveryFailedError.value = null
}

// ── Talabat handover — hand to the platform's own driver ────────────────────
function isTalabat(order) { return order.custom_order_type === "Talabat" }

async function handoverTalabat(order) {
	// Kitchen must be done before the order can leave the branch.
	if (!order.kds_ready) {
		showError(__("لا يمكن التسليم قبل تجهيز المطبخ"))
		return
	}
	// Unpaid → collect payment (mode of payment) first; paid → deliver immediately.
	// Either way it is delivered in one step — no assign / tracking.
	if ((order.outstanding_amount || 0) > 0) {
		openTalabatCollect(order)
		return
	}
	statusLoading.value = true
	try {
		await call("ecs_posnext.ecs_posnext.api.dispatcher.deliver_talabat", { order: order.name })
		showSuccess(__("تم تسليم أوردر طلبات"))
		selectedOrders.value = selectedOrders.value.filter(n => n !== order.name)
		await Promise.all([loadOrders(), loadActiveAssignments()])
	} catch (e) { showError(errMsg(e)) }
	finally { statusLoading.value = false }
}

// Unpaid Talabat: open the collect modal (marked as a Talabat delivery, no assignment yet)
function openTalabatCollect(order) {
	bundleCollectRows.value = [{
		order_reference: order.name,
		custom_number_order: order.custom_number_order,
		customer: order.customer,
		payment_mode: "Cash (COD)",
		amount_to_collect: order.outstanding_amount || 0,
		payments: [{ mode_of_payment: defaultPaymentMode.value, amount: order.outstanding_amount || 0 }],
	}]
	bundleCollectModal.value = {
		driver_name: __("طيار طلبات"),
		talabatOrder: order,
		assignments: [order],
		total_cod: order.outstanding_amount || 0,
	}
	collectError.value = null
}

async function confirmBundleDeliver() {
	statusLoading.value = true
	collectError.value = null
	try {
		// Talabat delivery: create + collect + deliver in one step (no assignment)
		if (bundleCollectModal.value?.talabatOrder) {
			const order = bundleCollectModal.value.talabatOrder
			const row = bundleCollectRows.value[0]
			await call("ecs_posnext.ecs_posnext.api.dispatcher.deliver_talabat", {
				order: order.name,
				payments: JSON.stringify(row.payments || []),
			})
			showSuccess(__("تم تسليم أوردر طلبات"))
			bundleCollectModal.value = null
			selectedOrders.value = selectedOrders.value.filter(n => n !== order.name)
			await Promise.all([loadOrders(), loadActiveAssignments()])
			return
		}
		await Promise.all(bundleCollectRows.value.map(row => {
			const isCod = row.payment_mode === "Cash (COD)"
			return call("ecs_posnext.ecs_posnext.api.dispatcher.update_assignment_status", {
				assignment: row.name, status: "Delivered",
				payments: isCod ? JSON.stringify(row.payments || []) : undefined,
				amount_collected: isCod ? undefined : 0,
			})
		}))
		showSuccess(__("Bundle delivered"))
		bundleCollectModal.value = null
		await Promise.all([loadDrivers(), loadActiveAssignments()])
	} catch (e) { collectError.value = errMsg(e) }
	finally { statusLoading.value = false }
}

async function confirmDeliveryFailed() {
	if (!deliveryFailedReason.value.trim()) return
	statusLoading.value = true
	deliveryFailedError.value = null
	try {
		await Promise.all(deliveryFailedModal.value.assignments.map(a =>
			call("ecs_posnext.ecs_posnext.api.dispatcher.mark_delivery_failed", {
				assignment: a.name,
				reason: deliveryFailedReason.value.trim(),
			})
		))
		showSuccess(__("Marked as Failed — appears in Need My Action"))
		deliveryFailedModal.value = null
		deliveryFailedReason.value = ""
		await Promise.all([loadDrivers(), loadActiveAssignments()])
	} catch (e) {
		deliveryFailedError.value = errMsg(e)
	} finally {
		statusLoading.value = false
	}
}

// ── Helpers ───────────────────────────────────────────────────────────────
function errMsg(e) { return e?.messages?.[0] || e?.message || String(e) }
function fmtCurrency(val) {
	if (val == null) return "—"
	return new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val)
}
function initials(name) {
	if (!name) return "?"
	return name.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase()
}
function statusBadge(status) {
	const map = { "Assigned": "bg-blue-900 text-blue-300", "Picked Up": "bg-purple-900 text-purple-300", "Out for Delivery": "bg-amber-900 text-amber-300" }
	return `text-xs rounded-full px-2 py-0.5 font-bold ${map[status] || "bg-gray-700 text-gray-400"}`
}

function playNewOrderSound() {
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

let prevOrderCount = -1
watch(orders, (newOrders) => {
	const count = newOrders.length
	if (prevOrderCount >= 0 && count > prevOrderCount) playNewOrderSound()
	prevOrderCount = count
}, { deep: false })

// ── Open Shift ────────────────────────────────────────────────────────────
async function doOpenShift() {
	if (!openShiftProfile.value) return
	openShiftLoading.value = true
	openShiftError.value = null
	try {
		const shift = await call("ecs_posnext.ecs_posnext.api.dispatcher.open_dispatcher_shift", {
			pos_profile: openShiftProfile.value,
		})
		currentShift.value = shift
		openShiftModal.value = false
		openShiftProfile.value = ""
		showSuccess(__("Shift opened: ") + shift.name)
		loadPaymentModes()
		await refresh()
	} catch (e) {
		openShiftError.value = errMsg(e)
	} finally {
		openShiftLoading.value = false
	}
}

// ── Data loading ──────────────────────────────────────────────────────────
async function loadShift() {
	try { currentShift.value = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_open_shift") }
	catch { currentShift.value = null }
}
async function loadPosProfiles() {
	try { posProfiles.value = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_pos_profiles") || [] }
	catch { posProfiles.value = [] }
}
async function loadPaymentModes() {
	try { paymentModes.value = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_pos_payment_modes") || [] }
	catch { paymentModes.value = [] }
}
async function loadOrders() {
	try {
		const raw = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_unassigned_orders") || []
		// Newest orders first (by placement time).
		const placedAt = (o) => new Date(`${o.posting_date} ${o.posting_time}`).getTime() || 0
		raw.sort((a, b) => placedAt(b) - placedAt(a))
		orders.value = raw
	} catch { orders.value = [] }
}
async function loadDrivers() {
	try { drivers.value = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_available_drivers", { branch: currentShift.value?.branch || null }) || [] }
	catch { drivers.value = [] }
}
async function loadActiveAssignments() {
	try { activeAssignments.value = await call("ecs_posnext.ecs_posnext.api.dispatcher.get_active_assignments") || [] }
	catch { activeAssignments.value = [] }
}
async function refresh() {
	loading.value = true
	try { await Promise.all([loadOrders(), loadDrivers(), loadActiveAssignments()]) }
	finally { loading.value = false }
}

// ── Order selection ───────────────────────────────────────────────────────
function toggleOrder(name) {
	const idx = selectedOrders.value.indexOf(name)
	if (idx === -1) selectedOrders.value.push(name)
	else selectedOrders.value.splice(idx, 1)
}
function assignToDriver(driver) {
	if (selectedOrders.value.length === 0) { showError(__("Select at least one order first")); return }
	if (!driverCanTake(driver)) {
		showError(__("الطيار وصل الحد الأقصى للأوردرات") + ` (${maxDriverOrders.value})`)
		return
	}
	pendingAssign.value = { driver, orders: [...selectedOrders.value] }
}
async function doAssign() {
	if (!pendingAssign.value) return
	assignLoading.value = true
	try {
		await call("ecs_posnext.ecs_posnext.api.dispatcher.create_assignments", {
			driver: pendingAssign.value.driver.name,
			orders: JSON.stringify(pendingAssign.value.orders),
		})
		showSuccess(__("Assignments created"))
		selectedOrders.value = []; pendingAssign.value = null
		await Promise.all([loadOrders(), loadDrivers(), loadActiveAssignments()])
	} catch (e) { showError(errMsg(e)) }
	finally { assignLoading.value = false }
}

// ── Realtime ──────────────────────────────────────────────────────────────
function onRealtimeRefresh() { loadOrders(); loadDrivers(); loadActiveAssignments() }

onMounted(async () => {
	await loadShift()
	loadPosProfiles()
	loadPaymentModes()
	await refresh()
	timerInterval = setInterval(() => { timerTick.value++ }, 1000)
	const socket = initSocket()
	if (socket) {
		socket.connect()
		socket.on("dispatch_desk_refresh", onRealtimeRefresh)
		socket.on("kds_update", loadOrders)
	}
})
onUnmounted(() => {
	clearInterval(timerInterval)
	const socket = initSocket()
	if (socket) { socket.off("dispatch_desk_refresh", onRealtimeRefresh); socket.off("kds_update", loadOrders) }
})
</script>
