# Offline Customer Search & Creation Fix - 2026-05-08

## Summary
Fixed the customer search and customer creation in the Complete Payment dialog so both work while the POS is offline, matching the behavior of the cart's customer search shown in the screenshot. Previously, the inline customer fields called `frappe.client.get_list` for search and `frappe.client.insert` for creation, both of which fail without network connectivity.

## Root Cause
`PaymentDialog.vue` implemented inline customer search using server-side `frappe.client.get_list` calls only. It did not use the shared `customerSearchStore` (which the cart uses) and did not handle offline customer creation.

## Changes Made

### `POS/src/components/sale/PaymentDialog.vue`
1. **Import `useCustomerSearchStore`**: Added the shared store that InvoiceCart uses for customer search and caching.
2. **Load customer cache on open**: When the dialog opens, `customerSearchStore.loadAllCustomers(props.posProfile)` is called so the cache is ready immediately.
3. **`_searchCustomersByName`**: Now always filters `customerSearchStore.allCustomers` in memory (same as the cart's customer search), so it works offline and online.
4. **`_searchCustomersByMobile`**: Same change as above, filtering by `mobile_no`.
5. **`_searchCachedCustomers(query, field)`**: Refactored to a synchronous helper that filters the store's `allCustomers` array.
6. **Offline customer creation**: In `completePayment`, when `props.isOffline` is true and a new customer name is typed, a local customer object is created and cached via `customerSearchStore.addCustomerToCache`. Online creation still uses `frappe.client.insert`.

## Files Modified
- `POS/src/components/sale/PaymentDialog.vue`
- `CHANGELOG.md`

## Build Status
⚠️ Build/lint was not executed in this session.

## Notes
- The payment dialog customer search now behaves like the cart's customer search (same shared store, same offline-first cache).
- Offline-created customers are cached locally and will be created on the server when the offline invoice is synced (the backend `update_invoice` already creates missing customers).
