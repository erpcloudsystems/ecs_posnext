frappe.ui.form.on("Sales Order", {
	before_cancel(frm) {
		if (frm.doc.docstatus !== 1) return;

		return new Promise((resolve, reject) => {
			let finished = false;
			const dialog = new frappe.ui.Dialog({
				title: __("Cancellation Details"),
				fields: [
					{
						fieldname: "wastage_status",
						label: __("Status"),
						fieldtype: "Select",
						options: ["Wastage", "Not Wastage"],
						reqd: 1,
						default: frm.doc.posa_cancellation_status || "Not Wastage",
					},
					{
						fieldname: "client_phone",
						label: __("Client Phone Number"),
						fieldtype: "Data",
						reqd: 1,
						default: frm.doc.posa_cancellation_phone || "",
					},
				],
				primary_action_label: __("Continue Cancel"),
				primary_action: (values) => {
					frm.set_value("posa_cancellation_status", values.wastage_status);
					frm.set_value("posa_cancellation_phone", values.client_phone);
					dialog.hide();
					finished = true;
					resolve();
				},
			});

			dialog.set_secondary_action_label(__("Abort"));
			dialog.set_secondary_action(() => {
				dialog.hide();
				finished = true;
				reject();
			});

			dialog.$wrapper.on("hidden.bs.modal", () => {
				if (!finished) {
					reject();
				}
			});

			dialog.show();
		});
	},
});
