<template>
	<div v-if="customer" class="flex flex-col h-full bg-white border-t border-gray-200 overflow-hidden">
		<!-- Profile Header -->
		<div class="flex items-center justify-between px-3 py-2 bg-gray-50 border-b border-gray-100">
			<div class="flex items-center gap-2">
				<div
					class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
					:class="profileBadgeClass"
				>
					{{ customerInitial }}
				</div>
				<div class="min-w-0">
					<p class="text-sm font-bold text-gray-900 truncate">{{ profile?.customer_name || customerDisplayName }}</p>
					<p class="text-[10px] text-gray-500">
						{{ profile?.mobile_no || customerMobile }} · {{ __("Orders") }}: {{ profile?.total_orders || 0 }}
					</p>
					<p v-if="profile?.last_order?.branch" class="text-[10px] text-blue-600 font-medium">
						{{ __("Last Visit") }}: {{ profile.last_order.branch }} · {{ profile.last_order.date }}
					</p>
					<p v-if="profile?.favorite_branch || profile?.last_branch" class="text-[10px] text-gray-500 flex items-center gap-1">
						<span>🏪</span>
						<span>{{ profile.favorite_branch || profile.last_branch }}</span>
					</p>
				</div>
			</div>
			<div class="flex items-center gap-1.5">
				<!-- Customer Type Badge -->
				<span v-if="profile?.customer_type === 'VIP'" class="px-2 py-0.5 bg-amber-100 text-amber-800 text-[10px] font-bold rounded-full uppercase">VIP</span>
				<span v-else-if="profile?.customer_type === 'Blacklist'" class="px-2 py-0.5 bg-red-100 text-red-700 text-[10px] font-bold rounded-full uppercase">{{ __("Blacklist") }}</span>
				<!-- Toggle button -->
				<button
					type="button"
					@click="expanded = !expanded"
					class="p-1 rounded hover:bg-gray-200 text-gray-500 transition-colors"
				>
					<svg class="w-4 h-4 transition-transform" :class="{ 'rotate-180': expanded }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
					</svg>
				</button>
			</div>
		</div>

		<!-- VIP / Blacklist quick toggles (sent for approval) -->
		<div v-if="customerName" class="flex items-center gap-2 px-3 py-1.5 border-b border-gray-100 bg-white">
			<button type="button" @click="requestStatus('VIP')" :disabled="!!statusBusy"
				:class="['flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg text-[11px] font-bold border transition-colors disabled:opacity-50',
					customerStatus.is_vip ? 'bg-amber-500 text-white border-amber-500' : 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100']">
				<span>⭐</span>
				<span>{{ customerStatus.is_vip ? __('VIP') : __('Make VIP') }}</span>
				<span v-if="vipPending" class="text-[9px] bg-black/20 px-1 rounded-full">{{ __('Pending') }}</span>
			</button>
			<button type="button" @click="requestStatus('Blacklist')" :disabled="!!statusBusy"
				:class="['flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg text-[11px] font-bold border transition-colors disabled:opacity-50',
					customerStatus.is_blacklist ? 'bg-red-600 text-white border-red-600' : 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100']">
				<span>🚫</span>
				<span>{{ customerStatus.is_blacklist ? __('Blacklisted') : __('Blacklist') }}</span>
				<span v-if="blacklistPending" class="text-[9px] bg-black/20 px-1 rounded-full">{{ __('Pending') }}</span>
			</button>
		</div>

		<!-- Loading -->
		<div v-if="loading" class="flex items-center justify-center py-6">
			<div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
		</div>

		<!-- Profile Content (collapsible) -->
		<div v-else-if="profile && expanded" class="flex-1 overflow-y-auto custom-scrollbar">
			<!-- Tabs -->
			<div class="flex border-b border-gray-100 px-2 pt-1">
				<button
					v-for="tab in tabs"
					:key="tab.id"
					@click="activeTab = tab.id"
					class="px-3 py-1.5 text-[11px] font-bold rounded-t transition-colors"
					:class="activeTab === tab.id ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50' : 'text-gray-500 hover:text-gray-700'"
				>
					{{ tab.label }}
					<span v-if="tab.badge" class="ml-1 px-1 py-0.5 bg-blue-100 text-blue-700 text-[9px] rounded-full">{{ tab.badge }}</span>
				</button>
			</div>

			<!-- Branch stats bar — always visible when branch is set -->
			<div v-if="props.branch" class="flex items-center gap-3 px-3 py-1.5 bg-blue-50 border-b border-blue-100 text-[10px]">
				<svg class="w-3 h-3 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 00-1-1h-2a1 1 0 00-1 1v5m4 0H9" />
				</svg>
				<span class="font-bold text-blue-700 truncate">{{ props.branch }}</span>
				<span class="text-gray-500">{{ __("Orders") }}: <span class="font-bold text-gray-700">{{ profile?.branch_total_orders || 0 }}</span></span>
				<span v-if="profile?.last_order_in_branch" class="text-gray-500">{{ __("Last") }}: <span class="font-bold text-gray-700">{{ profile.last_order_in_branch.date }}</span></span>
				<span v-if="!profile?.last_order_in_branch" class="text-gray-400 italic">{{ __("No orders yet") }}</span>
			</div>

			<div class="p-3">
				<!-- Favorites Tab -->
				<div v-if="activeTab === 'favorites'" class="space-y-3">
					<div v-if="profile.favorite_item" class="flex items-center gap-2 p-2 bg-amber-50 rounded-lg border border-amber-100">
						<span class="text-lg">⭐</span>
						<div>
							<p class="text-[10px] text-amber-600 font-bold uppercase">{{ __("Favorite Item") }}</p>
							<p class="text-xs font-medium text-gray-800">{{ profile.favorite_item }}</p>
						</div>
					</div>
					<div v-if="profile.favorite_branch" class="flex items-center gap-2 p-2 bg-purple-50 rounded-lg border border-purple-100">
						<span class="text-lg">🏪</span>
						<div>
							<p class="text-[10px] text-purple-600 font-bold uppercase">{{ __("Favorite Branch") }}</p>
							<p class="text-xs font-medium text-gray-800">{{ profile.favorite_branch }}</p>
						</div>
					</div>
					<div v-if="!profile.favorite_item && !profile.favorite_branch" class="text-center py-4">
						<p class="text-xs text-gray-400">{{ __("No favorites yet") }}</p>
					</div>
				</div>

				<!-- Last Order Tab -->
				<div v-if="activeTab === 'lastOrder'" class="space-y-2">
					<!-- Branch last order summary -->
					<div v-if="profile.last_order_in_branch" class="flex items-center gap-2 px-2 py-1.5 bg-blue-50 rounded-lg border border-blue-100">
						<svg class="w-3.5 h-3.5 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 00-1-1h-2a1 1 0 00-1 1v5m4 0H9" />
						</svg>
						<div class="min-w-0">
							<p class="text-[10px] text-blue-600 font-bold uppercase">{{ props.branch || __("Last Order in Branch") }}</p>
							<p class="text-[10px] text-gray-600">{{ profile.last_order_in_branch.date }} · {{ profile.last_order_in_branch.order_type || 'Pickup' }} · <span class="font-medium text-gray-800">{{ formatCurrency(profile.last_order_in_branch.grand_total) }}</span></p>
						</div>
					</div>
					<div v-if="profile.last_order" class="space-y-2">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-[10px] text-gray-500">{{ profile.last_order.date }} · {{ profile.last_order.order_type || 'Pickup' }}</p>
								<p class="text-xs font-bold text-gray-800">{{ formatCurrency(profile.last_order.grand_total) }}</p>
							</div>
							<button
								type="button"
								@click="handleReorder"
								class="px-3 py-1.5 bg-blue-600 text-white text-[11px] font-bold rounded-lg hover:bg-blue-700 transition-all active:scale-95 flex items-center gap-1"
							>
								<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
								</svg>
								{{ __("Reorder") }}
							</button>
						</div>
						<!-- Order Items -->
						<div class="space-y-1 max-h-[120px] overflow-y-auto custom-scrollbar">
							<div
								v-for="item in profile.last_order.items"
								:key="item.item_code"
								class="flex items-center justify-between px-2 py-1 bg-gray-50 rounded text-[11px]"
							>
								<span class="text-gray-700 truncate flex-1">{{ item.item_name }}</span>
								<span class="text-gray-500 ml-2">x{{ item.qty }}</span>
							</div>
						</div>
					</div>
					<div v-else class="text-center py-4">
						<p class="text-xs text-gray-400">{{ __("No previous orders") }}</p>
					</div>
				</div>

				<!-- Notes Tab -->
				<div v-if="activeTab === 'notes'" class="space-y-2">
					<!-- Add Note -->
					<div class="flex gap-2">
						<input
							v-model="newNote"
							type="text"
							:placeholder="__('Add a note...')"
							class="flex-1 h-8 px-3 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-400"
							@keydown.enter="addNote"
						/>
						<button
							type="button"
							@click="addNote"
							:disabled="!newNote.trim()"
							class="px-3 h-8 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
						>
							{{ __("Add") }}
						</button>
					</div>
					<!-- Notes List -->
					<div v-if="profile.notes?.length > 0" class="space-y-1.5 max-h-[100px] overflow-y-auto custom-scrollbar">
						<div
							v-for="(note, idx) in profile.notes"
							:key="idx"
							class="p-2 bg-yellow-50 rounded-lg border border-yellow-100"
						>
							<p class="text-xs text-gray-800">{{ note.content }}</p>
							<p class="text-[9px] text-gray-400 mt-0.5">{{ note.creation }}</p>
						</div>
					</div>
					<div v-else class="text-center py-3">
						<p class="text-xs text-gray-400">{{ __("No notes") }}</p>
					</div>
				</div>

				<!-- Coupons Tab -->
				<div v-if="activeTab === 'coupons'" class="space-y-2">
					<!-- Count summary -->
					<div class="flex items-center gap-2">
						<div class="flex-1 bg-gray-50 rounded-lg border border-gray-100 px-2 py-1.5 text-center">
							<p class="text-[10px] text-gray-500 uppercase tracking-wider">{{ __("Total") }}</p>
							<p class="text-sm font-bold text-gray-900">{{ profile.coupons_total || 0 }}</p>
						</div>
						<div class="flex-1 bg-green-50 rounded-lg border border-green-100 px-2 py-1.5 text-center">
							<p class="text-[10px] text-green-600 uppercase tracking-wider">{{ __("Unused") }}</p>
							<p class="text-sm font-bold text-green-800">{{ profile.coupons_unused || 0 }}</p>
						</div>
					</div>

					<div v-if="profile.coupons?.length > 0" class="space-y-1.5">
						<div
							v-for="coupon in profile.coupons"
							:key="coupon.name"
							class="flex items-center justify-between p-2 rounded-lg border"
							:class="isCouponExpired(coupon) ? 'bg-gray-50 border-gray-200' : 'bg-green-50 border-green-100'"
						>
							<div>
								<p class="text-xs font-bold" :class="isCouponExpired(coupon) ? 'text-gray-500' : 'text-green-800'">{{ coupon.coupon_code }}</p>
								<p class="text-[10px]" :class="isCouponExpired(coupon) ? 'text-red-500' : 'text-green-600'">
									{{ isCouponExpired(coupon) ? __("Expired") : __("Valid until") }}: {{ coupon.valid_upto }}
								</p>
							</div>
							<span class="text-lg">🎟️</span>
						</div>
					</div>
					<div v-else class="text-center py-4">
						<p class="text-xs text-gray-400">{{ __("No unused coupons") }}</p>
					</div>
				</div>

				<!-- Complaints Tab -->
				<div v-if="activeTab === 'complaints'" class="space-y-2">
					<!-- New Complaint Form -->
					<div class="bg-red-50 rounded-lg border border-red-100 p-2 space-y-2">
						<p class="text-[10px] font-bold text-red-700 uppercase">{{ __("New Complaint") }}</p>
						<select
							v-model="newComplaint.type"
							class="w-full h-7 px-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-red-400 bg-white"
						>
							<option value="">{{ __("Select type (optional)") }}</option>
							<option v-for="ct in complaintTypes" :key="ct.name" :value="ct.name">{{ ct.name }}</option>
						</select>
						<select
							v-model="newComplaint.branch"
							class="w-full h-7 px-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-red-400 bg-white"
						>
							<option value="">{{ __("Select branch *") }}</option>
							<option v-for="b in branches" :key="b.name" :value="b.name">{{ b.name }}</option>
						</select>
						<textarea
							v-model="newComplaint.details"
							:placeholder="__('Describe the complaint...')"
							rows="2"
							class="w-full px-2 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-red-400 resize-none"
						/>
						<button
							type="button"
							@click="submitComplaint"
							:disabled="!newComplaint.details.trim() || !newComplaint.branch || complaintSubmitting"
							class="w-full h-7 bg-red-600 text-white text-xs font-bold rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1"
						>
							<svg v-if="complaintSubmitting" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
							</svg>
							{{ complaintSubmitting ? __("Submitting...") : __("Submit Complaint") }}
						</button>
					</div>

					<!-- Complaints List -->
					<div v-if="complaintsLoading" class="flex justify-center py-3">
						<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-red-500"></div>
					</div>
					<div v-else-if="complaints.length > 0" class="space-y-1.5 max-h-[160px] overflow-y-auto custom-scrollbar">
						<div
							v-for="c in complaints"
							:key="c.name"
							class="p-2 bg-white rounded-lg border border-gray-100 shadow-sm"
						>
							<div class="flex items-center justify-between mb-0.5">
								<span class="text-[10px] font-bold text-gray-700">{{ c.custom_complaint_number || c.name }}</span>
								<span
									class="px-1.5 py-0.5 text-[9px] font-bold rounded-full"
									:class="{
										'bg-red-100 text-red-700': c.status === 'Open',
										'bg-yellow-100 text-yellow-700': c.status === 'In Progress',
										'bg-green-100 text-green-700': c.status === 'Resolved',
										'bg-gray-100 text-gray-600': c.status === 'Rejected',
									}"
								>{{ c.status }}</span>
							</div>
							<p v-if="c.type" class="text-[9px] text-blue-600 mb-0.5">{{ c.type }}</p>
							<p class="text-[10px] text-gray-600 line-clamp-2">{{ c.complaint_details }}</p>
							<p class="text-[9px] text-gray-400 mt-0.5">{{ formatDate(c.complaint_date || c.creation) }}</p>
						</div>
					</div>
					<div v-else class="text-center py-3">
						<p class="text-xs text-gray-400">{{ __("No complaints on record") }}</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue"
