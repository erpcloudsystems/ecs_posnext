// Copyright (c) 2026, BrainWise and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Report Settings", {
	refresh(frm) {
		// A disabled report cannot be run, so keep it out of the picker entirely
		frm.set_query("report", "reports", () => ({
			filters: {
				disabled: 0,
			},
		}));
	},
});
