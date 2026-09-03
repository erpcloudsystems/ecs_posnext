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
const PAPER_WIDTH_STORAGE_KEY = "pos_qz_paper_width"

/** Roll width in mm used when the till has not been configured. */
export const DEFAULT_PAPER_WIDTH_MM = 80

/** Roll widths thermal printers actually come in. */
export const PAPER_WIDTH_OPTIONS = [58, 80]

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

/**
 * Paper roll width in mm for this till.
 *
 * Per-till rather than a POS Profile field on purpose: the same profile is used
 * from counters with different printers, and the roll is a property of the
 * hardware in front of the cashier.
 */
export function getPaperWidth() {
	try {
		const saved = Number.parseFloat(
			localStorage.getItem(PAPER_WIDTH_STORAGE_KEY),
		)
		if (Number.isFinite(saved) && saved > 0) return saved
	} catch {
		// fall through to the default
	}
	return DEFAULT_PAPER_WIDTH_MM
}

export function savePaperWidth(mm) {
	try {
		localStorage.setItem(
			PAPER_WIDTH_STORAGE_KEY,
			String(mm || DEFAULT_PAPER_WIDTH_MM),
		)
	} catch (e) {
		log.warn("Failed to save paper width to localStorage:", e)
	}
}

// ============================================================================
// Security Setup (once)
// ============================================================================

/**
 * QZ Tray 2.0 — the last release that runs on Windows 7, so it is what the older
 * tills are stuck on — ignores the `signAlgorithm` the browser advertises and
 * always verifies signatures as SHA1withRSA. A SHA-512 signature simply fails to
 * verify there, and a request whose signature does not verify is treated as
 * unsigned: the "Untrusted website" prompt comes back on every print, however
 * correctly `override.crt` is installed.
 *
 * SHA1 is verified by every version, so that is what we start on. The stronger
 * hash is switched on only after the handshake reports 2.1 or newer.
 */
const LEGACY_SIGN_ALGORITHM = "SHA1"
const PREFERRED_SIGN_ALGORITHM = "SHA512"

/** WebCrypto spells the digests differently to QZ Tray. */
const WEBCRYPTO_HASH = {
	SHA1: "SHA-1",
	SHA256: "SHA-256",
	SHA512: "SHA-512",
}

/** Set up once per page session; concurrent connects share the same promise. */
let _securityPromise = null

/** Whether requests are signed at all — false when the site has no certificate. */
let _signingEnabled = false

/** Algorithm currently advertised to QZ Tray and used to produce signatures. */
let _signAlgorithm = LEGACY_SIGN_ALGORITHM

/** Signing key as PEM, or null when the site keeps the key server-side. */
let _privateKeyPem = null

/**
 * Imported keys per algorithm. The hash is bound to a `CryptoKey` at import, so
 * each algorithm needs its own. A cached `null` means "this browser cannot sign
 * that way" — the request goes to the server instead.
 * @type {Map<string, CryptoKey|null>}
 */
const _signingKeys = new Map()

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
		const material = await call(
			"ecs_posnext.api.qz_signing.get_signing_material",
		)
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
 * Import the signing key for in-browser signing with one algorithm.
 * @returns {Promise<CryptoKey|null>} null when the browser can't do it — WebCrypto
 *   is unavailable on pages served over plain http, for instance.
 */
