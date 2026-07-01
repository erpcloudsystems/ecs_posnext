// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Daily Operation Planning"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			hidden: !frappe.boot.doctype_layouts || !frappe.meta.has_field("Sales Invoice", "branch"),
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			reqd: 1,
			get_query: function() {
				return {
					filters: {
						is_group: 0,
						disabled: 0,
					}
				};
			}
		},
		{
			fieldname: "posting_date",
			label: __("Target Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
			description: __("Select a date to analyze consumption for that weekday"),
		},
		{
			fieldname: "weeks_count",
			label: __("Number of Weeks"),
			fieldtype: "Int",
			default: 4,
			description: __("Number of historical weeks to analyze"),
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "only_operation_items",
			label: __("Only Operation Items"),
			fieldtype: "Check",
			default: 1,
			description: __("Show only items marked for operation planning"),
		},
		{
			fieldname: "include_returns",
			label: __("Include Returns"),
			fieldtype: "Check",
			default: 0,
			description: __("Include return invoices in consumption calculation"),
		},
	],

	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname === "net_required_qty" && data) {
			if (flt(data.net_required_qty) > 0) {
				value = `<span style="color: red; font-weight: bold;">${value}</span>`;
			} else {
				value = `<span style="color: green;">${value}</span>`;
			}
		}
		
		if (column.fieldname === "current_stock_qty" && data) {
			if (flt(data.current_stock_qty) <= 0) {
				value = `<span style="color: orange;">${value}</span>`;
			}
		}
		
		if (column.fieldname === "required_packs" && data) {
			if (flt(data.required_packs) > 0) {
				value = `<span style="color: blue; font-weight: bold;">${value}</span>`;
			}
		}
		
		return value;
	},

	onload: function(report) {
		// Add refresh button
		report.page.add_inner_button(__("Refresh"), function() {
			report.refresh();
		});
	},
};
