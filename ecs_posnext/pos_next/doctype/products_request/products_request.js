// Copyright (c) 2026, ECS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Products Request", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.dashboard.set_headline(
				__("Products Request — finished products load automatically; enter the request quantity for what you need.")
			);
			frm.add_custom_button(__("Load Products"), () =>
				load_requisition_items(frm, "ecs_posnext.api.branch_requisition.get_product_items")
			);
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

	onload(frm) {
		if (frm.is_new() && !(frm.doc.items || []).length) {
			load_requisition_items(frm, "ecs_posnext.api.branch_requisition.get_product_items", { silent: true });
		}
	},
});

function load_requisition_items(frm, method, opts) {
	opts = opts || {};
	frappe.call({
		method: method,
		freeze: !opts.silent,
		freeze_message: __("Loading items..."),
		callback: (r) => {
			const rows = r.message || [];
			if (!rows.length) {
				if (!opts.silent) {
					frappe.msgprint(__("No items are flagged for this form yet. Tick the matching checkbox on the relevant Items."));
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
				row.qty = 0;
				added += 1;
			});
			frm.refresh_field("items");
			if (added) {
				frappe.show_alert({ message: __("Loaded {0} item(s).", [added]), indicator: "green" });
			}
		},
	});
}
