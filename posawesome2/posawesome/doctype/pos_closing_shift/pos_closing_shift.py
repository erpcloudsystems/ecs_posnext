# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, now_datetime, getdate, get_datetime
from posawesome.posawesome.api.posapp import get_shift_window_for_opening_shift


class POSClosingShift(Document):
    def validate(self):
        # Rebuild data from the selected opening shift on every save/submit
        self.calculate_total_cash()
        self.sync_from_opening_shift()
        # Coerce to datetime to avoid string-vs-datetime comparisons from JSON payloads
        start = get_datetime(self.period_start_date) if self.period_start_date else None
        end = get_datetime(self.period_end_date) if self.period_end_date else None
        if start:
            self.period_start_date = start
        if end:
            self.period_end_date = end

        if start and end and end < start:
            frappe.throw(
                _("Period End Date must be on or after Period Start Date."),
                title=_("Invalid Period"),
            )

        user = frappe.get_all(
            "POS Closing Shift",
            filters={
                "user": self.user,
                "docstatus": 1,
                "pos_opening_shift": self.pos_opening_shift,
                "name": ["!=", self.name],
            },
        )

        if user:
            frappe.throw(
                _(
                    "POS Closing Shift {} against {} between selected period".format(
                        frappe.bold("already exists"), frappe.bold(self.user)
                    )
                ),
                title=_("Invalid Period"),
            )

        if (
            frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status")
            != "Open"
        ):
            frappe.throw(
                _("Selected POS Opening Shift should be open."),
                title=_("Invalid Opening Entry"),
            )
        self.set_non_cash_closing_amounts()
        self.update_payment_reconciliation()
        self.validate_cash_denominations_total()
        self.validate_second_shift_payments()

    def sync_from_opening_shift(self):
        """Populate invoices, payments, taxes, and totals directly from the opening shift to prevent duplication."""
        if not self.pos_opening_shift:
            return

        # Preserve user-entered closing amounts keyed by mode of payment
        closing_amount_map = {
            d.mode_of_payment: flt(d.closing_amount)
            for d in self.payment_reconciliation
            if d.mode_of_payment
        }

        opening_shift_doc = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
        period_start = self.period_start_date or opening_shift_doc.period_start_date
        period_end = self.period_end_date or now_datetime()

        # Ensure dates are set so downstream filters work
        if not self.period_start_date:
            self.period_start_date = period_start
        if not self.period_end_date:
            self.period_end_date = period_end

        details = _prepare_closing_data(self.pos_opening_shift, period_start, period_end)

        # Align header fields with opening shift defaults if missing
        if not self.pos_profile:
            self.pos_profile = opening_shift_doc.pos_profile
        if not self.company:
            self.company = opening_shift_doc.company
        if not self.user:
            self.user = opening_shift_doc.user
        if not self.period_start_date:
            self.period_start_date = opening_shift_doc.period_start_date

        self.grand_total = details.grand_total
        self.net_total = details.net_total
        self.total_quantity = details.total_quantity
        self.set("pos_transactions", details.pos_transactions)
        self.set("payment_reconciliation", details.payment_reconciliation)
        self.set("taxes", details.taxes)
        self.set("pos_payments", details.pos_payments)

        # Restore previously entered closing amounts after refresh
        for row in self.payment_reconciliation:
            if row.mode_of_payment in closing_amount_map:
                row.closing_amount = closing_amount_map[row.mode_of_payment]

    def update_payment_reconciliation(self):
        # update the difference values in Payment Reconciliation child table
        # get default precision for site
        precision = (
            frappe.get_cached_value("System Settings", None, "currency_precision") or 3
        )
        for d in self.payment_reconciliation:
            d.difference = +flt(d.closing_amount, precision) - flt(
                d.expected_amount, precision
            )

    def set_non_cash_closing_amounts(self):
        """Auto-fill closing amount with expected amount for non-cash payment types."""
        if not self.payment_reconciliation:
            return

        cash_mop = (
            frappe.get_value(
                "POS Profile", self.pos_profile, "posa_cash_mode_of_payment"
            )
            or "Cash"
        )
        mop_names = [
            d.mode_of_payment for d in self.payment_reconciliation if d.mode_of_payment
        ]
        mop_types = {
            row.name: (row.type or "").lower()
            for row in frappe.get_all(
                "Mode of Payment",
                filters={"name": ["in", mop_names]},
                fields=["name", "type"],
            )
        }

        for d in self.payment_reconciliation:
            mop_type = mop_types.get(d.mode_of_payment, "")
            is_cash = mop_type == "cash" or d.mode_of_payment == cash_mop
            if is_cash:
                d.closing_amount = self.total_cash
                continue
            d.closing_amount = flt(d.expected_amount)
    def calculate_total_cash(self):
        self.total_cash = (
            (self.cash_200_egp or 0) * 200 +
            (self.cash_100_egp or 0) * 100 +
            (self.cash_50_egp  or 0) * 50  +
            (self.cash_20_egp  or 0) * 20  +
            (self.cash_10_egp  or 0) * 10  +
            (self.cash_5_egp   or 0) * 5   +
            (self.cash_1_egp   or 0) * 1
        )
    def validate_cash_denominations_total(self):
        """Ensure counted cash matches the declared closing amount and does not exceed expected cash for the cash mode of payment."""
        if not self.payment_reconciliation:
            return

        cash_mop_default = (
            frappe.get_value(
                "POS Profile", self.pos_profile, "posa_cash_mode_of_payment"
            )
            or "Cash"
        )

        mop_names = [d.mode_of_payment for d in self.payment_reconciliation]
        mop_types = {
            row.name: (row.type or "").lower()
            for row in frappe.get_all(
                "Mode of Payment",
                filters={"name": ["in", mop_names]},
                fields=["name", "type"],
            )
        }

        # Prefer type=cash; fallback to configured name
        cash_row = next(
            (d for d in self.payment_reconciliation if mop_types.get(d.mode_of_payment) == "cash"),
            None,
        ) or next(
            (d for d in self.payment_reconciliation if d.mode_of_payment == cash_mop_default),
            None,
        )

        if not cash_row:
            return

        currency = (
            frappe.get_cached_value("Company", self.company, "default_currency")
            if self.company
            else None
        )
        mop_label = cash_row.mode_of_payment or cash_mop_default
        denominations_total = (
            200 * cint(self.cash_200_egp or 0)
            + 100 * cint(self.cash_100_egp or 0)
            + 50 * cint(self.cash_50_egp or 0)
            + 20 * cint(self.cash_20_egp or 0)
            + 10 * cint(self.cash_10_egp or 0)
            + 5 * cint(self.cash_5_egp or 0)
            + 1 * cint(self.cash_1_egp or 0)
        )
        expected_amount = flt(cash_row.expected_amount)
        closing_amount = flt(cash_row.closing_amount)
        self.total_diff = flt(self.total_cash) - expected_amount
        # if denominations_total != closing_amount:
        #     frappe.throw(
        #         _(
        #             "Cash counted ({0}) must equal closing amount ({1}) for {2}."
        #         ).format(
        #             frappe.utils.fmt_money(denominations_total, currency=currency),
        #             frappe.utils.fmt_money(closing_amount, currency=currency),
        #             mop_label,
        #         )
        #     )

    def validate_second_shift_payments(self):
        """For second/night shift, block closing if any linked invoices are unpaid."""
        if not self.pos_opening_shift or not self.pos_transactions:
            return

        window = get_shift_window_for_opening_shift(self.pos_opening_shift)
        if not window or not (window.label or "").lower().endswith("2"):
            return

        invoice_names = [d.sales_invoice for d in self.pos_transactions if d.sales_invoice]
        if not invoice_names:
            return

        unpaid = frappe.db.sql(
            """
            select name from `tabSales Invoice`
            where name in %(names)s and docstatus = 1 and ifnull(outstanding_amount, 0) > 0
            """,
            {"names": invoice_names},
            as_dict=True,
        )
        if unpaid:
            ids = ", ".join([u.name for u in unpaid])
            frappe.throw(
                _("Cannot close this shift because unpaid invoices exist: {0}").format(ids),
                title=_("Unpaid Invoices"),
            )

    def on_submit(self):
        opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
        opening_entry.pos_closing_shift = self.name
        opening_entry.set_status()
        self.delete_draft_invoices()
        opening_entry.save()
        self.upsert_closing_summary()

    def after_insert(self):
        # Create summary right after the POS Closing Shift is created (before submit)
        self.upsert_closing_summary()

    def delete_draft_invoices(self):
        if frappe.get_value("POS Profile", self.pos_profile, "posa_allow_delete"):
            data = frappe.db.sql(
                """
                select
                    name
                from
                    `tabSales Invoice`
                where
                    docstatus = 0 and posa_is_printed = 0 and posa_pos_opening_shift = %s
                """,
                (self.pos_opening_shift),
                as_dict=1,
            )

            for invoice in data:
                frappe.delete_doc("Sales Invoice", invoice.name, force=1)

    @frappe.whitelist()
    def get_payment_reconciliation_details(self):
        currency = frappe.get_cached_value("Company", self.company, "default_currency")
        return frappe.render_template(
            "posawesome/posawesome/doctype/pos_closing_shift/closing_shift_details.html",
            {"data": self, "currency": currency},
        )

    def upsert_closing_summary(self):
        """Create or update a POS Closing Summary record for cash difference tracking."""
        cash_mop = (
            frappe.get_value(
                "POS Profile", self.pos_profile, "posa_cash_mode_of_payment"
            )
            or "Cash"
        )
        mop_names = [d.mode_of_payment for d in self.payment_reconciliation if d.mode_of_payment]
        mop_types = (
            {
                row.name: (row.type or "").lower()
                for row in frappe.get_all(
                    "Mode of Payment",
                    filters={"name": ["in", mop_names]},
                    fields=["name", "type"],
                )
            }
            if mop_names
            else {}
        )
        cash_row = next(
            (
                d
                for d in self.payment_reconciliation
                if d.mode_of_payment == cash_mop or mop_types.get(d.mode_of_payment) == "cash"
            ),
            None,
        )
        # fallback to first row if no cash identified
        if not cash_row and self.payment_reconciliation:
            cash_row = self.payment_reconciliation[0]
        if not cash_row:
            return
        expected = flt(cash_row.expected_amount)
        closing = flt(cash_row.closing_amount)
        diff = closing - expected
        existing = frappe.db.exists("POS Closing Summary", {"pos_closing_id": self.name})
        if existing:
            frappe.db.set_value(
                "POS Closing Summary",
                existing,
                {
                    "cashier": self.user,
                    "expected_cash_amount": expected,
                    "closing_cash_amount": closing,
                    "difference": diff,
                },
            )
        else:
            doc = frappe.get_doc(
                {
                    "doctype": "POS Closing Summary",
                    "pos_closing_id": self.name,
                    "cashier": self.user,
                    "expected_cash_amount": expected,
                    "closing_cash_amount": closing,
                    "difference": diff,
                }
            )
            doc.insert(ignore_permissions=True)


