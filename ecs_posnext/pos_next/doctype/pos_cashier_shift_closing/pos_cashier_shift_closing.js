// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

const DENOMS = ["cash_200_egp", "cash_100_egp", "cash_50_egp", "cash_20_egp", "cash_10_egp", "cash_5_egp", "cash_1_egp"];

frappe.ui.form.on("POS Cashier Shift Closing", {
	refresh(frm) {
		// Blind close: keep the reconciliation collapsed until the drawer is counted.
		// "Counted" is the explicit flag — a 0 drawer is still a valid count.
		const counted = !!frm.doc.cash_counted;
		frm.toggle_display("section_reveal", counted);
		frm.toggle_display("section_reconciliation", counted);

		if (frm.doc.docstatus === 0 && frm.doc.difference_requires_approval && !frm.doc.approved_by) {
			const roles = frappe.user_roles || [];
			if (roles.some((r) => ["POSNext Branch Manager", "POSNext Operations Manager", "System Manager"].includes(r))) {
				frm.add_custom_button(__("Approve Difference"), () => {
					frappe.prompt(
						[{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 }],
						(v) => {
							frappe.call({
								method: "ecs_posnext.pos_next.doctype.pos_cashier_shift_closing.pos_cashier_shift_closing.approve_difference",
								args: { pos_cashier_shift_closing: frm.doc.name, reason: v.reason },
								callback: () => frm.reload_doc(),
							});
						},
						__("Approve Cash Difference"),
						__("Approve")
					);
				}).addClass("btn-warning");
			}
		}
	},
});

// Recompute the counted total live as denominations are entered.
DENOMS.forEach((f) => {
	frappe.ui.form.on("POS Cashier Shift Closing", f, (frm) => {
		const total =
			(frm.doc.cash_200_egp || 0) * 200 +
			(frm.doc.cash_100_egp || 0) * 100 +
			(frm.doc.cash_50_egp || 0) * 50 +
			(frm.doc.cash_20_egp || 0) * 20 +
			(frm.doc.cash_10_egp || 0) * 10 +
			(frm.doc.cash_5_egp || 0) * 5 +
			(frm.doc.cash_1_egp || 0) * 1;
		frm.set_value("actual_counted_cash", total);
		// Entering any denomination means the drawer is being counted.
		if (total > 0 && !frm.doc.cash_counted) frm.set_value("cash_counted", 1);
	});
});
