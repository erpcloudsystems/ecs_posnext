# QZ Tray Signing — removing the "Untrusted website" prompt

QZ Tray shows this dialog for every **unsigned** request:

> **Action Required** — An anonymous request wants to connect to QZ Tray
> *Untrusted website* — [Allow] [Block]

Because the POS connects on each load, the cashier sees it again after every
reload. The fix is the one QZ documents: sign the requests with a certificate,
and install that certificate on the till so QZ Tray trusts it silently.

POS Next does the signing part automatically. Installing the certificate on each
machine is a one-time manual step (three minutes per till).

## How it works

- On the first POS load, the server generates a self-signed RSA keypair for the
  site and stores it in `sites/<site>/private/qz-tray/`
  (`certificate.pem`, `private-key.pem`, mode `600`).
  It is **only** used to authenticate print requests to QZ Tray on the cashier's
  own machine — never for TLS, never as a web-server certificate.
- The POS fetches the certificate (and the signing key) once per session, caches
  it in `localStorage`, and signs every QZ Tray request in the browser with
  `RSASSA-PKCS1-v1_5 / SHA-512`. Signing in the browser is deliberate: a till in
  offline mode can still print, which server-side signing would prevent.
- If anything fails — no backend endpoint, offline first load, WebCrypto blocked —
  the POS falls back to unsigned requests. Printing keeps working exactly as
  before; the dialog just comes back.

Code: [`ecs_posnext/api/qz_signing.py`](../ecs_posnext/api/qz_signing.py),
[`POS/src/utils/qzTray.js`](../POS/src/utils/qzTray.js).

## Install the certificate on a till (one time per machine)

1. Log into the site as a **System Manager** and open:

   ```
   https://<your-site>/api/method/ecs_posnext.api.qz_signing.download_certificate
   ```

   This downloads `override.crt`. (Same file for every till on the site — copy it
   to a USB stick or a share once.)

2. Copy `override.crt` into the QZ Tray installation folder:

   | OS      | Path                                        |
   | ------- | ------------------------------------------- |
   | Windows | `C:\Program Files\QZ Tray\override.crt`     |
   | macOS   | `/Applications/QZ Tray.app/Contents/Resources/override.crt` |
   | Linux   | `/opt/qz-tray/override.crt`                 |

   On Windows this needs administrator rights (accept the UAC prompt when copying).
   Check the real filename: with Explorer hiding known extensions, a browser save
   easily leaves you with `override.crt.txt`, which QZ Tray ignores. Turn on
   **View → File name extensions** and confirm.

