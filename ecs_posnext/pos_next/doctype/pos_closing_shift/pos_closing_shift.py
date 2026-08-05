# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

import json
from collections import defaultdict

import frappe
from erpnext.accounts.doctype.pos_invoice_merge_log.pos_invoice_merge_log import (
    consolidate_pos_invoices,
)
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


def get_base_value(doc, fieldname, base_fieldname=None, conversion_rate=None):
    """Return the value for a field in company currency."""

    base_fieldname = base_fieldname or f"base_{fieldname}"
    base_value = doc.get(base_fieldname)

    if base_value not in (None, ""):
        return flt(base_value)

    value = doc.get(fieldname)
    if value in (None, ""):
        return 0

    if conversion_rate is None:
        conversion_rate = (
            doc.get("conversion_rate")
            or doc.get("exchange_rate")
            or doc.get("target_exchange_rate")
            or doc.get("plc_conversion_rate")
            or 1
        )

    return flt(value) * flt(conversion_rate or 1)


class POSClosingShift(Document):
    def validate(self):
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
                    "POS Closing Shift <strong>already exists</strong> against {0} between selected period".format(
                        frappe.bold(self.user)
                    )
                ),
                title=_("Invalid Period"),
            )

        if frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status") != "Open":
            frappe.throw(
                _("Selected POS Opening Shift should be open."),
                title=_("Invalid Opening Entry"),
            )
        self.validate_closing_amounts()
        self.update_payment_reconciliation()
        self._compute_daily_payments_and_tip()

    def validate_closing_amounts(self):
        """Every payment method must have an actual counted amount greater than zero."""
        precision = frappe.get_cached_value("System Settings", None, "currency_precision") or 3
        invalid_modes = [
            d.mode_of_payment
            for d in self.payment_reconciliation
            if flt(d.closing_amount, precision) <= 0
        ]

        if invalid_modes:
            frappe.throw(
                _(
                    "Actual counted amount must be greater than 0 for the following payment methods: {0}"
                ).format(frappe.bold(", ".join(invalid_modes))),
                title=_("Invalid Closing Amount"),
            )

    def update_payment_reconciliation(self):
        # update the difference values in Payment Reconciliation child table
        # get default precision for site
        precision = frappe.get_cached_value("System Settings", None, "currency_precision") or 3
        for d in self.payment_reconciliation:
            d.difference = +flt(d.closing_amount, precision) - flt(d.expected_amount, precision)

    def _compute_daily_payments_and_tip(self):
        totals = _get_opening_shift_totals(self.pos_opening_shift)
        self.total_daily_payments = totals["total_daily_payments"]
        self.total_tip = totals["total_tip"]
        visa_amount = sum(
            flt(r.expected_amount) - flt(r.opening_amount)
            for r in self.payment_reconciliation
            if r.mode_of_payment == "بنك CIB فيزا"
        )
        self.actual_amount = (
            flt(self.grand_total) - visa_amount
            - flt(self.total_daily_payments) - flt(self.total_tip)
        )
        visa_amount = sum(
            flt(r.expected_amount) - flt(r.opening_amount)
            for r in self.payment_reconciliation
            if r.mode_of_payment == "بنك CIB فيزا"
        )
        self.actual_amount = (
            flt(self.grand_total) - visa_amount
            - flt(self.total_daily_payments) - flt(self.total_tip)
        )

    def on_submit(self):
        opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
        opening_entry.pos_closing_shift = self.name
        opening_entry.set_status()
        self.delete_draft_invoices()
        opening_entry.save()
        # link invoices with this closing shift so ERPNext can block edits
        self._set_closing_entry_invoices()

    def on_cancel(self):
        if frappe.db.exists("POS Opening Shift", self.pos_opening_shift):
            opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
            if opening_entry.pos_closing_shift == self.name:
                opening_entry.pos_closing_shift = ""
                opening_entry.set_status()
                opening_entry.save()
        # remove links from invoices so they can be cancelled
        self._clear_closing_entry_invoices()

    def _set_closing_entry_invoices(self):
        """Set `pos_closing_entry` on linked invoices."""
        for d in self.pos_transactions:
            invoice = d.get("sales_invoice") or d.get("pos_invoice")
            if not invoice:
                continue
            doctype = "Sales Invoice" if d.get("sales_invoice") else "POS Invoice"
            if frappe.db.has_column(doctype, "pos_closing_entry"):
                frappe.db.set_value(doctype, invoice, "pos_closing_entry", self.name)

    def _clear_closing_entry_invoices(self):
        """Clear closing shift links, cancel merge logs and cancel consolidated sales invoices."""
        consolidated_sales_invoices = set()
        for d in self.pos_transactions:
            pos_invoice = d.get("pos_invoice")
            sales_invoice = d.get("sales_invoice")
            if pos_invoice:
                if frappe.db.has_column("POS Invoice", "pos_closing_entry"):
                    frappe.db.set_value("POS Invoice", pos_invoice, "pos_closing_entry", None)

                merge_logs = frappe.get_all(
                    "POS Invoice Merge Log",
                    filters={"pos_invoice": pos_invoice},
                    pluck="name",
                )
                for log in merge_logs:
                    log_doc = frappe.get_doc("POS Invoice Merge Log", log)
                    for field in (
                        "consolidated_invoice",
                        "consolidated_credit_note",
                    ):
                        si = log_doc.get(field)
                        if si:
                            consolidated_sales_invoices.add(si)
                    if log_doc.docstatus == 1:
                        log_doc.cancel()
                    frappe.delete_doc("POS Invoice Merge Log", log_doc.name, force=1)

                if frappe.db.has_column("POS Invoice", "consolidated_invoice"):
                    frappe.db.set_value("POS Invoice", pos_invoice, "consolidated_invoice", None)

                if frappe.db.has_column("POS Invoice", "status"):
                    pos_doc = frappe.get_doc("POS Invoice", pos_invoice)
                    pos_doc.set_status(update=True)

            if sales_invoice:
                if frappe.db.has_column("Sales Invoice", "pos_closing_entry"):
                    frappe.db.set_value("Sales Invoice", sales_invoice, "pos_closing_entry", None)
                if self._is_consolidated_sales_invoice(sales_invoice):
                    consolidated_sales_invoices.add(sales_invoice)

        for si in consolidated_sales_invoices:
            if frappe.db.exists("Sales Invoice", si):
                si_doc = frappe.get_doc("Sales Invoice", si)
                if si_doc.docstatus == 1:
                    si_doc.cancel()

    def _is_consolidated_sales_invoice(self, sales_invoice):
        """Return True if the Sales Invoice was generated by consolidating POS Invoices."""

        if not sales_invoice:
            return False

        if frappe.db.exists(
            "POS Invoice Merge Log", {"consolidated_invoice": sales_invoice}
        ):
            return True

        return bool(
            frappe.db.exists(
                "POS Invoice Merge Log", {"consolidated_credit_note": sales_invoice}
            )
        )

    def delete_draft_invoices(self):
        if frappe.get_value("POS Profile", self.pos_profile, "posa_allow_delete"):
            doctype = "Sales Invoice"
            data = frappe.db.sql(
                f"""
		select
		    name
		from
		    `tab{doctype}`
		where
		    docstatus = 0 and posa_is_printed = 0 and posa_pos_opening_shift = %s
		""",
                (self.pos_opening_shift),
                as_dict=1,
            )

            for invoice in data:
                frappe.delete_doc(doctype, invoice.name, force=1)

    @frappe.whitelist()
    def get_payment_reconciliation_details(self):
        company_currency = frappe.get_cached_value(
            "Company", self.company, "default_currency"
        )

        sales_breakdown = defaultdict(float)
        net_breakdown = defaultdict(float)
        payment_breakdown = {}

        def update_payment_breakdown(mode_of_payment, base_amount=0, currency=None, amount=0):
            if not mode_of_payment:
                return

            row = payment_breakdown.setdefault(
                mode_of_payment,
                {"base": 0.0, "currencies": defaultdict(float)},
            )
            row["base"] += flt(base_amount)
            if currency:
                row["currencies"][currency] += flt(amount)

        cash_mode_of_payment = (
            frappe.db.get_value(
                "POS Profile", self.pos_profile, "posa_cash_mode_of_payment"
            )
            or "Cash"
        )

        for row in self.get("pos_transactions", []):
            invoice = row.get("sales_invoice") or row.get("pos_invoice")
            if not invoice:
                continue

            doctype = "Sales Invoice" if row.get("sales_invoice") else "POS Invoice"
            if not frappe.db.exists(doctype, invoice):
                continue

            invoice_doc = frappe.get_cached_doc(doctype, invoice)
            currency = invoice_doc.get("currency") or company_currency
            conversion_rate = (
                invoice_doc.get("conversion_rate")
                or invoice_doc.get("exchange_rate")
                or invoice_doc.get("target_exchange_rate")
                or invoice_doc.get("plc_conversion_rate")
                or 1
            )

            sales_breakdown[currency] += flt(invoice_doc.get("grand_total") or 0)
            net_breakdown[currency] += flt(invoice_doc.get("net_total") or 0)

            for payment in invoice_doc.get("payments", []):
                update_payment_breakdown(
                    payment.mode_of_payment,
                    get_base_value(payment, "amount", "base_amount", conversion_rate),
                    currency,
                    payment.amount,
                )

            change_amount = invoice_doc.get("change_amount") or 0
            if change_amount:
                update_payment_breakdown(
                    cash_mode_of_payment,
                    -get_base_value(
                        invoice_doc,
                        "change_amount",
                        "base_change_amount",
                        conversion_rate,
                    ),
                    currency,
                    -change_amount,
                )

        for row in self.get("pos_payments", []):
            payment_entry = row.get("payment_entry")
            if not payment_entry or not frappe.db.exists("Payment Entry", payment_entry):
                continue

            payment_doc = frappe.get_cached_doc("Payment Entry", payment_entry)
            currency = (
                payment_doc.get("paid_from_account_currency")
                or payment_doc.get("paid_to_account_currency")
                or payment_doc.get("party_account_currency")
                or payment_doc.get("currency")
                or company_currency
            )
            base_amount = flt(payment_doc.get("base_paid_amount") or 0)
            paid_amount = flt(payment_doc.get("paid_amount") or 0)
            mode_of_payment = row.get("mode_of_payment") or payment_doc.get("mode_of_payment")

            update_payment_breakdown(mode_of_payment, base_amount, currency, paid_amount)

        mode_summaries = []
        payment_breakdown_copy = payment_breakdown.copy()
        for detail in self.get("payment_reconciliation", []):
            mop = detail.mode_of_payment
            breakdown = payment_breakdown_copy.pop(mop, None)
            currencies = []
            if breakdown:
                currencies = [
                    frappe._dict({"currency": currency, "amount": amount})
                    for currency, amount in sorted(breakdown["currencies"].items())
                    if amount
                ]

            base_total = flt(detail.expected_amount) - flt(detail.opening_amount)

            mode_summaries.append(
                frappe._dict(
                    {
                        "mode_of_payment": mop,
                        "base_amount": base_total,
                        "opening_amount": flt(detail.opening_amount),
                        "expected_amount": flt(detail.expected_amount),
                        "difference": flt(detail.difference),
                        "currency_breakdown": currencies,
                    }
                )
            )

        for mop, breakdown in payment_breakdown_copy.items():
            mode_summaries.append(
                frappe._dict(
                    {
                        "mode_of_payment": mop,
                        "base_amount": breakdown["base"],
                        "opening_amount": 0,
                        "expected_amount": breakdown["base"],
                        "difference": 0,
                        "currency_breakdown": [
                            frappe._dict({"currency": currency, "amount": amount})
                            for currency, amount in sorted(breakdown["currencies"].items())
                            if amount
                        ],
                    }
                )
            )

        sales_currency_breakdown = [
            frappe._dict({"currency": currency, "amount": amount})
            for currency, amount in sorted(sales_breakdown.items())
            if amount
        ]
        net_currency_breakdown = [
            frappe._dict({"currency": currency, "amount": amount})
            for currency, amount in sorted(net_breakdown.items())
            if amount
        ]

        totals = _get_opening_shift_totals(self.pos_opening_shift)
        visa_amount = sum(
            flt(s.expected_amount) - flt(s.opening_amount)
            for s in mode_summaries
            if s.mode_of_payment == "بنك CIB فيزا"
        )
        actual_amount = (
            flt(self.grand_total) - visa_amount
            - totals["total_daily_payments"] - totals["total_tip"]
        )

        return frappe.render_template(
            "ecs_posnext/pos_next/doctype/pos_closing_shift/closing_shift_details.html",
            {
                "data": self,
                "currency": company_currency,
                "company_currency": company_currency,
                "mode_summaries": mode_summaries,
                "sales_currency_breakdown": sales_currency_breakdown,
                "net_currency_breakdown": net_currency_breakdown,
                "total_daily_payments": totals["total_daily_payments"],
                "total_tip": totals["total_tip"],
                "actual_amount": actual_amount,
            },
        )


