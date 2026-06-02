// Copyright (c) 2020, Youssef Restom and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Opening Shift", {
  setup(frm) {
    if (frm.doc.docstatus == 0) {
      frm.trigger("set_posting_date_read_only");
      frm.set_value("period_start_date", frappe.datetime.now_datetime());
      frm.set_value("user", frappe.session.user);
    }
    frm.set_query("user", function (doc) {
      return {
        query:
          "ecs_posnext.ecs_posnext.doctype.pos_closing_shift.pos_closing_shift.get_cashiers",
        filters: { parent: doc.pos_profile },
      };
    });
    frm.set_query("pos_profile", function (doc) {
      return {
        filters: { company: doc.company },
      };
    });
  },

  refresh(frm) {
    // set default posting date / time
    if (frm.doc.docstatus == 0) {
      if (!frm.doc.posting_date) {
        frm.set_value("posting_date", frappe.datetime.nowdate());
      }
      frm.trigger("set_posting_date_read_only");
    }

    if (
      frm.doc.docstatus === 1 &&
      frm.doc.status === "Open" &&
      (frm.doc.user === frappe.session.user ||
        frappe.user.has_role("System Manager") ||
        frappe.user.has_role("Assistant branch manager") ||
        frappe.user.has_role("Branch supervisor") ||
        frappe.user.has_role("Bransh Manager"))
    ) {
      frm.add_custom_button(__("Close Shift"), () => {
        frappe.call({
          method:
            "ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift.make_closing_shift_from_opening",
          args: { opening_shift: JSON.stringify(frm.doc) },
          callback: (r) => {
            if (r.message) {
              const doc = frappe.model.sync(r.message)[0];
              frappe.set_route("Form", doc.doctype, doc.name);
            }
          },
          error: () => {
            frappe.msgprint(
              __("Unable to create closing shift from this opening shift.")
            );
          },
        });
      });
    }
  },

  set_posting_date_read_only(frm) {
    if (frm.doc.docstatus == 0 && frm.doc.set_posting_date) {
      frm.set_df_property("posting_date", "read_only", 0);
    } else {
      frm.set_df_property("posting_date", "read_only", 1);
    }
  },

  set_posting_date(frm) {
    frm.trigger("set_posting_date_read_only");
  },

  pos_profile: (frm) => {
    if (frm.doc.pos_profile) {
      frappe.db
        .get_doc("POS Profile", frm.doc.pos_profile)
        .then(({ payments }) => {
          if (payments.length) {
            frm.doc.balance_details = [];
            payments.forEach(({ mode_of_payment }) => {
              frm.add_child("balance_details", { mode_of_payment });
            });
            frm.refresh_field("balance_details");
          }
        });
    }
  },
});
