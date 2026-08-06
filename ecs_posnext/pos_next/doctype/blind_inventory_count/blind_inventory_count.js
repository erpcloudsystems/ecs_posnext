// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Blind Inventory Count", {
	refresh(frm) {
		toggle_blind_columns(frm);

		if (frm.doc.docstatus === 0) {
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(
				__("Blind count: enter physically counted quantities. System quantities and variance stay hidden until you submit.")
			);
			frm.add_custom_button(__("Load Default Items"), () => load_items(frm, "default"));
			frm.add_custom_button(__("Load All Warehouse Items"), () => load_items(frm, "warehouse"));
		}

		if (frm.doc.docstatus === 1) {
			const indicator = frm.doc.has_variance ? "red" : "green";
			const label = frm.doc.has_variance
				? __("{0} item(s) with variance", [frm.doc.items_with_variance])
				: __("No variance");
			frm.dashboard.clear_headline();
			frm.dashboard.add_indicator(label, indicator);
		}
	},

	pos_profile(frm) {
		if (!frm.doc.pos_profile) return;
		frappe.db.get_value("POS Profile", frm.doc.pos_profile, ["warehouse", "company"]).then((r) => {
			const v = (r && r.message) || {};
			if (v.warehouse && !frm.doc.warehouse) frm.set_value("warehouse", v.warehouse);
			if (v.company) frm.set_value("company", v.company);
		});
	},

	warehouse(frm) {
		// On a fresh, empty sheet, auto-fill the manager's default (flagged) items so they
		// only have to type quantities.
		if (frm.doc.docstatus === 0 && frm.doc.warehouse && !(frm.doc.items || []).length) {
			load_items(frm, "default", { silent: true });
		}
	},
});

function toggle_blind_columns(frm) {
	// Reveal columns are hidden while the count is a draft, shown once submitted.
	const blind = frm.doc.docstatus !== 1;
	const grid = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (!grid) return;
	["system_qty", "variance_qty", "valuation_rate", "variance_value"].forEach((f) => {
		grid.update_docfield_property(f, "hidden", blind ? 1 : 0);
	});
	// The counted-qty field is only editable while drafting.
	grid.update_docfield_property("counted_qty", "read_only", frm.doc.docstatus === 0 ? 0 : 1);
	grid.refresh();
}

function load_items(frm, source, opts) {
	opts = opts || {};
	if (!frm.doc.warehouse) {
		if (!opts.silent) frappe.msgprint(__("Please set a Warehouse (or POS Profile) first."));
		return;
	}
	const method =
		source === "warehouse"
			? "ecs_posnext.pos_next.doctype.blind_inventory_count.blind_inventory_count.get_warehouse_count_items"
			: "ecs_posnext.pos_next.doctype.blind_inventory_count.blind_inventory_count.get_default_count_items";
	frappe.call({
		method: method,
		args: { warehouse: frm.doc.warehouse },
		freeze: !opts.silent,
		freeze_message: __("Loading items..."),
		callback: (r) => {
			const rows = r.message || [];
			if (!rows.length) {
				if (!opts.silent) {
					frappe.msgprint(
						source === "warehouse"
							? __("No stock items found in this warehouse.")
							: __("No default items are flagged. Tick 'Include in Blind Inventory Count' on the relevant Items, or use 'Load All Warehouse Items'.")
					);
				}
				return;
			}
			const existing = new Set((frm.doc.items || []).map((d) => d.item_code));
			let added = 0;
			rows.forEach((it) => {
				if (existing.has(it.item_code)) return;
				const row = frm.add_child("items");
				row.item_code = it.item_code;
				row.item_name = it.item_name;
				row.uom = it.uom;
				row.warehouse = it.warehouse;
				row.counted_qty = 0;
				added += 1;
			});
			frm.refresh_field("items");
			if (added) {
				frappe.show_alert({ message: __("Added {0} item(s) to count.", [added]), indicator: "green" });
			}
		},
	});
}
