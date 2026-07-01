<template>
	<div class="flex flex-col h-screen bg-gray-50 overflow-hidden">
		<!-- Header -->
		<header class="flex-shrink-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm z-10">
			<div class="flex items-center gap-4">
				<button
					@click="goBack"
					class="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
					</svg>
				</button>
				<div>
					<h1 class="text-2xl font-bold text-gray-900">{{ __('Global Cash Management') }}</h1>
					<p class="text-sm text-gray-500 mt-0.5">{{ __('View and transfer cash balances across all branches') }}</p>
				</div>
			</div>
			<div class="flex items-center gap-3">
				<button
					@click="fetchBalances"
					:disabled="loading"
					class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors font-medium shadow-sm disabled:opacity-50"
				>
					<svg :class="['w-5 h-5', loading ? 'animate-spin text-blue-500' : 'text-gray-500']" fill="none" viewBox="0 0 24 24">
						<circle v-if="loading" class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path v-if="loading" class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						<path v-else stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
					</svg>
					<span>{{ __('Refresh') }}</span>
				</button>
			</div>
		</header>

		<!-- Main Content -->
		<main class="flex-1 overflow-y-auto p-6 md:p-8">
			<div class="max-w-6xl mx-auto">
				<!-- Summary Cards -->
				<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
					<div class="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-md relative overflow-hidden">
						<div class="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-white opacity-10 rounded-full blur-xl"></div>
						<h3 class="text-blue-100 font-medium mb-1">{{ __('Total Available Cash') }}</h3>
						<div class="text-3xl font-bold tracking-tight">
							{{ formatCurrency(totalBalance, defaultCurrency) }}
						</div>
					</div>
					<div class="bg-white rounded-xl p-6 border border-gray-200 shadow-sm flex flex-col justify-center">
						<h3 class="text-gray-500 font-medium mb-1">{{ __('Active Branches') }}</h3>
						<div class="text-3xl font-bold text-gray-900 tracking-tight">{{ branches.length }}</div>
					</div>
				</div>

				<!-- Data Table -->
				<div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
					<div class="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
						<h2 class="text-lg font-bold text-gray-800">{{ __('Branch Balances') }}</h2>
						<div class="relative w-64">
							<div class="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
								<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
							</div>
							<input v-model="searchQuery" type="text" class="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full ps-10 p-2" :placeholder="__('Search branches...')">
						</div>
					</div>
					
					<div v-if="loading && branches.length === 0" class="p-12 flex justify-center">
						<svg class="animate-spin h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
					</div>
					
					<div v-else-if="filteredBranches.length === 0" class="p-12 text-center">
						<div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
							<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
						</div>
						<h3 class="text-lg font-medium text-gray-900">{{ __('No branches found') }}</h3>
						<p class="text-gray-500 mt-1">{{ searchQuery ? __('Try adjusting your search query.') : __('No active POS Profiles with configured cash accounts were found.') }}</p>
					</div>
					
					<div v-else class="overflow-x-auto">
						<table class="w-full text-left border-collapse">
							<thead>
								<tr class="bg-gray-50 border-b border-gray-200 text-xs uppercase tracking-wider text-gray-500">
									<th class="px-6 py-4 font-semibold">{{ __('Branch / POS Profile') }}</th>
									<th class="px-6 py-4 font-semibold">{{ __('Cash Account') }}</th>
									<th class="px-6 py-4 font-semibold text-right">{{ __('Available Balance') }}</th>
									<th class="px-6 py-4 font-semibold text-center w-32">{{ __('Action') }}</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-200">
								<tr v-for="branch in filteredBranches" :key="branch.pos_profile" class="hover:bg-gray-50/50 transition-colors">
									<td class="px-6 py-4">
										<div class="font-medium text-gray-900">{{ branch.pos_profile }}</div>
										<div class="text-xs text-gray-500 mt-0.5">{{ branch.company }}</div>
									</td>
									<td class="px-6 py-4">
										<div class="inline-flex items-center px-2.5 py-1 rounded-md bg-gray-100 text-gray-700 text-xs font-medium border border-gray-200">
											{{ branch.account }}
										</div>
									</td>
									<td class="px-6 py-4 text-right">
										<div class="font-bold text-gray-900 text-lg">
											{{ formatCurrency(branch.balance, branch.currency) }}
										</div>
									</td>
									<td class="px-6 py-4 text-center">
										<button
											@click="openTransferModal(branch)"
											:disabled="branch.balance <= 0"
											class="inline-flex items-center justify-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
										>
											{{ __('Transfer') }}
										</button>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>
		</main>

		<!-- Transfer Modal -->
		<Transition name="fade">
			<div v-if="showTransferModal" class="fixed inset-0 bg-black/50 z-[400] flex items-center justify-center p-4" @click.self="closeTransferModal">
				<div class="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col">
					<div class="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
						<h3 class="text-lg font-bold text-gray-900">{{ __('Transfer Cash') }}</h3>
						<button @click="closeTransferModal" class="text-gray-400 hover:text-gray-600 transition-colors">
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
						</button>
					</div>
					
					<div class="p-6 flex flex-col gap-5">
						<div class="bg-blue-50 rounded-lg p-4 border border-blue-100">
							<div class="text-sm text-blue-800 mb-1">{{ __('From Branch') }}: <span class="font-bold">{{ selectedBranch?.pos_profile }}</span></div>
							<div class="text-sm text-blue-800">{{ __('Available') }}: <span class="font-bold text-lg">{{ formatCurrency(selectedBranch?.balance, selectedBranch?.currency) }}</span></div>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1.5">{{ __('Amount') }}</label>
							<div class="relative">
								<input
									v-model.number="transferForm.amount"
									type="number"
									step="0.01"
									min="0.01"
									:max="selectedBranch?.balance"
									class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-lg font-medium"
									:placeholder="__('Enter amount')"
								/>
								<button
									@click="transferForm.amount = selectedBranch?.balance"
									class="absolute inset-y-1 end-1 px-3 bg-gray-100 text-gray-700 text-xs font-semibold rounded-md hover:bg-gray-200 transition-colors"
								>
									{{ __('MAX') }}
								</button>
							</div>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1.5">{{ __('Destination Account (Optional)') }}</label>
							<select
								v-model="transferForm.to_account"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white"
							>
								<option value="">{{ selectedBranch?.manager_account || __('Default manager account') }}</option>
								<option v-for="account in destinationAccounts" :key="account.name" :value="account.name">
									{{ account.name }}
								</option>
							</select>
							<p class="text-xs text-gray-500 mt-1">{{ __('Leave blank to use the default manager account.') }}</p>
						</div>

						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1.5">{{ __('Remarks') }}</label>
							<input
								v-model="transferForm.remarks"
								type="text"
								class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
								:placeholder="__('Transfer remarks')"
							/>
						</div>
					</div>
					
					<div class="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
						<button @click="closeTransferModal" class="px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-white transition-colors">
							{{ __('Cancel') }}
						</button>
						<button 
							@click="submitTransfer" 
							:disabled="isSubmitting || !transferForm.amount || transferForm.amount <= 0 || transferForm.amount > selectedBranch?.balance"
							class="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
						>
							<svg v-if="isSubmitting" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							<span>{{ isSubmitting ? __('Processing...') : __('Confirm Transfer') }}</span>
						</button>
					</div>
				</div>
			</div>
		</Transition>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { useToast } from '@/composables/useToast'
