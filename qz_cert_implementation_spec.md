# QZ Tray Request Signing — Implementation Spec

**Audience: an AI coding agent implementing this in a different POS application.**

This is a port specification, not a tutorial. It contains the complete reference
implementation, the exact contracts between the pieces, and — most importantly —
the reasoning behind each non-obvious decision. Several of those decisions look
like over-engineering and are not; they are fixes for failures observed on real
tills. **Do not simplify them away.** Sections marked ⚠️ are where a reasonable-
looking simplification breaks production.

---

## 0. TL;DR of what you are building

| Piece | What it does |
| ----- | ------------ |
| Server: key material | Generate + store one self-signed RSA keypair per site/tenant |
| Server: 3 endpoints | Hand the cert + key to the POS, sign a message, download `override.crt` |
| Client: security setup | Register QZ's certificate + signature callbacks once per page session |
| Client: signing | Sign each request with WebCrypto, falling back to the server |
| Client: algorithm negotiation | Start on SHA1, upgrade to SHA512 only after the handshake proves QZ ≥ 2.1 |
| Ops: install | Copy `override.crt` onto each till + set `authcert.override` |

Non-negotiable invariant: **every failure path degrades to unsigned printing, never to broken printing.** A till that cannot sign must still print — the cashier just sees the approval dialog again.

---

## 1. The problem

QZ Tray is a desktop app on the cashier's machine exposing a local websocket
(ports 8181 secure / 8182 insecure). Any web page can connect, so QZ Tray shows
an approval dialog for every **unsigned** request:

> **Action Required** — An anonymous request wants to connect to QZ Tray
> *Untrusted website* — [Allow] [Block]

A POS connects on every page load, so the cashier sees this after every reload.

The fix QZ documents: the page presents an X.509 certificate and signs every
request. Once that certificate is installed in QZ Tray's trust store on the
machine, requests are served silently.

**This certificate is not a TLS certificate.** It authenticates print requests to
a local desktop process. It has nothing to do with the site's HTTPS, and must
never be confused with a web-server certificate.

---

## 2. Architecture decisions you must preserve

These are the decisions that cost real debugging time. Each one has a failure
mode attached. Read this section before writing code.

### 2.1 ⚠️ The private key goes to the browser (by default)

The obvious-looking design is to keep the key on the server and sign each request
there. **That breaks offline selling.** A till in offline mode can still print —
if it can sign locally. Server-side signing means every QZ call (connect, printer
lookup, and each print) needs a round trip, so an offline till loses silent
printing entirely, and an online one pays 3+ extra round trips per receipt.

So: ship the key to the browser, cache it, sign locally. Provide a config flag for
deployments whose threat model forbids this, and document the trade-off.

Consider the actual exposure honestly: the key signs print requests to a desktop
app on the same machine as the authenticated user. It is not a credential for
anything else. Treat it as a capability token, not a secret.

### 2.2 ⚠️ Start on SHA1, upgrade after the handshake

**This is the single most expensive bug to rediscover.**

QZ Tray 2.0 — the last version that runs on Windows 7, so it is what older tills
are stuck on — **ignores the `signAlgorithm` the browser advertises and always
verifies as `SHA1withRSA`.** A SHA-512 signature does not verify there, and a
request whose signature fails to verify is treated as *unsigned*.

The symptom is indistinguishable from a broken certificate install: the prompt
keeps appearing no matter how correctly `override.crt` is deployed. Someone will
spend a day reinstalling certificates.

Therefore:
- Initialise with **SHA1**, which every QZ version verifies.
- Only after the websocket handshake — where `qz.api.isVersion(2, 0)` reveals the
  real version — upgrade to SHA-512.
- `qz.api.isVersion()` **throws when not connected**, so it cannot be called during
  setup. The upgrade must happen in the connect success path.
- Only switch after confirming a key for the new algorithm imported successfully.
  Advertising an algorithm you then fail to sign with breaks printing outright.

Yes, SHA1 for a window. The alternative is tills that cannot print.

### 2.3 ⚠️ The certificate must be a CA (`BasicConstraints(ca=True)`)

QZ Tray validates the signing certificate against its trusted store. A
self-signed leaf without `ca=True` is rejected as an invalid chain — it must be
usable as its own issuer. Omit this and the certificate installs cleanly and
still never works.

