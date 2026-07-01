frappe.ui.form.on("Delivery Assignment", {
	refresh(frm) {
		const terminal = ["Delivered", "Returned", "Failed"];
		if (terminal.includes(frm.doc.status)) {
			frm.disable_save();
		}

		// Amount collected only editable when status = Delivered
		frm.set_df_property(
			"amount_collected",
			"read_only",
			frm.doc.status !== "Delivered" ? 1 : 0
		);

		// Show quick status buttons for dispatcher
		if (frm.doc.docstatus === 0 && !terminal.includes(frm.doc.status)) {
			const next_statuses = {
				Assigned: "Picked Up",
				"Picked Up": "Out for Delivery",
				"Out for Delivery": "Delivered",
			};
			const next = next_statuses[frm.doc.status];
			if (next) {
				frm.add_custom_button(__("Mark as {0}", [next]), () => {
					frm.set_value("status", next);
					frm.save();
				}, __("Update Status"));
			}

			if (!["Returned", "Failed"].includes(frm.doc.status)) {
				frm.add_custom_button(__("Mark as Returned"), () => {
					frm.set_value("status", "Returned");
					frm.save();
				}, __("Update Status"));
			}
		}
	},

	order_reference(frm) {
		if (frm.doc.order_reference && frm.doc.order_doctype === "Sales Invoice") {
			frappe.db.get_value("Sales Invoice", frm.doc.order_reference, [
				"customer", "outstanding_amount", "contact_mobile"
			], (r) => {
				if (r) {
					frm.set_value("customer", r.customer);
					if (!frm.doc.amount_to_collect) {
						frm.set_value("amount_to_collect", r.outstanding_amount);
					}
				}
			});
		}
	},
});
