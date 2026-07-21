// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Cashier Shift", {
	refresh(frm) {
		if (frm.is_new()) return;

		// If a closing already exists, offer to jump straight to it.
		if (frm.doc.cashier_shift_closing) {
			frm.add_custom_button(__("Go to Closing"), () => {
				frappe.set_route("Form", "POS Cashier Shift Closing", frm.doc.cashier_shift_closing);
			});
		}

		// Close Shift — only while the shift is Open.
		if (frm.doc.status === "Open") {
			frm.add_custom_button(__("Close Shift"), () => {
				frappe.call({
					method: "ecs_posnext.api.cashier_shift.prepare_cashier_shift_closing",
					args: { pos_cashier_shift: frm.doc.name },
					freeze: true,
					freeze_message: __("Opening cashier shift closing..."),
					callback: (r) => {
						if (r.message && r.message.name) {
							// Redirect to the closing (pos_cashier_shift is set, the rest fetch in).
							frappe.set_route("Form", "POS Cashier Shift Closing", r.message.name);
						}
					},
				});
			}).addClass("btn-primary");
		}
	},
});
