# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **POS Profile Setting to Stop Issuing Stock with Sales**
  - New **Create Stock Entry with POS Sales** checkbox on POS Profile, on by default so nothing changes for a profile that does not ask. With it off the POS records the sale as a Sales Order alone and creates no Material Issue
  - Gated in one place — `_submitStockEntry` in the cart store — so all four paths that used to issue stock honour it: the ordinary customer sale, the employee cash sale, the employee Loan and the employee Benefits handout
  - A profile saved before the field existed still issues stock, rather than silently stopping because the setting reads as undefined
  - **A Sales Order moves no stock by itself.** With this off, a sale never reduces the balance — the stock has to be issued some other way
- **Employee Benefits Follows the Profile's Stock Setting**
  - A Benefits handout obeys **Create Stock Entry with POS Sales** like every other path: with it off nothing here moves stock, and the handout is recorded by its Sales Order alone
  - Where a profile does issue stock, the Material Issue is still made **before** the Sales Order — so goods are never recorded as handed out without the movement behind them — and the two are cross-linked
  - The success dialog names whichever document was actually created
  - Confirmed against the floor's own orders rather than a contrived one: `SAL-ORD-2026-00182` (825.00) and `SAL-ORD-2026-00179` (565.00) both carry their employee and the `Benefits` tag, and have **zero rows in Protel** — neither in the permanent ledger nor on any folio
- **Employee Benefits Recorded as a Sales Order, Kept Out of Protel**
  - The Benefits handout had no Sales Order of its own: issuing stock *was* the whole flow. On a profile that does not issue stock it would have recorded nothing at all, so it now books a Sales Order against the fixed "Employee" customer, tagged `Benefits`
  - `is_protel_sale` in the `royal` app keeps a Benefits order out of Protel entirely — it is stock handed to staff, not a guest charge or hotel revenue, so it belongs on neither a folio nor the hotel's books
  - The same guard covers the submit hook, the cancel hook (nothing was posted, so there is nothing to void) and `validate_protel_operator`, which no longer demands a Protel Operator for a sale that never reaches Protel
  - The success dialog names what was actually created, rather than announcing a Stock Entry that no longer exists
- **Tax and After-Tax Price in POS Sales Detail**
  - Detail rows gain **Rate with Tax**, **Tax** and **Amount with Tax** beside the figures they already showed; grouped rows gain **Avg Rate with Tax**, **Tax** and **Amount with Tax**
  - The report summary now separates **Items Total**, **Tax** and **Items Total with Tax**
  - Tax is charged on the order as a whole — one rate on its net total — so there is no per-item figure to read. Each line is given its share in proportion to what it contributed, and the last line of an order absorbs the rounding, so the Tax column adds up to the tax actually charged rather than a cent more or less
  - A line's share is measured against the whole order even when a filter holds only part of it, so narrowing the report never changes what a line is carrying
  - Verified against every submitted order: allocated tax matches charged tax order by order, and all six groupings agree on amount, tax and amount with tax
- **Supervisor Password for Edits to an Open Check**
  - Two new POS Profile fields under **Check Edit Protection**: a checkbox to turn it on and the password itself. Off by default, so nothing changes for a profile that does not want it
  - While a table is open, the password is asked before **reducing a quantity**, **removing an item**, **clearing the check**, **discounting it** or **lowering a line's price**. Adding items is never gated, and a sale with no table open is not gated either
  - Cancelling a check or freeing a table that has an order always asks, table or no table — there is no cart to judge it by
  - The password **never reaches the browser**. It uses Frappe's `Password` fieldtype, so it lives in the `__Auth` table and the document carries a placeholder; on top of that the field is dropped from the POS Profile payload outright. The POS learns only that a password is required, and sends each attempt to `verify_check_edit_password` to be judged on the server
  - Compared with `hmac.compare_digest`, and five wrong attempts lock that cashier out of the check for five minutes. Only failures count, so a busy shift making many legitimate edits is never throttled. A correct password during a lockout is still refused
  - A lost connection or a lockout **refuses** the edit rather than waving it through — an approval that cannot be checked is not an approval
  - Once a line is approved the cashier can keep correcting it without the dialog reappearing; the quantity box emits on every keystroke, and repeated asks about the same line share one answer instead of each cancelling the last. Approvals are forgotten when the cart moves to another check
  - Protection on with no password set allows the edit and logs the misconfiguration, rather than leaving the floor unable to correct a check at all. The field is mandatory when the checkbox is ticked, so this only happens if the row is edited directly
- **POS Sales Detail Report**
  - New Script Report answering what the POS sold, broken down by **item**, **item group** or **room**, and by **which shift sold it**
  - Group By switches the whole report between Item, Item Group, Room, Shift, Item Group + Item, Room + Item, and Detail (one row per sold line, with its order, shift, cashier, room and customer)
  - Every grouping carries quantity, average rate, amount and a count of distinct orders; the report summary adds the items total, the orders' grand total **including tax**, total quantity and how many distinct items sold
  - Filters: company, date range, POS Profile, shift, cashier, room, item group, item and customer. The shift picker narrows to the chosen profile
  - Built on **Sales Orders**, not Sales Invoices, because that is what this POS submits — a report over invoices would be empty. A POS sale is recognised by the shift stamped on it or the Stock Entry it issued stock through, so back-office Sales Orders stay out
  - Split checks charged room by room are read at line level (`Sales Order Item.room`) and fall back to the order's room, so a table split across two rooms reports against both
  - Where a row is keyed by item, its group is named from the **Item master** rather than the sold line: the line stores the group the item had when sold, so an item recategorised since would have its whole history labelled with whichever group came first. Grouping *by* item group still reads the line, which is the historical truth
  - A grouped row leaves the UOM blank when the item sold in more than one unit, rather than printing one unit over a summed quantity
  - Sales with no room are labelled "Walk-in" and sales predating the shift field "No shift recorded" — both are counted, and neither leaves an empty cell to interpret
  - Reachable from a new **Reports** card on the POSNext workspace. Open to System Manager, Sales Manager, Accounts Manager and Stock Manager
- **Table & Guest Count Required Before Item Selection (Table Service)**
  - New `POS Table Session` doctype records the table and number of guests for an order, independent of any Sales Invoice — the sale may be posted to an external system (e.g. Protel) rather than persisted locally
  - New `require_table_and_guests` POS Setting ("Table Service" section) gates the POS: with it on, the cashier must pick a table and enter the guest count before any item can enter the cart. Default off, so retail / take-away profiles are unaffected
  - New `TableGuestsDialog.vue` — table search with "Occupied" indicators, guest counter with quick picks, seating-capacity warning
  - Table and guest count shown as a chip in the POS header, clickable to change either at any time mid-order
  - Only one open session per table, so two cashiers cannot build separate orders for the same table; picking an occupied table resumes its session and its held draft instead
  - Sessions close automatically when the sale completes (freeing the table) and are cancelled when the cart is cleared; held orders keep their session open and carry it in the draft
  - New API module `ecs_posnext.api.table_sessions` — `get_tables`, `start_table_session`, `update_table_session`, `close_table_session`, `cancel_table_session`, `get_open_table_sessions`, `get_table_session`
  - `external_reference` field on the session as the hook for the external system's reference (the Protel push itself is not yet implemented)
  - The gate lives inside `ItemsSelector`, alongside the item selection it gates: an opaque overlay on that component's own root element replaces the grid with a "Select Table" panel, and the table dialog is mounted and auto-opened there. Fixes a real hole — `ItemsSelector` has three root nodes, so the previous `v-show` on the component from `POSSale.vue` was applied to a fragment and silently did nothing (Vue warns "non-element root node"), leaving the items grid visible while the gate was supposedly up
  - `ItemsSelector` also guards its own `item-selected` emit, which is what stops a barcode scan from adding an item while the gate is showing
  - The dialog is freely dismissable; cancelling lands back on the gate overlay, which is itself the gate. Held orders, invoice management, the sidebar and header all stay reachable, which matters right after a Hold when the cart is cleared and no table is set
  - The header chip changes table/guests mid-order through `ItemsSelector`'s exposed `openTableDialog()`, so there is a single dialog instance
- **Open Tables Dashboard with Idle Colour Coding**
  - New `POS Table Order` doctype (with `POS Table Order Item` child table) holds a table's order on the server, so a manager screen or a second terminal sees the true state of the floor. Held orders were previously browser-only (IndexedDB), invisible to everyone else
  - `cart_payload` on the order stores the full POS cart, so resuming brings back offers, batches, serials and UOM pricing exactly; the items child table is the readable projection used by the dashboard and reports
  - New **Open Tables** dashboard in the POS sidebar (table-service profiles only): live cards per table showing guests, item count, open total, seated time and time since the last order, worst-first. Tap a card to take or resume that table's order
  - Tables colour by how long they have gone **without ordering** — amber past `table_idle_warning_minutes`, red past `table_idle_late_minutes`, both new POS Settings. Measured from the last order, falling back to seating time while nothing has been ordered
  - Timers tick locally between 30-second server refreshes, and cards re-evaluate their colour band live so a table crosses into amber or red without waiting for the next fetch
  - New **Open Tables** Script Report for the Desk (filters by POS Profile / status / nothing-ordered, coloured status column, donut chart, summary tiles, optional 30s auto-refresh), plus a "Table Service" card on the POSNext workspace
  - Holding a table-service order now writes to the server; offline still falls back to the local draft, and the gate panel links to the dashboard for server-held orders and to the drafts dialog for offline ones
  - Settling or clearing a table settles/cancels its order alongside the session, so a freed table can never leave an open order behind on the dashboard

