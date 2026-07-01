frappe.ui.form.on('POS Shift Group Closing', {
    refresh(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Fetch Closings'), () => {
                frm.trigger('fetch_data');
            });
        }

        if (frm.is_new() && !frm.doc.supervisor) {
            frm.set_value('supervisor', frappe.session.user);
        }
    },
    
    custom_transfer_cash(frm) {
        if (!frm.doc.custom_mode_of_payment) {
            frappe.msgprint(__('Please select Target Mode of Payment first.'));
            return;
        }
        
        frappe.confirm(__('Are you sure you want to transfer all cash to {0}?', [frm.doc.custom_mode_of_payment]), () => {
            frm.call({
                doc: frm.doc,
                method: 'transfer_cash',
                freeze: true,
                freeze_message: __('Creating internal transfers...'),
                callback: (r) => {
                    // Success messages are handled by the backend msgprint
                }
            });
        });
    },
    
    fetch_data(frm) {
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
    }
});

frappe.ui.form.on('POS Shift Group Unpaid Invoice', {
    pay: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (!row.sales_invoice) return;
        
        // 1. Check open shift
        frappe.call({
            method: 'ecs_posnext.api.shifts.check_opening_shift',
            callback: function(r) {
                let open_shift_name = null;
                let pos_profile = null;

                if (r.message && !r.message.is_prepared) {
                    open_shift_name = r.message.pos_opening_shift.name;
                    pos_profile = r.message.pos_profile;
                    show_payment_dialog(open_shift_name, pos_profile);
                } else {
                    let pos_profile_name = frm.doc.pos_profile;
                    
                    if (pos_profile_name) {
                        fetch_profile_and_show(pos_profile_name);
                    } else {
                        // Fetch POS profile from Sales Invoice if not set on the closing record
                        frappe.db.get_value('Sales Invoice', row.sales_invoice, 'pos_profile').then(r => {
                            if (r && r.message && r.message.pos_profile) {
                                fetch_profile_and_show(r.message.pos_profile);
                            } else {
                                frappe.msgprint(__('Could not determine POS Profile for this invoice.'));
                            }
                        });
                    }

                    function fetch_profile_and_show(profile_name) {
                        // Silently show the payment dialog; the shift will be opened and closed in the background
                        frappe.db.get_doc('POS Profile', profile_name).then(profile => {
                            show_payment_dialog(null, profile);
                        });
                    }
                }
                
                function show_payment_dialog(open_shift_name, pos_profile) {
                    // 2. Show Dialog
                    let d = new frappe.ui.Dialog({
                        title: __('Pay Invoice: {0}', [row.sales_invoice]),
                        fields: [
                            {
                                label: __('Outstanding Amount'),
                                fieldname: 'outstanding_amount',
                                fieldtype: 'Currency',
                                default: row.outstanding_amount,
                                read_only: 1
                            },
                            {
                                fieldname: 'payments',
                                fieldtype: 'Table',
                                label: __('Payments'),
                                fields: [
                                    {
                                        fieldname: 'mode_of_payment',
                                        fieldtype: 'Link',
                                        options: 'Mode of Payment',
                                        label: __('Mode of Payment'),
                                        in_list_view: 1,
                                        read_only: 1
                                    },
                                    {
                                        fieldname: 'amount',
                                        fieldtype: 'Currency',
                                        label: __('Amount'),
                                        in_list_view: 1,
                                        default: 0
                                    }
                                ],
                                data: (pos_profile.payments || []).map(p => ({
                                    mode_of_payment: p.mode_of_payment,
                                    amount: 0
                                }))
                            }
                        ],
                        primary_action_label: __('Pay'),
                        primary_action(values) {
                            let total_paying = values.payments.reduce((acc, p) => acc + (p.amount || 0), 0);
                            if (total_paying <= 0) {
                                frappe.msgprint(__('Please enter at least one payment amount.'));
                                return;
                            }
                            if (total_paying > row.outstanding_amount + 0.01) {
                                frappe.msgprint(__('Total payment amount ({0}) exceeds outstanding amount ({1}).', [total_paying, row.outstanding_amount]));
                                return;
                            }

                            d.get_primary_btn().prop('disabled', true);
                            
                            if (open_shift_name) {
                                frappe.call({
                                    method: 'ecs_posnext.api.payment_entry.create_pos_payment_entry',
                                    args: {
                                        payload: JSON.stringify({
                                            selected_invoice: row.sales_invoice,
                                            pos_profile: pos_profile,
                                            pos_profile_name: pos_profile.name,
                                            pos_opening_shift_name: open_shift_name,
                                            payment_methods: values.payments.filter(p => p.amount > 0),
                                            submit: true
                                        })
                                    },
                                    callback: function(r) {
                                        d.hide();
                                        frappe.show_alert({message: __('Payment processed successfully'), indicator: 'green'});
                                        if (frm.events.fetch_data) {
                                            frm.events.fetch_data(frm);
                                        } else {
                                            frm.trigger('fetch_data');
                                        }
                                    },
                                    error: function() {
                                        d.get_primary_btn().prop('disabled', false);
                                    }
                                });
                            } else {
                                frappe.call({
                                    method: 'ecs_posnext.api.shifts.auto_process_payment_with_temp_shift',
                                    args: {
                                        invoice: row.sales_invoice,
                                        pos_profile_name: pos_profile.name,
                                        payment_methods_json: JSON.stringify(values.payments.filter(p => p.amount > 0))
                                    },
                                    callback: function(r) {
                                        d.hide();
                                        frappe.show_alert({message: __('Payment and temporary shift processed successfully'), indicator: 'green'});
                                        if (frm.events.fetch_data) {
                                            frm.events.fetch_data(frm);
                                        } else {
                                            frm.trigger('fetch_data');
                                        }
                                    },
                                    error: function() {
                                        d.get_primary_btn().prop('disabled', false);
                                    }
                                });
                            }
                        }
                    });
                    d.show();
                }
            }
        });
    }
});