### 2.4 ⚠️ Backdate `not_valid_before` by one day

Till clocks drift, especially older Windows machines. A certificate that becomes
valid "now" is rejected by a till whose clock runs a few minutes slow.

### 2.5 ⚠️ Long validity (20 years)

The certificate is copied onto every till **by hand**. A 1-year expiry means
silently re-visiting every machine in the estate on an unknown date, with the
failure presenting as "the dialog came back". Make it outlive the hardware.

### 2.6 ⚠️ Generation must be behind a lock

Two workers racing on first load will each generate a keypair and interleave the
writes, leaving `certificate.pem` from one pair next to `private-key.pem` from
another. Every signature then fails verification, and the state looks perfectly
healthy on disk. Use a named lock plus double-checked read, and write each file
atomically (temp file + rename) so a reader never sees a half-written key.

### 2.7 ⚠️ Probe the imported key with a test signature

A browser can accept `crypto.subtle.importKey()` and still fail to sign with the
result. If you discover that at print time you have already committed to local
signing and the receipt fails. Sign a throwaway string at import time; on failure
return `null` and fall back to the server. Cache the failure too, so a broken
import is not retried on every print job.

### 2.8 ⚠️ Cache imported keys *per algorithm*

WebCrypto binds the hash to the `CryptoKey` at import. A key imported for SHA1
cannot produce a SHA-512 signature. One cache entry per algorithm; a cached
`null` means "this browser cannot sign that way".

### 2.9 ⚠️ Cache signing material in `localStorage`

A till that opens the POS while offline must still sign. Fetch from the server
when possible, write through to `localStorage`, and fall back to the cached copy
on any fetch failure (offline, or a backend that predates the endpoint).

### 2.10 WebCrypto needs a secure context

`crypto.subtle` is `undefined` on pages served over plain `http://` to a LAN IP.
That is a common POS deployment. Detect it, fall back to server-side signing, and
log loudly that HTTPS would remove several round trips per receipt — otherwise
nobody connects the slowness to the URL scheme.

---

## 3. Server implementation

### 3.1 Dependencies

Python `cryptography`. On Frappe this is already a transitive dependency — check
before adding it. Elsewhere: `pip install cryptography`.

### 3.2 Storage layout

One keypair per site/tenant, in a private directory the web server does not serve:

```
<site>/private/qz-tray/
├── certificate.pem   (mode 644 — public)
└── private-key.pem   (mode 600 — secret)
```

Directory mode `700`.

### 3.3 Reference implementation

Complete and working. Frappe-specific calls are flagged inline with porting notes.

