import { call } from "@/utils/apiWrapper"
import { logger } from "@/utils/logger"
import {
	getPaperWidth,
	printPDF as qzPrintPDF,
	resolvePrinter,
} from "@/utils/qzTray"

const log = logger.create("PrintInvoice")

const DEFAULT_PRINT_FORMAT = "POS Next Receipt"

/** Left/right margin on the roll — thermal heads cannot print to the edge. */
const RECEIPT_SIDE_MARGIN_MM = 2

/** Padding added under the measured content so the last line is never clipped. */
const RECEIPT_TAIL_MM = 6

/** Page length used when the receipt height could not be measured. */
const RECEIPT_FALLBACK_HEIGHT_MM = 297

// ============================================================================
// Shared helpers
// ============================================================================

function formatCurrency(amount) {
	return Number.parseFloat(amount || 0).toFixed(2)
}

/**
 * Fetch server-rendered print HTML + style for a Sales Invoice via our own
 * ecs_posnext endpoint rather than Frappe's core printview endpoints.
 * Frappe's `document.check_permission()` / `validate_print_permission()` run a
 * per-document permission check that cascades into unrelated Account link
 * fields (write_off_account, etc.), which incorrectly blocks branch cashiers
 * from printing invoices they just created themselves.
 */
async function fetchPrintHTML(
	invoiceName,
	{ printFormat, letterhead = null, noLetterhead = 1, inlineAssets = 0 } = {},
) {
	const result = await call("ecs_posnext.api.invoices.get_invoice_print_html", {
		invoice_name: invoiceName,
		print_format: printFormat || DEFAULT_PRINT_FORMAT,
		letterhead,
		no_letterhead: noLetterhead,
		inline_assets: inlineAssets,
	})

	const html = result?.html || result?.message?.html
	const style = result?.style || result?.message?.style || ""
	if (!html) throw new Error("Failed to get print HTML from server")
	return { html, style }
}

/**
 * Fetch a server-rendered PDF of the invoice, base64-encoded.
 *
 * Pass `pageWidth` to get a receipt-roll page instead of A4.
 */
async function fetchPrintPDF(
	invoiceName,
	{
		printFormat,
		letterhead = null,
		noLetterhead = 1,
		pageWidth = null,
		pageHeight = null,
	} = {},
) {
	const result = await call("ecs_posnext.api.invoices.get_invoice_print_pdf", {
		invoice_name: invoiceName,
		print_format: printFormat || DEFAULT_PRINT_FORMAT,
		letterhead,
		no_letterhead: noLetterhead,
		page_width: pageWidth,
		page_height: pageHeight,
		side_margin: pageWidth ? RECEIPT_SIDE_MARGIN_MM : null,
	})

	const payload = result?.message || result
	if (!payload?.content) throw new Error("Server returned no PDF content")
	return payload
}

/**
 * Measure how tall the receipt renders, in mm, so the PDF page can be cut to
 * the content instead of feeding a fixed page length of roll.
 *
 * Measured in a hidden iframe at the exact printable width, with images and
 * fonts resolved first — a letterhead logo that has not loaded yet would make
 * the receipt come out short. Chrome lays text out slightly looser than
 * wkhtmltopdf does, so this reads a little tall; that is the safe direction,
 * since underestimating spills the footer onto a second page (and a second cut).
 *
 * @returns {Promise<number>} height in mm, or 0 if it could not be measured
 */
