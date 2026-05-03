# Session: 2026-05-03 — Add Item Price Validity Filters to POS

**Agent:** Windsurf Cascade  
**Developer:** erpcloud.systems  
**Goal:** Ensure POS displays only currently valid Item Prices by adding `valid_from` and `valid_upto` date filters to all price queries

---

## Summary

The POS was displaying all Item Prices from the database without filtering by validity dates. This meant expired prices or future-dated prices could be shown to cashiers, causing incorrect pricing.

**Root Cause:**
All Item Price queries in `ecs_posnext/api/items.py` were missing date validity filters:
- `valid_from` field — price becomes valid from this date
- `valid_upto` field — price expires after this date

ERPNext's Item Price DocType has these fields to manage time-based pricing (e.g., seasonal discounts, promotional pricing), but the POS wasn't respecting them.

**Additional Issue:**
When multiple Item Price records existed for the same item/price list/UOM (all valid), the query didn't order by `modified` date, potentially returning an older price instead of the latest one.

**Price Overwrite Bug:**
Even after adding `ORDER BY modified DESC`, the code was iterating through ALL price results and overwriting the dict, so the LAST price (oldest) won instead of the FIRST (newest).

Example:
- Item "قص اطفال" has 2 valid prices:
  - Rate 270, modified: 2026-05-03 (newest) ← returned first by ORDER BY modified DESC
  - Rate 250, modified: 2026-01-14 (oldest) ← returned second

**Bug:** Loop iterated through both, overwriting 270 with 250 ❌
**Fix:** Only set price if uom not already in dict (first result wins) ✅

---

## Changes Made

### File: `ecs_posnext/api/items.py`

**Import Added (line 11):**
```python
from frappe.query_builder import DocType, Order, functions as fn
```

Updated **4 functions** to add Item Price validity filters and modified date ordering:

| Function | Lines Modified | Change |
|----------|----------------|--------|
| `get_items()` | 1190-1218 | Added `valid_from`, `valid_upto` filters and `ORDER BY modified DESC` |
| `get_items_bulk()` | 1509-1535 | Added `valid_from`, `valid_upto` filters and `ORDER BY modified DESC` |
| `get_item_variants()` | 587-614 | Added `valid_from`, `valid_upto` filters and `ORDER BY modified DESC` |
| `search_by_barcode()` | 395-412 | Added `valid_from`, `valid_upto` filters and `ORDER BY modified DESC` |

**Filter Logic Added:**
```python
today = nowdate()
prices = (
    frappe.qb.from_(ItemPrice)
    .select(...)
    .where(ItemPrice.item_code.isin(item_codes))
    .where(ItemPrice.price_list == pos_profile_doc.selling_price_list)
    .where((ItemPrice.valid_from.isnull()) | (ItemPrice.valid_from <= today))  # NEW
    .where((ItemPrice.valid_upto.isnull()) | (ItemPrice.valid_upto >= today))  # NEW
    .run(as_dict=True)
)
```

**Logic:**
- `valid_from IS NULL OR valid_from <= today` — show prices that have started or have no start date
- `valid_upto IS NULL OR valid_upto >= today` — show prices that haven't expired or have no expiry date

### File: `CHANGELOG.md`

Added entry under `[Unreleased] → Fixed` section documenting the change.

---

## Technical Details

**Before Fix:**
```python
# Missing validity filters
.where(ItemPrice.item_code.isin(item_codes))
.where(ItemPrice.price_list == pos_profile_doc.selling_price_list)
```

**After Fix:**
```python
# Now respects Item Price validity period
today = nowdate()
.where(ItemPrice.item_code.isin(item_codes))
.where(ItemPrice.price_list == pos_profile_doc.selling_price_list)
.where((ItemPrice.valid_from.isnull()) | (ItemPrice.valid_from <= today))
.where((ItemPrice.valid_upto.isnull()) | (ItemPrice.valid_upto >= today))
.orderby(ItemPrice.item_code)
.orderby(ItemPrice.uom)
.orderby(ItemPrice.modified, order=Order.desc)  # Latest price first
.run(as_dict=True)
)

# Only set price if not already set (first result wins)
for price in prices:
    if price["item_code"] not in uom_prices_map:
        uom_prices_map[price["item_code"]] = {}
    if price["uom"] not in uom_prices_map[price["item_code"]]:
        uom_prices_map[price["item_code"]][price["uom"]] = price["price_list_rate"]
```

**Example Scenario:**
- Item "ABC-001" has 3 prices in "Standard Selling" price list:
  1. Rate: 100, valid_from: 2026-01-01, valid_upto: 2026-03-31 ❌ (expired)
  2. Rate: 120, valid_from: 2026-04-01, valid_upto: NULL ✅ (current)
  3. Rate: 150, valid_from: 2026-06-01, valid_upto: NULL ❌ (future)

**Before:** POS might show rate 100, 120, or 150 (unpredictable)  
**After:** POS shows only rate 120 (currently valid)

**Modified Date Ordering + Price Selection Fix:**
When multiple valid prices exist for same item/price list/UOM:
- Price A: Rate 100, modified: 2026-01-01
- Price B: Rate 120, modified: 2026-04-01
- Price C: Rate 110, modified: 2026-05-01 (updated price change)

**Without ordering:** Might return Price A (oldest) ❌
**With `ORDER BY modified DESC` but bug:** Returns Price C first, then overwrites with A ❌
**With `ORDER BY modified DESC` + fix:** Returns Price C (first) and keeps it ✅

---

## Affected API Endpoints

All endpoints that fetch items for POS now respect Item Price validity:
- `/api/method/ecs_posnext.api.items.get_items` — main item search/browse
- `/api/method/ecs_posnext.api.items.get_items_bulk` — bulk item fetch for offline caching
- `/api/method/ecs_posnext.api.items.get_item_variants` — variant selection dialog
- `/api/method/ecs_posnext.api.items.search_by_barcode` — barcode scanning

---

## Impact

**Positive:**
- ✅ Correct pricing displayed based on current date
- ✅ Expired promotional prices automatically hidden
- ✅ Future-dated prices don't appear early
- ✅ Aligns with ERPNext's standard Item Price behavior

**No Breaking Changes:**
- Items without price validity dates (`NULL` values) continue to work as before
- Existing functionality maintained, just more accurate filtering

---

## Testing Notes

To verify the fix:

**Validity Filtering:**
1. Create an Item Price with `valid_from` = tomorrow's date
2. Search for the item in POS
3. **Expected:** Item should show without this price (falls back to other valid prices or 0)
4. Change `valid_from` to yesterday
5. **Expected:** Item now shows this price

**Modified Date Ordering:**
1. Create 2 Item Price records for same item/price list/UOM:
   - Price A: Rate 100, modified: 2026-01-01
   - Price B: Rate 120, modified: 2026-05-03 (today)
2. Search for the item in POS
3. **Expected:** Item shows Rate 120 (most recent)
4. Update Price A to Rate 150 (modified becomes today)
5. **Expected:** Item shows Rate 150 (now most recent)

**UI Cache:**
After backend changes, clear POS cache to refresh item prices:
1. Open POS menu (top right)
2. Click "Clear Cache"
3. Confirm
4. Search item to verify updated price

---

## Follow-up Items

- [ ] Test with items that have multiple UOM-specific prices with different validity periods
- [ ] Verify offline mode correctly syncs only valid prices
- [ ] Test edge case: midnight transition (price expires at 23:59:59, new price starts at 00:00:00)
