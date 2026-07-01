// Copyright (c) 2020, Youssef Restom and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Closing Shift", {
	onload: function (frm) {
		frm.set_query("pos_profile", function (doc) {
			return {
				filters: { user: doc.user },
			};
		});

		frm.set_query("user", function (doc) {
			return {
				query: "ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift.get_cashiers",
				filters: { parent: doc.pos_profile },
			};
		});

		frm.set_query("pos_opening_shift", function (doc) {
			return { filters: { status: "Open", docstatus: 1 } };
		});

		if (frm.doc.docstatus === 0) {
			frm.set_value("period_end_date", frappe.datetime.now_datetime());
		}
		if (frm.doc.docstatus === 1) {
			set_html_data(frm);
		}

		if (frm.doc.pos_profile) {
			frappe.call({
				method: "ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift.get_cash_mode_of_payment_py",
				args: { pos_profile: frm.doc.pos_profile },
				callback: (r) => {
					frm.cash_mop = r.message || "Cash";
					if (frm.doc.docstatus === 0) {
						calculate_total_cash(frm);
					}
				},
			});
		}
	},

	refresh: function (frm) {
		if (frm.doc.docstatus === 0 && frm.doc.pos_profile && !frm.cash_mop) {
			frm.trigger("onload");
		}
	},

	before_save(frm) {
		if (frm.doc.docstatus !== 0) return;
		return refresh_shift_data(frm);
	},

	pos_opening_shift(frm) {
		if (frm.doc.pos_opening_shift && frm.doc.user) {
			refresh_shift_data(frm);
		}
	},

	cash_200_egp: calculate_total_cash,
	cash_100_egp: calculate_total_cash,
	cash_50_egp: calculate_total_cash,
	cash_20_egp: calculate_total_cash,
	cash_10_egp: calculate_total_cash,
	cash_5_egp: calculate_total_cash,
	cash_1_egp: calculate_total_cash,

	before_submit(frm) {
		return new Promise((resolve, reject) => {
			frappe.confirm(
				`
                <b>إجمالي النقدية:</b> ${format_currency(frm.doc.total_cash, "EGP")}<br><br>
                هل أنت متأكد من اعتماد المستند؟
                `,
				() => resolve(),
				() => reject()
			);
		});
	},

	on_submit(frm) {
		const diff = flt(frm.doc.total_diff || 0);
		const abs_diff = Math.abs(diff);
		if (diff !== 0 && (!frm.doc.difference_reason || !frm.doc.difference_reason.trim())) {
			const diff_type = diff > 0 ? "زيادة ✅" : "عجز ❌";

			let d = new frappe.ui.Dialog({
				title: `${diff_type} بمبلغ ${format_currency(abs_diff, "EGP")}`,
				fields: [
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: "سبب الفرق",
						reqd: 1,
						description: "يرجى إدخال سبب الفرق في الإقفال",
					},
				],
				primary_action_label: "حفظ السبب",
				primary_action: (values) => {
					frappe.call({
						method: "frappe.client.set_value",
						args: {
							doctype: "POS Closing Shift",
							name: frm.doc.name,
							fieldname: "difference_reason",
							value: values.reason,
						},
						callback: function (r) {
							if (!r.exc) {
								frm.reload_doc();
								frappe.show_alert({
									message: "تم حفظ سبب الفرق",
									indicator: "green",
								});
							}
						},
					});
					d.hide();
				},
			});
			d.show();
		}

		if (diff > 0) {
			frappe.msgprint({
				title: "الإقفال",
				message: `زيادة ✅ بمبلغ ${format_currency(abs_diff, "EGP")}`,
				indicator: "orange",
			});
		} else if (diff < 0) {
			frappe.msgprint({
				title: "الإقفال",
				message: `عجز ❌ بمبلغ ${format_currency(abs_diff, "EGP")}`,
				indicator: "red",
			});
		}
		if (diff == 0) {
			frappe.msgprint({
				title: "الإقفال",
				message: `تم غلق بنجاح`,
				indicator: "orange",
			});
		}
	},

	after_workflow_action(frm) {
		if (frm.doc.workflow_state !== "Approved by branch manager") return;

		const diff = flt(frm.doc.total_diff || 0);
		const abs_diff = Math.abs(diff);

		if (diff !== 0 && (!frm.doc.difference_reason || !frm.doc.difference_reason.trim())) {
			const diff_type = diff > 0 ? "زيادة ✅" : "عجز ❌";

			let d = new frappe.ui.Dialog({
				title: `${diff_type} بمبلغ ${format_currency(abs_diff, "EGP")}`,
				fields: [
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: "سبب الفرق",
						reqd: 1,
						description: "يرجى إدخال سبب الفرق في الإقفال",
					},
				],
				primary_action_label: "حفظ السبب",
				primary_action: (values) => {
					frappe.call({
						method: "frappe.client.set_value",
						args: {
							doctype: "POS Closing Shift",
							name: frm.doc.name,
							fieldname: "difference_reason",
							value: values.reason,
						},
						callback: function (r) {
							if (!r.exc) {
								frm.reload_doc();
								frappe.show_alert({
									message: "تم حفظ سبب الفرق",
									indicator: "green",
								});
							}
						},
					});
					d.hide();
				},
			});
			d.show();
		}

		if (diff > 0) {
			frappe.msgprint({
				title: "الإقفال",
				message: `زيادة ✅ بمبلغ ${format_currency(abs_diff, "EGP")}`,
				indicator: "orange",
			});
		} else if (diff < 0) {
			frappe.msgprint({
				title: "الإقفال",
				message: `عجز ❌ بمبلغ ${format_currency(abs_diff, "EGP")}`,
				indicator: "red",
			});
		}
		if (diff == 0) {
			frappe.msgprint({
				title: "الإقفال",
				message: `تم غلق بنجاح`,
				indicator: "orange",
			});
		}
	},

	set_opening_amounts(frm) {
		if (!frm.doc.pos_opening_shift) return Promise.resolve();
		return frappe.db.get_doc("POS Opening Shift", frm.doc.pos_opening_shift).then(({ balance_details }) => {
			(balance_details || []).forEach((detail) => {
				frm.add_child("payment_reconciliation", {
					mode_of_payment: detail.mode_of_payment,
					opening_amount: detail.amount || 0,
					expected_amount: detail.amount || 0,
				});
			});
		});
	},

	get_pos_invoices(frm) {
		if (!frm.doc.pos_opening_shift) return Promise.resolve();
		return frappe.call({
			method: "ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift.get_pos_invoices",
			args: {
				pos_opening_shift: frm.doc.pos_opening_shift,
			},
			callback: (r) => {
				if (r.message) {
					set_form_data(r.message, frm);
				}
			},
		});
	},

	get_pos_payments(frm) {
		if (!frm.doc.pos_opening_shift) return Promise.resolve();
		return frappe.call({
			method: "ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift.get_payments_entries",
			args: {
				pos_opening_shift: frm.doc.pos_opening_shift,
			},
			callback: (r) => {
				if (r.message) {
					set_form_payments_data(r.message, frm);
				}
			},
		});
	},
});

