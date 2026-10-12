# Session: 2026-09-03 — Open Tables Dashboard with Idle Colour Coding

**Agent:** Claude Code (Opus 5)
**Developer:** erpcloud.systems
**Goal:** A dashboard of open tables and their orders, colouring a table by how long it has sat
without ordering

Follows on from [`table-and-guests-before-items-2026-09-03.md`](table-and-guests-before-items-2026-09-03.md).

---

## Summary

Requested: *"dashboard للترابيزات المفتوحة والطلبات الي خدوها. لو العميل قعد اكتر من فترة معينه
يتغير لون الترابيزة بلون مختلف انه قد فترة كبيرة بدون مايطلب"*.

**The blocking finding, surfaced before building:** held orders were stored **only in the cashier's
browser** (`utils/draftManager.js` → IndexedDB, database `ecs_posnext_drafts`). A dashboard could
therefore show open tables but not their orders on any other device. Separately,
`api/invoices.get_draft_invoices` exists on the backend but **nothing in the frontend calls it** —
a dead endpoint, not an existing server-side hold.

## Decisions Made

| Question | Decision |
|---|---|
| Where do held orders live? | **A new doctype** on the server — not draft Sales Invoices ("بدل sales invoice لا هنخليها new doctype افضل"), consistent with the Protel-not-ERPNext direction |
| Where does the dashboard live? | **Both** — POS sidebar and a Frappe Desk report |
| When does the idle clock start? | **From the last order**, falling back to seating time while nothing has been ordered |
| Colour levels | **Two** — amber then red, both configurable |

---

## Changes Made

### New: `POS Table Order` + `POS Table Order Item`

The server-side held order. Key design point: it carries the order **twice**, deliberately.

- `items` (child table: item_code, item_name, qty, uom, rate, amount) — the readable projection the
  dashboard and the Desk report read
- `cart_payload` (Long Text, JSON) — the **full** POS cart, which is what resume restores

The cart is far richer than six columns (offers, `item_uoms`, batch/serial, `conversion_factor`,
per-item discount and tax state). Rebuilding it from the child table would resume the order at
subtly wrong prices, so resume uses the payload and refuses rather than guessing when it is missing.

Totals (`total_qty`, `total_amount`) are recomputed in `validate()`, never trusted from the client,
and each row's `amount` falls back to `qty × rate`.

`last_order_at` only moves when `total_qty`/`total_amount` actually change — so a status change or
an `external_reference` being filled in does not reset the idle clock. `on_update` mirrors it onto
the session, which makes idle time a field lookup instead of a join per table.

### New: `ecs_posnext/api/table_orders.py`

| Endpoint | Purpose |
|---|---|
| `get_open_tables` | The dashboard. Sessions + order summary + idle minutes + colour band |
| `save_table_order` | Create or update a table's held order — **one open order per session**, so hold is idempotent |
| `get_table_order` | Resume, with the payload parsed back |
| `settle_table_order` / `cancel_table_order` | Settled on payment, cancelled on cart clear |
| `get_tables_summary` | Headline counts |

`get_open_tables` reads sessions first (a seated table may have no order at all), then fetches every
open order and all table metadata in **one query each** rather than per table.

Idle time falls back in three steps: the order's `last_order_at` → the session's mirror → the
seating time. `_idle_state` checks `late` before `warning` so the more severe band wins, and a
threshold of `0` disables its band instead of matching everything.

The response includes `server_now` so the client can tick timers without drifting against the
server clock or the browser timezone.

### POS Settings

`table_idle_warning_minutes` (default 15) and `table_idle_late_minutes` (default 30), both
`depends_on: require_table_and_guests`. Added to `POS_SETTINGS_FIELDS` **and**
`DEFAULT_POS_SETTINGS` (bootstrap reads through that whitelist and the store prefers bootstrap).
The controller rejects `late <= warning`.

### POS: `components/tables/TableDashboard.vue`

Full-screen overlay matching `InvoiceManagement.vue`. Cards sorted **worst-first** — the tables
needing attention are the entire point of the screen. Each card shows guests, item count, open
total, seated time, time since last order, and cashier; a card with no order says so explicitly.

Two timing details:
- Timers tick locally every 15s between 30s server refreshes, by adding locally-elapsed minutes to
  the server's figures — no timestamp maths, so no timezone or clock-skew bugs.
