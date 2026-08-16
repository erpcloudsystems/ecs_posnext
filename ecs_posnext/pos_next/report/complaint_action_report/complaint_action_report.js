frappe.query_reports["Complaint Action Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -7),
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
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: [
				"", "New", "Under Review", "Pending Approval", "Approved",
				"Rejected", "Coupon Issued", "Coupon Redeemed", "Closed",
			].join("\n"),
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "agent",
			label: __("Agent"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "pos_cashier_shift",
			label: __("Cashier Shift"),
			fieldtype: "Link",
			options: "POS Cashier Shift",
		},
		{
			fieldname: "pos_business_day",
			label: __("Business Day"),
			fieldtype: "Link",
			options: "POS Business Day",
		},
	],
};