3. Point QZ Tray's config at it. Open `C:\Program Files\QZ Tray\qz-tray.properties`
   in Notepad **run as administrator**, and add (or correct) the line:

   ```
   authcert.override=C:/Program Files/QZ Tray/override.crt
   ```

   **Use forward slashes.** This is a Java properties file, where `\` is an escape
   character: `C:\Program Files\...` is read as `C:Program Files...` and QZ Tray
   quietly falls back to its built-in root, leaving the certificate untrusted with
   no visible error. (`C:\\Program Files\\...` also works, if you prefer.)

   Only QZ Tray **2.1 and newer** picks up `override.crt` from the installation
   folder on its own. On **2.0.x** — which is what Windows 7 tills run — this
   property (or `-DtrustedRootCert=`) is the *only* mechanism; the file sitting in
   the folder is ignored entirely. Setting the property works on every version, so
   always set it.

4. Restart QZ Tray completely: right-click the tray icon → **Exit**, then start it
   again. If it was installed as a Windows service, restart the **QZ Tray** service
   in `services.msc` (or reboot) — closing the tray icon alone does not reload the
   configuration.

5. Reload the POS. No dialog should appear — check the printer indicator in the POS
   header turns green.

### Stopgap while the certificate is not installed

Click **Allow** — without ticking "Remember this decision" — and the till keeps
selling. The prompt returns on the next reload.

There is no way to make it permanent from the dialog: QZ Tray only lets you
*remember* a decision for a certificate it already trusts, so ticking the box
greys **Allow** out. That greyed-out button is the reliable signal that steps 2–3
have not taken effect yet.

## Windows 7 tills (QZ Tray 2.0.x)

QZ Tray 2.1 dropped Windows 7, so those tills run 2.0.4 — and 2.0 verifies every
signature as **SHA1withRSA**. It ignores the algorithm the browser advertises, so
a SHA-512 signature does not verify, and a request whose signature does not verify
is treated as unsigned. The result looks exactly like a certificate problem: the
prompt keeps appearing no matter how correctly `override.crt` is installed.

The POS handles this itself. It starts on SHA1 — which *every* QZ Tray version
verifies — and only moves up to SHA-512 after the handshake reports 2.1 or newer.
Nothing to configure; a 2.0 till just needs the POS build that contains this.

Confirm it in the browser console on the till. You want:

```
[QZTray] QZ Tray requests will be signed in the browser (SHA1)
[QZTray] QZ Tray 2.0 detected — signing requests with SHA1
```

Two other things to know about 2.0:

- **`override.crt` sitting in the installation folder does nothing on 2.0.x.**
  Auto-discovery of that file arrived in 2.1. On 2.0 the certificate is only
  trusted if `authcert.override` in `qz-tray.properties` points at it — with
  forward slashes (step 3 above). This is the usual reason a Windows 7 till keeps
  showing "Untrusted website" after the file has been copied into place.
- Windows 7 clocks drift. QZ Tray rejects a request whose timestamp is far from
  its own clock, which also shows up as a prompt — check the till's date and time.

## Troubleshooting

**"Allow" is greyed out as soon as "Remember this decision" is ticked**
QZ Tray only lets you permanently allow a certificate it trusts — an untrusted one
can be permanently *blocked* but not permanently allowed. So this means the
certificate is not trusted on that machine yet: `override.crt` is missing, misnamed,
or `authcert.override` is not set in `qz-tray.properties` (steps 2–4 above).
Untick the checkbox and **Allow** works again per request, which keeps the till
selling until the certificate is in place.

**Dialog still appears after installing `override.crt`**
- QZ Tray was not restarted, or the file landed in the wrong folder (check the
  exact filename — `override.crt`, not `override.crt.txt`).
- `authcert.override` is missing from `qz-tray.properties`, or points at a path
  that doesn't exist.
- Confirm what QZ Tray actually received: click **View request details** in the
  dialog. The certificate should read `CN=<your site>, O=POS Next,
  OU=QZ Tray Printing`. Tray icon → **Advanced → Diagnostic → View Logs** shows
  why a certificate was rejected.
- The POS is running unsigned. Open the browser console and look for
  `[QZTray] QZ Tray requests will be signed in the browser`. If instead you see
  `Could not fetch QZ Tray signing material`, the browser could not reach the
  endpoint — reload while online.

**Dialog names the site instead of "anonymous request"**
Signing works; the certificate just isn't trusted on that machine yet. Finish
step 2–3, or use the stopgap above.

**POS served over plain `http://` on a LAN IP**
Browsers expose WebCrypto only in a secure context, so the POS falls back to
signing on the server (a request per print job — it needs the server reachable).
Serving the POS over HTTPS restores offline-capable browser signing.

## Keeping the key server-side

To avoid handing the signing key to the browser, set in `site_config.json`:

```json
{ "qz_tray_server_side_signing": 1 }
```

The POS then calls `ecs_posnext.api.qz_signing.sign_message` per request. Trade-off:
printing needs the server reachable, so offline sales lose silent printing.

## Rotating the key

Delete `sites/<site>/private/qz-tray/`, then reload the POS — a new keypair is
generated. Every till needs the new `override.crt`, and each browser needs one
online reload to pick up the new material (it is cached under the `localStorage`
key `pos_qz_signing_material`).