### Fixed
- **Employee Benefits Issue Did Nothing**
  - Pressing Benefits produced no document at all. The flow raised `isSubmitting` and then called the submit, which **refuses to run while that flag is set** — it logged "already in progress, skipping duplicate request" and returned null. Nothing was created and nothing said why
  - The flag is now left to the submit itself, which raises and clears it around its own request
  - The employee was also being dropped: the order takes its employee from an argument, never from `selectedEmployee` — deliberately, so a plain customer sale cannot pick up whoever was left attached — and this flow was not passing one. Benefits orders recorded the customer "Employee" with no employee on them, so nothing said who received the handout
  - **The Loan flow had the same two defects.** It survived while stock issuing was on, because the Stock Entry call cleared the flag on its way out; once a profile stopped issuing stock that call returns immediately and the flag stayed up, blocking the Loan's Sales Order
  - Covered by tests driving the real store: the draft is created, carries `pos_sale_type` (`Benefits` / `Loan`) and the employee, is booked against the Employee customer as a Sales Order, and is refused outright when no employee is chosen
  - The tag matters beyond bookkeeping: `Benefits` is what keeps the handout out of Protel, and no order in the system had ever carried one
- **Protel Charges Went to the Wrong Guest, or to Nobody** (`royal`)
  - `resolve_room_guest` accepted any *confirmed* booking (`resstatus = 100`) and preferred the one starting latest. A guest arriving today therefore outranked the guest sitting in the room: `SAL-ORD-2026-00116` put room 510's water on Nadia louati — arriving, room **216** — instead of Mohamed Ibrahim, who was in 510
  - It now requires `buchstatus = 1`, Protel's "checked in", the same rule that already governs which rooms the POS offers. The date ordering survives as a tie-break, so a room changing hands the same day charges the guest who has just arrived
  - Verified against all **45 occupied rooms**: the resolver now agrees with Protel on every one, and room 510 resolves to Mohamed Ibrahim. Rooms holding only a not-yet-arrived booking (507, 205, 305) resolve to nobody, as they should
  - **A sale with no guest to charge is no longer posted at all.** It used to go in with `kundennr = 0` and an empty room, which lands in the ledger belonging to nobody: invisible on every folio and every room history, so no one is ever billed and no one can find it to correct. There are **50 such rows in Protel, 5,105.00 EGP**. The sale is now left visibly unsynced with the reason on `protel_sync_error`, which is a state someone can act on
  - This also stops a sale carrying neither a room nor an employee from posting — which is most of the "Employee" customer sales. They were the bulk of those orphan rows
- **Checkout Now Frees the Table**
  - Paying a check left the table occupied. `submit_invoice` settles the check and closes the table in the same call that submits the sale, reading `pos_table_session` back off the document — but **Sales Order had no such field**, so the value the POS sent was dropped on save and that read always came back empty
  - Added `pos_table_session` and `pos_table_order` to Sales Order. The same failure as `v1_17_0`: the POS described what it was doing and the document had nowhere to put it
  - `pos_table_order` matters on a split table, where settling "the" order is ambiguous and the server refuses to guess
  - Verified end to end through the POS's own two calls — seat a table, ring up a sale, submit it — and the session comes back **Closed** with `closed_at` set, without a follow-up request from the browser
  - Until now no session had ever reached `Closed`: all 24 in the system were `Cancelled`, i.e. freed by hand from Open Tables after each checkout failed to do it
- **Tax Missing from POS Sales Orders**
  - The POS showed the cashier a tax figure and then submitted an order without it. The payload it sends carries no `taxes` and no `taxes_and_charges` at all: a Sales Invoice still picked the template up because ERPNext reads `pos_profile` off the document, but **Sales Order has no such field**, so every order was saved with its grand total short by exactly the tax on screen
  - `update_invoice` now puts the POS Profile's tax template on the document before totals are worked out — the same template the POS previews through `pos_profile.get_taxes`, so the figure quoted and the figure recorded come from one source
  - Taxes already on the document win, so a return, or a re-save of something priced earlier, is not re-templated underneath
  - ERPNext computes the amounts from the template rather than the browser, so the account head, rate and cost centre are its own. A line that previously landed with `rate: 0` and a hand-computed amount now carries the real 14% row against `VAT 14% - RR`
  - Whether the price already includes the tax follows this profile's **`tax_inclusive` POS Setting**, not the template. The POS reads that same setting to decide what to show and whether to send a gross or a net rate, so a template that disagreed would put the screen and the document on different arithmetic — the one thing this is here to prevent. Note that POS Settings is one record per profile here, not a Single
  - Inclusive: the POS sends the gross rate and the tax rows are marked `included_in_print_rate`, so ERPNext takes the tax out of that rate instead of adding it again on top. Exclusive: the rate is net and the tax goes above it
  - Verified by creating orders through the POS's own entry point in both modes: ten units quoted at 45.60 inclusive and ten at 40.00 exclusive both land on a grand total of 456.00 — net 400.00 plus 56.00 tax — matching what the cashier was shown either way
- **Close Shift Figures on a Sales Order POS**
  - The closing screen showed **"No Sales During This Shift"** next to a non-zero sales total, and hid the transaction list entirely. Both are driven by `pos_transactions`, which was only ever filled from Sales Invoices — this POS submits Sales Orders, so the list was always empty
  - Sales Orders now produce a transaction row each, so the cashier can see the sales making up the total. The rows carry `sales_order` and are display-only: the saved child table's link field points at Sales Invoice and would reject them, and `submit_closing_shift` strips them on the way back so a round-trip cannot fail the save
  - **Tax Collected read 0.00** on every shift: taxes were aggregated from invoices only. Sales Order taxes are now aggregated too (one shift here was under-reporting 49.11 of VAT)
  - **Expected cash looked wrong with no way to tell why.** A sale charged to a room goes onto the guest's folio in Protel, and an employee Benefits/Loan sale is not paid at the counter, so neither adds to the drawer — but the screen showed gross sales of 479.91 against expected cash of 100.00 and said nothing. A **Charged to Rooms** figure now states the difference, and each transaction row is tagged with its room or "Not collected"
  - Verified against three real shifts: gross 280.00 − charged 200.00 = expected 80.00 over opening; gross 479.91 − charged 479.91 = opening only; gross 240.00 − charged 240.00 = 0.00
  - `_is_drawer_money` was whitelisted, exposing an endpoint nothing calls. It is an internal helper taking a dict, so the decorator is gone
- **Invoice History Shows Sales Orders**
  - The history list queried Sales Invoices only, so it was empty: this POS submits Sales Orders. It now returns **both**, newest first, so a profile that does create invoices keeps its history
  - Sales Order rows are mapped onto the shape the list already renders — the time from `creation` (Sales Order has no `posting_time`), and `paid_amount` / `outstanding_amount` derived from the `posa_payments` breakdown now recorded on each order
  - Scoped through the shift, because **Sales Order has no `pos_profile` column** (Sales Invoice does). Orders predating the new shift field carry no shift and are left out — there is nothing to attribute them to
  - `get_invoice` takes an optional `doctype` and otherwise detects it, so opening a row works for either kind and older callers passing only a name still work
  - Sales Orders are reported as non-returns: the return flow operates on invoices, and marking them otherwise would offer a return that cannot run
  - **The history dialog never reached that endpoint.** `InvoiceHistoryDialog` queried `frappe.client.get_list` on Sales Invoice directly, so the list stayed empty however the API behaved. It now reads `ecs_posnext.api.invoices.get_invoices`, and a Sales Order row carries a badge saying so
  - "Load more" re-reads the list one page wider instead of paging by offset: the endpoint merges two doctypes before trimming, so an offset would skip or repeat rows across the join
  - Reopening the dialog resets to the first page, so it does not silently re-fetch a slice widened earlier in the session
  - The return button is hidden on Sales Order rows, matching the endpoint's own position that they cannot be returned
  - Printing carries the doctype through: `printWithSilentFallback` passes it to the thermal-print call, which was hardcoded to Sales Invoice. Every POS sale is a Sales Order, so silent printing had been failing on each one and quietly falling back to the browser print dialog

