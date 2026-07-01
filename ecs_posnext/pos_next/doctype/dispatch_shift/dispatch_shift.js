frappe.ui.form.on("Dispatch Shift", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === "Open") {
			frm.add_custom_button(__("Close Shift"), () => {
				frappe.confirm(
					__("Close shift {0}? This will reconcile cash and post accounting entries.", [frm.docname]),
					() => {
						frm.call("close_shift").then(() => {
							frm.reload_doc();
						});
					}
				);
			}, __("Actions")).addClass("btn-warning");
		}

		if (frm.doc.status === "Closed") {
			frm.disable_save();
		}
	},

	dispatcher(frm) {
		if (!frm.doc.dispatcher) {
			frm.set_value("dispatcher", frappe.session.user);
		}
	},
});