function measureReceiptHeightMM(fullHTML, contentWidthMM) {
	return new Promise((resolve) => {
		if (typeof document === "undefined") {
			resolve(0)
			return
		}

		const iframe = document.createElement("iframe")
		iframe.setAttribute("aria-hidden", "true")
		iframe.setAttribute("tabindex", "-1")
		iframe.style.cssText = `position:fixed;left:-10000px;top:0;width:${contentWidthMM}mm;height:10px;border:0;visibility:hidden;pointer-events:none;`

		let settled = false
		const finish = (mm) => {
			if (settled) return
			settled = true
			clearTimeout(watchdog)
			iframe.remove()
			resolve(mm)
		}

		// Never hold up a sale for measurement — fall back to a fixed page length.
		const watchdog = setTimeout(() => finish(0), 5000)

		iframe.onload = async () => {
			try {
				const frameDoc = iframe.contentDocument
				const frameWindow = iframe.contentWindow
				if (!frameDoc || !frameWindow) {
					finish(0)
					return
				}

				const pending = [...frameDoc.images]
					.filter((img) => !img.complete)
					.map(
						(img) =>
							new Promise((done) => {
								img.addEventListener("load", done, { once: true })
								img.addEventListener("error", done, { once: true })
							}),
					)
				if (frameDoc.fonts?.ready) pending.push(frameDoc.fonts.ready)
				await Promise.all(pending)

				const px = Math.max(
					frameDoc.documentElement?.scrollHeight || 0,
					frameDoc.body?.scrollHeight || 0,
				)
				// CSS px are 1/96in by definition, which is also how wkhtmltopdf
				// maps them onto the page.
				finish(px > 0 ? (px * 25.4) / 96 : 0)
			} catch (err) {
				log.warn("Could not measure receipt height:", err)
				finish(0)
			}
		}

		iframe.onerror = () => finish(0)
		iframe.srcdoc = fullHTML
		document.body.appendChild(iframe)
	})
}

/**
 * Resolve print format & letterhead from a POS Profile.
 * Returns defaults when the profile lookup fails so callers always get a value.
 *
 * `preset` lets a caller that already holds the POS Profile (the sale screen has
 * it in `shiftStore.currentProfile`) supply the two fields directly, so a sale
 * does not spend an HTTP round trip re-reading them from the server. Callers
 * without a loaded profile pass nothing and fall through to the fetch below.
 */
async function resolvePrintSettings(
	posProfile,
	printFormat,
	letterhead,
	preset = null,
) {
	if (printFormat) return { printFormat, letterhead }

	if (preset?.printFormat) {
		return {
			printFormat: preset.printFormat,
			letterhead: letterhead || preset.letterhead || null,
		}
	}

	if (posProfile) {
		try {
			const doc = await call("frappe.client.get", {
				doctype: "POS Profile",
				name: posProfile,
			})
			if (doc) {
				return {
					printFormat: doc.print_format || DEFAULT_PRINT_FORMAT,
					letterhead: letterhead || doc.letter_head || null,
				}
			}
		} catch (err) {
			log.warn("Could not fetch POS Profile print settings:", err)
		}
	}

	return { printFormat: DEFAULT_PRINT_FORMAT, letterhead }
}

// ============================================================================
// Browser printing (renders server print HTML in a hidden iframe)
// ============================================================================

/**
 * Print an HTML document without opening a visible browser window.
 *
 * The receipt is rendered into an off-screen, same-origin iframe and printed
 * from there, so the cashier never sees an extra `about:blank` tab. The browser
 * itself still owns the print dialog: when Chrome runs with `--kiosk-printing`
 * this prints straight to the default printer with no dialog at all, otherwise
 * the OS/Chrome preview appears over the POS instead of in a popup window.
 * For fully driverless silent printing use the QZ Tray path below.
 *
 * @param {string} fullHTML complete HTML document to print
 * @returns {Promise<boolean>} resolves once printing finished (or timed out)
 */