```python
"""
QZ Tray request signing.

QZ Tray answers every *unsigned* request with the "Anonymous request / Untrusted
website" dialog, so a till pops that prompt again on each POS reload. Requests
signed by a certificate QZ Tray trusts are served silently instead.

This module keeps one self-signed keypair per site, generated on first use and
stored under the site's private directory. It is only ever used to authenticate
print requests to the QZ Tray running on the cashier's own machine — it is not a
web-server certificate and is never used for TLS.
"""

import base64
import datetime
import os

import frappe
from frappe import _
from frappe.utils.synchronization import filelock

KEY_DIR_NAME = "qz-tray"
CERT_FILENAME = "certificate.pem"
KEY_FILENAME = "private-key.pem"

#: Long-lived on purpose. The certificate is copied onto every till by hand, so a
#: short expiry would mean silently re-visiting each machine.  [§2.5]
CERT_VALIDITY_DAYS = 365 * 20


# ============================================================================
# Key material on disk
# ============================================================================

def _key_dir():
	# PORT: replace with your framework's per-tenant private storage path.
	return frappe.get_site_path("private", KEY_DIR_NAME)


def _read_material():
	"""Return (certificate_pem, private_key_pem), or (None, None) when not generated yet."""
	directory = _key_dir()
	cert_path = os.path.join(directory, CERT_FILENAME)
	key_path = os.path.join(directory, KEY_FILENAME)

	try:
		with open(cert_path) as f:
			certificate = f.read()
		with open(key_path) as f:
			private_key = f.read()
	except OSError:
		return None, None

	if not certificate.strip() or not private_key.strip():
		return None, None

	return certificate, private_key


def _write_atomically(path, content, mode):
	"""Write via a temp file + rename so a reader never sees a half-written key."""
	tmp_path = f"{path}.tmp"
	with open(tmp_path, "w") as f:
		f.write(content)
	os.chmod(tmp_path, mode)
	os.replace(tmp_path, path)


def _generate_material():
	"""Create a self-signed RSA keypair for QZ Tray and return (cert_pem, key_pem)."""
	from cryptography import x509
	from cryptography.hazmat.primitives import hashes, serialization
	from cryptography.hazmat.primitives.asymmetric import rsa
	from cryptography.x509.oid import NameOID

	private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

	# PORT: CN should identify the deployment — it is what the admin sees in QZ
	# Tray's "View request details" dialog when verifying an install.
	name = x509.Name([
		x509.NameAttribute(NameOID.COMMON_NAME, frappe.local.site),
		x509.NameAttribute(NameOID.ORGANIZATION_NAME, "POS Next"),
		x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "QZ Tray Printing"),
	])

	now = datetime.datetime.now(datetime.timezone.utc)
	certificate = (
		x509.CertificateBuilder()
		.subject_name(name)
		.issuer_name(name)
		.public_key(private_key.public_key())
		.serial_number(x509.random_serial_number())
		# Backdated a day so a till whose clock runs slow still accepts it.  [§2.4]
		.not_valid_before(now - datetime.timedelta(days=1))
		.not_valid_after(now + datetime.timedelta(days=CERT_VALIDITY_DAYS))
		# QZ Tray validates the signing certificate against its trusted store, so
		# the certificate the admin installs has to be usable as its own issuer.  [§2.3]
		.add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
		.sign(private_key, hashes.SHA256())
	)

	cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
	key_pem = private_key.private_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.PKCS8,   # WebCrypto importKey("pkcs8") requires this
		encryption_algorithm=serialization.NoEncryption(),
	).decode()

	return cert_pem, key_pem


def ensure_material():
	"""
	Return (certificate_pem, private_key_pem), generating the keypair on first call.

	Guarded by a file lock: two workers racing here would otherwise leave a
	certificate from one keypair next to the private key of another, and every
	signature would then be rejected.  [§2.6]
	"""
	certificate, private_key = _read_material()
	if certificate and private_key:
		return certificate, private_key

	# PORT: any named cross-process lock works (file lock, advisory DB lock, redis).
	with filelock("qz_tray_signing_material", timeout=30):
		# Another worker may have won the race while we waited for the lock.
		certificate, private_key = _read_material()
		if certificate and private_key:
			return certificate, private_key

		directory = _key_dir()
		os.makedirs(directory, mode=0o700, exist_ok=True)

		certificate, private_key = _generate_material()
		_write_atomically(os.path.join(directory, KEY_FILENAME), private_key, 0o600)
		_write_atomically(os.path.join(directory, CERT_FILENAME), certificate, 0o644)

		frappe.logger().info("Generated QZ Tray signing certificate for %s", frappe.local.site)

	return certificate, private_key


def _hash_algorithm(algorithm):
	"""
	Digest QZ Tray will verify the signature with.

	QZ Tray 2.0 — the newest release that runs on Windows 7 — only ever verifies
	SHA1withRSA, so tills on it ask the POS for a SHA1 signature.  [§2.2]
	"""
	from cryptography.hazmat.primitives import hashes

	algorithms = {
		"SHA1": hashes.SHA1,
		"SHA256": hashes.SHA256,
		"SHA512": hashes.SHA512,
	}

	factory = algorithms.get((algorithm or "SHA512").upper())
	if not factory:
		frappe.throw(_("Unsupported signing algorithm {0}").format(algorithm))

	return factory()


def sign(message, algorithm="SHA512"):
	"""Sign `message` with the site's QZ Tray key. Returns a base64 signature."""
	from cryptography.hazmat.primitives import serialization
	from cryptography.hazmat.primitives.asymmetric import padding

	_certificate, key_pem = ensure_material()
	private_key = serialization.load_pem_private_key(key_pem.encode(), password=None)

	# PKCS1 v1.5, NOT PSS — QZ Tray verifies RSASSA-PKCS1-v1_5 only.
	signature = private_key.sign(
		message.encode(),
		padding.PKCS1v15(),
		_hash_algorithm(algorithm),
	)
	return base64.b64encode(signature).decode()


# ============================================================================
# Endpoints
# ============================================================================

@frappe.whitelist(allow_guest=False)
def get_signing_material():
	"""
	Certificate the POS presents to QZ Tray, plus the key it signs with.

	The key is handed to the browser so a till can keep printing while the server
	is unreachable.  [§2.1]
	"""
	certificate, private_key = ensure_material()

	material = {"certificate": certificate}
	if not frappe.conf.get("qz_tray_server_side_signing"):
		material["private_key"] = private_key

	return material


@frappe.whitelist(allow_guest=False)
def sign_message(request, algorithm="SHA512"):
	"""Sign a single QZ Tray request. Used when the browser cannot sign locally."""
	if not request:
		frappe.throw(_("Nothing to sign"))

	return sign(request, algorithm)


@frappe.whitelist(allow_guest=False)
def download_certificate():
	"""
	Download the public certificate as `override.crt`, ready to drop into the QZ
	Tray installation folder on a till. Admin-only: it identifies the deployment.
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	certificate, _private_key = ensure_material()

	frappe.response["type"] = "download"
	frappe.response["filename"] = "override.crt"
	frappe.response["filecontent"] = certificate
	frappe.response["display_content_as"] = "attachment"
```

