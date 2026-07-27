import {
	getPendingOperationCount,
	syncOfflineInvoices,
	syncOfflineOperations,
} from "@/utils/offline"
import { offlineState } from "@/utils/offline/offlineState"
import { offlineWorker } from "@/utils/offline/workerClient"
import { computed, onMounted, onUnmounted, ref, watch } from "vue"

export function useOffline() {
	// Reactive state that syncs with centralized offlineState
	const isOffline = ref(offlineState.isOffline)
	const pendingInvoicesCount = ref(0)
	const pendingOperationsCount = ref(0)
	const isSyncing = ref(false)
	const connectionQuality = ref(offlineState.getConnectionQuality())

	// Track previous offline state for transition detection
	let wasOffline = offlineState.isOffline
	let unsubscribe = null

	// Update offline status from centralized state
	const updateOfflineStatus = () => {
		isOffline.value = offlineState.isOffline
		connectionQuality.value = offlineState.getConnectionQuality()
	}

	// Update pending invoices count using worker
	const updatePendingCount = async () => {
		try {
			pendingInvoicesCount.value = await offlineWorker.getOfflineInvoiceCount()
		} catch (error) {
			console.error("[useOffline] Error getting pending count:", error)
		}
	}

	// Update pending (non-invoice) operations count
	const updatePendingOpCount = async () => {
		try {
			pendingOperationsCount.value = await getPendingOperationCount()
		} catch (error) {
			console.error("[useOffline] Error getting pending op count:", error)
		}
	}

	// Sync queued non-invoice operations (shift/attendance/daily-payment/customer)
	const syncPendingOperations = async () => {
		if (isOffline.value) {
			throw new Error("Cannot sync while offline")
		}
		try {
			const result = await syncOfflineOperations()
			await updatePendingOpCount()
			return result
		} catch (error) {
			console.error("[useOffline] Error syncing operations:", error)
			throw error
		}
	}

	// Save invoice offline using worker
	const saveInvoiceOffline = async (invoiceData) => {
		try {
			await offlineWorker.saveOfflineInvoice(invoiceData)
			await updatePendingCount()
			return true
		} catch (error) {
			console.error("[useOffline] Error saving invoice offline:", error)
			throw error
		}
	}

	// Sync pending invoices
	const syncPending = async () => {
		if (isOffline.value) {
			throw new Error("Cannot sync while offline")
		}

		isSyncing.value = true
		try {
			const result = await syncOfflineInvoices()
			await updatePendingCount()
			return result
		} catch (error) {
			console.error("[useOffline] Error syncing invoices:", error)
			throw error
		} finally {
			isSyncing.value = false
		}
	}

	// Get pending invoices using worker
	const getPending = async () => {
		return await offlineWorker.getOfflineInvoices()
	}

	// Delete pending invoice using worker
	const deletePending = async (id) => {
		await offlineWorker.deleteOfflineInvoice(id)
		await updatePendingCount()
	}

	// Cache data using worker
	const cacheData = async (items, customers) => {
		try {
			if (items && items.length > 0) {
				await offlineWorker.cacheItems(items)
			}
			if (customers && customers.length > 0) {
				await offlineWorker.cacheCustomers(customers)
			}
			return true
		} catch (error) {
			console.error("[useOffline] Error caching data:", error)
			return false
		}
	}

	// Search cached items using worker
	const searchItems = async (searchTerm, limit = 50) => {
		return await offlineWorker.searchCachedItems(searchTerm, limit)
	}

	// Search cached customers using worker
	const searchCustomers = async (searchTerm, limit = 20) => {
		return await offlineWorker.searchCachedCustomers(searchTerm, limit)
	}

	// Check if cache is ready using worker
	const checkCacheReady = async () => {
		return await offlineWorker.isCacheReady()
	}

	// Get cache stats using worker
	const getCacheStats = async () => {
		return await offlineWorker.getCacheStats()
	}

	// Handle state changes from centralized manager
	const handleStateChange = async (state) => {
		const nowOffline = state.isOffline

		// Update reactive refs
		isOffline.value = nowOffline
		connectionQuality.value = state.quality || offlineState.getConnectionQuality()

		// Detect transition from offline to online
		if (wasOffline && !nowOffline) {
			console.log("[useOffline] Transition to online detected, syncing...")
			isSyncing.value = true
			try {
				// Operations first: shifts/customers must exist server-side before
				// invoices that reference them are pushed.
				await syncPendingOperations()
			} catch (error) {
				console.error("[useOffline] Auto-sync (operations) failed:", error)
			}
			try {
				await syncPending()
			} catch (error) {
				console.error("[useOffline] Auto-sync (invoices) failed:", error)
			} finally {
				isSyncing.value = false
			}
		}

		wasOffline = nowOffline
	}

	// Force immediate connectivity check
	const checkConnectivity = async () => {
		const state = await offlineState.checkConnectivity()
		isOffline.value = state.isOffline
		connectionQuality.value = state.quality
		return state
	}

	// Handle invoice sync completion
	const handleInvoicesSynced = () => {
		console.log("[useOffline] Invoices synced event received, updating count...")
		updatePendingCount()
	}

	onMounted(() => {
		// Initial state sync
		updateOfflineStatus()
		updatePendingCount()
		updatePendingOpCount()

		// Subscribe to centralized state changes
		unsubscribe = offlineState.subscribe(handleStateChange)

		// Listen for sync completion events
		window.addEventListener("offlineInvoicesSynced", handleInvoicesSynced, {
			passive: true,
		})
	})

	onUnmounted(() => {
		// Cleanup subscription
		if (unsubscribe) {
			unsubscribe()
			unsubscribe = null
		}

		window.removeEventListener("offlineInvoicesSynced", handleInvoicesSynced)
	})

	return {
		isOffline,
		pendingInvoicesCount,
		pendingOperationsCount,
		isSyncing,
		connectionQuality,
		saveInvoiceOffline,
		syncPending,
		syncPendingOperations,
		getPending,
		deletePending,
		cacheData,
		searchItems,
		searchCustomers,
		checkCacheReady,
		getCacheStats,
		checkConnectivity,
		updateOfflineStatus,
		updatePendingCount,
		updatePendingOpCount,
	}
}
