# Session: 2026-09-03 — User Attribution for the Protel Push

**Agent:** Claude Code (Opus 5)
**Developer:** erpcloud.systems
**Goal:** Anything pushed to Protel must carry the POS Next user who actually performed it

---

## Summary

Requested: *"اي حركة هتروح بروتيل تروح باسم اليوزر الي عملها في نكست / user id"* — every movement
sent to Protel goes under the id of the user who made it in Next.

The Protel push itself is still not built (no API contract yet), so the work here is to make sure
the acting user is **captured accurately and preserved** on every table-service record, ready for
whatever payload the push ends up sending. Auditing what was captured found three genuine defects.

## Defects found

**1. Offline sync credited the wrong user.** `sync_offline_table_order` never passed a cashier, so
`POSTableSession.before_insert` fell back to `frappe.session.user` — **the user whose terminal
uploaded the order**, not the one who took it. A waiter's offline round would appear under whoever
happened to come online first.

**2. Re-holding destroyed attribution.** `save_table_order` did `doc.cashier = frappe.session.user`
on *every* save. When a second waiter added a round to an existing table order, the first waiter's
name was overwritten and gone.

**3. No per-round attribution.** Only the order header had a user. A table where waiter A takes
drinks and waiter B takes food had no record of which lines belonged to whom — so a per-movement
push to Protel had nothing to attribute.

## Changes Made

### Doctypes

| Doctype | Field | Purpose |
|---|---|---|
| `POS Table Order Item` | `added_by` | The user who rang **this line** |
| `POS Table Order` | `last_order_by` | Who last added to the order |
| `POS Table Order` | `synced_by` | Whose terminal uploaded it (offline case) |
| `POS Table Session` | `synced_by` | Same, for the seating |

`cashier` keeps its meaning on both: the user who **opened** the session / the order.

### API

- `save_table_order` sets `cashier` only when it is not already set, always updates
  `last_order_by`, and stamps `added_by` on each line (keeping a value the client already supplied,
  which is how a replayed offline round retains its original waiter).
- `sync_offline_table_order` / `promote_offline_session` accept `cashier` and attribute the record
  to that user, setting `synced_by` to the uploading session. Since `save_table_order` attributes to
  the session (correct online, wrong here), the sync path corrects `cashier` / `last_order_by`
  afterwards.
- `_resolve_offline_actor()` validates a claimed user: unknown users are logged and ignored,
  disabled users are not credited with new activity, and either way it falls back to the uploading
  session.

**Spoofing.** A client-supplied user is honoured **only** on the offline-replay endpoints, because
only there can the server not know who acted. `save_table_order` deliberately has no `cashier`
parameter, so the online path always takes the acting user from `frappe.session.user` and a request
cannot claim to be someone else. `synced_by` means even an honoured claim stays auditable.

### Frontend

`tableCashier` added to the cart state (`useInvoice` → `posCart`) and the draft context, recorded
only for an **offline** seating — online the server already knows. Item lines carry
`added_by: item.added_by || session.user`, and the reconnect sync sends both the line-level
attribution and the draft's `table_cashier`.

### Surfacing

Dashboard cards show the opener, plus "last: <user>" only when a different waiter added the last
round. The Open Tables report replaces its single "Cashier" column with "Opened By" and
"Last Order By".

---

## Verification

Two real POS Profile members acting as two waiters (a first run failed with `PermissionError`
because the users picked were not profile members — the access check working as intended):

| Case | Result |
|---|---|
| A opens, B adds a round (online) | `cashier` stays **A**, `last_order_by` becomes **B** |
| Session cashier | **A** |
| A takes it offline, **B uploads** | session + order `cashier` = **A**, `synced_by` = **B** |
| Offline line attribution | every `added_by` = **A** |
| Claimed user that does not exist | refused, falls back to the uploading session |
| `save_table_order` signature | has **no** `cashier` parameter — online cannot be spoofed |
| Dashboard / report | both show Opened By and Last Order By correctly |
| Test data left behind | 0 sessions, 0 orders |

Build, `bench build` and migrations clean.

---

## Follow-up Items

- [ ] **The Protel push itself.** Still needs the API contract: endpoint, auth, payload shape, and
      how a POS Next user id maps to a Protel user/waiter id. The data is now ready to send
- [ ] Consider whether Protel needs one push per round (per `added_by` group) or one per bill —
      that decision changes whether `added_by` or `cashier` is the field the payload carries
- [ ] `POS Table Session.cashier` is still the opener only; if a table is handed over between
      shifts there is no handover record
