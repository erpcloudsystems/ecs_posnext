/**
 * POS Sales Person Store
 *
 * Drives the "Multiple Sales Persons" mode of the sale screen, where the cashier
 * selects one or more sales persons and assigns specific items to each of them.
 *
 * - `enabled`           : the "Multiple Sales Persons" checkbox state
 * - `selected`          : sales persons participating in this invoice
 * - `activeSalesPerson` : the sales person that newly added items are assigned to
 *
 * Allocation (per-invoice commission split) is DERIVED from the per-item
 * assignment: each sales person's allocated_percentage is the share of the
 * cart's net total that their assigned items represent.
 *
 * IMPORTANT: this store must NOT import the cart store (posCart imports this one).
 * Allocation helpers therefore take the cart items as an argument.
 */

import { defineStore } from "pinia"
import { computed, ref } from "vue"
import { createResource } from "frappe-ui"
import { roundCurrency } from "@/utils/currency"
import { logger } from "@/utils/logger"

const log = logger.create("posSalesPerson")

export const usePOSSalesPersonStore = defineStore("posSalesPerson", () => {
	// State
	const enabled = ref(false) // "Multiple Sales Persons" checkbox
	const salesPersons = ref([]) // master list loaded from server
	const selected = ref([]) // [{ sales_person, sales_person_name, commission_rate }]
	const activeSalesPerson = ref(null) // sales_person id currently receiving items
	const loading = ref(false)
	const posProfile = ref(null)

	// Resource: reuse the existing backend endpoint
	const salesPersonsResource = createResource({
		url: "ecs_posnext.api.pos_profile.get_sales_persons",
		makeParams() {
			return { pos_profile: posProfile.value }
		},
		auto: false,
		onSuccess(data) {
			salesPersons.value = data?.message || data || []
			loading.value = false
		},
		onError(error) {
			log.error("Error loading sales persons:", error)
			salesPersons.value = []
			loading.value = false
		},
	})

	// Computed
	const selectedIds = computed(() => selected.value.map((p) => p.sales_person))

	const availableSalesPersons = computed(() => {
		const ids = selectedIds.value
		return salesPersons.value.filter((p) => !ids.includes(p.name))
	})

	const hasSelection = computed(() => selected.value.length > 0)

	// Actions
	function loadSalesPersons(profileName = null) {
		if (profileName) posProfile.value = profileName
		if (!posProfile.value) return
		if (salesPersons.value.length === 0 && !loading.value) {
			loading.value = true
			salesPersonsResource.fetch()
		}
	}

	function setEnabled(value) {
		enabled.value = !!value
		if (enabled.value) {
			if (!activeSalesPerson.value && selected.value.length) {
				activeSalesPerson.value = selected.value[0].sales_person
			}
		} else {
			// Leaving the mode: stop routing new items to anyone
			activeSalesPerson.value = null
		}
	}

	function addSalesPerson(person) {
		if (!person) return
		const id = person.name || person.sales_person
		if (!id) return
		if (selected.value.some((p) => p.sales_person === id)) {
			activeSalesPerson.value = id
			return
		}
		selected.value.push({
			sales_person: id,
			sales_person_name: person.sales_person_name || person.name || id,
			commission_rate: person.commission_rate || 0,
		})
		// First added becomes active automatically
		if (!activeSalesPerson.value) activeSalesPerson.value = id
	}

	function removeSalesPerson(id) {
		selected.value = selected.value.filter((p) => p.sales_person !== id)
		if (activeSalesPerson.value === id) {
			activeSalesPerson.value = selected.value.length
				? selected.value[0].sales_person
				: null
		}
	}

	function setActive(id) {
		activeSalesPerson.value = id
	}

	function getActive() {
		return (
			selected.value.find((p) => p.sales_person === activeSalesPerson.value) ||
			null
		)
	}

	function nameFor(id) {
		const found = selected.value.find((p) => p.sales_person === id)
		return found ? found.sales_person_name || found.sales_person : id
	}

	function reset() {
		enabled.value = false
		selected.value = []
		activeSalesPerson.value = null
	}

	/**
	 * Derive the commission split from per-item assignment.
	 * @param {Array} items - cart items (each may carry sales_person + amount)
	 * @returns {Array} [{ sales_person, sales_person_name, amount, allocated_percentage }]
	 */
	function computeAllocations(items = []) {
		const totals = {}
		let grand = 0
		for (const item of items) {
			const amt = item.amount || 0
			grand += amt
			const sp = item.sales_person || null
			if (sp) totals[sp] = (totals[sp] || 0) + amt
		}
		return selected.value.map((p) => {
			const amount = roundCurrency(totals[p.sales_person] || 0)
			return {
				sales_person: p.sales_person,
				sales_person_name: p.sales_person_name,
				amount,
				allocated_percentage:
					grand > 0 ? roundCurrency((amount / grand) * 100) : 0,
			}
		})
	}

	/**
	 * True when every cart item has been assigned to a sales person.
	 * Used to block checkout while items remain unassigned.
	 */
	function allItemsAssigned(items = []) {
		return items.every((item) => !!item.sales_person)
	}

	return {
		// State
		enabled,
		salesPersons,
		selected,
		activeSalesPerson,
		loading,
		posProfile,

		// Computed
		availableSalesPersons,
		hasSelection,

		// Actions
		loadSalesPersons,
		setEnabled,
		addSalesPerson,
		removeSalesPerson,
		setActive,
		getActive,
		nameFor,
		reset,
		computeAllocations,
		allItemsAssigned,
	}
})
