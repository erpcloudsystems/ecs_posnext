# Offline Mode — Detailed Implementation Plan (Phased)

> Goal: a cashier can run a **complete day offline** — open a shift, clock attendance,
> sell, record cash movements, create customers, and **close the shift** — with no
> internet, then everything syncs safely (no duplicates) when connectivity returns.
>
> Status legend: ✅ already works · ❌ broken offline · 🟡 partial

---

## 0. What already works vs. what is missing

| Day step | Offline status | Where |
|---|---|---|
| Open the app | ✅ | PWA runtime cache — `POS/vite.config.js:184` |
| Re-attach to an **existing** open shift | ✅ | `localStorage("pos_shift_data")` — `useShift.js:39` |
| **Open a new shift** | ❌ | `shifts.create_opening_shift` — no offline path |
| **Clock employee attendance** | ❌ | `EmployeeAttendance.vue:257` `mark_employee_attendance` |
| Sell all day (invoices) | ✅ | `invoice_queue` + `sync.js:354` + backend idempotency `invoices.py:1052` |
| **Create a customer mid-sale** | ❌ | `CreateCustomerDialog.vue` — direct insert, no queue |
| **Record a cash movement / expense** | ❌ | `DailyPaymentForm.vue:543` `create_daily_payment` + broken pickers |
| View branch balance / payment history | 🟡 | `DailyPaymentManagement.vue` — returns blank offline |
| **Close the shift / Z-report** | ❌ | `ShiftClosingDialog.vue` + `useShift.js:125` — no cache, no queue, prints via server |

**Root cause:** the proven offline pattern (`invoice_queue` → `sync.js` → backend `offline_id` dedup)
was never generalized to the other write operations.

---

## Δ Recent updates on `develop` — plan adjustments

Uncommitted feature/permission work already touches several files in this plan. None of it adds
offline support, so every gap below still stands — but it shifts a few priorities:

- **Create-customer button is now Administrator-only** (`InvoiceCart.vue`, gated by
  `isAdministrator` in `data/session.js`). So the **dedicated** `CreateCustomerDialog.vue`
  is no longer reachable by regular cashiers → its offline support drops to **LOW** priority.
  **But** `PaymentDialog.vue::completePayment` still auto-creates a customer at checkout when a name
  is typed (`PaymentDialog.vue:~2393`), reachable by any cashier, and it **already has an offline
  branch** (`PaymentDialog.vue:~2398`) that caches the customer via
  `customerSearchStore.addCustomerToCache` — **with no queue and no sync**. That half-path is the
  real risk (invoice syncs referencing a customer that never reaches the server). Phase 3.1 is
  refocused onto this path (see below).
- **Attendance now carries a Shift Type** (`employee_attendance.py::get_shift_types` +
  `mark_employee_attendance(shift=...)`, `EmployeeAttendance.vue`). The offline attendance queue
  (Phase 2.2) must include `shift`; `get_shift_types` should be cached (it already degrades to an
  empty dropdown offline via its `try/catch`).
- **Invoice history is now shift-scoped for cashiers** (`shifts.py::get_shift_invoices`,
  `InvoiceHistoryDialog.vue` now picks between two resources via an `activeResource` computed on
  `isAdministrator`). Neither resource has an offline fallback. Phase 2.4 must feed cached
  `invoice_history` into **whichever** resource is active for the current user.
- **Payment-method switching** (`PaymentDialog.vue`, removed "Clear All") is pure client logic —
  **no offline impact**.
- **Other admin-only buttons** (View Shift, Drafts, Return Invoice) — Return was already deliberately
  offline-gated; nothing to change.

---

## Phase 0 — Shared offline-operations foundation (prerequisite for all phases)

Build **one** generic operation queue + sync engine that mirrors the invoice pattern, so
Phases 1–3 only register new operation *types* instead of re-inventing queue/sync each time.

### 0.1 New IndexedDB store — `POS/src/utils/offline/db.js`

