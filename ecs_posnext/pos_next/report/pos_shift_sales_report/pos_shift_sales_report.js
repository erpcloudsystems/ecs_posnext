// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

frappe.query_reports["POS Shift Sales Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "pos_profile",
			label: __("POS Profile"),
			fieldtype: "Link",
			options: "POS Profile",
		},
		{
			fieldname: "pos_shift",
			label: __("POS Shift"),
			fieldtype: "Link",
			options: "POS Opening Shift",
		},
		{
			fieldname: "pos_business_day",
			label: __("POS Business Day"),
			fieldtype: "Link",
			options: "POS Business Day",
		},
		{
			fieldname: "pos_cashier_shift",
			label: __("POS Cashier Shift"),
			fieldtype: "Link",
			options: "POS Cashier Shift",
		},
	],
};