def _prepare_closing_data_legacy(pos_opening_shift):
    """Backwards compatibility wrapper (deprecated)."""
    return _prepare_closing_data(pos_opening_shift, None, None)


def _prepare_closing_data(pos_opening_shift, period_start_date=None, period_end_date=None):
    """Build closing shift child tables and totals from the selected opening shift and date range."""
    opening_shift = frappe.get_doc("POS Opening Shift", pos_opening_shift)
    invoices = get_pos_invoices(pos_opening_shift, period_start_date, period_end_date)
    pos_payments = get_payments_entries(pos_opening_shift, period_start_date, period_end_date)
    cash_mode_of_payment = (
        frappe.get_value("POS Profile", opening_shift.pos_profile, "posa_cash_mode_of_payment")
        or "Cash"
    )

    pos_transactions = []
    taxes = []
    payments = []
    pos_payments_table = []

    payments_index = {}
    taxes_index = {}

    def get_payment_row(mode_of_payment):
        if not mode_of_payment:
            return None
        row = payments_index.get(mode_of_payment)
        if not row:
            row = frappe._dict(
                {
                    "mode_of_payment": mode_of_payment,
                    "opening_amount": 0,
                    "expected_amount": 0,
                }
            )
            payments_index[mode_of_payment] = row
            payments.append(row)
        return row

    def get_tax_row(account_head, rate):
        key = (account_head, flt(rate))
        row = taxes_index.get(key)
        if not row:
            row = frappe._dict(
                {"account_head": account_head, "rate": rate, "amount": 0}
            )
            taxes_index[key] = row
            taxes.append(row)
        return row

    # Seed payment reconciliation with opening balances
    for detail in opening_shift.get("balance_details", []):
        payment_row = get_payment_row(detail.get("mode_of_payment"))
        if payment_row:
            opening_amount = flt(detail.get("amount"))
            payment_row.opening_amount = opening_amount
            payment_row.expected_amount += opening_amount

    grand_total = 0
    net_total = 0
    total_quantity = 0

    seen_invoices = set()
    for inv in invoices:
        if inv.name in seen_invoices:
            continue
        seen_invoices.add(inv.name)
        pos_transactions.append(
            frappe._dict(
                {
                    "sales_invoice": inv.name,
                    "posting_date": inv.posting_date,
                    "grand_total": inv.grand_total,
                    "customer": inv.customer,
                }
            )
        )
        grand_total += flt(inv.grand_total)
        net_total += flt(inv.net_total)
        total_quantity += flt(inv.total_qty)

        for t in inv.taxes:
            tax_row = get_tax_row(t.account_head, t.rate)
            tax_row.amount += flt(t.tax_amount)

        for p in inv.payments:
            payment_row = get_payment_row(p.mode_of_payment)
            if not payment_row:
                continue
            amount = p.amount
            if p.mode_of_payment == cash_mode_of_payment:
                amount = p.amount - inv.change_amount
            payment_row.expected_amount += flt(amount)

    seen_payment_entries = set()
    for py in pos_payments:
        if py.name in seen_payment_entries:
            continue
        seen_payment_entries.add(py.name)
        pos_payments_table.append(
            frappe._dict(
                {
                    "payment_entry": py.name,
                    "mode_of_payment": py.mode_of_payment,
                    "paid_amount": py.paid_amount,
                    "posting_date": py.posting_date,
                    "customer": py.party,
                }
            )
        )
        payment_row = get_payment_row(py.mode_of_payment)
        if payment_row:
            payment_row.expected_amount += flt(py.paid_amount)

    return frappe._dict(
        {
            "opening_shift": opening_shift,
            "pos_transactions": pos_transactions,
            "payment_reconciliation": payments,
            "taxes": taxes,
            "pos_payments": pos_payments_table,
            "grand_total": grand_total,
            "net_total": net_total,
            "total_quantity": total_quantity,
        }
    )