import { call } from "@/utils/apiWrapper"
import { useToast } from "@/composables/useToast"

const props = defineProps({
	customer: {
		type: [String, Object],
		default: null
	},
	posProfile: {
		type: String,
		default: null
	},
	branch: {
		type: String,
		default: null
	},
	currency: {
		type: String,
		default: ""
	}
})

const emit = defineEmits(["reorder"])
const { showSuccess, showError } = useToast()

const profile = ref(null)
const loading = ref(false)
const expanded = ref(true)
const activeTab = ref("favorites")
const newNote = ref("")

// Complaints state
const complaints = ref([])
const complaintsLoading = ref(false)
const complaintSubmitting = ref(false)
const complaintTypes = ref([])
const branches = ref([])
const newComplaint = ref({ details: "", type: "", branch: "" })

const tabs = computed(() => [
	{ id: "favorites", label: __("Favorites"), badge: null },
	{ id: "lastOrder", label: __("Last Order"), badge: null },
	{ id: "notes", label: __("Notes"), badge: profile.value?.notes?.length || null },
	{ id: "coupons", label: __("Coupons"), badge: profile.value?.coupons_unused || null },
	{ id: "complaints", label: __("Complaints"), badge: complaints.value.length || null },
])

// A coupon is expired when its valid_upto date is before today.
function isCouponExpired(coupon) {
	if (!coupon?.valid_upto) return false
	return new Date(coupon.valid_upto) < new Date(new Date().toDateString())
}