async function importSigningKey(privateKeyPem, algorithm) {
	if (!globalThis.crypto?.subtle) {
		log.warn(
			"WebCrypto unavailable — QZ Tray requests will be signed server-side",
		)
		// Worth spelling out, because the cost is easy to miss: every QZ Tray call
		// (connect, printer lookup, and the print itself) then needs its own
		// round trip to the server for a signature, on every single receipt.
		if (!globalThis.isSecureContext) {
			log.warn(
				"This page is not a secure context, which is why the browser will not sign locally. " +
					"Serving the POS over https (or from localhost) removes several server round trips per receipt.",
			)
		}
		return null
	}

	let key
	try {
		key = await crypto.subtle.importKey(
			"pkcs8",
			pemToBytes(privateKeyPem),
			{ name: "RSASSA-PKCS1-v1_5", hash: WEBCRYPTO_HASH[algorithm] },
			false,
			["sign"],
		)
	} catch (err) {
		log.warn(
			`Could not import QZ Tray signing key for ${algorithm}:`,
			err?.message || err,
		)
		return null
	}

	// Prove the key actually signs before committing to it. A key the browser
	// accepts but cannot use would block printing outright, where falling back to
	// server-side signing keeps the till selling.
	try {
		await signLocally(key, "qz-tray-signing-probe")
	} catch (err) {
		log.warn(
			`QZ Tray signing key failed a test ${algorithm} signature:`,
			err?.message || err,
		)
		return null
	}

	return key
}

/**
 * Imported key for `algorithm`, or null when this browser has to defer to the
 * server. Cached — including the failures, so a broken import is not retried on
 * every print job.
 */
async function getSigningKey(algorithm) {
	if (_signingKeys.has(algorithm)) return _signingKeys.get(algorithm)

	const key = _privateKeyPem
		? await importSigningKey(_privateKeyPem, algorithm)
		: null
	_signingKeys.set(algorithm, key)
	return key
}

async function signLocally(key, message) {
	const signature = await crypto.subtle.sign(
		"RSASSA-PKCS1-v1_5",
		key,
		new TextEncoder().encode(message),
	)
	let binary = ""
	for (const byte of new Uint8Array(signature)) {
		binary += String.fromCharCode(byte)
	}
	return btoa(binary)
}

async function signOnServer(message, algorithm) {
	return await call("ecs_posnext.api.qz_signing.sign_message", {
		request: message,
		algorithm,
	})
}

/** Sign one request with whichever algorithm the connected QZ Tray can verify. */
async function signRequest(message) {
	const algorithm = _signAlgorithm
	const key = await getSigningKey(algorithm)
	return key
		? await signLocally(key, message)
		: await signOnServer(message, algorithm)
}

async function _initSecurity() {
	const material = await loadSigningMaterial()
	if (!material?.certificate) {
		useUnsignedRequests()
		return
	}

	_signingEnabled = true
	_privateKeyPem = material.private_key || null
	_signAlgorithm = LEGACY_SIGN_ALGORITHM

	qz.security.setCertificatePromise((resolve) => {
		resolve(material.certificate)
	})

	qz.security.setSignatureAlgorithm(_signAlgorithm)
	qz.security.setSignaturePromise((toSign) => {
		return (resolve, reject) => {
			signRequest(toSign)
				.then(resolve)
				.catch((err) => {
					log.error("Could not sign QZ Tray request:", err?.message || err)
					reject(err)
				})
		}
	})

	const key = await getSigningKey(_signAlgorithm)
	log.info(
		`QZ Tray requests will be signed ${key ? "in the browser" : "on the server"} (${_signAlgorithm})`,
	)
}

/**
 * Move to the stronger hash once the handshake says the till runs a QZ Tray that
 * can verify it. Only callable while connected: the version is unknown before
 * that, and `qz.api.isVersion` throws when there is no connection.
 */
