# Payment Dialog Refinement — 2026-04-26

**Participants:** Developer, AI Agent (Cascade)

**Topics Discussed:**

1. **PaymentDialog.vue build error fix** — "Invalid end tag" at line 795 caused by orphaned `</div>` tags after numpad section was partially removed in a previous edit. Removed the entire numpad grid (7-8-9, 4-5-6, 1-2-3, 00-0-., backspace, clear, Add buttons).
2. **DailyPaymentManagement.vue date defaults** — Set `fromDate` and `toDate` to `new Date().toISOString().split("T")[0]` so filters open pre-set to today.
3. **PaymentDialog.vue sales person relocation** — Moved Sales Person selection block from left column (lines 38–237) to the top of the right column, above payment methods.
4. **PaymentDialog.vue payment method click behavior** — Added `addPayment(method)` wrapper that delegates to `quickAddPayment` so payment method buttons directly add the remaining amount on click (no separate Add button needed).
5. **ReturnInvoiceDialog.vue new return flow** — Replaced "Create Return" button with "Cancel & Amend". The old `is_return=1` invoice creation is no longer used.
6. **Backend `process_return_by_cancel` API** — Added new `ecs_posnext.api.invoices.process_return_by_cancel` that cancels the original Sales Invoice and, if items remain, creates a new Sales Invoice with proportional payments copied from the original. The existing `create_payment_entry_on_submit` hook auto-creates Payment Entries.

**Decisions Made:**

- Numpad section fully removed from PaymentDialog.vue (previously left orphaned tags).
- Sales Person block moved to right column top; left column now only holds Invoice Summary.
- Return flow switched from `is_return=1` credit-note pattern to cancel-and-recreate pattern to avoid separate return invoices.
- Proportional payments are calculated as `new_total / original_grand_total` and passed to the new invoice so it is auto-paid and Payment Entries are created by the existing hook.

**Files Created / Modified:**

| File | Action |
|------|--------|
| `POS/src/components/sale/PaymentDialog.vue` | Modified — removed numpad, moved sales person to right column, added `addPayment` function |
| `POS/src/components/daily_payment/DailyPaymentManagement.vue` | Modified — `fromDate`/`toDate` default to today |
| `POS/src/components/sale/ReturnInvoiceDialog.vue` | Modified — replaced "Create Return" with "Cancel & Amend", added `cancelAndRecreateResource` and `handleCancelAndRecreate` |
| `ecs_posnext/api/invoices.py` | Modified — added `process_return_by_cancel` function |

**Outcomes:**

- All build errors resolved; `bench build --app ecs_posnext` passes cleanly.
- PaymentDialog layout reorganized per user request.
- Return flow now cancels original invoice and recreates a new one with remaining items and proportional payments.
