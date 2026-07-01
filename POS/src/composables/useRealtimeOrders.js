/**
 * Realtime Orders Composable
 *
 * Singleton module that:
 *  - Subscribes to `pos_order_changed` socket events
 *  - Auto-retries until the socket is ready (bootstrap is async)
 *  - Calls registered handlers on any order change
 *  - Tracks "Need My Action" pending count for the sidebar badge
 *  - Plays a notification chime when a new Call Center draft arrives
 */

import { ref, readonly } from "vue"
import { call } from "@/utils/apiWrapper"

const EVENT_NAME = "pos_order_changed"

// ── Singleton state ──────────────────────────────────────────────────────────
const isListening = ref(false)
const pendingCount = ref(0)

/** @type {Set<Function>} */
const changeHandlers = new Set()

let retryTimer = null
let audioCtx = null

// ── Audio ────────────────────────────────────────────────────────────────────

function getAudioContext() {
	if (!audioCtx) {
		audioCtx = new (window.AudioContext || window.webkitAudioContext)()
	}
	return audioCtx
}

export function playNewOrderSound() {
	try {
		const ctx = getAudioContext()
		const tones = [
			{ freq: 880, start: 0, duration: 0.18 },
			{ freq: 1100, start: 0.22, duration: 0.22 },
		]
		tones.forEach(({ freq, start, duration }) => {
			const osc = ctx.createOscillator()
			const gain = ctx.createGain()
			osc.connect(gain)
			gain.connect(ctx.destination)
			osc.type = "sine"
			osc.frequency.value = freq
			const t = ctx.currentTime + start
			gain.gain.setValueAtTime(0, t)
			gain.gain.linearRampToValueAtTime(0.35, t + 0.02)
			gain.gain.exponentialRampToValueAtTime(0.001, t + duration)
			osc.start(t)
			osc.stop(t + duration)
		})
	} catch {
		// AudioContext may be blocked before first user gesture — silently ignore
	}
}

// ── Pending count ────────────────────────────────────────────────────────────

export async function refreshPendingCount() {
	try {
		const orders = await call("ecs_posnext.api.invoices.get_need_my_action_orders")
		pendingCount.value = (orders || []).length
	} catch {
		// Non-fatal — sidebar badge stays at last known value
	}
}

// ── Socket listener ──────────────────────────────────────────────────────────

function handleOrderChanged(data) {
	// Notify all registered page-level handlers
	changeHandlers.forEach((fn) => {
		try { fn(data) } catch { /* ignore */ }
	})

	// Sound only for new Call Center drafts
	if (data?.action === "create") {
		const profile = (data.pos_profile || "").toLowerCase()
		if (profile.includes("call center")) {
			playNewOrderSound()
		}
	}

	// Keep sidebar badge accurate
	refreshPendingCount()
}

function startListening() {
	if (isListening.value) return

	if (!window.frappe?.realtime) {
		// Socket not ready yet (bootstrap still loading) — retry shortly
		clearTimeout(retryTimer)
		retryTimer = setTimeout(startListening, 400)
		return
	}

	clearTimeout(retryTimer)
	retryTimer = null
	window.frappe.realtime.on(EVENT_NAME, handleOrderChanged)
	isListening.value = true
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Register a handler called on every pos_order_changed event.
 * Automatically starts the socket listener (with retry until socket is ready).
 * Returns an unregister cleanup function.
 *
 * @param {Function} fn
 * @returns {Function} cleanup
 */
function onOrderChanged(fn) {
	changeHandlers.add(fn)
	// Auto-start listener as soon as first handler is registered
	startListening()
	return () => changeHandlers.delete(fn)
}

/**
 * Call once (from main.js after socket setup) to fetch initial pending count
 * and kick off the listener for the sidebar badge even when no page has
 * registered a handler yet.
 */
function init() {
	refreshPendingCount()
	startListening()
}

export function useRealtimeOrders() {
	return {
		pendingCount: readonly(pendingCount),
		isListening: readonly(isListening),
		init,
		startListening,
		onOrderChanged,
		refreshPendingCount,
		playNewOrderSound,
	}
}
