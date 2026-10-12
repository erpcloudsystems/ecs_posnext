# Session: 2026-09-03 — Separate Checks (Split a Bill by Item)

**Agent:** Claude Code (Opus 5)
**Developer:** erpcloud.systems
**Goal:** Split a table's check among several people, each posted to its own room

---

## Summary

Asked: *"اقدر اقسم الشيك علي اكتر من فرد Separated check"*.

**Nothing existed.** `api/partial_payments.py` is about paying **one** invoice in instalments — a
different thing entirely. The README's "split bills" bullet was never implemented.

## Decisions Made

| Question | Decision |
|---|---|
| How is it split? | **By item only** — no equal-split shortcut |
| What does each check produce? | *"كل شيك يروح ع بروتيل منفصل ع رووم"* — each check posts to Protel separately, **charged to a room** |
| Payment | Each check paid on its own |

The room answer is the design driver: each check needs its own `room`, so the existing `Room`
doctype (65 records, from the `royal` app) is what a check is charged to.

## The architectural problem this exposed

The table-service code I had built assumed **exactly one open order per session**. Eight places
did `get_value(POS Table Order, {table_session, status: Open})`. Once a bill is split there are N
open orders and every one of those returns an **arbitrary** row — meaning items or a payment could
land on the wrong guest's check. That was the real work of this session.

`_get_working_order(session)` now makes the assumption explicit: it returns the single order, or
**throws** when the table is split. Callers that cannot act on an ambiguous table get
*"Table has N separate checks. Choose which check to use."* rather than a silent wrong answer.

| Place | Behaviour once split |
|---|---|
| `save_table_order` | refuses — adding to "the" order would pick a guest |
| `settle_table_order(table_session=…)` | refuses — pay a named check |
| `get_table_order(table_session=…)` | refuses |
| `split_table_order` on a check | refuses (no nested splits) |
| `cancel_table_order(table_session=…)` | cancels **every** check |
| `_move_to_free_table` | moves **all** checks |
| `update_table_session` (header chip move) | moves **all** checks |
| `_merge_into_session` | refuses if either side is split |
| `close_table_session` | refuses while any check is unpaid |
| `get_open_tables` | **aggregates** qty/total across checks, exposes `open_checks`, `is_split`, `rooms` |

## Changes Made

### Doctype

`POS Table Order` gained `check_number` (0 = the working order, 1..N = split checks), `room`
(Link → Room) and `split_from`.

### API

`split_table_order(order, checks)` — reconciles **exactly**: every unit of every line must land on
one check, or it throws. A partial split would leave items belonging to nobody and a table that
could never be fully settled. Rates are read from the **source order**, never from the client, so a
split cannot be used to reprice. The source order is Cancelled once the checks exist, otherwise the
table's total would double.

`get_table_checks(session)` — every check with its lines, room, status and Protel reference.
`set_check_room(order, room)` — correct a room while the check is open; refused once settled.

Splits are logged to the session timeline alongside the existing move/merge notes.

### POS frontend

- `SplitCheckDialog.vue` — an unassigned pool on the left, check columns on the right; tap to
  assign a unit, minus to return it. Quantities are tracked as a **remaining pool** rather than by
  moving objects, because the server demands exact reconciliation and the UI has to be able to prove
  nothing is left over. A live banner shows unassigned count, and Split stays disabled until zero.
  Each check carries a Room picker.
- `TableChecksDialog.vue` — per-check items, room, paid/unpaid, Pay button, inline room fix.
- `TableDashboard.vue` — Split action, "N separate checks" with rooms, and the primary button
  becomes **Pay checks** for a split table.
- `POSSale.vue` — the cart now carries `tableOrder` (which check it is settling), so payment
  settles that check. `closeTableSession` passes the order, reads `remaining_open_checks`, and tells
  the cashier when checks are still unpaid instead of appearing to finish the table.

---

## Verification

Two live runs, 20+ cases. Highlights:

| Case | Result |
|---|---|
| Split 3×100 + 1×50 into two checks | 200 + 150 = **350** = source total exactly |
| Each check | own `check_number`, own room, own `external_reference` |
| Source order after split | `Cancelled` |
| Fewer than two checks / unassigned items / over-quantity | all refused, specific messages |
| Re-split a check | refused |
| `save`/`settle`/`get` by session once split | **all refuse**, no silent pick |
| Move a split table | **both** checks moved |
| Join a split table (either direction) | refused |
| Pay check 1 | `remaining_open_checks: 1`, table **stays open** |
| Pay check 2 | table closes, dashboard empties |
| Dashboard while split | `open_checks: 2`, total 350, both rooms listed |
| `set_check_room` bad room / settled check | both refused |
| Test data left behind | 0 sessions, 0 orders |

Build, `bench build` and migrations clean.

---

## Follow-up Items

- [ ] **Protel push** — each check is now an independently postable unit with a room and an
      `external_reference` slot. Still needs the API contract
- [ ] No **unsplit**: once split, the checks cannot be recombined into one order
- [ ] Adding items after a split requires opening a specific check; there is no "add to the table"
      shortcut that asks which check
- [ ] Splitting by amount or equally was explicitly out of scope (by item only)