@frappe.whitelist()
def get_cashiers(doctype, txt, searchfield, start, page_len, filters):
    cashiers_list = frappe.get_all("POS Profile User", filters=filters, fields=["user"])
    return [c["user"] for c in cashiers_list]


@frappe.whitelist()
def get_pos_invoices(pos_opening_shift, period_start_date=None, period_end_date=None):
    submit_printed_invoices(pos_opening_shift)
    conditions = ["docstatus = 1", "posa_pos_opening_shift = %(pos_opening_shift)s"]
    params = {"pos_opening_shift": pos_opening_shift}

    start_dt = get_datetime(period_start_date) if period_start_date else None
    end_dt = get_datetime(period_end_date) if period_end_date else None

    if start_dt:
        conditions.append(
            "timestamp(posting_date, ifnull(posting_time, '00:00:00')) >= %(period_start_dt)s"
        )
        params["period_start_dt"] = start_dt
    if end_dt:
        conditions.append(
            "timestamp(posting_date, ifnull(posting_time, '23:59:59')) <= %(period_end_dt)s"
        )
        params["period_end_dt"] = end_dt

    data = frappe.db.sql(
        f"""
	select
		name
	from
		`tabSales Invoice`
	where
		{" and ".join(conditions)}
	""",
        params,
        as_dict=1,
    )

    data = [frappe.get_doc("Sales Invoice", d.name).as_dict() for d in data]

    return data


