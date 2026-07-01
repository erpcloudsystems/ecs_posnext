// frappe.ui.form.on('Item', {
//     refresh: function (frm) {
//         if (frm.is_new()) {
//             show_item_creation_dialog(frm);
//         }
//     }
// });

// function show_item_creation_dialog(frm) {
//     let dialog = new frappe.ui.Dialog({
//         title: __('Create SKU for Item'),
//         fields: [
//             {
//                 fieldname: 'item_name',
//                 fieldtype: 'Data',
//                 label: __('Item Name'),
//                 reqd: 1,
//                 change: function () {
//                     if (this.get_value()) {
//                         let product_code = this.get_value().substring(0, 3).toUpperCase();
//                         dialog.set_value('product_code', product_code);
//                         update_full_item_code(dialog);
//                     }
//                 }
//             },
//             {
//                 fieldname: 'custom_item_name_arabic',
//                 fieldtype: 'Data',
//                 label: __('Arabic Item Name')
//             },
//             {
//                 fieldname: 'item_group',
//                 fieldtype: 'Link',
//                 label: __('Item Group'),
//                 options: 'Item Group',
//                 reqd: 1,
//                 change: function () {
//                     if (this.get_value()) {
//                         get_category_code(this.get_value(), dialog);
//                     }
//                 }
//             },
//             {
//                 fieldname: 'category_code',
//                 fieldtype: 'Data',
//                 label: __('Category Code'),
//                 reqd: 1,
//                 read_only: 1,
//                 description: __('Auto-populated from Item Group custom_item_group_code')
//             },
//             {
//                 fieldname: 'product_code',
//                 fieldtype: 'Data',
//                 label: __('Product Code'),
//                 reqd: 1,
//                 description: __('First 3 characters from Item Name')
//             },
//             {
//                 fieldname: 'full_item_code',
//                 fieldtype: 'Data',
//                 label: __('Full Item Code'),
//                 read_only: 1,
//                 description: __('Combination of Category Code and Product Code')
//             }
//         ],
//         primary_action: function () {
//             let values = dialog.get_values();
//             if (values) {
//                 // Check if item code already exists
//                 check_item_code_uniqueness(values.full_item_code, function (is_unique) {
//                     if (is_unique) {
//                         // Create new item document
//                         create_new_item(values, function () {
//                             dialog.hide();
//                         });
//                     } else {
//                         frappe.msgprint({
//                             title: __('Duplicate Item Code'),
//                             message: __('Item Code "{0}" already exists. Please modify the product code to generate a unique SKU.', [values.full_item_code]),
//                             indicator: 'red'
//                         });
//                     }
//                 });
//             }
//         },
//         primary_action_label: __('Create Item SKU')
//     });

//     // Auto-populate fields when product_code changes
//     dialog.fields_dict.product_code.$input.on('blur', function () {
//         update_full_item_code(dialog);
//     });


//     dialog.show();
// }

// function get_category_code(item_group, dialog) {
//     frappe.call({
//         method: 'frappe.client.get_value',
//         args: {
//             doctype: 'Item Group',
//             fieldname: 'custom_item_group_code',
//             filters: { name: item_group }
//         },
//         callback: function (r) {
//             if (r.message && r.message.custom_item_group_code) {

//                 dialog.set_value('category_code', r.message.custom_item_group_code);
//                 update_full_item_code(dialog);
//             }
//         }
//     });
// }

// function update_full_item_code(dialog) {
//     let category_code = dialog.get_value('category_code')?.toUpperCase() || '';
//     let product_code = dialog.get_value('product_code')?.toUpperCase() || '';
//     let full_code = `${category_code}-${product_code}`;
//     dialog.set_value('full_item_code', full_code);
// }

// function check_item_code_uniqueness(item_code, callback) {
//     frappe.call({
//         method: 'frappe.client.get_count',
//         args: {
//             doctype: 'Item',
//             filters: { item_code: item_code }
//         },
//         callback: function (r) {
//             callback(r.message === 0);
//         }
//     });
// }

// function create_new_item(values, callback) {
//     frappe.call({
//         method: 'frappe.client.insert',
//         args: {
//             doc: {
//                 doctype: 'Item',
//                 item_code: values.full_item_code,
//                 item_name: values.item_name,
//                 custom_item_name_arabic: values.custom_item_name_arabic,
//                 item_group: values.item_group
//             }
//         },
//         callback: function (r) {
//             if (r.message && !r.message.exc) {
//                 frappe.show_alert({
//                     message: __('Item "{0}" created successfully', [values.item_name]),
//                     indicator: 'green'
//                 });
//                 // Redirect to the newly created item
//                 frappe.set_route('Form', 'Item', r.message.name);
//                 if (callback) callback();
//             } else {
//                 frappe.show_alert({
//                     message: __('Error creating item: {0}', [r.message ? r.message.exc : __('Unknown error')]),
//                     indicator: 'red'
//                 });
//             }
//         }
//     });
// }
