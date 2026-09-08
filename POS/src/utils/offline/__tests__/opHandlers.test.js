import { beforeEach, describe, expect, it, vi } from "vitest"

// ---- Mocks (no IndexedDB / no network) --------------------------------------
const H = vi.hoisted(() => {
	class FakeTable {
		constructor() {
			this.rows = []
			this.seq = 0
		}
		async add(obj) {
			const id = ++this.seq
			this.rows.push({ id, ...obj })
			return id
		}
		async get(id) {
			return this.rows.find((r) => r.id === id) || null
		}
		async update(id, changes) {
			const r = this.rows.find((x) => x.id === id)
			if (r) Object.assign(r, changes)
			return r ? 1 : 0
		}
		filter(fn) {
			const matched = this.rows.filter(fn)
			return {
				toArray: async () => matched.slice(),
				count: async () => matched.length,
				modify: async (mut) => {
					matched.forEach((r) => mut(r))
					return matched.length
				},
			}
		}
	}
	return {
		fakeDb: {
			operation_queue: new FakeTable(),
			invoice_queue: new FakeTable(),
		},
		// Stateful settings store: the shift name map lives here, so open_shift's
		// onSynced hook and the daily_payment handler see the same data.
		settings: {},
		uuid: { n: 0 },
		isOfflineMock: vi.fn(() => false),
		callMock: vi.fn(),
	}
})

const fakeDb = H.fakeDb
const callMock = H.callMock

vi.mock("../db", () => ({
	db: H.fakeDb,
	getSetting: vi.fn(async (key, fallback = null) =>
		key in H.settings ? H.settings[key] : fallback,
	),
	setSetting: vi.fn(async (key, value) => {
		H.settings[key] = value
	}),
}))

vi.mock("../uuid", () => ({ generateOfflineId: () => `op_${++H.uuid.n}` }))

vi.mock("@/utils/logger", () => ({
	logger: {
		create: () => ({
			info() {},
			warn() {},
			error() {},
			success() {},
			debug() {},
		}),
	},
}))

vi.mock("@/utils/mutex", () => ({
	CoalescingMutex: class {
		async withLock(fn) {
			return fn()
		}
	},
}))

vi.mock("../sync", () => ({ isOffline: H.isOfflineMock }))
vi.mock("@/utils/apiWrapper", () => ({ call: (...a) => H.callMock(...a) }))

// Import AFTER mocks are declared
import { enqueueOperation } from "../operations"
import { registerOfflineOpHandlers } from "../opHandlers"
import { syncOfflineOperations } from "../syncOps"

registerOfflineOpHandlers()

// open_shift's onSynced hook adopts the real shift name into localStorage,
// which the node test environment does not provide.
const store = new Map()
globalThis.localStorage = {
	getItem: (k) => (store.has(k) ? store.get(k) : null),
	setItem: (k, v) => store.set(k, String(v)),
	removeItem: (k) => store.delete(k),
	clear: () => store.clear(),
}

const REAL_SHIFT = "POSA-OS-26-0000094"

beforeEach(() => {
	fakeDb.operation_queue.rows = []
	fakeDb.operation_queue.seq = 0
	for (const k of Object.keys(H.settings)) delete H.settings[k]
	H.uuid.n = 0
	callMock.mockReset()
	H.isOfflineMock.mockReturnValue(false)
	localStorage.clear()
})

/** Find the arguments the sync engine passed to a given server method. */
const paramsFor = (method) =>
	callMock.mock.calls.find(([m]) => m === method)?.[1]

