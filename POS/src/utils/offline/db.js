import Dexie from "dexie"
import { logger } from "../logger"

/** @type {import('../logger').Logger} */
const log = logger.create("OfflineDB")

/**
 * @fileoverview IndexedDB persistence layer for POS Next offline functionality.
 *
 * This module provides:
 * - Auto-versioned Dexie database with schema migration
 * - Offline caching for items, customers, stock, prices
 * - Queue management for offline invoices and payments
 * - Settings persistence and translation cache
 *
 * Schema changes are auto-detected via hash comparison and trigger version bumps.
 *
 * @module db
 * @see {@link https://dexie.org/} Dexie.js documentation
 */

/** @type {Dexie} Main database instance */
export const db = new Dexie("ecs_posnext_offline")

/**
 * Database schema definition.
 * Modify this object to change the schema - version will auto-increment.
 *
 * Index notation:
 * - `&` = unique primary key
 * - `++` = auto-increment primary key
 * - `*` = multi-entry index (array field)
 * - `[a+b]` = compound index
 *
 * @constant {Object}
 */
const CURRENT_SCHEMA = {
	// Key-value store for settings and metadata
	settings: "&key",

	// Invoice queue for offline submissions
	// offline_id is a unique UUID for deduplication across syncs
	invoice_queue: "++id, &offline_id, timestamp, synced",

	// Generic queue for non-invoice offline write operations
	// (open_shift, close_shift, attendance, daily_payment, customer, ...)
	// op_id is a unique UUID for server-side deduplication; type routes it to
	// the matching sync handler registered in syncOps.js
	operation_queue: "++id, &op_id, type, timestamp, synced",

	// Items cache with searchable fields
	// variant_of index allows querying variants by their template item
	items: "&item_code, item_name, item_group, variant_of, *barcodes",

	// Customers cache
	customers: "&name, customer_name, mobile_no, email_id",

	// Price list cache
	item_prices: "&[price_list+item_code], price_list, item_code",

	// Local stock cache
	stock: "&[item_code+warehouse], item_code, warehouse",

	// Payment methods cache
	payment_methods: "&mode_of_payment, pos_profile",

	// Drafts (already handled by draftManager, but keeping for consistency)
	drafts: "++id, draft_id, timestamp",

	// Translations cache for offline language support
	translations: "&locale, timestamp",

	// Promotional offers cache for offline use
	// Indexed by name (unique), filterable by pos_profile
	offers: "&name, pos_profile, apply_on, valid_upto",

	// Invoice history cache for offline viewing
	// Stores submitted invoices for offline access
	invoice_history: "&name, pos_profile, posting_date, customer",

	// Unpaid invoices cache for offline viewing
	// Stores invoices with outstanding amounts for partial payment management
	unpaid_invoices: "&name, pos_profile, outstanding_amount, customer",
}

/**
 * Fixed schema version (manual-bump convention).
 *
 * Previously the version was derived from a hash of CURRENT_SCHEMA stored in
 * localStorage and auto-incremented. That was fragile: if localStorage was
 * cleared while the IndexedDB still existed, the version reset to 1 and Dexie
 * threw VersionError, which the recovery path handled by NUKING the database —
 * silently destroying the unsynced invoice/operation queues.
 *
 * A fixed constant removes that data-loss trigger entirely (the standard Dexie
 * pattern). The base is deliberately large so it sits safely above any version
 * a legacy client could have reached under the old auto-increment scheme;
 * Dexie upgrades such clients to this version, preserving their data.
 *
 * When you change CURRENT_SCHEMA, bump this number by 1.
 * @constant {number}
 */
const DB_VERSION = 1001

log.debug(`Initializing database with schema version: ${DB_VERSION}`)
db.version(DB_VERSION).stores(CURRENT_SCHEMA)

/**
 * Opens the database connection.
 * Called automatically on module import.
 * @returns {Promise<boolean>} True if opened successfully
 */
export const initDB = async () => {
	try {
		await db.open()
		log.success("POS Next offline database initialized")
		return true
	} catch (error) {
		log.error("Failed to initialize offline database:", error)
		return false
	}
}

/**
 * Verifies database health and attempts recovery if needed.
 * Handles VersionError and InvalidStateError by recreating the database.
 * @returns {Promise<boolean>} True if database is healthy or recovered
 */
export const checkDBHealth = async () => {
	try {
		await db.settings.get("health_check")
		return true
	} catch (error) {
		log.error("Database health check failed:", error)

		// Try to reopen
		try {
			if (db.isOpen()) {
				db.close()
			}
			await db.open()
			log.info("Database reopened successfully")
			return true
		} catch (reopenError) {
			log.error("Failed to reopen database:", reopenError)

			// If corrupted, recreate
			if (
				reopenError.name === "VersionError" ||
				reopenError.name === "InvalidStateError"
			) {
				log.warn("Database appears corrupted, recreating...")
				try {
					await Dexie.delete("ecs_posnext_offline")
					await db.open()
					log.success("Database recreated successfully")
					return true
				} catch (recreateError) {
					log.error("Failed to recreate database:", recreateError)
					return false
				}
			}
			return false
		}
	}
}

