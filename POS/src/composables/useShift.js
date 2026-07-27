import { createResource } from "frappe-ui"
import { computed, ref } from "vue"
import { db, getSetting, setSetting } from "@/utils/offline/db"
import { enqueueOperation } from "@/utils/offline/operations"
import { isOffline } from "@/utils/offline/sync"
import { generateOfflineId } from "@/utils/offline/uuid"

// Settings-store key holding the cached get_opening_dialog_data payload so a new
// shift can be opened while offline.
export const OPENING_DIALOG_CACHE_KEY = "opening_dialog_data"

export const shiftState = ref({
	pos_opening_shift: null,
	pos_profile: null,
	company: null,
	isOpen: false,
	/** Initial elapsed ms at the moment shift data was received from server */
	_initialElapsedMs: 0,
	/** Local timestamp (Date.now()) when shift data was received */
	_receivedAt: 0,
})

export function useShift() {
	// Check for existing open shift
	const checkOpeningShift = createResource({
		url: "ecs_posnext.api.shifts.check_opening_shift",
		auto: false,
		onSuccess(data) {
			if (data) {
				// Compute initial elapsed time using server timestamps
				// (avoids timezone mismatch between server and browser)
				let initialElapsedMs = 0
				if (data.server_now && data.pos_opening_shift?.period_start_date) {
					const serverNow = new Date(data.server_now).getTime()
					const shiftStart = new Date(data.pos_opening_shift.period_start_date).getTime()
					initialElapsedMs = Math.max(0, serverNow - shiftStart)
				}
				shiftState.value = {
					pos_opening_shift: data.pos_opening_shift,
					pos_profile: data.pos_profile,
					company: data.company,
					isOpen: true,
					_initialElapsedMs: initialElapsedMs,
					_receivedAt: Date.now(),
				}
				// Store in localStorage for offline support
				localStorage.setItem("pos_shift_data", JSON.stringify({
					...data,
					_initialElapsedMs: initialElapsedMs,
					_receivedAt: Date.now(),
				}))
			} else {
				shiftState.value = {
					pos_opening_shift: null,
					pos_profile: null,
					company: null,
					isOpen: false,
					_initialElapsedMs: 0,
					_receivedAt: 0,
				}
				localStorage.removeItem("pos_shift_data")
			}
		},
		onError(error) {
			console.error("Error checking opening shift:", error)
			// Try to load from localStorage
			const cachedData = localStorage.getItem("pos_shift_data")
			if (cachedData) {
				try {
					const data = JSON.parse(cachedData)
					shiftState.value = {
						pos_opening_shift: data.pos_opening_shift,
						pos_profile: data.pos_profile,
						company: data.company,
						isOpen: true,
						_initialElapsedMs: data._initialElapsedMs || 0,
						_receivedAt: data._receivedAt || Date.now(),
					}
				} catch (e) {
					console.error("Error parsing cached shift data:", e)
				}
			}
		},
	})

	// Get opening dialog data (POS profiles, payment methods, etc.)
	const getOpeningDialogData = createResource({
		url: "ecs_posnext.api.shifts.get_opening_dialog_data",
		auto: false,
	})

	// Create new opening shift
	const createOpeningShift = createResource({
		url: "ecs_posnext.api.shifts.create_opening_shift",
		makeParams({ pos_profile, company, balance_details }) {
			return {
				pos_profile,
				company,
				balance_details: JSON.stringify(balance_details),
			}
		},
		onSuccess(data) {
			shiftState.value = {
				pos_opening_shift: data.pos_opening_shift,
				pos_profile: data.pos_profile,
				company: data.company,
				isOpen: true,
				_initialElapsedMs: 0,
				_receivedAt: Date.now(),
			}
			// Store in localStorage
			localStorage.setItem("pos_shift_data", JSON.stringify({
				...data,
				_initialElapsedMs: 0,
				_receivedAt: Date.now(),
			}))
		},
		onError(error) {
			console.error("Error creating opening shift:", error)
		},
	})

	// Get closing shift data
	const getClosingShiftData = createResource({
		url: "ecs_posnext.api.shifts.get_closing_shift_data",
		makeParams({ opening_shift }) {
			return { opening_shift }
		},
		auto: false,
	})

	// Submit closing shift
	const submitClosingShift = createResource({
		url: "ecs_posnext.api.shifts.submit_closing_shift",
		makeParams({ closing_shift }) {
			return { closing_shift: JSON.stringify(closing_shift) }
		},
		onSuccess() {
			shiftState.value = {
				pos_opening_shift: null,
				pos_profile: null,
				company: null,
				isOpen: false,
				_initialElapsedMs: 0,
				_receivedAt: 0,
			}
			localStorage.removeItem("pos_shift_data")
		},
		onError(error) {
			console.error("Error submitting closing shift:", error)
		},
	})

	// ========================================================================
	// OFFLINE SHIFT LIFECYCLE
	// ========================================================================

	/**
	 * Cache the opening-dialog payload (POS profiles + payment methods) so a
	 * shift can be opened later without a server round-trip.
	 * @param {Object} data - Result of ecs_posnext.api.shifts.get_opening_dialog_data
	 */
	const cacheOpeningDialogData = async (data) => {
		if (!data) return
		try {
			await setSetting(OPENING_DIALOG_CACHE_KEY, data)
		} catch (error) {
			console.error("Error caching opening dialog data:", error)
		}
	}

	/**
	 * Read the cached opening-dialog payload for offline shift opening.
	 * @returns {Promise<Object|null>}
	 */
	const getCachedOpeningDialogData = async () => {
		return await getSetting(OPENING_DIALOG_CACHE_KEY, null)
	}

	/**
	 * Open a shift while offline. Queues an `open_shift` operation and sets local
	 * shift state under a temporary name so selling can begin immediately. The
	 * temporary name is remapped onto queued invoices when the op later syncs
	 * (see registerShiftOpHandlers in utils/offline/opHandlers.js).
	 *
	 * @returns {Promise<Object>} the local shift data (mirrors the server shape)
	 */
	const createOpeningShiftOffline = async ({
		pos_profile,
		company,
		balance_details,
		profile = null,
	}) => {
		const startedAt = new Date().toISOString()
		const localName = `OFFLINE-OPEN-${generateOfflineId()}`

		const { op_id } = await enqueueOperation("open_shift", {
			pos_profile,
			company,
			balance_details,
			period_start_date: startedAt,
			local_name: localName,
		})

		const openingShiftDoc = {
			name: localName,
			pos_profile,
			company,
			period_start_date: startedAt,
			status: "Open",
			// Kept locally so an offline shift-close can compute expected amounts
			balance_details: balance_details || [],
			_offline: true,
			_op_id: op_id,
		}

		const data = {
			pos_opening_shift: openingShiftDoc,
			pos_profile: profile || { name: pos_profile, company },
			company: company ? { name: company } : null,
		}

		shiftState.value = {
			pos_opening_shift: openingShiftDoc,
			pos_profile: data.pos_profile,
			company: data.company,
			isOpen: true,
			_initialElapsedMs: 0,
			_receivedAt: Date.now(),
		}
		localStorage.setItem(
			"pos_shift_data",
			JSON.stringify({ ...data, _initialElapsedMs: 0, _receivedAt: Date.now() }),
		)

		return data
	}

	/**
	 * Build the shift-closing dataset locally from cached/queued invoices when
	 * offline, mirroring the shape returned by get_closing_shift_data so the
	 * closing dialog can render without the server.
	 *
	 * @param {string} openingName - Opening shift name (may be an offline temp name)
	 * @returns {Promise<Object>}
	 */
	const buildOfflineClosingData = async (openingName) => {
		// Opening shift info (incl. opening balances) from local state
		let openingDoc = shiftState.value.pos_opening_shift
		if (!openingDoc || openingDoc.name !== openingName) {
			try {
				const cached = localStorage.getItem("pos_shift_data")
				if (cached) openingDoc = JSON.parse(cached).pos_opening_shift
			} catch {
				openingDoc = null
			}
		}
		const balanceDetails = openingDoc?.balance_details || []

		// This shift's invoices still sitting in the offline queue
		const queued = await db.invoice_queue
			.filter((inv) => inv.data?.posa_pos_opening_shift === openingName)
			.toArray()

		const salesByMethod = {}
		let grandTotal = 0
		let totalTax = 0
		const posTransactions = []

		for (const q of queued) {
			const d = q.data || {}
			grandTotal += Number(d.grand_total || 0)
			totalTax += Number(d.total_tax || 0)
			for (const p of d.payments || []) {
				const amt = Number(p.amount || 0)
				if (!amt) continue
				salesByMethod[p.mode_of_payment] =
					(salesByMethod[p.mode_of_payment] || 0) + amt
			}
			posTransactions.push({
				sales_invoice: d.offline_id || `OFFLINE-${q.timestamp}`,
				pos_invoice: null,
				customer: d.customer || "",
				grand_total: Number(d.grand_total || 0),
				posting_date: new Date(q.timestamp).toISOString(),
				is_return: false,
			})
		}

		const methods = new Set([
			...balanceDetails.map((b) => b.mode_of_payment),
			...Object.keys(salesByMethod),
		])
		const paymentReconciliation = [...methods].map((mode) => {
			const opening = Number(
				balanceDetails.find((b) => b.mode_of_payment === mode)?.opening_amount ||
					0,
			)
			const sales = salesByMethod[mode] || 0
			return {
				mode_of_payment: mode,
				opening_amount: opening,
				expected_amount: opening + sales,
				closing_amount: null,
				difference: 0,
			}
		})

		return {
			pos_opening_shift: openingName,
			pos_profile: openingDoc?.pos_profile || null,
			period_start_date: openingDoc?.period_start_date || null,
			grand_total: grandTotal,
			sales_total: grandTotal,
			returns_total: 0,
			returns_count: 0,
			sales_count: posTransactions.length,
			taxes: [],
			pos_transactions: posTransactions,
			payment_reconciliation: paymentReconciliation,
			_offline: true,
		}
	}

	/**
	 * Submit a shift closing while offline. Queues a `close_shift` operation and
	 * clears local shift state. The Z-report is rendered locally by the closing
	 * dialog; the server regenerates official figures on sync.
	 *
	 * @param {Object} closingShift - Closing payload (same shape as the online submit)
	 * @returns {Promise<{op_id: string, offline: true}>}
	 */
	const submitClosingShiftOffline = async (closingShift) => {
		const openingOpId = shiftState.value.pos_opening_shift?._op_id || null
		const openingName = shiftState.value.pos_opening_shift?.name || null

		const { op_id } = await enqueueOperation("close_shift", {
			closing_shift: closingShift,
			opening_op_id: openingOpId,
			opening_shift_local_name: openingName,
		})

		shiftState.value = {
			pos_opening_shift: null,
			pos_profile: null,
			company: null,
			isOpen: false,
			_initialElapsedMs: 0,
			_receivedAt: 0,
		}
		localStorage.removeItem("pos_shift_data")

		return { op_id, offline: true }
	}

	// Computed properties
	const hasOpenShift = computed(() => shiftState.value.isOpen)
	const currentShift = computed(() => shiftState.value.pos_opening_shift)
	const currentProfile = computed(() => shiftState.value.pos_profile)
	const currentCompany = computed(() => shiftState.value.company)

	return {
		// State
		shiftState,
		hasOpenShift,
		currentShift,
		currentProfile,
		currentCompany,

		// Resources
		checkOpeningShift,
		getOpeningDialogData,
		createOpeningShift,
		getClosingShiftData,
		submitClosingShift,

		// Offline lifecycle
		cacheOpeningDialogData,
		getCachedOpeningDialogData,
		createOpeningShiftOffline,
		buildOfflineClosingData,
		submitClosingShiftOffline,
	}
}