### 3.4 Endpoint contracts

Implement these three exactly; the client depends on the shapes.

| Endpoint | Auth | Request | Response |
| -------- | ---- | ------- | -------- |
| `get_signing_material` | Logged in | — | `{"certificate": "<PEM>", "private_key": "<PKCS8 PEM>"}`; `private_key` **omitted** when server-side signing is configured |
| `sign_message` | Logged in | `request: str`, `algorithm: "SHA1"\|"SHA256"\|"SHA512"` (default `SHA512`) | base64 signature string |
| `download_certificate` | **Admin only** | — | File download, `Content-Disposition: attachment; filename=override.crt`, body = certificate PEM |

Notes:
- `download_certificate` must be admin-gated: the certificate identifies the deployment.
- `sign_message` must reject an empty `request` rather than signing `""`.
- Never expose the private key on an unauthenticated route.

---

## 4. Client implementation

### 4.1 Dependency

```bash
npm install qz-tray    # ^2.2.5 at time of writing
```

### 4.2 Reference implementation (security layer only)

This is the portion of the client that concerns signing. Printing, printer
discovery, connection cooldowns and cash-drawer handling are separate concerns —
see §7.

```javascript
import qz from "qz-tray"
import { call } from "@/utils/apiWrapper"   // PORT: your authenticated RPC helper
import { logger } from "@/utils/logger"

const log = logger.create("QZTray")

const SIGNING_STORAGE_KEY = "pos_qz_signing_material"

/**
 * QZ Tray 2.0 — the last release that runs on Windows 7, so it is what the older
 * tills are stuck on — ignores the `signAlgorithm` the browser advertises and
 * always verifies signatures as SHA1withRSA. A SHA-512 signature simply fails to
 * verify there, and a request whose signature does not verify is treated as
 * unsigned: the "Untrusted website" prompt comes back on every print, however
 * correctly `override.crt` is installed.
 *
 * SHA1 is verified by every version, so that is what we start on. The stronger
 * hash is switched on only after the handshake reports 2.1 or newer.  [§2.2]
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
 * that way" — the request goes to the server instead.  [§2.8]
 * @type {Map<string, CryptoKey|null>}
 */
const _signingKeys = new Map()

/**
 * QZ Tray only serves a request silently when it can verify who sent it.
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
 * so a till that opens the POS offline still signs its print jobs.  [§2.9]
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
 * Import the signing key for in-browser signing with one algorithm.
 * @returns {Promise<CryptoKey|null>} null when the browser can't do it — WebCrypto
 *   is unavailable on pages served over plain http, for instance.  [§2.10]
 */
async function importSigningKey(privateKeyPem, algorithm) {
	if (!globalThis.crypto?.subtle) {
		log.warn("WebCrypto unavailable — QZ Tray requests will be signed server-side")
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
			false,          // not extractable
			["sign"],
		)
	} catch (err) {
		log.warn(`Could not import QZ Tray signing key for ${algorithm}:`, err?.message || err)
		return null
	}

	// Prove the key actually signs before committing to it. A key the browser
	// accepts but cannot use would block printing outright, where falling back to
	// server-side signing keeps the till selling.  [§2.7]
	try {
		await signLocally(key, "qz-tray-signing-probe")
	} catch (err) {
		log.warn(`QZ Tray signing key failed a test ${algorithm} signature:`, err?.message || err)
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

	const key = _privateKeyPem ? await importSigningKey(_privateKeyPem, algorithm) : null
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
	return key ? await signLocally(key, message) : await signOnServer(message, algorithm)
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
 * that, and `qz.api.isVersion` throws when there is no connection.  [§2.2]
 */
async function upgradeSignatureAlgorithm() {
	if (!_signingEnabled) return

	let legacy = true    // assume the worst until proven otherwise
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
```

