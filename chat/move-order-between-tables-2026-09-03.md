# Session: 2026-09-03 — Move an Open Order Between Tables

**Agent:** Claude Code (Opus 5)
**Developer:** erpcloud.systems
**Goal:** Move an open order from one table to another

---

## Summary

Asked: *"اقدر انقل الاوردر المفتوح من ترابيزة لتانيه"* — can I move an open order from one table to
another?

**Answer before this session: partially, and it corrupted data.** The header chip already let a
cashier change the table via `update_table_session`, but that updated only the session —
`POS Table Order.table` kept pointing at the old table. Reproduced live: session moved to table 10
while the order record still said table 1, so the dashboard (which reads the session) and the order
record disagreed.

There was also no way to move an order that was **not** in the current cart. The offline-conflict
path I had added earlier literally told cashiers *"move this order to another table"* — with no
action anywhere that could do it.

## Changes Made

### `api/table_orders.move_table_session(session, target_table, merge=False)`

| Destination | Result |
|---|---|
| Same table | `unchanged` |
| Free | `moved` — session **and** its open order both point at the new table |
| Occupied, `merge=False` | `occupied` — **nothing is written**, the caller is told what is in the way |
| Occupied, `merge=True` | `merged` — bills combined |

Refusing by default matters: two open orders on two tables are two different bills, and silently
combining them is a money bug. The caller has to ask for it.

**Merging** appends the source order's lines to the destination's (creating the destination's order
if the table was seated but had not ordered), adds the guest counts together, then closes the source
session and cancels its order so the dashboard shows one table rather than two. Lines keep their
`added_by`, so waiter attribution survives the merge.

`update_table_session` was fixed the same way — a table change there now moves the session's open
order too, and returns `moved_from`.

Moves and merges are written to the session's timeline via `add_comment`, rather than new fields:
moves are occasional, and the timeline already records who and when. The logging is wrapped so an
audit note can never fail the move itself.

The `table_sessions` → `table_orders` import is function-local, since `table_orders` already imports
from `table_sessions` at module level.

### POS frontend

`components/tables/MoveTableDialog.vue` — destination picker as a grid with occupancy shown, the
current table excluded, and a checkbox that gates joining. Re-picking a destination clears the tick.
If the destination fills up between opening the list and confirming, the `occupied` response is
handled inline rather than throwing.

`TableDashboard.vue` gained a Move button per card and re-reads after a move, since a merge changes
which tables exist.

`POSSale.handleTableMoved` keeps the open cart in step:
- its session **moved** → update the cart's table
- its session **merged away** → repoint the cart at the surviving session, so items still sitting
  unsaved in the cart get held onto the combined bill instead of a closed session. Held lines are
  already server-side; only unsaved ones are at stake, hence the different message depending on
  whether the cart is empty.

---

## Verification

Backend, live:

| Case | Result |
|---|---|
| Move to a free table | session `10`, order `10` — **consistent** (was the bug) |
| Header-chip path (`update_table_session`) | order follows too, `moved_from` returned |
| Same table | `unchanged` |
| Occupied without merge | `occupied`; source session **and** order both unchanged |
| Merge | 1 line moved, qty 1 → 3, amount 40 → 190, guests 2+3 = **5** |
| After merge | source session `Closed`, source order `Cancelled`, dashboard shows **one** table |
| Line attribution | survives the merge |
| Timeline | three notes recording each move/merge and who did it |
| Test data left behind | 0 sessions, 0 orders |

Frontend, 9 vitest cases: the current table is never offered, no destination = cannot move, a free
table needs no extra confirmation, **an occupied table is blocked until ticked**, no double-submit;
and the cart follows a move, ignores another table's move, repoints after its own merge, and ignores
another table's merge.

Build, `bench build` and deploy clean.

---

## Follow-up Items

- [ ] **Swap** two occupied tables is not supported — only move-to-free and join
- [ ] A merge cannot be undone; splitting a joined bill back apart would need a separate feature
- [ ] Protel push still outstanding; a move/merge will need to be reflected there once it exists