function printHTMLInHiddenIframe(fullHTML) {
	return new Promise((resolve, reject) => {
		if (typeof document === "undefined") {
			reject(new Error("No document available for printing"))
			return
		}

		const iframe = document.createElement("iframe")
		iframe.setAttribute("aria-hidden", "true")
		iframe.setAttribute("tabindex", "-1")
		iframe.style.cssText =
			"position:fixed;right:0;bottom:0;width:0;height:0;border:0;opacity:0;pointer-events:none;"

		let settled = false
		const finish = (fn, value) => {
			if (settled) return
			settled = true
			clearTimeout(watchdog)
			// Keep the iframe alive briefly — removing it while the print job is
			// still spooling cancels the job in some browsers.
			setTimeout(() => iframe.remove(), 1000)
			fn(value)
		}

		// Safety net: some browsers never fire `afterprint` (e.g. the user leaves
		// the dialog open). Resolve anyway so the caller is not blocked forever.
		const watchdog = setTimeout(() => finish(resolve, true), 60000)

		iframe.onload = () => {
			const frameWindow = iframe.contentWindow
			if (!frameWindow) {
				finish(reject, new Error("Print iframe has no content window"))
				return
			}

			frameWindow.onafterprint = () => finish(resolve, true)

			// Give fonts/images a tick to settle before handing off to the printer.
			setTimeout(() => {
				try {
					frameWindow.focus()
					frameWindow.print()
				} catch (err) {
					finish(reject, err)
				}
			}, 150)
		}

		iframe.onerror = () =>
			finish(reject, new Error("Failed to load print iframe"))

		iframe.srcdoc = fullHTML
		document.body.appendChild(iframe)
	})
}

/**
 * Fetch server-rendered print HTML/style for the invoice and print it from a
 * hidden iframe — no popup window, no manual click.
 * Falls back to the hardcoded receipt template if the server render fails.
 */
export async function printInvoice(
	invoiceData,
	printFormat = null,
	letterhead = null,
) {
	try {
		if (!invoiceData?.name) throw new Error("Invalid invoice data")

		const { html, style } = await fetchPrintHTML(invoiceData.name, {
			printFormat: printFormat || DEFAULT_PRINT_FORMAT,
			letterhead,
			// noLetterhead: letterhead ? 0 : 1,
		})

		const fullHTML = `<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>${style}</style></head>
<body>${html}</body>
</html>`

		await printHTMLInHiddenIframe(fullHTML)
		return true
	} catch (error) {
		log.error("Browser print failed:", error)
		return printInvoiceCustom(invoiceData)
	}
}

/**
 * Fetch an invoice by name, resolve its POS Profile print settings,
 * then open the browser print window.
 */
export async function printInvoiceByName(
	invoiceName,
	printFormat = null,
	letterhead = null,
) {
	const invoiceDoc = await call("ecs_posnext.api.invoices.get_invoice", {
		invoice_name: invoiceName,
	})
	if (!invoiceDoc) throw new Error("Invoice not found")

	const settings = await resolvePrintSettings(
		invoiceDoc.pos_profile,
		printFormat,
		letterhead,
	)
	return printInvoice(invoiceDoc, settings.printFormat, settings.letterhead)
}

// ============================================================================
// Silent printing (QZ Tray — no browser dialog)
// ============================================================================

/**
 * Render the invoice to a receipt-sized PDF on the server and send that to the
 * thermal printer via QZ Tray.
 *
 * The PDF detour is what fixes Arabic: wkhtmltopdf shapes and reorders RTL text
 * the way a browser does, while QZ Tray's own HTML renderer prints Arabic
 * letters unjoined and in the wrong order. QZ now only rasterizes a finished
 * page, so the silent receipt matches what the browser print path produces.
 *
 * The page is the roll width configured for this till (80mm by default) and is
 * cut to the measured height of the receipt, so nothing is scaled and no blank
 * tail is fed before the cut.
 *
 * @param {string} invoiceName
 * @param {string|null} [printFormat]
 * @param {string|null} [printerName]
 * @param {Object} [options]
 * @param {string|null} [options.letterhead] - letterhead to render (none by default)
 * @param {number|null} [options.width] - roll width in mm; per-till setting by default
 */
