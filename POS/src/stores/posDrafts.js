import { getDraftsCount, saveDraft, getAllDrafts, updateDraft, getDraftById } from "@/utils/draftManager"
import { useToast } from "@/composables/useToast"
import { defineStore } from "pinia"
import { ref } from "vue"

// Internal-only delete (not exported, used only after successful invoice submission)
const _DB_NAME = "ecs_posnext_drafts"
const _STORE_NAME = "invoices"

async function _internalDeleteDraft(draftId) {
	const draft = await getDraftById(draftId)
	if (!draft) return

	return new Promise((resolve, reject) => {
		const request = indexedDB.open(_DB_NAME, 1)
		request.onsuccess = () => {
			const db = request.result
			const tx = db.transaction([_STORE_NAME], "readwrite")
			const store = tx.objectStore(_STORE_NAME)
			const delReq = store.delete(draft.id)
			delReq.onsuccess = () => resolve(true)
			delReq.onerror = () => reject(delReq.error)
		}
		request.onerror = () => reject(request.error)
	})
}

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
		orderType = "",
		tableNumbers = [],
		serverDraftName = null,
		invoiceNote = "",
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
				order_type: orderType || "", // Save order type (custom_so_type)
				table_numbers: Array.isArray(tableNumbers) ? tableNumbers : [], // Save multiple tables
				// Backward compat: keep table_number as first selected table
				table_number: Array.isArray(tableNumbers) && tableNumbers.length > 0 ? tableNumbers[0] : "",
				server_draft_name: serverDraftName || null, // Server-side draft link (for Dinin)
				invoice_note: invoiceNote || "", // Invoice-level note (posa_notes)
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
				order_type: draft.order_type || "", // Restore order type
				// Multi-table: prefer table_numbers array, fall back to single table_number for old drafts
				table_numbers: draft.table_numbers || (draft.table_number ? [draft.table_number] : []),
				server_draft_name: draft.server_draft_name || null, // Restore server draft link
				invoice_note: draft.invoice_note || "", // Restore invoice-level note
			}
		} catch (error) {
			console.error("Error loading draft:", error)
			showError(__("Failed to load draft"))
			throw error
		}
	}

	// Internal: delete draft after successful invoice submission only
	async function deleteDraft(draftId) {
		try {
			await _internalDeleteDraft(draftId)
			await loadDrafts()
		} catch (error) {
			console.error("Error cleaning up draft after submission:", error)
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
		deleteDraft,
	}
})
