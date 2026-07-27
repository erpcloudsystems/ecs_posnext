/**
 * @fileoverview Generic sync engine for the offline operation queue.
 *
 * Flushes queued non-invoice write operations to the server once online.
 * Each operation `type` registers a handler describing which whitelisted
 * endpoint to call and how to map the queued payload onto its arguments.
 * Server-side idempotency is provided by the Offline Operation Sync doctype:
 * every call carries the client `op_id`, so re-syncing a previously-synced op
 * is a no-op on the server.
 *
 * Structurally mirrors the invoice sync in {@link module:utils/offline/sync}
 * (mutex-guarded, pre-sync dedup check, in-progress retry, failure counting).
 *
 * @module utils/offline/syncOps
 */

import { call } from "@/utils/apiWrapper"
import { logger } from "@/utils/logger"
import { CoalescingMutex } from "@/utils/mutex"
import {
	getPendingOperations,
	handleOperationFailure,
	markOperationSynced,
} from "./operations"
import { isOffline } from "./sync"

const log = logger.create("SyncOps")

// Independent of the invoice mutex: operations and invoices can flush in
// separate passes. Callers that need ordering (customers before invoices)
// await the operations sync first (see useOffline.js).
const opsMutex = new CoalescingMutex({ timeout: 60000, name: "OperationSync" })

const MAX_IN_PROGRESS_RETRIES = 3
const IN_PROGRESS_WAIT_MS = 2000

const DUPLICATE_ERROR_PATTERNS = [
	"DUPLICATE_OFFLINE",
	"already been synced",
	"already synced",
]
const SYNC_IN_PROGRESS_PATTERNS = [
	"SYNC_IN_PROGRESS",
	"currently being processed",
	"QueryDeadlock",
]

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

// ============================================================================
// HANDLER REGISTRY
// ============================================================================

/**
 * @typedef {Object} OpHandler
 * @property {string} method - Whitelisted server method to call
 * @property {(data: Object) => Object} [buildParams] - Map queued data to endpoint args
 * @property {(op: Object, refName: string) => Promise<void>|void} [onSynced] - Post-sync hook
 */

/** @type {Record<string, OpHandler>} */
const OP_HANDLERS = {}

/**
 * Register (or override) the sync handler for an operation type.
 * @param {string} type
 * @param {OpHandler} handler
 */
export const registerOpHandler = (type, handler) => {
	if (!handler?.method)
		throw new Error(`Handler for "${type}" requires a method`)
	OP_HANDLERS[type] = handler
}

/** @returns {string[]} registered operation types */
export const getRegisteredOpTypes = () => Object.keys(OP_HANDLERS)

// ============================================================================
// HELPERS
// ============================================================================

const errorText = (error) =>
	error?.message || error?.exc || error?.title || String(error)

const isDuplicateError = (error) =>
	DUPLICATE_ERROR_PATTERNS.some((p) => errorText(error).includes(p))

const isInProgressError = (error) =>
	SYNC_IN_PROGRESS_PATTERNS.some((p) => errorText(error).includes(p))

/** Extract the created document name from a variety of response shapes. */
const extractRefName = (res) => {
	if (!res) return ""
	if (typeof res === "string") return res
	return res.name || res.message?.name || res.ref_name || res.message || ""
}

/**
 * Pre-sync deduplication: has this op_id already produced a server doc?
 * @param {string} opId
 * @returns {Promise<{synced: boolean, ref_name?: string}>}
 */
const checkOpSynced = async (opId) => {
	if (!opId) return { synced: false }
	try {
		const res = await call("ecs_posnext.api.offline_ops.is_op_synced", {
			op_id: opId,
		})
		return res || { synced: false }
	} catch (error) {
		// If the check fails, proceed — the server enforces idempotency anyway
		log.warn("is_op_synced check failed", { op_id: opId, error })
		return { synced: false }
	}
}

// ============================================================================
// SYNC
// ============================================================================

/**
 * Sync a single operation to the server.
 * @param {Object} op - operation_queue record
 * @param {number} [retryCount=0]
 * @returns {Promise<{status: 'success'|'skipped', name?: string}>}
 */
const syncOperation = async (op, retryCount = 0) => {
	const handler = OP_HANDLERS[op.type]
	if (!handler) {
		throw new Error(`No sync handler registered for operation type: ${op.type}`)
	}

	// Pre-sync dedup
	const already = await checkOpSynced(op.op_id)
	if (already.synced) {
		return { status: "skipped", name: already.ref_name }
	}

	// buildParams may be async (e.g. resolving a synced shift's real name)
	const params = handler.buildParams
		? await handler.buildParams(op.data)
		: { ...op.data }

	try {
		const res = await call(handler.method, { ...params, op_id: op.op_id })
		const refName = extractRefName(res)
		return { status: "success", name: refName }
	} catch (error) {
		if (isInProgressError(error) && retryCount < MAX_IN_PROGRESS_RETRIES) {
			await sleep(IN_PROGRESS_WAIT_MS)
			return syncOperation(op, retryCount + 1)
		}
		throw error
	}
}

/**
 * Flush all pending offline operations to the server.
 * Mutex-guarded; concurrent callers coalesce onto the running pass.
 *
 * @returns {Promise<{success: number, skipped: number, failed: number, errors: Array}>}
 */
export const syncOfflineOperations = async () => {
	if (isOffline()) {
		log.debug("Cannot sync operations while offline")
		return { success: 0, skipped: 0, failed: 0, errors: [] }
	}

	return await opsMutex.withLock(async () => {
		const pending = await getPendingOperations()
		if (!pending.length) {
			return { success: 0, skipped: 0, failed: 0, errors: [] }
		}

		log.info(`Syncing ${pending.length} offline operation(s)`)
		const result = { success: 0, skipped: 0, failed: 0, errors: [] }

		for (const op of pending) {
			try {
				const r = await syncOperation(op)
				await markOperationSynced(op.id, r.name)
				if (r.status === "success") {
					result.success++
					// Post-sync hook (e.g. remap a temp customer name onto queued invoices)
					if (OP_HANDLERS[op.type]?.onSynced) {
						try {
							await OP_HANDLERS[op.type].onSynced(op, r.name)
						} catch (hookError) {
							log.error("onSynced hook failed", { type: op.type, hookError })
						}
					}
					log.success("Operation synced", {
						type: op.type,
						op_id: op.op_id,
						ref: r.name,
					})
				} else {
					result.skipped++
				}
			} catch (error) {
				if (isDuplicateError(error)) {
					await markOperationSynced(op.id, "")
					result.skipped++
					continue
				}
				log.error("Failed to sync operation", {
					id: op.id,
					type: op.type,
					error,
				})
				await handleOperationFailure(op.id, errorText(error))
				result.errors.push({ id: op.id, type: op.type, op_id: op.op_id, error })
				result.failed++
			}
		}

		log.info("Operation sync completed", {
			success: result.success,
			skipped: result.skipped,
			failed: result.failed,
		})

		if (typeof window !== "undefined") {
			window.dispatchEvent(
				new CustomEvent("offlineOperationsSynced", { detail: result }),
			)
		}

		return result
	}, log.debug.bind(log))
}
