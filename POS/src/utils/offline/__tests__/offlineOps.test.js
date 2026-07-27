import { beforeEach, describe, expect, it, vi } from "vitest"

// ---- Mocks (no IndexedDB / no network) --------------------------------------
// Shared mock state must be created inside vi.hoisted so it exists when the
// hoisted vi.mock factories run.
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
		async delete(id) {
			this.rows = this.rows.filter((r) => r.id !== id)
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
		fakeDb: { operation_queue: new FakeTable(), invoice_queue: new FakeTable() },
		uuid: { n: 0 },
		isOfflineMock: vi.fn(() => false),
		callMock: vi.fn(),
	}
})

const fakeDb = H.fakeDb
const isOfflineMock = H.isOfflineMock
const callMock = H.callMock

vi.mock("../db", () => ({
	db: H.fakeDb,
	getSetting: vi.fn(async () => null),
	setSetting: vi.fn(async () => {}),
}))

vi.mock("../uuid", () => ({
	generateOfflineId: () => `op_${++H.uuid.n}`,
}))

vi.mock("@/utils/logger", () => ({
	logger: {
		create: () => ({
			info() {}, warn() {}, error() {}, success() {}, debug() {},
		}),
	},
}))

vi.mock("@/utils/mutex", () => ({
	// Run the critical section immediately, no locking
	CoalescingMutex: class {
		async withLock(fn) {
			return fn()
		}
	},
}))

// isOffline is imported by syncOps from ./sync
vi.mock("../sync", () => ({ isOffline: H.isOfflineMock }))

// The server call() — controlled per test
vi.mock("@/utils/apiWrapper", () => ({ call: (...a) => H.callMock(...a) }))

// Import AFTER mocks are declared
import {
	enqueueOperation,
	getPendingOperationCount,
	getPendingOperations,
	handleOperationFailure,
	markOperationSynced,
} from "../operations"
import {
	registerOpHandler,
	syncOfflineOperations,
} from "../syncOps"

beforeEach(() => {
	fakeDb.operation_queue.rows = []
	fakeDb.operation_queue.seq = 0
	H.uuid.n = 0
	callMock.mockReset()
	isOfflineMock.mockReturnValue(false)
})

// ---- operations.js ----------------------------------------------------------

describe("operation queue", () => {
	it("enqueues and lists pending ops oldest-first", async () => {
		const a = await enqueueOperation("attendance", { x: 1 })
		const b = await enqueueOperation("daily_payment", { y: 2 })
		expect(a.op_id).toBeTruthy()
		const pending = await getPendingOperations()
		expect(pending.map((o) => o.type)).toEqual(["attendance", "daily_payment"])
		expect(await getPendingOperationCount()).toBe(2)
		expect(await getPendingOperationCount("attendance")).toBe(1)
	})

	it("strips reactivity via structured clone (no throw on nested)", async () => {
		await expect(
			enqueueOperation("customer", { a: { b: [1, 2] } }),
		).resolves.toBeTruthy()
	})

	it("markOperationSynced removes op from pending", async () => {
		const { id } = await enqueueOperation("attendance", {})
		await markOperationSynced(id, "REF-1")
		expect(await getPendingOperationCount()).toBe(0)
		const row = await fakeDb.operation_queue.get(id)
		expect(row.synced).toBe(true)
		expect(row.server_name).toBe("REF-1")
	})

	it("handleOperationFailure flags sync_failed after 3 tries", async () => {
		const { id } = await enqueueOperation("attendance", {})
		await handleOperationFailure(id, "boom")
		await handleOperationFailure(id, "boom")
		let row = await fakeDb.operation_queue.get(id)
		expect(row.retry_count).toBe(2)
		expect(row.sync_failed).toBeUndefined()
		await handleOperationFailure(id, "boom")
		row = await fakeDb.operation_queue.get(id)
		expect(row.retry_count).toBe(3)
		expect(row.sync_failed).toBe(true)
	})
})

// ---- syncOps.js -------------------------------------------------------------

describe("operation sync engine", () => {
	// helper: make call() answer is_op_synced + the endpoint
	function wireCall({ synced = false, refName = null, endpoint } = {}) {
		callMock.mockImplementation(async (method) => {
			if (method === "ecs_posnext.api.offline_ops.is_op_synced") {
				return { synced, ref_name: refName }
			}
			return endpoint ? endpoint(method) : { name: "SERVER-1" }
		})
	}

	it("does nothing when offline", async () => {
		isOfflineMock.mockReturnValue(true)
		await enqueueOperation("attendance", {})
		const res = await syncOfflineOperations()
		expect(res).toEqual({ success: 0, skipped: 0, failed: 0, errors: [] })
		expect(callMock).not.toHaveBeenCalled()
	})

	it("syncs a pending op and marks it synced", async () => {
		registerOpHandler("t_ok", { method: "app.create", buildParams: (d) => d })
		wireCall({ endpoint: () => ({ name: "DOC-42" }) })
		const { id } = await enqueueOperation("t_ok", { foo: "bar" })

		const res = await syncOfflineOperations()
		expect(res.success).toBe(1)
		const row = await fakeDb.operation_queue.get(id)
		expect(row.synced).toBe(true)
		expect(row.server_name).toBe("DOC-42")
		// op_id is injected into the endpoint call
		const endpointCall = callMock.mock.calls.find((c) => c[0] === "app.create")
		expect(endpointCall[1]).toMatchObject({ foo: "bar", op_id: row.op_id })
	})

	it("skips an op already synced on the server (dedup)", async () => {
		registerOpHandler("t_dup", { method: "app.create" })
		wireCall({ synced: true, refName: "EXISTING" })
		const { id } = await enqueueOperation("t_dup", {})

		const res = await syncOfflineOperations()
		expect(res.skipped).toBe(1)
		expect(res.success).toBe(0)
		// endpoint create must NOT be called
		expect(callMock.mock.calls.some((c) => c[0] === "app.create")).toBe(false)
		expect((await fakeDb.operation_queue.get(id)).synced).toBe(true)
	})

	it("records a failure and increments retry on endpoint error", async () => {
		registerOpHandler("t_fail", { method: "app.create" })
		callMock.mockImplementation(async (method) => {
			if (method.endsWith("is_op_synced")) return { synced: false }
			throw new Error("server exploded")
		})
		const { id } = await enqueueOperation("t_fail", {})

		const res = await syncOfflineOperations()
		expect(res.failed).toBe(1)
		const row = await fakeDb.operation_queue.get(id)
		expect(row.synced).toBeFalsy()
		expect(row.retry_count).toBe(1)
		expect(row.last_error).toContain("server exploded")
	})

	it("runs onSynced hook after a successful sync", async () => {
		const hook = vi.fn()
		registerOpHandler("t_hook", { method: "app.create", onSynced: hook })
		wireCall({ endpoint: () => ({ name: "DOC-9" }) })
		await enqueueOperation("t_hook", {})
		await syncOfflineOperations()
		expect(hook).toHaveBeenCalledTimes(1)
		expect(hook.mock.calls[0][1]).toBe("DOC-9") // refName
	})

	it("awaits async buildParams (e.g. close_shift name resolution)", async () => {
		registerOpHandler("t_async", {
			method: "app.create",
			buildParams: async (d) => ({ resolved: d.raw + "!" }),
		})
		wireCall({ endpoint: () => ({ name: "DOC-async" }) })
		await enqueueOperation("t_async", { raw: "hi" })
		await syncOfflineOperations()
		const endpointCall = callMock.mock.calls.find((c) => c[0] === "app.create")
		expect(endpointCall[1]).toMatchObject({ resolved: "hi!" })
	})
})