export async function silentPrintInvoice(
	invoiceName,
	printFormat = null,
	printerName = null,
	options = {},
) {
	const format = printFormat || DEFAULT_PRINT_FORMAT
	const letterhead = options.letterhead || null
	const pageWidth = options.width || getPaperWidth()
	const contentWidth = Math.max(pageWidth - 2 * RECEIPT_SIDE_MARGIN_MM, 20)

	// Measure against the same HTML the PDF will be built from, so the page
	// length matches this receipt rather than a worst-case guess.
	let pageHeight = RECEIPT_FALLBACK_HEIGHT_MM
	try {
		const { html, style } = await fetchPrintHTML(invoiceName, {
			printFormat: format,
			letterhead,
			noLetterhead: letterhead ? 0 : 1,
			// Ask for the images already inlined as data URIs. The measurement
			// iframe below waits for every image to load, and pulling the logo and
			// QR over the till's network just to work out a page height was the
			// slowest and least predictable part of printing a receipt.
			inlineAssets: 1,
		})
		const measured = await measureReceiptHeightMM(
			`<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>${style}</style></head>
<body>${html}</body>
</html>`,
			contentWidth,
		)
		if (measured > 0) pageHeight = Math.ceil(measured + RECEIPT_TAIL_MM)
	} catch (err) {
		log.warn(
			"Receipt height measurement failed, using fallback page length:",
			err,
		)
	}

	const pdf = await fetchPrintPDF(invoiceName, {
		printFormat: format,
		letterhead,
		noLetterhead: letterhead ? 0 : 1,
		pageWidth,
		pageHeight,
	})

	await qzPrintPDF(pdf.content, printerName, {
		width: pdf.page_width || pageWidth,
		height: pdf.page_height || pageHeight,
	})
	log.info(
		`Silent print sent for ${invoiceName} (${pageWidth}×${pageHeight}mm)`,
	)
	return true
}

/**
 * Try silent print, fall back to browser print on failure.
 * silentPrintInvoice → qzPrintPDF → connect() handles auto-reconnect
 * internally, so no separate connection logic is needed here.
 *
 * When the silent path fails the caller gets `reason` — the browser print
 * dialog reappearing is otherwise indistinguishable from silent print being
 * switched off, which makes a misconfigured till hard to spot on the floor.
 *
 * @returns {Promise<{method: "silent"|"browser", success: boolean, reason?: string}>}
 */
export async function printWithSilentFallback(
	invoiceData,
	printFormat = null,
	options = {},
) {
	const invoiceName = invoiceData?.name
	if (!invoiceName) throw new Error("Invalid invoice data — missing name")

	const settings = await resolvePrintSettings(
		options.posProfile,
		printFormat,
		options.letterhead,
	)

	let reason
	try {
		await silentPrintInvoice(invoiceName, settings.printFormat, null, {
			letterhead: settings.letterhead,
		})
		return { method: "silent", success: true }
	} catch (err) {
		reason = err?.message || String(err)
		log.warn("Silent print failed, falling back to browser:", reason)
	}

	try {
		await printInvoiceByName(invoiceName, printFormat)
		return { method: "browser", success: true, reason }
	} catch (err) {
		log.error("Browser print fallback also failed:", err)
		return { method: "browser", success: false, reason }
	}
}

// ============================================================================
// PDF download (used when no printer can be reached)
// ============================================================================

/**
 * Fetch the invoice as a server-rendered PDF and save it to the browser's
 * download location.
 *
 * This is the no-printer path for auto-print: the cashier still ends up with a
 * receipt file they can print or file later, and crucially no dialog appears and
 * nothing has to be clicked.
 *
 * @param {string} invoiceName
 * @param {string|null} [printFormat]
 * @param {string|null} [letterhead]
 * @returns {Promise<string>} the downloaded filename
 */
