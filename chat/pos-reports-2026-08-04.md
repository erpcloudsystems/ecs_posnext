# Reports in POS - 2026-08-04

## Summary
Added a configurable Reports feature to the POS: a new Single DocType selects which Frappe/ERPNext reports are exposed, a Reports icon sits below Employee Attendance in the management sidebar, and picking a report opens it inside the POS with its own filter bar plus Excel, CSV and Print buttons.

## Changes Made

### New DocType: `POS Report Settings` (Single, module POS Next)
- `enable_reports_in_pos` (Check, default 1) — master switch that hides the POS Reports button for every profile
- `reports` (Table → `POS Report Setting Item`)
- `validate()` rejects duplicate `(report, pos_profile)` rows — including a profile-specific row that collides with an all-profiles row for the same report — and rejects disabled reports, which could only dead-end the cashier
- `get_pos_report_rows(pos_profile)` module function returns the enabled rows for a profile, honouring the master switch. Rows with a blank POS Profile apply everywhere; a profile-scoped row is skipped when the caller did not say which profile it is running for
- `pos_report_settings.js` filters the Report link field to `disabled: 0`

### New DocType: `POS Report Setting Item` (child table)
`report` (Link → Report, required), `label` (POS display override), `icon` (Feather icon name, default `bar-chart-2`), `pos_profile` (optional scope), `enabled` (default 1), plus read-only `report_type` / `ref_doctype` fetched from the report.

### New: `ecs_posnext/api/reports.py`
Whitelisted endpoints:
- `get_pos_reports(pos_profile)` — configured reports the current user may actually run, each with `can_export`
- `get_report_definition(report_name, pos_profile)` — label, report type, ref doctype, `add_total_row`, `can_export`, and normalised filter definitions
- `run_pos_report(report_name, filters, pos_profile)` — wraps `frappe.desk.query_report.run`
- `search_filter_options(doctype, txt, ...)` — Link lookup for the filter bar, wrapping `frappe.desk.search.search_link`

Filter resolution (the substantial part): the POS has no desk bundle, so it cannot evaluate a Script Report's `.js` the way `query_report.js` does. Filters are resolved server side from the Report's own `filters` child table when it has one, otherwise by parsing the `filters: [...]` literal out of the report script. The parser is a small JS-literal reader (string/comment/nesting aware, balanced-bracket slicing) plus an evaluator for the handful of expressions ERPNext uses in defaults: `__()`, `frappe.datetime.get_today/month_start/month_end/year_start/year_end/add_days/add_months`, `frappe.defaults.get_user_default/get_default`. Anything else resolves to no default rather than a guess.

