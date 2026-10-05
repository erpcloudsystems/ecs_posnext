// Copyright (c) 2026, BrainWise and contributors
// For license information, please see license.txt

frappe.ui.form.on("Spot Check", {
	refresh(frm) {
		frm.disable_save();
	},

	get_data(frm) {
		if (!frm.doc.pos_profile || !frm.doc.date) {
			frappe.msgprint(__("Please select POS Profile and Date"));
			return;
		}
		frm.call({
			doc: frm.doc,
			method: "get_data",
			freeze: true,
			freeze_message: __("Fetching shifts..."),
			callback() {
				frm.refresh_fields();
				if (!frm.doc.shifts?.length) {
					frappe.show_alert({ message: __("No shifts found for this date"), indicator: "orange" });
				}
			},
		});
	},
});
