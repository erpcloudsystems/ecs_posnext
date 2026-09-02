# Submit → printed receipt: where the ~7 seconds goes

The complaint: the cashier presses **Complete Payment** and paper comes out of the thermal
printer about **7 seconds** later.

This document attributes that time to stages, says which parts can be cut, and — the part
that matters for expectation-setting — which parts **cannot** be cut and why.

Nothing here has been changed yet. This is the analysis that a change should be based on.

---

## Table of Contents

1. [The short answer](#the-short-answer)
2. [What actually happens between the click and the paper](#what-actually-happens-between-the-click-and-the-paper)
3. [The six root causes](#the-six-root-causes)
4. [What can be shortened](#what-can-be-shortened)
5. [What cannot be shortened, and why](#what-cannot-be-shortened-and-why)
6. [Measure it before changing it](#measure-it-before-changing-it)

---

## The short answer

The 7 seconds is **not one slow thing**. It is a chain of **six sequential, fully-awaited
server round trips**, plus a browser render pass, plus a `wkhtmltopdf` subprocess, plus a
QZ Tray rasterize step. Nothing on the chain runs in parallel, and nothing is deferred to a
background job — `grep -rn "frappe.enqueue" ecs_posnext/` returns **zero** hits.

Three findings account for most of it:

| Rank | Cause | Cost |
|------|-------|------|
| 1 | The receipt pulls a **QR image from `api.qrserver.com` and fonts from Google** — on the critical path, **twice** (browser, then server) | 1–4 s |
| 2 | The print format is rendered **twice**, and the invoice is validated **three times** | 1–2 s |
| 3 | Work that has nothing to do with printing (stock refresh, POS Profile fetch) sits **between** submit and print | 0.3–1.5 s |

**Yes, it can be made shorter** — realistically from ~7 s to about **2 s**.
**It cannot go much below ~1.5–2 s** without changing what a receipt is or when the
accounting happens. Reasons in [the last section](#what-cannot-be-shortened-and-why).

---

## What actually happens between the click and the paper

Entry point: `handlePaymentCompleted` in
[POSSale.vue:1900](../POS/src/pages/POSSale.vue#L1900), hot path at
[POSSale.vue:1983-2013](../POS/src/pages/POSSale.vue#L1983-L2013).

```
Cashier presses "Complete Payment"
        │
        ▼
┌───────────────────────────────────────────────────────────────┐
│ 1  update_invoice          create + save draft  (validate #1) │  server
├───────────────────────────────────────────────────────────────┤
│ 2  submit_invoice          reload, save again, submit         │  server
│                            (validate #2 and #3, SLE + GL,     │
│                             Payment Entry, app hooks)         │
├───────────────────────────────────────────────────────────────┤
│ 3  stockStore.refresh      ← awaited, unrelated to printing   │  server + IndexedDB
├───────────────────────────────────────────────────────────────┤
│ 4  frappe.client.get       full POS Profile doc, every sale   │  server
├───────────────────────────────────────────────────────────────┤
│ 5  get_invoice_print_html  Jinja render #1                    │  server
├───────────────────────────────────────────────────────────────┤
│ 6  measure height          hidden iframe: waits on ALL images │  browser +
│                            + fonts.ready, 5 s watchdog        │  INTERNET
├───────────────────────────────────────────────────────────────┤
│ 7  get_invoice_print_pdf   Jinja render #2 + image fetch +    │  server +
│                            wkhtmltopdf                        │  INTERNET
├───────────────────────────────────────────────────────────────┤
│ 8  qz.print                JS SHA over base64 PDF, then QZ    │  till CPU +
│                            rasterizes the page                │  printer
└───────────────────────────────────────────────────────────────┘
        │
        ▼
     Paper moves
```

### Stage budget

| # | Stage | Code | Estimate |
|---|-------|------|----------|
| 1 | `update_invoice` — create + save draft | [useInvoice.js:1019](../POS/src/composables/useInvoice.js#L1019) → [invoices.py:744](../ecs_posnext/api/invoices.py#L744) | 0.4–1.0 s |
| 2 | `submit_invoice` — reload, save again, submit | [useInvoice.js:1045](../POS/src/composables/useInvoice.js#L1045) → [invoices.py:1248](../ecs_posnext/api/invoices.py#L1248) | 1.0–2.5 s |
| 3 | `stockStore.refresh(...)` (awaited **before** print) | [POSSale.vue:2001](../POS/src/pages/POSSale.vue#L2001) | 0.1–1.0 s |
| 4 | POS Profile fetch for `print_format` | [printInvoice.js:170](../POS/src/utils/printInvoice.js#L170) | 0.1–0.3 s |
| 5 | `get_invoice_print_html` | [printInvoice.js:42](../POS/src/utils/printInvoice.js#L42) → [invoices.py:1606](../ecs_posnext/api/invoices.py#L1606) | 0.2–0.5 s |
| 6 | Receipt height measurement | [printInvoice.js:97-140](../POS/src/utils/printInvoice.js#L97-L140) | 0.3–**5.0 s** |
| 7 | `get_invoice_print_pdf` | [printInvoice.js:70](../POS/src/utils/printInvoice.js#L70) → [invoices.py:1742](../ecs_posnext/api/invoices.py#L1742) | 1.0–3.0 s |
| 8 | `qz.print` → rasterize → spool | [qzTray.js:599-635](../POS/src/utils/qzTray.js#L599-L635) | 0.5–3.0 s |

The ranges overlap because two of the stages are bounded by network timeouts rather than by
work — a good day and a bad day differ by seconds on the same till.

### One thing that is *not* the problem

The QZ Tray websocket. It is connected **once**, at page mount
([POSSale.vue:1333](../POS/src/pages/POSSale.vue#L1333)), through a shared singleton promise
with a 60 s cooldown after a failed connect
([qzTray.js:365-401](../POS/src/utils/qzTray.js#L365-L401)). The signing certificate and key
are fetched once per session and cached in `localStorage`
([qzTray.js:104-135](../POS/src/utils/qzTray.js#L104-L135)). There is no connect/disconnect
churn per receipt, and no signing round trip per receipt — *unless* the till is on plain
HTTP, see cause **F**.

---

## The six root causes

### A — The same work done two or three times

**The print format is rendered twice per receipt.** The client fetches the HTML to measure
the receipt height ([printInvoice.js:355](../POS/src/utils/printInvoice.js#L355)), and then
`get_invoice_print_pdf` renders the whole thing again server-side:

```python
# ecs_posnext/api/invoices.py:1785
rendered = get_invoice_print_html(
    invoice_name, print_format=print_format, letterhead=letterhead, ...
)
```

Each render is `frappe.get_doc` + `frappe.get_meta` + `get_print_format_doc` +
`set_link_titles` (which walks every Link and Dynamic Link field, including in child tables)
+ full Jinja + `get_print_style`.

**The invoice is validated three times.** `save()` in `update_invoice`
([invoices.py:1017](../ecs_posnext/api/invoices.py#L1017)), `save()` again in `submit_invoice`
([invoices.py:1459](../ecs_posnext/api/invoices.py#L1459)), then `submit()`
([invoices.py:1469](../ecs_posnext/api/invoices.py#L1469)). Each pass re-runs
`set_missing_values()` and `calculate_taxes_and_totals()`, and every `validate` doc_event from
every installed app. `apply_tax_inclusive` adds *another*
`calculate_taxes_and_totals()` whenever a tax flag differs
([sales_invoice_hooks.py:72](../ecs_posnext/api/sales_invoice_hooks.py#L72)).

**Payment Entry creation is implemented three separate times:**

1. the `on_submit` hook — [sales_invoice_hooks.py:146](../ecs_posnext/api/sales_invoice_hooks.py#L146)
2. an explicit call — [invoices.py:1474](../ecs_posnext/api/invoices.py#L1474)
3. `ecs_heshamrabea`'s own `create_payment_entry_on_submit`

Each guards with `frappe.db.exists("Payment Entry", ...)`, so only the first actually creates
one — but all three still run their existence check and account lookups per payment row.

### B — The public internet is on the critical path, and it is hit twice

This is the sharpest finding. The shipped receipt format `POS Next Receipt`
([fixtures/print_format.json](../ecs_posnext/fixtures/print_format.json)) contains:

```html
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Cairo:wght@500;700&display=swap" rel="stylesheet">
...
<img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={{ doc.name }}">
<img src="/api/method/ecs_s3_storage.utils.s3_file_storage.get_s3_file?key=...jpeg">
```

**The QR code can never be cached.** The URL embeds `{{ doc.name }}`, so it is a different URL
for every invoice. The server-side image cache keys on `sha1(url)`:

```python
# ecs_posnext/api/invoices.py:1675
cache_key = "ecs_posnext_print_image:{0}".format(hashlib.sha1(url.encode()).hexdigest())
```

so the 1-hour cache at [invoices.py:1676-1679](../ecs_posnext/api/invoices.py#L1676-L1679)
**misses on every single receipt**, and every receipt makes a live outbound call:

```python
# ecs_posnext/api/invoices.py:1685
response = requests.get(url, timeout=5, cookies=cookies, stream=True)
```

Typical 200–800 ms; a slow or firewalled egress path costs the full **5 seconds** and then
the QR is dropped from the receipt anyway.

**The browser pays for the same fetches first.** The height measurement loads the real
receipt HTML into a hidden iframe and waits for everything in it:

```js
// POS/src/utils/printInvoice.js:130-140
const pending = [...frameDoc.images]
    .filter((img) => !img.complete)
    .map((img) => new Promise((done) => { ... }))
if (frameDoc.fonts?.ready) pending.push(frameDoc.fonts.ready)
await Promise.all(pending)
```

with a **5 second watchdog** at [printInvoice.js:119](../POS/src/utils/printInvoice.js#L119).
So per receipt the browser fetches the never-cacheable QR, the Google Fonts stylesheet, the
`.woff2` files, and the S3-proxied logo — and only then does the server repeat the QR fetch.

**And `wkhtmltopdf` fetches the fonts a third time.** `_inline_print_images`
([invoices.py:1708](../ecs_posnext/api/invoices.py#L1708)) rewrites `<img>` tags only; the
`<link>` to Google Fonts is left alone, so the PDF renderer goes out to the internet for it.
`load-error-handling: ignore` ([invoices.py:1810](../ecs_posnext/api/invoices.py#L1810))
prevents *failure*, not *waiting*.

> On a till behind a slow or filtered internet connection, cause **B** alone can be 5+ of the
> 7 seconds — and it is entirely avoidable, because none of these assets need to come from
> the internet.

### C — Work between submit and print that has nothing to do with printing

```js
// POS/src/pages/POSSale.vue:2001
await stockStore.refresh(soldItemCodes, shiftStore.profileWarehouse);

// POS/src/pages/POSSale.vue:2004
loadInvoiceHistoryData().catch(...)

// POS/src/pages/POSSale.vue:2013
const printResult = await autoPrintInvoice({ name: invoiceName }, ...);
```

The stock refresh is **awaited** before the print starts. It also awaits an IndexedDB worker
round trip and wraps its HTTP call in a 10 s `Promise.race`
([stock.js:125-136](../POS/src/stores/stock.js#L125-L136)). The cashier is waiting on paper;
the item grid's stock badge is not why.

The POS Profile fetch at [printInvoice.js:170](../POS/src/utils/printInvoice.js#L170) pulls
the whole profile document with all child tables on **every** sale, to read two fields
(`print_format`, `letter_head`).

And these fire unawaited at the same moment, competing for the same gunicorn workers that the
print calls need: `get_default_customer` (twice — once from `resetInvoice`, once from
`clearCart`), `cleanup_old_drafts`, and `get_invoices(limit=100)`. On a bench with few
workers, that directly delays stages 4–7.

### D — A third-party app doing accounting work inline

`ecs_heshamrabea` is installed on this site (confirmed in `sites/apps.txt`) and hooks **every**
Sales Invoice event, loading before `ecs_posnext`
(`apps/ecs_heshamrabea/ecs_heshamrabea/hooks.py:177-189`). Its `on_submit`:

```python
def on_submit(doc, method=None):
    create_extra_salary_components(doc)
    create_journal_entry_for_assistant(doc)
    create_journal_entry(doc)
    create_payment_entry_on_submit(doc)
```

That is up to four side documents, each a full insert + submit with its own validate and GL
entries — and `create_extra_salary_components` does
`frappe.get_doc("Item", item.item_code)` **inside the item loop**
(`doctype_triggers/accounting/sales_invoice/sales_invoice.py:150`), an uncached full document
load per line. A 20-line cart means 20 of those.

`before_validate` also monkey-patches `apply_discount_amount` globally and `validate` unpatches
it — a global patch flipped on every validate pass.

### E — N+1 query patterns inside submit

| Pattern | Location |
|---|---|
| One `Bin` query (or `get_batch_qty`) **per item row** | `_validate_stock_on_invoice` → [invoices.py:481-524](../ecs_posnext/api/invoices.py#L481-L524) |
| `db.get_value("Item", ..., "has_batch_no")` + `get_batch_qty` per row | [invoices.py:583](../ecs_posnext/api/invoices.py#L583) |
| Raw SQL join on `tabPOS Payment Method × tabPOS Profile`, ~8× for 2 payment modes | `get_payment_account` [invoices.py:283-341](../ecs_posnext/api/invoices.py#L283-L341) |
| Triple-nested N+1 + `get_balance_on` (heavy GL aggregate) on **every** validate pass | `get_pending_wallet_payments` [wallet.py:199-235](../ecs_posnext/api/wallet.py#L199-L235) |
| `db.get_value("Mode of Payment", ...)` per payment row | [overrides/sales_invoice.py:135-140](../ecs_posnext/overrides/sales_invoice.py#L135-L140) |

There is also **no `frappe.db.commit()`** anywhere in the POS submit path, so the whole thing
is one long transaction — row locks are held for the full duration, which matters when two
tills sell the same item at the same moment.

### F — Possibly one extra round trip per print job

If the POS is served over plain `http://` on a LAN IP, the browser does not expose
`crypto.subtle`, so key import fails
([qzTray.js:202-207](../POS/src/utils/qzTray.js#L202-L207)) and every signed QZ call falls
back to the server:

```js
// POS/src/utils/qzTray.js:280-284
const key = await getSigningKey(algorithm)
return key ? await signLocally(key, message) : await signOnServer(message, algorithm)
```

`signOnServer` is an HTTP round trip *inside* `qz.print`, and the server re-parses the PEM
private key on every call ([qz_signing.py:171-184](../ecs_posnext/api/qz_signing.py#L171-L184)).
See [QZ_TRAY_SIGNING.md](QZ_TRAY_SIGNING.md). Whether this applies to the slow till is a
one-line check — see the last section.

Two smaller till-side costs on the same stage: `qz-tray.js` computes a **pure-JS SHA hash over
the entire stringified request, including the full base64 PDF**, synchronously on the main
thread; and `printPDF` sends `rasterize: true`
([qzTray.js:616](../POS/src/utils/qzTray.js#L616)), so QZ Tray rasterizes the PDF at printer
DPI before spooling.

---

## What can be shortened

Ranked by saving ÷ risk. Target: **~7 s → ~2 s**, without touching accounting semantics.

| # | Change | Where | Saving | Risk |
|---|--------|-------|--------|------|
| 1 | Generate the QR **locally** (client-side lib, or server-side `qrcode` → data URI) instead of `api.qrserver.com`, and inline the two fonts as base64 `@font-face` in the print format | [fixtures/print_format.json](../ecs_posnext/fixtures/print_format.json), [invoices.py:1708](../ecs_posnext/api/invoices.py#L1708) | **1–4 s** | Low |
| 2 | Let `get_invoice_print_pdf` reuse the HTML the client already has (accept it as a parameter, or return the PDF from the same call that returns the HTML) so the format renders once | [invoices.py:1785](../ecs_posnext/api/invoices.py#L1785), [printInvoice.js:340-390](../POS/src/utils/printInvoice.js#L340-L390) | 0.2–0.5 s | Low |
| 3 | Move `stockStore.refresh` and `loadInvoiceHistoryData` to **after** `autoPrintInvoice`, or run them with `Promise.all` alongside it | [POSSale.vue:2001-2013](../POS/src/pages/POSSale.vue#L2001-L2013) | 0.1–1.0 s | Very low |
| 4 | Cache the POS Profile's `print_format` / `letter_head` in the shift store at shift open instead of fetching per sale | [printInvoice.js:165-186](../POS/src/utils/printInvoice.js#L165-L186) | 0.1–0.3 s | Very low |
| 5 | Collapse `update_invoice` + `submit_invoice` into one endpoint — removes one full save/validate pass and one whole-document round trip | [useInvoice.js:1019-1045](../POS/src/composables/useInvoice.js#L1019-L1045), [invoices.py:1328-1337](../ecs_posnext/api/invoices.py#L1328-L1337) | 0.4–1.0 s | Medium — the offline sync path shares `submit_invoice` and its `offline_id` dedup |
| 6 | Batch the per-item `Bin` lookups into one query; memoize `get_payment_account` per request | [invoices.py:481-524](../ecs_posnext/api/invoices.py#L481-L524), [invoices.py:283-341](../ecs_posnext/api/invoices.py#L283-L341) | 0.1–0.5 s | Low |
| 7 | Serve the till over HTTPS so QZ requests are signed in the browser | deployment | 0.1–0.3 s per print | Low, and fixes other things |
| 8 | Skip the height measurement when the receipt has no images left to wait for, or measure from a cached template rather than the live HTML | [printInvoice.js:97-159](../POS/src/utils/printInvoice.js#L97-L159) | 0.2–0.5 s | Low |

Items 1, 3 and 4 alone are low-risk and plausibly take the biggest bite. They are the place to
start.

---

## What cannot be shortened, and why

This is the part worth setting expectations on. Some of the 7 seconds is buying something.

**The PDF must be rendered server-side.** Printing the receipt as HTML through QZ Tray's own
renderer was tried and deliberately removed:

```js
// POS/src/utils/qzTray.js:644-646
// `format: "html"` pixel printing was removed on purpose: QZ Tray renders that
// HTML with its own engine, which does no complex-script shaping, so Arabic came
// out with unjoined letters in the wrong order. Receipts go through printPDF.
```

`wkhtmltopdf` is what makes Arabic come out correctly shaped and ordered. Its 0.4–2 s is the
price of a correct Arabic receipt, and no amount of caching removes it — the receipt content
is different every time.

**`rasterize: true` is needed for thermal heads.** Rasterize time scales with receipt length
and happens inside QZ Tray and the printer driver, not in our code. A long receipt is simply a
slower print. The only lever here is a shorter receipt.

**The submit work is ERPNext core.** The invoice carries `update_stock: 1`
([useInvoice.js:999](../POS/src/composables/useInvoice.js#L999)), so Stock Ledger Entries and
GL entries are written inside the submit transaction. That is not something to background:
doing so would break immediate stock accuracy, the return path, and the guarantee that a
submitted invoice is a complete accounting fact. Expect ~0.6–1.5 s here permanently.

**The third-party app's side documents are a business decision, not a technical one.**
`ecs_heshamrabea`'s Extra Salary rows and Journal Entries *could* be moved to a background
queue, which would cut real time — but that changes when those documents exist. That call
belongs to whoever owns that app and the accounting process, not to a performance fix. Worth
raising; not worth doing unilaterally. (The `frappe.get_doc("Item", ...)` inside the item loop
*is* a straightforward bug to fix there, independent of the queueing question.)

**Offline capability constrains some of the obvious caching.** The QZ signing key is handed to
the browser precisely so an offline till can still print silently
([QZ_TRAY_SIGNING.md](QZ_TRAY_SIGNING.md)); similarly, the receipt is rendered from the live
invoice rather than from a cached template because the totals must be exact.

**Realistic floor: ~1.5–2 seconds.** One invoice submit with stock and GL entries, one PDF
render, one QZ rasterize. Getting below that means changing what a receipt is (drop the logo,
drop the QR, shorter layout) or when the accounting happens (background the side documents) —
both are product decisions, not optimisations.

---

## Measure it before changing it

No timings have been captured on the slow till yet, and two of the stages are bounded by
network timeouts, so the same code can take 2 s or 7 s depending on the site's egress. Confirm
the split first — it decides whether cause **B** is 5 seconds or 0.5.

**1. Browser Network panel (the most informative single trace)**

On the till, open DevTools → Network, tick *Preserve log*, complete one sale, then read:

- the durations of `update_invoice`, `submit_invoice`, `get_stock_quantities`,
  `frappe.client.get`, `get_invoice_print_html`, `get_invoice_print_pdf`;
- the **gap** between `get_invoice_print_html` finishing and `get_invoice_print_pdf` starting —
  that gap *is* the iframe height measurement;
- whether `api.qrserver.com` and `fonts.googleapis.com` appear, and how long they take.
  If they are slow here, they are slow inside `get_invoice_print_pdf` too, where you cannot
  see them.

**2. Server-side query counts**

Enable Frappe's recorder (`/app/recorder` → Start), do one sale, stop it, and read the request
list. You are looking for the number of queries in `submit_invoice` (the N+1s in cause **E**
show up as dozens of near-identical `SELECT`s) and the duration of `get_invoice_print_pdf`.

**3. Is this till on HTTP? (cause F)**

In the till's browser console:

```js
window.isSecureContext   // false ⇒ QZ signing goes to the server, one round trip per print
```

and check the console log for either
`[QZTray] QZ Tray requests will be signed in the browser` (good) or
`Could not fetch QZ Tray signing material`.

**4. Isolate the printer**

Print the same receipt twice in a row from the invoice history. The second print skips nothing
server-side, but the fonts and logo will be browser-cached — if the second print is much
faster, cause **B** is confirmed on the client side. If both are equally slow, the weight is
in stages 7 and 8.

Record the numbers next to this document before opening a change, so the effect of each fix
is measurable rather than assumed.
