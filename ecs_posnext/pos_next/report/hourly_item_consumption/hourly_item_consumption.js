// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Hourly Item Consumption"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
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
			label: __("التاريخ"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
			description: __("اختر تاريخ لتحليل الاستهلاك بالساعة لنفس اليوم من الأسبوع")
		},
		{
			fieldname: "weeks_count",
			label: __("عدد الأسابيع"),
			fieldtype: "Int",
			default: 4,
			description: __("عدد الأسابيع السابقة للتحليل")
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
	],

	formatter: function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		// Highlight total row
		if (data && data.item_name === __("Total")) {
			value = `<span style="font-weight: bold; background-color: #f0f0f0;">${value}</span>`;
		}
		
		// Highlight total column
		if (column.fieldname === "total_qty" && data) {
			if (flt(data.total_qty) > 0) {
				value = `<span style="color: blue; font-weight: bold;">${value}</span>`;
			}
		}
		
		// Highlight hours with high consumption
		if (column.fieldname && column.fieldname.startsWith("hour_") && data) {
			let qty = flt(data[column.fieldname]);
			if (qty > 0) {
				// Color intensity based on quantity
				let intensity = Math.min(qty / 10, 1);
				let red = Math.floor(255 * intensity);
				value = `<span style="color: rgb(${red}, 0, 0);">${value}</span>`;
			}
		}
		
		return value;
	},

	onload: function(report) {
		report.page.add_inner_button(__("Refresh"), function() {
			report.refresh();
		});
	},
};
