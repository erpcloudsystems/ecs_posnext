frappe.ui.form.on("KDS Settings", {
	refresh: (frm) => update_warning_pct(frm),
	warning_threshold_minutes: (frm) => update_warning_pct(frm),
	default_target_minutes: (frm) => update_warning_pct(frm),
});

// Mirror the server-side derivation so the % and the hint update as you type,
// rather than only showing the stored value until the next save.
function update_warning_pct(frm) {
	const target = cint(frm.doc.default_target_minutes);
	const minutes = cint(frm.doc.warning_threshold_minutes);

	if (!target || !minutes) {
		frm.set_df_property("warning_threshold_minutes", "description", "");
		return;
	}

	if (minutes >= target) {
		frm.set_df_property(
			"warning_threshold_minutes",
			"description",
			__("Must be less than Target Minutes ({0} min).", [target])
		);
		return;
	}

	const pct = Math.max(1, Math.min(99, Math.round((minutes / target) * 100)));
	frm.set_value("warning_threshold_pct", pct);
	frm.set_df_property(
		"warning_threshold_minutes",
		"description",
		__("Timer turns amber at {0} min, red at {1} min ({2}% of target).", [minutes, target, pct])
	);
}