- `liveIdleState()` re-evaluates the colour band against the *live* timer, so a table crosses into
  amber or red between fetches instead of waiting for the next one.

Polling runs only while the dashboard is on screen. A refresh failure keeps the last good view;
only a first-load failure surfaces an error, since that is the only case leaving the cashier with
nothing.

New sidebar icon (`grid`), shown only when `require_table_and_guests` is on.

### POS: hold now goes to the server

`performSaveDraft()` routes table-service holds to `save_table_order` when online, and still falls
back to the local IndexedDB draft when offline — the only thing available without a network.
`closeTableSession`/`cancelTableSession` now settle/cancel the order **before** touching the
session, so a table can never be freed while its order is still open on the dashboard.

`handleOpenTableFromDashboard` holds the current cart before switching tables, and refuses to switch
(rather than discarding) when the cart has no session to be held against.

The gate panel's shortcut now points at the dashboard, with a separate, quieter link to offline
drafts — the two are different stores and conflating them would mislead.

### Desk: `Open Tables` Script Report

Calls the same `get_open_tables` as the POS dashboard, so the two can never disagree. Filters (POS
Profile / status / nothing-ordered-yet), coloured Status and Idle columns, donut chart, six summary
tiles, and an optional 30s auto-refresh button for a wall screen.

`status_label()` builds its labels per call: `_()` in a module-level dict would freeze them in
whichever language loaded the module first.

### Workspace patch — `v1_16_0.add_table_service_workspace_links`

Adds a "Table Service" card (Open Tables, Table, POS Table Session, POS Table Order).

Two things worth recording:

1. `v1_7_0.reinstall_workspace` **no longer applies this file at all** — it requires the workspace
   JSON to be a list (`isinstance(workspace_data, list)`) and `posnext.json` is now an object, so it
   silently returns. The new patch does its own narrower thing rather than relying on it.
2. The new patch **appends** rather than reinstalling, because a reinstall deletes the Workspace
   first and would discard shortcuts a site has added itself.

It also has to pin `idx`. Frappe derives a new row's `idx` from the row **count**, but this
workspace's existing links have gaps in theirs (3, 4, 8, 9, 10), so appended rows collided at 8/9/10
and the Table Service card rendered in the middle of the Offers card's links. `_pin_order()`
renumbers every row sequentially, which is also what repaired the site where that had already
happened.

---

## Verification

All against `royal.erpnext.cloud` (POS Profile "Buffet", 12 `Table` records), thresholds 15/30:

| Case | Result |
|---|---|
| Table ordered just now | `ok` |
| Table seated 18m, **never ordered** | `warning` — the requested behaviour |
| Table that ordered 47m ago | `late` |
| Amount omitted by client | derived as `qty × rate` (240) |
| Re-hold same session | updates the same order, does not stack |
| Empty items | ValidationError |
| Resume | `cart_payload` returned byte-identical (marker survived) |
| Settle | order Settled, table drops off the dashboard |
| Summary | 3 tables / 12 guests / 940 total / 1 warning / 1 late |
| Desk report | 13 columns, correct rows + indicators, chart `[ok,warning,late]`, 6 tiles |
| Report filters | `idle_state=late` → 1 row; `only_without_order` → the un-ordered table only |
| `late <= warning` | ValidationError |

Frontend build and `bench build` clean; migrations clean.

### Test-data incident

`bench console` **commits on exit**, so `frappe.db.rollback()` at the end of a console script does
not undo anything. Seven `POS Table Session` rows from earlier console runs were left committed,
each holding a table as "Occupied" and blocking it in the POS. They were identified (all
Administrator, timestamps matching the console runs) and deleted; the database is back to 0 sessions
and 0 orders.

Later tests were rewritten to run via `bench execute` and delete their own records in a `finally`
block, asserting `left_behind == 0` rather than trusting rollback.

---

## Follow-up Items

- [ ] Protel push — `external_reference` is in place on both the session and the order, but nothing
      posts to Protel yet
- [ ] Offline holds stay in IndexedDB and never reach the dashboard, even after coming back online.
      Syncing them into `POS Table Order` would close the last gap
- [ ] `POS Table Order` has no cleanup for a shift that closes with tables still open — a stale
      Open order keeps its table occupied indefinitely
- [ ] The dashboard polls every 30s; the app already has Socket.IO, so pushing table events would
      remove the polling