def _get_opening_shift_totals(pos_opening_shift):
    """Return total Daily Payments and total Tip amounts for a POS Opening Shift."""
    # Expense-type Daily Payments keep their amounts in the General Expenses
    # child table and leave the parent `amount` empty, so add both.
    daily_result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(
            COALESCE(dp.amount, 0)
            + CASE WHEN dp.expenses = 1 THEN (
                SELECT COALESCE(SUM(ge.amount), 0)
                FROM `tabGeneral Expenses` ge
                WHERE ge.parent = dp.name AND ge.parenttype = 'Daily Payment'
              ) ELSE 0 END
        ), 0) AS total
        FROM `tabDaily Payment` dp
        WHERE dp.pos_opening_shift = %s AND dp.docstatus = 1
        """,
        (pos_opening_shift,),
        as_dict=True,
    )
    total_daily_payments = flt(daily_result[0].total) if daily_result else 0.0

    tip_result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(sii.amount), 0) AS total
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.posa_pos_opening_shift = %s
          AND si.docstatus = 1
          AND sii.item_code = 'Tip'
        """,
        (pos_opening_shift,),
        as_dict=True,
    )
    total_tip = flt(tip_result[0].total) if tip_result else 0.0

    return {"total_daily_payments": total_daily_payments, "total_tip": total_tip}


