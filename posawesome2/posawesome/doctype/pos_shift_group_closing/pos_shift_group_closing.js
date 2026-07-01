frappe.ui.form.on('POS Shift Group Closing', {
    refresh(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Fetch Closings'), () => {
                if (frm.is_new()) {
                    frappe.msgprint(__('Please save the document before fetching closings.'));
                    return;
                }
                if (!frm.doc.working_day || !frm.doc.shift) {
                    frappe.msgprint(__('Please set Working Day and Shift first.'));
                    return;
                }
                frappe.call({
                    method: 'posawesome.posawesome.doctype.pos_shift_group_closing.pos_shift_group_closing.fetch_closings',
                    args: { name: frm.doc.name },
                    callback: (r) => {
                        if (r.message) {
                            frm.reload_doc();
                        }
                    }
                });
            });
        }

        if (frm.is_new() && !frm.doc.supervisor) {
            frm.set_value('supervisor', frappe.session.user);
        }
    }
});