Add to `CURRENT_SCHEMA` (after `invoice_queue`, `db.js:43`):

```js
// Generic queue for non-invoice offline write operations
// op_id = client UUID for idempotency; type routes it to the right sync handler
operation_queue: "++id, &op_id, type, timestamp, synced",

// Cache stores read by the new offline screens
employees: "&name, employee_name, branch, company",
opening_dialog: "&key",          // cached POS profiles + balance-detail defaults
daily_payment_meta: "&key",      // expense-claim types, salary components, loan products
```

> Note: adding stores bumps the schema hash → auto version upgrade (`db.js:109`). **Before merging**,
> fix the version-reset data-loss bug (see Phase 3.3) so existing queued invoices survive the upgrade.

### 0.2 New module — `POS/src/utils/offline/operations.js`

Thin wrapper over the worker/DB, same shape as the invoice queue helpers:

```js
import { initDB } from "./db"
import { generateOfflineId } from "./uuid"

// Enqueue any offline write op. `type` must be registered in the sync registry (0.4).
export async function enqueueOperation(type, data) {
  const db = await initDB()
  const opId = generateOfflineId()
  const id = await db.table("operation_queue").add({
    op_id: opId, type, data,
    timestamp: Date.now(), synced: false, retry_count: 0,
  })
  return { success: true, id, op_id: opId }
}

export async function getPendingOperations(type = null) {
  const db = await initDB()
  let coll = db.table("operation_queue").filter((o) => !o.synced)
  return (await coll.toArray()).filter((o) => !type || o.type === type)
}

export async function markOperationSynced(id, serverName) {
  const db = await initDB()
  await db.table("operation_queue").update(id, {
    synced: true, synced_at: Date.now(), server_name: serverName,
  })
}

export async function handleOperationFailure(id, message) {
  const db = await initDB()
  const op = await db.table("operation_queue").get(id)
  const retry = (op?.retry_count || 0) + 1
  await db.table("operation_queue").update(id, {
    retry_count: retry, last_error: message, sync_failed: retry >= 3,
  })
}
```

### 0.3 New sync engine — `POS/src/utils/offline/syncOps.js`

Copy the structure of `sync.js:291-416` (mutex, per-item dedup, in-progress retry, failure
counting, cleanup) but drive it from a **type registry**:

```js
import { call } from "@/utils/apiWrapper"
import { isOffline } from "./sync"          // reuse existing offline check (sync.js:75)
import { getPendingOperations, markOperationSynced, handleOperationFailure } from "./operations"
import { syncMutex } from "./sync"          // export the existing mutex from sync.js

// type -> how to sync it. buildParams shapes the whitelisted-arg payload.
const OP_HANDLERS = {}
export function registerOpHandler(type, handler) { OP_HANDLERS[type] = handler }

async function syncOne(op) {
  const h = OP_HANDLERS[op.type]
  if (!h) throw new Error(`No sync handler for op type: ${op.type}`)
  // Pre-sync dedup: ask the server if this op_id already produced a doc
  const already = await call("ecs_posnext.api.offline_ops.is_op_synced", { op_id: op.op_id })
  if (already?.synced) return { status: "skipped", name: already.ref_name }
  const res = await call(h.method, { ...h.buildParams(op.data), op_id: op.op_id })
  return { status: "success", name: res?.name || res?.message }
}

export const syncOfflineOperations = async () => {
  if (isOffline()) return { success: 0, failed: 0, skipped: 0 }
  return syncMutex.withLock(async () => {
    const pending = await getPendingOperations()
    const result = { success: 0, failed: 0, skipped: 0, errors: [] }
    for (const op of pending) {
      try {
        const r = await syncOne(op)
        if (r.status === "success") { await markOperationSynced(op.id, r.name); result.success++ }
        else { await markOperationSynced(op.id, r.name); result.skipped++ }
      } catch (e) {
        await handleOperationFailure(op.id, e.message); result.errors.push({ op, e }); result.failed++
      }
    }
    return result
  })
}
```

