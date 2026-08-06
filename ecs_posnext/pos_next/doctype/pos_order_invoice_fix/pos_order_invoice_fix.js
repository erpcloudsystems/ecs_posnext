// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Order Invoice Fix", {
	import_orders(frm) {
		if (!frm.doc.attach_file) {
			frappe.throw(__("Please upload an Excel file first."));
		}

		frm.save().then(() => {
			frappe.show_alert(__("Importing orders..."));
			frm.call("import_orders").then((r) => {
				frm.reload_doc();
				if (r.message) frappe.msgprint(r.message);
			});
		});
	},

	create_invoices(frm) {
		const pending = (frm.doc.orders || []).filter((r) => r.status === "Pending").length;
		if (!pending) {
			frappe.msgprint(__("There are no Pending rows to create invoices for."));
			return;
		}

		frappe.confirm(
			__("This will create {0} Sales Invoice(s) as drafts from the Pending rows below. Continue?", [
				pending,
			]),
			() => {
				frappe.show_alert(__("Creating invoices..."));
				frm.call("create_invoices").then((r) => {
					frm.reload_doc();
					if (r.message) frappe.msgprint(r.message);
				});
			}
		);
	},

	submit_invoices(frm) {
		const ready = (frm.doc.orders || []).filter((r) => r.status === "Invoice Created").length;
		if (!ready) {
			frappe.msgprint(__("There are no rows with a draft Invoice Created to submit."));
			return;
		}

		frappe.confirm(
			__(
				"This will submit {0} Sales Invoice(s) and mark them as paid. This cannot be undone. Continue?",
				[ready]
			),
			() => {
				frappe.show_alert(__("Submitting invoices..."));
				frm.call("submit_invoices").then((r) => {
					frm.reload_doc();
					if (r.message) frappe.msgprint(r.message);
				});
			}
		);
	},
});