- **Shift Closing Now Totals the Money** *(Close Shift no longer reports zero)*
  - The POS has always sent `posa_pos_opening_shift` **and** the per-mode payment breakdown with every sale. Sales Order had neither field, so both were silently dropped on arrival — the money was collected, described, sent, and thrown away. That, not a reporting bug, is why every shift closed at zero
  - New `POS Order Payment` child table plus two Sales Order custom fields (`posa_pos_opening_shift`, `posa_payments`), added by patch `v1_17_0` and shipped in fixtures
  - `make_closing_shift_from_opening` aggregates the shift's submitted Sales Orders alongside the existing Sales Invoice and Payment Entry sources, so profiles that do create invoices are unaffected
  - **Room charges and employee Benefits/Loan sales count as sales but not as drawer money.** A room charge goes to the guest's folio in Protel and is never collected at the counter; counting it as cash would show a shortage on every shift exactly equal to the room postings
  - Verified end to end: four orders totalling 380 (100 cash + 50 cash + 200 room charge + 30 employee benefit) report **380 sold** and **150 expected in the drawer**
  - No change to the POS Closing Shift doctype or the closing dialog — both already had the right shape; only the source of `expected_amount` changed

- **Tables Sort by Number**
  - The Open Tables screen now orders every card by table number, numerically (1, 2, 10, 20 — not 1, 10, 2, 20), regardless of state. A table sits where the cashier expects it on the floor, and stops moving between refreshes as its idle time changes
  - Urgency is still carried by the card colour and the Waiting/Late counts in the summary strip, which is what the previous worst-first ordering conveyed

- **A Table Now Closes Only on Checkout**
  - Closing moved into the **same server call that submits the sale**. It used to depend on a separate request from the browser afterwards, which could be missed — a dropped connection, a closed tab, any early return in the payment handler — leaving the table occupied with its bill already paid. The follow-up call remains as an idempotent fallback
  - Clearing the cart **no longer frees the table**. It emptied the items and released the table, but the guests are still sitting there, so the floor showed it as available while it was occupied. The cart now keeps its table, so the cashier carries on ordering for the same one
  - New **Free table** action on the Open Tables screen — the deliberate escape hatch for a mistaken seating or guests who left without ordering. It confirms first, naming the unpaid amount it would discard
  - A split bill still stays open until the last check is paid
  - Settle/close failures now warn the cashier instead of going only to the browser console

- **Customers No Longer Cached in IndexedDB**
  - The whole customer list was downloaded at startup and mirrored into IndexedDB so it could be searched in the browser. With searching now done on the server that copy was pure cost — a slow first load, and a second source of truth that went stale the moment anyone edited a customer elsewhere
  - `loadAllCustomers` fetches a bounded first page (50) for the pre-search list instead of `limit: 0` meaning *every* customer; the background "Loading customers for offline use..." sync is gone entirely
  - A newly created customer is still pickable immediately — held in memory — and realtime removals drop out of both the list and the current search results
  - **Deliberate trade: there is no customer list while offline.** The store returns an empty list and logs it, rather than showing a stale one. Item caching for offline is untouched

- **Customer Search Is Now Server-Side**
  - `get_customers` accepted a `search_term`, logged it, and then **never used it** — the query was built from the POS Profile's customer groups alone. Searching returned the same rows as not searching, which is why the POS had to download every customer and filter them in the browser
  - The term now matches customer ID, name, mobile and email on the server, combined with the profile's customer-group filter rather than replacing it
  - The POS searches the server, debounced at 250ms, instead of scanning the full in-memory list: typing five characters makes one request, not five. The existing local ranking still orders the returned page, so result quality is unchanged while the full list is never loaded
  - Out-of-order responses are discarded by sequence number, so a slow early request cannot overwrite a newer one's results
  - Offline still searches the IndexedDB cache, and a failed search falls back to what is already in memory rather than showing an empty list

- **Room Search Now Queries Protel Live** *(in the `royal` app)*
  - New `search_in_house_rooms` endpoint asks Protel at the moment the cashier types, instead of reading the `Room.is_active` flag that only refreshes every 15 minutes. That lag was wrong in both directions: a guest who had just checked in could not be charged, and one who had just checked out still could
  - Guest names come back with the rooms and show beside the number ("205 · Dhekra Alsabri"), so the waiter can check it against the person in front of them. Search matches the room number **or** the guest's name
  - A Protel outage never blocks the POS: the search falls back to the last synced list and the dropdown says so, matching how the Protel posting already refuses to fail a checkout
  - Rooms returned live are created as Room records on the fly, since `Sales Invoice.room` and the POS table order both Link to Room — a room Protel knows about is unusable until that record exists
  - Pseudo-accounts (`PASS`, `99999`) are filtered out of both the live results and the auto-creation

- **Room List Now Matches Protel's "Guest in House"** *(fix is in the `royal` app)*
  - `sync_active_rooms` counted `buchstatus IN (0, 1)` — confirmed-but-not-yet-arrived **and** checked-in. Seven empty rooms were being offered to cashiers, who could charge a restaurant sale to a guest not yet in the hotel. Now `buchstatus = 1` only, which is exactly what Protel's Guest in House page shows
  - The sync now **creates** Room records for occupied Protel rooms that have none. Protel holds 167 rooms against ERPNext's 65, and a room with no Room record can never be charged — the POS simply never offers it, so a guest demonstrably in the hotel could not order. Five in-house rooms (9000, 9002, 9004, 9011, 9013) were in exactly that state
  - Only numeric, currently-occupied rooms are created, so Protel's pseudo-accounts (`PASS`, `99999`) stay out of the cashier's dropdown
  - The four POS room dropdowns already filtered `is_active = 1` and were unchanged; the defect was entirely in what that flag meant

### Added
- **The Open Tables Screen Is Now the Table Picker**
  - The "Select Table" gate opens the Open Tables screen instead of a separate dialog, so the cashier sees the whole floor — free tables to seat and busy ones to go back to — on one screen
  - `get_open_tables` gained `include_free`, returning unoccupied tables in the **same row shape** (`seated: 0`, `idle_state: "free"`) so a single card renders both. The default call is unchanged, so the manager dashboard still shows only what is actually open
  - Guest count is taken **inline on the free table's own card** — counter plus quick picks — rather than opening a second dialog on top of the first. Capacity prefills it, since it is the likeliest head count
  - Free tables sort last and numerically (4 before 10), and are excluded from the summary strip: they are choices, not activity, and counting them would make every figure on the strip wrong
  - Seating works offline, creating the local session and syncing later, exactly as the old dialog did
  - The small table dialog stays for editing the table or guest count of an order already in progress, where the rest of the floor is irrelevant

- **Held-Orders Button Opens Table Orders on a Table-Service Profile**
  - The cart's "Draft Invoices" button (and the same entry in the header menu) now opens the open-tables view instead of the local drafts dialog when `require_table_and_guests` is on. Table-service holds are server-side table orders, so the drafts dialog would have looked empty
  - Both are relabelled "Table Orders" in that mode, and the local-drafts count badge is hidden there since it only ever reflects offline holds
  - Retail / take-away profiles are unchanged, and the gate panel keeps its separate "Offline held orders (N)" shortcut to the local drafts

- **Separate Checks (Split a Bill by Item, Each Charged to Its Own Room)**
  - New `split_table_order` endpoint and a Split Check screen: the cashier assigns each item to a check, and every check becomes its own `POS Table Order` with its own `check_number`, `room` and `external_reference` — so each one can be posted to a different hotel room separately
  - A split must reconcile **exactly**: every unit of every line has to land on one check. Unassigned items, over-assignment, fewer than two checks, an empty check, and re-splitting an existing check are all refused with specific messages. Rates come from the source order, never the client, so a split cannot reprice
  - Each check is paid on its own. Settling one reports `remaining_open_checks`, and the table stays open (and visible on the dashboard) until every check is paid — `close_table_session` now refuses to free a table that still owes money
  - New `set_check_room` lets a check's room be corrected while it is still open, and refuses once it is settled
  - `POS Table Order Item.added_by` is carried onto the split checks, so the waiter who rang each line survives the split
  - **Fixes 8 latent bugs**: the table-service code assumed exactly one open order per session. Once split, `save_table_order`, `settle_table_order`/`get_table_order` by session, and re-splitting all now **refuse rather than pick an arbitrary check** (which would have put items or a payment on the wrong guest); cancelling a table releases *every* check; moving a table moves *all* of its checks; and the dashboard aggregates totals across checks instead of reporting one
  - Joining tables is refused when either side is split — which of several checks to fold into is genuinely ambiguous
  - Dashboard cards show "N separate checks" with the rooms, and a Checks screen lists each check with its items, room, paid state and a Pay button

