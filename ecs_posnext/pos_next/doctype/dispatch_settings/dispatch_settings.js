frappe.ui.form.on("Dispatch Settings", {
	refresh(frm) {
		frm.set_intro(
			__("Configure accounts and defaults for the Dispatch module."),
			"blue"
		);
	},
});