frappe.ui.form.on("POS Closing Shift Detail", {
	closing_amount: (frm, cdt, cdn) => {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "difference", flt(row.closing_amount) - flt(row.expected_amount));
		calculate_total_diff(frm);
	},
});

function calculate_total_cash(frm) {
	let total =
		(frm.doc.cash_200_egp || 0) * 200 +
		(frm.doc.cash_100_egp || 0) * 100 +
		(frm.doc.cash_50_egp || 0) * 50 +
		(frm.doc.cash_20_egp || 0) * 20 +
		(frm.doc.cash_10_egp || 0) * 10 +
		(frm.doc.cash_5_egp || 0) * 5 +
		(frm.doc.cash_1_egp || 0) * 1;

	frm.set_value("total_cash", total);

	const cash_mop = get_cash_mode_of_payment(frm);

	(frm.doc.payment_reconciliation || []).forEach((d) => {
		const is_cash = d.mode_of_payment === cash_mop || (d.mode_of_payment || "").toLowerCase().includes("cash");
		if (is_cash) {
			frappe.model.set_value(d.doctype, d.name, "closing_amount", total);
		} else {
			frappe.model.set_value(d.doctype, d.name, "closing_amount", d.expected_amount);
		}
	});

	calculate_total_diff(frm);
}

