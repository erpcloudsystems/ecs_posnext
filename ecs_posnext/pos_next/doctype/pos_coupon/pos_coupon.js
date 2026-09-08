// Copyright (c) 2021, Youssef Restom and contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Coupon", {
	setup: function (frm) {
		frm.set_query("pos_offer", function () {
			return {
				filters: {
					company: frm.doc.company,
					coupon_based: 1,
					disable: 0,
				},
			};
		});
	},
	coupon_name: function (frm) {
		if (frm.doc.__islocal === 1) {
			frm.trigger("make_coupon_code");
		}
	},
	coupon_type: function (frm) {
		if (frm.doc.__islocal === 1) {
			frm.trigger("make_coupon_code");
		}
	},
	make_coupon_code: function (frm) {
		var coupon_name = frm.doc.coupon_name;
		var coupon_code;
		if (frm.doc.coupon_type == "Gift Card") {
			coupon_code = Math.random().toString(12).substring(2, 12).toUpperCase();
		} else if (frm.doc.coupon_type == "Promotional") {
			coupon_name = coupon_name.replace(/\s/g, "");
			coupon_code = coupon_name.toUpperCase().slice(0, 8);
		}
		frm.doc.coupon_code = coupon_code;
		frm.refresh_field("coupon_code");
	},
	refresh: function (frm) {
		if (frm.doc.pricing_rule) {
			frm.add_custom_button(__("Add/Edit Coupon Conditions"), function () {
				frappe.set_route("Form", "POS Offer", frm.doc.pos_offer);
			});
		}
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Usage"), function () {
				frappe.set_route("query-report", "POS Coupon Usage", {
					company: frm.doc.company,
					coupon_code: frm.doc.coupon_code,
					// The report defaults to the last month; a coupon's own history
					// should show in full regardless of when it was redeemed.
					from_date: frm.doc.valid_from || frappe.datetime.add_months(frm.doc.creation, -1),
					to_date: frappe.datetime.get_today(),
				});
			});
		}
	},
});
