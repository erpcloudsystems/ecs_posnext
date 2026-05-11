# POS Customer Inline Entry - 2026-05-08

## Summary
Implemented inline customer name and mobile number fields in the Complete Payment dialog, replacing the mandatory customer selection popup that previously blocked checkout when no customer was selected.

## Changes Made

### `POS/src/pages/POSSale.vue`
1. **`handleProceedToPayment`**: Removed the block that checked for a cart customer and showed `CustomerDialog` if none was selected. Now goes directly to `uiStore.showPaymentDialog = true`.
2. **PaymentDialog template**: Added `:profile-customer="shiftStore.profileCustomer"` prop.
3. **`handlePaymentCompleted`**: Added handling for `paymentData.customer` — calls `cartStore.setCustomer(paymentData.customer)` before the invoice submission check. Removed the redirect to `CustomerDialog` from within this function.

### `POS/src/components/sale/PaymentDialog.vue`
1. **New prop**: `profileCustomer: String` — used to determine if customer fields are required.
2. **New reactive state**: `customerNameQuery`, `customerMobileQuery`, `customerNameResults`, `customerMobileResults`, `customerSearchLoading`, `selectedCustomer`, `customerNameDropdownOpen`, `customerMobileDropdownOpen`, `isCreatingCustomer`.
3. **New computeds**:
   - `customerRequired`: true when cart has no customer AND POS profile has no default customer.
   - `effectiveCustomer`: returns `selectedCustomer.value` if it has a name, else null.
4. **Template**: Added customer block at the top of the right column (above Sales Person), containing:
   - Customer Name input with live search dropdown (debounced, ≥2 chars)
   - Customer Mobile input with live search dropdown (debounced, ≥3 chars)
   - Link icon (opens `/app/customer/{name}` in new tab) when a customer is selected
   - Red validation styling when customer is required and nothing is entered
5. **Customer search functions**: `_searchCustomersByName`, `_searchCustomersByMobile`, `handleCustomerNameInput`, `handleCustomerMobileInput`, `selectCustomerFromSearch`, `handleCustomerNameBlur`, `handleCustomerMobileBlur` — uses `call("frappe.client.get_list", ...)`.
6. **`canComplete`**: Added customer check at the top — returns false when `customerRequired && !customerNameQuery.trim() && !selectedCustomer`.
7. **`watch(show)`**: Added initialization of customer fields when dialog opens — pre-fills name/mobile from `props.customer` and sets `selectedCustomer` to the cart customer object.
8. **`completePayment`** (now `async`):
   - If `effectiveCustomer` is null but a name is typed → calls `frappe.client.insert` to create a new Customer with the entered name and mobile, then uses the new customer.
   - Adds `customer: resolvedCustomer` to the emitted `paymentData`.
9. **Button disabled conditions**: Both Complete Payment buttons (mobile and desktop) now include `|| isCreatingCustomer`.

## Architecture Notes
- Customer search uses `frappe.client.get_list` via `call` (already imported from `frappe-ui` in this file).
- Customer creation uses `frappe.client.insert` with `customer_group: "أفراد"` and `territory: "All Territories"` as defaults (matching existing `CreateCustomerDialog.vue`).
- The `selectedCustomer` ref is initialized from `props.customer` when the dialog opens, so existing cart customers appear pre-filled and linkable.
- `paymentData.customer` is always passed to `handlePaymentCompleted`; POSSale.vue calls `cartStore.setCustomer()` only if it's truthy.

## Build Status
✅ `yarn build` succeeded (exit code 0, 26.30s)
