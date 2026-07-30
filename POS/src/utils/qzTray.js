import qz from "qz-tray"
import { ref } from "vue"
import { call } from "@/utils/apiWrapper"
import { logger } from "@/utils/logger"

const log = logger.create("QZTray")

// ============================================================================
// Reactive State
// ============================================================================

/** Whether QZ Tray is currently connected */
export const qzConnected = ref(false)

/** Whether a connection attempt is in progress */
export const qzConnecting = ref(false)

// ============================================================================
// localStorage Persistence
// ============================================================================

const PRINTER_STORAGE_KEY = "pos_qz_printer_name"
const SIGNING_STORAGE_KEY = "pos_qz_signing_material"

export function getSavedPrinterName() {
	try {
		return localStorage.getItem(PRINTER_STORAGE_KEY) || ""
	} catch {
		return ""
	}
}

export function savePrinterName(name) {
	try {
		localStorage.setItem(PRINTER_STORAGE_KEY, name || "")
	} catch (e) {
		log.warn("Failed to save printer name to localStorage:", e)
	}
}

// ============================================================================
// Security Setup (once)
// ============================================================================

/** Set up once per page session; concurrent connects share the same promise. */
let _securityPromise = null

/**
 * QZ Tray only serves a request silently when it can verify who sent it. Requests
 * signed with the site's certificate are trusted (once that certificate is
 * installed on the till), so the cashier never sees the "Anonymous request /
 * Untrusted website" dialog.
 *
 * Every failure here falls back to unsigned requests — the till still prints,
 * exactly as before, it just gets the dialog again.
 */
function setupSecurity() {
	if (!_securityPromise) _securityPromise = _initSecurity()
	return _securityPromise
}

/** Unsigned requests: QZ Tray prompts the cashier for each one. */
function useUnsignedRequests() {
	qz.security.setCertificatePromise((resolve) => {
		resolve()
	})

	qz.security.setSignatureAlgorithm("SHA512")
	qz.security.setSignaturePromise(() => {
		return (resolve) => {
			resolve()
		}
	})
}

/**
 * Fetch the site's certificate (and signing key) from the server, remembering it
 * so a till that opens the POS offline still signs its print jobs.
 * @returns {Promise<Object|null>}
 */
async function loadSigningMaterial() {
	let cached = null
	try {
		cached = JSON.parse(localStorage.getItem(SIGNING_STORAGE_KEY) || "null")
	} catch {
		cached = null
	}

	try {
		const material = await call("ecs_posnext.api.qz_signing.get_signing_material")
		if (material?.certificate) {
			try {
				localStorage.setItem(SIGNING_STORAGE_KEY, JSON.stringify(material))
			} catch (e) {
				log.warn("Could not cache QZ Tray signing material:", e)
			}
			return material
		}
		log.warn("Server returned no QZ Tray certificate")
	} catch (err) {
		// Offline, or an older backend without the endpoint.
		log.warn("Could not fetch QZ Tray signing material:", err?.message || err)
	}

	return cached?.certificate ? cached : null
}

/** Decode a PEM block into the raw DER bytes WebCrypto expects. */
function pemToBytes(pem) {
	const base64 = pem.replace(/-----[^-]*-----/g, "").replace(/\s+/g, "")
	const binary = atob(base64)
	const bytes = new Uint8Array(binary.length)
	for (let i = 0; i < binary.length; i++) {
		bytes[i] = binary.charCodeAt(i)
	}
	return bytes
}

/**
 * Import the signing key for in-browser signing.
 * @returns {Promise<CryptoKey|null>} null when the browser can't do it — WebCrypto
 *   is unavailable on pages served over plain http, for instance.
 */
async function importSigningKey(privateKeyPem) {
	if (!globalThis.crypto?.subtle) {
		log.warn("WebCrypto unavailable — QZ Tray requests will be signed server-side")
		return null
	}

	try {
		return await crypto.subtle.importKey(
			"pkcs8",
			pemToBytes(privateKeyPem),
			{ name: "RSASSA-PKCS1-v1_5", hash: "SHA-512" },
			false,
			["sign"],
		)
	} catch (err) {
		log.warn("Could not import QZ Tray signing key:", err?.message || err)
		return null
	}
}

async function signLocally(key, message) {
	const signature = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(message))
	let binary = ""
	for (const byte of new Uint8Array(signature)) {
		binary += String.fromCharCode(byte)
	}
	return btoa(binary)
}