- **Move an Open Order Between Tables (and Join Tables)**
  - New `move_table_session` endpoint plus a "Move" action on every tables-dashboard card: pick a destination and the order moves with it
  - **Fixes a data bug**: changing a session's table (which the header chip already allowed) updated only the session, leaving `POS Table Order.table` pointing at the table the guests had left — the dashboard read correctly while the order record disagreed. Both the new move endpoint and `update_table_session` now move the order with the session
  - Moving onto an occupied table changes nothing by default and reports `status: "occupied"`. Combining two bills is a deliberate choice, so the dialog requires ticking "Join the tables and combine the bills" — previously the offline-conflict message told cashiers to "move this order to another table" with no way to do it
  - Joining tables folds the source order's lines into the destination's, adds the guest counts together, closes the source session and cancels its order, so the dashboard shows one table rather than two. Each line keeps the waiter who rang it across the merge
  - Every move and merge is recorded on the session's timeline with who did it
  - The open cart follows its own table: a move updates the cart's table, and a merge repoints the cart at the surviving session so items still in it are held onto the combined bill instead of a session that no longer exists

- **User Attribution on Table Service (for the Protel push)**
  - Every table-service record now carries the POS Next user who actually performed the action, so anything later pushed to an external system (Protel) can be attributed to them rather than to a service account
  - `POS Table Order Item.added_by` — attribution **per line**, since a table's rounds can be taken by different waiters and each movement must carry the user who rang it
  - `POS Table Order.cashier` is no longer overwritten on every save. It stays as the user who **opened** the order; the new `last_order_by` records who last added to it. Previously a second waiter adding a round erased the first waiter's attribution entirely
  - `synced_by` on both `POS Table Session` and `POS Table Order` — an order held offline by one user and uploaded from another terminal previously got credited to whoever's browser happened to sync it. The acting user is now sent with the sync and kept in `cashier`, with the uploader recorded separately so attribution stays auditable
  - A client-supplied user is only honoured on the offline-replay path, and only for a real, enabled User — otherwise it falls back to the uploading session. The online endpoints take the acting user from the server session and never from the request, so it cannot be spoofed
  - "Opened By" and "Last Order By" surfaced on the tables dashboard cards and as columns in the Open Tables report

- **Offline Table Service**
  - Tables can now be seated and held with no network. Previously the whole flow was online-only: both `get_tables` and `start_table_session` were plain server calls, so an offline cashier could not even list a table, let alone seat one
  - The table list is cached in `localStorage` on each successful fetch and used as the fallback when the server is unreachable. Occupancy flags are deliberately not cached, since a stale "Occupied" badge would be worse than none
  - A table seated offline gets a client-generated session id (`pos_offline_session_<uuid>`, distinct from the `pos_offline_<uuid>` used for offline invoices) and is created on the server later
  - New `sync_offline_table_order` and `promote_offline_session` endpoints, plus a unique `offline_id` on `POS Table Session`. Keyed on that id, so replaying a sync finds the existing session and order instead of duplicating them — enforced at the database level, not just in code
  - Offline seating and hold times are sent with the sync, so a synced table shows how long the guests have really been seated rather than appearing freshly served
  - Offline-held orders sync on reconnect (and on a normal online load, in case the browser was closed before an earlier reconnect could run), then the local draft is deleted so each order exists in exactly one place
  - If another cashier took the table while this terminal was offline, the sync reports a conflict and writes nothing: the local order is kept and the cashier is told, rather than silently splicing two parties' bills together
  - Coming online mid-order promotes the local session to a real one on the next hold, so nothing has to be re-entered
- **POS Customer Inline Entry in Payment Dialog**
  - Removed mandatory customer selection popup that blocked checkout when no customer was selected
  - Added Customer Name and Mobile Number fields inline in the Complete Payment dialog, above the Sales Person section
  - Both fields support live search: typing in either field queries existing customers by name or mobile number and shows a dropdown of matches
  - Selecting a customer from the dropdown fills both fields and enables a link icon to open the customer record in a new tab
  - If the entered customer name does not match any existing customer, a new Customer record is automatically created on Complete Payment
  - If a customer is already selected in the cart, the fields are pre-filled with their name and mobile number
  - Customer fields are required (with red validation styling) only when the cart has no customer and the POS profile has no default customer
  - All existing payment dialog functionality (sales persons, payment methods, write-off, etc.) is preserved

### Fixed
- **Item Price Validity Filters**
  - Added `valid_from` and `valid_upto` date filters to all Item Price queries across `get_items()`, `get_items_bulk()`, `get_item_variants()`, and `search_by_barcode()` functions
  - POS now displays only currently valid prices, excluding expired or future-dated prices
  - Ensures price list rates match ERPNext's validity period logic
  - Added `ORDER BY modified DESC` and fixed price selection logic to ensure the most recently updated price is returned when multiple valid prices exist for the same item/price list/UOM (prevents older prices from overwriting newer ones)

### Changed
- **Item Selector Opens on the Item Group Grid**
  - The item selector now opens on the item group card grid at root level instead of jumping straight to the flat item list
  - Typing a search or picking a group chip still goes straight to items; clearing the search returns to the grid
  - The "All" tab and the grid's "Back to items" link both step past the grid to the flat list
  - Falls through to the item list when the POS Profile exposes no item groups, so the grid can never be a dead end
- **PaymentDialog.vue UI Refinements**
  - Removed numeric keypad section from payment dialog (desktop view)
  - Moved Sales Person selection from left column to top of right column, above payment methods
  - Payment method buttons now directly add the remaining amount on click (no separate Add button needed)
- **DailyPaymentManagement.vue Default Filters**
  - `from_date` and `to_date` filters now default to today's date instead of empty values
- **Return Flow: Cancel-and-Recreate Pattern**
  - Replaced "Create Return" button with "Cancel & Amend" in ReturnInvoiceDialog.vue
  - Return process now cancels the original Sales Invoice instead of creating a separate `is_return=1` invoice
  - If items remain after a partial return, a new Sales Invoice is created with only the remaining items
  - New invoice is created with proportional payments copied from the original, making it auto-paid
  - Existing `create_payment_entry_on_submit` hook creates Payment Entries automatically for the new invoice

## [1.15.1] - 2026-04-26

### Added
- **Agent & AI Workflow Infrastructure**
  - Created `chat/` directory to maintain structured AI-assisted development session logs
  - Added `chat/chat_log.md` as the canonical session log for all AI development sessions
  - Established session logging protocol: date, participants, topics, decisions, file changes, outcomes
  - Updated `.clauderc` agent file with mandatory pre-session reading instructions (README, CHANGELOG, all chat logs)
  - Added `## 🤖 Agent & AI Workflow` section to README documenting the new workflow structure

## [1.15.0] - 2026-02-06

### Added
- **Customer Credit Balance as Payment Method**
  - New "Add to Customer Credit Balance" option in return dialog — cashiers can choose between cash refund or adding credit to customer balance
  - Customer credit payment method — use positive credit balance (from returns/advances) as payment
  - New `allow_customer_credit_payment` POS Setting to enable credit balance payments
  - Race condition protection using SELECT FOR UPDATE for concurrent credit redemption
  - Optimistic locking with modified timestamps to prevent stale credit usage
  - Return type indicators in Invoice Details: blue "Added to Customer Credit" vs green "Cash Refund"
  - Separated credit calculation: regular invoice outstanding (debt) vs return invoice credit, preventing double-counting

- **Shift Duration Improvements**
  - Timezone-safe shift duration calculation — server sends `server_now` timestamp, frontend computes elapsed time without timezone mismatch
  - Multi-day shift display with proper formatting (e.g., "2 Days 3 Hours 15 Minutes")
  - Full word time labels on desktop: Hours, Minutes, Seconds with proper singular/plural handling
  - Shift timer pauses automatically when closing dialog is open
  - Idle warning when shift closing dialog stays open for over 1 minute

- **Enhanced Mobile Payment UI**
  - Physical keyboard input support (0-9, decimal, backspace, Enter) for payment numpad
  - Consistent payment method layout across cash and non-cash payment types
  - Context-aware quick amounts: ceiling/rounded denominations for cash, exact fractional amounts for non-cash
  - Quick amounts always visible with proper disabled states

### Changed
- **Sidebar Navigation**
  - Settings button moved to bottom of sidebar for better visual hierarchy
  - Removed empty Dashboard and Reports placeholder components

- **Code Quality**
  - Centralized `DEFAULT_CURRENCY` and `DEFAULT_LOCALE` constants, eliminating hardcoded "USD" and "en-US" strings
  - Removed redundant credit sale check from `get_available_credit` API — fetching existing credit no longer requires credit sale to be enabled
  - Removed duplicate return success message (was showing twice from both dialog and parent)

### Fixed
- **Returns & Refunds**
  - Use `net_rate` for accurate return refund calculation, properly accounting for coupon and invoice-level discounts
  - Display customer name and posting date in return dialog
  - Calculate effective rate for refunds including taxes and discounts — customers refunded exactly what they paid

- **Monetary Calculations**
  - Use `roundCurrency` consistently across all payment, return, edit, and draft dialogs
  - 3-decimal precision (`round3`) for rate calculations preventing floating-point rounding discrepancies
  - Backend uses `flt(..., 3)` for rate calculations matching frontend precision
  - Fixed decimal precision issues causing incorrect "PARTIAL PAYMENT" status on fully paid invoices