const customerName = computed(() => {
	if (!props.customer) return null
	return typeof props.customer === 'string' ? props.customer : props.customer.name
})

const customerDisplayName = computed(() => {
	if (!props.customer) return ""
	if (typeof props.customer === 'object') return props.customer.customer_name || props.customer.name || ""
	return props.customer
})

const customerMobile = computed(() => {
	if (!props.customer || typeof props.customer !== 'object') return ""
	return props.customer.mobile_no || ""
})

const customerInitial = computed(() => {
	const name = profile.value?.customer_name || customerDisplayName.value || ""
	return name.charAt(0).toUpperCase()
})

const profileBadgeClass = computed(() => {
	if (profile.value?.customer_type === 'VIP') return 'bg-amber-500'
	if (profile.value?.customer_type === 'Blacklist') return 'bg-red-500'
	return 'bg-blue-500'
})

function formatCurrency(amount) {
	if (!amount) return "0"
	return new Intl.NumberFormat(undefined, {
		style: "currency",
		currency: props.currency || "EGP",
		minimumFractionDigits: 2
	}).format(amount)
}

async function loadProfile() {
	const custId = customerName.value
	if (!custId) {
		profile.value = null
		return
	}
	loading.value = true
	try {
		const res = await call("ecs_posnext.api.customers.get_customer_profile", {
			customer: custId,
			pos_profile: props.posProfile || "",
			branch: props.branch || ""
		})
		console.log("[CustomerProfile] API response for", custId, ":", res)
		if (res && typeof res === 'object') {
			profile.value = res
		} else {
			console.warn("[CustomerProfile] Unexpected response:", res)
			profile.value = null
		}
	} catch (err) {
		console.error("[CustomerProfile] Error loading profile for", custId, ":", err)
		profile.value = null
	} finally {
		loading.value = false
	}
}

