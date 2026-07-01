import { call } from "@/utils/apiWrapper"
import { isOffline } from "@/utils/offline"
import { logger } from "@/utils/logger"
import { useRealtimeCustomers } from "@/composables/useRealtimeCustomers"
import { defineStore } from "pinia"
import { computed, ref } from "vue"

const log = logger.create("CustomerSearch")

const RECENT_KEY = "pos_recent_customers_v2"
const FREQUENT_KEY = "pos_frequent_customers_v2"
const MAX_RECENT = 20
const MAX_FREQUENT = 30

export const useCustomerSearchStore = defineStore("customerSearch", () => {
	// State — only recent/frequent stored locally (full objects)
	const recentCustomers = ref([])
	const frequentCustomers = ref([])
	const serverResults = ref([])
	const searchTerm = ref("")
	const loading = ref(false)
	const selectedIndex = ref(-1)

	// Backward-compat: allCustomers = deduplicated recent+frequent
	const allCustomers = computed(() => {
		const seen = new Set()
		return [...recentCustomers.value, ...frequentCustomers.value].filter(c => {
			if (seen.has(c.name)) return false
			seen.add(c.name)
			return true
		})
	})

	const filteredCustomers = computed(() => {
		const term = searchTerm.value.trim()
		if (!term) return allCustomers.value.slice(0, 30)
		return serverResults.value
	})

	const recommendations = computed(() => {
		const term = searchTerm.value.trim().toLowerCase()
		if (!term || term.length < 2 || loading.value) return []
		if (serverResults.value.length < 3) {
			return [{ type: "create", text: __('Create new customer: {0}', [term]), icon: "➕" }]
		}
		return []
	})

	// Server search — called with debounce from UI
	async function searchServer(posProfile, term) {
		if (!term) {
			serverResults.value = []
			return
		}

		// Offline: search within recent+frequent locally
		if (isOffline()) {
			const t = term.toLowerCase()
			serverResults.value = allCustomers.value.filter(c =>
				(c.customer_name || "").toLowerCase().includes(t) ||
				(c.mobile_no || "").includes(t) ||
				(c.email_id || "").toLowerCase().includes(t)
			).slice(0, 20)
			return
		}

		loading.value = true
		try {
			const response = await call("ecs_posnext.api.customers.get_customers", {
				pos_profile: posProfile,
				search_term: term,
				limit: 30
			})
			serverResults.value = (response?.message || response || []).filter(c => !c.disabled)
		} catch (error) {
			log.error("Server search failed", error)
			serverResults.value = []
		} finally {
			loading.value = false
		}
	}

	function _saveHistory() {
		try {
			localStorage.setItem(RECENT_KEY, JSON.stringify(recentCustomers.value))
			localStorage.setItem(FREQUENT_KEY, JSON.stringify(frequentCustomers.value))
		} catch (e) {
			log.warn("Failed to persist customer history:", e)
		}
	}

	// Track selection — accepts full customer object
	function trackCustomerSelection(customer) {
		if (!customer || typeof customer === "string") return

		recentCustomers.value = [
			customer,
			...recentCustomers.value.filter(c => c.name !== customer.name)
		].slice(0, MAX_RECENT)

		frequentCustomers.value = [
			customer,
			...frequentCustomers.value.filter(c => c.name !== customer.name)
		].slice(0, MAX_FREQUENT)

		_saveHistory()
	}

	function loadCustomerHistory() {
		try {
			const recent = localStorage.getItem(RECENT_KEY)
			const frequent = localStorage.getItem(FREQUENT_KEY)
			if (recent) recentCustomers.value = JSON.parse(recent)
			if (frequent) frequentCustomers.value = JSON.parse(frequent)
		} catch (e) {
			log.warn("Failed to load customer history:", e)
		}
	}

	function addCustomerToCache(customer) {
		trackCustomerSelection(customer)
	}

	// Real-time updates — only touch recent/frequent cache
	const { onCustomerUpdate } = useRealtimeCustomers()
	onCustomerUpdate((data) => {
		const { name, action, customer_name, mobile_no, email_id, disabled } = data
		if (action === "delete" || disabled) {
			recentCustomers.value = recentCustomers.value.filter(c => c.name !== name)
			frequentCustomers.value = frequentCustomers.value.filter(c => c.name !== name)
		} else {
			const updated = { name, customer_name, mobile_no, email_id }
			recentCustomers.value = recentCustomers.value.map(c => c.name === name ? { ...c, ...updated } : c)
			frequentCustomers.value = frequentCustomers.value.map(c => c.name === name ? { ...c, ...updated } : c)
		}
		_saveHistory()
	})

	function setSearchTerm(term) {
		searchTerm.value = term
		selectedIndex.value = -1
		if (!term) serverResults.value = []
	}

	function clearSearch() {
		searchTerm.value = ""
		selectedIndex.value = -1
		serverResults.value = []
	}

	function setSelectedIndex(index) { selectedIndex.value = index }
	function resetSelectedIndex() { selectedIndex.value = -1 }

	// Compat: loadAllCustomers now just loads history (instant, no network)
	async function loadAllCustomers(posProfile, forceReload = false) {
		loadCustomerHistory()
	}

	return {
		allCustomers,
		searchTerm,
		loading,
		selectedIndex,
		recentCustomers,
		frequentCustomers,
		serverResults,
		filteredCustomers,
		recommendations,
		loadAllCustomers,
		loadCustomerHistory,
		searchServer,
		addCustomerToCache,
		trackCustomerSelection,
		setSearchTerm,
		clearSearch,
		setSelectedIndex,
		resetSelectedIndex,
	}
})
