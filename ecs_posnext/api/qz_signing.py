# Copyright (c) 2025, BrainWise and contributors
# For license information, please see license.txt

"""
QZ Tray request signing.

QZ Tray answers every *unsigned* request with the "Anonymous request / Untrusted
website" dialog, so a till pops that prompt again on each POS reload. Requests
signed by a certificate QZ Tray trusts are served silently instead.

This module keeps one self-signed keypair per site, generated on first use and
stored under the site's private directory. It is only ever used to authenticate
print requests to the QZ Tray running on the cashier's own machine — it is not a
web-server certificate and is never used for TLS.

Install the public certificate on each till (see docs/qz-tray-signing.md) so QZ
Tray stops asking altogether.
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
#: short expiry would mean silently re-visiting each machine.
CERT_VALIDITY_DAYS = 365 * 20


# ============================================================================
# Key material on disk
# ============================================================================


def _key_dir():
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

	name = x509.Name(
		[
			x509.NameAttribute(NameOID.COMMON_NAME, frappe.local.site),
			x509.NameAttribute(NameOID.ORGANIZATION_NAME, "POS Next"),
			x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "QZ Tray Printing"),
		]
	)

	now = datetime.datetime.now(datetime.timezone.utc)
	certificate = (
		x509.CertificateBuilder()
		.subject_name(name)
		.issuer_name(name)
		.public_key(private_key.public_key())
		.serial_number(x509.random_serial_number())
		# Backdated a day so a till whose clock runs slow still accepts it.
		.not_valid_before(now - datetime.timedelta(days=1))
		.not_valid_after(now + datetime.timedelta(days=CERT_VALIDITY_DAYS))
		# QZ Tray validates the signing certificate against its trusted store, so
		# the certificate the admin installs has to be usable as its own issuer.
		.add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
		.sign(private_key, hashes.SHA256())
	)

	cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
	key_pem = private_key.private_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.PKCS8,
		encryption_algorithm=serialization.NoEncryption(),
	).decode()

	return cert_pem, key_pem


def ensure_material():
	"""
	Return (certificate_pem, private_key_pem), generating the keypair on first call.

	Guarded by a file lock: two workers racing here would otherwise leave a
	certificate from one keypair next to the private key of another, and every
	signature would then be rejected.
	"""
	certificate, private_key = _read_material()
	if certificate and private_key:
		return certificate, private_key

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
	SHA1withRSA, so tills on it ask the POS for a SHA1 signature. Newer versions
	verify whatever the request advertises.
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
	is unreachable — signing every print job server-side would make offline sales
	fall back to the "Untrusted website" prompt (or fail outright). Sites that
	would rather keep the key server-side can set `qz_tray_server_side_signing`
	in site_config.json; the POS then calls `sign_message` per request instead.
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
