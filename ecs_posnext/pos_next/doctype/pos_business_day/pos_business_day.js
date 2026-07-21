// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Business Day", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Refresh Summary"), () => {
			frappe.call({
				method: "ecs_posnext.pos_next.doctype.pos_business_day.pos_business_day.refresh_business_day_summary",
				args: { business_day: frm.doc.name },
				freeze: true,
				freeze_message: __("Recalculating..."),
				callback: () => frm.reload_doc(),
			});
		});

		if (frm.doc.status !== "Closed") {
			frm.add_custom_button(__("Validate Closing"), () => {
				frappe.call({
					method: "ecs_posnext.api.business_day_closing.validate_business_day_closable",
					args: { business_day: frm.doc.name },
					freeze: true,
					freeze_message: __("Checking..."),
					callback: (r) => {
						frm.reload_doc();
						const res = r.message || {};
						if (res.closable) {
							frappe.msgprint({
								title: __("Ready to Close"),
								message: __("No blocking issues found. The Business Day can be closed."),
								indicator: "green",
							});
						} else {
							frappe.msgprint({
								title: __("Closing Issues"),
								message: __("{0} issue(s) are blocking the close. See the Closing Issues table.", [res.count]),
								indicator: "red",
							});
						}
					},
				});
			});

			frm.add_custom_button(__("Close Business Day"), () => {
				frappe.confirm(__("Close this Business Day? This is only allowed when there are no blocking issues."), () => {
					_close(frm, 0);
				});
			}).addClass("btn-primary");

			const roles = frappe.user_roles || [];
			if (roles.includes("POSNext Operations Manager") || roles.includes("System Manager")) {
				frm.add_custom_button(__("Override Close"), () => {
					frappe.prompt(
						[{ fieldname: "reason", fieldtype: "Small Text", label: __("Override Reason"), reqd: 1 }],
						(values) => _close(frm, 1, values.reason),
						__("Override & Force Close"),
						__("Force Close")
					);
				}, __("Actions"));
			}
		}

		if (frm.doc.status === "Closed") {
			const roles = frappe.user_roles || [];
			if (roles.some((r) => ["POSNext Branch Manager", "POSNext Operations Manager", "System Manager"].includes(r))) {
				frm.add_custom_button(__("Reopen Business Day"), () => {
					frappe.prompt(
						[{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason for reopening"), reqd: 1 }],
						(v) => {
							frappe.call({
								method: "ecs_posnext.api.business_day_closing.reopen_business_day",
								args: { business_day: frm.doc.name, reason: v.reason },
								freeze: true,
								callback: () => frm.reload_doc(),
							});
						},
						__("Reopen Business Day"),
						__("Reopen")
					);
				}).addClass("btn-warning");
			}
		}

		if (frm.doc.closing_issues && frm.doc.closing_issues.length) {
			frm.dashboard.add_indicator(
				__("{0} Closing Issues", [frm.doc.closing_issues.length]),
				"red"
			);
		}
	},
});

function _close(frm, force, reason) {
	frappe.call({
		method: "ecs_posnext.api.business_day_closing.close_business_day",
		args: { business_day: frm.doc.name, force: force, reason: reason || null },
		freeze: true,
		freeze_message: __("Closing Business Day..."),
		callback: (r) => {
			frm.reload_doc();
			if (r.message && r.message.status === "Closed") {
				frappe.show_alert({ message: __("Business Day closed."), indicator: "green" });
			}
		},
	});
}
