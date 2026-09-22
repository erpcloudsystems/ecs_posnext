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

		if (frm.doc.status === "Closed") {
			_render_cash_custody(frm);
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

// ----------------------------------------------------------------------
// Cash custody: drawer -> branch safe -> master cash
// ----------------------------------------------------------------------
const CASH_GROUP = "Cash Transfer";

function _render_cash_custody(frm) {
	frappe.call({
		method: "ecs_posnext.api.cash_transfer.get_cash_custody_state",
		args: { business_day: frm.doc.name },
		callback: (r) => {
			const state = r.message;
			if (!state || !state.can_transfer) return;

			if (!state.drawer_transfer) {
				frm.add_custom_button(__("Transfer Drawer to Branch Safe"), () => {
					_confirm_drawer_transfer(frm, state);
				}, __(CASH_GROUP));
			} else if (!state.safe_transfer) {
				frm.add_custom_button(__("Transfer Branch Safe to Master Cash"), () => {
					_confirm_master_transfer(frm, state);
				}, __(CASH_GROUP));
			}

			_show_custody_indicators(frm, state);
		},
	});
}

function _show_custody_indicators(frm, state) {
	const money = (v) => frappe.format(v, { fieldtype: "Currency", options: state.currency });
	if (state.drawer_transfer) {
		frm.dashboard.add_indicator(__("Drawer handed to branch safe"), "green");
	} else {
		frm.dashboard.add_indicator(__("Drawer not handed over: {0}", [money(state.figures.counted)]), "orange");
	}
	if (state.safe_transfer) {
		frm.dashboard.add_indicator(__("Deposited to master cash"), "blue");
	}
}

function _confirm_drawer_transfer(frm, state) {
	const money = (v) => frappe.format(v, { fieldtype: "Currency", options: state.currency });
	const variance = state.figures.variance;
	const variance_label = variance < 0 ? __("Shortage") : __("Overage");

	const rows = [
		[__("Expected Cash"), money(state.figures.expected)],
		[__("Counted Cash"), money(state.figures.counted)],
	];
	if (variance) rows.push([variance_label, money(Math.abs(variance))]);
	rows.push([__("From"), state.accounts.drawer || __("Not configured")]);
	rows.push([__("To"), state.accounts.branch_safe || __("Not configured")]);

	const d = new frappe.ui.Dialog({
		title: __("Transfer Drawer to Branch Safe"),
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "summary",
				options: `<table class="table table-bordered">${rows
					.map(([k, v]) => `<tr><td class="text-muted">${k}</td><td class="text-right">${v}</td></tr>`)
					.join("")}</table>`,
			},
			{ fieldtype: "Small Text", fieldname: "remarks", label: __("Remarks") },
		],
		primary_action_label: __("Transfer {0}", [money(state.figures.counted)]),
		primary_action: (values) => {
			d.hide();
			frappe.call({
				method: "ecs_posnext.api.cash_transfer.transfer_drawer_to_safe",
				args: { business_day: frm.doc.name, remarks: values.remarks || null },
				freeze: true,
				freeze_message: __("Transferring cash..."),
				callback: (r) => {
					frm.reload_doc();
					if (r.message) {
						frappe.show_alert({
							message: __("Cash transfer {0} created.", [r.message.name]),
							indicator: "green",
						});
					}
				},
			});
		},
	});
	d.show();
}

function _confirm_master_transfer(frm, state) {
	const money = (v) => frappe.format(v, { fieldtype: "Currency", options: state.currency });
	const d = new frappe.ui.Dialog({
		title: __("Transfer Branch Safe to Master Cash"),
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "summary",
				options: `<p class="text-muted">${__("Branch safe balance: {0}", [
					money(state.branch_safe_balance),
				])}<br>${__("From")}: ${state.accounts.branch_safe || __("Not configured")}<br>${__("To")}: ${
					state.accounts.master || __("Not configured")
				}</p>`,
			},
			{
				fieldtype: "Currency",
				fieldname: "amount",
				label: __("Amount"),
				reqd: 1,
				default: state.figures.counted,
			},
			{ fieldtype: "Small Text", fieldname: "remarks", label: __("Remarks") },
		],
		primary_action_label: __("Transfer"),
		primary_action: (values) => {
			d.hide();
			frappe.call({
				method: "ecs_posnext.api.cash_transfer.transfer_safe_to_master",
				args: {
					business_day: frm.doc.name,
					amount: values.amount,
					remarks: values.remarks || null,
				},
				freeze: true,
				freeze_message: __("Transferring cash..."),
				callback: (r) => {
					frm.reload_doc();
					if (r.message) {
						frappe.show_alert({
							message: __("Cash transfer {0} created.", [r.message.name]),
							indicator: "green",
						});
					}
				},
			});
		},
	});
	d.show();
}
