# Session: 2026-04-28 — Fix POS Sales Invoice Status and Journal Entry Cancel

**Agent:** Windsurf Cascade  
**Developer:** erpcloud.systems  
**Goal:** Fix two issues: 1) POS Sales Invoices showing status "unpaid" instead of "Paid", 2) Cancel linked Journal Entries when canceling Sales Invoice

---

## Summary

Fixed two critical bugs in the POS workflow:

1. **Invoice Status Issue**: When an existing invoice draft was updated via `submit_invoice()`, the `is_pos` flag was not being set, causing ERPNext to treat it as a regular invoice with outstanding balance, showing status as "unpaid" instead of "Paid".

2. **Journal Entry Cancel Issue**: When canceling a Sales Invoice, the linked Journal Entries (CIB Visa commission and assistant commission) were not being canceled, causing orphaned documents.

---

## Changes Made

### ecs_posnext

| File | Change |
|------|--------|
| `ecs_posnext/api/invoices.py` | Added `invoice_doc.is_pos = 1` in the existing invoice update path (line 1204) |

### ecs_heshamrabea

| File | Change |
|------|--------|
| `ecs_heshamrabea/doctype_triggers/accounting/sales_invoice/sales_invoice.py` | Added `cancel_linked_journal_entries()` function and called it in `on_cancel` hook |

---

## Technical Details

### Fix 1: Invoice Status

**Location**: `@/home/frappe/frappe-bench/apps/ecs_posnext/ecs_posnext/api/invoices.py:1202-1205`

```python
# Ensure POS flags are set for Sales Invoice
if doctype == "Sales Invoice":
    invoice_doc.is_pos = 1
    invoice_doc.update_stock = 1
```

The fix ensures `is_pos = 1` is set for both new and existing invoice drafts when submitting via the POS API.

### Fix 2: Journal Entry Cancel

**Location**: `@/home/frappe/frappe-bench/apps/ecs_heshamrabea/ecs_heshamrabea/doctype_triggers/accounting/sales_invoice/sales_invoice.py:369-409`

Added `cancel_linked_journal_entries()` function that:
- Cancels CIB Visa commission JEs (linked via `custom_sales_invoice` field)
- Cancels assistant commission JEs (linked via `user_remark` containing invoice name pattern)

Updated `on_cancel` hook to call the new function alongside existing cancel logic.

---

## Decisions / Notes

- The `is_pos` flag must be set before `doc.submit()` is called for ERPNext to properly calculate the invoice status as "Paid" for POS invoices.
- Journal Entry linking for assistant commissions uses `user_remark` pattern matching since there's no dedicated link field.
- Both fixes follow the existing error handling patterns (log errors, don't block main operation).

---

## Follow-up Items

- [ ] Test POS invoice submission with existing draft to verify "Paid" status
- [ ] Test Sales Invoice cancel with CIB Visa payment to verify JE cancellation
- [ ] Test Sales Invoice cancel with assistant salesperson to verify JE cancellation