// ---- VIP / Blacklist status (request + approval) ----
const customerStatus = ref({})
const statusBusy = ref("")

async function loadStatus() {
	const custId = customerName.value
	if (!custId) { customerStatus.value = {}; return }
	try {
		customerStatus.value = (await call("ecs_posnext.api.customer_status.get_customer_status", { customer: custId })) || {}
	} catch (e) {
		customerStatus.value = {}
	}
}

const vipPending = computed(() => !!customerStatus.value?.pending?.VIP)
const blacklistPending = computed(() => !!customerStatus.value?.pending?.Blacklist)

async function requestStatus(type) {
	const custId = customerName.value
	if (!custId || statusBusy.value) return
	const isOn = type === "VIP" ? customerStatus.value.is_vip : customerStatus.value.is_blacklist
	statusBusy.value = type
	try {
		await call("ecs_posnext.api.customer_status.request_customer_status", {
			customer: custId,
			request_type: type,
			enable: isOn ? 0 : 1,
			pos_profile: props.posProfile || "",
		})
		showSuccess(__("Request sent for approval"))
		await loadStatus()
	} catch (e) {
		showError(e.message || __("Failed to send request"))
	} finally {
		statusBusy.value = ""
	}
}

async function addNote() {
	if (!newNote.value.trim() || !customerName.value) return
	try {
		const res = await call("ecs_posnext.api.customers.add_customer_note", {
			customer: customerName.value,
			note: newNote.value.trim()
		})
		if (res) {
			if (!profile.value.notes) profile.value.notes = []
			profile.value.notes.unshift(res)
			newNote.value = ""
			showSuccess(__("Note added"))
		}
	} catch (err) {
		showError(err.message || __("Failed to add note"))
	}
}

