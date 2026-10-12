import { call } from "@/utils/apiWrapper"
import { logger } from "@/utils/logger"
import { reactive } from "vue"

const log = logger.create("CheckEditApproval")

/**
 * Supervisor approval for edits that take value off an open check.
 *
 * The password is never held here or anywhere else in the browser - the dialog
 * sends an attempt to the server, which answers only yes or no. State lives at
 * module level so one dialog instance can serve every call site.
 */
const state = reactive({
	open: false,
	/** What is about to happen, shown to whoever is typing the password. */
	reason: "",
	posProfile: null,
	verifying: false,
	error: "",
})

let resolver = null

/** Lines the supervisor has already approved, and asks still in flight. */
const approved = new Set()
const pending = new Map()

function settle(approved) {
	const done = resolver
	resolver = null
	state.open = false
	state.verifying = false
	state.error = ""
	if (done) done(approved)
}

export function useCheckEditApproval() {
	/**
	 * Ask for approval. Resolves true when the edit may go ahead.
	 *
	 * @param {object} options
	 * @param {string} options.reason - Describes the edit, e.g. "Remove item".
	 * @param {string} options.posProfile - Profile whose password is checked.
	 * @param {boolean} options.required - False resolves immediately, so callers
	 *   can pass their own condition rather than branching around this.
	 */
	function request({ reason, posProfile, required }) {
		if (!required) return Promise.resolve(true)

		// A second request while one is open abandons the first rather than
		// leaving its caller waiting on a promise nothing will settle.
		if (resolver) settle(false)

		state.reason = reason || ""
		state.posProfile = posProfile || null
		state.error = ""
		state.open = true

		return new Promise((resolve) => {
			resolver = resolve
		})
	}

	async function submit(password) {
		if (!password) {
			state.error = __("Enter the password")
			return
		}

		state.verifying = true
		state.error = ""

		try {
			const result = await call(
				"ecs_posnext.api.pos_profile.verify_check_edit_password",
				{ pos_profile: state.posProfile, password },
			)

			if (result?.verified) {
				settle(true)
				return
			}

			state.error =
				result?.attempts_left > 0
					? __("Wrong password. {0} attempts left.", [result.attempts_left])
					: __("Wrong password")
		} catch (error) {
			log.error("Could not check the password", error)
			// A lockout or a lost connection both land here. The edit is refused
			// rather than waved through, which is the point of the password.
			state.error =
				error?.messages?.[0] || error?.message || __("Could not check the password")
		} finally {
			state.verifying = false
		}
	}

	/**
	 * Ask for approval once per line.
	 *
	 * Two things make this more than a call to `request`. A line the supervisor
	 * has already approved is not asked about again, so the cashier can keep
	 * correcting it; and the quantity box emits on every keystroke, so repeated
	 * asks about the same line while its dialog is open share one answer instead
	 * of each cancelling the last.
	 *
	 * @param {object} options
	 * @param {string|null} options.key - The line this covers. Null for one-off
	 *   actions, which are always asked about.
	 */
	function approve({ key, reason, posProfile }) {
		if (key && approved.has(key)) return Promise.resolve(true)
		if (key && pending.has(key)) return pending.get(key)

		const approval = request({ reason, posProfile, required: true })
			.then((ok) => {
				if (ok && key) approved.add(key)
				return ok
			})
			.finally(() => {
				if (key) pending.delete(key)
			})

		if (key) pending.set(key, approval)
		return approval
	}

	/** Forget what was approved - a different check is a different approval. */
	function resetApprovals() {
		approved.clear()
		pending.clear()
	}

	function cancel() {
		settle(false)
	}

	return { state, request, approve, resetApprovals, submit, cancel }
}
