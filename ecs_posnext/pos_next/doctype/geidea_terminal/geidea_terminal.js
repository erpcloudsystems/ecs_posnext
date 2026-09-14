// Copyright (c) 2026, BrainWise and contributors
// For license information, please see license.txt

frappe.ui.form.on("Geidea Terminal", {
	refresh(frm) {
		frm.set_intro(
			__(
				"The Geidea Web ECR Windows service must be installed and running on the cashier PC for this terminal to work.",
			),
			"blue",
		);
	},
});
