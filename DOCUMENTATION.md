# POS Next (ecs_posnext) — Documentation

Developer and functional documentation for **ecs_posnext**, the erpcloud.systems fork of BrainWise
"POS Next" for Frappe v15 / ERPNext v15 (license AGPL-3.0).

The upstream product provides a Vue 3, offline-first Point of Sale on top of ERPNext: cart, payments, offers,
coupons, wallet and loyalty, returns, shifts, and PWA support. This fork adds the client's branch operations:

- **Daily Payments** (advances, petty expenses, salary deductions) and **employee attendance** from the POS
- extra **closing-shift totals**: tips, daily payments, expected cash, Visa
- an automatic **cash sweep** to the branch-manager safe
- a **working day** that runs past midnight
- **correction tools** for drifted shift totals
- desk **reports runnable inside the POS**
- **QZ Tray** silent printing
- changing the mode of payment on submitted invoices

It works together with [ecs_heshamrabea](../ecs_heshamrabea/DOCUMENTATION.md), which owns `Daily Payment`,
the commission engine and the branch reports.

> Written from the source code as of 2026-11-02. When this file and `README.md` / `FEATURES.md` / `CHANGELOG.md`
> disagree, the code wins. Topic deep-dives that already existed are kept in [`docs/`](docs/README.md) and linked
> where relevant ([§11](#11-related-documents)).

## Contents

**Part I — Backend**
1. [Backend architecture](#1-backend-architecture)
2. [Backend API reference](#2-backend-api-reference)
3. [DocTypes](#3-doctypes)
4. [Shifts and closing](#4-shifts-and-closing)
5. [Reports in the POS](#5-reports-in-the-pos)
6. [Customizations and setup](#6-customizations-and-setup)

**Part II — Frontend**

7. [Frontend architecture](#7-frontend-architecture)
8. [Frontend stores, composables and utils](#8-frontend-stores-composables-and-utils)
9. [Frontend components](#9-frontend-components)

**Reference**

10. [Known issues](#10-known-issues)
11. [Related documents](#11-related-documents)

---

# Part I — Backend

## 1. Backend architecture

### 1.1 App identity

| Item | Value | Source |
|---|---|---|
| App name | `ecs_posnext` | `ecs_posnext/hooks.py` |
| Title / publisher | "POS Next" / BrainWise (upstream metadata kept) | `ecs_posnext/hooks.py` |
| Version | `1.15.0` (`__version__`) | `ecs_posnext/__init__.py` |
| Module | `POS Next` (single module) | `ecs_posnext/modules.txt` |
| Python | `>=3.10`, depends on `erpnext` | `pyproject.toml` |
| License | AGPL-3.0 | `license.txt` |

`ecs_posnext/__init__.py` also defines `console(*data)`. It publishes a `toconsole` realtime message to the current user, which is handy for debugging.

#### Runtime dependencies on other apps

`hooks.py` does not declare `required_apps`, but the code depends on these apps:

| App | What is used | Where |
|---|---|---|
| **erpnext** | Sales Invoice, POS Profile, Pricing Rule, Payment Entry, Loyalty, etc. | everywhere |
| **hrms** | `Employee`, `Attendance`, `Shift Type`, `Expense Claim Type` | `api/employee_attendance.py`, `api/daily_payment.py`, attendance correction doctype |
| **ecs_heshamrabea** (site-specific) | `Daily Payment` + `General Expenses` doctypes and the custom fields `Item.custom_not_included`, `Sales Person.custom_nickname`, `Payment Entry.custom_pos` / `custom_mode_of_payment_to`, `Shift Type.custom_default`, `Attendance.custom_branch` | `api/daily_payment.py`, `pos_closing_shift.py`, `api/items.py`, `api/pos_profile.py`, `api/employee_attendance.py` |
| **barcode_resolver** (optional) | weighted/priced barcode parsing | `services/barcode.py` |

The app will not run cleanly without `ecs_heshamrabea`. `api/items.py` selects `custom_not_included` unconditionally, and the closing shift sums `tabDaily Payment`. See [CUSTOMIZATIONS_AND_SETUP.md](#required-configuration).

---

### 1.2 Package layout

```
ecs_posnext/
├── __init__.py              # __version__, console()
├── hooks.py                 # all hook registrations (see §3)
├── install.py               # after_install / after_migrate
├── uninstall.py             # before_uninstall
├── utils.py                 # get_build_version(), get_app_version()
├── realtime_events.py       # Socket.IO emitters wired via doc_events (§4)
├── validations.py           # Item validate hook + Item standard query
├── working_day.py           # POS working-day window logic (+1 endpoint)
├── modules.txt / patches.txt
├── api/                     # whitelisted endpoints used by the POS (see §2)
│   ├── __init__.py          # imports submodules; ping()
│   ├── bootstrap.py         # get_initial_data – single startup call
│   ├── constants.py         # POS_SETTINGS_FIELDS, DEFAULT_POS_SETTINGS
│   ├── invoices.py          # draft/submit/print/return/payment-mode update (4.4k lines)
│   ├── items.py             # item catalogue, stock, barcode, variants
│   ├── shifts.py            # opening/closing shift endpoints
│   ├── daily_payment.py     # Daily Payment (ecs_heshamrabea doctype) from POS
│   ├── employee_attendance.py
│   ├── reports.py           # POS report runner
│   ├── customers.py, pos_profile.py, offers.py, promotions.py,
│   ├── credit_sales.py, partial_payments.py, wallet.py,
│   ├── localization.py, branding.py, qz_signing.py, utilities.py,
│   ├── offline_ops.py       # generic op_id idempotency layer
│   └── sales_invoice_hooks.py  # doc_event handlers for Sales Invoice
├── overrides/
│   ├── sales_invoice.py     # CustomSalesInvoice (override_doctype_class)
│   └── report.py            # POSReport (override_doctype_class)
├── services/
│   ├── __init__.py          # re-exports barcode helpers
│   └── barcode.py           # optional barcode_resolver integration
├── tasks/
│   ├── branding_monitor.py
│   └── cleanup_expired_promotions.py
├── patches/
│   ├── v1_7_0/reinstall_workspace.py
│   └── v1_15_0/item_child_links_ignore_user_permissions.py
├── fixtures/                # custom_field, role, custom_docperm, print_format
├── pos_next/                # the "POS Next" module
│   ├── doctype/             # 28 DocTypes (see §3)
│   ├── report/pos_closing_shift_(branch)/   # Query Report (see §5)
│   ├── workspace/posnext/posnext.json
│   └── page/test_page/      # empty dev page "test-page" (no roles)
├── templates/pages/         # empty package
├── translations/            # ar.csv, id.csv, pt-br.csv
├── www/pos.html             # SPA shell, generated by the Vite build
└── public/pos/              # built frontend assets (Vite outDir)
```

#### The SPA entry point

- `website_route_rules = [{"from_route": "/pos/<path:app_path>", "to_route": "pos"}]` sends every `/pos/...` URL to `www/pos.html`. Vue Router then handles the client-side route.
- `www/pos.html` is **generated** by the Vite build (`POS/vite.config.js`: `indexHtmlPath: "../ecs_posnext/www/pos.html"`, `outDir: "../ecs_posnext/public/pos"`). Do not hand-edit it, because the next `yarn build` overwrites it.
- The template loops over a Jinja `boot` variable (`{% for key in boot %}`), but the app has **no `www/pos.py`** to supply it. The loop renders nothing. The frontend gets its CSRF token from `ecs_posnext.api.utilities.get_csrf_token` and its startup data from `ecs_posnext.api.bootstrap.get_initial_data`. See [STARTUP_SEQUENCE.md](docs/STARTUP_SEQUENCE.md).
- `utils.get_build_version()` is evaluated into `_asset_version` in `hooks.py`. Every hook that would use it (`app_include_js/css`) is commented out, so at runtime it only feeds the version-control tooling. See [VERSION_CONTROL.md](docs/VERSION_CONTROL.md).

---

### 1.3 Hooks map (`ecs_posnext/hooks.py`)

#### 1.3.1 Fixtures

Exported and imported by `bench export-fixtures` / `bench migrate`:

| DocType | Filter | Records |
|---|---|---|
| Custom Field | `name in [...]` | 12 fields: Sales Invoice ×2, Item ×2, POS Profile ×3, Mode of Payment ×1, Selling Settings ×4 |
| Print Format | `name in ["POS Next Receipt"]` | 1 (Jinja, Sales Invoice) |
| Role | `role_name in ["POSNext Cashier"]` | 1 |
| Custom DocPerm | `role in ["POSNext Cashier"]` | 19 rows |

[CUSTOMIZATIONS_AND_SETUP.md](#6-customizations-and-setup) lists each field and permission.

> Fixture filters are an allow-list. A new custom field only ships if its name is added to the `Custom Field` filter in `hooks.py` **and** `bench export-fixtures` is re-run.

#### 1.3.2 Install / migrate / uninstall

| Hook | Function | What it does |
|---|---|---|
| `after_install` | `ecs_posnext.install.after_install` | Sets `print_format = "POS Next Receipt"` on every POS Profile that has none, clears cache, commits. Rolls back and re-raises on error. |
| `after_migrate` | `ecs_posnext.install.after_migrate` | Same as above (quiet), on every `bench migrate`. |
| `before_uninstall` | `ecs_posnext.uninstall.before_uninstall` | Deletes the custom fields `Sales Invoice-posa_pos_opening_shift` and `-posa_is_printed`, and `Item-custom_company` unless an app named `nexus` is installed. Clears `print_format` on POS Profiles that use "POS Next Receipt", then deletes that print format. |

Fixtures (custom fields, roles, docperms, print format) are synced by Frappe *before* `after_install` / `after_migrate` run. `install.py` itself creates nothing.

#### 1.3.3 `override_doctype_class`

| DocType | Class | File | Purpose |
|---|---|---|---|
| Sales Invoice | `CustomSalesInvoice(SalesInvoice)` | `overrides/sales_invoice.py` | (1) `set_pos_fields`: when the POS Profile has no `account_for_change_amount`, use the account of the profile's **own Cash mode of payment** instead of `Company.default_cash_account`. Change then lands in the branch till, not head office. (2) `make_pos_gl_entries`: re-implements ERPNext's POS GL entries so wallet modes (`Mode of Payment.is_wallet_payment = 1`) post `party_type=Customer` / `party=<customer>` on the receivable wallet account. It also handles `post_change_gl_entries`, which lives in Accounts Settings on v15 and POS Settings on v16. Both lookups are memoised on `frappe.local` per request. |
| Report | `POSReport(Report)` | `overrides/report.py` | Overrides `execute_query_report` to bind missing named SQL parameters before pymysql sees them. This applies to **every** Query Report on the site, desk included. Details in [REPORTS.md](#the-report-override). |

#### 1.3.4 `standard_queries`

```python
standard_queries = {"Item": "ecs_posnext.validations.item_query"}
```

This replaces the default link search for **every Item link field on the site**. It returns `name, item_name, item_group` for enabled items whose `item_code`/`item_name` matches. If `filters.company` is given, the results are restricted to items of that company plus "global" items (empty `custom_company`). All other filters passed to the query are ignored. See Known issues in [CUSTOMIZATIONS_AND_SETUP.md](#10-known-issues).

#### 1.3.5 `doc_events`

| DocType | Event | Handler(s) | Effect |
|---|---|---|---|
| Item | `validate` | `validations.validate_item` | For new items, stores `custom_company = ""` when blank (global item). |
| Customer | `after_insert` | `api.customers.auto_assign_loyalty_program`, `realtime_events.emit_customer_event` | Assigns the default loyalty program; broadcasts `pos_customer_changed` (`action: create`). |
| Customer | `on_update` | `realtime_events.emit_customer_event` | Broadcasts `pos_customer_changed` (`action: update`). |
| Customer | `on_trash` | `realtime_events.emit_customer_event` | Broadcasts `pos_customer_changed` (`action: delete`). |
| Sales Invoice | `validate` | `api.sales_invoice_hooks.validate`, `api.wallet.validate_wallet_payment` | Applies POS Settings `tax_inclusive` to tax rows (never to `Actual`) and recalculates totals if anything changed. Auto-assigns the default loyalty program to the customer. Throws if the wallet payment exceeds the wallet balance. |
| Sales Invoice | `before_cancel` | `api.sales_invoice_hooks.before_cancel` | Cancels the credit-redemption Journal Entries (`credit_sales.cancel_credit_journal_entries`). Errors are logged and never block the cancel. |
| Sales Invoice | `on_submit` | `realtime_events.emit_stock_update_event`, `api.wallet.process_loyalty_to_wallet` | Broadcasts `pos_stock_update`. Converts the earned loyalty points into a submitted Wallet Transaction when POS Settings enable `loyalty_to_wallet`. |
| Sales Invoice | `on_cancel` | `realtime_events.emit_stock_update_event` | Broadcasts `pos_stock_update` (`event_type: cancel`). |
| Sales Invoice | `after_insert` | `realtime_events.emit_invoice_created_event` | Broadcasts `pos_invoice_created` for `is_pos` invoices. |
| POS Profile | `on_update` | `realtime_events.emit_pos_profile_updated_event` | Broadcasts `pos_profile_updated` when `item_groups` changed. |

`api/sales_invoice_hooks.py` also contains `create_payment_entry_on_submit` and `cancel_payment_entries_on_cancel`. They create one Receive Payment Entry per payment row and cancel them again. They are **commented out** in `hooks.py`, so they are not active. The Payment Entry and the "CIB Visa commission" Journal Entry that `invoices.update_invoice_payment_mode` expects to reverse are created by hooks in another app (ecs_heshamrabea).

#### 1.3.6 `scheduler_events`

| Frequency | Task | What it does |
|---|---|---|
| hourly | `tasks.branding_monitor.monitor_branding_integrity` | If `BrainWise Branding` is enabled: sends a Notification Log to System Managers when `tampering_attempts > 50`, and logs an error if `encrypted_signature` is empty. |
| daily | `tasks.cleanup_expired_promotions.cleanup_expired_promotions` | Sets `disable = 1` on every Pricing Rule and Promotional Scheme whose `valid_upto < today`. This is site-wide and not limited to POS rules. |
| daily | `tasks.branding_monitor.validate_all_active_sessions` | Counts sessions active in the last 24 h and writes the count to the log. It enforces nothing. |
| monthly | `tasks.branding_monitor.reset_tampering_counter` | Logs and resets `BrainWise Branding.tampering_attempts` to 0. |

#### 1.3.7 Patches (`patches.txt`)

| Patch | Section | Effect |
|---|---|---|
| `patches.v1_7_0.reinstall_workspace` | post_model_sync | Meant to delete and re-insert the POSNext workspace from JSON. It looks in `<app>/ecs_posnext/workspace` and expects a JSON *list*, but the file is `pos_next/workspace/posnext/posnext.json` and holds a *dict*. **In practice it is a no-op.** The workspace is still synced by Frappe's normal module sync. |
| `patches.v1_15_0.item_child_links_ignore_user_permissions #2026-10-29` | post_model_sync | Adds Property Setters `ignore_user_permissions = 1` to every Account / Branch / Warehouse / Cost Center link field in `Item Default` and `Commission`. Without them, a branch-restricted cashier cannot read an Item whose defaults point at another branch, and `update_invoice` / `submit_invoice` fail with PermissionError on Item. Property Setters are used because migrate re-syncs Custom Field rows and would reset the flag. |

#### 1.3.8 Hooks deliberately not used

The following are not set: `app_include_js/css`, `doctype_js`, `boot_session`, `permission_query_conditions`, `has_permission`, `override_whitelisted_methods`, `on_session_creation`, `required_apps` and `add_to_apps_screen` (commented). Permission scoping for the POS is done **inside the endpoints**. See [API_REFERENCE.md](#permission-model).

---

### 1.4 Realtime events (`ecs_posnext/realtime_events.py`)

Every event is published with `frappe.publish_realtime(..., user=None, after_commit=True)`. It is broadcast to every connected client, and only after the transaction commits. Failures are logged to Error Log and never raise into the document transaction.

| Event | Fired by | Payload | Notes |
|---|---|---|---|
| `pos_stock_update` | Sales Invoice `on_submit` / `on_cancel` | `{invoice_name, warehouses[], stock_updates[{item_code, warehouse, actual_qty, stock_qty, ...}], timestamp, event_type: "submit"\|"cancel"}` | Only when `update_stock` and `is_pos`. Skips non-stock rows. Quantities come from `api.items.get_stock_quantities`, so they match the API. |
| `pos_invoice_created` | Sales Invoice `after_insert` | `{invoice_name, grand_total, customer, pos_profile, timestamp}` | `is_pos` only. Fires on the *draft* insert. |
| `pos_profile_updated` | POS Profile `on_update` | `{pos_profile, item_groups[{item_group}], timestamp, change_type: "item_groups_updated"}` | Only when `item_groups` changed. Clients invalidate their item cache. |
| `pos_customer_changed` | Customer `after_insert` / `on_update` / `on_trash` | `{name, customer_name, mobile_no, email_id, disabled, action: create\|update\|delete, timestamp}` | Keeps the offline customer cache in step. |
| `toconsole` | `ecs_posnext.console()` | arbitrary | Debug helper, sent to the current user only. |

Because these are broadcasts, every logged-in socket receives every branch's stock and customer changes. The frontend filters by warehouse and profile.

---

### 1.5 Services (`ecs_posnext/services/`)

`services/barcode.py` wraps the optional **barcode_resolver** app:

- `is_barcode_resolver_available()` checks `"barcode_resolver" in frappe.get_installed_apps()`. The result is cached with `lru_cache(maxsize=1)` for the life of the worker.
- `resolve_barcode(barcode, pos_profile)` loads `POS Settings` for the profile, takes the enabled rows of its `barcode_rules` child table (`POS Barcode Rules`) and calls `barcode_resolver...barcode_rule.utils.resolve_barcode`. It returns `None` when the app is missing or the barcode does not match.
- `compute_resolved_item_data(resolved, item)` turns a match into `{resolved_qty, resolved_uom, resolved_price, resolved_barcode_type}`. *Weighted* barcodes carry the quantity. *Priced* barcodes carry the price, and qty = price / UOM rate, using the UOM conversion factor when the barcode UOM has no price of its own.

It is used by `api.items.search_by_barcode`.

---

### 1.6 Other shared modules

| Module | Contents |
|---|---|
| `working_day.py` | Working-day window maths driven by `Selling Settings.posa_working_day_start_time/end_time`. See [SHIFTS_AND_CLOSING.md](#working-day-logic). Exposes `get_working_day_context`. |
| `validations.py` | `validate_item` (doc_event) and `item_query` (standard query). |
| `utils.py` | `get_build_version()`: `public/pos/version.json`, then the manifest mtime, then `__version__-<timestamp>`. Also `get_app_version()`. |
| `api/constants.py` | `POS_SETTINGS_FIELDS` (fields pushed to the client) and `DEFAULT_POS_SETTINGS`. |
| `api/utilities.py` | `get_csrf_token`, plus helpers `is_wallet_payment_mode()` and `get_wallet_payment_modes()` used across modules. |
| `api/offline_ops.py` | `ensure_op_once(op_id)` and `create_op_sync_record(...)`. This is the generic idempotency layer for queued offline writes; see [SHIFTS_AND_CLOSING.md](#offline-operations) and [OFFLINE_SYNC.md](docs/OFFLINE_SYNC.md). |

#### Request-level caching conventions

Several hot paths memoise on `frappe.local` so the three validate passes of a POS submit do not repeat queries:

- `frappe.local._ecs_posnext_post_change_gl_entries` and `_ecs_posnext_profile_cash_account` in `overrides/sales_invoice.py`.
- `frappe.local._ecs_pos_ctx_<profile>` (POS context: profile doc and POS Settings) is built in `api/invoices.py:_get_pos_context`. `sales_invoice_hooks` reads it to avoid re-fetching POS Settings.

---

### 1.7 Background jobs

| Enqueued from | Job | Queue | Work |
|---|---|---|---|
| `api.invoices.submit_invoice` | `api.invoices._post_submit_tasks` | `short` | Completes the Offline Invoice Sync record, redeems customer credit (Journal Entries), reverses wallet transactions for returns, and writes the audit comment for manually edited rates. |

Because of this job, the **Offline Invoice Sync row is marked complete asynchronously**. A client that re-checks `check_offline_invoice_synced` immediately after a dropped response may briefly see the record as Pending. See [OFFLINE_SYNC.md](docs/OFFLINE_SYNC.md).

---

### 1.8 Data flow at a glance

```
Browser (Vue SPA at /pos)  ──frappe-ui call──►  ecs_posnext.api.*  ──►  ERPNext doctypes
        ▲                                         │
        │   Socket.IO (pos_stock_update, ...)     ├─► POS Next doctypes (shifts, settings, sync, wallet …)
        └─────────── realtime_events.py ◄─────────┘   doc_events on Sales Invoice / Customer / POS Profile
```

- **Startup:** `bootstrap.get_initial_data` returns the open shift, POS Profile, POS Settings and payment methods.
- **Selling:** `invoices.update_invoice` saves the draft and `invoices.submit_invoice` submits it. The Sales Invoice is linked to the shift via `posa_pos_opening_shift`. See [PRICING_AND_SUBMISSION.md](docs/PRICING_AND_SUBMISSION.md).
- **Shift:** `shifts.create_opening_shift`, then `shifts.get_closing_shift_data`, then `shifts.submit_closing_shift`. See [SHIFTS_AND_CLOSING.md](#4-shifts-and-closing).

---

## 2. Backend API reference

Every `@frappe.whitelist()` method in `ecs_posnext`, grouped by module. Call them with `POST /api/method/<dotted path>`, or with `call("<dotted path>", {...})` from the Vue app.

Conventions used below:

- **Auth.** Every method requires a logged-in user unless it says `allow_guest`.
- **Used by.** `POS` means it is referenced from `POS/src`. `Desk` means it is called from a DocType form script under `pos_next/doctype/*/*.js`. `Internal` means it is called from other Python code. `—` means no caller was found in this repo (it may still be used by another app or by hand).
- **List / JSON params.** These may be sent as a JSON string. Every endpoint below `json.loads` string input where it expects a list or dict.
- **Errors.** `frappe.throw` returns HTTP 417 (`ValidationError`) or 403 (`PermissionError`) with `_server_messages`.
- Longer descriptions of the flows live in the topic documents linked in each section.

---

### Permission model

Whitelisted methods run as the session user, and Frappe does **not** apply DocType permissions to a whitelisted method by itself. Each endpoint decides what to check. The app uses these patterns:

| Pattern | Example | Meaning |
|---|---|---|
| Plain ORM (`frappe.get_list`, `doc.insert()`, `doc.save()`) | `get_employees`, `create_pos_profile` | Normal DocType permissions and User Permissions apply. |
| Explicit role guard | `frappe.only_for("System Manager")` in the correction doctypes; `_check_half_day_permitted()` | Hard role gate. |
| Profile-membership check | `POS Profile User` lookup in `pos_settings.get_pos_settings`, `shifts.get_last_closing_shift` | The user must be listed on the POS Profile. |
| `_check_invoice_access` (`api/invoices.py`) | `get_invoice`, `update_invoice_payment_mode` | DocType-level `read` on Sales Invoice plus Branch User Permission matching. It deliberately skips per-document checks because those would also validate unrelated Account links. |
| `ignore_permissions=True` writes | `create_opening_shift`, `submit_closing_shift`, `create_daily_payment`, `mark_employee_attendance`, `submit_invoice` | The write bypasses permissions. Whatever check the endpoint makes is the only gate. Several of these have no check at all; see [Known issues](#10-known-issues). |

---

### `ecs_posnext.api` (package `__init__`)

| Method | Params | Returns | Notes |
|---|---|---|---|
| `ecs_posnext.api.ping` | — | `"pong"` | `allow_guest=True`. Connectivity probe used by the offline detector. Used by: POS. |

### `ecs_posnext.api.utilities`

| Method | Params | Returns | Notes |
|---|---|---|---|
| `get_csrf_token` | — | `{csrf_token, session_id}` | Throws for Guest or disabled users. Used by: POS (startup, see [STARTUP_SEQUENCE.md](docs/STARTUP_SEQUENCE.md)). |

### `ecs_posnext.api.bootstrap`

| Method | Params | Returns | Notes |
|---|---|---|---|
| `get_initial_data` | — | `{success, site_name, locale, precision, shift\|None, pos_profile\|None, pos_settings\|None, payment_methods[]}` | One startup call. If the user has no open POS Opening Shift, `shift`, `pos_profile` and `pos_settings` are `None`. Throws `AuthenticationError` for Guest. Used by: POS. |

### `ecs_posnext.api.shifts`

Lifecycle details: [SHIFTS_AND_CLOSING.md](#4-shifts-and-closing).

| Method | Params | Returns | Permissions / side effects | Used by |
|---|---|---|---|---|
| `get_opening_dialog_data` | — | `{pos_profiles_data[], companies[], payments_method[]}` | Only enabled profiles where the user is in `POS Profile User`. Wallet modes are excluded from the opening balance. Payment rows are read with `ignore_permissions`. | POS |
| `check_opening_shift` | `user=None` | `None` or `{pos_opening_shift, pos_profile, company, server_now}` (full docs) | Accepts any `user`, with no check that it is the caller. | POS |
| `get_shift_invoices` | `pos_profile=None, pos_opening_shift=None, limit=10` | `{pos_opening_shift, invoices[]}` with `mode_of_payment` added | Latest POS invoices of the given or last open shift. The caller's own shift is preferred, then the profile's. An explicit `pos_opening_shift` is not checked against the caller. | POS |
| `create_opening_shift` | `pos_profile, company, balance_details (JSON list of {mode_of_payment, opening_amount}), op_id=None, period_start_date=None` | `{name, pos_opening_shift, pos_profile, company}` | Idempotent via `op_id` (`open_shift`). Throws if the user already has an open shift. A UTC `period_start_date` (ISO with `Z`) is converted to system time. `insert(ignore_permissions)` and then `submit()`. | POS |
| `get_closing_shift_data` | `opening_shift` | Closing Shift dict plus `returns_total, returns_count, sales_total, sales_count`, and `pos_transactions` with `is_return` / `return_against` | Wraps `pos_closing_shift.make_closing_shift_from_opening`. **Side effect:** submits any draft invoices of the shift that have `posa_is_printed = 1`. | POS |
| `submit_closing_shift` | `closing_shift (JSON dict), op_id=None` | `{name, status: "success"}` | Idempotent via `op_id` (`close_shift`). Throws `SYNC_IN_PROGRESS: ...` if the referenced opening shift does not exist yet, so the client retries. Saves and submits with `ignore_permissions`, then runs the auto cash transfer. | POS |
| `get_last_closing_shift` | `pos_profile=None` | Latest submitted closing `{name, pos_profile, user, period_start_date, period_end_date, posting_date, grand_total}` or `None` | Limited to profiles the user is assigned to. The user's own closing is preferred. | POS |

### `ecs_posnext.api.invoices`

Draft and submit flow: [PRICING_AND_SUBMISSION.md](docs/PRICING_AND_SUBMISSION.md). Offline deduplication: [OFFLINE_SYNC.md](docs/OFFLINE_SYNC.md). Receipt rendering: [PRINT_LATENCY_ANALYSIS.md](docs/PRINT_LATENCY_ANALYSIS.md).

#### Selling

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `validate_cart_items` | `items (JSON), pos_profile=None` | `[ {item_code, requested, available, ...} ]` rows that exceed stock | Pre-submit stock check. | POS |
| `update_invoice` | `data (JSON Sales Invoice dict)` | Saved draft `as_dict()` | Step 1: create or update the draft. Sets `is_pos`, `update_stock` and payment accounts. | POS |
| `submit_invoice` | `invoice (JSON), data (JSON)` (also accepts everything nested inside `data`) | `{name, status, grand_total, total, net_total, outstanding_amount, paid_amount, change_amount, offline_id?}` | Step 2. Handles `offline_id` dedup (an already-synced id returns the stored invoice data), sales team, POS Coupon usage, return batches, the write-off limit and stock validation (unless POS Settings `allow_negative_stock`). Saves and submits with `ignore_permissions` and `ignore_account_permission`. Enqueues `_post_submit_tasks` on the `short` queue. | POS |
| `check_offline_invoice_synced` | `offline_id` | `{synced, sales_invoice}` | Pre-sync dedup probe. | POS |
| `apply_offers` | `invoice_data (JSON), selected_offers=None` | `{items[], free_items[], applied_pricing_rules[]}` | Runs ERPNext Pricing Rules on the cart. See [OFFERS_AND_PROMOTIONS.md](docs/OFFERS_AND_PROMOTIONS.md). | POS |

#### History / lookup

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `get_invoices` | `pos_profile, limit=100` | list of invoice summaries | Requires Sales Invoice read or profile membership. | POS |
| `get_invoice` | `invoice_name` | full invoice `as_dict()` | `_check_invoice_access`. | POS |
| `get_invoice_payment_modes` | `invoice_names (JSON list)` | `{invoice: "Cash, Visa"}` | For the history list. | POS |
| `get_draft_invoices` | `pos_opening_shift, doctype="Sales Invoice"` | drafts of the shift | | — |
| `delete_invoice` | `invoice` | message string | Drafts only. `frappe.delete_doc(force=1)` is permission-checked. | — |
| `cleanup_old_drafts` | `pos_profile=None, max_age_hours=24` | `{deleted, message}` | Deletes up to 100 draft Sales Invoices older than N hours with `ignore_permissions`. There is no `is_pos` filter and no role check. | POS |

#### Printing

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `get_invoice_print_html` | `invoice_name, print_format=None, letterhead=None, no_letterhead=0, trigger_print=0, inline_assets=0` | `{html, style, ...}` | Uses the "POS Next Receipt" format by default. | POS |
| `get_invoice_print_pdf` | `invoice_name, print_format=None, letterhead=None, no_letterhead=1, page_width=None, page_height=None, side_margin=None` | `{filename, content (base64), page_width, page_height}` | wkhtmltopdf. A roll width gives a thermal receipt; no width gives A4. | POS |
| `get_receipt_pdf` | `invoice_name, print_format=None, letterhead=None, no_letterhead=1, page_width=None, side_margin=None` | same shape as above | Single-call receipt that estimates the page height on the server. | POS |

#### Returns

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `validate_return_items` | `original_invoice_name, return_items, doctype="Sales Invoice"` | `{valid, message?}` | Quantity and validity-days check. | — |
| `get_returnable_invoices` | `limit=50, pos_profile=None` | list | Invoices that still have returnable qty. | POS |
| `search_invoice_by_number` | `search_term (min 3 chars), pos_profile=None` | up to 10 invoices | | POS |
| `search_invoices_for_return` | `invoice_name, company, customer_name, customer_id, mobile_no, from_date, to_date, min_amount, max_amount, page=1, doctype` | `{invoices[], has_more}` | | — |
| `check_invoice_return_validity` | `invoice_name` | `{valid, error_type?, invoice_date?, days_since?, allowed_days?}` | Uses POS Settings `return_validity_days`. | POS |
| `get_invoice_for_return` | `invoice_name` | invoice dict with remaining qty per item | | — |
| `prepare_return_invoice` | `invoice_name, pos_opening_shift=None` | return invoice dict (built by ERPNext `make_sales_return`) | | POS |
| `process_return_by_cancel` | `invoice_name, returned_items (JSON [{sales_invoice_item, return_qty}]), pos_opening_shift=None, pos_profile=None, return_reason=None` | `{cancelled_invoice, new_invoice, has_remaining_items}` | Cancels the original and re-issues the remaining lines as a new invoice. | POS |

#### Mode-of-payment correction (fork feature)

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `get_payment_mode_update_options` | `invoice_name` | `{invoice, currency, grand_total, paid_amount, allowed, blocker, current_modes[], modes[{mode_of_payment, account, type}]}` | `blocker` is a translated reason when the update is not allowed (draft, return, consolidated, partly paid, loyalty, wallet, already returned or amended, not in the caller's open shift). | POS |
| `update_invoice_payment_mode` | `invoice_name, mode_of_payment` | `{cancelled_invoice, new_invoice, mode_of_payment, amount}` | Cancels the invoice, which lets other apps' `on_cancel` hooks reverse the Payment Entry and the CIB commission JE. Then submits an amendment with one payment row. The whole correction rolls back if a linked Payment Entry or a JE with `custom_sales_invoice` survives. Cashiers are limited to their own open shift; Administrator is exempt. See CHANGELOG "Correct the Mode of Payment". | POS |

### `ecs_posnext.api.items`

Catalogue loading strategy: [LARGE_CATALOG_OPTIMIZATION.md](docs/LARGE_CATALOG_OPTIMIZATION.md).

| Method | Params | Returns | Used by |
|---|---|---|---|
| `get_items` | `pos_profile, search_term=None, item_group=None, start=0, limit=20, include_variants=0` | list of items with price, stock, UOM prices, barcodes | POS |
| `get_items_bulk` | `pos_profile, item_groups=None (JSON), start=0, limit=2000, include_variants=0` | items from many groups in one query | POS |
| `get_items_count` | `pos_profile, item_group=None, include_variants=0` | int | POS |
| `get_item_details` | `item_code, pos_profile, customer=None, qty=1, uom=None` | ERPNext `get_item_details` result | POS |
| `get_item_groups` | `pos_profile` | profile item groups with hierarchy (cached) | POS |
| `get_item_variants` | `template_item, pos_profile` | variants with price and stock | POS |
| `search_by_barcode` | `barcode, pos_profile` | item details plus `resolved_*` from barcode_resolver when installed | POS |
| `get_item_stock` | `item_code, warehouse` | `{item_code, warehouse, stock_qty, reserved_qty, available_qty}` | — |
| `get_stock_quantities` | `item_codes (JSON), warehouse` | `[{item_code, warehouse, actual_qty, stock_qty, ...}]` (also used by realtime) | POS, Internal |
| `get_item_warehouse_availability` | `item_code=None, item_codes=None, company=None` | per-warehouse stock | POS |
| `get_product_bundle_availability` | `item_code, warehouse` | `{available_qty, components[]}` | — |
| `get_batch_serial_details` | `item_code, warehouse` | batches and serials | — |
| `get_batch_serial_data_for_items` | `item_codes (JSON), warehouse` | `{item_code: {batches, serials}}` for the offline cache | POS |

`api/items.py` reads `Item.custom_not_included` (an ecs_heshamrabea custom field) in its base column list.

### `ecs_posnext.api.pos_profile`

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `get_pos_profiles` | — | profiles the user is assigned to | | POS |
| `get_pos_profile_data` | `pos_profile` | `{pos_profile, company, pos_settings, item_groups_hierarchy, print_settings}` | | POS |
| `get_pos_settings` | `pos_profile` | POS Settings subset (`POS_SETTINGS_FIELDS`) or `DEFAULT_POS_SETTINGS` | Not the same function as `pos_settings.get_pos_settings`. | — |
| `get_payment_methods` | `pos_profile` | payment rows with account, type and wallet flag | | POS |
| `get_taxes` | `pos_profile` | rows of the profile's Sales Taxes template | | POS |
| `get_warehouses` | `pos_profile` | company warehouses | | POS |
| `get_default_customer` | `pos_profile` | `{customer, customer_name, customer_group}` | | POS |
| `update_warehouse` | `pos_profile, warehouse` | `{success, message, warehouse}` | Profile member or POS Profile write. Saves the POS Profile. | POS |
| `get_wallet_payment_flags` | `methods (JSON list)` | `{mode: is_wallet_payment}` | | POS |
| `get_sales_persons` | `pos_profile=None` | active individual Sales Persons with `custom_nickname` | Hides Sales Persons whose Employee is not Active. Hides "craftsmen" (designation `صنايعى`) whose attendance for the running shift does not put them on shift. Errors are swallowed and return `[]`. | POS |
| `get_create_pos_profile` | — | selection lists for the profile wizard | | — |
| `create_pos_profile` | kwargs (`__newname, currency, warehouse, payments, write_off_*`, ...) | POS Profile doc | Standard insert permission. | — |
| `update_pos_profile` | kwargs (`pos_profile`, ...) | POS Profile doc | Standard save permission. | — |
| `delete_pos_profile` | `pos_profile` | — | Standard delete permission. | — |

### `ecs_posnext.api.customers`

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `get_customers` | `search_term="", pos_profile=None, limit=20, modified_since=None` | `[{name, customer_name, mobile_no, email_id, disabled, ...}]` | Filtered by the profile's customer groups. `modified_since` is used for delta sync. | POS |
| `create_customer` | `customer_name, mobile_no=None, email_id=None, customer_group="أفراد", territory="All Territories", company=None, op_id=None` | Customer `as_dict()` | Requires Customer create. Idempotent via `op_id`. The default customer group is hard-coded to `أفراد`. | POS |
| `get_customer_details` | `customer` | Customer `as_dict()` | | — |

`customers.auto_assign_loyalty_program(doc, method)` is a doc_event, not an endpoint.

### `ecs_posnext.api.credit_sales`

| Method | Params | Returns | Used by |
|---|---|---|---|
| `get_customer_balance` | `customer, company=None` | `{total_outstanding, total_credit, net_balance}` | POS |
| `get_available_credit` | `customer, company, pos_profile=None` | list of credit sources (negative-outstanding invoices, unallocated advances) | POS |
| `redeem_customer_credit` | `invoice_name, customer_credit_dict (JSON)` | list of created Journal Entry names | Internal (`_post_submit_tasks`) |
| `cancel_credit_journal_entries` | `invoice_name` | cancelled count | Internal (`before_cancel`) |
| `get_credit_sale_summary` | `pos_profile` | `{count, total_outstanding, total_amount, total_paid}` | — |
| `get_credit_invoices` | `pos_profile, limit=100` | invoices with outstanding | — |

`redeem_customer_credit` and `cancel_credit_journal_entries` are whitelisted but have no ownership check. They create or cancel Journal Entries with `ignore_permissions`.

### `ecs_posnext.api.partial_payments`

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `get_partial_paid_invoices` | `pos_profile, limit=50 (max 500)` | invoices with payment history | | POS |
| `get_unpaid_invoices` | `pos_profile, limit` | partial and fully unpaid invoices | | POS |
| `get_partial_payment_details` | `invoice_name` | invoice, items and payment history | Per-document read check. | POS |
| `add_payment_to_partial_invoice` | `invoice_name, payments (JSON [{mode_of_payment, amount, account?}])` | result with created Payment Entries | Per-document write check. Creates Payment Entries and cancels the ones already created if a later one fails. Commits. | POS |
| `get_partial_payment_summary` | `pos_profile` | `{count, total_outstanding, total_paid, total_grand_total}` | | POS |
| `get_unpaid_summary` | `pos_profile` | same shape | | POS |

### `ecs_posnext.api.wallet` and wallet doctypes

Full design: [Wallet-System-Technical-Guide.md](docs/Wallet-System-Technical-Guide.md).

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `api.wallet.get_wallet_info` | `customer, company, pos_profile=None` | `{wallet_enabled, wallet_exists, wallet_balance, wallet_name, auto_create, loyalty_program, loyalty_to_wallet}` | | POS |
| `api.wallet.get_customer_wallet_balance` | `customer, company=None, exclude_invoice=None` | float | | — (Internal) |
| `api.wallet.get_customer_wallet` | `customer, company=None` | wallet dict | | — |
| `api.wallet.get_or_create_wallet` | `customer, company, pos_settings=None` | wallet | Inserts with `ignore_permissions`. | — (Internal) |
| `api.wallet.get_wallet_payment_methods` | `pos_profile` | wallet modes of the profile | | — |
| `api.wallet.create_manual_wallet_credit` | `customer, company, amount, remarks=None` | Wallet Transaction name | Requires Wallet Transaction create. | — |
| `pos_next.doctype.wallet.wallet.get_customer_wallet` / `get_customer_wallet_balance` / `get_or_create_wallet` / `create_customer_wallet` | as named | | Older duplicates of the API module. | — |
| `pos_next.doctype.wallet_transaction.wallet_transaction.create_wallet_credit` | `wallet, amount, source_type="Manual Adjustment", remarks, reference_doctype, reference_name, submit=True` | Wallet Transaction | **No permission check**: `insert(ignore_permissions)` and then submit. | Internal |
| `...wallet_transaction.credit_loyalty_points_to_wallet` | `customer, company, loyalty_points, conversion_factor=None` | Wallet Transaction | No permission check. | — |
| `...wallet_transaction.reverse_wallet_transactions_for_return` | `original_invoice, return_invoice` | reversed transactions | | Internal |

### `ecs_posnext.api.offers` / `ecs_posnext.api.promotions`

See [OFFERS_AND_PROMOTIONS.md](docs/OFFERS_AND_PROMOTIONS.md) for behaviour.

| Method | Params | Returns | Permissions | Used by |
|---|---|---|---|---|
| `offers.get_offers` | `pos_profile` | auto-applicable offers | | POS |
| `offers.get_active_coupons` | `customer, company` | gift-card coupons | | POS |
| `offers.validate_coupon` | `coupon_code, customer, company` | `{valid, coupon?, message?}` | | POS |
| `promotions.get_promotions` | `pos_profile=None, company=None, include_disabled=False` | schemes and standalone pricing rules | Promotional Scheme read | POS |
| `promotions.get_promotion_details` | `scheme_name` | detail | read | POS |
| `promotions.create_promotion` / `update_promotion` / `toggle_promotion` / `delete_promotion` | `data` / `scheme_name, data` / `scheme_name, disable` / `scheme_name` | `{success, message, ...}` | write / write / write / delete | POS |
| `promotions.get_item_groups` / `get_brands` | `company=None` / — | lists | | POS |
| `promotions.search_items` | `search_term, pos_profile=None, limit=20` | items | | — |
| `promotions.get_coupons` / `get_coupon_details` | filters / `coupon_name` | POS Coupons | read | POS |
| `promotions.create_coupon` / `update_coupon` / `toggle_coupon` / `delete_coupon` | `data` / `coupon_name, data` / `coupon_name, disabled` / `coupon_name` | `{success, ...}` | write / write / write / delete | POS |
| `promotions.apply_referral_code` | `referral_code, customer` | `{success, message, referrer_coupon, referee_coupon}` | | — |
| `promotions.get_referral_codes` / `get_referral_details` | `company, include_disabled` / `referral_name` | Referral Codes | read | — |

### `ecs_posnext.api.daily_payment` (fork feature)

Operates on the **`Daily Payment`** doctype from ecs_heshamrabea. See [SHIFTS_AND_CLOSING.md](#daily-payments).

| Method | Params | Returns | Permissions / side effects | Used by |
|---|---|---|---|---|
| `employee_query` | link-query signature (`doctype, txt, searchfield, start, page_len, filters{branch}`) | `[(name, employee_name)]` | Raw SQL over active Employees, no permission filtering. | POS |
| `get_branch_balance` | `branch` | `{branch, account, balance, currency}` | GL balance of the hard-coded account `صندوق عمولات المساعدين - HR` for the branch. No permission check. | POS |
| `get_daily_payments` | `employee=None, from_date=None, to_date=None, branch=None, limit=50` | Daily Payment rows plus `expenses_amount` | `frappe.get_list` (permission-checked). Dates are calendar dates. | POS |
| `get_invoice_counts` | `branch=None, from_date=None, to_date=None, pos_opening_shift=None` | `{cash, visa, total, visa_amount}` | Needs Sales Invoice read and, when given, a Branch User Permission. The dates are **working days** (see `working_day.py`). An invoice split across cash and card counts in both buckets. `visa_amount` sums the non-cash payment rows. | POS |
| `get_daily_payment_detail` | `name` | Daily Payment `as_dict()` | `frappe.get_doc` without a permission check. | — |
| `get_cash_mode_of_payment` | `pos_opening_shift=None, modes=None (JSON)` | Cash-type mode name or `None` | | POS |
| `create_daily_payment` | `date, branch, employee, amount, mode_of_payment, payment_to_employees=0, expenses=0, loan_product, general_expenses (JSON [{expense_claim_type, amount, description}]), pos_opening_shift, deduction=0, salary_component, op_id` | `{name, status: "submitted"}` | Idempotent via `op_id` (`daily_payment`). The mode of payment is forced to the shift profile's Cash mode, except for deductions. `insert(ignore_permissions)`, submit, commit. | POS |

### `ecs_posnext.api.employee_attendance` (fork feature)

See [SHIFTS_AND_CLOSING.md](#employee-attendance).

| Method | Params | Returns | Permissions / side effects | Used by |
|---|---|---|---|---|
| `get_attendance_date` | `shift=None, for_timestamp=None` | `"YYYY-MM-DD"` | Business date: the previous day while an overnight shift that started yesterday is still running. | Internal |
| `get_shift_types` | — | `{shift_types[], default_shift, last_shift, business_date, server_date}` | `last_shift` is an alias kept for old bundles. | POS |
| `get_employees` | `date, company=None, branch=None` | `{marked[], unmarked[]}` | `frappe.get_list` on Employee and Attendance. Needs the POSNext Cashier read docperms. | POS |
| `mark_employee_attendance` | `employee_list (JSON), status ∈ {Present, Absent, Half Day}, date, company=None, shift (ignored), branch=None, op_id=None` | `None` | The shift is always `get_default_shift()`. Employees who already have attendance for the date are skipped. Writes `Attendance.custom_branch` when that field exists. `insert(ignore_permissions)`, submit, commit. No role check. | POS |
| `convert_attendance_to_half_day` | `employee_list (JSON), date, reason ∈ {early_exit, late_entry}, company=None, branch=None, op_id=None` | `{updated[], skipped[], already_synced?}` | Role gate: POSNext Cashier or System Manager. Cancels the submitted record and submits an amendment with `status = Half Day` and `late_entry` / `early_exit` set. Adds a comment. Commits. | POS |

### `ecs_posnext.api.reports` (fork feature)

See [REPORTS.md](#5-reports-in-the-pos).

| Method | Params | Returns | Used by |
|---|---|---|---|
| `get_pos_reports` | `pos_profile=None` | `[{report, label, icon, report_type, ref_doctype, can_export}]` | POS |
| `get_report_definition` | `report_name, pos_profile=None` | `{report, label, icon, report_type, ref_doctype, add_total_row, can_export, filters[], print_layouts[]}` | POS |
| `run_pos_report` | `report_name, filters (JSON)=None, pos_profile=None` | `{filters (as applied), columns, result, message, report_summary, skip_total_row, add_total_row, execution_time}` | POS |
| `render_report_print` | `report_name, print_layout=None, filters=None, orientation="Portrait", with_letterhead=0, pos_profile=None` | full HTML page (string) | POS |
| `get_print_template` | `report_name, print_layout=None, pos_profile=None, with_letterhead=0` | `{layout, template, template_type: "JS"\|"Jinja", letterhead}` | POS |
| `search_filter_options` | `doctype, txt="", filters=None, page_length=20` | `[{value, description}]` (wraps `frappe.desk.search.search_link`) | POS |

### `ecs_posnext.api.offline_ops`

| Method | Params | Returns | Used by |
|---|---|---|---|
| `is_op_synced` | `op_id` | `{synced, ref_doctype, ref_name, status}` | POS |

Op types in use: `open_shift`, `close_shift`, `daily_payment`, `attendance`, `attendance_half_day`, `customer`.

### `ecs_posnext.api.localization`

See [LOCALIZATION.md](docs/LOCALIZATION.md).

| Method | Params | Returns | Used by |
|---|---|---|---|
| `get_app_translations` | — | `{source: translation}` for the user's language | POS |
| `get_user_language` | — | `{success, locale}` | POS |
| `get_allowed_locales` | — | `{success, locales[]}` (union of POS Settings `allowed_locales`) | POS |
| `change_user_language` | `locale` | `{success, message, locale}` (updates `User.language`, commits) | POS |

### `ecs_posnext.api.qz_signing`

See [QZ_TRAY_SIGNING.md](docs/QZ_TRAY_SIGNING.md).

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `get_signing_material` | — | `{certificate, private_key?}` | The private key is omitted when `qz_tray_server_side_signing` is set in site_config. Otherwise **any logged-in user** receives it. | POS |
| `sign_message` | `request, algorithm="SHA512"` (`SHA1`, `SHA256` or `SHA512`) | base64 signature | | POS |
| `download_certificate` | — | file download `override.crt` | System Manager only. | — |

### `ecs_posnext.api.branding` and `BrainWise Branding`

Upstream anti-tampering for the "Powered by BrainWise" footer.

| Method | Params | Returns | Used by |
|---|---|---|---|
| `api.branding.get_branding_config` | — | obfuscated config | POS |
| `api.branding.validate_branding` | `client_signature, brand_name, brand_url` | `{valid, timestamp, message}`; increments `tampering_attempts` on mismatch | POS |
| `api.branding.log_client_event` | `event_type, details` | `{logged, message}` | POS |
| `api.branding.get_tampering_stats` | — | `{enabled, tampering_attempts, last_validation, server_validation}` (System Manager) | Desk |
| `pos_next.doctype.brainwise_branding.brainwise_branding.get_branding_config` / `validate_branding` / `log_client_event` | same as above | duplicates | — |
| `...brainwise_branding.verify_master_key` | `master_key_input` | verification result (System Manager) | Desk |
| `...brainwise_branding.generate_new_master_key` | — | new key pair (System Manager) | — |

### `ecs_posnext.working_day`

| Method | Params | Returns | Used by |
|---|---|---|---|
| `get_working_day_context` | `day=None, at=None` | `{enabled, start_time, end_time, crosses_midnight, working_day, opens_at, closes_at, from_datetime, to_datetime}` | POS (closing dialog, Track Invoices) |

### `ecs_posnext.validations`

| Method | Params | Returns | Notes |
|---|---|---|---|
| `item_query` | link-query signature | `[(name, item_name, item_group)]` | Registered as the site-wide `standard_queries["Item"]`. `searchfield` is interpolated into the SQL. |

### `ecs_posnext.pos_next.doctype.pos_settings.pos_settings`

| Method | Params | Returns | Permissions |
|---|---|---|---|
| `get_pos_settings` | `pos_profile` | all POS Settings fields plus `_global_allow_negative_stock`; **creates** default settings if none exist | Profile member or POS Settings read |
| `update_pos_settings` | `pos_profile, settings (JSON)` | POS Settings dict | Profile member **or** POS Settings write. `doc.save()` is still permission-checked, and POSNext Cashier has POS Settings write via the docperm fixture. |

### `ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift`

Desk form helpers and the closing engine. See [SHIFTS_AND_CLOSING.md](#closing-shift).

| Method | Params | Returns | Notes | Used by |
|---|---|---|---|---|
| `make_closing_shift_from_opening` | `opening_shift (JSON doc)` | unsaved closing dict plus display totals | Submits printed drafts first. | Internal (shifts) |
| `submit_closing_shift` | `closing_shift (JSON doc)` | closing name | Save and submit with `ignore_permissions`, then auto cash transfer. | Internal (shifts) |
| `get_pos_invoices` | `pos_opening_shift, doctype=None` | submitted invoices (full dicts) of the shift | **Side effect:** submits drafts with `posa_is_printed = 1`. | Desk |
| `get_payments_entries` | `pos_opening_shift` | Receive Payment Entries with `reference_no = shift` | | Desk |
| `get_opening_shift_totals` | `pos_opening_shift` | `{total_daily_payments, total_tip}` | | Desk |
| `get_cashiers` | link-query signature | `[[user, "user (email)"]]` from `POS Profile User` | | Desk |
| `POSClosingShift.get_payment_reconciliation_details` | (doc method via `frm.call`) | rendered HTML (`closing_shift_details.html`) | | Desk |

### Correction doctypes (fork features, System Manager only)

See [SHIFTS_AND_CLOSING.md](#corrections).

| Method | Params | Returns |
|---|---|---|
| `pos_next.doctype.pos_daily_payments_correction.pos_daily_payments_correction.get_problem_shifts` | `branch=None, pos_closing_shift=None` | rows of drifted shifts |
| `...pos_daily_payments_correction.problem_shift_query` | link-query signature | `[[name, "branch \| fields"]]` |
| `...pos_daily_payments_correction.apply_corrections` | `shifts (JSON [{pos_closing_shift, apply}])` | `{updated[], skipped[]}` |
| `pos_next.doctype.pos_closing_shift_daily_payment_update.pos_closing_shift_daily_payment_update.affected_closing_shift_query` | link-query signature | `[[name, branch, current, correct]]` |
| `POSClosingShiftDailyPaymentUpdate.fetch_affected_shifts` | doc method | count (fills the child table and saves) |
| `POSClosingShiftDailyPaymentUpdate.update_total_daily_payments` | doc method | number of shifts updated |
| `pos_next.doctype.pos_attendance_shift_correction.pos_attendance_shift_correction.get_target_shift` | — | default Shift Type |
| `...pos_attendance_shift_correction.get_attendance_to_correct` | `from_date, to_date, only_missing_shift=1` | rows |
| `...pos_attendance_shift_correction.apply_corrections` | `records (JSON [{attendance, apply}])` | `{updated[], skipped[]}` |

---

## 3. DocTypes

All DocTypes are in module **POS Next**, under `ecs_posnext/pos_next/doctype/`. The `Daily Payment`, `Extra Salary`
and `Item Sorting` DocTypes used by the POS belong to `ecs_heshamrabea`.

| DocType | Type | Naming | Roles | Purpose |
|---|---|---|---|---|
| POS Opening Shift | submittable | `POSA-OS-.YY.-.#######` (site override: `{OP}-{posting_date}-{pos_profile}-{##}`) | POSNext Cashier, Sales Manager, System Manager | Cash-drawer opening per user + POS Profile |
| POS Closing Shift | submittable | `POSA-CS-.YY.-.#######` (site override: `{CL}-…`) | POSNext Cashier, Sales Manager, System Manager | Shift close and reconciliation |
| POS Settings | per profile | hash | POSNext Cashier, Sales Manager/User, System Manager | Feature switches for one POS Profile |
| POS Report Settings | single | | POSNext Cashier, Sales Manager/User, System Manager | Which reports the POS lists, per profile |
| POS Offer | master | `title` | Sales/Accounts roles | Upstream offers engine |
| POS Coupon | master | `coupon_name` | Accounts User, Sales Manager, Website Manager | Coupons (promotional, gift card, referral) |
| Referral Code | master | `referral_name` | as above | Generates referrer and referee coupons |
| Wallet | master | `{customer}-WALLET` | Accounts Manager, POS User, Sales User | Customer wallet balance |
| Wallet Transaction | submittable | `WT-.YYYY.-` | Accounts Manager/User | Wallet credit/debit with GL entries |
| Offline Invoice Sync | log | hash | POSNext Cashier, Sales User | `offline_id` → Sales Invoice dedup record |
| Offline Operation Sync | log | hash | POSNext Cashier, Sales User | `op_id` → document dedup for non-invoice offline ops |
| BrainWise Branding | single | | Sales Manager/User | Upstream "Powered by" anti-tamper settings |
| POS Daily Payments Correction | single (tool) | | System Manager | Recompute drifted shift totals |
| POS Closing Shift Daily Payment Update | document (tool) | `POS-CS-DPU-.YYYY.-` | System Manager | Batch fix of `total_daily_payments` / `actual_amount` |
| POS Attendance Shift Correction | single (tool) | | System Manager | Set the shift on POS-marked Attendance |

Child tables:

| Child table | Parent | Fields |
|---|---|---|
| POS Opening Shift Detail | Opening Shift | `mode_of_payment`, `amount` |
| POS Closing Shift Detail | Closing Shift | `mode_of_payment`, `opening_amount`, `expected_amount`, `closing_amount`, `difference` |
| POS Closing Shift Taxes | Closing Shift | `account_head`, `rate`, `amount` |
| Sales Invoice Reference | Closing Shift `pos_transactions` | `sales_invoice`, `posting_date`, `customer`, `grand_total`, `transaction_currency`, `transaction_amount` |
| POS Payment Entry Reference | Closing Shift `pos_payments` | `payment_entry`, `posting_date`, `customer`, `paid_amount`, `mode_of_payment` |
| POS Allowed Locale | POS Settings | `language` |
| POS Barcode Rules | POS Settings | `barcode_rule`, `disable` |
| POS Report Setting Item | POS Report Settings | `report`, `label`, `icon`, `pos_profile`, `enabled`, `report_type`, `ref_doctype` |
| POS Offer Detail | Sales Invoice | applied offers |
| POS Coupon Detail | Sales Invoice | applied coupons |
| POS Daily Payments Correction Item | correction tool | stored vs correct `total_daily_payments` / `total_tip` / `actual_amount`, `apply` |
| POS Closing Shift Daily Payment Update Item | update tool | current vs correct daily payments / actual amount, `updated` |
| POS Attendance Shift Correction Item | attendance tool | `attendance`, `employee`, `current_shift`, `new_shift`, `date_note`, `apply` |

### POS Opening Shift

`pos_opening_shift.py`. Fields: `period_start_date`, `posting_date`, `company`, `pos_profile`, `user`,
`balance_details`, `status` (Draft / Open / Closed / Cancelled) and `pos_closing_shift`. `validate` checks that the
profile is enabled and the user is one of its POS Profile Users. On submit the status becomes **Open**. When the
closing shift is linked, `set_status` makes it **Closed**.

### POS Closing Shift

`pos_closing_shift.py`. Fields: `period_start_date`, `period_end_date`, `posting_date`, `pos_opening_shift`,
`pos_profile`, `user`, `company`, `grand_total`, `net_total`, `total_quantity`, the tables `pos_transactions`,
`payment_reconciliation`, `taxes` and `pos_payments`, and the fork fields `total_daily_payments`, `total_tip` and
`actual_amount`. The lifecycle is described under [Shifts and closing](#4-shifts-and-closing).

### POS Settings

One record per POS Profile. `get_pos_settings` creates default settings for a profile if they are missing. The fields
are grouped as follows:

| Group | Fields |
|---|---|
| Locale | `allowed_locales` |
| Loyalty and wallet | `enable_loyalty_program`, `default_loyalty_program`, `wallet_account`, `auto_create_wallet`, `loyalty_to_wallet` |
| Discounts and rates | `allow_user_to_edit_additional_discount`, `allow_user_to_edit_item_discount`, `allow_user_to_edit_rate`, `use_percentage_discount`, `max_discount_allowed` |
| Credit and partial | `allow_credit_sale`, `allow_customer_credit_payment`, `allow_partial_payment`, `use_exact_amount` |
| Returns | `allow_return`, `allow_return_without_invoice`, `return_validity_days`, `allow_free_batch_return` |
| Display | `default_card_view`, `display_item_code`, `show_customer_balance`, `hide_expected_amount`, `display_discount_percentage`, `display_discount_amount`, `decimal_precision`, `input_qty` |
| Sales persons | `enable_sales_persons` (Disabled / Single / Multiple) |
| Sales orders | `allow_sales_order`, `allow_select_sales_order`, `create_only_sales_order` |
| Printing | `allow_print_draft_invoices`, `allow_print_last_invoice`, `silent_print` |
| Misc | `tax_inclusive`, `allow_customer_purchase_order`, `allow_duplicate_customer_names`, `fetch_coupon`, `use_delivery_charges`, `auto_set_delivery_charges`, `use_limit_search`, `search_limit`, `allow_submissions_in_background_job`, `allow_delete_offline_invoice`, `allow_change_posting_date`, `allow_negative_stock` (kept in sync with Stock Settings by `sync_negative_stock_setting`), `barcode_rules` |
| **Fork: cash transfer** | `enable_auto_cash_transfer`, `branch_cash_account`, `branch_manager_cash_account` |

### Wallet, coupons, offers

These are upstream features. See [docs/Wallet-System-Technical-Guide.md](docs/Wallet-System-Technical-Guide.md) and
[docs/OFFERS_AND_PROMOTIONS.md](docs/OFFERS_AND_PROMOTIONS.md). A `Wallet Transaction` submit posts GL entries between
the wallet account and the source account. On Sales Invoice submit, `process_loyalty_to_wallet` converts earned
loyalty points into wallet credit when `loyalty_to_wallet` is set. Returns reverse that credit.

### Offline sync records

`Offline Invoice Sync` (`offline_id`, `sales_invoice`, `status`, `pos_profile`, `customer`, `synced_at`) and
`Offline Operation Sync` (`op_id`, `op_type`, `status`, `ref_doctype`, `ref_name`, `error`). Each has a
`create_sync_record` / `is_synced` helper, so replaying an offline request returns the document it already created
instead of creating a duplicate. See [docs/OFFLINE_SYNC.md](docs/OFFLINE_SYNC.md).

---

## 4. Shifts and closing

<a id="closing-shift"></a>

### Lifecycle

```
ShiftOpeningDialog ── shifts.create_opening_shift ──► POS Opening Shift (submitted, status Open)
      │                                                 Sales Invoice.posa_pos_opening_shift = shift
      ▼
 selling, Daily Payments, attendance … (all stamped with the opening shift)
      │
ShiftClosingDialog ── shifts.get_closing_shift_data ──► make_closing_shift_from_opening()
      │                  (submits printed drafts, builds the reconciliation)
      ▼
   cashier counts each mode ── shifts.submit_closing_shift ──► POS Closing Shift submit
                                                         ├─ opening shift → Closed
                                                         ├─ delete unprinted drafts (if posa_allow_delete)
                                                         ├─ link invoices (pos_closing_entry)
                                                         └─ auto cash transfer Payment Entry (optional)
```

### Opening

`create_opening_shift(pos_profile, company, balance_details, op_id, period_start_date)` refuses to open a second shift
for a user who already has one open. It is idempotent through `op_id`. A shift opened offline sends its client time as
UTC ISO, which is converted to system time.

### Building the closing (`make_closing_shift_from_opening`)

1. `submit_printed_invoices`: every **draft** Sales Invoice of the shift with `posa_is_printed = 1` is submitted.
   A printed receipt is treated as a sale.
2. `payment_reconciliation` starts with one row per opening balance (`opening_amount = expected_amount = amount`).
3. Every submitted Sales Invoice of the shift (`get_pos_invoices`) is aggregated by `_process_invoice`. Payments are
   added to `expected_amount` per mode in company currency. Change given is subtracted from the profile's cash mode
   (`posa_cash_mode_of_payment`, else the first Cash-type mode). Taxes are summed per account. Returns and sales are
   counted separately.
4. Payment Entries of type Receive with `reference_no = opening shift` (credit-sale collections) go into `pos_payments`
   and are added to their mode.
5. The result also carries `returns_total/count` and `sales_total/count` for the dialog.

### Validation and fork totals

`validate()` runs these checks and calculations in order:

- One submitted closing per user and opening shift. The opening shift must still be **Open**.
- `validate_closing_amounts`: a counted (`closing_amount`) value may not be negative. It must be above 0 only where
  money was expected. A mode with no opening balance and no movement can close at 0; requiring a positive number used
  to leave such shifts stuck open.
- `difference = closing_amount − expected_amount` per row.
- `_compute_daily_payments_and_tip`:
  - `total_daily_payments` = Σ submitted Daily Payment `amount` of the shift, plus their `General Expenses` amounts
    when `expenses = 1` (expense-only payments leave the parent amount empty);
  - `total_tip` = Σ `Sales Invoice Item.amount` for item `Tip` on the shift's submitted invoices;
  - **`actual_amount` (expected cash)** = `grand_total − Visa − total_daily_payments − total_tip`, where
    Visa = Σ (`expected − opening`) of the `بنك CIB فيزا` reconciliation row.

The closing dialog shows the working-day window from `working_day.get_working_day_context`. `hide_expected_amount`
hides the expected figures from the cashier.

### Submit and cancel

- **on_submit**: links the closing shift on the opening shift and sets it to Closed. If the profile has
  `posa_allow_delete`, it deletes the shift's **unprinted** draft invoices. It then sets `pos_closing_entry` on the
  linked invoices (where the column exists) so ERPNext blocks edits.
- **After submit** (`submit_closing_shift` in the controller): `_create_cash_transfer_payment_entry`. When POS Settings
  has `enable_auto_cash_transfer` and `actual_amount > 0`, this creates an **Internal Transfer** Payment Entry from the
  branch cash account to the branch-manager cash account for `actual_amount`. It sets `custom_pos = 1` (so the
  ecs_heshamrabea full-balance rule does not apply), `reference_no` = closing shift, and the modes of payment found by
  reverse lookup of the accounts.
  - The accounts come from POS Settings `branch_cash_account` / `branch_manager_cash_account`. If those are empty,
    they are auto-detected among Cash accounts named `خزينة فرع <profile>` / `خزينة مدير فرع <profile>`, using
    normalized Arabic fuzzy matching (threshold 0.75, margin 0.05).
  - An existing PE with the same `reference_no` is not duplicated. When no account is found, the transfer is skipped
    with an orange alert and an Error Log entry.
- **on_cancel**: unlinks the opening shift (back to Open), clears `pos_closing_entry` on invoices, and cancels POS
  Invoice Merge Logs and consolidated invoices if POS Invoices were used.

<a id="daily-payments"></a>

### Daily Payments from the POS

`api/daily_payment.py` together with `components/daily_payment/DailyPaymentForm.vue` and `DailyPaymentManagement.vue`.

- The cashier records an employee advance (`payment_to_employees` + `loan_product`, default `سلفة من الراتب`), petty
  expenses (`expenses` + `general_expenses` rows), or a salary **deduction** (`deduction` + `salary_component`).
- `create_daily_payment` forces `mode_of_payment` to the shift profile's **Cash** mode (except for deductions), stamps
  `pos_opening_shift`, inserts and submits. It is idempotent by `op_id`, so it can be queued offline.
- What submit creates (Loan + Disbursement, Journal Entry, Extra Salary) is defined by the `Daily Payment` controller
  in ecs_heshamrabea.
- The management screen lists payments (`get_daily_payments`) and shows the branch balance from `get_branch_balance`.
  That balance is the GL balance of the hard-coded account `صندوق عمولات المساعدين - HR`.
- Shift totals feed `POS Closing Shift.total_daily_payments` (see above).
- **Track Invoices** (`TrackInvoices.vue`, `get_invoice_counts`) counts cash and Visa invoices per working day or shift.

<a id="employee-attendance"></a>

### Employee attendance from the POS

`api/employee_attendance.py` together with `EmployeeAttendance.vue`.

- `get_employees(date, company, branch)` returns `marked` and `unmarked` active employees for the business date.
  `get_attendance_date` returns the previous day while an overnight shift that started yesterday is still running.
- `mark_employee_attendance(employee_list, status ∈ Present/Absent/Half Day, …)` submits Attendance with the
  **default Shift Type**, whatever shift the client sends. It writes `Attendance.custom_branch` (`BRANCH_FIELD`) and
  skips employees who already have attendance that day.
- `convert_attendance_to_half_day(…, reason ∈ early_exit/late_entry)` is limited to POSNext Cashier or System Manager.
  It cancels the attendance and submits an amended **Half Day** with `late_entry` / `early_exit` set.
- Both are idempotent by `op_id` and can be queued offline (`attendance`, `attendance_half_day`).
- ecs_heshamrabea's *Employee Attendance* report counts only these POS-marked rows. Sub Salary pays from them.

<a id="working-day-logic"></a>

### Working day (`ecs_posnext/working_day.py`)

A branch trades from **Working Day Start Time** to **Working Day End Time** (Selling Settings,
`posa_working_day_start_time` / `posa_working_day_end_time`). The end time can fall on the next calendar date
(e.g. 10:00 → 06:00).

- `get_working_day_window(from_date, to_date)` turns a range of working-day dates into absolute `[from, to)` datetimes.
- The boundary between two days is the **closing** time, so consecutive windows are contiguous and nothing posted
  while the branch is shut falls through a gap.
- `get_current_working_day()` gives the working day a moment belongs to. `get_working_day_hours(day)` gives the real
  open and close datetimes.
- With either time unset, every caller falls back to plain calendar dates.
- Used by `api/daily_payment.get_invoice_counts`, the closing dialog, and the ecs_heshamrabea reports
  *POS Shift Transactions* and *Extra Salary Report*.

<a id="corrections"></a>

### Correction tools (System Manager)

These fix shifts whose stored totals drifted from the formula, for example shifts closed before the formula changed
or with Daily Payments submitted late. All of their whitelisted methods call `frappe.only_for("System Manager")`.

| Tool | What it does |
|---|---|
| **POS Daily Payments Correction** (single) | Mode *Single Shift* or *by Branch*. `get_problem_shifts` recomputes `total_daily_payments`, `total_tip` and `actual_amount` for submitted closing shifts and lists the ones that differ. `apply_corrections` writes the ticked rows directly to the submitted documents. |
| **POS Closing Shift Daily Payment Update** | A saved, auditable batch. Choose a branch / single shift and, optionally, `update_actual_amount`. Then **Get Affected Shifts** (`fetch_affected_shifts`) and `update_total_daily_payments`. The `status` and `shifts_updated` fields record the outcome. |
| **POS Attendance Shift Correction** (single) | `get_attendance_to_correct(from_date, to_date, only_missing_shift)` lists POS-marked Attendance whose shift is missing or wrong. `apply_corrections` sets `target_shift` (default Shift Type) on the ticked rows. |

<a id="offline-operations"></a>

### Offline operations

Opening and closing shifts, Daily Payments, attendance, half-day conversions and customer creation can be queued while
offline. Each request carries an `op_id`, recorded in **Offline Operation Sync**. `api/offline_ops.is_op_synced(op_id)`
lets the client check before retrying. `submit_closing_shift` throws `SYNC_IN_PROGRESS` if its opening shift has not
reached the server yet, so the client retries later. Invoices use `offline_id` instead
(see [docs/OFFLINE_SYNC.md](docs/OFFLINE_SYNC.md)).

---

## 5. Reports in the POS

<a id="the-report-override"></a>

### Exposing reports

1. In **POS Report Settings** tick `enable_reports_in_pos` and add rows: `report`, an optional `label` / `icon`, an
   optional `pos_profile` (empty = every profile), and `enabled`. Validation rejects duplicate (report, profile) pairs
   and disabled reports.
2. The POS **Reports** screen (`components/reports/POSReports.vue`) lists them with `api.reports.get_pos_reports`.
3. `get_report_definition` returns the filter bar. Desk report scripts cannot run in the standalone app, so filters
   are parsed out of the report's `.js` `filters: [...]` literal on the server. Common defaults (`frappe.datetime.*`,
   `get_user_default`, `__()`) are evaluated; anything else gets an empty default. The Report's own filter table is
   used only when the script has none, matching the desk.
4. `run_pos_report` runs the report with the desk's two-part permission gate (Report roles + `report` permission on
   `ref_doctype`), but only for reports configured for the profile. A shift-scoped profile/branch can be injected as
   parameters (`_scoped_parameters`).
5. Printing: `get_print_template` / `render_report_print` render the report's `.html` layout (JS microtemplate) or a
   Print Format made for the report (JS or Jinja), with an optional letter head.

### Report class override (`overrides/report.py`, `POSReport`)

The query parameters of a **Query Report** are bound only from the filters that were filled in. A query that names
`%(x)s` for an empty filter therefore raises `KeyError`. `_bind_query_parameters` fills every parameter the SQL names
before binding, for every caller (desk, POS, prepared report, Auto Email Report):

- an unset filter binds `None`, so SQL can use `%(x)s IS NULL OR …`;
- **session parameters** are answered by the session. `%(pos_profile_user)s` is the current user, or `None` for
  Administrator and System Manager (`UNSCOPED_ROLES`), so a query can limit cashiers to the profiles they belong to;
- POS-only parameters (profile and branch pinned by the cashier's shift) bind `None` on the desk.

This is what lets the Arabic Query Reports in ecs_heshamrabea use optional filters.

### Reports in this app

`pos_next/report/pos_closing_shift_(branch)` is a Query Report named **POS Closing Shift (Branch)** (module POS Next,
standard). ecs_heshamrabea ships a report with the **same name** in its own module (see Known issues).

---

## 6. Customizations and setup

### Fixtures

| Fixture | Content |
|---|---|
| Custom Field | Sales Invoice `posa_pos_opening_shift`, `posa_is_printed`. Item `custom_company`, `custom_allow_rate_edit`. POS Profile `posa_cash_mode_of_payment`, `posa_allow_delete`, `posa_block_sale_beyond_available_qty`. Mode of Payment `is_wallet_payment`. Selling Settings working-day section with `posa_working_day_start_time` and `posa_working_day_end_time`. |
| Print Format | `POS Next Receipt` |
| Role | `POSNext Cashier` |
| Custom DocPerm (POSNext Cashier) | full selling rights on Sales Invoice, POS Opening/Closing Shift, POS Closing Entry; create/submit Payment Entry and Expense Claim; read/write POS Settings and Offline Invoice Sync; create/write Customer; read on POS Profile, Item, Bin, Warehouse, Territory, Employee, Attendance, Shift Type, Expense Claim Type |

### Install, migrate, uninstall

- `after_install` / `after_migrate` (`install.py`): set `POS Next Receipt` as the default print format on POS Profiles,
  then clear the cache.
- Patches: `v1_7_0.reinstall_workspace`, and `v1_15_0.item_child_links_ignore_user_permissions`. The latter sets
  `ignore_user_permissions` on the Account / Branch / Warehouse / Cost Center links of `Item Default` and `Commission`,
  so branch-restricted cashiers can still read Items while invoicing.
- `before_uninstall` (`uninstall.py`): removes the custom fields and print formats and resets the POS Profile settings.

### Build and install

```bash
bench get-app <repo-url>                     # requires erpnext (and hrms, lending, ecs_heshamrabea for the fork features)
bench --site <site> install-app ecs_posnext
cd apps/ecs_posnext/POS && yarn install && yarn build   # see the Frontend part
bench --site <site> migrate && bench build --app ecs_posnext
```

The POS runs at `/pos` (`website_route_rules`: `/pos/<path>` → `pos`).

### Required configuration

1. **POS Profile**: company, warehouse, price list, payment modes (one Cash-type mode, or
   `posa_cash_mode_of_payment`), POS Profile Users, the `branch` custom field (ecs_heshamrabea), and optionally
   `posa_allow_delete` / `posa_block_sale_beyond_available_qty`.
2. **POS Settings** for each profile (created with defaults on first load). For the cash sweep, also set
   `enable_auto_cash_transfer` and the two cash accounts, or name the accounts `خزينة فرع <profile>` /
   `خزينة مدير فرع <profile>`.
3. **Users**: role `POSNext Cashier`, plus **User Permission** on Branch for branch-restricted cashiers.
4. **Selling Settings**: Working Day Start and End Time.
5. **Mode of Payment** `بنك CIB فيزا` (the name is hard-coded in the closing formula). Mark wallet modes with
   `is_wallet_payment`.
6. **Item `Tip`** (the item code is hard-coded in the tip total). **Shift Type** default for attendance.
7. **QZ Tray** certificate and key for silent printing: see [docs/QZ_TRAY_SIGNING.md](docs/QZ_TRAY_SIGNING.md).
8. **POS Report Settings** for the reports cashiers should see.

---

# Part II — Frontend

## 7. Frontend architecture

### 7.1 Tech stack

From `POS/package.json`. The frontend package version is `1.15.0` and is kept in step with the root `package.json`.

| Concern | Library |
|---------|---------|
| Framework | Vue `3.5.13` (Composition API, `<script setup>`) |
| Router | vue-router 4 (`createWebHistory("/pos")`) |
| State | Pinia 3 (setup-style stores only) |
| UI kit | frappe-ui `^0.1.240` (`Button`, `Dialog`, `FormControl`, `createResource`, `call`, `frappeRequest`, ...) |
| Styling | Tailwind CSS 3, plus a generated light/dark theme layer (`src/theme.css`, `tailwind.theme.js`) |
| Icons | Lucide through frappe-ui's vite plugin (`lucideIcons: true`), and `feather-icons` |
| Offline DB | Dexie 4 (IndexedDB) |
| Background work | One ES-module Web Worker (`src/workers/offline.worker.js`) |
| Realtime | socket.io-client 4 (connects to the Frappe socketio server) |
| PWA | vite-plugin-pwa (Workbox `generateSW`, `registerType: "autoUpdate"`) |
| Printing | Browser printing through a hidden iframe, and `qz-tray` 2.2 for silent thermal printing and the cash drawer |
| Fonts | Inter (bundled in `src/assets/Inter`), IBM Plex Sans and Cairo (Google Fonts, preconnected in `index.html`), Saudi Riyal symbol font |
| Lint/format | Biome 1.9 (`POS/biome.json`, tab indentation) |
| Tests | Vitest 2 with jsdom and `@vue/test-utils` (`src/utils/__tests__`, `src/utils/offline/__tests__`) |

frappe-ui's vite plugin with `lucideIcons: true` also turns on **unplugin-vue-components** and **unplugin-auto-import**. As a result, any `.vue` file under `src/components/` can be used in a template **without an import**. `POS/components.d.ts` and `POS/auto-imports.d.ts` are the generated typings. For example, `<InstallAppBadge />` in `src/pages/POSSale.vue` is never imported. Most code still imports components explicitly.

---

### 7.2 Build and dev workflow

#### 7.2.1 Commands

Run these from `apps/ecs_posnext/POS`:

| Command | What it does |
|---------|--------------|
| `yarn install` | Installs dependencies. The root `package.json` `postinstall` runs this for you. |
| `yarn dev` | Vite dev server on **port 8080**, with HMR |
| `yarn build` | `vite build --base=/assets/ecs_posnext/pos/` (production bundle) |
| `yarn preview` | Serves the built bundle |
| `yarn lint` / `yarn lint:fix` / `yarn format` | Biome |
| `yarn test` / `yarn test:run` / `yarn test:coverage` | Vitest |
| `yarn copy-html-entry` | Manual fallback: copies `public/pos/index.html` to `www/pos.html`. The build already does this. |

The root `apps/ecs_posnext/package.json` defines `build: cd POS && yarn build`. This is what `bench build --app ecs_posnext` runs.

#### 7.2.2 Dev server

`POS/vite.config.js` `server` block:

- Port 8080, with `allowedHosts: true`.
- Proxies `^/(app|api|assets|files|printview)` (including websockets) to `http://<host>:8000`. The `router` function maps `localhost` and `127.0.0.1` to `127.0.0.1`. Any other host name is passed through, so open `http://<site-name>:8080` to reach a named site.
- frappe-ui's `frappeProxy: true` adds its own proxy config.
- The PWA plugin runs in dev as well (`devOptions.enabled: true, type: "module"`). If you see stale bundles while developing, unregister the service worker.
- The upstream starter README (`POS/README.md`) suggests `"ignore_csrf": 1` in `site_config.json` for dev. The app also fetches a CSRF token itself (see §4).

#### 7.2.3 How assets reach the site

```
POS/src  ──vite build──►  ecs_posnext/public/pos/          (outDir, emptyOutDir: true)
                            ├── index.html                  (built entry)
                            ├── assets/*.js|css|woff2       (hashed chunks, incl. offline.worker-<hash>.js)
                            ├── workers/offline.worker.js   (raw copy, see Known issues)
                            ├── sw.js, workbox-*.js         (generated service worker)
                            ├── manifest.webmanifest
                            ├── version.json                (build version, see below)
                            └── favicon.png, icon*.svg, offline.html   (from POS/public)

frappe-ui buildConfig plugin ──copies index.html──► ecs_posnext/www/pos.html
```

- **Served at:** `/assets/ecs_posnext/pos/...`, because of `--base` and `bench build` symlinking `public/` into `sites/assets/ecs_posnext`.
- **Page route:** `ecs_posnext/www/pos.html` is a Frappe www page. `ecs_posnext/hooks.py` maps `website_route_rules = [{'from_route': '/pos/<path:app_path>', 'to_route': 'pos'}]`, so every `/pos/*` deep link renders the same HTML and vue-router handles the route.
- **Jinja boot data:** frappe-ui's `jinjaBootData` plugin injects `{% for key in boot %} window[key] = ... {% endfor %}` into `pos.html`. There is no `www/pos.py` that supplies `boot`, so this loop normally emits nothing. `window.csrf_token` is therefore *not* set by the page, and the app gets its token from the cookie or from `ecs_posnext.api.utilities.get_csrf_token` (`src/utils/csrf.js`).
- **Pre-paint theme script:** `POS/index.html` contains an inline script that reads `localStorage.ecs_posnext_theme` and sets `data-theme="dark"` before the first paint.

#### 7.2.4 Build version

- `vite.config.js` reads `process.env.ecs_posnext_BUILD_VERSION`. If it is not set, it uses `Date.now()`.
- The `posNextBuildVersionPlugin` writes `ecs_posnext/public/pos/version.json` (`{version, timestamp, buildDate}`) in `writeBundle`.
- The same value is exposed as the compile-time constant `__BUILD_VERSION__`. No code in `src/` currently reads it.
- On the backend, `ecs_posnext.utils.get_build_version()` reads `version.json` (falling back to the manifest mtime, then the app version plus a timestamp). `hooks.py` uses it as `_asset_version` for cache busting.
- The version shown in the header (`POSHeader.vue`) is `version` from `POS/package.json`, **not** the build version.
- To pin a version: `ecs_posnext_BUILD_VERSION=1.15.0 yarn build`. See [VERSION_CONTROL.md](docs/VERSION_CONTROL.md) and `scripts/version-bump.sh`.

Other build settings: `target: "es2015"`, `chunkSizeWarningLimit: 1500`, and source maps off unless `ecs_posnext_ENABLE_SOURCEMAP=true`. Workers build as ES modules. `optimizeDeps` pre-bundles `qz-tray`, `feather-icons` and others. The alias `@` points to `POS/src`.

#### 7.2.5 Theme generation

`POS/scripts/gen_theme.py` regenerates `POS/src/theme.css` (CSS variables for light and dark) and `POS/tailwind.theme.js` (Tailwind colour scales that point at those variables) from `node_modules/frappe-ui/tailwind/colors.json`. Re-run it after a frappe-ui upgrade or a palette change. The ROOT path inside the script is hardcoded to `/home/frappe/frappe-bench/apps/ecs_posnext/POS`. Theme switching at runtime is a single `data-theme` attribute write (`src/composables/useTheme.js`, `src/components/common/ThemeToggle.vue`).

---

### 7.3 Directory layout

```
POS/
├── index.html                 Vite entry template (theme pre-paint script, fonts)
├── vite.config.js             Build, PWA, proxy, build-version plugin
├── tailwind.config.js / tailwind.theme.js / postcss.config.js
├── biome.json
├── scripts/gen_theme.py       Generates theme.css + tailwind.theme.js
├── public/                    Copied verbatim to the build (icons, offline.html)
└── src/
    ├── main.js                App bootstrap (SW, Pinia, plugins, auth, bootstrap preload, socket)
    ├── router.js              Routes + auth guard
    ├── App.vue                <router-view :key="translationVersion"> + <Toast/>
    ├── socket.js              Socket.IO client factory
    ├── index.css / theme.css  Global styles and theme variables
    ├── data/                  session.js (login/logout/session), user.js (user resource + cookie data)
    ├── pages/                 POSSale.vue (the whole POS), Login.vue, Home.vue (unused starter page)
    ├── components/
    │   ├── pos/               POSHeader, ManagementSlider
    │   ├── sale/              Cart, item grid, payment, customers, returns, offers/coupons, drafts, history...
    │   ├── invoices/          InvoiceManagement, InvoiceFilters, InvoiceDetailDialog
    │   ├── daily_payment/     DailyPaymentManagement/Form, TrackInvoices, EmployeeAttendance
    │   ├── reports/           POSReports, ReportFilterField
    │   ├── settings/          POSSettings + field widgets + settingsConfig.js
    │   ├── partials/          PartialPayments (unused, see Known issues)
    │   ├── common/            Toast, AutocompleteSelect, SelectInput, LazyImage, LanguageSwitcher, ThemeToggle, POSFooter, ...
    │   ├── ShiftOpeningDialog.vue
    │   └── ShiftClosingDialog.vue
    ├── stores/                Pinia stores (see §8)
    ├── composables/           use* composables (see §8)
    ├── utils/                 Printing, QZ, currency, csrf, logger, reports, mutex, ...
    │   └── offline/           Dexie DB, offline state, queues, sync engines, worker client
    ├── workers/offline.worker.js
    └── assets/Inter/          Bundled Inter font
```

---

### 7.4 Boot sequence (summary)

[STARTUP_SEQUENCE.md](docs/STARTUP_SEQUENCE.md) has the full timeline. In `src/main.js`:

1. Registers the service worker (`virtual:pwa-register`, `immediate: true`) on `window.load`.
2. `useTheme().initTheme()`, then `registerOfflineOpHandlers()` (`src/utils/offline/opHandlers.js`).
3. Wraps `frappeRequest` with `createCSRFAwareRequest`, which retries on a CSRF 401/403, and sets it as frappe-ui's `resourceFetcher`.
4. Installs Pinia, `resourcesPlugin`, `pageMetaPlugin` and `translationPlugin`. The translation plugin exposes `__()` both as a template global and as `window.__`, which is why stores call `__()` without importing it. It also registers the global frappe-ui components and a `v-touch-action` directive.
5. Fetches the CSRF token (cookie, or `ecs_posnext.api.utilities.get_csrf_token`) **in parallel with** the user (`frappe.auth.get_logged_user`), then pushes the token into the worker (`offlineWorker.setCSRFToken`).
6. If a user is logged in, it lazy-imports `stores/bootstrap` and runs `loadInitialData()` (`ecs_posnext.api.bootstrap.get_initial_data`). It then calls `initPrecision(...)` and creates the socket with `initSocket(siteName)`, assigns it to `window.frappe.realtime` and calls `.connect()`. **This step is not awaited.** The app mounts right away.
7. `app.use(router)`, `app.mount("#app")`.
8. Refreshes the CSRF token every 30 minutes.

`POSSale.vue` then runs its own init (`checkShift`, settings, tax rules, offline preload, offers and so on). See [Frontend components](#9-frontend-components).

---

### 7.5 Routing and pages

`src/router.js`, history base `/pos`:

| Path | Name | Component | Notes |
|------|------|-----------|-------|
| `/` | `POSSale` | `pages/POSSale.vue` (lazy) | The entire POS. Every other screen is a dialog or modal inside it. |
| `/account/login` | `Login` | `pages/Login.vue` (lazy) | Uses `session.login` (`url: "login"`) |
| `/:pathMatch(.*)*` | | redirect `/` | |

The guard (`router.beforeEach`) redirects to `Login` when `session.isLoggedIn` is false, and sends a logged-in user away from `Login`. `session.user` is set in `main.js` before the router is installed. `pages/Home.vue` is the frappe-ui starter page (it calls `ecs_posnext.api.ping`) and is **not routed**.

Because the POS is effectively a single page, "screens" such as Invoices, Daily Payment, Reports and Settings are **dialogs toggled by refs in `POSSale.vue`**, not routes (see §9).

---

### 7.6 Offline layer

#### 7.6.1 Building blocks

| Module | Role |
|--------|------|
| `src/utils/offline/db.js` | **Owns the Dexie schema** for the `ecs_posnext_offline` IndexedDB database. Also provides `checkDBHealth`, `getSetting`/`setSetting`, `clearCachedData`, `nukeDatabase`, `clearBrowserCache`. |
| `src/workers/offline.worker.js` | A Web Worker that opens the **same** database in dynamic mode (no schema declared, so it relies on the main thread having created it). It does heavy IndexedDB reads and writes (item and customer search, bulk caching, invoice queue, offers cache), server pings, and **periodic stock sync** (`ecs_posnext.api.items.get_stock_quantities`, minimum interval 10 s). It has a query cache (100 entries, 5 min TTL) and a circuit breaker. |
| `src/utils/offline/workerClient.js` | `offlineWorker` singleton: a promise-based message bus to the worker with retries and exponential backoff, a health check, graceful degradation after 3 failed inits, and CSRF token forwarding. The worker is created with `new Worker(new URL("../../workers/offline.worker.js?worker", import.meta.url), {type: "module"})`. |
| `src/utils/offline/offlineState.js` | `offlineState`, the **single source of truth** for online/offline. It combines `navigator.onLine`, server pings (`/api/method/ecs_posnext.api.ping`), the Network Information API, a stability buffer against flapping, a visibility-change re-check, and a manual offline toggle. Consumers call `offlineState.subscribe()` or `isOffline()`. |
| `src/utils/offline/sync.js` | Invoice queue: `saveOfflineInvoice`, `syncOfflineInvoices` (mutex-guarded, checks `ecs_posnext.api.invoices.check_offline_invoice_synced`, then calls `ecs_posnext.api.invoices.submit_invoice`). Also stock and the invoice-history and unpaid-invoice caches. |
| `src/utils/offline/operations.js` | **Generic operation queue** (`operation_queue`) for non-invoice writes: `enqueueOperation(type, data)`, `getPendingOperations`, `markOperationSynced`, `handleOperationFailure`, ... |
| `src/utils/offline/syncOps.js` | Operation sync engine: `registerOpHandler(type, {method, buildParams, onSynced})`, `syncOfflineOperations()`. Ops are processed oldest-first under a mutex, and duplicates are detected through `ecs_posnext.api.offline_ops.is_op_synced`. It dispatches a `window` `offlineOperationsSynced` event. |
| `src/utils/offline/opHandlers.js` | Registers handlers for each op type (see 6.3). |
| `src/utils/offline/cache.js`, `items.js` | Item, customer and payment-method caching and search helpers, an in-memory cache, and the cache-structure hash in `localStorage` |
| `src/utils/offline/translationCache.js` | Caches translations per locale in the `translations` table |
| `src/utils/offline/uuid.js` | `generateOfflineId()`, shared by the main thread and the worker |
| `src/utils/draftManager.js` | **Separate** raw-IndexedDB database `ecs_posnext_drafts` (store `invoices`) for draft carts |

#### 7.6.2 IndexedDB schema (`ecs_posnext_offline`, `DB_VERSION = 1001`)

Defined in `CURRENT_SCHEMA` in `src/utils/offline/db.js`. The version is a **fixed constant**: bump it by 1 whenever you change the schema. An older scheme derived the version from a hash in `localStorage` and could wipe the queues; see the comment in the source.

| Table | Primary key and indexes | Contents |
|-------|-------------------------|----------|
| `settings` | `&key` | Key-value metadata (e.g. `opening_dialog_data`, shift-name mappings, health check) |
| `invoice_queue` | `++id, &offline_id, timestamp, synced` | Offline invoices awaiting sync |
| `operation_queue` | `++id, &op_id, type, timestamp, synced` | Offline non-invoice writes |
| `items` | `&item_code, item_name, item_group, variant_of, *barcodes` | Item cache (plus price and stock fields, and batch and serial data) |
| `customers` | `&name, customer_name, mobile_no, email_id` | Customer cache |
| `item_prices` | `&[price_list+item_code], price_list, item_code` | Price cache |
| `stock` | `&[item_code+warehouse], item_code, warehouse` | Local stock |
| `payment_methods` | `&mode_of_payment, pos_profile` | Payment methods per profile |
| `drafts` | `++id, draft_id, timestamp` | Unused. Drafts actually live in `ecs_posnext_drafts`. |
| `translations` | `&locale, timestamp` | Offline translations |
| `offers` | `&name, pos_profile, apply_on, valid_upto` | Offers cache |
| `invoice_history` | `&name, pos_profile, posting_date, customer` | Submitted invoices, for offline viewing |
| `unpaid_invoices` | `&name, pos_profile, outstanding_amount, customer` | Partial or unpaid invoices, for offline viewing |

#### 7.6.3 Offline write operations (not covered in docs/OFFLINE_SYNC.md)

`registerOfflineOpHandlers()` in `src/utils/offline/opHandlers.js`:

| `type` | Enqueued by | Synced to |
|--------|-------------|-----------|
| `open_shift` | `composables/useShift.js` (via `ShiftOpeningDialog.vue`) | `ecs_posnext.api.shifts.create_opening_shift`. `onSynced` maps the local shift name to the real one, remaps queued invoices' `pos_opening_shift`, and updates `localStorage.pos_shift_data`. |
| `close_shift` | `composables/useShift.js` (via `ShiftClosingDialog.vue`) | `ecs_posnext.api.shifts.submit_closing_shift`. It resolves the real opening-shift name first and can call `ecs_posnext.api.shifts.get_closing_shift_data`. |
| `attendance` | `EmployeeAttendance.vue` | `ecs_posnext.api.employee_attendance.mark_employee_attendance` |
| `attendance_half_day` | `EmployeeAttendance.vue` | `ecs_posnext.api.employee_attendance.convert_attendance_to_half_day` |
| `daily_payment` | `DailyPaymentForm.vue` | `ecs_posnext.api.daily_payment.create_daily_payment` |
| `customer` | `CreateCustomerDialog.vue`, `PaymentDialog.vue` (inline customer) | `ecs_posnext.api.customers.create_customer`. `onSynced` remaps the temporary customer name on queued invoices. |

Each op carries an `op_id` (UUID) for server-side deduplication. The queue and its retry and failure state are shown in `components/sale/OfflineInvoicesDialog.vue`, which has "Retry" and "Sync all" actions.

#### 7.6.4 When sync runs

- **Invoices:** `stores/posSync.js` subscribes to `offlineState`. On an offline-to-online transition it calls `syncOfflineInvoices()` automatically. Users can also trigger it manually (header sync button, then `POSSale.handleSyncAll`, then `posSync.syncAllPending`).
- **Operations:** synced only from `OfflineInvoicesDialog.vue` (Retry or Sync all) and `useOffline().syncPendingOperations()`. There is no automatic sync of operations on reconnect (see Known issues).
- **Stock:** the worker's periodic stock sync (configured from `POSSale.setupPeriodicStockSync`), the realtime `pos_stock_update` event, and `stores/stock.js` `refresh()`.
- **Offline preload:** `posSync.preloadDataForOffline(profile)` runs during POS init when online. It caches items, customers, payment methods and offers through the worker. Large catalogs are synced in the background by `itemSearch.startBackgroundCacheSync` (see [LARGE_CATALOG_OPTIMIZATION.md](docs/LARGE_CATALOG_OPTIMIZATION.md)).

The end-to-end invoice path, deduplication and troubleshooting are in [OFFLINE_SYNC.md](docs/OFFLINE_SYNC.md).

#### 7.6.5 Browser storage keys (localStorage)

These are useful for support. Clearing them resets per-till preferences.

| Key | Owner |
|-----|-------|
| `ecs_posnext_theme` | `useTheme.js`, `index.html` |
| `ecs_posnext_language`, allowed-locales key | `useLocale.js` |
| `pos_shift_data` | `useShift.js`, `opHandlers.js` (cached open shift for offline) |
| `pos_stock_sync_settings` | stock sync configuration |
| `pos_invoice_filters` | `stores/invoiceFilters.js` presets |
| `pos_recent_customers`, `pos_frequent_customers` | `stores/customerSearch.js` |
| `pos_performance_tier` | `utils/performanceConfig.js` |
| `ecs_posnext_cache_version`, `ecs_posnext_cache_structure_hash` | `utils/offline/cache.js` |
| printer, paper width, drawer pin, signing keys | `utils/qzTray.js` (per-till QZ settings) |
| `POS_LOGGING_ENABLED`, `POS_LOG_LEVEL`, `POS_LOG_NAMESPACES_ENABLED/DISABLED` | `utils/logger.js`. Set these to turn on console logging in production. |

---

### 7.7 Realtime (Socket.IO)

`src/socket.js`:

- `initSocket(siteName)` builds `io("<protocol>://<host><:port>/<siteName>", {withCredentials: true, reconnectionAttempts: 3, autoConnect: false})`. `socketio_port` is **imported at build time** from `../../../../sites/common_site_config.json`. If the page URL has an explicit port, the client uses `http://host:<socketio_port>`. Otherwise it uses `https://host` with no port, which is what a production nginx setup with TLS expects.
- `main.js` assigns the socket to `window.frappe.realtime` after bootstrap and calls `connect()`. `disconnectSocket()` and `useSocket()` are exported as well.
- If initialisation throws, it returns a no-op mock socket.

Events the UI handles. All of them are published by `ecs_posnext/realtime_events.py`.

| Event | Composable | Consumer and effect |
|-------|------------|---------------------|
| `pos_stock_update` | `composables/useRealtimeStock.js` (batched, deduplicated) | `POSSale.vue` filters updates by the profile warehouse, then calls `stockStore.update()` and `offlineWorker.updateStockQuantities()` |
| `pos_invoice_created` | `useRealtimeStock.js` | Hook point only (currently logs) |
| `pos_profile_updated` | `composables/useRealtimePosProfile.js` (with retry) | `stores/itemSearch.js` computes the item-group delta, removes or fetches groups, and falls back to a full cache recovery |
| `pos_customer_changed` | `composables/useRealtimeCustomers.js` (with retry) | `stores/customerSearch.js` updates the customer cache |

There is also an **in-app event bus** that is separate from Socket.IO: `stores/posEvents.js` and `composables/usePOSEvents.js`. It emits `settings:changed`, `settings:warehouse-changed`, `settings:stock-policy-changed`, `settings:pricing-changed`, `settings:display-changed`, `settings:sales-operations-changed`, `settings:sync-configured` and `sync:stock-updated`. `POSSettings.vue` emits these through `detectSettingsChanges()`, and `POSSale.vue` and `stores/stock.js` listen.

---

### 7.8 PWA and service worker

From the `VitePWA` config in `POS/vite.config.js`:

- The manifest is named "POSNext", with `scope: /assets/ecs_posnext/pos/`, `start_url: /pos` and `display: standalone`.
- Workbox precaches `**/*.{js,css,html,ico,png,svg,woff,woff2}` (max 4 MB per file), with `skipWaiting` and `clientsClaim`.
- Runtime caching:
  - Google Fonts: CacheFirst, 1 year
  - `/assets/ecs_posnext/pos/*`: CacheFirst, 30 days
  - `/files/*.(jpg|png|...)`: StaleWhileRevalidate, 7 days, 200 entries
  - `/api/*` GET: **NetworkFirst** with a 10 s timeout, 24 h, 100 entries
  - `/pos*` navigations: NetworkFirst with a 3 s timeout
- The install prompt is handled by `composables/usePWAInstall.js` and `components/common/InstallAppBadge.vue` (mobile only).
- "Clear cache" in the header uses `ClearCacheOverlay.vue` and the helpers in `utils/offline/db.js` (`clearCachedData`, `nukeDatabase`, `clearBrowserCache`).

---

### 7.9 Conventions for adding a feature or screen

1. **New management screen.** Follow the pattern of Reports, Daily Payment and Attendance:
   - Create `src/components/<area>/MyScreen.vue` as a frappe-ui `<Dialog>` driven by `v-model` (`modelValue` prop plus `update:modelValue`).
   - Add a tile in `src/components/pos/ManagementSlider.vue` that calls `handleMenuClick('my-screen')`.
   - In `src/pages/POSSale.vue`, add a `showMyScreen` ref, a branch in `handleManagementMenuClick()`, and the `<MyScreen v-model="showMyScreen" :pos-profile=... />` element next to the other management dialogs. Pass profile, branch and shift through `shiftStore` getters (`profileName`, `profileBranch`, `profileCompany`, `currentShift`).
   - Only add a route in `router.js` if the screen must be deep-linkable. Nothing else in the app is a route.
2. **Backend calls.** Use `createResource({url: "ecs_posnext.api.<module>.<fn>", makeParams, onSuccess, onError})` for reactive loading, or `call()` from `@/utils/apiWrapper` (or `frappe-ui`'s `call`) for imperative calls. Both go through the CSRF-aware fetcher. Put logic shared by several components in a store or composable, not in the component.
3. **Shared state** goes in a setup-style Pinia store under `src/stores/` that returns `{state, getters, actions}`. Stores can be cross-wired (e.g. `posCart` wraps `useInvoice()`), but keep the dependency one-directional.
4. **Offline support for a write.** Check `isOffline()` from `@/utils/offline/sync`. If offline, call `enqueueOperation("<type>", payload)` with a JSON-serialisable payload, and register a handler for `<type>` in `src/utils/offline/opHandlers.js` (`method`, `buildParams`, optional `onSynced`). The backend endpoint should accept and deduplicate by `op_id` (see `ecs_posnext.api.offline_ops`). Add a label for the op type in `OfflineInvoicesDialog.vue` (`OP_LABELS`).
5. **IndexedDB schema changes.** Edit `CURRENT_SCHEMA` in `src/utils/offline/db.js` and **bump `DB_VERSION`**. Worker code reads the tables dynamically, so it needs no schema change.
6. **Translations.** Wrap every user-visible string in `__("...")`, with `{0}` placeholders and an argument array. Strings come from `ecs_posnext.api.localization.get_app_translations` and are cached offline. See [LOCALIZATION.md](docs/LOCALIZATION.md). Arabic and RTL are first-class: use logical Tailwind utilities (`ms-`, `me-`, `start-`, `end-`).
7. **Toasts and errors.** Use `useToast()` (`showSuccess`, `showError`, `showWarning`). For API errors, use `parseError()` and `handleApiError()` from `utils/errorHandler.js`, and `uiStore.showError(...)` for the blocking error dialog.
8. **Logging.** Use `logger.create("Namespace")` from `utils/logger.js` instead of `console.*`. It is silent in production unless the `POS_LOGGING_*` keys are set.
9. **Concurrency.** Wrap actions that must not run twice in `CoalescingMutex` or `QueuedMutex` from `utils/mutex.js`. Invoice submission and both sync engines already use them.
10. **Settings flags.** Add the field to the POS Settings doctype (backend) and a computed getter in `stores/posSettings.js`. If the setting is editable in the POS, also add it in `components/settings/settingsConfig.js` and `POSSettings.vue`. Add an event in `posEvents.detectSettingsChanges` if other parts of the app must react live.
11. **Styling.** Use Tailwind plus the themed palette. Do not hardcode hex colours, because dark mode works by swapping variables. Re-run `scripts/gen_theme.py` only when the palette itself changes.
12. **Tests.** Keep pure logic in `src/utils/*` and add Vitest specs under `src/utils/__tests__/`. Run them with `yarn test:run`.
13. **Formatting.** Run `yarn lint:fix`. Biome uses tab indentation.

---

## 8. Frontend stores, composables and utils

### 8.1 Store dependency overview

```
POSSale.vue
  ├─ posShift ──► useShift() (module-level shiftState)
  ├─ posSettings ◄── bootstrap (preloaded settings)
  ├─ posCart ──► useInvoice() (cart math, submission, taxes)
  │     ├─ posOffers   (eligibility from cart snapshot)
  │     ├─ posSalesPerson
  │     └─ posUI (dialogs)
  ├─ itemSearch ──► stock, offlineWorker, useRealtimePosProfile
  ├─ customerSearch ──► offlineWorker, useRealtimeCustomers
  ├─ posSync ──► offlineState, offlineWorker, utils/offline/sync
  ├─ posDrafts ──► utils/draftManager
  ├─ stock ──► posEvents ('settings:warehouse-changed')
  └─ posEvents (in-app event bus)
```

---

### 8.2 Pinia stores

#### `bootstrap` (`stores/bootstrap.js`, ~170 lines)
- **Role:** Loads all initial data in a single request at startup, before the POS page needs it. It is lazy-imported from `main.js`.
- **State:** `loaded`, `loading`, `data`, `error`.
- **Actions/getters:**
  - `loadInitialData()`
  - `getPreloadedLocale()`, `getSiteName()`, `getPreloadedShift()`, `getPreloadedPOSProfile()`, `getPreloadedPOSSettings()`, `getPreloadedPaymentMethods()`, `getPreloadedPrecision()`
  - `hasBootstrapData()`, `reset()`
- **Endpoints:** `ecs_posnext.api.bootstrap.get_initial_data`
- See [STARTUP_SEQUENCE.md](docs/STARTUP_SEQUENCE.md).

#### `posShift` (`stores/posShift.js`, ~140 lines)
- **Role:** A thin facade over `composables/useShift.js` plus the header clock.
- **State:** `currentProfile`, `currentShift`, `hasOpenShift` (all from `useShift`), `currentTime`, `shiftDuration`, `shiftTimerPaused`.
- **Getters:** `profileName`, `profileCurrency`, `profileWarehouse`, `profileCompany`, `profileCustomer`, `profileBranch`, `profilePaymentMethods`, `autoPrintEnabled`, `writeOffAccount`, `writeOffCostCenter`, `writeOffLimit`.
- **Actions:**
  - `checkShift()`. Once a shift is found it also calls `qzTray.prewarm()` so the first receipt does not pay the cost of the QZ handshake.
  - `startTimers()`, `updateShiftDuration()`, `updateCurrentTime()`.
- **Endpoints:** none directly. They come through `useShift` (§3).

#### `posSettings` (`stores/posSettings.js`, ~470 lines)
- **Role:** Holds the POS Settings doctype for the current profile as reactive flags.
- **State:** `settings` (object with defaults), `isLoading`, `isLoaded`.
- **Getters:** about 40 boolean or numeric computeds. Examples:
  - Discounts: `allowItemDiscount`, `allowAdditionalDiscount`, `maxDiscountAllowed`, `usePercentageDiscount`
  - Payment and returns: `allowCreditSale`, `allowPartialPayment`, `allowReturn`, `allowReturnWithoutInvoice`, `allowWriteOffChange`, `useExactAmount`
  - Sales orders: `allowSalesOrder`, `createOnlySalesOrder`
  - Printing: `silentPrint`, `allowPrintLastInvoice`, `allowPrintDraftInvoices`
  - Display: `defaultCardView`, `displayItemCode`, `hideExpectedAmount`, `showCustomerBalance`
  - Loyalty and wallet: `enableLoyaltyProgram`, `walletAccount`, `autoCreateWallet`, `loyaltyToWallet`
  - Other: `decimalPrecision`, `useDeliveryCharges`, ...
- **Actions:**
  - `loadSettings(posProfile)` uses the bootstrap data when present.
  - `reloadSettings()`, `resetSettings()`, `validateDiscount(pct)`, `isNegativeStockAllowed()`, `shouldEnforceStockValidation()`.
- **Endpoints:** `ecs_posnext.pos_next.doctype.pos_settings.pos_settings.get_pos_settings`

#### `posCart` (`stores/posCart.js`, ~1,790 lines)
- **Role:** The cart. It re-exports the reactive cart from `useInvoice()` and adds offer and coupon handling, UOM and variant selection, drafts integration and sales-person rules.
- **State:**
  - From `useInvoice`: `invoiceItems`, `customer`, `subtotal`, `totalTax`, `totalDiscount`, `grandTotal`, `payments`, `salesTeam`, `additionalDiscount`, `taxInclusive`, `isSubmitting`, `posProfile`, `posOpeningShift`.
  - Its own: `pendingItem`, `pendingItemQty`, `appliedOffers`, `appliedCoupon`, `selectionMode`, `currentDraftId`, `targetDoctype` (`Sales Invoice` or `Sales Order`), `deliveryDate`, `writeOffAmount`, `offerProcessingState`.
- **Getters:** `itemCount`, `isEmpty`, `hasCustomer`, `isProcessingOffers`.
- **Actions:**
  - Items and cart: `addItem` (refuses to add until a sales person is chosen when multiple sales persons is on), `removeItem`, `updateItemQuantity`, `clearCart`, `setCustomer`, `setPendingItem`, `changeItemUOM`, `updateItemDetails`.
  - Discounts: `applyDiscountToCart`, `removeDiscountFromCart`.
  - Offers: `applyOffer`, `removeOffer`, `reapplyOffer`, `autoApplyEligibleOffers`, `applyOffersOffline` (client-side price-discount and free-item rules), `triggerOfferProcessing` / `debouncedProcessOffers` (dynamic debounce plus an async queue with cancellation), `forceRefreshOffers`.
  - Submission: `buildInvoicePayload(overrides)` (also used for **offline** invoices so they sync identically), `submitInvoice()`, `createSalesOrder()`.
  - Taxes: `loadTaxRules`, `setTaxInclusive`.
- **Endpoints:** through `useInvoice` (§3). Offers go to `ecs_posnext.api.invoices.apply_offers`.
- Pricing and offer math are covered in [PRICING_AND_SUBMISSION.md](docs/PRICING_AND_SUBMISSION.md) and [OFFERS_AND_PROMOTIONS.md](docs/OFFERS_AND_PROMOTIONS.md).

#### `posOffers` (`stores/posOffers.js`, ~365 lines)
- **Role:** The list of available offers and the client-side eligibility check against a cart snapshot.
- **State:** `availableOffers`, `cartSnapshot`, `hasFetched`.
- **Getters:** `allEligibleOffers`, `allEligibleOffersSorted`, `autoEligibleOffers`, `autoEligibleCount`.
- **Actions:** `ensureOffersFetched(posProfile)` (uses the worker `CACHE_OFFERS` / `GET_CACHED_OFFERS` when offline), `updateCartSnapshot`, `checkOfferEligibility`, `getUnlockAmount`, `clearOffers`.
- **Endpoints:** `ecs_posnext.api.offers.get_offers`

#### `posSalesPerson` (`stores/posSalesPerson.js`, ~210 lines)
- **Role:** Multiple sales persons per sale. One person is "active" and receives newly added items. The store also computes commission allocations.
- **State:** `enabled`, `salesPersons`, `selected`, `activeSalesPerson`, `loading`, `posProfile`.
- **Actions:** `loadSalesPersons`, `refreshSalesPersons`, `addSalesPerson`, `removeSalesPerson`, `setActive`, `computeAllocations(items)`, `allItemsAssigned(items)`, `reset`, `clearSelection`.
- **Endpoints:** `ecs_posnext.api.pos_profile.get_sales_persons`
- **UI:** `components/sale/SalesPersonsPanel.vue`. On mobile it gets its own "sellers" tab.

#### `posUI` (`stores/posUI.js`, ~190 lines)
- **Role:** Visibility flags for every dialog on the sale screen, the global error dialog, the success dialog and responsive layout.
- **State:**
  - Dialog flags: `showPaymentDialog`, `showCustomerDialog`, `showOpenShiftDialog`, `showCloseShiftDialog`, `showDraftDialog`, `showReturnDialog`, `showCouponDialog`, `showOffersDialog`, `showBatchSerialDialog`, `showHistoryDialog`, `showOfflineInvoicesDialog`, `showCreateCustomerDialog`, `showClearCartDialog`, `showLogoutDialog`, `showItemSelectionDialog`, `showErrorDialog`, `showSuccessDialog`.
  - Error dialog: `errorDialogTitle`, `errorDialogMessage`, `errorDetails`, `errorType`, `errorRetryAction`.
  - Last sale: `lastInvoiceName`, `lastInvoiceTotal`, `lastPaidAmount`.
  - Layout: `mobileActiveTab`, `windowWidth`, `isDesktop` (1024 px or wider), `onePage`.
- **Getters:** `isAnyDialogOpen`.
- **Actions:** `showError(title, message, details, type, retryAction, retryData)`, `clearError`, `showSuccess`, `resetAllDialogs`, `setMobileTab`, ...
- **Endpoints:** none.

#### `posSync` (`stores/posSync.js`, ~445 lines)
- **Role:** UI-facing offline status, the pending invoice queue, and the offline preload.
- **State:** `isOffline`, `connectionQuality`, `pendingInvoicesCount`, `pendingInvoicesList`, `isSyncing`.
- **Getters:** `hasPendingInvoices`.
- **Actions:**
  - Queue: `saveInvoiceOffline`, `loadPendingInvoices`, `deleteOfflineInvoice`, `syncAllPending`.
  - Preload: `preloadDataForOffline(profile)` (items, customers, payment methods, invoice history and unpaid-invoice caches), `checkOfflineCacheAvailability`, `checkCacheReady`, `getCacheStats`.
- **Behaviour:** It subscribes to `offlineState` for the app's lifetime and **auto-syncs invoices** on an offline-to-online transition. It does not auto-sync operations.
- **Endpoints:**
  - `ecs_posnext.api.customers.get_customers`
  - `ecs_posnext.api.invoices.get_invoices`
  - `ecs_posnext.api.partial_payments.get_unpaid_invoices`
  - `ecs_posnext.api.partial_payments.get_unpaid_summary`
  - sync itself goes through `utils/offline/sync.js` (see §4)

#### `posDrafts` (`stores/posDrafts.js`, ~110 lines)
- **Role:** Draft carts kept on the device.
- **State:** `drafts`, `draftsCount`.
- **Actions:** `saveDraftInvoice`, `loadDrafts`, `loadDraft`, `deleteDraftById`, `updateDraftsCount`.
- **Storage:** IndexedDB `ecs_posnext_drafts` through `utils/draftManager.js`. It makes no server calls. Server-side draft cleanup is `ecs_posnext.api.invoices.cleanup_old_drafts` in `useInvoice`.

#### `posEvents` (`stores/posEvents.js`, ~450 lines)
- **Role:** An in-process pub/sub bus with history (100 events).
- **Actions:**
  - `on`, `off`, `emit`, `emitBatch`.
  - `detectSettingsChanges(new, old)` diffs the settings and emits `settings:*` events.
  - `updateSettingsSnapshot`, `emitStockSyncConfigured`, `emitStockSyncStatus`.
  - Pending-reload tracking: `isReloadPending`, `markReloadCompleted`.
- **Events:** `settings:changed`, `settings:warehouse-changed`, `settings:stock-policy-changed`, `settings:pricing-changed`, `settings:display-changed`, `settings:sales-operations-changed`, `settings:sync-configured`, `sync:stock-updated`.
- **Wrapper:** `composables/usePOSEvents.js` provides helpers such as `onWarehouseChanged` and `onPricingChanged`, and unsubscribes automatically on unmount.
- **Endpoints:** none.

#### `itemSearch` (`stores/itemSearch.js`, ~2,140 lines)
- **Role:** The item catalogue. It covers browsing (paged, per item group), search (cache plus server, debounced), barcode lookup, sorting, background caching of large catalogs, and reacting to POS Profile changes.
- **State:** `allItems`, `searchResults`, `searchTerm`, `selectedItemGroup`, `itemGroups`, `profileItemGroups`, `loading`, `loadingMore`, `searching`, `sortBy`, `sortOrder`, `currentOffset`, `hasMore`, `totalServerItems`, `cacheReady`, `cacheSyncing`, `cacheStats`, `serverDataFresh`.
- **Getters:** `itemsPerPage` (20, 50 or 100, from `performanceConfig`), `filteredItems` (memoised, with an LRU cache).
- **Actions:**
  - Loading: `loadAllItems(profile, forceServerFetch)`, `fetchItemsForGroup`, `fetchItemsFromGroups`, `fetchPage`, `loadMoreItems`.
  - Search: `searchItems(term)`, `searchByBarcode`, `getItem`, `loadItemGroups`.
  - Background cache: `startBackgroundCacheSync` / `stopBackgroundCacheSync`.
  - Profile changes: `handlePosProfileUpdateWithRecovery`, `attemptFullCacheRecovery`.
  - Item registration also initialises entries in the `stock` store.
- **Endpoints:**
  - `ecs_posnext.api.items.get_items`, `ecs_posnext.api.items.get_items_bulk`, `ecs_posnext.api.items.get_items_count`
  - `ecs_posnext.api.items.get_item_groups`, `ecs_posnext.api.items.search_by_barcode`
  - `ecs_posnext.api.items.get_item_variants`, `ecs_posnext.api.items.get_batch_serial_data_for_items`
  - `ecs_posnext.api.pos_profile.get_pos_profile_data`
- **Realtime:** `pos_profile_updated`, through `useRealtimePosProfile`.
- See [LARGE_CATALOG_OPTIMIZATION.md](docs/LARGE_CATALOG_OPTIMIZATION.md).

#### `stock` (`stores/stock.js`, ~195 lines)
- **Role:** Display stock = server stock − reserved (in-cart) stock. It is a cache; the server is the source of truth.
- **State:** `server` (Map of item to `{qty, warehouse, ts}`), `reserved` (Map), `warehouse`, `refreshing`.
- **Actions:** `init`, `reserve`, `update(stockData)` (called from realtime events), `refresh(itemCodes?)` (after its own sale, a manual refresh or a warehouse change), `getDisplayStock`, `getStockInfo`. It listens to `settings:warehouse-changed`.
- **Endpoints:** `ecs_posnext.api.items.get_stock_quantities`

#### `customerSearch` (`stores/customerSearch.js`, ~425 lines)
- **Role:** An in-memory customer index with fast matching, recent and frequent customers, and recommendations.
- **State:** `allCustomers`, `searchTerm`, `selectedIndex`, `recentSearches`, `frequentCustomers`, `loading`.
- **Getters:** `filteredCustomers`, `recommendations`.
- **Actions:**
  - `loadAllCustomers(posProfile, forceReload)` (worker cache first, then the server).
  - `addCustomerToCache`, `trackCustomerSelection`, `loadCustomerHistory`, `setSearchTerm`, `clearSearch`.
- **Endpoints:** `ecs_posnext.api.customers.get_customers`
- **Realtime:** `pos_customer_changed`.

#### `serialNumber` (`stores/serialNumber.js`, ~215 lines)
- **Role:** A per-item cache of available serial numbers, invalidated when the warehouse changes or a serial is sold.
- **Actions:** `fetchSerials`, `getSerials`, `consumeSerials`, `returnSerials`, `prefetchSerials`, `setWarehouse`, `clearCache`, `isCacheValid`.
- **Endpoints:** `frappe.client.get_list` (Serial No).

#### `invoiceFilters` (`stores/invoiceFilters.js`, ~325 lines)
- **Role:** Filter state for invoice lists: date presets, customer, status, product, search term, and saved presets in `localStorage.pos_invoice_filters`.
- **Endpoints:** none. It is used by `composables/useInvoiceFilters.js` and `components/invoices/InvoiceFilters.vue`.

#### `countries` (`stores/countries.js`, ~160 lines)
- **Role:** The country list with ISD codes and flags, plus phone-number parsing, formatting and validation.
- **Endpoints:** `frappe.geo.country_info.get_country_timezone_info`

---

### 8.3 Composables

| Composable | Responsibility | Endpoints |
|------------|----------------|-----------|
| `useInvoice.js` (~1,330 lines) | The cart engine behind `posCart`. Covers adding, removing and updating items, rates, item and cart discounts, the tax cache and recalculation, UOM pricing, payments, stock validation, `buildInvoicePayload`, and the two-step `submitInvoice` (update, then submit) guarded by a shared `CoalescingMutex`. Also handles the default customer, `loadTaxRules` and draft cleanup. | `ecs_posnext.api.invoices.update_invoice`, `.submit_invoice`, `.validate_cart_items`, `.apply_offers`, `.cleanup_old_drafts`; `ecs_posnext.api.items.get_item_details`; `ecs_posnext.api.pos_profile.get_taxes`, `.get_default_customer` |
| `useShift.js` | Module-level `shiftState`. Checks, opens and closes shifts, keeps `localStorage.pos_shift_data` and caches the opening-dialog data (`OPENING_DIALOG_CACHE_KEY`) so a shift can be **opened and closed offline** (`enqueueOperation("open_shift" / "close_shift")`). | `ecs_posnext.api.shifts.check_opening_shift`, `.get_opening_dialog_data`, `.create_opening_shift`, `.get_closing_shift_data`, `.submit_closing_shift` |
| `useOffline.js` | Component-friendly wrapper around `offlineState` and the queues: pending counts, `syncPending`, `syncPendingOperations`, cached search. | none directly (`utils/offline/*`) |
| `useLocale.js` | Current locale and direction (`ltr`/`rtl`), allowed locales and language switching. Persists `ecs_posnext_language`. | `ecs_posnext.api.localization.get_allowed_locales`, `.get_user_language`, `.change_user_language` |
| `useRealtimeStock.js` | Singleton listener for `pos_stock_update` and `pos_invoice_created`, with batching and deduplication. Exposes `onStockUpdate(handler)`, which returns a cleanup function. | (Socket.IO) |
| `useRealtimePosProfile.js` | Singleton listener for `pos_profile_updated`, with retry. | (Socket.IO) |
| `useRealtimeCustomers.js` | Singleton listener for `pos_customer_changed`, with retry. | (Socket.IO) |
| `usePOSEvents.js` | Wrapper around the `posEvents` bus that cleans up on unmount. | none |
| `useCashDrawer.js` | `openDrawer()`, with a module-level guard and a 1 s cooldown. Used by the F7 shortcut and the header button. | through `utils/qzTray.js` |
| `usePermissions.js` | `usePermissions` / `usePOSPermissions`: reactive doctype permission checks. | `frappe.client.has_permission` |
| `useCountryCodes.js` | Country dial codes (globally cached). | `frappe.geo.country_info.get_country_timezone_info` |
| `usePaymentNumpad.js` | Numpad state and **window keyboard input** for the payment dialog (digits, `.` or `,`, Backspace, Delete or Escape to clear, Enter to confirm). Ignored while focus is in an input. | none |
| `useResponsivePayment.js` | Viewport tracking and sizing for the payment dialog. | none |
| `useSearchInput.js` | Search box, barcode-scanner detection and auto-add, with timers and concurrency control (extracted from `ItemsSelector`). | none (through `itemSearch`) |
| `useCartSort.js` | Sort options and state for the cart (order of addition, name, ...). | none |
| `useDialogState.js` | Global registry of open dialogs, used for example to hide the draggable divider. | none |
| `useFormatters.js` | Currency, date and number formatters, and `localDateString`. | none |
| `useInvoiceFilters.js` | Applies the `invoiceFilters` store to an invoice array. | none |
| `useStock.js` | Stock badge styling by quantity level. | none |
| `useTheme.js` | Light and dark mode through `data-theme`. Persists `ecs_posnext_theme` and follows OS changes. | none |
| `useToast.js` | Queued toasts (4 s each), rendered by `components/common/Toast.vue`. | none |
| `usePWAInstall.js` | `beforeinstallprompt` handling for `InstallAppBadge`. | none |
| `useLazyLoad.js` | IntersectionObserver image lazy-loading (`LazyImage.vue`). | none |
| *Unused:* `useItems.js`, `usePosProfile.js`, `useSalesPersons.js`, `usePaymentCalculations.js`, `useQuickAmounts.js`, `useLongPress.js` | Upstream leftovers that nothing imports. They still reference `ecs_posnext.api.items.get_items/get_item_groups/search_by_barcode`, `ecs_posnext.api.pos_profile.get_pos_profiles/get_pos_profile_data`, and `ecs_posnext.api.pos_profile.get_sales_persons`. | |

---

### 8.4 Utils of note

#### Networking and session
- `utils/apiWrapper.js`: `call(method, params)`, a frappe-ui `call` with a CSRF auto-refresh retry.
- `utils/csrf.js`: `getCSRFTokenFromCookie`, `ensureCSRFToken`, `forceRefreshCSRFToken`, `createCSRFAwareRequest`, `onCSRFTokenRefresh`. Endpoint: `/api/method/ecs_posnext.api.utilities.get_csrf_token`.
- `data/session.js`:
  - `session.login` (`login`) and `session.logout` (`logout`)
  - `session.isLoggedIn`
  - `isAdministrator`, a UI-only check that hides admin-only shortcuts
- `data/user.js`: `userResource` (`frappe.auth.get_logged_user`), and `userData`, built from the `user_id`, `full_name` and `user_image` cookies.
- `utils/errorHandler.js`: `parseError`, `handleApiError`, `formatErrorReport`, which turn Frappe exceptions into a title, message and technical details.

#### Money and numbers
- `utils/currency.js`:
  - `initPrecision` (from bootstrap), `formatCurrency`, `round`, `roundCurrency`, `roundFloat`
  - rounding methods that match ERPNext System Settings (including Banker's rounding)
- `utils/payment.js`: `getPaymentIcon`, `applyPaymentTopUp`, `applyPaymentReduction`.
- `utils/invoice.js`: invoice status colours and themes, and `canUpdatePaymentMode`. It also references `ecs_posnext.api.invoices.update_invoice_payment_mode`.
- `utils/shiftDay.js`: `shiftDayOf()`. A shift day runs from 09:00 to 09:00, so a shift opened after midnight belongs to the previous calendar date.
- `utils/stockValidator.js`: `checkStockAvailability`, `validateCartStock`. Uses `frappe.client.get_value`.

#### Printing and reports
[Frontend components](#9-frontend-components) has the printing details.
- `utils/printInvoice.js`: `printInvoice`, `printInvoiceByName`, `silentPrintInvoice`, `printWithSilentFallback`, `autoPrintInvoice`, `downloadInvoicePDF`, `printInvoiceCustom`.
- `utils/qzTray.js`: the QZ Tray client.
- `utils/printClosingShift.js`: `openClosingShiftPrintView`, `printLastClosingShift`. Uses `ecs_posnext.api.shifts.get_last_closing_shift`.
- `utils/printBranchExpenses.js`: prints the "مصاريف الفروع" report alongside the Z-report. Uses `ecs_posnext.api.reports.run_pos_report` and `.get_print_template`.
- `utils/reportOutput.js`: report cell formatting, `exportReport` (through `/api/method/frappe.desk.query_report.export_query`), `printReport`, `openPrintWindow`, `printHtmlString`.
- `utils/reportPrintFormat.js` and `utils/microtemplate.js`: render report Print Formats of type **JS** in the browser with a port of Frappe's client-side microtemplate engine, the same way the desk renders them (not with Jinja).

#### Performance
- `utils/performanceConfig.js`: device tier detection (CPU cores, memory). Drives `itemsPerPage` and other settings. Persisted in `pos_performance_tier`.
- `utils/lowEndOptimizations.js`: `runWhenIdle`, `debounceRAF`, `throttleRAF`, `processArrayInChunks`, `domBatcher`, `isLowEndDevice`.
- `utils/mutex.js`:
  - `CoalescingMutex`: concurrent callers share the result of the run in progress.
  - `QueuedMutex`: callers run one after another.

#### Infrastructure
- `utils/logger.js`: namespaced logger. It is silent in production unless the `localStorage` `POS_LOGGING_ENABLED` flag (and level and namespace keys) are set.
- `utils/translation.ts`: translation plugin, `__()`, `translationVersion` (bumping it re-keys `<router-view>`), `changeLanguage`. Endpoint: `ecs_posnext.api.localization.get_app_translations`.
- `utils/draftManager.js`: the draft IndexedDB (`ecs_posnext_drafts`).

#### Offline
[§7.6 Offline layer](#76-offline-layer) covers `utils/offline/*`. Their endpoints:
- `sync.js`: `ecs_posnext.api.ping`, `ecs_posnext.api.invoices.check_offline_invoice_synced`, `ecs_posnext.api.invoices.submit_invoice`
- `syncOps.js`: `ecs_posnext.api.offline_ops.is_op_synced`
- `opHandlers.js`:
  - `ecs_posnext.api.shifts.create_opening_shift`, `.submit_closing_shift`, `.get_closing_shift_data`
  - `ecs_posnext.api.employee_attendance.mark_employee_attendance`, `.convert_attendance_to_half_day`
  - `ecs_posnext.api.daily_payment.create_daily_payment`
  - `ecs_posnext.api.customers.create_customer`
  - `ecs_posnext.api.offline_ops.is_op_synced`
- `cache.js`: `ecs_posnext.api.items.get_items`, `ecs_posnext.api.customers.get_customers`, `ecs_posnext.api.pos_profile.get_payment_methods`
- `offlineState.js`: `/api/method/ecs_posnext.api.ping`
- `workers/offline.worker.js`: `/api/method/ecs_posnext.api.ping`, `/api/method/ecs_posnext.api.items.get_stock_quantities`

---

### 8.5 Worker message types

`offlineWorker` (`utils/offline/workerClient.js`) sends the following messages to the `switch` in `workers/offline.worker.js`:

| Group | Message types |
|-------|---------------|
| Session and connectivity | `SET_CSRF_TOKEN`, `PING_SERVER`, `CHECK_OFFLINE`, `SET_MANUAL_OFFLINE` |
| Invoices | `GET_INVOICE_COUNT`, `GET_INVOICES`, `SAVE_INVOICE`, `DELETE_INVOICE` |
| Items and customers | `SEARCH_ITEMS`, `SEARCH_ITEMS_BY_GROUP`, `COUNT_ITEMS_BY_GROUP`, `SEARCH_CUSTOMERS`, `CACHE_ITEMS`, `CACHE_CUSTOMERS`, `DELETE_CUSTOMERS`, `CLEAR_ITEMS_CACHE`, `CLEAR_CUSTOMERS_CACHE`, `REMOVE_ITEMS_BY_GROUPS` |
| Payment methods | `CACHE_PAYMENT_METHODS`, `GET_PAYMENT_METHODS` |
| Cache status | `IS_CACHE_READY`, `GET_CACHE_STATS`, `GET_METRICS` |
| Stock | `UPDATE_STOCK_QUANTITIES`, `START_STOCK_SYNC`, `STOP_STOCK_SYNC`, `CONFIGURE_STOCK_SYNC`, `GET_STOCK_SYNC_STATUS`, `TRIGGER_STOCK_SYNC` |
| Offers | `CACHE_OFFERS`, `GET_CACHED_OFFERS`, `CLEAR_OFFERS_CACHE` |

The worker posts these back without a request: `WORKER_READY`, `STOCK_SYNC_COMPLETE` and `STOCK_SYNC_ERROR`. `POSSale.vue` handles the last two in `handleStockSyncComplete` and `handleStockSyncError`.

---

## 9. Frontend components

### Screen structure

`pages/POSSale.vue` (~2,860 lines) is the whole cashier screen. It mounts:

| Area | Components |
|---|---|
| Header | `pos/POSHeader.vue`: shift timer, sync/offline status, cash-drawer button, user menu, language and theme |
| Left: catalogue | `sale/ItemsSelector.vue` (grid/list, search, barcode, item groups; uses `itemSearch` store), `ItemSelectionDialog`, `BatchSerialDialog`, `WarehouseAvailabilityDialog` |
| Right: cart | `sale/InvoiceCart.vue` (lines, qty/rate/discount edits via `EditItemDialog`, customer, sales persons via `SalesPersonsPanel`, coupons, offers) |
| Checkout | `sale/PaymentDialog.vue` (~2,770 lines): modes, quick amounts, numpad, change, credit/partial, wallet, print |
| Customers | `CustomerDialog`, `CreateCustomerDialog` (inline entry, works offline) |
| Invoices | `DraftInvoicesDialog`, `InvoiceHistoryDialog`, `OfflineInvoicesDialog`, `ReturnInvoiceDialog`, `invoices/InvoiceManagement.vue` + `InvoiceDetailDialog`, `sale/UpdatePaymentModeDialog.vue` (fork: change the mode of payment of a submitted invoice) |
| Promotions | `OffersDialog`, `CouponDialog`, `CouponManagement`, `PromotionManagement` |
| Management | `pos/ManagementSlider.vue`, a slide-over hub for Invoice Management, Products and Promotions |
| Shift | `ShiftOpeningDialog.vue`, `ShiftClosingDialog.vue` (~1,150 lines: working-day window, gross/net sales, per-mode reconciliation, prints the branch-expenses report) |
| Fork screens | `daily_payment/DailyPaymentManagement.vue` + `DailyPaymentForm.vue`, `daily_payment/EmployeeAttendance.vue`, `daily_payment/TrackInvoices.vue`, `reports/POSReports.vue` + `ReportFilterField.vue` |
| Settings | `settings/POSSettings.vue` (driven by `settingsConfig.js`) |
| Shared | `components/common/*`: Toast, ActionButton, LazyImage, AutocompleteSelect, StatusBadge, ClearCacheOverlay, InstallAppBadge, … |

### Keyboard

- **F7** opens the cash drawer (`useCashDrawer`, handled in `POSSale.vue`, with `preventDefault` because Firefox uses
  F7 for caret browsing).
- **Enter / Escape** confirm and dismiss in the search, cart, customer, return and payment numpad inputs.
- The F4 / F8 / F9 shortcuts mentioned in `README.md` do not exist in the code.

### Printing

- Browser printing renders the `POS Next Receipt` / site default print format.
- **Silent printing** goes through **QZ Tray**. Signing material comes from `api.qz_signing`
  (see [docs/QZ_TRAY_SIGNING.md](docs/QZ_TRAY_SIGNING.md)). Latency notes are in
  [docs/PRINT_LATENCY_ANALYSIS.md](docs/PRINT_LATENCY_ANALYSIS.md).
- A draft marked printed (`posa_is_printed`) is submitted automatically when the shift closes.
- Report prints come from `api.reports.render_report_print`. The closing dialog prints `مصاريف الفروع` through
  `utils/printBranchExpenses.js`.

---

## 10. Known issues

Found while reading the code on 2026-11-02. None of them has been fixed. Verify each one before acting on it.

### Backend

1. **Duplicate report name.** Both `ecs_posnext` (module POS Next, standard) and `ecs_heshamrabea` (module
   ecs_heshamrabea) ship a report named **POS Closing Shift (Branch)**. Each migrate syncs both JSON files onto the
   same Report record, so the result depends on app order. ecs_heshamrabea's after-migrate patch then sets it non-standard.
2. **Hard-coded master data.** The Mode of Payment `بنك CIB فيزا` and the item code `Tip` are hard-coded in
   `_compute_daily_payments_and_tip` and the correction tools. The account `صندوق عمولات المساعدين - HR` is hard-coded
   in `get_branch_balance`, and the account prefixes `خزينة فرع` / `خزينة مدير فرع` in the cash transfer.
3. `_compute_daily_payments_and_tip` contains the Visa / `actual_amount` calculation twice (harmless duplicate).
4. The auto cash transfer Payment Entry uses `posting_date = today()`, not the shift's posting date. A shift closed
   after midnight posts the transfer on the next calendar day.
5. Permission gaps in whitelisted methods:
   - `shifts.check_opening_shift(user)` accepts any user;
   - `shifts.get_shift_invoices` does not check an explicit `pos_opening_shift` against the caller;
   - `daily_payment.get_daily_payment_detail` uses `frappe.get_doc` without a permission check;
   - `daily_payment.employee_query` and `get_branch_balance` do not filter by permission;
   - `employee_attendance.mark_employee_attendance` has no role check.
6. `qz_signing.get_signing_material` returns the **private key** to any logged-in user unless
   `qz_tray_server_side_signing` is set in site_config.
7. `validations.item_query` (registered site-wide as the Item standard query) interpolates `searchfield` into SQL.
8. `mark_employee_attendance` ignores the shift sent by the client and always uses the default Shift Type.
9. The POS depends on DocTypes and fields from `ecs_heshamrabea` (`Daily Payment`, `General Expenses`,
   `POS Profile.branch`, `Payment Entry.custom_pos` / `custom_mode_of_payment_to`, `Item Sorting`), but this is not
   declared in `required_apps`.
10. `pos_next/page/test_page` is an empty leftover.
11. `README.md` / `FEATURES.md` describe upstream POS Next (F4/F8/F9 shortcuts and similar). They do not describe the
    fork features documented here.

### Frontend

1. **Only F7 is a global keyboard shortcut.** There are no F4, F8 or F9 bindings anywhere in `src/`. The only `F*` strings in the built bundle are a library key-name table. See [Frontend components](#9-frontend-components).
2. **Operations are not auto-synced on reconnect, and ordering can break.** `posSync` auto-syncs only `invoice_queue` on an offline-to-online transition. `operation_queue` (`open_shift`, `customer`, ...) is flushed only from `OfflineInvoicesDialog` or `useOffline`. `OfflineInvoicesDialog.syncAll()` emits the invoice sync *before* syncing operations. An invoice that references an offline-opened shift or an offline-created customer can therefore be submitted with a temporary name before the remapping in `opHandlers.onSynced` has run.
3. **The realtime stock listener can miss the socket.** `main.js` creates `window.frappe.realtime` only after the non-awaited bootstrap finishes. `useRealtimeStock.startListening()` gives up (with a warning) if the socket is absent when `POSSale` mounts, and it has no retry, unlike the profile and customer composables. The stock listener is then inactive until `onStockUpdate` is registered again.
4. **The socket URL is built at build time and uses a heuristic.** `socket.js` imports `sites/common_site_config.json` at build time, so the port is baked into the bundle and the build fails outside a bench. Any page URL with an explicit port is assumed to be plain `http` on `socketio_port`. HTTPS on a non-default port will not connect.
5. **Service worker scope does not cover the page.** `sw.js` is served from `/assets/ecs_posnext/pos/`, and no `Service-Worker-Allowed` header was found in the backend. The SW's scope therefore excludes `/pos`, so the `/pos*` navigation rule and `start_url` probably do not take effect for page loads. Offline reloads of `/pos` may then depend on the HTTP cache.
6. **The `/api/*` NetworkFirst cache (24 h)** stores GET API responses in Cache Storage. That includes per-user and per-profile data, which can be served stale when the network is slow (timeout 10 s). It is not partitioned by user.
7. **Raw worker copy.** `viteStaticCopy` copies `src/workers` unbundled into `public/pos/workers/`, and Workbox precaches it. The app uses the bundled `assets/offline.worker-<hash>.js`. The raw copy is dead weight, and its relative imports (`../utils/logger`) would not resolve if anything loaded it.
8. **Hardcoded site-specific values.** These include:
   - customer group `"أفراد"` (`CreateCustomerDialog.vue`, `PaymentDialog.vue`)
   - default item group `"التشغيل"` (`ItemsSelector.vue`)
   - report names `"مصاريف الفروع"` and `"تقفيل الفنيين"`, and the `view_by` value `"شيفت"` (`utils/printBranchExpenses.js`, `ShiftClosingDialog.vue`)
   - loan product `"سلفة من الراتب"` (`DailyPaymentForm.vue`)
   - cash detection by the name substrings `cash`, `نقد` and `نقدي` (`PaymentDialog.vue`)

   These break or behave differently on a site with different master data.
9. **Formatting bug in a translated string.** `POSSale.vue` `handleSyncAll` uses `"Failed to sync invoice for {0}\n\n${1}..."` in a plain string literal, so a literal `$` is shown before the error message.
10. **Dead code:**
    - `pages/Home.vue` (not routed)
    - `components/partials/PartialPayments.vue`, `components/common/PhoneInput.vue`, `components/settings/SettingsSection.vue` (never rendered)
    - composables `useItems`, `useLongPress`, `usePaymentCalculations`, `usePosProfile`, `useQuickAmounts`, `useSalesPersons` (never imported)
    - the `drafts` Dexie table
    - the `__BUILD_VERSION__` define
    - the unused `shiftState` import in `router.js`

    Dead files still get auto-registered and type-generated, which can mislead readers.
11. **Two "version" values.** The header shows `package.json` `version`, while cache busting uses `version.json`. A rebuild without a version bump changes only the latter. `gen_theme.py` has an absolute hardcoded ROOT path.
12. **Very large single-file components.** `POSSale.vue` (~2,860 lines), `PaymentDialog.vue` (~2,770), `InvoiceCart.vue` (~2,020), `ReturnInvoiceDialog.vue` (~1,900), plus the stores `itemSearch.js` (~2,140) and `posCart.js` (~1,790). Changes there need care: there are many watchers and cross-store side effects.
13. **The jinja boot loop is empty.** No `www/pos.py` exists to supply `boot`, so `window.csrf_token` and `window.site_name` are never injected. The app works around this (cookie or `get_csrf_token`, and the site name from bootstrap), but the socket is created only after bootstrap succeeds. When the POS boots offline there is no socket at all, which is expected, but nothing creates it later when the connection returns.

---

## 11. Related documents

Existing topic guides in `docs/`, kept as separate deep-dives:

| Document | Topic |
|---|---|
| [STARTUP_SEQUENCE.md](docs/STARTUP_SEQUENCE.md) | Boot timeline: service worker, parallel CSRF + user, bootstrap preload |
| [OFFLINE_SYNC.md](docs/OFFLINE_SYNC.md) | Offline invoice queue, `offline_id` deduplication, IndexedDB |
| [PRICING_AND_SUBMISSION.md](docs/PRICING_AND_SUBMISSION.md) | Rate vs price-list rate, tax modes, discounts, submit flow |
| [OFFERS_AND_PROMOTIONS.md](docs/OFFERS_AND_PROMOTIONS.md) | Pricing Rules, Promotional Schemes, offers store |
| [Wallet-System-Technical-Guide.md](docs/Wallet-System-Technical-Guide.md) / [Wallet-Loyalty-User-Guide.md](docs/Wallet-Loyalty-User-Guide.md) | Wallet and loyalty |
| [LOCALIZATION.md](docs/LOCALIZATION.md) | Languages and the switcher |
| [LARGE_CATALOG_OPTIMIZATION.md](docs/LARGE_CATALOG_OPTIMIZATION.md) | Background item sync for 65K+ items |
| [QZ_TRAY_SIGNING.md](docs/QZ_TRAY_SIGNING.md) | QZ Tray certificate and signing |
| [PRINT_LATENCY_ANALYSIS.md](docs/PRINT_LATENCY_ANALYSIS.md) | Submit-to-receipt latency |
| [VERSION_CONTROL.md](docs/VERSION_CONTROL.md) / [QUICKSTART_VERSION.md](docs/QUICKSTART_VERSION.md) | Versioning and releases |
| `SUBMIT_INVOICE_ANALYSIS.md`, `qz_cert_implementation_spec.md`, `chat/*.md`, `CHANGELOG.md` | Design notes and history |
