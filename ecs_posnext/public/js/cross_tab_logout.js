// Cross-tab logout for Desk: when the session user changes in another tab
// (logout from Desk or POS Next, or login as a different user), reload this tab
// so it lands on the login page instead of staying open on a dead session.
// Mirrors POS/src/utils/crossTabLogout.js.
(function () {
	if (window.__ecs_cross_tab_logout) return;
	window.__ecs_cross_tab_logout = true;

	function getSessionUser() {
		const match = document.cookie.match(/(?:^|;\s*)user_id=([^;]*)/);
		const user = match ? decodeURIComponent(match[1]) : null;
		return user && user !== "Guest" ? user : null;
	}

	let lastUser = getSessionUser();

	function check() {
		const current = getSessionUser();
		if (lastUser && current !== lastUser) {
			lastUser = current;
			window.location.reload();
			return;
		}
		lastUser = current;
	}

	setInterval(check, 2000);
	document.addEventListener("visibilitychange", function () {
		if (!document.hidden) check();
	});
	window.addEventListener("focus", check);
})();