- **Write-Off Feature**
  - Implemented write-off for small remaining payment amounts with visual toggle UI
  - Centralized currency rounding using Frappe's `flt()` as single source of truth

- **Invoice History**
  - Integrated ReturnInvoiceDialog directly into InvoiceHistoryDialog (no nested modals)
  - Fixed pagination — "Load More" button now correctly appends results
  - Changed invoice sorting from creation date to modified date
  - Added `canCreateReturn()` check to hide return button for fully returned invoices

- **Barcode**
  - Handle absent barcode UOM price with proper conversion factor calculation
  - Cache calculated prices for consistency across barcode operations

- **ERPNext v15/v16 Compatibility**
  - Support both `post_change_gl_entries` field locations (Accounts Settings vs Singles table)
  - Support both v15 `make_gle_for_change_amount()` and v16 `get_gle_for_change_amount()` methods
  - Convert `get_stock_availability` from SQL string to Query Builder for Frappe 16

- **Shift Timer**
  - Fixed negative shift duration (-1 Hours -60 Minutes) caused by timezone mismatch between server and browser

- **Translations**
  - Added Arabic, Indonesian, and Portuguese translations for all new features

## [1.14.0] - 2026-01-25

### Added
- **Frappe 16 Compatibility**
  - Converted SQL queries to Query Builder for full Frappe 16 support
  - Updated item filtering conditions using Query Builder patterns
  - Replaced pypika date functions with frappe.utils for date filtering

- **Enhanced Barcode Support**
  - Added POS Barcode Rules DocType for configurable barcode parsing
  - Integrated barcode rules into POS Settings for centralized management
  - Implemented resolved barcode handling for weighted and priced items
  - Auto-select UOM based on single barcode presence
  - Enhanced barcode resolution with POS profile settings integration
  - Warehouse availability now supports barcode UOM conversion

- **Offline Mode Enhancements**
  - Added offline support for invoice history and unpaid invoices
  - Cache batch/serial data for offline selection
  - Enhanced Return Invoice dialog with offline support and optimizations
  - Eager variant caching with offline verification
  - Disable clear cache button when offline mode is active

- **Sales Person Management**
  - Enhanced sales person selection with validation and dropdown support
  - Keep dropdown open for multiple sales person selection

- **Permissions & Roles**
  - Added new roles and permissions for system and sales managers
  - Correct POS Settings permissions with create for managers
  - Moved POSNext Cashier permissions from fixtures to DocType definitions

- **Payment Improvements**
  - Added exact amount mode for payment processing
  - Optimized payment queries for better performance
  - Added Arabic translations for payment dialog
  - Extract shared constants and add payment composables
  - Add toast queue system for better notification management

- **Localization**
  - Added Indonesian translations
  - Updated terminology and translations
  - Corrected CSV escaping and RTL toast positioning

- **POS Settings**
  - Added use_exact_amount field with validation

### Changed
- **Promotions UX**
  - Improved item selection UX with searchable dropdowns
  - Added clear all functionality for promotion items
  - Expanded template items to include variants in eligibility check

- **Code Quality**
  - Improved code quality with shared utilities and consistent patterns
  - Standardized pricing and submission functions across frontend and backend
  - Replaced console.warn with logger utility
  - Replaced silent exception handling with proper error logging

### Fixed
- **InvoiceCart**
  - Prevented event propagation on quantity buttons and input fields

- **Returns**
  - Use ERPNext make_sales_return for proper sales_team handling
  - Set update_outstanding_for_self=0 for proper credit note handling

- **Batch Display**
  - Show actual batch quantities instead of hardcoded 999

- **Offers**
  - Expanded template items to include variants in eligibility check

- **Permissions**
  - Preserve standard ERPNext role permissions in Custom DocPerm fixtures

- **Payment**
  - Added mutex protection to prevent duplicate invoice submissions

- **User Display**
  - Prevent undefined initials when name has trailing spaces

- **Localization**
  - Removed 'id' from default locales in get_allowed_locales_from_settings
  - Fixed RTL toast positioning

- **Info Toast**
  - Added info toast type for informational messages

### DevOps
- Added stale issue/PR automation workflow
- Added comprehensive issue templates
- Added .claude/settings.json to gitignore

## [1.13.0] - 2026-01-07

### Added
- **POSNext Cashier Role & Permissions**
  - Created dedicated POSNext Cashier role for POS operations
  - Added custom permissions for Customer, Bin, Item, and Warehouse doctypes
  - Proper role-based access control for POS users

- **Offline Invoice Sync Enhancement**
  - Added deduplication mechanism for offline invoice synchronization
  - Prevents duplicate invoice creation during sync recovery
  - Defensive type checks and mutex for concurrent sync operations

- **Return Invoice Improvements**
  - Added item search functionality in Return Invoice Dialog
  - Improved code quality and user experience for returns

- **Shift Closing Enhancement**
  - Return invoices now included in shift closing calculations
  - More accurate end-of-day reporting

### Changed
- **Offers & Promotions Optimization**
  - Optimized apply_offers with batch queries for better performance
  - Added dynamic debounce for offer application
  - Support for standalone pricing rules in apply_offers
  - Validate min_qty against eligible item quantity instead of total cart
  - Ensures offers fetched before processing in mobile view
  - Added offline support for promotions with mixed conditions

- **Cart & Payment Improvements**
  - Corrected subtotal display for tax-inclusive mode
  - Enhanced mobile responsiveness and dynamic sizing in PaymentDialog
  - Restored Hold Order button functionality

- **Internationalization**
  - Fixed translation API and added missing translations
  - Improved i18n coverage across the application

- **Build & Dependencies**
  - Updated frappe-ui imports to use proper exports
  - Improved build compatibility

### Fixed
- **Offers System**
  - Fixed min_qty validation to check eligible item quantity, not total cart
  - Fixed standalone pricing rules not being applied correctly
  - Fixed offers not being fetched before processing in mobile view

- **Cart Display**
  - Fixed subtotal display in tax-inclusive mode showing incorrect values

- **Offline Sync**
  - Added defensive type checks preventing sync errors
  - Added mutex to prevent concurrent sync race conditions

- **UI/UX**
  - Fixed Hold Order button missing from cart (regression fix)
  - Enhanced mobile responsiveness in PaymentDialog

## [1.12.0] - 2025-12-18

### Added
- **Wallet & Loyalty Program System**
  - Implement wallet functionality with loyalty points conversion
  - Auto-assignment of loyalty programs for new customers
  - Auto-assignment of loyalty program on sales invoice validation
  - Partial payment support for wallet/loyalty points redemption
  - Enable Loyalty Program as master switch in Wallet & Loyalty settings
  - Comprehensive technical documentation for Wallet System

- **Customer Search Enhancements**
  - Enhanced customer search with autocomplete functionality
  - Frequent customers display for quick selection
  - Optimized click handler for instant response on frequent customers

- **Sales Order Support in POS**
  - Sales order settings and store methods exposure
  - Delivery date selection integrated into payment flow
  - Delivery date dialogue for order scheduling
  - Dropdown menu for selecting between sales order and sales invoice

- **POS Profile Management**
  - Create, update, and delete POS profiles via API
  - Whitelist decorators for POS profile functions
  - Enforce user company association on profile creation
  - Enhanced parameter parsing for profile operations

- **Customer Management**
  - Edit customer functionality directly from cart

- **Payment Dialog Improvements**
  - Two-column layout redesign with invoice summary
  - Long-press payment with new composable
  - Dynamic sizing and responsive design adjustments
  - Enhanced credit balance and additional discount display
  - Improved mobile UX

- **Localization**
  - Configurable language settings
  - Brazilian Portuguese (pt-BR) support
  - RTL-friendly SelectInput component

- **Warehouse & Stock**
  - Loading state and improved stock availability logic in WarehouseAvailabilityDialog
  - Optimized bundle availability calculation across warehouses
  - Improved stock visibility and translation in warehouse dialogs

- **Draft Invoice Features**
  - Print button for draft invoices
  - Auto-save active cart when switching drafts

- **Coupon Management**
  - Validate coupon endpoint for gift cards
  - Enhanced customer selection in coupon management

- **Settings Organization**
  - Split POS Settings into organized tabs

### Changed
- **Cart Operations**
  - Refactored updateQuantity function to improve item removal logic
  - Improved UOM selection UI and cart item handling

- **POS Profile Handling**
  - User company check utility moved to ecs_posnext utilities
  - Refactored payment, user, item group, and customer group handling in profile update
  - Simplified profile creation with enhanced parameter parsing
  - Cleaned up imports in POS profile API

### Fixed
- **Offers & Promotions**
  - Race condition causing offers applied but cart not updating
  - Made offer processing more dynamic and robust
  - Enhanced offer management with automatic application and improved notifications

- **Stock Validation**
  - Fixed stock validation and double-add issue in ItemsSelector
  - Skip stock validation for non-stock items

- **RTL & Translation**
  - RTL alignment and translation in ShiftOpeningDialog
  - RTL overlap in OffersDialog badge positioning

