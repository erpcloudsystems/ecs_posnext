# Session: 2026-09-03 — Require Table & Guest Count Before Item Selection

**Agent:** Claude Code (Opus 5)
**Developer:** erpcloud.systems
**Goal:** Gate the POS so a table number and guest count are chosen before any item can enter the cart

---

## Summary

Requested (in Arabic): *"قبل اختيار الـ items اول حاجة نحدد رقم الترابيزة وعدد الافراد"* — before
selecting items, first determine the table number and the number of guests.

**State before this session:**
- Table number was asked **only at Hold time** — `handleSaveDraft()` in `POSSale.vue` opened a
  table dialog when `cartStore.table` was empty. There was no gate before item selection.
- **Guest count did not exist anywhere.** Not in the `Table` doctype (its `seating_capacity` is
  the table's physical capacity, not the current head count), and not among the Sales Invoice
  custom fields (`room`, `table`, `posa_customer_type`).

## Decisions Made

Four decisions were put to the developer before implementation:

| Question | Decision |
|---|---|
| When does the gate apply? | Behind a new **POS Settings** toggle, so retail/take-away profiles are unaffected |
| Shape of the UI | **Simple dialog** — table dropdown + guest counter (reuses the existing Hold dialog pattern) |
| Where is guest count stored? | **A new doctype** — *"انا مش بحفظ عندي انا برمي ع protel"* (the sale is posted to Protel, not persisted locally as a Sales Invoice) |
| Editable after starting? | **Yes**, from a header chip at any time |

The storage decision is the important one: guest count is **not** a Sales Invoice custom field.
It lives in `POS Table Session`, which is independent of whether a Sales Invoice is ever created.
An `external_reference` field is provided as the hook for the Protel reference.

**Not built (out of scope for this request):** the actual Protel push. `POS Table Session` records
the table/guest context and exposes `external_reference` for it, but nothing posts to Protel yet.

---

## Changes Made

### New: `ecs_posnext/pos_next/doctype/pos_table_session/`

`POS Table Session` — naming series `POS-TS-.YYYY.-`.

| Field | Type | Notes |
|---|---|---|
| `table` | Link → Table | required |
| `guest_count` | Int | required, >= 1 |
| `status` | Select | Open / Closed / Cancelled |
| `pos_profile`, `pos_opening_shift`, `cashier` | Link | context |
| `opened_at`, `closed_at` | Datetime | read-only |
| `sales_invoice` | Link → Sales Invoice | read-only, optional — empty when posted externally |
| `external_reference` | Data | reference from the external system (e.g. Protel) |

Controller validations:
- `guest_count >= 1`
- the table must not be `disabled`
- **only one `Open` session per table** — otherwise two cashiers could each build a separate
  order for the same table, the exact duplicate the table number exists to prevent

Permissions: System Manager + Sales Manager full; `POSNext Cashier` read/create/write.

### New: `ecs_posnext/api/table_sessions.py`

| Endpoint | Purpose |
|---|---|
| `get_tables` | Tables + an `occupied` flag and open-session info, in **one** extra query (not per-table) |
| `start_table_session` | Opens a session, or **resumes** the table's existing open one (updating head count) |
| `update_table_session` | Change table and/or guest count mid-order — backs the header chip |
| `close_table_session` | Called after a sale lands; frees the table |
| `cancel_table_session` | Called when the cart is cleared, so an abandoned order doesn't leave a table falsely occupied |
| `get_open_table_sessions`, `get_table_session` | Listing / re-hydration |

`start_table_session` resumes rather than throwing: picking an occupied table is a normal way for
a cashier to get back to that table's bill.

### POS Settings: new `require_table_and_guests`

- `pos_settings.json` — new "Table Service" section + Check field (default `0`, so **existing
  profiles are unaffected**)
- `api/constants.py` — added to **both** `POS_SETTINGS_FIELDS` and `DEFAULT_POS_SETTINGS`.
  This matters: `bootstrap.py` fetches settings through that field whitelist and the frontend
  store **prefers bootstrap over the API call**, so omitting it there would silently
  break the setting on startup. Verified through all three read paths.
- `POSSettings.vue` — checkbox in Sales Operations

### Frontend

| File | Change |
|---|---|
| `components/sale/TableGuestsDialog.vue` | **New.** Table search + guest counter with quick picks (1/2/4/6/8/10). Shows "Occupied" badges, warns when over seating capacity, and pre-fills capacity as the likely head count |
| `composables/useInvoice.js` | New `guestCount` / `tableSession` state + `setGuestCount` / `setTableSession`; both reset in `resetInvoice()` and `clearCart()` |
| `stores/posCart.js` | Wired the above through the store's public API |
| `stores/posSettings.js` | `require_table_and_guests` in state + `resetSettings`, `requireTableAndGuests` computed |
| `stores/posDrafts.js` | Drafts persist `guest_count` + `table_session` |
| `components/pos/POSHeader.vue` | New `showTableInfo` / `tableNumber` / `guestCount` props + `table-click` emit; renders a chip — emerald when seated, pulsing amber "Select Table" when not |
| `pages/POSSale.vue` | The gate: `tableServiceEnabled` / `needsTableSession` computeds, an `immediate` watcher that opens the dialog once shift + settings are ready, a guard at the top of `handleItemSelected`, session close/cancel wiring, and draft save/restore |

---

## Technical Details

**The gate.** `needsTableSession = requireTableAndGuests && !cartStore.tableSession`. While true the
items grid is hidden behind the "Select Table" panel (see below). `handleItemSelected` also guards
independently, which catches barcode scans from the still-mounted selector.

**Session lifecycle.**

```
gate → start_table_session → items → payment → close_table_session → gate reopens
                                   ↘ clear cart → cancel_table_session → table freed
                                   ↘ hold      → session stays Open, travels with the draft
```

Holding deliberately keeps the session `Open` — the table *is* still occupied until the bill is
settled. Resuming a held order re-attaches its session, and picking an occupied table auto-resumes
its draft via `resumeDraftForTable()`.

`sessionToClose` is captured **before** `clearCart()` in `handlePaymentCompleted`, because
`clearCart()` resets the cart's session reference. Both the online and offline success paths close
it; the offline path passes no invoice name since none exists yet. Close/cancel failures are logged
and swallowed — the invoice is already submitted by that point and must not be failed over
bookkeeping.

**Where the gate lives (revised twice).** The first design opened `TableGuestsDialog` automatically
and tried to lock it. That was wrong in the end: after a **Hold**, `performSaveDraft()` calls
`clearCart()`, which resets `tableSession`, which re-triggered the gate — so the cashier was trapped
in a locked modal and could not reach the held order they had just created. Reported directly:
*"when make hold i can't click draft invoice and etc"*.

The gate now lives in the **items panel** instead. While `needsTableSession` holds, `ItemsSelector`
is hidden (`v-show`) and replaced by a "Select Table" panel carrying the primary button plus a
shortcut to held orders. Everything else — drafts, invoice management, sidebar, header chip — stays
live, so there is nothing to be trapped behind. The dialog is now freely dismissable; cancelling
lands back on the panel, which is itself the gate.

**Revised a third time — the `v-show` never worked.** Reported as *"dialog table should mandatory
before select items"*, with the suggestion to put the dialog in the item selector instead. Both
halves were right.

`ItemsSelector.vue` has **three root nodes** (the main div, a `Teleport`, and
`WarehouseAvailabilityDialog`), making it a fragment component. Vue cannot apply a directive to a
fragment — it logs *"Runtime directive used on component with non-element root node"* and does
nothing. So `<ItemsSelector v-show="!needsTableSession">` in `POSSale.vue` **silently had no
effect** and the items grid stayed visible the whole time. Only the `handleItemSelected` guard was
holding the line, which blocked the add but left the UI looking ungated.

Proven with a vitest case rather than assumed: `v-show="false"` hides a single-root component but
leaves a three-root one fully visible, with Vue's warning captured.

The gate therefore moved **into `ItemsSelector`**, which is what the request asked for and is also
the only place it can work — inside the component the overlay sits on a real element:

- an opaque `absolute inset-0` overlay on the component's own root (`z-[10000]`, above the
  `z-[9999]` sort dropdown inside it)
