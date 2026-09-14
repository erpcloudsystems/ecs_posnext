/**
 * Geidea Web ECR client.
 *
 * The Geidea Windows service runs on the cashier PC and exposes a WebSocket
 * (ws://localhost:5000/messages by default). The browser drives the payment
 * terminal through it directly — there is no server-side gateway — so this
 * client lives entirely in the POS front end.
 *
 * Protocol (Geidea KSA Web ECR v1.09):
 *   - Every frame in both directions is a JSON string (stringify on send,
 *     parse on receive).
 *   - Requests carry an `Event` ("CONNECTION" | "TRANSACTION") plus an
 *     `Operation` naming what to do.
 *   - Responses carry an `Event` naming the callback: OnConnect, OnDisConnect,
 *     OnError, OnTerminalAction, OnTerminalStatus, OnDataReceive, OnWrite.
 *   - A finished transaction arrives as OnDataReceive with
 *     EventName == "TERMINAL_RESPONSE" and the actual fields inside the
 *     stringified `JsonResult`.
 *
 * Note the `BraudRate` spelling: that misspelling is the real field name the
 * service expects, not a typo here.
 */

import { logger } from "@/utils/logger"

const log = logger.create("GeideaECR")

/** SAMA response codes that mean the transaction was approved. Anything else
 * is a decline — the terminal's own English text is not reliable enough to
 * gate on, so the code is the source of truth (spec section 8.2). */
const APPROVED_SAMA_CODES = new Set([
	"000", // Approved
	"001", // Honour with identification
	"003", // Approved (VIP)
	"007", // Approved, update ICC
	"087", // Offline approved (chip only)
	"089", // Unable to go on-line, approved (chip only)
	"400", // Accepted (reversal)
	"500", // Reconciled, totals matched
	"501", // Reconciled, totals unmatched
])

/** Terminal actions that end the transaction with no approval (spec 8.1 #3). */
const TERMINAL_FAILURE_ACTIONS = new Set([
	"USER_CANCELLED_AND_TIMEOUT",
	"CARD_READ_ERROR",
	"DATA_ERROR",
	"BLOCKED_CARD",
	"NO_ACTIVE_APPLICATION_FOUND",
	"INSERT_CARD_ONLY_USE_SMART_CARD_READER",
	"MAXIMUM_AMOUNT_LIMIT_EXCEEDED",
	"PIN_QUIT",
	"TRANSACTION_CANCELLED",
	"WRONG_PIN",
	"RETRY_LIMIT_EXCEEDED",
	"MAXIMUM_SAF_REACHED",
	"MAG_STRIPE_NOT_SUPPORTED",
	"CARD_SCHEME_NOT_SUPPORTED",
	"DE_SAF_FAILED",
	"RECONCILIATION_NO_BUSINESS",
	"RECONCILIATION_FAILED",
	"NO_TXN_TO_REVERSE",
	"TRY_CONTACTING_INTERFACE",
	"SUPERVISOR_PASSWORD_QUIT",
	"GPRS_DOWN",
	"REFUND_PAN_NOT_MATCHING",
	"INVALID_PAWWORD",
	"CARD_NOT_DETECTED",
])

/** Human-readable progress text for the actions the cashier cares about. */
const ACTION_LABELS = {
	SWIPE_OR_INSERT: "Swipe or insert the card",
	CARD_INSERTED: "Card inserted",
	CARD_REMOVED: "Card removed",
	PIN_ENTRY: "Waiting for PIN",
	CONNECTING: "Connecting to the network",
	"RE-CONNECT": "Reconnecting",
	SENDING_REQUEST: "Sending the request",
	WAITING_RESPONSE: "Waiting for the response",
	SAF_PROCESSING: "Processing stored transactions",
	CONNECTION_MADE: "Connected",
}

const CONNECT_TIMEOUT_MS = 15000
const TRANSACTION_TIMEOUT_MS = 120000

/** Parse a `JsonResult` payload, which the service sends as a JSON string. */
function parseJsonResult(value) {
	if (!value) return null
	if (typeof value === "object") return value
	try {
		return JSON.parse(value)
	} catch (e) {
		log.warn("Could not parse JsonResult", value)
		return null
	}
}

/**
 * Pull the SAMA response code out of a terminal response.
 *
 * The spec shows it as `TransactionResponse:***` where *** is the code, but
 * different builds surface it under slightly different key names, so check the
 * ones seen in the wild before giving up.
 */
export function extractSamaCode(result) {
	if (!result) return null
	const raw =
		result.TransactionResponse ??
		result.ResponseCode ??
		result.TransactionResponseCode ??
		result.ActionCode
	if (raw === undefined || raw === null) return null
	// Values arrive as "000", 0, or "TransactionResponse:000" depending on build.
	const match = String(raw).match(/(\d{3})\s*$/)
	return match ? match[1] : String(raw).trim()
}

/** True when the terminal response carries an approving SAMA code. */
export function isApproved(result) {
	const code = extractSamaCode(result)
	return Boolean(code) && APPROVED_SAMA_CODES.has(code)
}

