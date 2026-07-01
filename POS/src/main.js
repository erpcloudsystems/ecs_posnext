/**
 * POS Next - Application Entry Point
 *
 * Initialization sequence:
 * 1. Register PWA service worker
 * 2. Configure Vue app with plugins and global components
 * 3. Authenticate user and initialize CSRF token (in parallel)
 * 4. Preload bootstrap data for faster page rendering
 * 5. Register router and mount app
 */

import { createPinia } from "pinia"
import { createApp } from "vue"

import App from "./App.vue"
import { session, sessionUser } from "./data/session"
import { userResource } from "./data/user"
import router from "./router"
import {
	createCSRFAwareRequest,
	ensureCSRFToken,
	getCSRFTokenFromCookie,
	onCSRFTokenRefresh,
} from "./utils/csrf"
import { logger } from "./utils/logger"
import { offlineWorker } from "./utils/offline/workerClient"
import translationPlugin from "./utils/translation"
import { initSocket } from "./socket"

import {
	Alert,
	Badge,
	Button,
	Dialog,
	ErrorMessage,
	FormControl,
	Input,
	TextInput,
	frappeRequest,
	pageMetaPlugin,
	resourcesPlugin,
	setConfig,
} from "frappe-ui"

import "./index.css"

const log = logger.create("Main")

// ---------------------------------------------------------------------------
// frappe.show_alert shim — the standalone POS SPA does NOT load Frappe's desk
// bundle, so window.frappe.show_alert is undefined and every call to it across
// the app is a silent no-op. Define a self-contained DOM toast so all those
// notifications (customer/address/invoice created, etc.) actually show.
// ---------------------------------------------------------------------------
;(function setupShowAlert() {
	if (typeof window === "undefined") return
	window.frappe = window.frappe || {}
	if (window.frappe.show_alert) return
	const COLORS = { green: "#16a34a", red: "#dc2626", orange: "#ea580c", yellow: "#ca8a04", blue: "#2563eb" }
	window.frappe.show_alert = function (arg, seconds) {
		try {
			const msg = typeof arg === "string" ? arg : (arg && arg.message) || ""
			if (!msg) return
			const indicator = (typeof arg === "object" && arg && arg.indicator) || "blue"
			let host = document.getElementById("pos-alert-host")
			if (!host) {
				host = document.createElement("div")
				host.id = "pos-alert-host"
				host.style.cssText =
					"position:fixed;top:16px;inset-inline-end:16px;z-index:99999;display:flex;flex-direction:column;gap:8px;pointer-events:none;"
				document.body.appendChild(host)
			}
			const el = document.createElement("div")
			el.textContent = msg
			el.style.cssText =
				"pointer-events:auto;background:#fff;color:#111827;font-size:13px;font-weight:600;" +
				"padding:10px 14px;border-radius:10px;box-shadow:0 6px 20px rgba(0,0,0,.18);" +
				"max-width:360px;line-height:1.4;font-family:system-ui,'Segoe UI',Tahoma,sans-serif;" +
				"border-inline-start:4px solid " + (COLORS[indicator] || COLORS.blue) + ";" +
				"opacity:0;transform:translateY(-6px);transition:opacity .2s,transform .2s;"
			host.appendChild(el)
			requestAnimationFrame(() => { el.style.opacity = "1"; el.style.transform = "translateY(0)" })
			const ms = (Number(seconds) || 5) * 1000
			setTimeout(() => {
				el.style.opacity = "0"
				el.style.transform = "translateY(-6px)"
				setTimeout(() => el.remove(), 250)
			}, ms)
		} catch (e) { /* never let a toast break the app */ }
	}
	// Common alias used in some Frappe code paths.
	if (!window.frappe.msgprint) window.frappe.msgprint = (m) => window.frappe.show_alert(m)
})()

// =============================================================================
// PWA Service Worker Registration
// =============================================================================

if ("serviceWorker" in navigator) {
	window.addEventListener(
		"load",
		() => {
			navigator.serviceWorker
				.register("/assets/ecs_posnext/pos/sw.js")
				.then((reg) => log.info("Service Worker registered", reg))
				.catch((err) => log.error("Service Worker registration error", err))
		},
		{ passive: true },
	)
}

// =============================================================================
// Global Components (available in all templates without import)
// =============================================================================

const globalComponents = {
	Button,
	TextInput,
	Input,
	FormControl,
	ErrorMessage,
	Dialog,
	Alert,
	Badge,
}