async function signOnServer(message) {
	return await call("ecs_posnext.api.qz_signing.sign_message", { request: message })
}

async function _initSecurity() {
	const material = await loadSigningMaterial()
	if (!material?.certificate) {
		useUnsignedRequests()
		return
	}

	let key = material.private_key ? await importSigningKey(material.private_key) : null

	// Prove the key actually signs before committing to signed requests. A key QZ
	// Tray can't verify would block printing outright, where unsigned only prompts.
	if (key) {
		try {
			await signLocally(key, "qz-tray-signing-probe")
		} catch (err) {
			log.warn("QZ Tray signing key failed a test signature:", err?.message || err)
			key = null
		}
	}

	qz.security.setCertificatePromise((resolve) => {
		resolve(material.certificate)
	})

	qz.security.setSignatureAlgorithm("SHA512")
	qz.security.setSignaturePromise((toSign) => {
		return (resolve, reject) => {
			const signing = key ? signLocally(key, toSign) : signOnServer(toSign)
			signing.then(resolve).catch((err) => {
				log.error("Could not sign QZ Tray request:", err?.message || err)
				reject(err)
			})
		}
	})

	log.info(`QZ Tray requests will be signed ${key ? "in the browser" : "on the server"}`)
}

// ============================================================================
// Connection Management
// ============================================================================

/** Guards against concurrent connect() calls */
let _connectPromise = null

/** When the last connect attempt failed, epoch ms. See FAILED_CONNECT_COOLDOWN_MS. */
let _lastFailedConnectAt = 0

/**
 * On a till with no QZ Tray installed, `qz.websocket.connect()` walks several
 * ports before giving up, which can take seconds. Auto-print calls connect on
 * every sale, so a failed attempt is remembered briefly and short-circuited —
 * otherwise every receipt on those tills would stall behind a doomed handshake.
 */
const FAILED_CONNECT_COOLDOWN_MS = 60000

/**
 * Connect to the locally-running QZ Tray application.
 * Singleton — concurrent calls share the same promise.
 *
 * @param {Object} [options]
 * @param {boolean} [options.force] Ignore the post-failure cooldown. Used by the
 *   manual "Retry" button in POS Settings, where the cashier has just fixed
 *   something and expects an immediate attempt.
 * @returns {Promise<boolean>} true if connected successfully
 */
export async function connect({ force = false } = {}) {
	if (qz.websocket.isActive()) {
		qzConnected.value = true
		return true
	}

	// Deduplicate concurrent calls
	if (_connectPromise) return _connectPromise

	if (!force && _lastFailedConnectAt && Date.now() - _lastFailedConnectAt < FAILED_CONNECT_COOLDOWN_MS) {
		log.debug("Skipping QZ Tray connect — previous attempt failed recently")
		return false
	}

	_connectPromise = _doConnect()
	try {
		return await _connectPromise
	} finally {
		_connectPromise = null
	}
}

async function _doConnect() {
	await setupSecurity()

	qz.websocket.setClosedCallbacks(() => {
		log.info("QZ Tray connection closed")
		qzConnected.value = false
		qzConnecting.value = false
	})

	qzConnecting.value = true

	try {
		await qz.websocket.connect()
		qzConnected.value = true
		_lastFailedConnectAt = 0
		log.info("Connected to QZ Tray")
		return true
	} catch (err) {
		qzConnected.value = false
		_lastFailedConnectAt = Date.now()
		log.warn("Could not connect to QZ Tray:", err?.message || err)
		return false
	} finally {
		qzConnecting.value = false
	}
}

/**
 * Disconnect from QZ Tray.
 */
export async function disconnect() {
	if (!qz.websocket.isActive()) {
		qzConnected.value = false
		return
	}

	try {
		await qz.websocket.disconnect()
	} catch (err) {
		log.warn("Error disconnecting from QZ Tray:", err?.message || err)
	} finally {
		qzConnected.value = false
	}
}

// ============================================================================
// Printer Discovery
// ============================================================================

/**
 * List all printers available on the system via QZ Tray.
 * Connects automatically if not already connected.
 * @returns {Promise<string[]>} Array of printer names
 */
export async function findPrinters() {
	if (!qz.websocket.isActive()) {
		const ok = await connect()
		if (!ok) return []
	}

	try {
		const printers = await qz.printers.find()
		log.info(`Found ${printers.length} printer(s)`)
		return printers
	} catch (err) {
		log.error("Error discovering printers:", err?.message || err)
		return []
	}
}

