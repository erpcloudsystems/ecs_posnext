import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, add_days


SHIFT_WINDOWS = {
    "Morning": (12, 0, 20, 0),
    "Evening": (20, 0, 5, 0),
}


class POSShiftGroupClosing(Document):
    def validate(self):
        self.set_period_window()
        self.update_totals()

    def set_period_window(self):
        if not self.working_day or not self.shift:
            return
        start_h, start_m, end_h, end_m = SHIFT_WINDOWS.get(self.shift, (12, 0, 5, 0))

        working = get_datetime(f"{self.working_day} 00:00:00")
        start_dt = working.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        end_dt = working.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

        if (end_h, end_m) <= (start_h, start_m):
            end_dt = add_days(end_dt, 1)

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

        existing = {row.pos_closing_shift for row in self.closings or []}
        payments_map = {}

        self.set("closings", [])

        for c in closings:
            if c.name in existing:
                continue
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

        self.update_totals()
        return self


@frappe.whitelist()
def fetch_closings(name):
    doc = frappe.get_doc("POS Shift Group Closing", name)
    doc.fetch_closings()
    doc.save(ignore_permissions=True)
    return doc


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