function handleReorder() {
	if (profile.value?.last_order?.items) {
		emit("reorder", profile.value.last_order.items)
	}
}

function formatDate(dateStr) {
	if (!dateStr) return ""
	return new Date(dateStr).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
}

async function loadComplaints() {
	if (!customerName.value) return
	complaintsLoading.value = true
	try {
		complaints.value = await call("ecs_posnext.api.customers.get_customer_complaints", {
			customer: customerName.value,
		}) || []
	} catch (err) {
		complaints.value = []
	} finally {
		complaintsLoading.value = false
	}
}

async function loadComplaintTypes() {
	if (complaintTypes.value.length > 0) return
	try {
		complaintTypes.value = await call("ecs_posnext.api.customers.get_complaint_types") || []
	} catch {}
}

async function submitComplaint() {
	if (!newComplaint.value.details.trim() || !customerName.value || !newComplaint.value.branch) return
	complaintSubmitting.value = true
	try {
		const result = await call("ecs_posnext.api.customers.create_customer_complaint", {
			customer: customerName.value,
			complaint_details: newComplaint.value.details.trim(),
			complaint_type: newComplaint.value.type || null,
			branch: newComplaint.value.branch,
		})
		if (result) {
			complaints.value.unshift(result)
			newComplaint.value = { details: "", type: "", branch: props.branch || "" }
			showSuccess(__("Complaint {0} submitted", [result.custom_complaint_number]))
		}
	} catch (err) {
		showError(err.message || __("Failed to submit complaint"))
	} finally {
		complaintSubmitting.value = false
	}
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

watch(activeTab, (tab) => {
	if (tab === "complaints") {
		loadComplaints()
		loadComplaintTypes()
		loadBranches()
		if (props.branch && !newComplaint.value.branch) {
			newComplaint.value.branch = props.branch
		}
	}
})

watch(customerName, (newVal) => {
	if (newVal) {
		loadProfile()
		loadStatus()
		complaints.value = []
		if (activeTab.value === "complaints") {
			loadComplaints()
		}
	} else {
		profile.value = null
		complaints.value = []
	}
}, { immediate: true })

watch(() => props.branch, (newBranch, oldBranch) => {
	if (newBranch !== oldBranch && customerName.value) {
		loadProfile()
	}
	if (newBranch) {
		newComplaint.value.branch = newBranch
	}
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
	width: 3px;
}
.custom-scrollbar::-webkit-scrollbar-track {
	background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
	background: #e2e8f0;
	border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
	background: #cbd5e1;
}
</style>
