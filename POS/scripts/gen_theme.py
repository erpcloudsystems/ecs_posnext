"""
Generates POS Next's theme layer:
  - POS/src/theme.css        CSS variables for light + dark
  - POS/tailwind.theme.js    Tailwind colour scales that point at those variables

Light values are copied verbatim from frappe-ui's own light palette, so light
mode renders exactly as it does today. Dark values are role-aware: a shade used
as a background flips differently from the same shade used as text, which is
what lets `bg-blue-600` stay a solid button while `text-blue-600` becomes a
legible link on a dark surface.
"""
import json, os

ROOT = "/home/frappe/frappe-bench/apps/ecs_posnext/POS"
C = json.load(open(os.path.join(ROOT, "node_modules/frappe-ui/tailwind/colors.json")))
LIGHT, DARK = C["lightMode"], C["darkMode"]

SHADES = ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900"]
ACCENTS = ["blue", "red", "green", "amber", "orange", "yellow", "purple", "teal", "violet", "cyan", "pink"]

def rgb(hex_):
    h = hex_.lstrip("#")[:6]
    return f"{int(h[0:2],16)} {int(h[2:4],16)} {int(h[4:6],16)}"

# --- gray -------------------------------------------------------------------
# Backgrounds climb monotonically, so every hover step (50->100, 600->700)
# reads as "lighter" the way it reads as "darker" in light mode.
# 50-700 climb, so every hover step (50->100, 600->700) reads as "lighter" the
# way it reads as "darker" in light mode. 800/900 break that run deliberately:
# they are the inverted-chip surfaces (tooltips, the dark Print button) and are
# always paired with `text-white`, which does not invert - so they have to stay
# dark, lifted just enough to separate from the page.
GRAY_BG_DARK = {
    "50": "#212121", "100": "#272727", "200": "#2E2E2E", "300": "#383838",
    "400": "#424242", "500": "#4A4A4A", "600": "#525252", "700": "#5C5C5C",
    "800": "#2A2A2A", "900": "#333333",
}
# Text inverts: gray-900 (near-black ink) becomes near-white.
GRAY_FG_DARK = {
    "50": "#0F0F0F", "100": "#1C1C1C", "200": "#232323", "300": "#424242",
    "400": "#717171", "500": "#8A8A8A", "600": "#A3A3A3", "700": "#C4C4C4",
    "800": "#DEDEDE", "900": "#F5F5F5",
}
GRAY_LINE_DARK = {
    "50": "#1F1F1F", "100": "#262626", "200": "#2E2E2E", "300": "#3A3A3A",
    "400": "#474747", "500": "#5A5A5A", "600": "#6E6E6E", "700": "#8A8A8A",
    "800": "#B0B0B0", "900": "#D4D4D4",
}

# --- accents ----------------------------------------------------------------
# Backgrounds: pale tints (50-300) become deep muted tints; the saturated
# fills (400-700) keep their light values so `text-white` on a primary button
# keeps exactly the contrast it has today; 800/900 lift slightly so very dark
# fills still separate from the page.
ACCENT_BG = {
    "50": ("dark", "900"), "100": ("dark", "800"), "200": ("dark", "700"),
    "300": ("dark", "600"), "400": ("light", "400"), "500": ("light", "500"),
    "600": ("light", "600"), "700": ("light", "700"), "800": ("dark", "600"),
    "900": ("dark", "700"),
}
# Coloured text brightens - but only the shades that are dark to begin with.
# 50-400 are already pale, meaning they are light-on-dark text in light mode
# (a label on a solid blue button, the red action inside the dark cache
# tooltip). Their backgrounds do not invert - a saturated fill stays saturated
# and a dark chip stays dark - so inverting the text would put dark text on a
# dark ground. Those shades keep their light values; 500-900 invert.
ACCENT_FG_KEEP_LIGHT = {"50", "100", "200", "300", "400"}
ACCENT_FG = {
    "500": "300", "600": "200", "700": "100", "800": "50", "900": "50",
}
ACCENT_LINE = {
    "50": "900", "100": "800", "200": "700", "300": "600", "400": "500",
    "500": "400", "600": "300", "700": "200", "800": "100", "900": "50",
}

