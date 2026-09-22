// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Branch Expense", {
	refresh(frm) {
		frm.add_custom_button(__("Branch Expenses Page"), () => {
			frappe.set_route("pos-branch-expenses");
		});
	},
});
