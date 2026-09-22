// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Cash Transfer", {
	refresh(frm) {
		if (frm.doc.pos_business_day) {
			frm.add_custom_button(__("Business Day"), () => {
				frappe.set_route("Form", "POS Business Day", frm.doc.pos_business_day);
			});
		}
		if (frm.doc.variance) {
			frm.dashboard.add_indicator(
				__("{0}: {1}", [
					frm.doc.variance < 0 ? __("Shortage") : __("Overage"),
					format_currency(Math.abs(frm.doc.variance), frappe.boot.sysdefaults.currency),
				]),
				frm.doc.variance < 0 ? "red" : "orange"
			);
		}
	},
});