light, dark = {}, {}

def put(var, l, d):
    light[var], dark[var] = rgb(l), rgb(d)

for s in SHADES:
    put(f"--pos-bg-gray-{s}",   LIGHT["gray"][s], GRAY_BG_DARK[s])
    put(f"--pos-fg-gray-{s}",   LIGHT["gray"][s], GRAY_FG_DARK[s])
    put(f"--pos-line-gray-{s}", LIGHT["gray"][s], GRAY_LINE_DARK[s])

for hue in ACCENTS:
    for s in SHADES:
        mode, shade = ACCENT_BG[s]
        put(f"--pos-bg-{hue}-{s}", LIGHT[hue][s], (LIGHT if mode == "light" else DARK)[hue][shade])
        fg_dark = LIGHT[hue][s] if s in ACCENT_FG_KEEP_LIGHT else DARK[hue][ACCENT_FG[s]]
        put(f"--pos-fg-{hue}-{s}", LIGHT[hue][s], fg_dark)
        put(f"--pos-line-{hue}-{s}", LIGHT[hue][s], DARK[hue][ACCENT_LINE[s]])

# Surfaces. `bg-white` is the card/panel surface and must go dark; `text-white`
# is left alone (it sits on solid coloured buttons), which is why background
# and text scales are declared separately.
put("--pos-surface", "#FFFFFF", "#1A1A1A")   # bg-white
put("--pos-page", LIGHT["gray"]["50"], "#0F0F0F")  # page/app background

# ---------------------------------------------------------------------------
# Tokens for the hand-written <style> blocks in InvoiceFilters,
# AutocompleteSelect, ReturnInvoiceDialog and CountryCodeSelector. Those blocks
# predate this theme layer and were written against default Tailwind colours
# rather than frappe-ui's, so each keeps its exact light value here and gains a
# dark counterpart. Emitted as whole colours, not channels, because the CSS that
# consumes them is hand-written and never needs an alpha modifier.
#
# Print templates (the Z-report in ShiftClosingDialog, utils/printInvoice.js)
# are deliberately excluded - they render onto paper and must stay light.
EXTRAS = {
    # neutrals
    "ink-strong":            ("#111827", "#F5F5F5"),
    "ink":                   ("#374151", "#D4D4D4"),
    "ink-soft":              ("#4b5563", "#B8B8B8"),
    "ink-muted":             ("#6b7280", "#A3A3A3"),
    "ink-faint":             ("#9ca3af", "#8A8A8A"),
    "line":                  ("#e5e7eb", "#2E2E2E"),
    "line-strong":           ("#d1d5db", "#3A3A3A"),
    "line-faint":            ("#f3f4f6", "#262626"),
    "fill":                  ("#ffffff", "#1A1A1A"),
    "fill-faint":            ("#f9fafb", "#212121"),
    "fill-muted":            ("#f3f4f6", "#272727"),
    "fill-subtle":           ("#fafbfc", "#1F1F1F"),
    "icon-empty":            ("#d1d5db", "#5A5A5A"),
    # scrollbars
    "scroll-track":          ("#f1f1f1", "#1F1F1F"),
    "scroll-thumb":          ("#cbd5e1", "#4A4A4A"),
    "scroll-thumb-hover":    ("#94a3b8", "#5C5C5C"),
    "scroll-thumb-alt":      ("#cbd5e0", "#4A4A4A"),
    "scroll-thumb-alt-hover":("#a0aec0", "#5C5C5C"),
    "scroll-thumb-gray":     ("#d1d5db", "#4A4A4A"),
    "scroll-thumb-gray-hover":("#9ca3af", "#5C5C5C"),
    # accent (indigo). Split by role: a fill keeps its saturation under white
    # text, the same colour used as text or a border has to brighten.
    "accent-ink":            ("#6366f1", "#A5A6FA"),
    "accent-line":           ("#6366f1", "#7B7CF4"),
    "accent-fill":           ("#6366f1", "#6366f1"),
    "accent-fill-strong":    ("#4f46e5", "#4F46E5"),
    "accent-soft":           ("#eef2ff", "#1E1B4B"),
    "accent-soft-alt":       ("#f5f3ff", "#211C4F"),
    "accent-line-soft":      ("#e0e7ff", "#312E81"),
    "accent-glow":           ("rgba(99, 102, 241, 0.1)", "rgba(139, 140, 247, 0.28)"),
    # success
    "success-ink":           ("#166534", "#9BE6C1"),
    "success-ink-alt":       ("#15803d", "#78D7A9"),
    "success-check":         ("#10b981", "#58C08E"),
    "success-fill":          ("#f0fdf4", "#0B2E1C"),
    "success-fill-hover":    ("#dcfce7", "#0A3F27"),
    "success-line":          ("#bbf7d0", "#0A3F27"),
    "success-line-soft":     ("#86efac", "#0F814A"),
    "success-line-hover":    ("#4ade80", "#1BA964"),
    # danger
    "danger-ink":            ("#dc2626", "#FC7474"),
    "danger-fill":           ("#fee2e2", "#521515"),
    "danger-fill-soft":      ("#fef2f2", "#361515"),
    "danger-line":           ("#fca5a5", "#681916"),
    "danger-line-hover":     ("#f87171", "#901818"),
    "danger-line-soft":      ("#fecaca", "#521515"),
    # POSFooter builds its CSS in JS (deliberately, to resist CSS targeting),
    # so its fallback colours need tokens of their own.
    "footer-fill":           ("#f8f9fa", "#161616"),
    "footer-line":           ("#e0e0e0", "#2E2E2E"),
    "link":                  ("#3b82f6", "#7EB6F5"),
    "link-hover":            ("#2563eb", "#A5CDF8"),
    # warning / highlight
    "warn-ink":              ("#92400e", "#F0BA31"),
    "warn-fill":             ("#fef3c7", "#4B2606"),
    "highlight-fill":        ("#fef08a", "#5B4605"),
}

