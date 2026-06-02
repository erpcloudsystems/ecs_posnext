// Copyright (c) 2026, Youssef Restom and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inventory', {
	get: function(frm) {
		if (!frm.doc.warehouse) {
			frappe.msgprint(__('Please select a warehouse first'));
			return;
		}
		
		frappe.call({
			method: 'ecs_posnext.pos_next.doctype.inventory.inventory.get_items_for_inventory',
			args: {
				warehouse: frm.doc.warehouse
			},
			freeze: true,
			freeze_message: __('Fetching items...'),
			callback: function(r) {
				if (r.message) {
					frm.clear_table('items');
					r.message.forEach(function(item) {
						let row = frm.add_child('items');
						row.item = item.item_code;
						row.qty = 0;
					});
					frm.refresh_field('items');
				}
			}
		});
	}
});