// =============================================================================
// CSRF Token Management
// =============================================================================

/** Sync CSRF token to offline worker for authenticated API calls */
async function syncCSRFTokenToWorker() {
	if (window.csrf_token && typeof window.csrf_token === "string") {
		try {
			await offlineWorker.setCSRFToken(window.csrf_token)
			log.debug("CSRF token synced to worker")
		} catch (error) {
			log.warn("Failed to sync CSRF token to worker", error)
		}
	}
}

// =============================================================================
// Application Initialization
// =============================================================================

async function initializeApp() {
	const app = createApp(App)
	const pinia = createPinia()

	// Keep worker in sync when CSRF token refreshes
	onCSRFTokenRefresh((newToken) => {
		offlineWorker.setCSRFToken(newToken).catch((error) => {
			log.warn("Failed to sync refreshed CSRF token to worker", error)
		})
	})

	// Enable automatic CSRF token refresh on 401/403 errors
	const csrfAwareFrappeRequest = createCSRFAwareRequest(frappeRequest)
	setConfig("resourceFetcher", csrfAwareFrappeRequest)

	// Register plugins
	app.use(pinia)
	app.use(resourcesPlugin)
	app.use(pageMetaPlugin)
	app.use(translationPlugin)

	// Register global components
	for (const key in globalComponents) {
		app.component(key, globalComponents[key])
	}

	// Disable double-tap zoom on mobile for faster touch response
	app.directive("touch-action", {
		mounted: (el) => (el.style.touchAction = "manipulation"),
	})

	// -------------------------------------------------------------------------
	// Authentication (CSRF must resolve before user fetch to avoid CSRFTokenError)
	// -------------------------------------------------------------------------

	const existingToken = getCSRFTokenFromCookie()
	if (existingToken) {
		log.debug("CSRF token found in cookie")
		await syncCSRFTokenToWorker()
	} else {
		log.debug("Fetching CSRF token...")
		try {
			await ensureCSRFToken({ silent: true })
			await syncCSRFTokenToWorker()
		} catch {
			log.debug("CSRF fetch failed, will retry on first API call")
		}
	}

	let user = null
	try {
		if (!userResource.loading) userResource.fetch()
		await userResource.promise
		user = sessionUser()
	} catch (error) {
		log.debug("User not logged in", error?.message || "No session")
	}
	session.user = user
	log.info(`User authenticated: ${session.user}`)

	// -------------------------------------------------------------------------
	// Bootstrap Preload (non-blocking, improves perceived performance)
	// -------------------------------------------------------------------------

	if (user) {
		import("./stores/bootstrap")
			.then(async ({ useBootstrapStore }) => {
				const bootstrapStore = useBootstrapStore()
				try {
					await bootstrapStore.loadInitialData()
					// Initialize precision settings from bootstrap data
					const { initPrecision } = await import("./utils/currency")
					initPrecision(bootstrapStore.getPreloadedPrecision())
					log.debug("Precision settings initialized from bootstrap")

					// Initialize Socket.IO with correct site name from bootstrap
					if (typeof window !== "undefined") {
						if (!window.frappe) window.frappe = {}
						const siteName = bootstrapStore.getSiteName()
						window.frappe.realtime = initSocket(siteName)

						// Ensure connection is established
						if (window.frappe.realtime && typeof window.frappe.realtime.connect === "function") {
							window.frappe.realtime.connect()
							log.info("Socket initialized and connecting...", { siteName })
						}

						// Start global order realtime listener for sidebar badge + AllOrders
						try {
							const { useRealtimeOrders } = await import("./composables/useRealtimeOrders")
							useRealtimeOrders().init()
						} catch { /* non-critical */ }
					}
				} catch (error) {
					log.debug("Bootstrap preload failed (non-critical)", error)
				}
			})
			.catch(() => { })
	}

	// -------------------------------------------------------------------------
	// Mount Application
	// -------------------------------------------------------------------------

	log.debug("Registering router, auth state:", session.isLoggedIn)
	app.use(router)
	app.mount("#app")

	// -------------------------------------------------------------------------
	// Scheduled CSRF Token Refresh (every 30 minutes)
	// -------------------------------------------------------------------------

	setInterval(
		async () => {
			log.debug("Scheduled CSRF token refresh")
			await ensureCSRFToken({ forceRefresh: true, silent: true })
			await syncCSRFTokenToWorker()
		},
		30 * 60 * 1000,
	)
}

initializeApp()
