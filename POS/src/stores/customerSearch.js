import { call } from "@/utils/apiWrapper"
import { isOffline } from "@/utils/offline"
import { offlineWorker } from "@/utils/offline/workerClient"
import { logger } from "@/utils/logger"
import { useRealtimeCustomers } from "@/composables/useRealtimeCustomers"
import { defineStore } from "pinia"
import { computed, ref } from "vue"

const log = logger.create("CustomerSearch")

export const useCustomerSearchStore = defineStore("customerSearch", () => {
	// State
	const allCustomers = ref([])
	const searchTerm = ref("")
	const loading = ref(false)
	const selectedIndex = ref(-1)
	const recentSearches = ref([])
	const frequentCustomers = ref([])

	// Performance optimization: Pre-computed search indices
	const searchIndex = ref(new Map())
	const resultCache = ref(new Map())

	// Server-side search results (online) or indexed cache results (offline). This is
	// the primary result set — no longer a scan over the full in-memory customer list.
	const serverResults = ref([])
	const searching = ref(false)
	const lastPosProfile = ref(null)
	// Full recent-customer objects (so empty-search can show them without loading all).
	const recentObjects = ref([])
	let searchDebounce = null

	// Sync state
	const CUSTOMERS_SYNC_KEY = "pos_customers_last_sync"
	const RECENT_OBJECTS_KEY = "pos_recent_customer_objects"
	let serverDataFresh = false

	// Ultra-fast search helper - optimized for speed
	function quickMatch(search, customer) {
		const term = search.toLowerCase()

		// Get or create cached lowercase strings for this customer
		let cached = searchIndex.value.get(customer.name)
		if (!cached) {
			cached = {
				name: (customer.customer_name || "").toLowerCase(),
				mobile: (customer.mobile_no || "").toLowerCase(),
				email: (customer.email_id || "").toLowerCase(),
				id: (customer.name || "").toLowerCase(),
				// Pre-compute word starts for super fast word matching
				nameWords: (customer.customer_name || "").toLowerCase().split(" "),
			}
			searchIndex.value.set(customer.name, cached)
		}

		// Lightning-fast checks in priority order
		// Name checks (most important)
		if (cached.name === term) return 300 // Exact name match
		if (cached.name.startsWith(term)) return 270 // Name starts with

		// Check each word start
		for (const word of cached.nameWords) {
			if (word.startsWith(term)) return 240 // Word in name starts with
		}

		if (cached.name.includes(term)) return 180 // Name contains

		// Phone checks (very important for POS)
		if (cached.mobile === term) return 250
		if (cached.mobile.startsWith(term)) return 225
		if (cached.mobile.includes(term)) return 150

		// Email checks
		if (cached.email.startsWith(term)) return 200
		if (cached.email.includes(term)) return 120

		// ID checks
		if (cached.id.startsWith(term)) return 135
		if (cached.id.includes(term)) return 90

		return 0 // No match
	}

	// Getters
	// Results come from the server (online) or the indexed IndexedDB cache (offline),
	// fetched in runSearch(); we no longer scan the full in-memory customer list.
	const filteredCustomers = computed(() => {
		const term = searchTerm.value.trim()

		// Empty search: show recent customers first, then the browse page.
		if (!term) {
			const seen = new Set()
			const merged = []
			for (const c of [...recentObjects.value, ...serverResults.value]) {
				if (!c || seen.has(c.name)) continue
				seen.add(c.name)
				merged.push(c)
			}
			return merged.slice(0, 50)
		}

		// Term search: rank the fetched matches by relevance (quickMatch scoring).
		return [...serverResults.value]
			.map((cust) => ({ cust, score: quickMatch(term, cust) }))
			.sort((a, b) => b.score - a.score)
			.map((r) => r.cust)
			.slice(0, 50)
	})

	// Recommendations based on search patterns
	const recommendations = computed(() => {
		const term = searchTerm.value.trim().toLowerCase()
		if (!term || term.length < 2) return []

		const recs = []

		// Check if it looks like a phone number
		if (/^\d+$/.test(term)) {
			recs.push({
				type: "phone",
				text: __("Search by phone: {0}", [term]),
				icon: "📱",
			})
		}

		// Check if it looks like an email
		if (term.includes("@")) {
			recs.push({
				type: "email",
				text: __("Search by email: {0}", [term]),
				icon: "✉️",
			})
		}

		// Suggest creating new customer if no exact matches
		const exactMatch = serverResults.value.some(
			(c) => c.customer_name?.toLowerCase() === term,
		)
		if (!exactMatch && filteredCustomers.value.length < 5) {
			recs.push({
				type: "create",
				text: __("Create new customer: {0}", [term]),
				icon: "➕",
			})
		}

		return recs
	})

	// Actions
	// Fetch matches for a term: server when online, indexed IndexedDB cache offline.
	async function searchCustomersServer(term) {
		const trimmed = (term || "").trim()
		if (!isOffline()) {
			const response = await call("ecs_posnext.api.customers.get_customers", {
				pos_profile: lastPosProfile.value,
				search_term: trimmed,
				limit: 50,
			})
			const rows = response?.message || response || []
			return rows.filter((c) => !c.disabled)
		}
		// Offline: indexed prefix search over the cached customers (bounded).
		const rows = await offlineWorker.searchCachedCustomers(trimmed, 50)
		return (rows || []).filter((c) => !c.disabled)
	}

	// Debounced search driver — updates serverResults for the current term.
	function runSearch(term) {
		if (searchDebounce) clearTimeout(searchDebounce)
		searchDebounce = setTimeout(async () => {
			searching.value = true
			try {
				serverResults.value = await searchCustomersServer(term)
			} catch (error) {
				log.error("Customer search failed:", error)
				serverResults.value = []
			} finally {
				searching.value = false
			}
		}, 250)
	}

	// Keep the IndexedDB cache fresh for OFFLINE use — runs in the background and must
	// NOT block the dialog. Uses modified_since delta so subsequent syncs are small.
	async function syncCustomerCache(posProfile, forceReload = false) {
		if (!posProfile || isOffline()) return
		if (!forceReload && serverDataFresh) return
		try {
			const lastSync = forceReload
				? null
				: localStorage.getItem(CUSTOMERS_SYNC_KEY)
			const response = await call("ecs_posnext.api.customers.get_customers", {
				pos_profile: posProfile,
				search_term: "",
				limit: 0,
				modified_since: lastSync,
			})
			const delta = response?.message || response || []
			if (delta.length > 0) {
				const active = delta.filter((c) => !c.disabled)
				const disabled = delta.filter((c) => c.disabled)
				if (active.length) await offlineWorker.cacheCustomers(active)
				if (disabled.length)
					await offlineWorker.deleteCustomers(disabled.map((c) => c.name))
				log.debug(
					`Background cache sync: ${active.length} active, ${disabled.length} disabled`,
				)
			}
			serverDataFresh = true
			localStorage.setItem(CUSTOMERS_SYNC_KEY, new Date().toISOString())
		} catch (error) {
			log.warn("Background customer cache sync failed:", error)
		}
	}

	// Called when the customer dialog opens. Fast: shows results immediately (server /
	// indexed cache) and refreshes the offline cache in the background (non-blocking).
	async function loadAllCustomers(posProfile, forceReload = false) {
		if (!posProfile) return
		lastPosProfile.value = posProfile

		// Instant: populate the browse/search results for the current term.
		runSearch(searchTerm.value)

		// Background (do NOT await): keep the offline cache fresh.
		syncCustomerCache(posProfile, forceReload)
	}

	async function addCustomerToCache(customer) {
		try {
			// Add to local array (at the beginning for visibility)
			const existingWithoutNew = allCustomers.value.filter(
				(cust) => cust.name !== customer.name,
			)
			allCustomers.value = [customer, ...existingWithoutNew]

			// Cache in worker (IndexedDB)
			await offlineWorker.cacheCustomers([customer])

			// Clear BOTH caches to ensure new customer appears in search
			searchIndex.value.clear()
			resultCache.value.clear()

			log.success(`New customer cached: ${customer.customer_name}`)
		} catch (error) {
			log.error("Error caching newly created customer:", error)
		}
	}

	// Real-time Push Integration
	const { onCustomerUpdate } = useRealtimeCustomers()
	onCustomerUpdate(async (data) => {
		const { name, action, customer_name, mobile_no, email_id, disabled } = data
		console.log("Customer update via real-time:", data)
		if (action === "delete" || disabled) {
			// Remove from memory
			allCustomers.value = allCustomers.value.filter((c) => c.name !== name)

			// Remove from IndexedDB
			await offlineWorker.deleteCustomers([name])

			// Clear search caches
			searchIndex.value.clear()
			resultCache.value.clear()

			log.info(`Customer removed/disabled via real-time: ${name}`)
		} else {
			// Upsert (Create or Update)
			const customer = {
				name,
				customer_name,
				mobile_no,
				email_id,
				disabled: !!disabled,
			}
			await addCustomerToCache(customer)
		}
	})

	function setSearchTerm(term) {
		searchTerm.value = term
		selectedIndex.value = -1
		runSearch(term)
	}

	function clearSearch() {
		searchTerm.value = ""
		selectedIndex.value = -1
		runSearch("")
	}

	function setSelectedIndex(index) {
		selectedIndex.value = index
	}

	function resetSelectedIndex() {
		selectedIndex.value = -1
	}

	function trackCustomerSelection(customer) {
		// Accept either a full customer object or a bare id (back-compat).
		const customerId = typeof customer === "string" ? customer : customer?.name
		if (!customerId) return

		// Add to recent searches (max 10)
		recentSearches.value = [
			customerId,
			...recentSearches.value.filter((id) => id !== customerId),
		].slice(0, 10)

		// Track frequency
		const index = frequentCustomers.value.indexOf(customerId)
		if (index > -1) {
			// Move to front if already exists
			frequentCustomers.value.splice(index, 1)
		}
		frequentCustomers.value = [customerId, ...frequentCustomers.value].slice(
			0,
			20,
		)

		// Keep full recent objects so the empty-search list can show them without
		// loading the entire customer table.
		if (typeof customer === "object" && customer?.name) {
			recentObjects.value = [
				{
					name: customer.name,
					customer_name: customer.customer_name,
					mobile_no: customer.mobile_no,
					email_id: customer.email_id,
				},
				...recentObjects.value.filter((c) => c.name !== customer.name),
			].slice(0, 10)
		}

		// Persist to localStorage
		try {
			localStorage.setItem(
				"pos_recent_customers",
				JSON.stringify(recentSearches.value),
			)
			localStorage.setItem(
				"pos_frequent_customers",
				JSON.stringify(frequentCustomers.value),
			)
			localStorage.setItem(
				RECENT_OBJECTS_KEY,
				JSON.stringify(recentObjects.value),
			)
		} catch (e) {
			log.warn("Failed to persist customer history:", e)
		}
	}

	function loadCustomerHistory() {
		try {
			const recent = localStorage.getItem("pos_recent_customers")
			const frequent = localStorage.getItem("pos_frequent_customers")
			const recentObjs = localStorage.getItem(RECENT_OBJECTS_KEY)

			if (recent) recentSearches.value = JSON.parse(recent)
			if (frequent) frequentCustomers.value = JSON.parse(frequent)
			if (recentObjs) recentObjects.value = JSON.parse(recentObjs)
		} catch (e) {
			log.warn("Failed to load customer history:", e)
		}
	}

	return {
		// State
		allCustomers,
		searchTerm,
		loading,
		searching,
		selectedIndex,
		recentSearches,
		frequentCustomers,

		// Getters
		filteredCustomers,
		recommendations,

		// Actions
		loadAllCustomers,
		addCustomerToCache,
		setSearchTerm,
		clearSearch,
		setSelectedIndex,
		resetSelectedIndex,
		trackCustomerSelection,
		loadCustomerHistory,
	}
})
