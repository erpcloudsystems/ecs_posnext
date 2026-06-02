frappe.ui.form.on('POS Shift Group Closing', {
    refresh(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Fetch Closings'), () => {
                if (!frm.doc.working_day || !frm.doc.shift || !frm.doc.company) {
                    frappe.msgprint(__('Please set Working Day, Shift and Company first.'));
                    return;
                }
                
                frappe.call({
                    method: 'ecs_posnext.pos_next.doctype.pos_shift_group_closing.pos_shift_group_closing.get_closings_data',
                    args: {
                        working_day: frm.doc.working_day,
                        shift: frm.doc.shift,
                        company: frm.doc.company,
                        pos_profile: frm.doc.pos_profile
                    },
                    freeze: true,
                    freeze_message: __('Fetching data...'),
                    callback: (r) => {
                        if (r.message) {
                            const data = r.message;
                            
                            frm.set_value('period_start', data.period_start);
                            frm.set_value('period_end', data.period_end);
                            
                            // Define tables to update
                            const tables = ['closings', 'payments', 'unpaid_invoices'];
                            
                            tables.forEach(table => {
                                frm.clear_table(table);
                                (data[table] || []).forEach(row => {
                                    let child = frm.add_child(table);
                                    // Copy fields but skip internal ones
                                    for (let key in row) {
                                        if (!['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx', 'doctype', 'parent', 'parentfield', 'parenttype', '__islocal'].includes(key)) {
                                            child[key] = row[key];
                                        }
                                    }
                                });
                            });
                            
                            frm.set_value('grand_total', data.grand_total);
                            frm.set_value('net_total', data.net_total);
                            frm.set_value('total_quantity', data.total_quantity);
                            frm.set_value('expected_amount', data.expected_amount);
                            frm.set_value('closing_amount', data.closing_amount);
                            frm.set_value('difference', data.difference);
                            
                            frm.refresh_fields();
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