async function upgradeSignatureAlgorithm() {
	if (!_signingEnabled) return

	let legacy = true
	try {
		legacy = qz.api.isVersion(2, 0)
	} catch (err) {
		log.warn("Could not read the QZ Tray version:", err?.message || err)
	}

	const algorithm = legacy ? LEGACY_SIGN_ALGORITHM : PREFERRED_SIGN_ALGORITHM
	if (algorithm === _signAlgorithm) {
		if (legacy) log.info("QZ Tray 2.0 detected — signing requests with SHA1")
		return
	}

	// Only switch once we know we can produce that signature. Advertising an
	// algorithm we then fail to sign with would break printing outright.
	if (_privateKeyPem && !(await getSigningKey(algorithm))) return

	_signAlgorithm = algorithm
	qz.security.setSignatureAlgorithm(algorithm)
	log.info(`Signing QZ Tray requests with ${algorithm}`)
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

	if (
		!force &&
		_lastFailedConnectAt &&
		Date.now() - _lastFailedConnectAt < FAILED_CONNECT_COOLDOWN_MS
	) {
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

/**
 * Warm up QZ Tray ahead of the first sale, without blocking anything.
 *
 * The signing handshake and the websocket port walk cost a noticeable amount on
 * a cold page, and until now that was paid by whichever receipt happened to be
 * printed first — i.e. with a customer waiting. Called at shift open, where
 * there is nobody to keep waiting.
 *
 * Never throws, never forces past the post-failure cooldown, and does nothing on
 * a till that has no QZ Tray.
 */
export async function prewarm() {
	try {
		if (qz.websocket.isActive()) return

		const ok = await connect()
		if (!ok) return

		// Settle the printer too, so the first receipt has nothing left to discover.
		await resolvePrinter()
		log.debug("QZ Tray pre-warmed")
	} catch (err) {
		log.debug("QZ Tray pre-warm skipped:", err?.message || err)
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
		await upgradeSignatureAlgorithm()
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

	const physical = (await findPrinters()).filter(
		(name) => !isVirtualPrinter(name),
	)
	if (physical[0]) {
		log.info(
			`No physical default printer, using first available "${physical[0]}"`,
		)
		return physical[0]
	}

	log.info("No physical printer found on this machine")
	return ""
}

// ============================================================================
// Print Dispatch
// ============================================================================

/** Connect if needed and settle on a printer, or throw with a usable reason. */
async function requirePrinter(printerName) {
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
	return printer
}

/**
 * Send a server-rendered PDF to a printer via QZ Tray.
 *
 * This is the receipt path. The PDF is produced by wkhtmltopdf on the server,
 * which shapes and reorders Arabic correctly; QZ Tray only rasterizes the
 * finished page. Letting QZ render HTML instead leaves the text layout to its
 * own engine, which breaks RTL scripts.
 *
 * The job is sized to the PDF's own page box, so the driver feeds the length of
 * the receipt and cuts, instead of a full default page.
 *
 * @param {string} base64 - PDF bytes, base64-encoded
 * @param {string} [printerName] - Target printer. Auto-detected when omitted.
 * @param {Object} [options]
 * @param {number} [options.width] - Page width in mm (defaults to the till's roll width)
 * @param {number} [options.height] - Page height in mm. Printer default when omitted.
 * @returns {Promise<boolean>} true if the print was dispatched successfully
 */
export async function printPDF(base64, printerName, options = {}) {
	if (!base64) throw new Error("No PDF content to print")

	const printer = await requirePrinter(printerName)
	const width = options.width || getPaperWidth()

	const configOptions = {
		units: "mm",
		orientation: options.orientation || "portrait",
		margins: { top: 0, right: 0, bottom: 0, left: 0 },
		colorType: "grayscale",
		interpolation: "nearest-neighbor",
		// A thermal head cannot print the full width of the roll (72mm of an 80mm
		// one, typically). Scaling to the printable area keeps both edges of the
		// receipt rather than cropping them.
		scaleContent: true,
		rasterize: true,
	}
	// Only pin the paper size when the page height is known — a size with no
	// height makes some drivers fall back to their full default page length.
	if (width && options.height) {
		configOptions.size = { width, height: options.height }
	}

	const config = qz.configs.create(printer, configOptions)

	const data = [
		{
			type: "pixel",
			format: "pdf",
			flavor: "base64",
			data: base64,
		},
	]

	try {
		await qz.print(config, data)
		log.info(`PDF print job sent to "${printer}" (${width}mm roll)`)
		return true
	} catch (err) {
		log.error(`PDF print failed on "${printer}":`, err?.message || err)
		throw err
	}
}

// `format: "html"` pixel printing was removed on purpose: QZ Tray renders that
// HTML with its own engine, which does no complex-script shaping, so Arabic came
// out with unjoined letters in the wrong order. Receipts go through printPDF.