function calculate_total_diff(frm) {
	let total_diff = 0;
	(frm.doc.payment_reconciliation || []).forEach((d) => {
		total_diff += flt(d.difference);
	});
	frm.set_value("total_diff", total_diff);
}

function get_cash_mode_of_payment(frm) {
	return frm.cash_mop || "Cash";
}

function refresh_shift_data(frm) {
	if (frm.doc.docstatus !== 0) return;
	if (frm.doc.pos_opening_shift && frm.doc.user) {
		const closingAmountMap = {};
		(frm.doc.payment_reconciliation || []).forEach((row) => {
			if (row.mode_of_payment) {
				closingAmountMap[row.mode_of_payment] = row.closing_amount;
			}
		});

		reset_values(frm);

		return frappe.run_serially([
			() => frm.trigger("set_opening_amounts"),
			() => frm.trigger("get_pos_invoices"),
			() => frm.trigger("get_pos_payments"),
			() => {
				(frm.doc.payment_reconciliation || []).forEach((row) => {
					if (closingAmountMap[row.mode_of_payment] != null) {
						row.closing_amount = closingAmountMap[row.mode_of_payment];
						row.difference = flt(row.closing_amount) - flt(row.expected_amount);
					}
				});
				refresh_fields(frm);
				set_html_data(frm);
				calculate_total_cash(frm);
			},
		]);
	}
}

function set_form_data(data, frm) {
	const seenInvoices = new Set(frm.doc.pos_transactions.map((row) => row.sales_invoice || row.pos_invoice));
	data.forEach((d) => {
		if (seenInvoices.has(d.name)) return;
		seenInvoices.add(d.name);

		add_to_pos_transaction(d, frm);

		const conversion_rate = get_conversion_rate(d);
		frm.doc.grand_total += get_base_value(d, "grand_total", "base_grand_total", conversion_rate);
		frm.doc.net_total += get_base_value(d, "net_total", "base_net_total", conversion_rate);
		frm.doc.total_quantity += flt(d.total_qty);

		add_to_payments(d, frm, conversion_rate);
		add_to_taxes(d, frm, conversion_rate);
	});
}

function set_form_payments_data(data, frm) {
	const seenPayments = new Set(frm.doc.pos_payments.map((row) => row.payment_entry));
	data.forEach((d) => {
		if (seenPayments.has(d.name)) return;
		seenPayments.add(d.name);

		add_to_pos_payments(d, frm);
		add_pos_payment_to_payments(d, frm);
	});
}

function add_to_pos_transaction(d, frm) {
	const conversion_rate = get_conversion_rate(d);
	const child = {
		posting_date: d.posting_date,
		grand_total: get_base_value(d, "grand_total", "base_grand_total", conversion_rate),
		transaction_currency: d.currency,
		transaction_amount: flt(d.grand_total),
		customer: d.customer,
	};
	if (d.doctype === "POS Invoice") {
		child.pos_invoice = d.name;
	} else {
		child.sales_invoice = d.name;
	}
	frm.add_child("pos_transactions", child);
}

function add_to_pos_payments(d, frm) {
	frm.add_child("pos_payments", {
		payment_entry: d.name,
		posting_date: d.posting_date,
		paid_amount: d.paid_amount,
		customer: d.party,
		mode_of_payment: d.mode_of_payment,
	});
}

