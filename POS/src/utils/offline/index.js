// Main offline module - exports all offline functionality

export { db, initDB, checkDBHealth, getSetting, setSetting } from "./db"

// Centralized offline state manager (single source of truth)
export {
	offlineState,
	isOffline,
	setManualOffline,
	toggleManualOffline,
	getOfflineState,
	checkConnectivity,
	getConnectionQuality,
} from "./offlineState"

export {
	pingServer,
	saveOfflineInvoice,
	getOfflineInvoices,
	getOfflineInvoiceCount,
	syncOfflineInvoices,
	deleteOfflineInvoice,
	updateLocalStock,
	getLocalStock,
	saveOfflinePayment,
	cacheInvoiceHistory,
	getCachedInvoiceHistory,
	clearInvoiceHistoryCache,
	cacheUnpaidInvoices,
	getCachedUnpaidInvoices,
	cacheUnpaidSummary,
	getCachedUnpaidSummary,
} from "./sync"

export {
	cacheItems,
	getCachedItems,
	searchCachedItems as searchCachedItemsOld,
	getItemByBarcode,
	getItemWithPrice,
	cacheCustomers,
	searchCachedCustomers as searchCachedCustomersOld,
	getItemsLastSync,
	getCustomersLastSync,
	isCacheFresh,
	clearItemsCache,
	clearCustomersCache,
} from "./items"

// Generic offline operation queue + sync engine
export {
	enqueueOperation,
	getPendingOperations,
	getPendingOperationCount,
	markOperationSynced,
	handleOperationFailure,
	deleteOperation,
	resetOperationFailure,
} from "./operations"

export {
	registerOpHandler,
	getRegisteredOpTypes,
	syncOfflineOperations,
} from "./syncOps"

// New cache system exports (excluding setManualOffline/toggleManualOffline - use offlineState instead)
export {
	memory,
	initMemoryCache,
	isCacheReady,
	isStockCacheReady,
	isManualOffline,
	cacheItemsFromServer,
	cacheCustomersFromServer,
	cachePaymentMethodsFromServer,
	getCachedPaymentMethods,
	searchCachedItems,
	searchCachedCustomers,
	getCachedItem,
	getCachedCustomer,
	needsCacheRefresh,
	clearAllCache,
	getCacheStats,
} from "./cache"
