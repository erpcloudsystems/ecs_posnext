frappe.pages["business-day-closing"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Business Day Closing"),
		single_column: true,
	});

	// --- Business Day selector + actions -------------------------------------
	const bd_field = page.add_field({
		fieldname: "business_day",
		label: __("Business Day"),
		fieldtype: "Link",
		options: "POS Business Day",
		reqd: 1,
		change() {
			load();
		},
	});
	page.set_primary_action(__("Refresh"), () => load(), "refresh");
	page.add_menu_item(__("Open Report"), () => {
		frappe.set_route("query-report", "Business Day Closing Report", {
			business_day: bd_field.get_value() || "",
		});
	});

	const $content = $('<div class="bdc-wrap" style="padding:12px 4px"></div>').appendTo(page.body);

	// Default to the most recent business day.
	frappe.db
		.get_list("POS Business Day", { fields: ["name"], order_by: "creation desc", limit: 1 })
		.then((r) => {
			if (r && r.length) bd_field.set_value(r[0].name);
		});

	const fmt = (v) => format_currency(flt(v));

	function load() {
		const bd = bd_field.get_value();
		if (!bd) {
			$content.html(empty(__("Select a Business Day to view its closing.")));
			return;
		}
		$content.html(loading());
		frappe.call({
			method: "frappe.desk.query_report.run",
			args: { report_name: "Business Day Closing Report", filters: { business_day: bd } },
			callback(r) {
				render((r.message && r.message.result) || [], bd);
			},
		});
	}

	function render(rows, bd) {
		// Split rows into: header/info, money metrics, count metrics, shift-status.
		const money = [];
		const counts = [];
		const shifts = [];
		let header = null,
			shiftInfo = null,
			inShiftSection = false;

		rows.forEach((row) => {
			const item = row.item || "";
			if (item.startsWith("Business Day ")) {
				header = row;
			} else if (item.startsWith("Shifts:")) {
				shiftInfo = row;
			} else if (item.indexOf("Shift Status Summary") !== -1) {
				inShiftSection = true;
			} else if (inShiftSection) {
				shifts.push(row);
			} else if (row.expected !== undefined && row.expected !== null) {
				money.push(row);
			} else if (row.count !== undefined && row.count !== null) {
				counts.push(row);
			}
		});

		let html = "";

		// Header strip
		html += `<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:14px">
			<div>
				<div style="font-size:18px;font-weight:700">${frappe.utils.escape_html(header ? header.item : bd)}</div>
				<div class="text-muted" style="font-size:12px">${header && header.note ? frappe.utils.escape_html(header.note) : ""}</div>
			</div>
			<div>${shiftInfo ? `<span class="indicator-pill blue">${frappe.utils.escape_html(shiftInfo.item)}</span>` : ""}</div>
		</div>`;

		// Count KPI cards
		if (counts.length) {
			html += `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:16px">`;
			counts.forEach((c) => {
				html += `<div style="border:1px solid var(--border-color);border-radius:10px;padding:12px 14px;background:var(--card-bg)">
					<div class="text-muted" style="font-size:11px;text-transform:uppercase;letter-spacing:.04em">${frappe.utils.escape_html(c.item)}</div>
					<div style="display:flex;align-items:baseline;justify-content:space-between;margin-top:4px">
						<div style="font-size:24px;font-weight:700">${cint(c.count)}</div>
						${c.invoices ? linkBtn(c.invoices) : ""}
					</div>
				</div>`;
			});
			html += `</div>`;
		}

		// Money table (Expected / Actual / Difference)
		html += `<div style="border:1px solid var(--border-color);border-radius:10px;overflow:hidden;margin-bottom:16px">
			<table class="table" style="margin:0">
			<thead><tr style="background:var(--subtle-fg,#f4f5f6)">
				<th style="padding:8px 12px">${__("Item")}</th>
				<th class="text-right" style="padding:8px 12px">${__("Expected")}</th>
				<th class="text-right" style="padding:8px 12px">${__("Actual")}</th>
				<th class="text-right" style="padding:8px 12px">${__("Difference")}</th>
				<th class="text-center" style="padding:8px 12px">${__("Invoices")}</th>
			</tr></thead><tbody>`;
		money.forEach((m) => {
			const diff = flt(m.difference);
			const dcolor = diff === 0 ? "var(--text-muted)" : diff < 0 ? "#c0392b" : "#b9770e";
			html += `<tr>
				<td style="padding:8px 12px">${frappe.utils.escape_html(m.item)}</td>
				<td class="text-right" style="padding:8px 12px">${fmt(m.expected)}</td>
				<td class="text-right" style="padding:8px 12px">${fmt(m.actual)}</td>
				<td class="text-right" style="padding:8px 12px;color:${dcolor};font-weight:600">${fmt(diff)}</td>
				<td class="text-center" style="padding:8px 12px">${m.invoices ? linkBtn(m.invoices) : ""}</td>
			</tr>`;
		});
		html += `</tbody></table></div>`;

		// Shift status
		if (shifts.length) {
			html += `<div style="font-weight:700;margin:6px 0 8px">${__("Shift Status")}</div>`;
			html += `<div style="display:flex;flex-direction:column;gap:6px">`;
			shifts.forEach((s) => {
				const open = (s.note || "").indexOf("Opened") !== -1;
				html += `<div style="display:flex;justify-content:space-between;align-items:center;border:1px solid var(--border-color);border-radius:8px;padding:8px 12px">
					<span>${frappe.utils.escape_html(s.item)}</span>
					<span class="indicator-pill ${open ? "red" : "green"}">${frappe.utils.escape_html(s.note || "")}</span>
				</div>`;
			});
			html += `</div>`;
		}

		$content.html(html);
	}

	function linkBtn(anchorHtml) {
		// The report returns an <a href="..."> anchor; render as a small button.
		const href = (anchorHtml.match(/href="([^"]+)"/) || [])[1];
		if (!href) return "";
		return `<a href="${href}" target="_blank" class="btn btn-xs btn-default">🔗 ${__("Review")}</a>`;
	}

	function empty(msg) {
		return `<div class="text-muted" style="text-align:center;padding:48px">${frappe.utils.escape_html(msg)}</div>`;
	}
	function loading() {
		return `<div class="text-muted" style="text-align:center;padding:48px">${__("Loading…")}</div>`;
	}
};
