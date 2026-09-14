# Correct the Mode of Payment of a POS Invoice - 2026-09-14

## Summary
Cashiers had no way to fix a sale rung up on the wrong tender. Added an **Update** action to each row of the POS Invoice History that switches an invoice between cash and card (and back), rebuilding every accounting document that depends on the mode of payment: the invoice GL entries, the Payment Entry, and the CIB Visa bank commission Journal Entry.

## Why cancel-and-reissue rather than an in-place edit
A POS invoice settles itself the moment it is submitted. By the time the mistake is noticed, three documents already point at the wrong account:

- the invoice's own GL entry debiting `بنك CIB - HR` or `خزينة فرع ... - HR`
- the Payment Entry created by the `on_submit` hooks in both `ecs_posnext` and `ecs_heshamrabea`
- for `بنك CIB فيزا`, the commission Journal Entry from `ecs_heshamrabea` (`custom_bank_commission_rate`, 1.5% → `عمولة تحصيل فيزا cib - HR`)

Editing the payment row would leave all three behind. The correction instead cancels the invoice — which lets each `on_cancel` hook reverse the documents it created — and submits an amendment (`amended_from`) that is identical except for the payment row, so the same code that posted the original chain posts the corrected one. This was the approach the developer chose over reversing entries by hand.

## Changes Made

### `ecs_posnext/api/invoices.py`
New **Mode of Payment Correction** section at the end of the file:
- `update_invoice_payment_mode(invoice_name, mode_of_payment)` — validates, cancels, re-issues. The amendment keeps the original `posting_date`, `posting_time` and `posa_pos_opening_shift`, so the correction lands in the period and the till the sale belongs to, and is settled for `rounded_total or grand_total` with `change_amount = 0` (cash handed back is not something the card collects). `_reapply_payment_amounts` is re-used after insert because ERPNext's `set_pos_fields` rebuilds the payments table from the POS Profile during save and zeroes the row.
- `get_payment_mode_update_options(invoice_name)` — one round trip for the dialog: current payment rows, the modes the POS Profile offers that have an account for the company (wallet modes excluded), and whether the correction is allowed with the reason if not.
- `_mode_of_payment_update_blocker` — returns a reason instead of throwing, so the same rules answer both endpoints. Blocks drafts, non-POS invoices, returns, consolidated invoices, invoices with no payment rows, partly paid and credit sales (`outstanding_amount > 0`), loyalty redemptions, wallet payments, invoices that already have a credit note or an amendment, and — for everyone but the Administrator — invoices outside the user's own open shift.
- `_assert_linked_vouchers_cancelled` — both payment hooks swallow their own errors so a failure there cannot block a cancellation. That is right for a plain cancel but here would post the money twice, once by the surviving voucher and once by the amendment, so a surviving submitted Payment Entry or commission JE throws and the whole correction is rolled back.
- `_log_payment_mode_update` — comment on the amendment naming the user, the invoice replaced and the modes moved between.

### `POS/src/components/sale/UpdatePaymentModeDialog.vue` (new)
Reads the options endpoint on open, shows the invoice with its current tender, offers the other modes as radio rows, and reports the server's refusal reason inline when the invoice is not eligible.

### `POS/src/components/sale/InvoiceHistoryDialog.vue`
Card icon between Print and Create Return, shown by `canUpdatePaymentMode`. The list is re-read after a correction, because the corrected sale is a new invoice.

### `POS/src/utils/invoice.js`
`canUpdatePaymentMode(invoice)` — mirrors the server guards that the history row already has the fields for, so the action is hidden where it could never work. The server re-checks everything.

### `ecs_posnext/translations/ar.csv`
Arabic for the dialog and for every server-side refusal message.

## Decisions
- **Shift-scoped for cashiers.** Once a shift is closed its totals have been reconciled, so a correction there belongs in the back office. The Administrator, who already sees history across shifts, is not limited.
- **Single payment row on the amendment.** A split payment collapses onto the chosen mode; there is no UI for re-splitting, which is a bigger feature than the one asked for.
- **Partly paid invoices refused** rather than guessed at: the correction settles the amendment in full, which would silently turn a credit sale into a paid one.

## Files Modified
- `ecs_posnext/api/invoices.py`
- `ecs_posnext/translations/ar.csv`
- `POS/src/components/sale/InvoiceHistoryDialog.vue`
- `POS/src/components/sale/UpdatePaymentModeDialog.vue` (new)
- `POS/src/utils/invoice.js`
- `POS/src/utils/__tests__/invoice.test.js` (new)
- `CHANGELOG.md`

## Verification
- `yarn test:run` — all suites pass, including the 5 new `canUpdatePaymentMode` cases
- `yarn biome check` clean on the new component and test; `invoice.js` and `InvoiceHistoryDialog.vue` report only their pre-existing formatting errors
- `yarn build` succeeds and the built assets in `ecs_posnext/public/pos` were refreshed
- Both directions exercised against live data inside a transaction that was rolled back afterwards (verified: nothing committed):
  - **Visa → Cash** on a 5,700 EGP invoice: original cancelled, Payment Entry cancelled and re-created against `خزينة فرع الحجاز - HR`, commission JE cancelled and none created, amendment `Paid`, GL balanced
  - **Cash → Visa** on an 800 EGP invoice: Payment Entry re-created against `بنك CIB - HR` and a 12.00 EGP commission JE created (1.5%), GL balanced
  - A partly paid invoice was refused with "Only fully paid invoices can be updated"

## Follow-up Items
- [ ] **Pre-existing, unrelated: POS payments look double-posted.** A POS Sales Invoice already posts its own cash/bank debit and settles the receivable, and the `on_submit` hooks then create an *unallocated* Payment Entry that debits the same cash/bank account and credits the receivable again (e.g. `ACC-SINV-2026-00385`: bank debited 5,700 twice, `الزبائن - HR` credited twice). This predates the correction feature — which faithfully reproduces whatever the normal submit does — but it is worth reviewing whether those Payment Entries should exist at all.