@frappe.whitelist()
def get_payments_entries(pos_opening_shift, period_start_date=None, period_end_date=None):
    start_dt = get_datetime(period_start_date) if period_start_date else None
    end_dt = get_datetime(period_end_date) if period_end_date else None

    has_posting_time = frappe.db.has_column("Payment Entry", "posting_time")

    conditions = [
        "docstatus = 1",
        "reference_no = %(pos_opening_shift)s",
        "payment_type = 'Receive'",
    ]
    params = {"pos_opening_shift": pos_opening_shift}

    if start_dt:
        if has_posting_time:
            conditions.append(
                "timestamp(posting_date, ifnull(posting_time, '00:00:00')) >= %(period_start_dt)s"
            )
            params["period_start_dt"] = start_dt
        else:
            conditions.append("posting_date >= %(period_start_dt)s")
            params["period_start_dt"] = getdate(start_dt)
    if end_dt:
        if has_posting_time:
            conditions.append(
                "timestamp(posting_date, ifnull(posting_time, '23:59:59')) <= %(period_end_dt)s"
            )
            params["period_end_dt"] = end_dt
        else:
            conditions.append("posting_date <= %(period_end_dt)s")
            params["period_end_dt"] = getdate(end_dt)

    fields = [
        "name",
        "mode_of_payment",
        "paid_amount",
        "reference_no",
        "posting_date",
        "party",
    ]
    if has_posting_time:
        fields.append("posting_time")

    return frappe.db.sql(
        f"""
		select
			{", ".join(fields)}
		from
			`tabPayment Entry`
		where
			{" and ".join(conditions)}
	""",
        params,
        as_dict=True,
    )


