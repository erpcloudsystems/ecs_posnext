// Copyright (c) 2026, erpcloud.systems and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Closing Shift Daily Payment Update", {
	setup(frm) {
		frm.set_query("pos_closing_shift", () => {
			return {
				query:
					"ecs_posnext.pos_next.doctype.pos_closing_shift_daily_payment_update.pos_closing_shift_daily_payment_update.affected_closing_shift_query",
				filters: { branch: frm.doc.branch },
			};
		});
	},

	refresh(frm) {
		frm.add_custom_button(__("Open POS Closing Shift List"), () => {
			frappe.set_route("List", "POS Closing Shift");
		});

		if (!frm.is_new()) {
			frm.page.set_primary_action(__("Update Total Daily Payments"), () =>
				confirm_and_update(frm)
			);
		}
	},

	branch(frm) {
		// The selected shift may not belong to the new branch.
		frm.set_value("pos_closing_shift", null);
		if (frm.doc.affected_shifts && frm.doc.affected_shifts.length) {
			frm.clear_table("affected_shifts");
			frm.refresh_field("affected_shifts");
			frm.set_value("status", "Pending");
			frm.set_value("shifts_updated", 0);
		}
	},

	update_mode(frm) {
		frm.set_value("status", "Pending");
		frm.set_value("shifts_updated", 0);
	},

	pos_closing_shift(frm) {
		if (!frm.doc.pos_closing_shift) {
			frm.set_value("current_total_daily_payments", 0);
			frm.set_value("correct_total_daily_payments", 0);
			frm.set_value("difference", 0);
		}
	},

	get_affected_shifts(frm) {
		save_then(frm, () =>
			frm.call({
				doc: frm.doc,
				method: "fetch_affected_shifts",
				freeze: true,
				freeze_message: __("Checking POS Closing Shifts..."),
				callback: () => frm.refresh(),
			})
		);
	},
});

function confirm_and_update(frm) {
	const single = frm.doc.update_mode === "Single Closing Shift";
	const count = single ? 1 : (frm.doc.affected_shifts || []).length;

	if (!single && !count) {
		frappe.msgprint({
			title: __("Nothing To Update"),
			message: __("Use {0} first.", [__("Get Affected Closing Shifts")]),
			indicator: "orange",
		});
		return;
	}

	let message = __("This will overwrite Total Daily Payments on {0} submitted POS Closing Shift(s).", [
		count,
	]);
	if (frm.doc.update_actual_amount) {
		message += " " + __("Actual Amount will be recalculated as well.");
	}
	message += "<br><br>" + __("An audit comment is added to every closing shift that changes.");

	frappe.confirm(message, () =>
		save_then(frm, () =>
			frm.call({
				doc: frm.doc,
				method: "update_total_daily_payments",
				freeze: true,
				freeze_message: __("Updating POS Closing Shifts..."),
				callback: () => frm.refresh(),
			})
		)
	);
}

function save_then(frm, action) {
	// Both actions persist changes to this document, so it must exist first.
	if (frm.is_new() || frm.is_dirty()) {
		frm.save().then(action);
		return;
	}
	action();
}