@frappe.whitelist()
def get_opening_shift_totals(pos_opening_shift):
    return _get_opening_shift_totals(pos_opening_shift)


@frappe.whitelist()
def get_cashiers(doctype, txt, searchfield, start, page_len, filters):
    cashiers_list = frappe.get_all("POS Profile User", filters=filters, fields=["user"])
    result = []
    for cashier in cashiers_list:
        user_email = frappe.get_value("User", cashier.user, "email")
        if user_email:
            # Return list of tuples in format (value, label) where value is user ID and label shows both ID and email
            result.append([cashier.user, f"{cashier.user} ({user_email})"])
    return result


@frappe.whitelist()
def get_pos_invoices(pos_opening_shift, doctype=None):
    if not doctype:
        pos_profile = frappe.db.get_value("POS Opening Shift", pos_opening_shift, "pos_profile")
        use_pos_invoice = False
        doctype = "POS Invoice" if use_pos_invoice else "Sales Invoice"
    submit_printed_invoices(pos_opening_shift, doctype)
    cond = " and ifnull(consolidated_invoice,'') = ''" if doctype == "POS Invoice" else ""
    data = frappe.db.sql(
        f"""
	select
		name
	from
		`tab{doctype}`
	where
		docstatus = 1 and posa_pos_opening_shift = %s{cond}
	""",
        (pos_opening_shift),
        as_dict=1,
    )

    data = [frappe.get_doc(doctype, d.name).as_dict() for d in data]

    return data