export async function downloadInvoicePDF(
	invoiceName,
	printFormat = null,
	letterhead = null,
) {
	if (!invoiceName) throw new Error("Invalid invoice name")

	// No page_width: this copy is A4, since it gets opened and printed on
	// whatever ordinary printer the branch has, not on the missing roll printer.
	const payload = await fetchPrintPDF(invoiceName, {
		printFormat,
		letterhead,
		noLetterhead: letterhead ? 0 : 1,
	})

	const content = payload.content
	const filename = payload.filename || `${invoiceName}.pdf`

	// Decode to a Blob rather than using a data: href — receipt PDFs comfortably
	// exceed the URL length limit that a data: URI download would hit.
	const binary = atob(content)
	const bytes = new Uint8Array(binary.length)
	for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)

	const url = URL.createObjectURL(
		new Blob([bytes], { type: "application/pdf" }),
	)
	const link = document.createElement("a")
	link.href = url
	link.download = filename
	link.style.display = "none"
	document.body.appendChild(link)
	link.click()

	// Revoke late — revoking straight away cancels the download in some browsers.
	setTimeout(() => {
		link.remove()
		URL.revokeObjectURL(url)
	}, 10000)

	log.info(`Invoice ${invoiceName} saved as ${filename}`)
	return filename
}

// ============================================================================
// Fully automatic printing (no dialog, no clicks)
// ============================================================================

/**
 * Print a just-created invoice with zero cashier interaction.
 *
 * 1. Detect a physical printer and print silently through QZ Tray.
 * 2. If no printer can be reached, download the receipt as a PDF instead.
 *
 * Deliberately never falls through to the browser print dialog: that dialog
 * requires someone to click Print, which is exactly what auto-print exists to
 * avoid. Manual print buttons still use `printInvoiceByName` and keep the dialog.
 *
 * @param {{name: string}} invoiceData
 * @param {string|null} [printFormat]
 * @param {Object} [options]
 * @param {string|null} [options.posProfile] - profile to take print format/letterhead from
 * @param {{printFormat: string, letterhead: string|null}|null} [options.printSettings]
 *   already-known print format/letterhead, to skip the POS Profile fetch
 * @param {Promise<string>|null} [options.printerPromise] - in-flight printer
 *   detection started before the invoice existed, to skip the QZ handshake here
 * @returns {Promise<{method: "silent"|"download", success: boolean, printer?: string, filename?: string, reason?: string}>}
 */
export async function autoPrintInvoice(
	invoiceData,
	printFormat = null,
	options = {},
) {
	const invoiceName = invoiceData?.name
	if (!invoiceName) throw new Error("Invalid invoice data — missing name")

	// Same format and letterhead the manual print button uses — the receipt a
	// customer is handed should not depend on which button produced it.
	const settings = await resolvePrintSettings(
		options.posProfile,
		printFormat,
		options.letterhead,
		options.printSettings,
	)

	let reason
	try {
		// Printer detection needs nothing from the invoice, so the sale screen
		// starts it before submitting and hands us the promise — the QZ connect
		// and signing handshake then costs nothing on this clock. Every other
		// caller passes nothing and detection happens here as before.
		const printer = options.printerPromise
			? await options.printerPromise
			: await resolvePrinter()
		if (!printer) throw new Error("No printer found on this machine")

		await silentPrintInvoice(invoiceName, settings.printFormat, printer, {
			letterhead: settings.letterhead,
		})
		return { method: "silent", success: true, printer }
	} catch (err) {
		reason = err?.message || String(err)
		log.warn("Silent print unavailable, saving receipt instead:", reason)
	}

	try {
		const filename = await downloadInvoicePDF(
			invoiceName,
			settings.printFormat,
			settings.letterhead,
		)
		return { method: "download", success: true, filename, reason }
	} catch (err) {
		const downloadReason = err?.message || String(err)
		log.error("PDF download fallback also failed:", downloadReason)
		return { method: "download", success: false, reason: downloadReason }
	}
}

// ============================================================================
// Hardcoded receipt fallback (used when the server print render fails)
// ============================================================================

/**
 * Last-resort receipt renderer. Builds a complete HTML document from the
 * invoice data and prints it from a hidden iframe. Only triggered when the
 * server-rendered print HTML request fails.
 */
