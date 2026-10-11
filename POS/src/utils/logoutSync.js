/**
 * Cross-tab logout synchronization
 *
 * When the user signs out from any POS tab (POS, Dispatcher, KDS, Live Orders...),
 * every other open tab clears its local cache and is closed (or sent to the
 * login page when the browser doesn't allow closing it).
 *
 * Also detects sign-out done outside the POS (e.g. from Desk) by watching
 * the `user_id` cookie.
 */

import { logger } from "@/utils/logger"

const log = logger.create("LogoutSync")

const CHANNEL_NAME = "pos_next_auth"
// Not prefixed with ecs_posnext_ so clearBrowserCache() doesn't wipe it mid-flight
const STORAGE_SIGNAL_KEY = "pos_next_logout_signal"
const LOGIN_URL = "/pos/account/login"

let channel = null
let initialized = false
let localLogoutInProgress = false
let handlingRemoteLogout = false

function getCookieUser() {
	const cookies = new URLSearchParams(document.cookie.split("; ").join("&"))
	const user = cookies.get("user_id")
	return user && user !== "Guest" ? user : null
}

/**
 * Clear cached POS data (IndexedDB caches + POS localStorage/sessionStorage).
 * Unsynced offline invoices, payments and drafts are preserved so no sales are lost.
 */
export async function clearLocalSessionData() {
	try {
		const { clearCachedData, clearBrowserCache } = await import("@/utils/offline/db.js")
		await clearCachedData({
			preserveInvoices: true,
			preserveDrafts: true,
			preserveSettings: true,
		})
		clearBrowserCache()
	} catch (error) {
		log.error("Failed to clear local data on logout", error)
	}
}

/** Mark that this tab started the logout (so it doesn't treat it as remote). */
export function markLocalLogout() {
	localLogoutInProgress = true
}

/**
 * Finish a logout started in this tab: clear cache, notify other tabs and
 * hard-reload into the login page so no in-memory state survives.
 */
export async function completeLocalLogout() {
	markLocalLogout()
	broadcastLogout()
	await clearLocalSessionData()
	window.location.replace(LOGIN_URL)
}

/** Notify all other tabs that the user logged out. */
export function broadcastLogout() {
	const message = { type: "LOGOUT", at: Date.now() }
	try {
		channel?.postMessage(message)
	} catch (error) {
		log.warn("BroadcastChannel postMessage failed", error)
	}
	// Fallback for browsers without BroadcastChannel (storage event fires in other tabs only)
	try {
		localStorage.setItem(STORAGE_SIGNAL_KEY, JSON.stringify(message))
		localStorage.removeItem(STORAGE_SIGNAL_KEY)
	} catch {
		// storage unavailable
	}
}

async function handleRemoteLogout(reason) {
	if (handlingRemoteLogout || localLogoutInProgress) return
	// Tab already sitting on the login page — nothing to do
	if (window.location.pathname.startsWith(LOGIN_URL)) return
	handlingRemoteLogout = true
	log.info(`Logged out from another tab (${reason}) — closing this tab`)

	await clearLocalSessionData()

	// Only works for tabs opened via window.open; otherwise it's a no-op
	try {
		window.close()
	} catch {
		// ignore
	}
	// If the tab is still alive, reload into the login page (fresh state, no in-memory cache)
	setTimeout(() => {
		window.location.replace(LOGIN_URL)
	}, 150)
}

/** Start listening for logout events from other tabs. Call once at app start. */
export function initLogoutSync() {
	if (initialized || typeof window === "undefined") return
	initialized = true

	if (typeof BroadcastChannel !== "undefined") {
		try {
			channel = new BroadcastChannel(CHANNEL_NAME)
			channel.onmessage = (event) => {
				if (event.data?.type === "LOGOUT") handleRemoteLogout("broadcast")
			}
		} catch (error) {
			log.warn("BroadcastChannel not available", error)
		}
	}

	window.addEventListener("storage", (event) => {
		if (event.key === STORAGE_SIGNAL_KEY && event.newValue) {
			handleRemoteLogout("storage")
		}
	})

	// Logout done outside the POS (e.g. Desk) — session cookie flips to Guest
	let wasLoggedIn = !!getCookieUser()
	const checkCookie = () => {
		const loggedIn = !!getCookieUser()
		if (wasLoggedIn && !loggedIn) handleRemoteLogout("cookie")
		wasLoggedIn = loggedIn
	}
	setInterval(checkCookie, 1000)
	document.addEventListener("visibilitychange", () => {
		if (document.visibilityState === "visible") checkCookie()
	})
}