@frappe.whitelist()
def get_payments_entries(pos_opening_shift):
    return frappe.get_all(
        "Payment Entry",
        filters={
            "docstatus": 1,
            "reference_no": pos_opening_shift,
            "payment_type": "Receive",
        },
        fields=[
            "name",
            "mode_of_payment",
            "paid_amount",
            "base_paid_amount",
            "target_exchange_rate",
            "reference_no",
            "posting_date",
            "party",
        ],
    )


def _get_cash_mode_of_payment(pos_profile):
    """
    Get the cash mode of payment for a POS profile.
    Looks up payment methods on the POS Profile and returns the one
    whose Mode of Payment type is 'Cash'.
    Falls back to 'Cash' if nothing found.
    """
    # Try custom field first
    cash_mode = frappe.get_value("POS Profile", pos_profile, "posa_cash_mode_of_payment")
    if cash_mode:
        return cash_mode

    # Find cash-type mode of payment from POS Profile payments table
    payments = frappe.get_all(
        "POS Payment Method",
        filters={"parent": pos_profile},
        fields=["mode_of_payment"],
    )
    for p in payments:
        mop_type = frappe.get_cached_value("Mode of Payment", p.mode_of_payment, "type")
        if mop_type == "Cash":
            return p.mode_of_payment

    return "Cash"