/**
 * Build the 16-digit ECRNumber the terminal echoes back on its receipt.
 *
 * Geidea does not interpret this value; it exists so a terminal transaction can
 * be matched back to the POS transaction during reconciliation or a dispute.
 * A fixed number would defeat that, so derive a unique one per request:
 * 12 digits of epoch milliseconds (unique to the millisecond, good past year
 * 5000) plus 4 random digits to survive two clicks in the same millisecond.
 */
export function buildEcrNumber() {
	const millis = String(Date.now()).slice(-12).padStart(12, "0")
	const salt = String(Math.floor(Math.random() * 10000)).padStart(4, "0")
	return `${millis}${salt}`
}

/** Format an amount the way the terminal expects: a string with exactly 2 decimals. */
export function formatTerminalAmount(amount) {
	return Number(amount || 0).toFixed(2)
}

/**
 * A single connection to the Geidea Web ECR service.
 *
 * One instance owns one WebSocket and runs one transaction at a time — the
 * terminal itself is single-threaded, and the service reports BUSY if a second
 * request arrives mid-transaction.
 */
export class GeideaEcrClient {
	/** @param {object} terminal Settings from `payments.get_card_terminal`. */
	constructor(terminal) {
		this.terminal = terminal || {}
		this.socket = null
		this.connected = false // WebSocket open (service reachable)
		this.terminalConnected = false // Terminal reachable through the service
		this.listeners = new Set()
		this.pendingTransaction = null
	}

	/** Subscribe to parsed service messages. Returns an unsubscribe function. */
	onMessage(handler) {
		this.listeners.add(handler)
		return () => this.listeners.delete(handler)
	}

	emit(event) {
		for (const handler of this.listeners) {
			try {
				handler(event)
			} catch (e) {
				log.error("Listener threw", e)
			}
		}
	}

	get serviceUrl() {
		return this.terminal.service_url || "ws://localhost:5000/messages"
	}

	/** Open the WebSocket to the Windows service. */
	openSocket() {
		if (this.connected && this.socket?.readyState === WebSocket.OPEN) {
			return Promise.resolve()
		}
		return new Promise((resolve, reject) => {
			let settled = false
			const timer = setTimeout(() => {
				if (settled) return
				settled = true
				reject(
					new Error(
						`Could not reach the Geidea Web ECR service at ${this.serviceUrl}. Check that the Windows service is running on this PC.`,
					),
				)
			}, CONNECT_TIMEOUT_MS)

			let socket
			try {
				socket = new WebSocket(this.serviceUrl)
			} catch (e) {
				clearTimeout(timer)
				reject(e)
				return
			}
			this.socket = socket

			socket.onopen = () => {
				this.connected = true
				log.info("Service socket open", this.serviceUrl)
				if (settled) return
				settled = true
				clearTimeout(timer)
				resolve()
			}
			socket.onmessage = (frame) => this.handleFrame(frame)
			socket.onerror = () => {
				log.error("Service socket error")
				if (settled) return
				settled = true
				clearTimeout(timer)
				reject(
					new Error(
						`Could not reach the Geidea Web ECR service at ${this.serviceUrl}.`,
					),
				)
			}
			socket.onclose = () => {
				this.connected = false
				this.terminalConnected = false
				log.info("Service socket closed")
				// Fail an in-flight transaction rather than leaving it hanging
				// until its timeout — the service is gone, no response is coming.
				this.rejectPending(
					new Error("The Geidea Web ECR service disconnected."),
				)
			}
		})
	}

	/** Send a request payload as the stringified JSON the service requires. */
	send(payload) {
		if (this.socket?.readyState !== WebSocket.OPEN) {
			throw new Error("The Geidea Web ECR service is not connected.")
		}
		log.debug("→", payload)
		this.socket.send(JSON.stringify(payload))
	}

	handleFrame(frame) {
		let parsed
		try {
			parsed = JSON.parse(frame.data)
		} catch (e) {
			log.warn("Non-JSON frame", frame.data)
			return
		}
		log.debug("←", parsed)

		// Event casing varies between builds ("OnConnect" vs "onConnect").
		const event = String(parsed.Event || "").toLowerCase()

		if (event === "onconnect") {
			this.terminalConnected = true
			this.emit({ type: "connected", raw: parsed })
			this.resolveConnect?.(parsed)
			return
		}
		if (event === "ondisconnect") {
			this.terminalConnected = false
			this.emit({ type: "disconnected", raw: parsed })
			return
		}
		if (event === "onerror") {
			const message =
				parsed.Message || parsed.Reason || "The terminal reported an error."
			this.emit({ type: "error", message, raw: parsed })
			this.rejectConnect?.(new Error(message))
			this.rejectPending(new Error(message))
			return
		}
		if (event === "onterminalaction") {
			const action = parsed.TerminalAction || ""
			this.emit({
				type: "action",
				action,
				label: ACTION_LABELS[action] || parsed.OptionalMessage || action,
				raw: parsed,
			})
			if (TERMINAL_FAILURE_ACTIONS.has(action)) {
				this.rejectPending(
					new Error(parsed.OptionalMessage || action.replace(/_/g, " ")),
				)
			}
			return
		}
		if (event === "onterminalstatus") {
			const status = parsed.TerminalStatus || ""
			this.emit({ type: "status", status, raw: parsed })
			if (status === "BUSY") {
				this.rejectPending(
					new Error(
						"The terminal is busy with another transaction. Finish or cancel it first.",
					),
				)
			}
			return
		}
		if (event === "ondatareceive") {
			this.handleDataReceive(parsed)
			return
		}
		// OnWrite carries raw buffers only — useful for logs, not for the flow.
		this.emit({ type: "raw", raw: parsed })
	}

