/**
 * Cross-tab logout: when the session user changes in another tab (logout from
 * Desk or POS Next, or login as a different user), reload this tab so the
 * router sends it to the login page instead of staying open on a dead session.
 * Mirrors ecs_posnext/public/js/cross_tab_logout.js (Desk).
 */

function getSessionUser() {
	const match = document.cookie.match(/(?:^|;\s*)user_id=([^;]*)/)
	const user = match ? decodeURIComponent(match[1]) : null
	return user && user !== "Guest" ? user : null
}

let started = false

export function startCrossTabLogoutWatcher(intervalMs = 2000) {
	if (started) return
	started = true

	let lastUser = getSessionUser()

	const check = () => {
		const current = getSessionUser()
		if (lastUser && current !== lastUser) {
			lastUser = current
			window.location.reload()
			return
		}
		// Picks up a login in this tab (Guest -> user) without reloading
		lastUser = current
	}

	setInterval(check, intervalMs)
	document.addEventListener("visibilitychange", () => {
		if (!document.hidden) check()
	})
	window.addEventListener("focus", check)
}