def _aggregate_payment(payments, mode_of_payment, amount, opening_amount=0):
    """Add or update payment amount for a mode of payment."""
    for pay in payments:
        if pay.mode_of_payment == mode_of_payment:
            pay.expected_amount += flt(amount)
            return
    payments.append(frappe._dict({
        "mode_of_payment": mode_of_payment,
        "opening_amount": opening_amount,
        "expected_amount": flt(amount) + opening_amount,
    }))


def _aggregate_tax(taxes, account_head, rate, amount):
    """Add or update tax amount for an account."""
    for tax in taxes:
        if tax.account_head == account_head and tax.rate == rate:
            tax.amount += amount
            return
    taxes.append(frappe._dict({
        "account_head": account_head,
        "rate": rate,
        "amount": amount,
    }))


def _process_invoice(invoice, invoice_field, company_currency, cash_mode, payments, taxes, summary):
    """Process a single invoice and update aggregates."""
    conversion_rate = invoice.get("conversion_rate")
    is_return = invoice.get("is_return", 0)

    base_grand_total = get_base_value(invoice, "grand_total", "base_grand_total", conversion_rate)
    base_net_total = get_base_value(invoice, "net_total", "base_net_total", conversion_rate)

    # Build transaction record
    transaction = frappe._dict({
        invoice_field: invoice.name,
        "posting_date": invoice.posting_date,
        "grand_total": base_grand_total,
        "transaction_currency": invoice.get("currency") or company_currency,
        "transaction_amount": flt(invoice.get("grand_total")),
        "customer": invoice.customer,
        "is_return": is_return,
        "return_against": invoice.get("return_against") if is_return else None,
    })

    # Update summary totals
    summary["grand_total"] += base_grand_total
    summary["net_total"] += base_net_total
    summary["total_quantity"] += flt(invoice.total_qty)

    if is_return:
        summary["returns_total"] += abs(base_grand_total)
        summary["returns_count"] += 1
    else:
        summary["sales_total"] += base_grand_total
        summary["sales_count"] += 1

    # Process taxes
    for t in invoice.taxes:
        tax_amount = get_base_value(t, "tax_amount", "base_tax_amount", conversion_rate)
        _aggregate_tax(taxes, t.account_head, t.rate, tax_amount)

    # Process payments
    for p in invoice.payments:
        amount = get_base_value(p, "amount", "base_amount", conversion_rate)
        if p.mode_of_payment == cash_mode:
            amount -= get_base_value(invoice, "change_amount", "base_change_amount", conversion_rate)
        _aggregate_payment(payments, p.mode_of_payment, amount)

    return transaction