- **Drafts**
  - Prevent draft deletion on load
  - Populate drafts store to show drafts in Invoice Management

- **Sales Order Compatibility**
  - Fixed 'SalesOrder' object attribute errors (outstanding_amount, is_return, payments)
  - Fixed "Value missing for Sales Order: Customer" error
  - Fixed ReferenceError issues (usePOSCartStore, cartStore not defined)
  - Fixed TypeError for NoneType multiplication with float
  - Fixed sales order submission on checkout

- **Payment Dialog RTL**
  - Improved RTL support and mobile responsiveness in PaymentDialog

## [1.11.0] - 2025-12-07

### Added
- **Multi-UOM Cart Support**
  - Support for adding same item with different Units of Measure (UOMs) to cart
  - Each UOM line is tracked independently with its own quantity and rate
  - Quantity input field in UOM selection dialog for faster item entry

- **Enhanced Stock Display**
  - Real-time available stock now subtracts cart quantities from displayed stock
  - Stock display accounts for conversion factors when using different UOMs
  - Defensive checks for stock reservation calculations

- **Stock Lookup Across Warehouses**
  - New stock lookup dialog for checking item availability across all warehouses
  - Variant selection support in warehouse availability dialog

- **Speed Enhancements**
  - Clear customer search input field on click for faster customer selection
  - Clear item search bar on click for faster item search
  - Improved search UX for high-volume POS operations

### Changed
- **Subtotal Calculation**
  - Fixed subtotal recalculation when UOM changes mid-transaction
  - Cache rebuild after UOM change ensures accurate totals

- **RTL/LTR Compatibility**
  - Fixed contradicting RTL patterns in InvoiceDetailDialog
  - Added text-start class for proper RTL text alignment in ReturnInvoiceDialog
  - Removed manual RTL overrides that prevented natural mirroring

- **Invoice Display**
  - Show actual paid amount instead of grand total in invoice confirmation
  - Enhanced InvoiceCart layout for improved alignment of financial summaries

### Fixed
- **Pay on Account & Partial Payment**
  - Improved Pay on Account and Partial Payment handling in returns
  - Fixed payment flow for credit sale returns

- **Cart Operations with UOM**
  - Remove item by UOM works correctly for multi-UOM carts
  - Update quantity targets correct item line with same item_code but different UOM
  - Quantity validation ensures positive integer values

- **Customer Selection**
  - Prevent auto-select when clearing customer search field

- **Arabic Translations**
  - Fixed truncated translation key for cart requirements message
  - Keep POS Next brand name consistent across translations
  - Fixed "Apply Coupon" and "serials" translations for clarity

## [1.10.0] - 2025-11-28

### Added
- **Comprehensive Localization System**
  - Added locale management with Arabic translations for the entire POS application
  - Implemented LanguageSwitcher component integrated into POSHeader
  - User language change API with locale management in useLocale composable
  - Translation caching with IndexedDB for improved performance
  - Dynamic translation updates ensuring components re-render with selected language
  - Page reload mechanism to apply new translations consistently
  - Translation function calls added throughout the codebase for full i18n support

- **Sales Person Feature**
  - Implemented sales person selection and allocation in payment dialog
  - Sales person tracking in invoice processing for commission management

- **Enhanced Stock Validation**
  - Improved stock validation and item handling in cart and selection dialogs
  - Better error handling for stock-related operations

### Changed
- **RTL/LTR Support Improvements**
  - Enhanced RTL support for TextInput components with better layout alignment
  - Improved InvoiceDetailDialog RTL/mobile support with currency formatting
  - Standardized invoice status colors for both LTR and RTL layouts
  - Fixed RTL support for resizing behavior in POSSale component
  - Adjusted cache tooltip positioning and styling for RTL direction in POSHeader

- **Language Switcher UX**
  - Moved language switcher to user menu on mobile for a more compact header
  - Improved button and dropdown styles for better UI consistency

- **Serial Number Management**
  - Enhanced serial number management in POS for better tracking and selection

- **Layout and Spacing Improvements**
  - Refactored layout and spacing across UserMenu, POSHeader, ItemsSelector, and POSSale components
  - Improved overall UI consistency throughout the application

### Fixed
- **Dependency Updates**
  - Fixed frappe-ui dependency version format in package.json

- **POS Settings Configuration**
  - Removed problematic autoname field from POS settings configuration

- **Arabic Translations**
  - Updated Arabic translations for improved clarity and accuracy
  - Enhanced Arabic translations for invoices and item sorting functionality

## [1.9.0] - 2025-11-23

### Added
- **Country Code Selector for Customer Phone Numbers**
  - Added country code selector with flag icons for customer phone input
  - Visual country flag display for better user experience
  - Support for international phone number formats
- **Invoice Detail View**
  - Implemented comprehensive invoice detail view with proper API endpoints
  - Enhanced invoice information display and navigation
- **User Profile Management**
  - Added user profile image display in POS header
  - Implemented reactive user data management system
  - Real-time user information updates

### Changed
- **Print Functionality**
  - Updated print endpoint to use printview for better browser compatibility
  - Improved cross-browser printing experience
- **Node.js Version Update**
  - Updated Node.js version to 20 in CI workflow for better performance and security

### Fixed
- **Warehouse Availability Check**
  - Added warehouse availability check for out-of-stock items
  - Prevents selection of items not available in selected warehouse
- **Disabled Items Filtering**
  - Filter disabled items from Items Selector and search results
  - Only show active items available for sale
- **Customer API**
  - Fixed indentation in customer API for better code readability
  - Load all customers without hardcoded limit for better scalability
- **Return Invoice Dialog**
  - Enhanced return invoice dialog layout and status display
  - Adjusted dialog sizes for better UX across different screen sizes
  - Improved mobile responsiveness for return invoice dialog
- **Shift Dialog Navigation**
  - Navigate to POSSale when shift dialog is closed via X button
  - Better user flow when dismissing shift dialog
- **User Authentication Race Condition**
  - Resolved race condition where user appears as Guest after login
  - Fixed authentication state synchronization issues
- **Automatic Offer Validation**
  - Added automatic offer validation and removal when cart conditions change
  - Ensures promotional offers remain valid based on current cart state
- **Login Error Messages**
  - Show descriptive error message when inputting wrong credentials
  - Navigate to /pos when clicking cancel button of ShiftDialog

### Improved
- **Return Invoice UI**
  - Extracted payment icon utility for better code reusability
  - Improved return invoice UI consistency and styling
- **Cart UX Improvements**
  - **Customer Section:**
    - Added quick customer creation button next to search input
    - Large touch-friendly button (44px+) with user-plus icon
    - Improved search input with better sizing and rounded corners
    - Professional customer card design with gradient avatar
  - **Empty Cart Quick Actions:**
    - Implemented 2x3 grid with 6 action buttons
    - Quick access to: View Shift, Draft Invoices, Invoice History, Return Invoice, Close Shift, Create Customer
    - Icon backgrounds with subtle hover effects
    - Touch-friendly sizing meeting accessibility standards
  - **Cart Items Section:**
    - Relocated Offers & Coupon buttons to dedicated section below customer bar
    - Larger buttons with improved styling and badge visibility
    - Better spacing and padding throughout
  - **Action Buttons:**
    - Checkout and Hold Order now side-by-side (50/50 width)
    - Saves ~70px vertical space for more cart visibility
    - Consistent sizing and rounded styling
  - **Touch & Mobile Improvements:**
    - All buttons meet 44px+ minimum touch target
    - Increased padding and better text sizes
    - Consistent rounded styling and proper hover/active states

### Removed
- **POS Profile Feature Cleanup**
  - Removed create_pos_invoice_instead_of_sales_invoice feature from POS Profile
  - Simplified POS Profile configuration

## [1.8.0] - 2025-11-17

### Added
- **User-Controlled Sorting UI**
  - Added interactive sort dropdown with adjustments icon next to view controls
  - Toggle-based sorting: click to cycle between ascending/descending/none
  - Sort by name, quantity, item group, price, and item code
  - Visual feedback with active state icons and tooltips
  - Conditional sorting: only sorts when user explicitly triggers
  - Easy to extend with new sort fields
- **First/Last Page Navigation**
  - Added First/Last page navigation buttons to both grid and list views
  - First button (« on mobile) jumps to page 1
  - Last button (» on mobile) jumps to last page
  - Buttons disabled when already on first/last page

### Changed
- **Payment Methods Preloading**
  - Payment methods now always load at application startup
  - Ensures payment modes are available for offline mode
  - Removed conditional cache check that could skip loading
  - Added comprehensive logging for payment methods caching
  - Better offline reliability for payment processing

### Fixed
- **Payment Dialog UX Improvements**
  - Fixed payment amount increment step from 0.01 to 5 for better user experience
  - Changed increment applies to both payment entry inputs and custom amount fields
  - More logical increments for typical payment amounts
- **Payment Dialog Layout**
  - Fixed button alignment in payment dialog footer
  - All action buttons now appear on the same row
  - "Clear All" button positioned on left, action buttons on right
  - Improved visual consistency and professional appearance
