/**
 * @fileoverview Registers sync handlers for offline write operations.
 *
 * Imported once at app startup (see main.js) so the operation sync engine
 * ({@link module:utils/offline/syncOps}) knows how to flush every queued op
 * type, regardless of which component enqueued it.
 *
 * @module utils/offline/opHandlers
 */

import { logger } from "@/utils/logger"
import { db, getSetting, setSetting } from "./db"
import { registerOpHandler } from "./syncOps"

const log = logger.create("OpHandlers")

// Maps offline temp shift names (OFFLINE-OPEN-*) to their real server names
// once the open_shift op has synced. Persisted so a page reload mid-sync still
// resolves dependent operations/invoices.
const SHIFT_MAP_KEY = "offline_shift_name_map"

const getShiftNameMap = async () => (await getSetting(SHIFT_MAP_KEY, {})) || {}

const setShiftNameMapping = async (localName, realName) => {
	if (!localName || !realName) return
	const map = await getShiftNameMap()
	map[localName] = realName
	await setSetting(SHIFT_MAP_KEY, map)
}

/**
 * Rewrite the opening-shift reference on queued (unsynced) invoices from a
 * temporary offline name to the real server name, so invoices sync correctly
 * after the shift they belong to has been created on the server.
 * @param {string} localName
 * @param {string} realName
 */
const remapQueuedInvoicesOpeningShift = async (localName, realName) => {
	if (!localName || !realName) return
	try {
		const modified = await db.invoice_queue
			.filter(
				(inv) => !inv.synced && inv.data?.posa_pos_opening_shift === localName,
			)
			.modify((inv) => {
				inv.data.posa_pos_opening_shift = realName
			})
		if (modified) {
			log.info("Remapped opening shift on queued invoices", {
				localName,
				realName,
				count: modified,
			})
		}
	} catch (error) {
		log.error("Failed to remap queued invoices' opening shift", error)
	}
}

/**
 * Resolve the real server name for a possibly-offline opening shift name.
 * Checks the local map first, then falls back to the server sync record.
 * @param {string} localName
 * @param {string} [opId] - open_shift op_id, used as a server-side fallback
 * @returns {Promise<string>} real name (or the input if already real / unresolved)
 */
const resolveOpeningShiftName = async (localName, opId) => {
	if (!localName || !localName.startsWith("OFFLINE-OPEN-")) return localName

	const map = await getShiftNameMap()
	if (map[localName]) return map[localName]

	// Fallback: ask the server whether the open_shift op has been recorded
	if (opId) {
		try {
			const { call } = await import("@/utils/apiWrapper")
			const res = await call("ecs_posnext.api.offline_ops.is_op_synced", {
				op_id: opId,
			})
			if (res?.synced && res.ref_name) {
				await setShiftNameMapping(localName, res.ref_name)
				return res.ref_name
			}
		} catch (error) {
			log.warn("resolveOpeningShiftName server fallback failed", error)
		}
	}

	// Not yet resolvable — throw so the close_shift op stays queued and retries
	// after the open_shift op syncs, rather than creating a closing for a
	// non-existent opening.
	throw new Error(`SYNC_IN_PROGRESS: opening shift ${localName} not yet synced`)
}

/**
 * Rewrite the customer reference on queued (unsynced) invoices from a temporary
 * offline customer name to the real server name, so invoices reference a
 * customer that exists after the customer op has synced.
 * @param {string} localName
 * @param {string} realName
 */
const remapQueuedInvoicesCustomer = async (localName, realName) => {
	if (!localName || !realName || localName === realName) return
	try {
		const modified = await db.invoice_queue
			.filter((inv) => !inv.synced && inv.data?.customer === localName)
			.modify((inv) => {
				inv.data.customer = realName
			})
		if (modified) {
			log.info("Remapped customer on queued invoices", {
				localName,
				realName,
				count: modified,
			})
		}
	} catch (error) {
		log.error("Failed to remap queued invoices' customer", error)
	}
}