/**
 * Virtual "printers" that Windows/macOS install by default. They are always
 * present even on a till with no hardware attached, and printing to one opens a
 * save-file dialog instead of producing paper — which defeats the whole point of
 * auto-printing. Auto-detection must skip them so that "only virtual printers
 * available" is correctly treated as "no printer".
 */
const VIRTUAL_PRINTER_PATTERNS = [
	"microsoft print to pdf",
	"microsoft xps document writer",
	"onenote",
	"fax",
	"adobe pdf",
	"foxit",
	"cutepdf",
	"pdf24",
	"dopdf",
	"bullzip",
	"primopdf",
	"nitro pdf",
	"print to pdf",
	"pdf-xchange",
	"preview", // macOS "Save as PDF"-style entries
]

/**
 * Whether a printer name looks like a virtual/PDF printer rather than hardware.
 * @param {string} name
 * @returns {boolean}
 */
export function isVirtualPrinter(name) {
	const lower = (name || "").toLowerCase()
	return VIRTUAL_PRINTER_PATTERNS.some((pattern) => lower.includes(pattern))
}

/**
 * Work out which physical printer to use without asking the cashier anything.
 *
 * Order: the printer chosen in POS Settings → the machine's OS default printer
 * → the first printer QZ Tray can see. Auto-print relies on this so a till that
 * was never configured in POS Settings still prints, as long as the OS has a
 * default printer set.
 *
 * An explicit choice in POS Settings is honoured even if it looks virtual — the
 * cashier picked it on purpose. Auto-detected candidates are filtered, so a
 * machine whose only "printer" is Microsoft Print to PDF resolves to "" and the
 * caller falls back to downloading the receipt.
 *
 * @returns {Promise<string>} printer name, or "" when the machine has no
 *   physical printer
 */
export async function resolvePrinter() {
	const saved = getSavedPrinterName()
	if (saved) return saved

	if (!qz.websocket.isActive()) {
		const ok = await connect()
		if (!ok) return ""
	}

	try {
		const defaultPrinter = await qz.printers.getDefault()
		if (defaultPrinter && !isVirtualPrinter(defaultPrinter)) {
			log.info(`Using OS default printer "${defaultPrinter}"`)
			return defaultPrinter
		}
		if (defaultPrinter) {
			log.info(`Ignoring virtual default printer "${defaultPrinter}"`)
		}
	} catch (err) {
		log.warn("Could not read OS default printer:", err?.message || err)
	}

	const physical = (await findPrinters()).filter((name) => !isVirtualPrinter(name))
	if (physical[0]) {
		log.info(`No physical default printer, using first available "${physical[0]}"`)
		return physical[0]
	}

	log.info("No physical printer found on this machine")
	return ""
}

// ============================================================================
// Print Dispatch
// ============================================================================

/**
 * Send rendered HTML to a printer via QZ Tray pixel printing.
 *
 * @param {string} html - Full HTML document string to print
 * @param {string} [printerName] - Target printer. Auto-detected when omitted.
 * @param {Object} [options] - Extra print options
 * @param {number} [options.width] - Paper width in mm (default 80)
 * @param {string} [options.orientation] - "portrait" | "landscape" (default "portrait")
 * @returns {Promise<boolean>} true if print was dispatched successfully
 */
export async function printHTML(html, printerName, options = {}) {
	if (!qz.websocket.isActive()) {
		const ok = await connect()
		if (!ok) {
			throw new Error("QZ Tray is not available")
		}
	}

	const printer = printerName || (await resolvePrinter())
	if (!printer) {
		throw new Error("No printer found on this machine")
	}

	const config = qz.configs.create(printer, {
		size: {
			width: options.width || 80,
			height: null, // auto height for receipts
		},
		units: "mm",
		orientation: options.orientation || "portrait",
		margins: { top: 0, right: 0, bottom: 0, left: 0 },
		colorType: "grayscale",
		interpolation: "nearest-neighbor",
	})

	const data = [
		{
			type: "pixel",
			format: "html",
			flavor: "plain",
			data: html,
		},
	]

	try {
		await qz.print(config, data)
		log.info(`Print job sent to "${printer}"`)
		return true
	} catch (err) {
		log.error(`Print failed on "${printer}":`, err?.message || err)
		throw err
	}
}