import { useFormatters } from '@/composables/useFormatters'
import { session } from '@/data/session'

const router = useRouter()
const { showError, showSuccess } = useToast()
const { formatCurrency } = useFormatters()

const loading = ref(false)
const isSubmitting = ref(false)
const branches = ref([])
const destinationAccounts = ref([])
const searchQuery = ref('')
const defaultCurrency = ref('USD')

const showTransferModal = ref(false)
const selectedBranch = ref(null)
const transferForm = ref({
	amount: null,
	to_account: '',
	remarks: ''
})

const filteredBranches = computed(() => {
	if (!searchQuery.value) return branches.value
	
	const q = searchQuery.value.toLowerCase()
	return branches.value.filter(b => 
		(b.pos_profile && b.pos_profile.toLowerCase().includes(q)) || 
		(b.company && b.company.toLowerCase().includes(q)) ||
		(b.account && b.account.toLowerCase().includes(q))
	)
})

const totalBalance = computed(() => {
	return branches.value.reduce((sum, branch) => sum + (branch.balance || 0), 0)
})

onMounted(() => {
	// Set default currency from session if available
	if (session.defaults && session.defaults.currency) {
		defaultCurrency.value = session.defaults.currency
	}
	fetchBalances()
})

function goBack() {
	router.push({ name: 'POSSale' })
}

async function fetchBalances() {
	loading.value = true
	try {
		const res = await call("ecs_posnext.api.cash_management.get_all_branches_cash_balances")
		if (res && Array.isArray(res)) {
			branches.value = res
			// Update default currency from first branch if possible
			if (res.length > 0 && res[0].currency) {
				defaultCurrency.value = res[0].currency
			}
		}
	} catch (error) {
		console.error("Failed to fetch branch balances:", error)
		showError(__("Could not load cash balances."))
	} finally {
		loading.value = false
	}
}

function openTransferModal(branch) {
	selectedBranch.value = branch
	transferForm.value = {
		amount: null,
		to_account: '',
		remarks: ''
	}
	showTransferModal.value = true
	fetchDestinationAccounts(branch.company)
}

async function fetchDestinationAccounts(company) {
	if (!company) return;
	try {
		const res = await call("ecs_posnext.api.cash_management.get_destination_accounts", { company })
		if (res && Array.isArray(res)) {
			destinationAccounts.value = res
		}
	} catch (error) {
		console.error("Failed to fetch destination accounts:", error)
	}
}

function closeTransferModal() {
	showTransferModal.value = false
	setTimeout(() => {
		selectedBranch.value = null
	}, 300) // wait for animation
}

async function submitTransfer() {
	if (!selectedBranch.value) return
	if (transferForm.value.amount <= 0 || transferForm.value.amount > selectedBranch.value.balance) return
	
	isSubmitting.value = true
	try {
		const res = await call("ecs_posnext.api.cash_management.transfer_cash", {
			pos_profile: selectedBranch.value.pos_profile,
			company: selectedBranch.value.company,
			amount: transferForm.value.amount,
			to_account: transferForm.value.to_account || null,
			remarks: transferForm.value.remarks || null
		})
		
		showSuccess(res.message || __("Cash transferred successfully."))
		closeTransferModal()
		await fetchBalances() // Refresh data
		
	} catch (error) {
		console.error("Transfer failed:", error)
		showError(error.messages?.[0] || error.message || __("Transfer failed."))
	} finally {
		isSubmitting.value = false
	}
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}

::-webkit-scrollbar {
	width: 8px;
	height: 8px;
}
::-webkit-scrollbar-track {
	background: #f1f5f9; 
}
::-webkit-scrollbar-thumb {
	background: #cbd5e1; 
	border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
	background: #94a3b8; 
}
</style>