> Requires exporting `syncMutex` from `sync.js` (currently module-private at `sync.js:15`).

### 0.4 Backend idempotency — new `ecs_posnext/api/offline_ops.py` + doctype `Offline Operation Sync`

Mirror the existing `Offline Invoice Sync` doctype (`offline_invoice_sync.py`) generically:

- **New doctype `Offline Operation Sync`**: fields `op_id` (Data, unique), `op_type` (Data),
  `ref_doctype` (Data), `ref_name` (Data), `status` (Select: Pending/Synced/Failed), `synced_at`.
- **`is_synced(op_id)` / `create_sync_record(op_id, ref_doctype, ref_name)`** — copy verbatim from
  `offline_invoice_sync.py:22-101`.

```python
# ecs_posnext/api/offline_ops.py
import frappe
from ecs_posnext.pos_next.doctype.offline_operation_sync.offline_operation_sync import OfflineOperationSync

@frappe.whitelist()
def is_op_synced(op_id):
    return OfflineOperationSync.is_synced(op_id)

def ensure_op_once(op_id, op_type):
    """Return existing ref if op_id already processed, else None. Call at the top of each
    whitelisted write that accepts op_id (open_shift, close_shift, attendance, daily_payment, customer)."""
    if not op_id:
        return None
    existing = OfflineOperationSync.is_synced(op_id)
    return existing.get("ref_name") if existing.get("synced") else None
```

Each write endpoint in Phases 1–3 gains an optional `op_id=None` arg, calls `ensure_op_once`
first (returns the existing doc name if already created), and calls `create_sync_record` after
a successful insert. This is exactly what `invoices.submit_invoice` does at `invoices.py:1304-1495`.

### 0.5 Wire auto-sync — `POS/src/composables/useOffline.js`

At the offline→online transition (`useOffline.js:119-126`, which today calls only the invoice sync),
also call `syncOfflineOperations()`. Order: **operations first** (shift/customer must exist server-side
before invoices that reference them sync), **then invoices**.

### 0.6 Shared "Pending Sync" UI (small, reused by all phases)

Extend the existing offline-invoices indicator (`components/sale/OfflineInvoicesDialog.vue`) into a
combined panel showing queued invoices **and** queued operations grouped by type, with a per-item
**Retry** button that clears `sync_failed` and re-runs the relevant sync. Closes the "failed ops
sit silently" gap (`sync.js` has no recovery UI today).

**Phase 0 deliverables:** `db.js` (+4 stores), new `operations.js`, new `syncOps.js`, export `syncMutex`
from `sync.js`, new `offline_ops.py` + `Offline Operation Sync` doctype, `useOffline.js` wiring,
extend `OfflineInvoicesDialog.vue`.

---

## Phase 1 — Shift lifecycle offline (CRITICAL: open + close the day)

### 1.1 Preload cache (while online) — extend the preload in `POS/src/pages/POSSale.vue` (~`1398`)

Cache what the open/close dialogs need:
- `shifts.get_opening_dialog_data()` → `opening_dialog` store (key `"data"`).
- Warehouses (`get_warehouses`, the one unguarded call at `POSSale.vue:1139`) → `settings`.

### 1.2 Open a shift offline — `POS/src/composables/useShift.js` + `ShiftOpeningDialog.vue`

`createOpeningShift` today is a bare `createResource` (`useShift.js:85-113`). Add an offline branch:

```js
async function createOpeningShiftOffline({ pos_profile, company, balance_details }) {
  const startedAt = new Date().toISOString()
  const localName = `OFFLINE-OPEN-${Date.now()}`     // temp name until synced
  const { op_id } = await enqueueOperation("open_shift", {
    pos_profile, company, balance_details, period_start_date: startedAt, local_name: localName,
  })
  const data = {
    pos_opening_shift: { name: localName, pos_profile, company,
      period_start_date: startedAt, status: "Open", _offline: true, _op_id: op_id },
    pos_profile: getCachedOpeningDialog().profiles.find(p => p.name === pos_profile),
    company,
  }
  shiftState.value = { ...data, isOpen: true, _initialElapsedMs: 0, _receivedAt: Date.now() }
  localStorage.setItem("pos_shift_data", JSON.stringify({ ...data, _receivedAt: Date.now() }))
  return data
}
```

