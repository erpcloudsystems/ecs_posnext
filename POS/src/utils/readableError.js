/**
 * Give API errors a message a cashier can read.
 *
 * frappe-ui builds `error.message` as "<url> <ExceptionType>", e.g.
 * "/api/method/ecs_posnext.api.invoices.submit_invoice ValidationError", and keeps
 * the server's actual text ("The POS Business Day ... is already closed") in
 * `error.messages`. Every screen that shows `error.message` therefore showed the URL.
 * This swaps the server's text into `error.message`; the original is kept on
 * `error.technicalMessage`, and `exc_type` / `messages` are left untouched.
 */

function stripHtml(text) {
	if (typeof document !== "undefined") {
		const container = document.createElement("div")
		container.innerHTML = text
		text = container.textContent || container.innerText || ""
	} else {
		text = text.replace(/<[^>]*>/g, " ")
	}
	return text.replace(/\s+/g, " ").trim()
}

export function toReadableError(error) {
	if (!error || typeof error !== "object" || error._readable) {
		return error
	}

	const messages = [
		...new Set(
			(Array.isArray(error.messages) ? error.messages : [])
				.filter((m) => typeof m === "string")
				.map(stripHtml)
				.filter(Boolean),
		),
	]

	const original = typeof error.message === "string" ? error.message : ""
	let readable = messages.join("\n")

	// No server text, only "<url> <ExceptionType>" — never show the URL.
	if (!readable && (error.exc_type || /\/api\/method\/|^[\w.]+\.[\w]+ /.test(original))) {
		readable = error.status >= 500
			? __("Something went wrong on the server. Please try again or contact your supervisor.")
			: __("The action could not be completed. Please try again or contact your supervisor.")
	}

	if (readable) {
		error.technicalMessage = original
		error.message = readable
	}
	error._readable = true
	return error
}

/** Wrap an async API function so whatever it throws carries a readable message. */
export function withReadableErrors(fn) {
	return async function (...args) {
		try {
			return await fn.apply(this, args)
		} catch (error) {
			throw toReadableError(error)
		}
	}
}