let registered = false

/** Register all offline operation sync handlers (idempotent). */
export const registerOfflineOpHandlers = () => {
	if (registered) return
	registered = true

	// --- open_shift -------------------------------------------------------
	registerOpHandler("open_shift", {
		method: "ecs_posnext.api.shifts.create_opening_shift",
		buildParams: (data) => ({
			pos_profile: data.pos_profile,
			company: data.company,
			balance_details: JSON.stringify(data.balance_details || []),
			period_start_date: data.period_start_date || null,
		}),
		onSynced: async (op, refName) => {
			const localName = op.data?.local_name
			if (localName && refName) {
				await setShiftNameMapping(localName, refName)
				await remapQueuedInvoicesOpeningShift(localName, refName)

				// If this offline shift is still the active one, adopt the real name
				try {
					const cached = localStorage.getItem("pos_shift_data")
					if (cached) {
						const parsed = JSON.parse(cached)
						if (parsed?.pos_opening_shift?.name === localName) {
							parsed.pos_opening_shift.name = refName
							parsed.pos_opening_shift._offline = false
							localStorage.setItem("pos_shift_data", JSON.stringify(parsed))
						}
					}
				} catch (error) {
					log.warn("Failed to adopt real shift name into local state", error)
				}
			}
		},
	})

	// --- close_shift ------------------------------------------------------
	registerOpHandler("close_shift", {
		method: "ecs_posnext.api.shifts.submit_closing_shift",
		buildParams: async (data) => {
			const offlineClosing = data.closing_shift || {}

			// Resolve the real (server) opening-shift name
			const realOpening = await resolveOpeningShiftName(
				offlineClosing.pos_opening_shift || data.opening_shift_local_name,
				data.opening_op_id,
			)

			const { call } = await import("@/utils/apiWrapper")

			// Rebuild the authoritative closing structure from the server (correct
			// child-table shape + server-computed expected amounts), then overlay
			// the amounts the cashier actually counted offline.
			const serverClosing = await call(
				"ecs_posnext.api.shifts.get_closing_shift_data",
				{ opening_shift: realOpening },
			)

			const countedByMode = {}
			for (const p of offlineClosing.payment_reconciliation || []) {
				if (p?.mode_of_payment != null) {
					countedByMode[p.mode_of_payment] = p.closing_amount
				}
			}
			if (serverClosing?.payment_reconciliation) {
				for (const p of serverClosing.payment_reconciliation) {
					if (countedByMode[p.mode_of_payment] != null) {
						p.closing_amount = countedByMode[p.mode_of_payment]
					}
				}
			}

			return { closing_shift: JSON.stringify(serverClosing) }
		},
	})

	// --- attendance -------------------------------------------------------
	registerOpHandler("attendance", {
		method: "ecs_posnext.api.employee_attendance.mark_employee_attendance",
		buildParams: (data) => ({
			employee_list: JSON.stringify(data.employee_list || []),
			status: data.status,
			date: data.date,
			company: data.company || null,
			shift: data.shift || null,
		}),
	})

	// --- daily_payment ----------------------------------------------------
	registerOpHandler("daily_payment", {
		method: "ecs_posnext.api.daily_payment.create_daily_payment",
		buildParams: (data) => ({ ...data }),
	})

	// --- customer ---------------------------------------------------------
	registerOpHandler("customer", {
		method: "ecs_posnext.api.customers.create_customer",
		buildParams: (data) => ({
			customer_name: data.customer_name,
			mobile_no: data.mobile_no || null,
			email_id: data.email_id || null,
			customer_group: data.customer_group || undefined,
			territory: data.territory || undefined,
			company: data.company || null,
		}),
		onSynced: async (op, refName) => {
			// The temp name used on invoices is derived deterministically from op_id
			const localName = `OFFLINE-CUST-${op.op_id}`
			await remapQueuedInvoicesCustomer(localName, refName)
		},
	})

	log.info("Offline operation handlers registered")
}
