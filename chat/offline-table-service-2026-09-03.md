# Session: 2026-09-03 — Offline Table Service

**Agent:** Claude Code (Opus 5)
**Developer:** erpcloud.systems
**Goal:** Close the offline gap left by the tables dashboard — held orders never reached the server

Follows [`open-tables-dashboard-2026-09-03.md`](open-tables-dashboard-2026-09-03.md).

---

## Summary

Raised as: offline holds stay in the browser and never reach the dashboard, even after the network
returns.

**The gap was bigger than reported.** Investigating first showed table service was *entirely*
blocked offline, not just its sync:

| Step | Before |
|---|---|
| List tables | `get_tables` — plain server call, fails offline |
| Seat a table | `start_table_session` — plain server call, fails offline |
| Hold | worked (local IndexedDB draft) |
| Sync on reconnect | did not exist |

So the reported symptom was the last link in a chain that was broken from the first step: a cashier
could not seat a table offline at all, which meant they could never reach the offline hold either.
The fix had to cover the whole chain.

---

## Changes Made

### Backend

**`POS Table Session`: `offline_id`** (Data, unique, read-only). Dedup key for a table seated
offline. Unique at the **database** level, following the existing `Offline Invoice Sync` pattern, so
a replay cannot duplicate even if the application check is bypassed.

**`api/table_orders.sync_offline_table_order`** — creates the session and its order in one
idempotent call keyed on `offline_id`:

- session found by `offline_id` → reuse it (this is what makes replay safe)
- table free → create the session, then `save_table_order` on it
- **table already seated by someone else** → return `{"status": "conflict"}` and write **nothing**

That last branch is the important judgement call. Merging an offline order into whatever session now
holds the table would splice two different parties' bills together — a money bug. Refusing and
handing the decision back is the only safe answer.

**`api/table_orders.promote_offline_session`** — creates the session alone, for coming online
mid-order when there is no hold to sync yet.

Both accept `opened_at` / `last_order_at` from the client and write them back with
`update_modified=False` after insert, because `before_insert` stamps `opened_at = now()`. Without
this, every table synced after an outage would look freshly seated and the idle colours — the whole
point of the dashboard — would be wrong.

### POS frontend

**Table list cache** (`TableGuestsDialog.vue`). Cached to `localStorage` on each successful fetch,
used as the fallback when the fetch fails. Occupancy fields (`occupied`, `session`,
`session_guest_count`) are **stripped before caching**: a stale "Occupied" badge is worse than no
badge, since it would block a table that is actually free.

**Offline seating.** When `offlineState.isOffline`, `confirm()` skips the server entirely and emits
a client-generated `pos_offline_session_<uuid>`. The prefix is deliberately distinct from the
`pos_offline_<uuid>` used for offline *invoices* — a shared prefix would make
`isOfflineSession()` match invoice ids too (covered by a test).

`tableOpenedAt` added to the cart state (`useInvoice` → `posCart`) and to the draft context, so the
real seating time survives a hold.

**Reconnect sync** (`syncOfflineTableOrders` in `POSSale.vue`). Scans local drafts for an offline
session id, syncs each, and deletes the local draft on success so the order exists in exactly one
place. Conflicts keep the draft and warn. A failed sync is left in place for the next reconnect
rather than dropped.

**Promotion on hold.** `saveTableOrderToServer` routes an offline session through
`sync_offline_table_order` instead of `save_table_order` (which would throw "session does not
exist"), then swaps the local id for the real session name so settling, the dashboard and later
holds all refer to the same record.

---

## Two frontend bugs caught before shipping

**1. The trigger fired too early to ever work.** The first version watched only
`offlineStore.isOffline` with `immediate: true`. At setup, POS Settings have not loaded, so
`tableServiceEnabled` is `false` and the watcher returned — meaning the "sync on a normal online
load" case never ran. Fixed by making settings part of the watched condition, with a
`offlineTableSyncDone` flag that reset on disconnect so it fires once per spell of connectivity
rather than on every dependency tick.

**2. Toast spam.** The sync loop called `draftsStore.deleteDraft`, which toasts "Draft deleted
successfully" per call — N toasts for N synced orders, plus the summary. Switched to the raw
`deleteDraft` util and one `loadDrafts()` after the loop to refresh the count.

---

## Verification

Backend, against `royal.erpnext.cloud`:

| Case | Result |
|---|---|
| Sync a table seated offline 40m ago, held 35m ago | session + order created, amount derived (240) |
| `opened_at` / `last_order_at` | preserved to within 2s of the offline times |
| Dashboard after sync | idle **35m**, seated **40m**, state **late** — not reset to sync time |
| Replay the identical sync | same session, same order; 1 session, 1 open order |
| Table taken by another cashier meanwhile | `conflict`, existing session reported, **nothing written** |
| `promote_offline_session` twice | same session, **no** order created |
| Duplicate `offline_id` inserted directly | `UniqueValidationError` |
| Test data left behind | 0 sessions, 0 orders |

Frontend, 10 vitest cases: offline-id recognition (including *not* matching an offline invoice id,
and null/empty), and the trigger — silent while offline, silent before settings load, fires once
settings arrive while online, exactly once per connectivity spell, again after a real
disconnect/reconnect, and never for a retail profile.

Build, `bench build` and migrations all clean.

---

## Follow-up Items

- [ ] Protel push — still the only outstanding piece from the original table-service work
- [ ] A sale completed entirely offline never creates a session or order. Correct for the dashboard
      (that table is no longer open) but it means no table-service record exists for those sales
- [ ] `POS Table Order` still has no cleanup for a shift closing with tables open
- [ ] Conflict resolution is manual — the cashier is told, but there is no "move this order to
      another table" action yet