@frappe.whitelist()
def make_closing_shift_from_opening(opening_shift):
    opening_shift = json.loads(opening_shift)
    doctype = "Sales Invoice"
    invoice_field = "sales_invoice"

    submit_printed_invoices(opening_shift.get("name"), doctype)

    # Initialize closing shift document
    closing_shift = frappe.new_doc("POS Closing Shift")
    closing_shift.update({
        "pos_opening_shift": opening_shift.get("name"),
        "period_start_date": opening_shift.get("period_start_date"),
        "period_end_date": frappe.utils.get_datetime(),
        "pos_profile": opening_shift.get("pos_profile"),
        "user": opening_shift.get("user"),
        "company": opening_shift.get("company"),
    })

    company_currency = frappe.get_cached_value("Company", closing_shift.company, "default_currency")
    cash_mode = _get_cash_mode_of_payment(opening_shift.get("pos_profile"))

    # Initialize collections
    payments = []
    taxes = []
    pos_transactions = []

    # Summary for tracking totals
    summary = {
        "grand_total": 0, "net_total": 0, "total_quantity": 0,
        "returns_total": 0, "returns_count": 0,
        "sales_total": 0, "sales_count": 0,
    }

    # Add opening balances to payments
    for detail in opening_shift.get("balance_details", []):
        opening_amount = flt(detail.get("amount"))
        payments.append(frappe._dict({
            "mode_of_payment": detail.get("mode_of_payment"),
            "opening_amount": opening_amount,
            "expected_amount": opening_amount,
        }))

    # Process invoices
    invoices = get_pos_invoices(opening_shift.get("name"), doctype)
    for invoice in invoices:
        txn = _process_invoice(invoice, invoice_field, company_currency, cash_mode, payments, taxes, summary)
        pos_transactions.append(txn)

    # Process payment entries
    pos_payments_table = []
    for py in get_payments_entries(opening_shift.get("name")):
        pos_payments_table.append(frappe._dict({
            "payment_entry": py.name,
            "mode_of_payment": py.mode_of_payment,
            "paid_amount": py.paid_amount,
            "posting_date": py.posting_date,
            "customer": py.party,
        }))
        amount = get_base_value(py, "paid_amount", "base_paid_amount")
        _aggregate_payment(payments, py.mode_of_payment, amount)

    # Update closing shift with totals
    closing_shift.grand_total = summary["grand_total"]
    closing_shift.net_total = summary["net_total"]
    closing_shift.total_quantity = summary["total_quantity"]

    # Set child tables (without return info - that's for display only)
    closing_shift.set("pos_transactions", [
        {k: v for k, v in txn.items() if k not in ("is_return", "return_against")}
        for txn in pos_transactions
    ])
    closing_shift.set("payment_reconciliation", payments)
    closing_shift.set("taxes", taxes)
    closing_shift.set("pos_payments", pos_payments_table)

    # Build response with display-only fields
    result = closing_shift.as_dict()
    result.update({
        "returns_total": summary["returns_total"],
        "returns_count": summary["returns_count"],
        "sales_total": summary["sales_total"],
        "sales_count": summary["sales_count"],
        "pos_transactions": pos_transactions,  # Include return info for display
    })

    return result


@frappe.whitelist()
def submit_closing_shift(closing_shift):
    closing_shift = json.loads(closing_shift)
    closing_shift_doc = frappe.get_doc(closing_shift)
    closing_shift_doc.flags.ignore_permissions = True
    closing_shift_doc.save()
    closing_shift_doc.submit()

    # Auto-create cash transfer Payment Entry if enabled in POS Settings
    _create_cash_transfer_payment_entry(closing_shift_doc)

    return closing_shift_doc.name


def _auto_detect_cash_accounts(pos_profile, company):
    """
    Auto-detect branch cash accounts by matching POS Profile name against
    account names using the pattern:
      Branch Cash Account        : خزينة فرع [profile_name] - ABBR
      Branch Manager Cash Account: خزينة مدير فرع [profile_name] - ABBR
    Falls back to any account containing the profile name if exact match not found.
    """
    company_abbr = frappe.get_cached_value("Company", company, "abbr") or ""

    # Build candidate patterns (exact first, then fuzzy)
    branch_candidates = [
        f"خزينة فرع {pos_profile} - {company_abbr}",
        f"خزينة فرع {pos_profile}",
    ]
    manager_candidates = [
        f"خزينة مدير فرع {pos_profile} - {company_abbr}",
        f"خزينة مدير فرع {pos_profile}",
    ]

    def find_account(candidates, fallback_like):
        for name in candidates:
            if frappe.db.exists("Account", {"name": name, "company": company, "account_type": "Cash"}):
                return name
        # Fuzzy fallback: LIKE search
        result = frappe.db.get_value(
            "Account",
            {"name": ["like", f"%{fallback_like}%"], "company": company, "account_type": "Cash"},
            "name",
        )
        return result

    branch_account = find_account(branch_candidates, f"خزينة فرع {pos_profile}")
    manager_account = find_account(manager_candidates, f"خزينة مدير فرع {pos_profile}")

    return branch_account, manager_account