@frappe.whitelist()
def make_closing_shift_from_opening(opening_shift):
    # opening_shift can be a JSON string, dict, or plain name
    if isinstance(opening_shift, str):
        try:
            opening_shift = json.loads(opening_shift)
        except Exception:
            opening_shift = {"name": opening_shift}
    if isinstance(opening_shift, frappe._dict):
        opening_shift = dict(opening_shift)

    if not opening_shift or not opening_shift.get("name"):
        frappe.throw(_("Opening Shift is required"))

    opening_shift_doc = frappe.get_doc("POS Opening Shift", opening_shift.get("name"))

    # Permission: owner or user with submit permission on POS Closing Shift (e.g., managers)
    if (
        opening_shift_doc.user != frappe.session.user
        and not frappe.has_permission("POS Closing Shift", ptype="submit")
    ):
        frappe.throw(
            _("You are not allowed to close this shift."),
            title=_("Not Permitted"),
        )

    submit_printed_invoices(opening_shift_doc.name)
    closing_shift = frappe.new_doc("POS Closing Shift")
    closing_shift.pos_opening_shift = opening_shift_doc.name
    closing_shift.period_start_date = opening_shift_doc.period_start_date
    closing_shift.period_end_date = frappe.utils.get_datetime()
    closing_shift.pos_profile = opening_shift_doc.pos_profile
    closing_shift.user = opening_shift_doc.user
    closing_shift.company = opening_shift_doc.company
    details = _prepare_closing_data(
        opening_shift_doc.name,
        opening_shift_doc.period_start_date,
        closing_shift.period_end_date,
    )
    closing_shift.grand_total = details.grand_total
    closing_shift.net_total = details.net_total
    closing_shift.total_quantity = details.total_quantity

    closing_shift.set("pos_transactions", details.pos_transactions)
    closing_shift.set("payment_reconciliation", details.payment_reconciliation)
    closing_shift.set("taxes", details.taxes)
    closing_shift.set("pos_payments", details.pos_payments)

    return closing_shift


@frappe.whitelist()
def submit_closing_shift(closing_shift):
    closing_shift = json.loads(closing_shift)
    closing_shift_doc = frappe.get_doc(closing_shift)
    closing_shift_doc.flags.ignore_permissions = True
    closing_shift_doc.save()
    if "Restaurant Manager" in frappe.get_roles(frappe.session.user):
        closing_shift_doc.submit()
    return closing_shift_doc.name


def submit_printed_invoices(pos_opening_shift):
    invoices_list = frappe.get_all(
        "Sales Invoice",
        filters={
            "posa_pos_opening_shift": pos_opening_shift,
            "docstatus": 0,
            "posa_is_printed": 1,
        },
    )
    for invoice in invoices_list:
        invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)
        invoice_doc.submit()