### 4.3 Wiring into the connect path

Two integration points, both mandatory:

```javascript
async function _doConnect() {
	await setupSecurity()             // 1. BEFORE connecting — the handshake itself is signed

	qzConnecting.value = true
	try {
		await qz.websocket.connect(qzConnectOptions())
		qzConnected.value = true
		await upgradeSignatureAlgorithm()   // 2. AFTER connecting — version is only known now
		return true
	} catch (err) {
		qzConnected.value = false
		log.warn("Could not connect to QZ Tray:", err?.message || err)
		return false
	} finally {
		qzConnecting.value = false
	}
}
```

Order matters. `setupSecurity()` must complete before `connect()` because the
connect handshake is itself a signed request. `upgradeSignatureAlgorithm()` must
run after, because `qz.api.isVersion()` throws when not connected.

### 4.4 Callback semantics (easy to get wrong)

`qz-tray`'s security API uses an unusual curried shape:

```javascript
// Certificate: a function receiving (resolve, reject) directly.
qz.security.setCertificatePromise((resolve, reject) => { resolve(certPem) })

// Signature: a function receiving the string to sign, which RETURNS a function
// receiving (resolve, reject). Note the extra layer.
qz.security.setSignaturePromise((toSign) => {
	return (resolve, reject) => { /* resolve(base64Signature) */ }
})
```

Getting this wrong produces a hang rather than an error — QZ waits forever for a
promise that was never wired up.

For unsigned operation, resolve both with **no arguments**.

---

## 5. Deployment (write this into your own operator docs)

1. Admin downloads `override.crt` from `download_certificate`. One file serves
   every till on the site.
2. Copy it into the QZ Tray installation folder:
   - Windows: `C:\Program Files\QZ Tray\override.crt` (needs admin/UAC)
   - macOS: `/Applications/QZ Tray.app/Contents/Resources/override.crt`
   - Linux: `/opt/qz-tray/override.crt`
3. Edit `qz-tray.properties` (as administrator) and add:
   ```properties
   authcert.override=C:/Program Files/QZ Tray/override.crt
   ```
   ⚠️ **Forward slashes.** It is a Java properties file where `\` escapes:
   `C:\Program Files\...` parses as `C:Program Files...`, QZ silently falls back
   to its built-in root, and the certificate stays untrusted **with no error
   shown anywhere**.

   ⚠️ QZ Tray 2.1+ auto-discovers `override.crt` in its folder. **2.0.x does not** —
   this property is the only mechanism there. Setting it works on all versions, so
   always set it.
4. Restart QZ Tray fully — tray icon → Exit, or restart the Windows service.
   Closing the tray icon alone does not reload configuration.
5. Reload the POS; no dialog should appear.

⚠️ **The `override.crt.txt` trap:** with Windows hiding known extensions, a browser
save easily produces `override.crt.txt`, which QZ ignores silently. Tell operators
to enable **View → File name extensions**.

**Stopgap before install:** click **Allow** *without* ticking "Remember this
decision". Ticking the box greys **Allow** out, because QZ only permanently
allows certificates it already trusts. That greyed-out button is the reliable
diagnostic that the certificate is not yet trusted.

---

## 6. Test plan

| # | Scenario | Setup | Expected |
| - | -------- | ----- | -------- |
| 1 | First generation | No `qz-tray/` dir | Files created, modes 700/600/644, valid PEM |
| 2 | Idempotent | Call `ensure_material()` twice | Identical material, no regeneration |
| 3 | Concurrency | N parallel first calls | One keypair; cert and key are a matching pair |
| 4 | Cert properties | Inspect with `openssl x509 -text` | `CA:TRUE`, `notBefore` in the past, ~20y validity |
| 5 | Signature verifies | `sign()` output | Verifies against cert pubkey, PKCS1v15, each of SHA1/256/512 |
| 6 | Cross-impl parity | Same message, browser vs server | **Byte-identical signatures** (deterministic for PKCS1v15) |
| 7 | Admin gate | `download_certificate` as non-admin | `PermissionError` |
| 8 | Key withheld | `qz_tray_server_side_signing = 1` | Response has no `private_key` |
| 9 | Empty sign | `sign_message("")` | Throws |
| 10 | Offline setup | Cache primed, server down | Signing still active from `localStorage` |
| 11 | No cert at all | Endpoint 404s, empty cache | Unsigned mode; **printing still works** |
| 12 | Insecure context | Serve over `http://<lan-ip>` | Server-side signing, warning logged, prints OK |
| 13 | QZ 2.0 till | Windows 7 + QZ 2.0.x | Stays on SHA1; no dialog once cert installed |
| 14 | QZ 2.1+ till | Modern QZ | Upgrades to SHA512 after connect |
| 15 | Rotation | Delete dir, reload online | New material fetched and re-cached |