`ShiftOpeningDialog.vue`: when `isOffline()`, read profiles/payment-methods from the
`opening_dialog` cache instead of `get_opening_dialog_data.fetch()` (`ShiftOpeningDialog.vue:232`),
and route submit through `createOpeningShiftOffline`.

### 1.3 Backend — `ecs_posnext/api/shifts.py::create_opening_shift` (`shifts.py:104`)

- Add `op_id=None, period_start_date=None`.
- `existing = ensure_op_once(op_id, "open_shift")` at the top → if set, return the existing shift
  (idempotent re-sync).
- Use the client `period_start_date` (the real offline start time) instead of `get_datetime()`
  at `shifts.py:116` when provided.
- After `.submit()`, `create_sync_record(op_id, "POS Opening Shift", new_pos_opening.name)`.
- Keep the "already have an open shift" guard (`shifts.py:110`) but treat a matching `op_id` as the
  same shift, not a conflict.

### 1.4 Close a shift offline — `useShift.js` + `ShiftClosingDialog.vue`

Closing needs the reconciliation figures. Compute them **locally** from cached data:
- Cash/sales totals from `invoice_history` + unsynced `invoice_queue` for the current shift.
- Build a `closing_shift` payload matching `get_closing_shift_data` shape (`shifts.py:147`), then:

```js
async function submitClosingShiftOffline(closingShift) {
  const { op_id } = await enqueueOperation("close_shift", {
    closing_shift: closingShift, opening_op_id: shiftState.value.pos_opening_shift?._op_id,
  })
  shiftState.value = { pos_opening_shift: null, pos_profile: null, company: null, isOpen: false,
    _initialElapsedMs: 0, _receivedAt: 0 }
  localStorage.removeItem("pos_shift_data")
  return { op_id, offline: true }
}
```

- **Z-report offline:** replace the server `/printview` (`ShiftClosingDialog.vue:648`) with a
  client-rendered receipt built from the local closing payload (reuse the existing invoice
  print-template approach). Server printout is regenerated after sync.

### 1.5 Backend — `shifts.py::submit_closing_shift` (`shifts.py:170`)

- Add `op_id=None`; `ensure_op_once` → return existing closing name if already synced.
- **Dependency:** if `opening_op_id` maps to an offline opening not yet synced, resolve the real
  POS Opening Shift name first (operation sync runs opens before closes — see 0.5). Guard with a
  clear error if the opening is missing so the op stays queued rather than failing permanently.
- `create_sync_record(op_id, "POS Closing Shift", name)` after submit.

**Phase 1 files:** `db.js` (stores from 0.1), `useShift.js`, `ShiftOpeningDialog.vue`,
`ShiftClosingDialog.vue`, `POSSale.vue` (preload + warehouses), `shifts.py`.

---

## Phase 2 — Attendance + Daily Payment offline (the two you flagged)

### 2.1 Preload cache
- `employee_attendance.get_employees(date, company, branch)` → `employees` store (refresh on preload
  and on going-online). `EmployeeAttendance.vue:236` reads from cache when `isOffline()`.
- `employee_attendance.get_shift_types()` → cache the shift-type list (drives the new Shift dropdown
  at `EmployeeAttendance.vue`). Already degrades to an empty dropdown offline via its `try/catch`;
  caching just keeps the dropdown populated offline.
- Daily-payment pickers → `daily_payment_meta` store: expense-claim types, salary components, loan
  products, and the employee list (replaces the `search_link`/`employee_query` LinkInputs at
  `DailyPaymentForm.vue:604` that fail offline). Offline, the LinkInputs become
  cache-backed selects.

