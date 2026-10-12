import { call } from "@/utils/apiWrapper"
import { isOffline } from "@/utils/offline"
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

	// Sync state
	let serverDataFresh = false

	// ---------------------------------------------------------------------------
	// Server-side search
	//
	// Searching used to scan every customer held in memory, which meant the whole
	// customer list had to be downloaded first. The server now does the matching
	// and returns a small page; the local ranking below still orders that page, so
	// results keep their quality without the list ever being loaded in full.
	// ---------------------------------------------------------------------------
	const SEARCH_DEBOUNCE_MS = 250
	const SEARCH_LIMIT = 50
	// The list shown before anything is typed - recent and frequent names come
	// first, so this only needs to be long enough to be useful, not complete.
	const INITIAL_LIMIT = 50

	// Remembered from loadAllCustomers so a search can scope itself to the same
	// customer groups the profile allows.
	const currentPosProfile = ref(null)
	const serverResults = ref([])
	const searching = ref(false)
	let searchTimer = null
	let searchSeq = 0

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

	// Getters - ULTRA OPTIMIZED for zero delay
	const filteredCustomers = computed(() => {
		const term = searchTerm.value.trim()

		// Show recent/frequent customers when no search term (CACHED)
		if (!term) {
			const cacheKey = "empty"
			let cached = resultCache.value.get(cacheKey)

			if (!cached) {
				// Build index maps once for O(1) lookup
				const recentSet = new Set(recentSearches.value)
				const frequentSet = new Set(frequentCustomers.value)

				// Separate into buckets
				const recent = []
				const frequent = []
				const other = []

				for (const c of allCustomers.value) {
					if (recentSet.has(c.name)) recent.push(c)
					else if (frequentSet.has(c.name)) frequent.push(c)
					else other.push(c)
				}

				cached = [...recent, ...frequent, ...other].slice(0, 50)
				resultCache.value.set(cacheKey, cached)
			}

			return cached
		}

		// The server already narrowed the list; rank that small page locally so the
		// ordering stays as good as it was, without ever scanning every customer.
		// Falls back to whatever is in memory when a search has not returned yet.
		const pool = serverResults.value.length > 0 ? serverResults.value : allCustomers.value

		// Ranking a server page is cheap, and caching it would go stale as soon as
		// the same term returns different rows, so only the no-term list is cached.
		const results = []
		const maxResults = 50

		// First pass: Get exact and high-scoring matches ONLY
		for (const cust of pool) {
			scanned++
			const score = quickMatch(term, cust)

			if (score >= 240) {
				// High priority matches
				results.push({ customer: cust, score })
				if (results.length >= maxResults) break // Exit immediately when we have enough
			}
		}

		// Second pass: Fill remaining slots with lower scores if needed
		if (results.length < maxResults) {
			const highResultNames = new Set(results.map((r) => r.customer.name))
			for (let i = 0; i < pool.length; i++) {
				const cust = pool[i]
				if (highResultNames.has(cust.name)) continue
				const score = quickMatch(term, cust)

				if (score > 0 && score < 240) {
					results.push({ customer: cust, score })
					if (results.length >= maxResults) break
				}
			}
		}

		// Sort ONLY what we found (much faster than sorting everything)
		results.sort((a, b) => b.score - a.score)
		return results.map((r) => r.customer)
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
				text: __('Search by phone: {0}', [term]),
				icon: "📱",
			})
		}

		// Check if it looks like an email
		if (term.includes("@")) {
			recs.push({
				type: "email",
				text: __('Search by email: {0}', [term]),
				icon: "✉️",
			})
		}

		// Suggest creating new customer if no exact matches
		const exactMatch = allCustomers.value.some(
			(c) => c.customer_name?.toLowerCase() === term,
		)
		if (!exactMatch && filteredCustomers.value.length < 5) {
			recs.push({
				type: "create",
				text: __('Create new customer: {0}', [term]),
				icon: "➕",
			})
		}

		return recs
	})

	// Actions
	/**
	 * Load the short list shown before the cashier types anything.
	 *
	 * Customers are no longer mirrored into IndexedDB. The whole list used to be
	 * downloaded and cached so it could be searched in the browser; searching now
	 * happens on the server, which makes the copy pure cost - a slow first load,
	 * and a second source of truth that goes stale the moment anyone edits a
	 * customer elsewhere.
	 *
	 * The trade is deliberate: with no local copy there is no customer list while
	 * offline.
	 */
	async function loadAllCustomers(posProfile, forceReload = false) {
		if (!posProfile) {
			return
		}

		currentPosProfile.value = posProfile

		if (!forceReload && serverDataFresh && allCustomers.value.length > 0) {
			return
		}

		if (isOffline()) {
			// Nothing to fall back to - say so rather than showing a stale list
			log.warn("Offline: the customer list is server-side only")
			allCustomers.value = []
			return
		}

		loading.value = true
		try {
			const response = await call("ecs_posnext.api.customers.get_customers", {
				pos_profile: posProfile,
				search_term: "",
				start: 0,
				limit: INITIAL_LIMIT,
			})
			const rows = response?.message || response || []

			allCustomers.value = rows.filter((c) => !c.disabled)
			serverDataFresh = true

			searchIndex.value.clear()
			resultCache.value.clear()
		} catch (error) {
			log.error("Error loading customers:", error)
			allCustomers.value = []
		} finally {
			loading.value = false
		}
	}

	/**
	 * Put a customer at the top of the in-memory list.
	 *
	 * In memory only - a just-created customer needs to be pickable straight away
	 * without waiting for a round trip, but the server stays the source of truth.
	 */
	function addCustomerToCache(customer) {
		allCustomers.value = [
			customer,
			...allCustomers.value.filter((cust) => cust.name !== customer.name),
		]

		// Clear BOTH caches so the new customer shows up in search
		searchIndex.value.clear()
		resultCache.value.clear()
	}

	// Real-time Push Integration
	const { onCustomerUpdate } = useRealtimeCustomers()
	onCustomerUpdate(async (data) => {
		const { name, action, customer_name, mobile_no, email_id, disabled } = data
		console.log("Customer update via real-time:", data)
		if (action === "delete" || disabled) {
			// Memory only - there is no local copy to keep in step any more
			allCustomers.value = allCustomers.value.filter((c) => c.name !== name)
			serverResults.value = serverResults.value.filter((c) => c.name !== name)

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
			addCustomerToCache(customer)
		}
	})

	function setSearchTerm(term) {
		searchTerm.value = term
		selectedIndex.value = -1

		clearTimeout(searchTimer)

		const trimmed = (term || "").trim()
		if (!trimmed) {
			serverResults.value = []
			searching.value = false
			return
		}

		searching.value = true
		searchTimer = setTimeout(() => runSearch(trimmed), SEARCH_DEBOUNCE_MS)
	}

	async function runSearch(term) {
		// Out-of-order responses would otherwise overwrite a newer search with an
		// older one's results.
		const seq = ++searchSeq

		try {
			const response = await call("ecs_posnext.api.customers.get_customers", {
				pos_profile: currentPosProfile.value || null,
				search_term: term,
				start: 0,
				limit: SEARCH_LIMIT,
			})
			const rows = response?.message || response || []

			if (seq !== searchSeq) return
			serverResults.value = (rows || []).filter((c) => !c.disabled)
		} catch (error) {
			log.error("Customer search failed", error)
			if (seq !== searchSeq) return
			// Fall back to whatever is already in memory rather than showing nothing
			serverResults.value = allCustomers.value
		} finally {
			if (seq === searchSeq) searching.value = false
		}
	}

	function clearSearch() {
		searchTerm.value = ""
		selectedIndex.value = -1
		serverResults.value = []
		searching.value = false
		clearTimeout(searchTimer)
		// Don't clear resultCache on empty search - it's beneficial
	}

	function setSelectedIndex(index) {
		selectedIndex.value = index
	}

	function resetSelectedIndex() {
		selectedIndex.value = -1
	}

	function trackCustomerSelection(customerId) {
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
		} catch (e) {
			log.warn("Failed to persist customer history:", e)
		}
	}

	function loadCustomerHistory() {
		try {
			const recent = localStorage.getItem("pos_recent_customers")
			const frequent = localStorage.getItem("pos_frequent_customers")

			if (recent) recentSearches.value = JSON.parse(recent)
			if (frequent) frequentCustomers.value = JSON.parse(frequent)
		} catch (e) {
			log.warn("Failed to load customer history:", e)
		}
	}

	return {
		// State
		allCustomers,
		searchTerm,
		loading,
		selectedIndex,
		recentSearches,
		frequentCustomers,

		// Getters
		filteredCustomers,
		searching,
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