function add_to_payments(d, frm, conversion_rate) {
	const cash_mop = get_cash_mode_of_payment(frm);

	(d.payments || []).forEach((p) => {
		const payment = (frm.doc.payment_reconciliation || []).find((pay) => pay.mode_of_payment === p.mode_of_payment);
		if (payment) {
			let amount = get_base_value(p, "amount", "base_amount", conversion_rate);
			if (payment.mode_of_payment == cash_mop) {
				amount -= get_base_value(d, "change_amount", "base_change_amount", conversion_rate);
			}
			payment.expected_amount += flt(amount);
			payment.difference = flt(payment.closing_amount) - flt(payment.expected_amount);
		} else {
			frm.add_child("payment_reconciliation", {
				mode_of_payment: p.mode_of_payment,
				opening_amount: 0,
				expected_amount: get_base_value(p, "amount", "base_amount", conversion_rate),
				difference: -get_base_value(p, "amount", "base_amount", conversion_rate),
			});
		}
	});
}

function add_pos_payment_to_payments(p, frm) {
	const payment = (frm.doc.payment_reconciliation || []).find((pay) => pay.mode_of_payment === p.mode_of_payment);
	if (payment) {
		let amount = get_base_value(p, "paid_amount", "base_paid_amount");
		payment.expected_amount += flt(amount);
		payment.difference = flt(payment.closing_amount) - flt(payment.expected_amount);
	} else {
		frm.add_child("payment_reconciliation", {
			mode_of_payment: p.mode_of_payment,
			opening_amount: 0,
			expected_amount: get_base_value(p, "paid_amount", "base_paid_amount"),
			difference: -get_base_value(p, "paid_amount", "base_paid_amount"),
		});
	}
}

function add_to_taxes(d, frm, conversion_rate) {
	(d.taxes || []).forEach((t) => {
		const tax = (frm.doc.taxes || []).find((tx) => tx.account_head === t.account_head && tx.rate === t.rate);
		if (tax) {
			tax.amount += flt(get_base_value(t, "tax_amount", "base_tax_amount", conversion_rate));
		} else {
			frm.add_child("taxes", {
				account_head: t.account_head,
				rate: t.rate,
				amount: get_base_value(t, "tax_amount", "base_tax_amount", conversion_rate),
			});
		}
	});
}

function reset_values(frm) {
	frm.doc.pos_transactions = [];
	frm.doc.payment_reconciliation = [];
	frm.doc.pos_payments = [];
	frm.doc.taxes = [];
	frm.doc.grand_total = 0;
	frm.doc.net_total = 0;
	frm.doc.total_quantity = 0;
}

function refresh_fields(frm) {
	frm.refresh_field("pos_transactions");
	frm.refresh_field("payment_reconciliation");
	frm.refresh_field("pos_payments");
	frm.refresh_field("taxes");
	frm.refresh_field("grand_total");
	frm.refresh_field("net_total");
	frm.refresh_field("total_quantity");
}

function set_html_data(frm) {
	if (!frm.doc.name || frm.doc.__islocal) return;
	frappe.call({
		method: "get_payment_reconciliation_details",
		doc: frm.doc,
		callback: (r) => {
			if (r.message && frm.fields_dict.payment_reconciliation_details) {
				frm.get_field("payment_reconciliation_details").$wrapper.html(r.message);
			}
		},
	});
}

const get_conversion_rate = (doc) =>
	doc.conversion_rate || doc.exchange_rate || doc.target_exchange_rate || doc.plc_conversion_rate || 1;

const get_base_value = (doc, field, base_field, conversion_rate) => {
	const base_fieldname = base_field || `base_${field}`;
	const base_value = doc[base_fieldname];
	if (base_value !== undefined && base_value !== null && base_value !== "") {
		return flt(base_value);
	}

	const value = doc[field];
	if (value === undefined || value === null || value === "") {
		return 0;
	}

	if (!conversion_rate) {
		conversion_rate = get_conversion_rate(doc);
	}

	return flt(value) * flt(conversion_rate || 1);
};
