// Copyright (c) 2020, Youssef Restom and contributors
// For license information, please see license.txt
frappe.ui.form.on("POS Closing Shift", {
  on_submit(frm) {
    const diff = flt(frm.doc.total_diff || 0);
    const abs_diff = Math.abs(diff);
    if (
      diff !== 0 &&
      (!frm.doc.difference_reason || !frm.doc.difference_reason.trim())
    ) {
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
    } else {
      frappe.msgprint({
        title: "الإقفال",
        message: `عجز ❌ بمبلغ ${format_currency(abs_diff, "EGP")}`,
        indicator: "red",
      });
    }
  },
  before_submit(frm) {
    return new Promise((resolve, reject) => {
      frappe.confirm(
        `
                <b>إجمالي النقدية:</b> ${frm.doc.total_cash} جنيه<br><br>
                هل أنت متأكد من اعتماد المستند؟
                `,
        () => resolve(),
        () => reject(),
      );
    });
  },
});
frappe.ui.form.on("POS Closing Shift", {
  cash_200_egp: calculate_total_cash,
  cash_100_egp: calculate_total_cash,
  cash_50_egp: calculate_total_cash,
  cash_20_egp: calculate_total_cash,
  cash_10_egp: calculate_total_cash,
  cash_5_egp: calculate_total_cash,
  cash_1_egp: calculate_total_cash,
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
}
frappe.ui.form.on("POS Closing Shift", {
  onload: function (frm) {
    frm.set_query("pos_profile", function (doc) {
      return {
        filters: { user: doc.user },
      };
    });

    frm.set_query("user", function (doc) {
      return {
        query:
          "posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.get_cashiers",
        filters: { parent: doc.pos_profile },
      };
    });

    frm.set_query("pos_opening_shift", function (doc) {
      return { filters: { status: "Open", docstatus: 1 } };
    });

    if (frm.doc.docstatus === 0)
      frm.set_value("period_end_date", frappe.datetime.now_datetime());
    if (frm.doc.docstatus === 1) set_html_data(frm);
  },

  before_save(frm) {
    if (frm.doc.docstatus !== 0) return;
    return refresh_shift_data(frm);
  },

  set_opening_amounts(frm) {
    return frappe.db
      .get_doc("POS Opening Shift", frm.doc.pos_opening_shift)
      .then(({ balance_details }) => {
        balance_details.forEach((detail) => {
          frm.add_child("payment_reconciliation", {
            mode_of_payment: detail.mode_of_payment,
            opening_amount: detail.amount || 0,
            expected_amount: detail.amount || 0,
          });
        });
      });
  },

  get_pos_invoices(frm) {
    return frappe
      .call({
        method:
          "posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.get_pos_invoices",
        args: {
          pos_opening_shift: frm.doc.pos_opening_shift,
          period_start_date: frm.doc.period_start_date,
          period_end_date: frm.doc.period_end_date,
        },
      })
      .then((r) => {
        let pos_docs = r.message || [];
        set_form_data(pos_docs, frm);
      });
  },

  get_pos_payments(frm) {
    return frappe
      .call({
        method:
          "posawesome.posawesome.doctype.pos_closing_shift.pos_closing_shift.get_payments_entries",
        args: {
          pos_opening_shift: frm.doc.pos_opening_shift,
          period_start_date: frm.doc.period_start_date,
          period_end_date: frm.doc.period_end_date,
        },
      })
      .then((r) => {
        let pos_payments = r.message || [];
        set_form_payments_data(pos_payments, frm);
      });
  },
});

frappe.ui.form.on("POS Closing Shift Detail", {
  closing_amount: (frm, cdt, cdn) => {
    const row = locals[cdt][cdn];
    frappe.model.set_value(
      cdt,
      cdn,
      "difference",
      flt(row.closing_amount) - flt(row.expected_amount),
    );
  },
});

function set_form_data(data, frm) {
  const seenInvoices = new Set(
    frm.doc.pos_transactions.map((row) => row.sales_invoice),
  );
  data.forEach((d) => {
    if (seenInvoices.has(d.name)) return;
    seenInvoices.add(d.name);
    add_to_pos_transaction(d, frm);
    frm.doc.grand_total += flt(d.grand_total);
    frm.doc.net_total += flt(d.net_total);
    frm.doc.total_quantity += flt(d.total_qty);
    add_to_payments(d, frm);
    add_to_taxes(d, frm);
  });
}

function set_form_payments_data(data, frm) {
  const seenPayments = new Set(
    frm.doc.pos_payments.map((row) => row.payment_entry),
  );
  data.forEach((d) => {
    if (seenPayments.has(d.name)) return;
    seenPayments.add(d.name);
    add_to_pos_payments(d, frm);
    add_pos_payment_to_payments(d, frm);
  });
}

function add_to_pos_transaction(d, frm) {
  frm.add_child("pos_transactions", {
    sales_invoice: d.name,
    posting_date: d.posting_date,
    grand_total: d.grand_total,
    customer: d.customer,
  });
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

function add_to_payments(d, frm) {
  d.payments.forEach((p) => {
    const payment = frm.doc.payment_reconciliation.find(
      (pay) => pay.mode_of_payment === p.mode_of_payment,
    );
    if (payment) {
      let amount = p.amount;
      let cash_mode_of_payment = get_value(
        "POS Profile",
        frm.doc.pos_profile,
        "posa_cash_mode_of_payment",
      );
      if (!cash_mode_of_payment) {
        cash_mode_of_payment = "Cash";
      }
      if (payment.mode_of_payment == cash_mode_of_payment) {
        amount = p.amount - d.change_amount;
      }
      payment.expected_amount += flt(amount);
    } else {
      frm.add_child("payment_reconciliation", {
        mode_of_payment: p.mode_of_payment,
        opening_amount: 0,
        expected_amount: p.amount || 0,
      });
    }
  });
}

function add_pos_payment_to_payments(p, frm) {
  const payment = frm.doc.payment_reconciliation.find(
    (pay) => pay.mode_of_payment === p.mode_of_payment,
  );
  if (payment) {
    let amount = p.paid_amount;
    payment.expected_amount += flt(amount);
  } else {
    frm.add_child("payment_reconciliation", {
      mode_of_payment: p.mode_of_payment,
      opening_amount: 0,
      expected_amount: p.amount || 0,
    });
  }
}

function add_to_taxes(d, frm) {
  d.taxes.forEach((t) => {
    const tax = frm.doc.taxes.find(
      (tx) => tx.account_head === t.account_head && tx.rate === t.rate,
    );
    if (tax) {
      tax.amount += flt(t.tax_amount);
    } else {
      frm.add_child("taxes", {
        account_head: t.account_head,
        rate: t.rate,
        amount: t.tax_amount,
      });
    }
  });
}

function reset_values(frm) {
  frm.set_value("pos_transactions", []);
  frm.set_value("payment_reconciliation", []);
  frm.set_value("pos_payments", []);
  frm.set_value("taxes", []);
  frm.set_value("grand_total", 0);
  frm.set_value("net_total", 0);
  frm.set_value("total_quantity", 0);
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
  frappe.call({
    method: "get_payment_reconciliation_details",
    doc: frm.doc,
    callback: (r) => {
      frm.get_field("payment_reconciliation_details").$wrapper.html(r.message);
    },
  });
}

const get_value = (doctype, name, field) => {
  let value;
  frappe.call({
    method: "frappe.client.get_value",
    args: {
      doctype: doctype,
      filters: { name: name },
      fieldname: field,
    },
    async: false,
    callback: function (r) {
      if (!r.exc) {
        value = r.message[field];
      }
    },
  });
  return value;
};

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
      },
    ]);
  }
}