- `TableGuestsDialog` mounted there and **auto-opened** when gated, so the choice is unavoidable
  rather than a button that can be missed
- the `item-selected` emit guarded at source, for the still-live barcode scanner
- confirmation **emitted up** to `POSSale`'s existing `handleTableGuestsConfirmed` rather than
  writing to the cart from the selector: the parent owns the session lifecycle (offline seating,
  resuming held orders, settling) and a second source of truth there would drift
- `openTableDialog()` exposed so the header chip still edits table/guests through the one instance

Auto-opening is safe now in a way it was not for the modal-gate design: the dialog is dismissable
and the overlay behind it is the gate, so dismissing leaves the cashier on the panel with the
sidebar, cart and held orders all reachable.

The `v-show` note below is kept for the record, but it was never doing anything: `ItemsSelector` keeps its grid and scroll state across
orders instead of re-mounting on every table change. The side effect is that its barcode scanner
stays live while gated, which is exactly what the `handleItemSelected` guard is there to catch.

The locking machinery below was removed along with the modal gate; it is recorded because the
frappe-ui finding is worth knowing.

**Why locking a frappe-ui Dialog is hard.** The first pass used `:dismissable="false"`, copying the
pattern already in `POSSale.vue` and `Home.vue`. **That prop does not exist on frappe-ui's `Dialog`**
— it accepts only `options` and `disableOutsideClickToClose`, so the attribute was inert. The gate
had three open escape hatches:

1. an X button rendered unconditionally in the Dialog's default `body-header`
2. `@escape-key-down="close()"` — hardwired, and *not* covered by `disableOutsideClickToClose`
3. backdrop click

Locking it required overriding the `body-header` slot (to control the close button), passing
`disableOutsideClickToClose`, and guarding the `v-model` setter — the setter being the only reliable
block for Escape. That guard then broke the success path: after `confirm()`, `props.isRequired` is
still `true` (props refresh only on the parent's next render flush), so the guard refused the close
and trapped the dialog open. All of this is gone now that the panel is the gate — a good sign the
modal was the wrong place for it.

Note: the two pre-existing `:dismissable` usages (`POSSale.vue:771`, `Home.vue:170`, both on logout
dialogs) are equally inert. Left alone — changing them would alter existing UX beyond this request.

**Safety valve.** If the `Table` doctype has no records, a required gate would lock the cashier out
of the POS entirely. `hasNoTables` (distinguishing "nothing configured" from "search came up
empty") makes the dialog dismissable and shows an explanatory notice instead.

**Link consistency.** `Table.autoname = field:table_number`, so `name == table_number`. The value
stored is therefore valid both for the header chip and for `Sales Invoice.table` (Link → Table).
Verified.

---

## Verification

Ran against `royal.erpnext.cloud` (POS Profile "Buffet", 12 existing `Table` records):

- `bench migrate` — doctype created, DB table present, POS Settings field present
- API end-to-end: start → resume-with-head-count-update → `occupied` flags → update → close →
  table free again
- Guards: `guest_count = 0` → ValidationError; non-existent table → ValidationError;
  direct duplicate `Open` session insert → ValidationError
- Concurrency: cashier B picking cashier A's table receives **A's session**, not a second one
- Setting reaches the frontend through all three read paths (doctype `*`, bootstrap whitelist,
  `api/pos_profile`), defaulting to `0`
- `yarn build` clean; `bench build --app ecs_posnext` clean

`yarn biome check` **crashed** on `POSSale.vue` — a Biome bug (`biome_text_size/src/range.rs:66`,
`assertion failed: start.raw <= end.raw`), not a code error. The one lint finding it surfaced
(`useConst` at `POSSale.vue:1045`) is pre-existing code, untouched by this session.

Diff is purely additive: **280 insertions, 0 deletions** across 9 files, plus 3 new files.

---

## Note on Git

Commit `ad7fc0a "Before new updates"` landed mid-session (from outside this session), committing
the item-group pagination work that was in flight. Nothing was lost; this session's changes sit on
top of it, uncommitted.

---

## Follow-up Items

- [ ] Protel push — post the order and store the returned reference in `external_reference`
- [ ] Decide whether closed sessions need a report (covers per shift, average head count)
- [ ] Offline behaviour: `start_table_session` is an online call, so the gate currently requires
      connectivity. Queue it in the offline worker if table service must survive a network drop
- [ ] Consider a stale-session sweeper — a session left `Open` across a shift close keeps its table
      occupied indefinitely