Verify #4 and #5 directly:

```bash
openssl x509 -in certificate.pem -noout -text | grep -A1 "Basic Constraints"
# Expect: CA:TRUE
```

```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
import base64

cert = x509.load_pem_x509_certificate(open("certificate.pem","rb").read())
sig  = base64.b64decode(sign("test-message", "SHA512"))
cert.public_key().verify(sig, b"test-message", padding.PKCS1v15(), hashes.SHA512())
print("OK")   # raises InvalidSignature on mismatch
```

---

## 7. Out of scope (but adjacent)

The reference app's client module also handles connection cooldowns, printer
discovery, PDF printing and cash-drawer pulses. Those are independent of signing.
Two are worth copying anyway, because they bite the same deployments:

- **Connect timeout + exponential cooldown.** On a till with no QZ Tray,
  `qz.websocket.connect()` walks several ports, some behind DNS, and can block for
  10–19 seconds *on the sale screen*. Constrain `host`/`port`/`retries`, impose a
  ~1.5s timeout (QZ answers on loopback in milliseconds), and back off
  exponentially after failures — branches with no printer are a supported
  configuration, not a fault to retry at full price.
- **Prewarm at shift open.** The signing handshake plus port walk is a one-off
  cost that otherwise lands on the first receipt, with a customer waiting.

---

## 8. Implementation checklist

Server:
- [ ] `ensure_material()` with named lock + double-checked read
- [ ] Atomic writes, modes 700 / 600 / 644
- [ ] Cert: `ca=True`, backdated `not_valid_before`, ~20y validity, PKCS8 key
- [ ] `sign()` with PKCS1v15 + SHA1/SHA256/SHA512 map
- [ ] `get_signing_material` (auth; omits key when configured)
- [ ] `sign_message` (auth; rejects empty)
- [ ] `download_certificate` (**admin only**, filename `override.crt`)

Client:
- [ ] `setupSecurity()` memoised behind one promise
- [ ] `localStorage` cache, read on fetch failure
- [ ] `useUnsignedRequests()` fallback on every failure path
- [ ] PEM → DER decode; `importKey("pkcs8", …, "RSASSA-PKCS1-v1_5")`
- [ ] Probe signature at import; cache `null` failures
- [ ] Per-algorithm key cache
- [ ] `signRequest()` local → server fallback
- [ ] Init on **SHA1**; `upgradeSignatureAlgorithm()` after connect only
- [ ] `setupSecurity()` before `connect()`; upgrade after
- [ ] Correct curried signature-callback shape

Ops:
- [ ] Operator doc covering forward slashes, `authcert.override` on 2.0.x, the
      `.txt` extension trap, full restart, and the greyed-out-Allow diagnostic
- [ ] Rotation procedure (delete dir → redistribute cert → one online reload per browser)

---

## 9. Reference files in the source app

| File | Contents |
| ---- | -------- |
| `ecs_posnext/api/qz_signing.py` | Complete server implementation |
| `POS/src/utils/qzTray.js` | Complete client (signing + printing + drawer) |
| `qz_cert_docs.md` | Operator/admin guide |
| `docs/QZ_TRAY_SIGNING.md` | Original field notes |
