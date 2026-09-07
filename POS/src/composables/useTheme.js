/**
 * Theme (light/dark) state for the POS.
 *
 * The rendered colours all come from the CSS variables in src/theme.css, which
 * are swapped by a single `data-theme` attribute on <html>. So switching theme
 * is one attribute write - no component needs to re-render, and frappe-ui's own
 * components follow along because its Tailwind preset is configured with
 * `darkMode: ['selector', '[data-theme="dark"]']`.
 *
 * State lives at module scope so every caller shares one source of truth.
 */
import { computed, ref } from "vue"
import { logger } from "../utils/logger"

const log = logger.create("Theme")

const THEME_KEY = "ecs_posnext_theme"

const LIGHT = "light"
const DARK = "dark"

/**
 * Browser status-bar / PWA theme colour per mode. Matches --pos-page so the
 * mobile address bar does not sit on a mismatched strip of colour.
 */
const THEME_COLOR = {
	[LIGHT]: "#4F46E5",
	[DARK]: "#0F0F0F",
}

/** Active theme. Seeded below from storage or the OS preference. */
const theme = ref(LIGHT)

/** True when the user has explicitly chosen; false means "follow the OS". */
const hasExplicitPreference = ref(false)

/** Guards against attaching the OS listener more than once. */
let systemListenerAttached = false

function systemPrefersDark() {
	return (
		typeof window !== "undefined" &&
		typeof window.matchMedia === "function" &&
		window.matchMedia("(prefers-color-scheme: dark)").matches
	)
}

function readStoredTheme() {
	try {
		const stored = localStorage.getItem(THEME_KEY)
		return stored === LIGHT || stored === DARK ? stored : null
	} catch (error) {
		// Private browsing and locked-down kiosk profiles can throw here.
		log.warn("Could not read stored theme", error)
		return null
	}
}

function storeTheme(value) {
	try {
		localStorage.setItem(THEME_KEY, value)
	} catch (error) {
		log.warn("Could not persist theme", error)
	}
}

/** Writes the theme to the DOM: the attribute Tailwind keys off, plus PWA meta. */
function applyTheme(value) {
	if (typeof document === "undefined") return

	const root = document.documentElement
	if (value === DARK) {
		root.setAttribute("data-theme", DARK)
	} else {
		root.removeAttribute("data-theme")
	}

	const meta = document.querySelector('meta[name="theme-color"]')
	if (meta)
		meta.setAttribute("content", THEME_COLOR[value] || THEME_COLOR[LIGHT])
}

/**
 * Resolves the starting theme and starts following the OS while the user has
 * not made a choice of their own. Safe to call more than once.
 */
function initTheme() {
	const stored = readStoredTheme()
	hasExplicitPreference.value = stored !== null
	theme.value = stored ?? (systemPrefersDark() ? DARK : LIGHT)
	applyTheme(theme.value)

	if (
		!systemListenerAttached &&
		typeof window !== "undefined" &&
		typeof window.matchMedia === "function"
	) {
		const query = window.matchMedia("(prefers-color-scheme: dark)")
		query.addEventListener("change", (event) => {
			// An explicit choice by the user outranks the OS.
			if (hasExplicitPreference.value) return
			theme.value = event.matches ? DARK : LIGHT
			applyTheme(theme.value)
		})
		systemListenerAttached = true
	}

	log.debug(`Theme initialised: ${theme.value}`, {
		explicit: hasExplicitPreference.value,
	})
}

/** Switches to a specific theme and remembers the choice. */
function setTheme(value) {
	const next = value === DARK ? DARK : LIGHT
	theme.value = next
	hasExplicitPreference.value = true
	applyTheme(next)
	storeTheme(next)
}

function toggleTheme() {
	setTheme(theme.value === DARK ? LIGHT : DARK)
}

export function useTheme() {
	return {
		theme,
		isDark: computed(() => theme.value === DARK),
		initTheme,
		setTheme,
		toggleTheme,
	}
}
