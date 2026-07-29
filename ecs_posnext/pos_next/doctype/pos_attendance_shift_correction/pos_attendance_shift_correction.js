// Copyright (c) 2026, erpcloud.systems and contributors
// For license information, please see license.txt

const METHOD_PATH =
	"ecs_posnext.pos_next.doctype.pos_attendance_shift_correction.pos_attendance_shift_correction";

frappe.ui.form.on("POS Attendance Shift Correction", {
	refresh(frm) {
		frm.disable_save();
		set_target_shift(frm);
		set_intro(frm);
		set_buttons(frm);
	},

	only_missing_shift(frm) {
		clear_records(frm);
	},

	from_date(frm) {
		clear_records(frm);
	},

	to_date(frm) {
		clear_records(frm);
	},
});

function set_target_shift(frm) {
	if (frm.doc.target_shift) return;

	frappe.call({
		method: `${METHOD_PATH}.get_target_shift`,
		callback(r) {
			if (r.message) {
				frm.set_value("target_shift", r.message);
			}
		},
	});
}

function set_intro(frm) {
	frm.set_intro(
		__(
			"POS hides a craftsman whose Attendance is not inside the running shift's window. A record with no Shift Type has no window, so it stops counting at midnight. Fetch the records below, review them, then apply. Only the Shift field is written — Attendance Date is never changed."
		),
		"blue"
	);
}

function set_buttons(frm) {
	frm.add_custom_button(__("Fetch Attendance to Correct"), () => {
		load_records(frm);
	});

	if ((frm.doc.records || []).length) {
		frm.add_custom_button(__("Apply Corrections"), () => {
			confirm_and_apply(frm);
		}).addClass("btn-primary");
	}
}

function clear_records(frm) {
	frm.clear_table("records");
	frm.refresh_field("records");
	frm.refresh();
}

function load_records(frm) {
	frappe.call({
		method: `${METHOD_PATH}.get_attendance_to_correct`,
		args: {
			from_date: frm.doc.from_date || undefined,
			to_date: frm.doc.to_date || undefined,
			only_missing_shift: cint(frm.doc.only_missing_shift),
		},
		freeze: true,
		freeze_message: __("Checking attendance records..."),
		callback(r) {
			frm.clear_table("records");

			(r.message || []).forEach((row) => {
				frm.add_child("records", Object.assign({ apply: 1 }, row));
			});

			frm.refresh_field("records");
			frm.refresh();

			if (!(r.message || []).length) {
				frappe.msgprint({
					title: __("Nothing to Correct"),
					message: __("Every submitted Attendance record in this range is already on {0}.", [
						frm.doc.target_shift || __("the default shift"),
					]),
					indicator: "green",
				});
			}
		},
	});
}

function confirm_and_apply(frm) {
	const selected = (frm.doc.records || []).filter((row) => row.apply);

	if (!selected.length) {
		frappe.msgprint(__("Tick at least one row to apply."));
		return;
	}

	frappe.confirm(
		`${__("Set the Shift to {0} on {1} submitted Attendance record(s)?", [
			frm.doc.target_shift,
			selected.length,
		])}<br><br>${__("Attendance Date is not changed. Each record keeps a comment recording the change.")}`,
		() => apply(frm, selected)
	);
}

function apply(frm, selected) {
	frappe.call({
		method: `${METHOD_PATH}.apply_corrections`,
		args: { records: selected },
		freeze: true,
		freeze_message: __("Applying corrections..."),
		callback(r) {
			if (!r.message) return;

			const { updated = [], skipped = [] } = r.message;

			let message = updated.length
				? __("Corrected {0} Attendance record(s) to {1}.", [
						updated.length,
						frm.doc.target_shift,
				  ])
				: __("No record needed correcting.");

			if (skipped.length) {
				message += `<p>${__("Already correct, skipped: {0}", [skipped.join(", ")])}</p>`;
			}

			frappe.msgprint({
				title: __("Corrections Applied"),
				message: message,
				indicator: updated.length ? "green" : "orange",
			});

			clear_records(frm);
		},
	});
}
