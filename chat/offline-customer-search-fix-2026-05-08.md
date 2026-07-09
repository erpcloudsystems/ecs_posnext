# Offline Customer Search Fix - 2026-05-08

## Summary
Fixed the customer search dropdown in the Complete Payment dialog so it works while the POS is offline. Previously, both the Customer Name and Customer Mobile searches called `frappe.client.get_list` directly, which fails without network connectivity and left the dropdown empty.

## Root Cause
`PaymentDialog.vue` implemented inline customer search using server-side `frappe.client.get_list` calls only. It did not use the existing IndexedDB customer cache maintained by the offline worker, even though `offlineWorker.searchCachedCustomers` was already exposed and preloaded.

## Changes Made

### `POS/src/components/sale/PaymentDialog.vue`
1. **`_searchCustomersByName`**: When `props.isOffline` is true, now calls `_searchCachedCustomers(query, "name")` instead of `frappe.client.get_list`.
2. **`_searchCustomersByMobile`**: When `props.isOffline` is true, now calls `_searchCachedCustomers(query, "mobile")` instead of `frappe.client.get_list`.
3. **New helper `_searchCachedCustomers(query, field)`**:
   - Uses `offlineWorker.searchCachedCustomers(term, 20)` to fetch from IndexedDB.
   - Filters results to match online behavior:
     - `"name"` search matches `customer_name` or `name`.
     - `"mobile"` search matches `mobile_no`.
   - Returns up to 10 results.
   - Catches and logs errors, returning an empty array so the UI degrades gracefully.

## Files Modified
- `POS/src/components/sale/PaymentDialog.vue`
- `CHANGELOG.md`

## Build Status
⚠️ Build/lint was not executed in this session.

## Notes
- Online behavior is unchanged; offline behavior now mirrors the online search as closely as possible using the local customer cache.
- New customer creation still requires network connectivity because it uses `frappe.client.insert`; this fix addresses only the search/fetch issue reported by the user.