def _create_cash_transfer_payment_entry(closing_shift_doc):
    """
    Create an Internal Transfer Payment Entry for the total cash amount
    when closing a shift, transferring from Branch Cash Account to
    Branch Manager Cash Account. Accounts are auto-detected from the
    POS Profile name — no manual configuration required.
    """
    try:
        pos_profile = closing_shift_doc.pos_profile
        if not pos_profile:
            return

        # Get POS Settings for this profile
        pos_settings = frappe.db.get_value(
            "POS Settings",
            {"pos_profile": pos_profile, "enabled": 1},
            ["enable_auto_cash_transfer", "branch_cash_account", "branch_manager_cash_account"],
            as_dict=True,
        )

        if not pos_settings or not pos_settings.enable_auto_cash_transfer:
            return

        company = closing_shift_doc.company

        # Use manually configured accounts if set, otherwise auto-detect
        branch_cash_account = pos_settings.branch_cash_account
        manager_cash_account = pos_settings.branch_manager_cash_account

        if not branch_cash_account or not manager_cash_account:
            branch_cash_account, manager_cash_account = _auto_detect_cash_accounts(pos_profile, company)

        if not branch_cash_account or not manager_cash_account:
            frappe.log_error(
                f"Cash Transfer skipped for shift {closing_shift_doc.name}: "
                f"Could not find cash accounts for POS Profile '{pos_profile}'. "
                f"Detected: branch='{branch_cash_account}', manager='{manager_cash_account}'",
                "POS Cash Transfer",
            )
            return

        # Get the current total balance of the branch cash account from GL
        # balance = SUM(debit) - SUM(credit) across all time (all voucher types)
        # gl_result = frappe.db.sql(
        #     """
        #     SELECT SUM(debit) - SUM(credit) AS balance
        #     FROM `tabGL Entry`
        #     WHERE account = %s
        #       AND company = %s
        #       AND is_cancelled = 0
        #     """,
        #     (branch_cash_account, company),
        #     as_dict=True,
        # )

        # cash_amount = flt(gl_result[0].balance) if gl_result and gl_result[0].balance else 0

        cash_amount =closing_shift_doc.actual_amount

        if cash_amount <= 0:
            return

        company_currency = frappe.get_cached_value("Company", company, "default_currency")

        # Create Payment Entry - Internal Transfer
        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Internal Transfer"
        pe.company = company
        pe.custom_pos = 1
        pe.posting_date = frappe.utils.today()
        pe.paid_from = branch_cash_account
        pe.paid_to = manager_cash_account
        pe.paid_amount = cash_amount
        pe.received_amount = cash_amount
        pe.paid_from_account_currency = company_currency
        pe.paid_to_account_currency = company_currency
        pe.reference_no = closing_shift_doc.name
        pe.reference_date = frappe.utils.today()
        pe.remarks = _("Auto cash transfer from POS Shift Close: {0}").format(closing_shift_doc.name)

        pe.flags.ignore_permissions = True
        pe.insert()
        pe.submit()

        frappe.msgprint(
            _("Payment Entry {0} created: {1} transferred from {2} to {3}").format(
                pe.name, frappe.format_value(cash_amount, {"fieldtype": "Currency"}),
                branch_cash_account, manager_cash_account
            ),
            indicator="green",
            alert=True,
        )

    except Exception:
        frappe.log_error(frappe.get_traceback(), "POS Cash Transfer Error")
        frappe.msgprint(
            _("Shift closed successfully, but auto cash transfer failed. Check Error Log for details."),
            indicator="orange",
            alert=True,
        )


def submit_printed_invoices(pos_opening_shift, doctype):
    invoices_list = frappe.get_all(
        doctype,
        filters={
            "posa_pos_opening_shift": pos_opening_shift,
            "docstatus": 0,
            "posa_is_printed": 1,
        },
    )
    for invoice in invoices_list:
        invoice_doc = frappe.get_doc(doctype, invoice.name)
        invoice_doc.submit()