export function printInvoiceCustom(invoiceData) {
	const printContent = `
		<!DOCTYPE html>
		<html>
		<head>
			<meta charset="UTF-8">
			<title>${__("Invoice - {0}", [invoiceData.name])}</title>
			<style>
				* { margin: 0; padding: 0; box-sizing: border-box; }
				body {
					font-family: 'Courier New', monospace;
					padding: 10px; width: 80mm; margin: 0; max-width: 80mm;
					font-weight: bold; color: black;
				}
				.receipt { width: 100%; }
				.header { text-align: center; margin-bottom: 20px; border-bottom: 2px dashed #000; padding-bottom: 10px; }
				.company-name { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
				.invoice-info { margin-bottom: 15px; font-size: 12px; }
				.invoice-info div { display: flex; justify-content: space-between; margin-bottom: 3px; }
				.partial-status { color: #000; font-weight: bold; margin-bottom: 5px; }
				.items-table { width: 100%; margin-bottom: 15px; border-top: 1px dashed #000; border-bottom: 1px dashed #000; padding: 10px 0; }
				.item-row { margin-bottom: 10px; font-size: 12px; }
				.item-name { font-weight: bold; margin-bottom: 3px; }
				.item-details { display: flex; justify-content: space-between; font-size: 11px; }
				.item-discount { display: flex; justify-content: space-between; font-size: 10px; margin-top: 2px; }
				.item-serials { font-size: 9px; margin-top: 3px; padding: 3px 5px; border: 1px dashed #000; border-radius: 2px; }
				.item-serials-label { font-weight: bold; margin-bottom: 2px; }
				.item-serials-list { word-break: break-all; }
				.totals { margin-top: 15px; border-top: 1px dashed #000; padding-top: 10px; }
				.total-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 12px; }
				.grand-total { font-size: 16px; font-weight: bold; border-top: 2px solid #000; padding-top: 10px; margin-top: 10px; }
				.payments { margin-top: 15px; border-top: 1px dashed #000; padding-top: 10px; }
				.payment-row { display: flex; justify-content: space-between; margin-bottom: 3px; font-size: 11px; }
				.total-paid { font-weight: bold; border-top: 1px solid #000; padding-top: 5px; margin-top: 5px; }
				.outstanding-row {
					display: flex; justify-content: space-between; font-size: 13px; font-weight: bold;
					border: 1px solid #000; padding: 8px; margin-top: 8px; border-radius: 4px;
				}
				.footer { text-align: center; margin-top: 20px; padding-top: 10px; border-top: 2px dashed #000; font-size: 11px; }
				@media print {
					@page { size: 80mm auto; margin: 0; }
					body { width: 80mm; padding: 5mm; margin: 0; }
					.no-print { display: none; }
				}
			</style>
		</head>
		<body>
			<div class="receipt">
				<div class="header">
					<div class="company-name">${invoiceData.company || "POS Next"}</div>
					<div style="font-size: 12px;">${__("TAX INVOICE")}</div>
				</div>

				<div class="invoice-info">
					<div><span>${__("Invoice #:")}</span><span><strong>${invoiceData.name}</strong></span></div>
					<div><span>${__("Date:")}</span><span>${new Date(invoiceData.posting_date || Date.now()).toLocaleString()}</span></div>
					${invoiceData.customer_name ? `<div><span>${__("Customer:")}</span><span>${invoiceData.customer_name}</span></div>` : ""}
					${invoiceData.sales_team && invoiceData.sales_team.length > 0 ? `<div><span>${__("Sales Person:")}</span><span>${invoiceData.sales_team.map((st) => st.sales_person).join(", ")}</span></div>` : ""}
					${invoiceData.status === "Partly Paid" || (invoiceData.outstanding_amount && invoiceData.outstanding_amount > 0 && invoiceData.outstanding_amount < invoiceData.grand_total) ? `<div class="partial-status"><span>${__("Status:")}</span><span>${__("PARTIAL PAYMENT")}</span></div>` : ""}
				</div>

				<div class="items-table">
					${invoiceData.items
						.map((item) => {
							const hasDiscount =
								(item.discount_percentage &&
									Number.parseFloat(item.discount_percentage) > 0) ||
								(item.discount_amount &&
									Number.parseFloat(item.discount_amount) > 0)
							const isFree = item.is_free_item
							const qty = item.quantity || item.qty
							const displayRate = item.price_list_rate || item.rate
							const subtotal = qty * displayRate
							return `
						<div class="item-row">
							<div class="item-name">${item.item_name || item.item_code} ${isFree ? __("(FREE)") : ""}</div>
							<div class="item-details">
								<span>${qty} × ${formatCurrency(displayRate)}</span>
								<span><strong>${formatCurrency(subtotal)}</strong></span>
							</div>
							${hasDiscount ? `<div class="item-discount"><span>Discount ${item.discount_percentage ? `(${Number(item.discount_percentage).toFixed(2)}%)` : ""}</span><span>-${formatCurrency(item.discount_amount || 0)}</span></div>` : ""}
							${item.serial_no ? `<div class="item-serials"><div class="item-serials-label">${__("Serial No:")}</div><div class="item-serials-list">${item.serial_no.replace(/\n/g, ", ")}</div></div>` : ""}
						</div>`
						})
						.join("")}
				</div>

				<div class="totals">
					${
						invoiceData.total_taxes_and_charges &&
						invoiceData.total_taxes_and_charges > 0
							? `
					<div class="total-row"><span>${__("Subtotal:")}</span><span>${formatCurrency((invoiceData.grand_total || 0) - (invoiceData.total_taxes_and_charges || 0))}</span></div>
					<div class="total-row"><span>${__("Tax:")}</span><span>${formatCurrency(invoiceData.total_taxes_and_charges)}</span></div>`
							: ""
					}
					${
						invoiceData.discount_amount
							? `
					<div class="total-row" style="color: #28a745;"><span>Additional Discount${invoiceData.additional_discount_percentage ? ` (${Number(invoiceData.additional_discount_percentage).toFixed(1)}%)` : ""}:</span><span>-${formatCurrency(Math.abs(invoiceData.discount_amount))}</span></div>`
							: ""
					}
					<div class="total-row grand-total"><span>${__("TOTAL:")}</span><span>${formatCurrency(invoiceData.grand_total)}</span></div>
				</div>

				${
					invoiceData.payments && invoiceData.payments.length > 0
						? `
				<div class="payments">
					<div style="font-weight: bold; margin-bottom: 5px; font-size: 12px;">${__("Payments:")}</div>
					${invoiceData.payments.map((p) => `<div class="payment-row"><span>${p.mode_of_payment}:</span><span>${formatCurrency(p.amount)}</span></div>`).join("")}
					<div class="payment-row total-paid"><span>${__("Total Paid:")}</span><span>${formatCurrency(invoiceData.paid_amount || 0)}</span></div>
					${invoiceData.change_amount && invoiceData.change_amount > 0 ? `<div class="payment-row" style="font-weight: bold; margin-top: 5px;"><span>${__("Change:")}</span><span>${formatCurrency(invoiceData.change_amount)}</span></div>` : ""}
					${invoiceData.outstanding_amount && invoiceData.outstanding_amount > 0 ? `<div class="outstanding-row"><span>${__("BALANCE DUE:")}</span><span>${formatCurrency(invoiceData.outstanding_amount)}</span></div>` : ""}
				</div>`
						: ""
				}

				<div class="footer">
					<div style="margin-bottom: 5px;">${__("Thank you for your business!")}</div>
					<div style="font-size: 10px;">Powered by <a href="https://nexus.brainwise.me" target="_blank" style="color: #3b82f6; text-decoration: none; font-weight: 600;">BrainWise</a></div>
				</div>
			</div>
		</body>
		</html>`

	return printHTMLInHiddenIframe(printContent)
		.then(() => true)
		.catch((error) => {
			log.error("Fallback receipt print failed:", error)
			return false
		})
}
