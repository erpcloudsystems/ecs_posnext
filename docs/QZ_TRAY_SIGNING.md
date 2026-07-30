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

3. Restart QZ Tray: right-click the tray icon → **Exit**, then start QZ Tray again.

4. Reload the POS. No dialog should appear — check the printer indicator in the POS
   header turns green.

### Faster stopgap

If you can't put the file on the machine right now: the next time the dialog
appears, tick **Remember this decision** and click **Allow**. Because the request
is now signed, QZ Tray stores that decision against the certificate and keeps it
across restarts. Installing `override.crt` is still preferable — it works on a
fresh till with no cashier interaction at all.

## Troubleshooting

**Dialog still appears after installing `override.crt`**
- QZ Tray was not restarted, or the file landed in the wrong folder (check the
  exact filename — `override.crt`, not `override.crt.txt`).
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