describe("daily_payment op handler", () => {
	it("swaps the offline opening-shift placeholder for the real name", async () => {
		const { op_id: openingOpId } = await enqueueOperation("open_shift", {
			pos_profile: "Main",
			company: "Hesham Rabea",
			balance_details: [],
			local_name: "OFFLINE-OPEN-op_1",
		})
		await enqueueOperation("daily_payment", {
			date: "2026-09-08",
			branch: "Main",
			employee: "HR-EMP-00003",
			amount: 120,
			deduction: 1,
			salary_component: "خصم من الراتب",
			pos_opening_shift: "OFFLINE-OPEN-op_1",
			opening_op_id: openingOpId,
		})

		callMock.mockImplementation(async (method) => {
			if (method === "ecs_posnext.api.offline_ops.is_op_synced")
				return { synced: false }
			if (method === "ecs_posnext.api.shifts.create_opening_shift")
				return { name: REAL_SHIFT }
			if (method === "ecs_posnext.api.daily_payment.create_daily_payment")
				return { name: "DP-0081", status: "submitted" }
			throw new Error(`unexpected method ${method}`)
		})

		const result = await syncOfflineOperations()

		expect(result.failed).toBe(0)
		expect(result.success).toBe(2)

		const params = paramsFor(
			"ecs_posnext.api.daily_payment.create_daily_payment",
		)
		// The real name is what makes the Daily Payment insert (and so the
		// deduction's Extra Salary) succeed on the server.
		expect(params.pos_opening_shift).toBe(REAL_SHIFT)
		expect(params.deduction).toBe(1)
		// opening_op_id is a client-side hint, not an endpoint argument
		expect(params).not.toHaveProperty("opening_op_id")
	})

	it("resolves via the server sync record when the local map is empty", async () => {
		// Models a reconnect where open_shift had already been recorded server-side
		// on an earlier pass, so its onSynced hook never repopulated the map.
		await enqueueOperation("daily_payment", {
			date: "2026-09-08",
			branch: "Main",
			deduction: 1,
			pos_opening_shift: "OFFLINE-OPEN-op_9",
			opening_op_id: "op_9",
		})

		callMock.mockImplementation(async (method, params) => {
			if (method === "ecs_posnext.api.offline_ops.is_op_synced")
				return params.op_id === "op_9"
					? { synced: true, ref_name: REAL_SHIFT }
					: { synced: false }
			if (method === "ecs_posnext.api.daily_payment.create_daily_payment")
				return { name: "DP-0082", status: "submitted" }
			throw new Error(`unexpected method ${method}`)
		})

		const result = await syncOfflineOperations()

		expect(result.failed).toBe(0)
		const params = paramsFor(
			"ecs_posnext.api.daily_payment.create_daily_payment",
		)
		expect(params.pos_opening_shift).toBe(REAL_SHIFT)
	})

	it("keeps the payment queued while the shift is unresolvable", async () => {
		await enqueueOperation("daily_payment", {
			date: "2026-09-08",
			branch: "Main",
			deduction: 1,
			pos_opening_shift: "OFFLINE-OPEN-op_never",
			opening_op_id: null,
		})

		callMock.mockImplementation(async (method) => {
			if (method === "ecs_posnext.api.offline_ops.is_op_synced")
				return { synced: false }
			throw new Error(`unexpected method ${method}`)
		})

		const result = await syncOfflineOperations()

		expect(result.failed).toBe(1)
		// Never created detached from its shift — the closing shift totals
		// daily payments by that field.
		expect(
			paramsFor("ecs_posnext.api.daily_payment.create_daily_payment"),
		).toBeUndefined()
		expect(fakeDb.operation_queue.rows[0].synced).toBe(false)
	})

	it("passes an online shift name through untouched", async () => {
		await enqueueOperation("daily_payment", {
			date: "2026-09-08",
			branch: "Main",
			deduction: 1,
			pos_opening_shift: REAL_SHIFT,
		})

		callMock.mockImplementation(async (method) => {
			if (method === "ecs_posnext.api.offline_ops.is_op_synced")
				return { synced: false }
			if (method === "ecs_posnext.api.daily_payment.create_daily_payment")
				return { name: "DP-0083", status: "submitted" }
			throw new Error(`unexpected method ${method}`)
		})

		const result = await syncOfflineOperations()

		expect(result.failed).toBe(0)
		expect(
			paramsFor("ecs_posnext.api.daily_payment.create_daily_payment")
				.pos_opening_shift,
		).toBe(REAL_SHIFT)
	})
})