### 2.2 Attendance offline — `EmployeeAttendance.vue`

Guard `mark_employee_attendance` (`EmployeeAttendance.vue:257`):

```js
if (isOffline()) {
  // include `shift` — the field added by the recent attendance update
  await enqueueOperation("attendance", { employee_list, status, date, company, shift })
  toast.success(`Attendance queued for ${employee_list.length} employee(s) — will sync when online`)
} else { await call("ecs_posnext.api.employee_attendance.mark_employee_attendance", {...}) }
```

**Backend** `mark_employee_attendance` (`employee_attendance.py:55`, already accepts `shift`): add `op_id=None`;
`ensure_op_once`; make insert idempotent per `(employee, attendance_date)` (skip/return existing
Attendance if one exists for that pair — protects against double submit on retry); record sync.
Register handler in `syncOps.js`: `{ method: "...mark_employee_attendance", buildParams: d => d }`.

### 2.3 Daily Payment offline — `DailyPaymentForm.vue`

Guard `create_daily_payment` (`DailyPaymentForm.vue:543`): offline → `enqueueOperation("daily_payment", formData)`.
Employee/expense-type/salary-component pickers read from `daily_payment_meta` cache when offline (2.1).

**Backend** `create_daily_payment` (`daily_payment.py:230`): add `op_id=None`; `ensure_op_once`
returns existing Daily Payment name on re-sync; `create_sync_record(op_id, "Daily Payment", doc.name)`
after submit. Register the `daily_payment` handler in `syncOps.js`.

### 2.4 Read-only screens (graceful, not blocking)
- `DailyPaymentManagement.vue` `get_branch_balance` / `get_daily_payments`
  (`daily_payment.py:35,73`): when offline, show cached-or-empty with a clear
  “balance/history unavailable offline” banner instead of a silent zero + error toast.
- `TrackInvoices.vue` `get_invoice_counts` (`daily_payment.py:143`): compute counts **locally**
  from `invoice_history` + `invoice_queue` so the shift dashboard is correct offline.
- `InvoiceHistoryDialog.vue` now selects between two resources via an `activeResource` computed
  (`shifts.get_shift_invoices` for cashiers, `frappe.client.get_list` for admins). Neither has an
  offline fallback: when `isOffline()`, populate `invoices` from the cached `invoice_history` store
  (plus unsynced `invoice_queue`) regardless of which resource is active, instead of calling either.

**Phase 2 files:** `EmployeeAttendance.vue`, `DailyPaymentForm.vue`, `DailyPaymentManagement.vue`,
`TrackInvoices.vue`, `POSSale.vue` (preload), `employee_attendance.py`, `daily_payment.py`,
`syncOps.js` (register 2 handlers).

---

## Phase 3 — Offline customer creation + reliability cleanup

### 3.1 Create a customer offline — primary path is `PaymentDialog.vue`, not the dialog

> Priority note (recent update): the dedicated `CreateCustomerDialog.vue` is now **Administrator-only**
> (`InvoiceCart.vue` gates its button on `isAdministrator`), so it drops to LOW priority. The path
> regular cashiers actually hit is the **inline auto-create at checkout** in `PaymentDialog.vue`.

**Primary — fix the inline checkout path (`PaymentDialog.vue::completePayment`, ~`2393`).**
It already has an offline branch (~`2398`) that caches the typed-in customer via
`customerSearchStore.addCustomerToCache(newCust)` **but never queues or syncs it** — so an invoice
that references `newCust.name` can reach the server with a customer that doesn't exist. Fix:
- On that offline branch, also `enqueueOperation("customer", newCust)` with a temp name
  `OFFLINE-CUST-<op_id>` and store that temp name on the cached customer.
