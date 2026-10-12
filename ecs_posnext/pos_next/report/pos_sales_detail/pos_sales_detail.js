// Copyright (c) 2026, BrainWise and contributors
// For license information, please see license.txt

frappe.query_reports["POS Sales Detail"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
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
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			default: "Room + Item",
			options: [
				{ value: "Item", label: __("Item") },
				{ value: "Item Group", label: __("Item Group") },
				{ value: "Room", label: __("Room / Table") },
				{ value: "Shift", label: __("Shift") },
				{ value: "Item Group + Item", label: __("Item Group + Item") },
				{ value: "Room + Item", label: __("Room / Table + Item") },
				{ value: "Detail", label: __("Detail (one row per line)") },
			],
		},
		{
			fieldname: "pos_profile",
			label: __("POS Profile"),
			fieldtype: "Link",
			options: "POS Profile",
		},
		{
			fieldname: "pos_opening_shift",
			label: __("Shift"),
			fieldtype: "Link",
			options: "POS Opening Shift",
			// Narrowed to the chosen profile, so a long shift list stays usable
			get_query() {
				const filters = {};
				const pos_profile = frappe.query_report.get_filter_value("pos_profile");
				const company = frappe.query_report.get_filter_value("company");
				if (pos_profile) filters.pos_profile = pos_profile;
				if (company) filters.company = company;
				return { filters };
			},
		},
		{
			fieldname: "cashier",
			label: __("Cashier"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "room",
			label: __("Room"),
			fieldtype: "Link",
			options: "Room",
		},
		{
			fieldname: "pos_table",
			label: __("Table"),
			fieldtype: "Link",
			options: "Table",
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
		},
		{
			fieldname: "pos_sale_type",
			label: __("Sale Type"),
			fieldtype: "Select",
			options: ["", "Cash", "Loan", "Benefits"],
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// A sale with no room was not charged to a guest: it was served at a
		// table, and which table - Officer, Hospitality, table 6 - is the thing
		// worth reading. Only a sale with no table either was rung up straight at
		// the till. Both beat an empty cell the reader has to interpret.
		if (column.fieldname === "room" && data && !data.room) {
			const table = data.pos_table;
			value = `<span style="color:#9ca3af">${table ? __("At {0}", [table]) : __("Walk-in")}</span>`;
		}

		// The grouped column already carries the table, so only the till sales
		// need toning down.
		if (column.fieldname === "place" && data && data.place === __("Walk-in")) {
			value = `<span style="color:#9ca3af">${__("Walk-in")}</span>`;
		}

		// A handout was never paid for, so its money columns are empty rather
		// than zero. Say why, instead of leaving the reader to guess.
		const money = ["rate", "rate_with_tax", "amount", "tax_amount", "amount_with_tax",
			"avg_rate", "avg_rate_with_tax"];
		if (money.includes(column.fieldname) && data && data[column.fieldname] === null) {
			value = `<span style="color:#9ca3af">${__("No price")}</span>`;
		}

		// Sales rung up before the POS started stamping the shift on the order.
		// They are real sales, so they are counted, but nothing attributes them.
		if (column.fieldname === "shift" && data && !data.shift) {
			value = `<span style="color:#9ca3af">${__("No shift recorded")}</span>`;
		}

		return value;
	},
};
