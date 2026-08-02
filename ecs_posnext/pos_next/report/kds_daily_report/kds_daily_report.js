frappe.query_reports["KDS Daily Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
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
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "order_type",
			label: __("Order Type"),
			fieldtype: "Select",
			options: ["", "Dine In", "Pickup", "Delivery", "Talabat"].join("\n"),
		},
	],
};
