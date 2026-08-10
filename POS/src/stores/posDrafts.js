import { deleteDraft, getDraftsCount, saveDraft, getAllDrafts, updateDraft } from "@/utils/draftManager"
import { useToast } from "@/composables/useToast"
import { defineStore } from "pinia"
import { ref } from "vue"

export const usePOSDraftsStore = defineStore("posDrafts", () => {
	// Use custom toast
	const { showSuccess, showError, showWarning } = useToast()

	// State
	const draftsCount = ref(0)
	const drafts = ref([])

	// Actions
	async function updateDraftsCount() {
		try {
			draftsCount.value = await getDraftsCount()
		} catch (error) {
			console.error("Error getting drafts count:", error)
		}
	}

	async function loadDrafts() {
		try {
			drafts.value = await getAllDrafts()
			draftsCount.value = drafts.value.length
		} catch (error) {
			console.error("Error loading drafts:", error)
		}
	}

	async function saveDraftInvoice(
		invoiceItems,
		customer,
		posProfile,
		appliedOffers = [],
		draftId = null,
		context = {},
	) {
		if (invoiceItems.length === 0) {
			showWarning(__("Cannot save an empty cart as draft"))
			return null
		}

		try {
			const draftData = {
				pos_profile: posProfile,
				customer: customer,
				items: invoiceItems,
				applied_offers: appliedOffers, // Save applied offers
				// Preserve table/room + sale-type context so resuming a held order
				// (Customer / Employee Benefits/Cash/Loan) puts the cart back exactly
				// as it was, instead of resetting to a plain customer sale.
				// Room (hotel room-service) and Table (restaurant table) are kept as
				// two distinct fields - they identify different things.
				room: context.room || "",
				table: context.table || "",
				customer_type: context.customerType || "",
				sale_type: context.saleType || "customer",
				employee: context.employee || null,
			}

			let savedDraft
			if (draftId) {
				savedDraft = await updateDraft(draftId, draftData)
			} else {
				savedDraft = await saveDraft(draftData)
			}

			await loadDrafts() // Refresh drafts list and count

			showSuccess(__("Invoice saved as draft successfully"))

			return savedDraft
		} catch (error) {
			console.error("Error saving draft:", error)
			showError(__("Failed to save draft"))
			return null
		}
	}

	async function loadDraft(draft) {
		try {
			showSuccess(__("Draft invoice loaded successfully"))

			return {
				items: draft.items || [],
				customer: draft.customer,
				applied_offers: draft.applied_offers || [], // Restore applied offers
				room: draft.room || "",
				table: draft.table || "",
				customerType: draft.customer_type || "",
				saleType: draft.sale_type || "customer",
				employee: draft.employee || null,
			}
		} catch (error) {
			console.error("Error loading draft:", error)
			showError(__("Failed to load draft"))
			throw error
		}
	}

	/**
	 * Find an existing open draft already held for the given table, so a second
	 * "hold" for the same table resumes it instead of creating a duplicate.
	 * @param {string} tableValue
	 * @param {string|null} excludeDraftId - the draft currently being edited, if any
	 */
	function getOpenDraftForTable(tableValue, excludeDraftId = null) {
		if (!tableValue) return null
		return (
			drafts.value.find(
				(d) => d.table === tableValue && d.draft_id !== excludeDraftId,
			) || null
		)
	}

	async function deleteDraftById(draftId) {
		try {
			await deleteDraft(draftId)
			await loadDrafts() // Refresh drafts list and count
			showSuccess(__("Draft deleted successfully"))
		} catch (error) {
			console.error("Error deleting draft:", error)
			showError(__("Failed to delete draft"))
		}
	}

	return {
		// State
		draftsCount,
		drafts,

		// Actions
		updateDraftsCount,
		loadDrafts,
		saveDraftInvoice,
		loadDraft,
		getOpenDraftForTable,
		deleteDraft: deleteDraftById,
	}
})