- **Print Format Discount Display**
  - Fixed print format condition to handle negative discount_amount values
  - Changed condition from `> 0` to checking if discount exists
  - Added absolute value filter for correct display regardless of sign
  - Fixed issue where Frappe's print pipeline negates discount_amount causing display failure
- **Pagination Display Logic**
  - Fixed "All items loaded" message to only show on last page or when all items fit in one page
  - Previously showed incorrectly on first page
- **Browser Compatibility**
  - Fixed "crypto.randomUUID is not a function" error in POS Events Store
  - Implemented multi-tier UUID generation strategy for older browsers
  - RFC4122 v4 compliant fallback using Crypto API and Math.random()
  - Support for globalThis, window.crypto, and legacy environments

### Improved
- **Shift Closing Dialog Performance & Accessibility**
  - Fixed hideExpectedAmount reactivity bug using storeToRefs
  - Added comprehensive prop validation with type checking
  - Converted template function calls to computed properties for better performance
  - Extracted complex nested conditions to readable computed properties
  - Added ARIA labels for screen readers and keyboard navigation
  - Improved error handling with user-friendly messages and dismiss action
  - Added loading states and input validation
- **Item Sorting Implementation**
  - Refactored from 265 lines of repetitive code to 78 lines using v-for loop
  - 70% code reduction in dropdown implementation
  - Extracted sort configuration into SORT_OPTIONS and SORT_ICONS constants
  - O(n log n) sorting only on user action, not every render
  - Improved maintainability: new sort options require single array entry
- **Quantity-Based Sorting**
  - Items sorted by stock quantity in descending order (highest first)
  - Out-of-stock items automatically move to the bottom
  - Uses JavaScript's native Timsort algorithm for optimal performance
  - O(n log n) worst case, O(n) best case for nearly-sorted data
  - Performance: 100 items ~1ms, 500 items ~3ms, 1000 items ~5ms
  - Works for regular stock items and Product Bundles
- **Bundle Stock Display**
  - Show stock badge only for stock items and bundles
  - Display "N/A" for non-stock items in list view
  - Add bundle-specific UOM label in tooltips
  - Skip validation for batch/serial items (handled in dialog)
  - Differentiate error messages between bundles and regular items

## [1.7.1] - 2025-11-13

### Added
- **Workspace Reinstallation Migration**
  - Added migration hook to automatically reinstall workspace with latest configuration
  - Dynamic auto-discovery of all workspace JSON files in the workspace directory
  - Ensures workspace updates are applied during app upgrades
  - Comprehensive error handling and logging for workspace operations
- **Community Support Enhancement**
  - Added Telegram community link for real-time user communication and support
  - Reorganized Support & Community section in README for better visibility

### Fixed
- **Workspace Configuration**
  - Resolved workspace URL link validation error
  - Removed problematic Start POS URL link from workspace links section
  - URL links now properly supported only in shortcuts section

## [1.7.0] - 2025-11-11

### Added
- **Proactive Filter-Aware Caching with Real-time Sync**
  - Filter-aware caching strategy that checks POS Profile item group filters before loading
  - Fetches and caches ONLY items from filtered groups (90% reduction in data transfer)
  - Real-time cache synchronization via Socket.IO when POS Profile changes
  - Smart delta calculation for surgical cache updates (added/removed groups)
  - No manual cache clearing or page reload required
  - Transaction batching in offline worker (10x performance boost)
  - Query result caching with LRU eviction (5x faster repeated queries)
  - Index-optimized IndexedDB operations
  - Circuit breaker pattern for fault tolerance with exponential backoff retry
- **Free Items Support for Promotional Offers**
  - Added processFreeItems() to handle free item quantities from backend
  - Display free item badge (+X FREE) in cart UI
  - Include free items in total quantity count
  - Minimum quantity validation for offer eligibility
  - Reactive offer eligibility based on cart changes
- **Professional Documentation Enhancement**
  - Added 5 high-quality screenshots showcasing POS features
  - Created animated sales cycle GIF demonstrating complete workflow
  - Enhanced README with visual elements and comprehensive documentation

### Fixed
- **Item Group Filter and Toast Notifications**
  - Fixed empty items display when updating item group filters
  - Added forceServerFetch parameter to bypass cache and fetch fresh data
  - Migrated from frappe-ui toast to custom useToast composable
  - Reduced notification noise by removing low-value success notifications
  - Kept critical error and warning notifications only
- **IndexedDB and Caching Issues**
  - Fixed item_prices IndexedDB constraint violations
  - Added default "Standard" price_list for items missing one
  - Graceful error handling with individual record recovery
  - Fixed Dexie transaction API syntax

### Changed
- **Offers Module Refactoring**
  - Refactored offers.py with type hints and data classes
  - Removed unused coupon functions and pos_offer references
  - Fixed database column checks in promotions.py

## [1.6.1] - 2025-11-08

### Fixed
- **Tax-Inclusive Calculation**
  - Fixed issue where tax amounts were incorrectly shown as discounts in tax-inclusive mode
  - Frontend now sends correct gross amount (after discount, before tax extraction) to ERPNext
  - Proper tax calculation based on included_in_print_rate flag
  - Fixed both scenarios: items without discounts and items with discounts

## [1.6.0] - 2025-11-07

### Added
- **Overdue Invoice Status Support**
  - Added Overdue status filter with warning icon in Invoice Management
  - Overdue invoices now clearly identified with red styling
  - Separate filter button for quick access to overdue invoices
  - Added Overdue status to invoice filters component
- **Payment Source Audit Trail**
  - Payment history now shows source (POS vs Back Office) for better tracking
  - Differentiate between POS-created payments and back-office Payment Entries
  - Enhanced payment cards with color-coded source labels (blue for Back Office)
  - Added posting date to payment history for complete audit trail

### Changed
- **Time and Date Formatting**
  - Improved time formatting to handle both Date objects and time strings (HH:MM:SS format)
  - Standardized date format to DD/MM/YY across all invoice displays
  - Enhanced `formatTime()` composable with better string parsing
  - Added comprehensive JSDoc documentation for formatter functions
- **Status Display Refactoring**
  - Consolidated status display with reusable helper functions (`getStatusLabel`, `getStatusClass`)
  - Consistent status styling across all invoice components
  - Status labels now use proper terminology ("Partially Paid" instead of "Partly Paid")

### Improved
- **Backend Performance & Architecture (partial_payments.py)**
  - **Critical N+1 Query Fix**: Reduced payment history queries from O(n) to O(1) using batch fetching
  - **48x Performance Improvement**: Optimized invoice list loading with batch queries
  - Added company filter to Payment Ledger queries for multi-company performance (10-100x faster)
  - Implemented optional metadata fetching for 2x faster dashboard views
  - SQL queries now use COALESCE for NULL safety and proper aggregation
- **Security & Validation**
  - Comprehensive input validation on all API endpoints
  - POS Profile and Mode of Payment existence validation
  - String length limits to prevent DoS attacks
  - Query limit caps to prevent resource exhaustion (max 500 invoices)
  - Payment account validation before Payment Entry creation
- **Business Logic Validations**
  - Payment date cannot be before invoice date
  - Invoice state validation (submitted, not cancelled)
  - Total payment amount validation across multiple payments
  - Currency consistency checks
  - Amount tolerance for floating-point comparisons (0.01)
- **Error Handling & Reliability**
  - Transactional rollback for atomic payment operations
  - Automatic cancellation of partially-created payments on failure
  - Structured error logging with full context for debugging
  - Graceful degradation when payment metadata unavailable
  - Missing Payment Entry detection and logging
- **Code Quality & Maintainability**
  - Added constants and Enum for configuration (PaymentSource, AMOUNT_TOLERANCE, limits)
  - Comprehensive documentation with docstrings for all functions
  - Full type hints throughout Python API (typing.Dict, List, Optional)
  - Inline comments explaining business logic and ERPNext concepts
  - Performance notes for critical operations
  - Usage examples in docstrings

### Technical Details
- Payment Ledger now used as single source of truth for all payment tracking
- Batch fetching eliminates N+1 query problem in `get_payment_history()`
- Added `include_metadata` parameter for performance optimization
- Error recovery with automatic rollback on Payment Entry creation failure
- Module docstring with architecture explanation and best practices

### Performance Metrics
- Payment history for invoice with 10 payments: 21 queries → 3 queries (7x faster)
- Load 50 partial invoices: 2,550+ queries → 53 queries (48x faster)
- Summary statistics: O(n) → O(1) (constant time)
- Multi-company Payment Ledger query: 100x+ faster with proper indexing

## [1.5.0] - 2025-11-06

### Added
- **Default Customer Auto-Loading**
  - New `get_default_customer` API endpoint in POS Profile
  - Automatically loads default customer when POS opens if configured in POS Profile
  - Customer appears in cart immediately without manual selection
  - Maintains proper customer object structure matching manual selection