for name, (l, d) in EXTRAS.items():
    light[f"--pos-x-{name}"] = l
    dark[f"--pos-x-{name}"] = d

# ---------------------------------------------------------------------------
css = ["/*",
       " * Theme variables - generated by scripts/gen_theme.py, do not hand-edit.",
       " *",
       " * Channels are stored space-separated so Tailwind's slash-opacity",
       " * modifiers (bg-white/50, bg-red-500/20) keep working.",
       " */",
       ":root {"]
for k, v in light.items():
    css.append(f"\t{k}: {v};")
css.append("}\n")
css.append('[data-theme="dark"] {')
for k, v in dark.items():
    css.append(f"\t{k}: {v};")
css.append("}")
open(os.path.join(ROOT, "src/theme.css"), "w").write("\n".join(css) + "\n")

def scale(prefix, hue):
    return "{\n" + "".join(
        f"\t\t{s}: 'rgb(var(--pos-{prefix}-{hue}-{s}) / <alpha-value>)',\n" for s in SHADES
    ) + "\t}"

def family(prefix):
    hues = ["gray"] + ACCENTS
    return "{\n" + "".join(f"\t{h}: {scale(prefix, h)},\n" for h in hues) + "}"

js = f"""// Generated by scripts/gen_theme.py - do not hand-edit.
//
// Three independent scales for the same shade names. Tailwind lets background,
// text and border colours be themed separately, so `bg-blue-600` (a solid
// button that keeps its light-mode fill) and `text-blue-600` (a label that has
// to brighten on a dark surface) can flip in opposite directions.

export const backgroundColor = {family('bg')}

export const textColor = {family('fg')}

export const borderColor = {family('line')}

export const surfaceColor = 'rgb(var(--pos-surface) / <alpha-value>)'
export const pageColor = 'rgb(var(--pos-page) / <alpha-value>)'

// Tailwind only substitutes <alpha-value> when it generates a utility. Values
// that land in a base declaration - the default --tw-ring-offset-color - have
// to be plain, or the placeholder leaks into the stylesheet as invalid CSS.
export const surfaceColorPlain = 'rgb(var(--pos-surface))'
"""
open(os.path.join(ROOT, "tailwind.theme.js"), "w").write(js)
print("wrote src/theme.css and tailwind.theme.js")
print("vars:", len(light))