- **Name remapping (critical):** when the `customer` op syncs, the temp name becomes a real Customer
  name. Before invoices sync, rewrite any queued `invoice_queue` rows whose `customer` equals the
  temp name to the real name. Implement `remapQueuedCustomer(tempName, realName)`, call it from the
  `customer` op’s success handler, and enforce sync order (customers → invoices) in 0.5.

**Secondary — `CreateCustomerDialog.vue` (LOW, admin-only).** Same treatment when convenient:
route its submit (`CreateCustomerDialog.vue:335,453`) through `enqueueOperation("customer", …)` when
offline; cache territory / customer-group pickers (`CreateCustomerDialog.vue:384`) during preload.

**Backend:** a whitelisted `create_customer(data, op_id)` with `ensure_op_once` +
`create_sync_record(op_id, "Customer", name)`, shared by both paths.

### 3.2 Fix stranded offline payments
`payment_queue` is written (`sync.js:488`) but **never synced** (data loss). Either:
- (preferred) fold standalone payments into `operation_queue` as type `payment` with a real backend
  sync + idempotency, **or**
- if standalone offline payments aren’t a supported flow, remove `saveOfflinePayment`/`payment_queue`
  (`sync.js:488-500`, `db.js:62`, clear at `db.js:262`) as dead code so it can’t silently lose data.

### 3.3 Fix the schema-version data-loss bug — `db.js:109-126`
Version is derived from a **localStorage** hash; clearing localStorage resets it to 1 and Dexie throws
`VersionError`, recovered only by nuking the DB (`db.js:154-191`) — which **deletes the unsynced
queue**. Fix: persist the version/hash inside IndexedDB (a `settings` row) rather than localStorage,
and on `VersionError` attempt an export-of-queue → recreate → re-import before nuking.

### 3.4 Fix the worker DB init-order race — `offline.worker.js:101-110`
The worker opens the DB with **no schema** and throws “No tables found” if it wins the race against
`db.js` (`offline.worker.js:108`). Fix: define the same `CURRENT_SCHEMA` in the worker (import a
shared `schema.js` used by both `db.js` and the worker) so whichever opens first creates the stores.

### 3.5 Dead-code cleanup (low risk, do last)
- `items.js` legacy `*Old` search exports (aliased in `index.js`) — remove once confirmed unused.
- Duplicate `saveOfflineInvoice`/`updateLocalStock`/`getLocalStock` in `sync.js:89-111` (the UI uses
  the worker path) — remove or clearly mark as the single source of truth.
- `translations` store (`db.js:68`) never read/written — remove or implement.

**Phase 3 files:** `CreateCustomerDialog.vue`, `PaymentDialog.vue`, new `create_customer` endpoint,
`sync.js`, `db.js`, `offline.worker.js`, new shared `schema.js`, `items.js`, `index.js`.

---

## Suggested order & rough sizing

| Phase | Blocks the offline day? | Effort |
|---|---|---|
| 0 — foundation | prerequisite | M (1 store migration + 2 modules + 1 doctype) |
| 1 — shift open/close | **Yes — starts & ends the day** | L (local Z-report is the hard part) |
| 2 — attendance + daily payment | **Yes — you flagged these** | M |
| 3 — offline customer + reliability fixes | Partly (customer) + prevents data loss | M |

Recommended: **0 → 1 → 2 → 3**. Phase 0 is small but everything else reuses it. If you want to
see attendance/daily-payment working fastest, we can do **0 → 2** first and defer the shift Z-report
(Phase 1) — the two are independent once Phase 0 exists.

### Open decisions to confirm before coding
1. **Backend idempotency:** one generic `Offline Operation Sync` doctype (recommended, this plan) vs.
   adding a bespoke `op_id` guard per endpoint with no tracking doctype.
2. **Offline Z-report:** client-rendered receipt at close (recommended) vs. block closing offline and
   only allow it once online (simpler, but breaks the “close the day offline” goal).
3. **Standalone offline payments (3.2):** wire a real sync, or remove as unsupported dead code?