	handleDataReceive(parsed) {
		const result = parseJsonResult(parsed.JsonResult)
		if (parsed.EventName === "TERMINAL_SETTINGS") {
			this.emit({ type: "settings", settings: result, raw: parsed })
			return
		}
		if (parsed.EventName === "TERMINAL_RESPONSE" || result) {
			this.emit({ type: "response", result, raw: parsed })
			this.resolvePending(result)
		}
	}

	resolvePending(result) {
		const pending = this.pendingTransaction
		if (!pending) return
		this.pendingTransaction = null
		clearTimeout(pending.timer)
		pending.resolve(result)
	}

	rejectPending(error) {
		const pending = this.pendingTransaction
		if (!pending) return
		this.pendingTransaction = null
		clearTimeout(pending.timer)
		pending.reject(error)
	}

	/** Connect the service to the terminal (COM or TCP, per the settings). */
	connectTerminal() {
		const t = this.terminal
		const payload =
			t.connection_mode === "COM"
				? {
						Event: "CONNECTION",
						Operation: "CONNECT",
						ConnectionMode: "COM",
						ComName: t.com_name,
						BraudRate: t.braud_rate || "38400",
						DataBits: t.data_bits || "8",
						Parity: t.parity || "none",
					}
				: {
						Event: "CONNECTION",
						Operation: "CONNECT",
						ConnectionMode: "TCP",
						IpAddress: t.ip_address,
						Port: Number(t.port) || 6100,
					}

		return new Promise((resolve, reject) => {
			const timer = setTimeout(() => {
				this.resolveConnect = null
				this.rejectConnect = null
				reject(
					new Error(
						"The terminal did not answer the connection request. Check that it is powered on and on the same network.",
					),
				)
			}, CONNECT_TIMEOUT_MS)

			this.resolveConnect = (value) => {
				clearTimeout(timer)
				this.resolveConnect = null
				this.rejectConnect = null
				resolve(value)
			}
			this.rejectConnect = (error) => {
				clearTimeout(timer)
				this.resolveConnect = null
				this.rejectConnect = null
				reject(error)
			}

			try {
				this.send(payload)
			} catch (e) {
				this.rejectConnect(e)
			}
		})
	}

	/** Open the socket and connect the terminal, if not already done. */
	async ensureReady() {
		await this.openSocket()
		if (!this.terminalConnected) {
			await this.connectTerminal()
		}
	}

	/**
	 * Run one PURCHASE and resolve with the terminal response.
	 *
	 * @param {number|string} amount Amount in SAR.
	 * @param {string} [ecrNumber] Reference echoed on the terminal receipt.
	 * @returns {Promise<object>} The parsed TERMINAL_RESPONSE fields.
	 */
	purchase(amount, ecrNumber = buildEcrNumber()) {
		if (this.pendingTransaction) {
			return Promise.reject(
				new Error("Another card transaction is already running."),
			)
		}

		const payload = {
			Event: "TRANSACTION",
			Operation: "PURCHASE",
			Amount: formatTerminalAmount(amount),
			ECRNumber: ecrNumber,
			PrintSettings: String(this.terminal.print_settings ?? "1"),
			AppId: String(this.terminal.app_id || "11"),
		}

		return new Promise((resolve, reject) => {
			const timer = setTimeout(() => {
				this.pendingTransaction = null
				reject(new Error("Timed out waiting for the terminal to respond."))
			}, TRANSACTION_TIMEOUT_MS)

			this.pendingTransaction = { resolve, reject, timer, ecrNumber }

			try {
				this.send(payload)
			} catch (e) {
				this.rejectPending(e)
			}
		})
	}

	/** Ask the terminal whether it is BUSY or AVAILABLE. */
	checkStatus() {
		this.send({ Event: "TRANSACTION", Operation: "CHECK_STATUS" })
	}

	/** Close the terminal connection and the socket. */
	close() {
		this.rejectPending(new Error("The card transaction was cancelled."))
		try {
			if (this.socket?.readyState === WebSocket.OPEN) {
				this.send({ Event: "CONNECTION", Operation: "DISCONNECT" })
			}
		} catch (e) {
			log.debug("DISCONNECT send failed (socket already gone)", e)
		}
		try {
			this.socket?.close()
		} catch (e) {
			log.debug("Socket close failed", e)
		}
		this.socket = null
		this.connected = false
		this.terminalConnected = false
	}
}
