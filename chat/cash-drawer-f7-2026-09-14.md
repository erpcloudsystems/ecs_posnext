# Open Cash Drawer without an Invoice (F7) - 2026-09-14

## Summary
The cash drawer could only be opened by completing a sale, so giving change, dropping a float or settling a Daily Payment meant ringing up something the till did not sell. Added a direct drawer kick: **F7** anywhere in the POS, an **Open Cash Drawer** entry in the user menu, and a **Cash Drawer** block in POS Settings with a connector-pin choice and a Test button.

## Changes Made

### `POS/src/utils/qzTray.js`
New Cash Drawer section at the end of the file:
- `openCashDrawer(printerName)` — reuses the existing `requirePrinter()` (connect → saved printer → OS default → first physical), then sends a print job carrying nothing but the ESC/POS pulse. The drawer has no connection of its own; it is a solenoid on the printer's RJ11 port, so this needs QZ Tray exactly as a receipt does, and fails with the same two reasons (`QZ Tray is not available`, `No printer found on this machine`).
- `drawerKickCommand(pin)` — `ESC p m t1 t2` as **hex** (`1B 70 00 19 FA`), not a plain string. The pulse widths are bytes above 0x7F (0x19 = 50ms on, 0xFA = 500ms off, the widest the command can express, which is what the stiffer solenoids need) and any text encoding on the way to the printer would mangle them. `qz-tray.js` down-converts `{type:'raw', format:'command', flavor:'hex'}` to the 2.0 spec on its own, so this works on the Windows 7 tills still on QZ Tray 2.0.
- `getDrawerPin()` / `saveDrawerPin()` / `DRAWER_PIN_OPTIONS` — pin 2 (default) or pin 5. Stored in localStorage per till, for the same reason as the paper width: the wiring is a property of the hardware in front of the cashier, not of the POS Profile.

### New: `POS/src/composables/useCashDrawer.js`
`openDrawer()` with toast feedback, plus the guard state at **module** scope so the menu button, the F7 shortcut and the settings Test button share it. The drawer takes about a second to spring; a second pulse while it is travelling does nothing but stack a second toast, so re-opens inside 1s are dropped. Failure reasons are put through `__()` before being interpolated, so an Arabic till does not get an English clause in the middle of the message.

### `POS/src/pages/POSSale.vue`
- New **KEYBOARD SHORTCUTS** section: `keydown` on `window` rather than on a component, because the cashier reaches for F7 mid-sale, with a dialog open, or with focus in the barcode field. Bare F7 only — any modifier is left alone. `preventDefault()` matters here: F7 toggles caret browsing in Firefox, which would leave a blinking cursor roaming the till.
- **Open Cash Drawer** entry in the header user menu, after Return Invoice, with an `F7` key hint. The menu closes itself on any click inside, so no extra handling.

### `POS/src/components/settings/POSSettings.vue`
New **Cash Drawer** block, a sibling of Cash Transfer on Shift Close rather than a child of the Silent Print sub-block: the drawer needs QZ Tray but not silent printing, and a till that prints through the browser dialog can still have a drawer to configure. Contains the pin selector (persisted on change, like the paper width) and a Test button.

### `ecs_posnext/translations/ar.csv`
Arabic for the new strings, including the two `qzTray` failure reasons that now surface to the cashier.

## Decisions
- **No audit record.** Opening the drawer with no sale attached is the classic shrinkage path, and a "No Sale" log would be the usual answer. Left out deliberately — it was not asked for, and it is a doctype plus a permission story, not a line of code. Worth raising separately.
- **No permission gate.** Any user who can open the POS can open the drawer, matching the fact that they can already open it by ringing up a sale.
- **Pin 5 offered but not auto-detected.** There is no way to ask a printer which pin its drawer is on; pin 2 is right for nearly every till, and the Test button makes the other case a ten-second fix.

## Files Modified
- `POS/src/utils/qzTray.js`
- `POS/src/composables/useCashDrawer.js` (new)
- `POS/src/pages/POSSale.vue`
- `POS/src/components/settings/POSSettings.vue`
- `ecs_posnext/translations/ar.csv`

## Verification
- `npx biome check` clean on the new composable and `qzTray.js`; `POSSale.vue` and `POSSettings.vue` report the same 4 pre-existing errors as their `HEAD` versions, so nothing new was introduced.
- `yarn build` passes; the pulse command is present in the emitted `POSSale` chunk.
- Not exercised against real hardware — the pulse needs a till with QZ Tray and a drawer attached.
