// Mirrors FALLBACK_TARGET_MINUTES / ORDER_TYPE_TARGET_FIELDS in kds_settings.py.
const FALLBACK_TARGET_MINUTES = 15;
const ORDER_TYPE_TARGET_FIELDS = [
	"pickup_target_minutes",
	"delivery_target_minutes",
	"dine_in_target_minutes",
	"talabat_target_minutes",
];

frappe.ui.form.on("KDS Settings", {
	refresh: (frm) => update_warning_pct(frm),
	warning_threshold_minutes: (frm) => update_warning_pct(frm),
	...Object.fromEntries(
		ORDER_TYPE_TARGET_FIELDS.map((fieldname) => [fieldname, (frm) => update_warning_pct(frm)])
	),
});

// Mirror the server-side derivation so the % and the hint update as you type,
// rather than only showing the stored value until the next save.
function update_warning_pct(frm) {
	const minutes = cint(frm.doc.warning_threshold_minutes);

	if (!minutes) {
		frm.set_df_property("warning_threshold_minutes", "description", "");
		return;
	}

	// Every order type must be able to turn amber before it turns red, so the
	// warning has to sit below each configured target.
	for (const fieldname of ORDER_TYPE_TARGET_FIELDS) {
		const target = cint(frm.doc[fieldname]);
		if (target && minutes >= target) {
			frm.set_df_property(
				"warning_threshold_minutes",
				"description",
				__("Must be less than {0} ({1} min).", [
					__(frm.get_docfield(fieldname).label),
					target,
				])
			);
			return;
		}
	}

	const targets = ORDER_TYPE_TARGET_FIELDS.map((fieldname) => cint(frm.doc[fieldname]));
	if (targets.some((target) => !target)) {
		if (minutes >= FALLBACK_TARGET_MINUTES) {
			frm.set_df_property(
				"warning_threshold_minutes",
				"description",
				__(
					"Must be less than the {0} min fallback used by order types with no target of their own.",
					[FALLBACK_TARGET_MINUTES]
				)
			);
			return;
		}
		targets.push(FALLBACK_TARGET_MINUTES);
	}

	const shortest = Math.min(...targets.filter(Boolean));
	const pct = Math.max(1, Math.min(99, Math.round((minutes / shortest) * 100)));
	frm.set_value("warning_threshold_pct", pct);
	frm.set_df_property(
		"warning_threshold_minutes",
		"description",
		__("Timer turns amber at {0} min, red at each order's own target ({1}% of target).", [
			minutes,
			pct,
		])
	);
}
