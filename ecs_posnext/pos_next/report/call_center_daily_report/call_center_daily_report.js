// Default window = the current business day, which runs 9:00 AM to 9:00 AM the next day.
// Before 9 AM we are still inside yesterday's business day.
function ccd_business_day_window() {
	const now = frappe.datetime.now_datetime(); // "YYYY-MM-DD HH:mm:ss"
	const hour = parseInt(now.slice(11, 13), 10);
	const today = frappe.datetime.get_today();
	if (hour < 9) {
		return { from: frappe.datetime.add_days(today, -1) + " 09:00:00", to: today + " 09:00:00" };
	}
	return { from: today + " 09:00:00", to: frappe.datetime.add_days(today, 1) + " 09:00:00" };
}

const _ccd_win = ccd_business_day_window();

frappe.query_reports["Call Center Daily Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date/Time"),
			fieldtype: "Datetime",
			default: _ccd_win.from,
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date/Time"),
			fieldtype: "Datetime",
			default: _ccd_win.to,
			reqd: 1,
		},
		{
			fieldname: "pos_profile",
			label: __("POS Profile"),
			fieldtype: "Link",
			options: "POS Profile",
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
			options: ["", "Delivery", "Talabat", "Pickup", "Dine In"].join("\n"),
		},
	],
};
