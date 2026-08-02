frappe.query_reports["My Action Report"] = {
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
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Approved", "Rejected", "Pending"].join("\n"),
		},
		{
			fieldname: "include_pending",
			label: __("Include Pending"),
			fieldtype: "Check",
			default: 0,
		},
	],
};