/**
 * Retrieves a setting value from the database.
 * @param {string} key - Setting key to retrieve
 * @param {*} [defaultValue=null] - Value to return if key not found
 * @returns {Promise<*>} Stored value or defaultValue
 */
export const getSetting = async (key, defaultValue = null) => {
	try {
		const result = await db.settings.get(key)
		return result ? result.value : defaultValue
	} catch (error) {
		log.error(`Error getting setting ${key}:`, error)
		return defaultValue
	}
}

/**
 * Stores a setting value in the database.
 * @param {string} key - Setting key
 * @param {*} value - Value to store (must be IndexedDB-serializable)
 * @returns {Promise<void>}
 */
export const setSetting = async (key, value) => {
	try {
		await db.settings.put({ key, value })
	} catch (error) {
		log.error(`Error setting ${key}:`, error)
	}
}

/**
 * Clear all cached data (items, customers, stock, etc.)
 * Preserves critical data like invoices, drafts, and settings
 * @param {Object} options - Options for clearing
 * @param {boolean} options.preserveInvoices - Keep invoice queue (default: true)
 * @param {boolean} options.preserveDrafts - Keep drafts (default: true)
 * @param {boolean} options.preserveSettings - Keep settings (default: true)
 * @returns {Promise<Object>} - Status of cleared tables
 */
export const clearCachedData = async (options = {}) => {
	const {
		preserveInvoices = true,
		preserveDrafts = true,
		preserveSettings = true,
	} = options

	const results = {
		items: 0,
		customers: 0,
		stock: 0,
		item_prices: 0,
		payment_methods: 0,
		invoices: 0,
		operations: 0,
		drafts: 0,
		settings: 0,
	}

	try {
		// Always clear these cache tables
		results.items = await db.items.clear()
		results.customers = await db.customers.clear()
		results.stock = await db.stock.clear()
		results.item_prices = await db.item_prices.clear()
		results.payment_methods = await db.payment_methods.clear()

		// Conditionally clear invoice and operation queues
		if (!preserveInvoices) {
			results.invoices = await db.invoice_queue.clear()
			results.operations = await db.operation_queue.clear()
		}

		// Conditionally clear drafts
		if (!preserveDrafts) {
			results.drafts = await db.drafts.clear()
		}

		// Conditionally clear settings
		if (!preserveSettings) {
			results.settings = await db.settings.clear()
		}

		log.info("Cached data cleared:", results)
		return { success: true, cleared: results }
	} catch (error) {
		log.error("Error clearing cached data:", error)
		return { success: false, error: error.message, cleared: results }
	}
}

/**
 * NUCLEAR OPTION: Delete entire database and recreate
 * Use with caution - clears EVERYTHING including invoices and drafts
 * @returns {Promise<boolean>} - Success status
 */
export const nukeDatabase = async () => {
	try {
		log.warn("NUKING DATABASE - All data will be lost!")

		// Close database connection
		if (db.isOpen()) {
			db.close()
		}

		// Delete entire database
		await Dexie.delete("ecs_posnext_offline")

		// Recreate database
		await db.open()

		log.success("Database nuked and recreated successfully")
		return true
	} catch (error) {
		log.error("Error nuking database:", error)
		return false
	}
}

/**
 * Clear browser cache and localStorage (POS-specific data only)
 * @returns {Object} - Status of cleared data
 */
export const clearBrowserCache = () => {
	const results = {
		localStorage: 0,
		sessionStorage: 0,
	}

	try {
		// Clear POS-specific localStorage items
		const keysToRemove = []
		for (let i = 0; i < localStorage.length; i++) {
			const key = localStorage.key(i)
			if (key?.startsWith("ecs_posnext_") || key?.startsWith("frappe_")) {
				keysToRemove.push(key)
			}
		}

		keysToRemove.forEach((key) => {
			localStorage.removeItem(key)
			results.localStorage++
		})

		// Clear sessionStorage
		const sessionKeys = []
		for (let i = 0; i < sessionStorage.length; i++) {
			const key = sessionStorage.key(i)
			if (key?.startsWith("ecs_posnext_") || key?.startsWith("frappe_")) {
				sessionKeys.push(key)
			}
		}

		sessionKeys.forEach((key) => {
			sessionStorage.removeItem(key)
			results.sessionStorage++
		})

		log.info("Browser cache cleared:", results)
		return { success: true, cleared: results }
	} catch (error) {
		log.error("Error clearing browser cache:", error)
		return { success: false, error: error.message, cleared: results }
	}
}

// Initialize database on import
initDB()
