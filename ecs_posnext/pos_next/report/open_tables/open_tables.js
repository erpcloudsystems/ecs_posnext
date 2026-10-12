// Copyright (c) 2026, BrainWise and contributors
// For license information, please see license.txt

frappe.query_reports["Open Tables"] = {
	filters: [
		{
			fieldname: "pos_profile",
			label: __("POS Profile"),
			fieldtype: "Link",
			options: "POS Profile",
		},
		{
			fieldname: "idle_state",
			label: __("Status"),
			fieldtype: "Select",
			options: [
				{ value: "", label: __("All") },
				{ value: "late", label: __("Late") },
				{ value: "warning", label: __("Waiting") },
				{ value: "ok", label: __("OK") },
			],
		},
		{
			fieldname: "only_without_order",
			label: __("Nothing ordered yet"),
			fieldtype: "Check",
			default: 0,
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Colour the two columns that carry the warning, so a long-idle table is
		// visible at a glance rather than needing the numbers read.
		if (data && (column.fieldname === "status_indicator" || column.fieldname === "idle_minutes")) {
			const colors = { red: "#ef4444", orange: "#f59e0b", green: "#22c55e" };
			const color = colors[data.indicator];
			if (color) {
				value = `<span style="color:${color};font-weight:600">${value}</span>`;
			}
		}

		return value;
	},

	onload(report) {
		// The floor changes constantly; a manager leaves this open on a screen.
		report.page.add_inner_button(__("Auto Refresh"), () => {
			if (report.__autoRefresh) {
				clearInterval(report.__autoRefresh);
				report.__autoRefresh = null;
				frappe.show_alert({ message: __("Auto refresh off"), indicator: "orange" });
				return;
			}
			report.__autoRefresh = setInterval(() => report.refresh(), 30000);
			frappe.show_alert({ message: __("Auto refresh on (30s)"), indicator: "green" });
		});
	},
};