### Fixed
- **Original Price Display in Receipts and UI**
  - Fixed discount handling to preserve original `price_list_rate` in both UI and created invoices
  - Receipts now clearly show: quantity × original price = subtotal, then discount line, then final total
  - Backend receives correct net rate for accurate invoice totals
  - Print format updated to 80mm thermal receipt size instead of A4
  - Discount percentages now display with 2 decimal precision (was showing many decimal places)
  - Added comprehensive JSDoc documentation for pricing and discount calculation logic

### Changed
- **Dependency Version Pinning**
  - Pinned Vue version to exact 3.5.13 (removed caret) for better stability and reproducible builds

### Improved
- **Edit Item Dialog Decimal Quantity Support**
  - Quantity field now accepts decimal values (e.g., 0.5, 1.25, 2.75) matching cart behavior
  - Added smart step increment/decrement based on current quantity value
  - Improved input handling allowing free editing with validation only on blur
  - Supports very small quantities down to 0.0001
  - Added mobile-friendly decimal keyboard input mode
- **Currency Formatting in Edit Item Dialog**
  - Replaced raw currency codes (SAR, EGP, etc.) with proper currency symbols
  - All amounts now use consistent formatCurrency utility across the dialog
  - Rate field prefix displays currency symbol instead of code
  - Subtotal, discount, and total now properly formatted with locale support

## [1.4.0] - 2025-11-06

### Fixed
- **Item Query Function Whitelisting**
  - Fixed "Function not whitelisted" error when adding Tax Rules
  - Added `@frappe.whitelist()` decorator to `item_query` function
  - Parse JSON filters parameter when called from frontend
  - Remove mandatory company validation to allow global items
  - Set `custom_company` to empty string for new items without company
  - Fix demo data setup which creates items without company
  - Enabled global item selection across POS profiles
- **Mobile UI Layout**
  - Make footer fixed at bottom to prevent scrolling issues on mobile
  - Add responsive column widths to list view for better mobile experience
  - Fix vertical scrolling in ItemsSelector with proper min-height constraints
  - Move status messages inside table rows to span full width
  - Adjust floating cart button position to sit above fixed footer
  - Optimize column sizing: mobile (120px name, 70px rate/qty), tablet (180px), desktop (200px)

## [1.3.0] - 2025-11-05

### Added
- **BrainWise Branding API**
  - Implemented secure branding configuration API with validation
  - Centralized branding management system
- **POS Profile Custom Fields**
  - Added "Cash Mode of Payment" field to specify default cash payment method
  - Added "Block Sale Beyond Available Qty" field for stock control
  - Added "Allow Delete Draft Invoices" field for draft management permissions
- **Saudi Riyal Font Support**
  - Updated CSS to properly render Saudi Riyal currency symbol (ر.س)
  - Improved font rendering for Arabic text

## [1.2.0] - 2025-11-04

### Added
- **CSRF Token Synchronization**
  - Implemented CSRF token sync with offline worker for enhanced security
  - Ensures secure API calls from background workers
- **POSNext Workspace Configuration**
  - Added workspace links for enhanced navigation
  - Improved accessibility to POS features

### Changed
- **Project Documentation**
  - Updated project references for clarity and consistency
  - Improved inline documentation across codebase

### Fixed
- **Cart Data Processing**
  - Use `toRaw()` to prevent stale cached quantities in invoice data
  - Ensures fresh data is always used in calculations
- **Header Layout**
  - Removed `overflow-x-hidden` class from POSHeader for improved responsiveness

## [1.1.1] - 2025-10-29

### Added
- **Payment Dialog: Customer Credit/Outstanding Balance Display**
  - Real-time customer balance display with color-coded indicators
  - Green indicator for available credit
  - Red indicator for outstanding balance (amount owed)
  - Gray indicator for zero balance
  - Comprehensive balance information showing total outstanding, total credit, and net position
- **New API Endpoint: `get_customer_balance`**
  - Returns detailed customer balance including total outstanding, total credit, and net balance
  - Calculates from Sales Invoices and Payment Entries
  - Supports company-specific filtering
- **Payment Dialog: Dynamic Button States**
  - "Pay on Account" button automatically disables when payment entries are added
  - Button re-enables when all payments are removed
  - Prevents mixing regular payments with credit sales

### Changed
- **Payment Dialog Layout Reorganization**
  - Information section moved to top (payment summary, customer credit, discount, payment breakdown)
  - All payment action buttons consolidated at bottom
  - Clear visual separation between information and actions
  - "Pay on Account" button matches "Complete Payment" button styling
  - Button color scheme changed to warm orange tones (orange-600 enabled, orange-400 disabled)
- **Customer Credit Display**
  - Now fetches both available credit sources and overall balance
  - Shows comprehensive credit position instead of just available credit
  - Displays appropriate message based on balance status
- Payment action buttons positioned in dialog footer for better UX

### Fixed
- **Critical: Double discount bug** - Discounts were being applied twice (once in item rate, once in total calculation)
  - Frontend now correctly uses `price_list_rate` for subtotal calculations
  - Backend reverse-calculates `price_list_rate` from discounted rate to prevent double application
  - Example: Item with 10% discount now correctly shows 90.00 instead of 81.00
- **Customer credit not displaying correctly** - Credit was only showing available credit, not outstanding balance
- **"Disable Rounded Total" setting not working** - Backend was checking POS Profile instead of POS Settings
- **ReferenceError: couponCode is not defined** - Fixed undefined couponCode error in posCart.js when re-applying offers
  - Changed reference from non-existent `couponCode.value` to `appliedCoupon.value?.name`
- Subtotal calculation now uses original price before discount (fixes display inconsistency)
- "Pay on Account" button styling now matches other action buttons

### Improved
- Improved discount calculation logic with comprehensive documentation
- Added validation to prevent invalid discount percentages (now clamped to 0-100%)
- Enhanced error handling for rounding setting retrieval
- Added data integrity checks (price_list_rate must be >= rate)
- Added detailed inline documentation for discount calculation flow
- Code cleanup with better comments explaining critical logic
- Separated discount calculation into clearly documented sections
- Payment dialog now provides clearer visual feedback for button states

## [1.1.0] - 2025-10-28

### Added
- Real-time settings updates without page reload using Pinia event system
- Event-driven architecture for settings changes (pricing, sales operations, display)
- Missing fields to POS Settings DocType: `allow_user_to_edit_item_discount` and `disable_rounded_total`
- Settings event listeners in POSSale component for immediate UI updates
- Display settings change detection and event emission
- Toast notifications for settings changes to provide user feedback
- Comprehensive CHANGELOG.md following Keep a Changelog format

### Changed
- Settings now update immediately in all components without requiring page refresh
- POS Settings store now includes `reloadSettings()` method for forced refresh
- Event detection system now includes all pricing and display fields

### Fixed
- "Allow Item Discount" setting not persisting to database
- "Disable Rounded Total" setting not persisting to database
- Settings reverting to defaults after page refresh

## [1.0.2] - 2025-10-28

### Added
- App version display in POS header with enhanced styling
- UOM pricing logic with conversion factor support

### Changed
- Enhanced POS header to display current application version
- Updated UOM pricing calculations to account for conversion factors

## [1.0.1] - 2025-10-27

### Added
- Invoice filtering logic and store management
- Partial Payments feature in POS
- Stock validation and event-driven settings management
- Word-order independent search for cached items
- Referral code management with validation and coupon generation
- Fuzzy word-order independent item search
- Periodic stock sync functionality
- Performance optimizations for low-end devices
- Developer tooling for debugging

### Changed
- Improved search functionality with fuzzy matching and relevance scoring
- Enhanced offline mode and UI responsiveness
- Optimized ItemsSelector component for better performance
- Improved list view functionality

### Fixed
- Stock badge synchronization issue
- Stock reservations preservation during refresh
- Warehouse change detection
- Logger.success error in Web Worker context
- High-priority performance and memory issues

## [1.0.0] - Initial Release

### Added
- Core POS functionality
- Offline mode support
- Invoice management
- Customer management
- Item search and selection
- Payment processing
- Shift management
- Stock tracking

[Unreleased]: https://github.com/BrainWise-DEV/POSNext/compare/v1.15.0...HEAD
[1.15.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.14.0...v1.15.0
[1.14.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.13.0...v1.14.0
[1.13.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.12.0...v1.13.0
[1.12.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.11.0...v1.12.0
[1.11.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.10.0...v1.11.0
[1.10.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.9.0...v1.10.0
[1.9.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.8.0...v1.9.0
[1.8.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.7.1...v1.8.0
[1.7.1]: https://github.com/BrainWise-DEV/POSNext/compare/v1.7.0...v1.7.1
[1.7.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.6.1...v1.7.0
[1.6.1]: https://github.com/BrainWise-DEV/POSNext/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/BrainWise-DEV/POSNext/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/BrainWise-DEV/POSNext/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/BrainWise-DEV/POSNext/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/BrainWise-DEV/POSNext/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/BrainWise-DEV/POSNext/releases/tag/v1.0.0
