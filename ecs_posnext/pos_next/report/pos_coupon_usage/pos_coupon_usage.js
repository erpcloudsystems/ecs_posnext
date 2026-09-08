// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

frappe.query_reports["POS Coupon Usage"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "coupon_code",
			label: __("Coupon Code"),
			fieldtype: "Data",
		},
		{
			fieldname: "coupon_type",
			label: __("Coupon Type"),
			fieldtype: "Select",
			options: ["", "Promotional", "Gift Card"],
		},
		{
			fieldname: "discount_type",
			label: __("Discount Type"),
			fieldtype: "Select",
			options: ["", "Percentage", "Amount", "Cashback and Point Loyalty"],
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "pos_profile",
			label: __("POS Profile"),
			fieldtype: "Link",
			options: "POS Profile",
		},
		{
			fieldname: "cashier",
			label: __("Cashier"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "include_cancelled",
			label: __("Include Cancelled Invoices"),
			fieldtype: "Check",
			default: 0,
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "status" && data && data.status === "Cancelled") {
			value = `<span style="color: var(--red-500)">${value}</span>`;
		}

		if (
			["coupon_points", "coupon_cashback"].includes(column.fieldname) &&
			data &&
			flt(data[column.fieldname]) > 0
		) {
			value = `<span style="color: var(--green-600)">${value}</span>`;
		}

		return value;
	},
};