Normalised filter shape is deliberately unambiguous instead of the desk's polymorphic `options`:
- `values` — a fixed list to pick from (Select, or a MultiSelectList declared with an array)
- `link_doctype` — the doctype to search
- `link_doctype_from` — the sibling filter that supplies the doctype at runtime (General Ledger's Party follows Party Type)
- Unrenderable fieldtypes (Autocomplete, Dynamic Link) and Selects whose options are built at runtime (currency lists) degrade to `Data`, so the value can still be typed

### New: `POS/src/components/reports/POSReports.vue`
Full-height dialog with two states — a searchable grid of configured reports, and the report viewer (filter bar, toolbar, result table). Runs automatically on open unless a mandatory filter has no default. Numeric columns are right-aligned, hidden columns dropped, the server-appended total row highlighted, and the report's `message` rendered through `TranslatedHTML` (DOMPurify).

### New: `POS/src/components/reports/ReportFilterField.vue`
One widget per fieldtype: Check, DateRange (emits `[from, to]`), Date/Datetime/Time, Select, numeric, Link (`AutocompleteSelect` with server search, primed on first focus via `focusin`), MultiSelectList (chips, typed or picked), and Data as the fallback. Receives all current filter values so `link_doctype_from` can be resolved.

### New: `POS/src/utils/reportOutput.js`
- `formatReportValue` / `getCellValue` / `isNumericColumn` / `visibleColumns` — shared by the on-screen table and the print layout. Rows may be keyed by fieldname or label, or be plain arrays. Dates are reordered by string, never parsed through `Date()`, which would shift the day behind UTC
- `exportReport` — form POST to `frappe.desk.query_report.export_query` targeting a hidden iframe
- `printReport` — builds a landscape A4 HTML table (escaped) from the loaded rows and prints it from a hidden iframe, carrying `document.documentElement.dir` for RTL

### `POS/src/components/pos/ManagementSlider.vue`
Added a `pie-chart` Reports button below Employee Attendance, emitting `menu-clicked` with `reports`.

### `POS/src/pages/POSSale.vue`
Imported `POSReports`, added `showReports` ref, rendered the dialog with `:pos-profile` / `:branch`, and handled `reports` in `handleManagementMenuClick`.

### `ecs_posnext/pos_next/workspace/posnext/posnext.json`
Added a **POS Report Settings** link under Configuration (`link_count` 2 → 3) and bumped `modified` so `bench migrate` picks the change up.

## Decisions / Notes
- **Export reuses the framework endpoint** rather than generating files here, so a POS export is byte-for-byte what the desk produces. It answers with a file attachment instead of JSON, hence the form POST; the target is a hidden iframe, not the top window, because a failed export would otherwise navigate the POS away mid-shift. The iframe is read back on `load` (same origin) to surface the server's message — a real download fires no `load` event.
- The "off" export flags are posted as `""`, not `"0"`: `export_query` tests some of them for truthiness before `cint`, and `"0"` is a truthy string (it was appending filter values to the download filename).
- `run_pos_report` passes `ignore_prepared_report=True` (the POS has no Prepared Report inbox) and `are_default_filters=False` so a Custom Report honours what the cashier picked instead of its saved filter values.
- Endpoints refuse reports that are not listed in POS Report Settings, so they cannot be used to run arbitrary reports. Report permissions are otherwise the desk's: the report's Roles table, `report` on the Ref DocType, `export` before the export buttons appear.
- Reports need connectivity — the dialog says so when offline rather than showing an empty list.
- Print builds from the loaded result rather than re-running the report, so what prints is exactly what is on screen.
- **Gotcha:** do not `frappe.reload_doc(..., "workspace", ...)` on a developer_mode site. `Workspace.on_update` skips `export_to_files` while `frappe.flags.in_import` is set but still calls `delete_folder`, so the reload deleted `pos_next/workspace/posnext/` from the app. Restored from git and re-applied the edit by hand; the DB workspace already had the link. Let `bench migrate` sync workspace JSON instead.

## Verification
- `get_report_filters` checked against 14 stock ERPNext reports (Sales Register, Item-wise Sales Register/History, Gross Profit, Sales Analytics, Stock Balance/Ledger, Accounts Receivable, General Ledger, Trial Balance, Sales Person Commission Summary, Batch-Wise Balance History, Sales Order Analysis, Payment Period Based On Invoice Date) — filters, labels, defaults, mandatory flags and lookup doctypes all resolved
- `run_pos_report("Sales Register", ...)` returned 33 columns / 98 rows; duplicate-row and unconfigured-report guards both raised
- `export_query` exercised with the exact parameters the POS posts: CSV 34 KB with the expected header row, `Sales Register.xlsx` 17 KB
- Formatting helpers unit-checked with vitest (temporary spec, not committed)

## Build Status
✅ `yarn build` succeeded (52.44s)

## Follow-up Items
- The Reports button is always visible; it shows an empty state until reports are configured in POS Report Settings
- Cashier roles need `report` (and `export`, for the export buttons) permission on each report's Ref DocType
- Tree-style reports render flat — no indentation or collapsible groups
- No chart rendering; `report_summary` is returned by the endpoint but not displayed
