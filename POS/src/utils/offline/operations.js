/**
 * @fileoverview Generic offline write-operation queue.
 *
 * Non-invoice write operations (opening/closing a shift, marking attendance,
 * recording a daily payment, creating a customer, ...) are enqueued here while
 * offline and flushed to the server by {@link module:utils/offline/syncOps}
 * once connectivity returns.
 *
 * Mirrors the invoice queue in {@link module:utils/offline/sync} but is keyed on
 * a generic `op_id` (client UUID) + `type` so a single sync engine can process
 * every operation kind. Records live in the `operation_queue` IndexedDB store.
 *
 * @module utils/offline/operations
 */

import { logger } from "@/utils/logger"
import { db } from "./db"
import { generateOfflineId } from "./uuid"

const log = logger.create("OfflineOps")

/**
 * Enqueue an offline write operation for later sync.
 *
 * @param {string} type - Operation type; must have a handler registered in syncOps.js
 * @param {Object} data - Whitelisted-arg payload for the operation's endpoint
 * @returns {Promise<{success: boolean, id: number, op_id: string}>}
 */
export const enqueueOperation = async (type, data) => {
	if (!type) throw new Error("enqueueOperation requires a type")

	// Strip reactive proxies so IndexedDB can structured-clone the payload
	const cleanData = JSON.parse(JSON.stringify(data ?? {}))
	const opId = generateOfflineId()

	const id = await db.operation_queue.add({
		op_id: opId,
		type,
		data: cleanData,
		timestamp: Date.now(),
		synced: false,
		retry_count: 0,
	})

	log.info("Operation queued", { type, op_id: opId })
	return { success: true, id, op_id: opId }
}

/**
 * Get pending (unsynced) operations, optionally filtered by type.
 * Ordered oldest-first so dependent ops (e.g. customer before invoice) flush in order.
 *
 * @param {string|null} [type=null] - Restrict to a single operation type
 * @returns {Promise<Array>}
 */
export const getPendingOperations = async (type = null) => {
	try {
		const pending = await db.operation_queue
			.filter((op) => !op.synced)
			.toArray()
		const filtered = type ? pending.filter((op) => op.type === type) : pending
		return filtered.sort((a, b) => a.timestamp - b.timestamp)
	} catch (error) {
		log.error("Failed to get pending operations", error)
		return []
	}
}

/**
 * Count pending (unsynced) operations, optionally filtered by type.
 * @param {string|null} [type=null]
 * @returns {Promise<number>}
 */
export const getPendingOperationCount = async (type = null) => {
	try {
		if (type) {
			return await db.operation_queue
				.filter((op) => !op.synced && op.type === type)
				.count()
		}
		return await db.operation_queue.filter((op) => !op.synced).count()
	} catch (error) {
		log.error("Failed to count pending operations", error)
		return 0
	}
}

/**
 * Mark an operation as synced.
 * @param {number} id - operation_queue row id
 * @param {string} [serverName] - Reference document name created on the server
 */
export const markOperationSynced = async (id, serverName) => {
	await db.operation_queue.update(id, {
		synced: true,
		synced_at: Date.now(),
		server_name: serverName || "",
	})
}

/**
 * Record a failed sync attempt. Flags the op as `sync_failed` after 3 tries so
 * the UI can surface it for manual retry instead of looping forever.
 * @param {number} id - operation_queue row id
 * @param {string} message - Error message
 */
export const handleOperationFailure = async (id, message) => {
	const op = await db.operation_queue.get(id)
	const retry = (op?.retry_count || 0) + 1
	const updates = { retry_count: retry, last_error: message }
	if (retry >= 3) updates.sync_failed = true
	await db.operation_queue.update(id, updates)
}

/**
 * Delete an operation from the queue by id.
 * @param {number} id
 * @returns {Promise<boolean>}
 */
export const deleteOperation = async (id) => {
	try {
		await db.operation_queue.delete(id)
		return true
	} catch (error) {
		log.error("Failed to delete operation", { id, error })
		return false
	}
}

/**
 * Clear the `sync_failed` flag and reset retries so an op can be retried.
 * @param {number} id
 */
export const resetOperationFailure = async (id) => {
	await db.operation_queue.update(id, {
		sync_failed: false,
		retry_count: 0,
		last_error: "",
	})
}
