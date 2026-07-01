import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime
from datetime import timedelta


SHIFT_WINDOWS = {
    "Morning": (9, 0, 22, 0),
    "Evening": (22, 0, 6, 0),
    "Whole Day": (9, 0, 6, 0),
}


class POSShiftGroupClosing(Document):
    def validate(self):
        self.set_period_window()
        self.update_totals()

        # Fetch and check for unpaid invoices on validate (save)
        self._fetch_unpaid_invoices()
        if self.unpaid_invoices:
            ids = ", ".join([f"{row.sales_invoice} ({row.outstanding_amount})" for row in self.unpaid_invoices])
            frappe.throw(
                _("لا يمكن حفظ الإغلاق لأن هناك فواتير غير مسددة: {0}").format(ids),
                title=_("Unpaid Invoices"),
            )

    def on_submit(self):
        pass

    def set_period_window(self):
        if not self.working_day or not self.shift:
            return
        start_h, start_m, end_h, end_m = SHIFT_WINDOWS.get(self.shift, (13, 0, 22, 0))

        working = get_datetime(f"{self.working_day} 00:00:00")
        start_dt = working.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        end_dt = working.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

        if (end_h, end_m) <= (start_h, start_m):
            end_dt = end_dt + timedelta(days=1)

        self.period_start = start_dt
        self.period_end = end_dt

    def update_totals(self):
        self.grand_total = 0
        self.net_total = 0
        self.total_quantity = 0
        self.expected_amount = 0
        self.closing_amount = 0
        self.difference = 0

        payments_index = {}

        for row in self.closings or []:
            self.grand_total += float(row.grand_total or 0)
            self.net_total += float(row.net_total or 0)
            self.total_quantity += float(row.total_quantity or 0)
            self.expected_amount += float(row.expected_amount or 0)
            self.closing_amount += float(row.closing_amount or 0)
            self.difference += float(row.difference or 0)

        for pay in self.payments or []:
            key = pay.mode_of_payment
            payments_index[key] = payments_index.get(key, {"expected": 0, "closing": 0})
            payments_index[key]["expected"] += float(pay.expected_amount or 0)
            payments_index[key]["closing"] += float(pay.closing_amount or 0)

        # keep difference field consistent
        for pay in self.payments or []:
            pay.difference = float(pay.closing_amount or 0) - float(pay.expected_amount or 0)

    @frappe.whitelist()
    def fetch_closings(self):
        self.set_period_window()
        if not self.period_start or not self.period_end:
            frappe.throw(_("Working Day and Shift are required to fetch closings."))

        filters = {
            "docstatus": 1,
            "period_end_date": ["between", [self.period_start, self.period_end]],
        }
        if self.company:
            filters["company"] = self.company
        if self.pos_profile:
            filters["pos_profile"] = self.pos_profile

        closings = frappe.get_all(
            "POS Closing Shift",
            filters=filters,
            fields=[
                "name",
                "user",
                "pos_profile",
                "period_start_date",
                "period_end_date",
                "grand_total",
                "net_total",
                "total_quantity",
            ],
        )

        payments_map = {}

        self.set("closings", [])

        for c in closings:
            closing_doc = frappe.get_doc("POS Closing Shift", c.name)
            # Cash-only filtering
            cash_mops = _get_cash_mops(closing_doc)
            expected = sum([float(r.expected_amount or 0) for r in closing_doc.payment_reconciliation if r.mode_of_payment in cash_mops])
            closing_amt = sum([float(r.closing_amount or 0) for r in closing_doc.payment_reconciliation if r.mode_of_payment in cash_mops])
            difference = closing_amt - expected
            self.append(
                "closings",
                {
                    "pos_closing_shift": c.name,
                    "cashier": c.user,
                    "pos_profile": c.pos_profile,
                    "period_start_date": c.period_start_date,
                    "period_end_date": c.period_end_date,
                    "grand_total": c.grand_total,
                    "net_total": c.net_total,
                    "total_quantity": c.total_quantity,
                    "expected_amount": expected,
                    "closing_amount": closing_amt,
                    "difference": difference,
                },
            )

            for pay in closing_doc.payment_reconciliation or []:
                mop = pay.mode_of_payment
                if not mop or mop not in cash_mops:
                    continue
                entry = payments_map.setdefault(
                    mop,
                    {"mode_of_payment": mop, "expected_amount": 0, "closing_amount": 0},
                )
                entry["expected_amount"] += float(pay.expected_amount or 0)
                entry["closing_amount"] += float(pay.closing_amount or 0)

        self.set("payments", [])
        for pay in payments_map.values():
            pay["difference"] = pay["closing_amount"] - pay["expected_amount"]
            self.append("payments", pay)

        # Fetch unpaid invoices linked to these closings' opening shifts
        self._fetch_unpaid_invoices()

        self.update_totals()
        return self

    def _fetch_unpaid_invoices(self):
        """Populate unpaid_invoices child table from opening shifts linked to closings."""
        self.set("unpaid_invoices", [])

        closing_names = [row.pos_closing_shift for row in self.closings if row.pos_closing_shift]
        if not closing_names:
            return

        opening_shifts = frappe.get_all(
            "POS Closing Shift",
            filters={"name": ["in", closing_names]},
            fields=["name", "pos_opening_shift"],
        )
        opening_names = list({o.pos_opening_shift for o in opening_shifts if o.pos_opening_shift})
        if not opening_names:
            return

        placeholders = ", ".join(["%s"] * len(opening_names))
        unpaid = frappe.db.sql(f"""
            SELECT name, customer, grand_total, outstanding_amount, posa_pos_opening_shift
            FROM `tabSales Invoice`
            WHERE posa_pos_opening_shift IN ({placeholders})
            AND docstatus = 1
            AND IFNULL(outstanding_amount, 0) > 0
            ORDER BY outstanding_amount DESC
        """, opening_names, as_dict=True)

        for inv in unpaid:
            self.append("unpaid_invoices", {
                "sales_invoice": inv.name,
                "customer": inv.customer,
                "grand_total": inv.grand_total,
                "outstanding_amount": inv.outstanding_amount,
                "pos_opening_shift": inv.posa_pos_opening_shift,
            })

    @frappe.whitelist()
    def transfer_cash(self):
        if not self.custom_mode_of_payment:
            frappe.throw(_("Please select Target Mode of Payment first."))

        target_mop = self.custom_mode_of_payment
        target_account = frappe.db.get_value("Mode of Payment Account", 
            {"parent": target_mop, "company": self.company}, "default_account")
        
        if not target_account:
            frappe.throw(_("No default account found for target Mode of Payment {0} and company {1}").format(target_mop, self.company))

        cash_mops = self._get_cash_modes()
        
        transfer_count = 0
        for row in self.payments:
            if row.mode_of_payment in cash_mops and float(row.closing_amount or 0) > 0:
                source_account = frappe.db.get_value("Mode of Payment Account", 
                    {"parent": row.mode_of_payment, "company": self.company}, "default_account")
                
                if not source_account:
                    frappe.msgprint(_("Skipping {0}: No default account found.").format(row.mode_of_payment))
                    continue

                # Create Payment Entry
                pe = frappe.new_doc("Payment Entry")
                pe.payment_type = "Internal Transfer"
                pe.company = self.company
                pe.posting_date = frappe.utils.today()
                pe.paid_from = source_account
                pe.paid_to = target_account
                pe.paid_amount = float(row.closing_amount or 0)
                pe.received_amount = float(row.closing_amount or 0)
                pe.reference_no = self.name
                pe.reference_date = frappe.utils.today()
                pe.remarks = _("Internal Transfer from POS Group Closing {0}").format(self.name)
                
                pe.insert(ignore_permissions=True)
                pe.submit()
                transfer_count += 1
        
        if transfer_count > 0:
            frappe.msgprint(_("Successfully created {0} cash transfer(s).").format(transfer_count))
        else:
            frappe.msgprint(_("No cash found to transfer."))

    def _get_cash_modes(self):
        mop_names = [r.mode_of_payment for r in self.payments if r.mode_of_payment]
        if not mop_names:
            return []
        mop_types = {
            row.name: (row.type or "").lower()
            for row in frappe.get_all(
                "Mode of Payment",
                filters={"name": ["in", mop_names]},
                fields=["name", "type"],
            )
        }
        return [m for m in mop_names if mop_types.get(m) == "cash"]


@frappe.whitelist()
def fetch_closings(name):
    doc = frappe.get_doc("POS Shift Group Closing", name)
    doc.fetch_closings()
    doc.save(ignore_permissions=True)
    return doc


@frappe.whitelist()
def get_closings_data(working_day, shift, company, pos_profile=None):
    doc = frappe.new_doc("POS Shift Group Closing")
    doc.working_day = working_day
    doc.shift = shift
    doc.company = company
    doc.pos_profile = pos_profile
    doc.fetch_closings()
    return doc.as_dict()


def _get_cash_mops(closing_doc):
    """Return the list of cash-mode-of-payment names relevant for this closing doc."""
    mop_names = [r.mode_of_payment for r in closing_doc.payment_reconciliation if r.mode_of_payment]
    if not mop_names:
        return []
    mop_types = {
        row.name: (row.type or "").lower()
        for row in frappe.get_all(
            "Mode of Payment",
            filters={"name": ["in", mop_names]},
            fields=["name", "type"],
        )
    }
    return [m for m in mop_names if mop_types.get(m) == "cash"]
