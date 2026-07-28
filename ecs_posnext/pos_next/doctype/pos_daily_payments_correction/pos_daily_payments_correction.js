// Copyright (c) 2026, erpcloud.systems and contributors
// For license information, please see license.txt

const METHOD_PATH =
	"ecs_posnext.pos_next.doctype.pos_daily_payments_correction.pos_daily_payments_correction";

frappe.ui.form.on("POS Daily Payments Correction", {
	setup(frm) {
		frm.set_query("pos_closing_shift", () => ({
			query: `${METHOD_PATH}.problem_shift_query`,
			filters: { branch: frm.doc.branch || undefined },
		}));
	},

	refresh(frm) {
		frm.disable_save();
		set_intro(frm);
		set_buttons(frm);
	},

	branch(frm) {
		reset(frm);
	},

	correction_mode(frm) {
		reset(frm);
	},

	pos_closing_shift(frm) {
		if (frm.doc.correction_mode !== "Single Shift") return;

		if (!frm.doc.pos_closing_shift) {
			clear_shifts(frm);
			return;
		}

		load_shifts(frm, { pos_closing_shift: frm.doc.pos_closing_shift }, false);
	},
});

function set_intro(frm) {
	frm.set_intro(null);

	if (frm.doc.correction_mode === "All Problem Shifts") {
		frm.set_intro(
			__(
				"Fetch every submitted POS Closing Shift whose Total Daily Payments is wrong, review the table, then apply."
			),
			"blue"
		);
	} else {
		frm.set_intro(
			__("Pick one POS Closing Shift to review and correct. Only wrong shifts are listed."),
			"blue"
		);
	}
}

function set_buttons(frm) {
	if (frm.doc.correction_mode === "All Problem Shifts") {
		frm.add_custom_button(__("Fetch Problem Shifts"), () => {
			load_shifts(frm, { branch: frm.doc.branch || undefined }, true);
		});
	}

	if ((frm.doc.shifts || []).length) {
		frm.add_custom_button(__("Update Total Daily Payments"), () => {
			confirm_and_apply(frm);
		}).addClass("btn-primary");
	}
}

function reset(frm) {
	if (frm.doc.pos_closing_shift) {
		frm.set_value("pos_closing_shift", null);
	}
	clear_shifts(frm);
}

function clear_shifts(frm) {
	frm.clear_table("shifts");
	frm.refresh_field("shifts");
	frm.refresh();
}

function load_shifts(frm, args, notify_when_empty) {
	frappe.call({
		method: `${METHOD_PATH}.get_problem_shifts`,
		args: args,
		freeze: true,
		freeze_message: __("Checking closing shifts..."),
		callback(r) {
			frm.clear_table("shifts");

			(r.message || []).forEach((row) => {
				frm.add_child("shifts", Object.assign({ apply: 1 }, row));
			});

			frm.refresh_field("shifts");
			frm.refresh();

			if (!(r.message || []).length && notify_when_empty) {
				frappe.msgprint({
					title: __("Nothing to Correct"),
					message: __("No closing shift has a wrong Total Daily Payments for this filter."),
					indicator: "green",
				});
			}
		},
	});
}

function confirm_and_apply(frm) {
	const selected = (frm.doc.shifts || []).filter((row) => row.apply);

	if (!selected.length) {
		frappe.msgprint(__("Tick at least one row to apply."));
		return;
	}

	const actual_note = frm.doc.update_actual_amount
		? __("Actual Amount will be moved by the same difference.")
		: __("Actual Amount will be left unchanged and will no longer match its own formula.");

	frappe.confirm(
		`${__("Correct Total Daily Payments on {0} submitted closing shift(s)?", [
			selected.length,
		])}<br><br>${actual_note}`,
		() => apply(frm, selected)
	);
}

function apply(frm, selected) {
	frappe.call({
		method: `${METHOD_PATH}.apply_corrections`,
		args: {
			shifts: selected,
			update_actual_amount: frm.doc.update_actual_amount ? 1 : 0,
		},
		freeze: true,
		freeze_message: __("Applying corrections..."),
		callback(r) {
			if (!r.message) return;

			const { updated = [], skipped = [] } = r.message;
			const lines = updated.map(
				(row) =>
					`<li>${row.pos_closing_shift}: ${format_currency(
						row.stored_total_daily_payments
					)} → <b>${format_currency(row.correct_total_daily_payments)}</b></li>`
			);

			let message = updated.length
				? `${__("Corrected {0} closing shift(s):", [updated.length])}<ul>${lines.join(
						""
				  )}</ul>`
				: __("No shift needed correcting.");

			if (skipped.length) {
				message += `<p>${__("Already correct, skipped: {0}", [skipped.join(", ")])}</p>`;
			}

			frappe.msgprint({
				title: __("Corrections Applied"),
				message: message,
				indicator: updated.length ? "green" : "orange",
			});

			reset(frm);
		},
	});
}
