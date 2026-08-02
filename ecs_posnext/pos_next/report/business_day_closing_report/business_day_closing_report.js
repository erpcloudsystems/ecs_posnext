frappe.query_reports["Business Day Closing Report"] = {
	filters: [
		{
			fieldname: "business_day",
			label: __("Business Day"),
			fieldtype: "Link",
			options: "POS Business Day",
			reqd: 1,
		},
	],
	// Render the "Invoices" column (raw <a> HTML) as a clickable link, and highlight
	// unreconciled differences + "(Still Opened)" shifts.
	formatter(value, row, column, data, default_formatter) {
		if (column.fieldname === "invoices" && value) {
			return value; // already an <a> anchor
		}
		let formatted = default_formatter(value, row, column, data);
		if (column.fieldname === "difference" && flt(value) !== 0) {
			formatted = `<span style="color:${flt(value) < 0 ? "#c0392b" : "#b9770e"};font-weight:600">${formatted}</span>`;
		}
		if (column.fieldname === "note" && value === "(Still Opened)") {
			formatted = `<span style="color:#c0392b;font-weight:700">${formatted}</span>`;
		}
		if (column.fieldname === "item" && data && !data.expected && !data.count && !data.actual) {
			formatted = `<b>${formatted}</b>`;
		}
		return formatted;
	},
};
