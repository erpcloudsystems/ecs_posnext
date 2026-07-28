# Copyright (c) 2026, erpcloud.systems and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift import (
    _get_opening_shift_totals,
)

# Mirrors the mode of payment treated as Visa in POS Closing Shift.
VISA_MODE_OF_PAYMENT = "بنك CIB فيزا"

ALLOWED_ROLE = "System Manager"


def _check_permitted():
    """Only System Managers may recalculate figures on submitted closing shifts."""
    if ALLOWED_ROLE not in frappe.get_roles():
        frappe.throw(
            _("Only {0} can update Total Daily Payments on a POS Closing Shift.").format(
                _(ALLOWED_ROLE)
            ),
            frappe.PermissionError,
        )


def _currency_precision():
    return cint(frappe.get_cached_value("System Settings", None, "currency_precision")) or 2


def _get_visa_amount(pos_closing_shift):
    """Visa portion of a closing shift, using the same basis as POS Closing Shift."""
    result = frappe.db.sql(
        """
        SELECT COALESCE(SUM(COALESCE(expected_amount, 0) - COALESCE(opening_amount, 0)), 0) AS total
        FROM `tabPOS Closing Shift Detail`
        WHERE parent = %s AND parenttype = 'POS Closing Shift' AND mode_of_payment = %s
        """,
        (pos_closing_shift, VISA_MODE_OF_PAYMENT),
        as_dict=True,
    )
    return flt(result[0].total) if result else 0.0


def _evaluate_shift(shift):
    """Return stored vs recalculated figures for one submitted closing shift row."""
    totals = _get_opening_shift_totals(shift.pos_opening_shift)
    correct_daily_payments = flt(totals["total_daily_payments"])
    visa_amount = _get_visa_amount(shift.name)

    return frappe._dict(
        {
            "pos_closing_shift": shift.name,
            "branch": shift.branch,
            "posting_date": shift.posting_date,
            "grand_total": flt(shift.grand_total),
            "current_total_daily_payments": flt(shift.total_daily_payments),
            "correct_total_daily_payments": correct_daily_payments,
            "difference": correct_daily_payments - flt(shift.total_daily_payments),
            "current_actual_amount": flt(shift.actual_amount),
            "correct_actual_amount": flt(shift.grand_total)
            - visa_amount
            - correct_daily_payments
            - flt(totals["total_tip"]),
        }
    )


def _get_submitted_shifts(branch=None, name=None):
    """Submitted closing shifts, with Branch resolved through their POS Profile."""
    conditions = ["cs.docstatus = 1"]
    values = {}

    if branch:
        conditions.append("pp.branch = %(branch)s")
        values["branch"] = branch

    if name:
        conditions.append("cs.name = %(name)s")
        values["name"] = name

    return frappe.db.sql(
        """
        SELECT cs.name, cs.pos_opening_shift, cs.posting_date, cs.grand_total,
               cs.total_daily_payments, cs.total_tip, cs.actual_amount,
               pp.branch AS branch
        FROM `tabPOS Closing Shift` cs
        LEFT JOIN `tabPOS Profile` pp ON pp.name = cs.pos_profile
        WHERE {conditions}
        ORDER BY cs.posting_date, cs.name
        """.format(conditions=" AND ".join(conditions)),
        values,
        as_dict=True,
    )


def get_affected_shifts(branch=None):
    """Submitted closing shifts whose stored Total Daily Payments is out of date."""
    precision = _currency_precision()
    affected = []

    for shift in _get_submitted_shifts(branch=branch):
        evaluated = _evaluate_shift(shift)
        if flt(evaluated.correct_total_daily_payments, precision) != flt(
            evaluated.current_total_daily_payments, precision
        ):
            affected.append(evaluated)

    return affected


class POSClosingShiftDailyPaymentUpdate(Document):
    def validate(self):
        if self.update_mode == "Single Closing Shift":
            self.affected_shifts = []
            self.set_single_shift_preview()
        else:
            self.pos_closing_shift = None
            self.current_total_daily_payments = 0
            self.correct_total_daily_payments = 0
            self.difference = 0

    def set_single_shift_preview(self):
        """Refresh the read-only preview beside the selected closing shift."""
        if not self.pos_closing_shift:
            self.current_total_daily_payments = 0
            self.correct_total_daily_payments = 0
            self.difference = 0
            return

        evaluated = self.evaluate_single_shift()
        self.current_total_daily_payments = evaluated.current_total_daily_payments
        self.correct_total_daily_payments = evaluated.correct_total_daily_payments
        self.difference = evaluated.difference

    def evaluate_single_shift(self):
        shifts = _get_submitted_shifts(branch=self.branch, name=self.pos_closing_shift)
        if not shifts:
            frappe.throw(
                _("{0} is not a submitted POS Closing Shift of the selected Branch.").format(
                    self.pos_closing_shift
                )
            )

        return _evaluate_shift(shifts[0])

    @frappe.whitelist()
    def fetch_affected_shifts(self):
        """Populate the child table with every closing shift that needs correcting."""
        _check_permitted()

        affected = get_affected_shifts(branch=self.branch)
        self.affected_shifts = []
        for row in affected:
            self.append("affected_shifts", row)

        self.status = "Pending"
        self.shifts_updated = 0
        self.save()

        if not affected:
            frappe.msgprint(
                _("No POS Closing Shift needs correcting for the selected Branch."),
                title=_("Nothing To Update"),
                indicator="green",
            )
        else:
            frappe.msgprint(
                _("{0} POS Closing Shift(s) need correcting.").format(len(affected)),
                title=_("Affected Closing Shifts"),
                indicator="orange",
            )

        return len(affected)

    @frappe.whitelist()
    def update_total_daily_payments(self):
        """Write the recalculated figures onto the target closing shifts."""
        _check_permitted()

        if self.update_mode == "Single Closing Shift":
            if not self.pos_closing_shift:
                frappe.throw(_("Please select a POS Closing Shift to update."))
            targets = [self.evaluate_single_shift()]
        else:
            if not self.affected_shifts:
                frappe.throw(
                    _("Please use {0} before updating.").format(
                        frappe.bold(_("Get Affected Closing Shifts"))
                    )
                )
            targets = [
                self.evaluate_single_shift_by_name(row.pos_closing_shift)
                for row in self.affected_shifts
            ]

        precision = _currency_precision()
        updated = 0
        for evaluated in targets:
            if flt(evaluated.correct_total_daily_payments, precision) == flt(
                evaluated.current_total_daily_payments, precision
            ):
                continue
            self.apply_correction(evaluated)
            updated += 1

        self.refresh_rows(targets)
        self.shifts_updated = updated
        self.status = "Completed" if updated else "Pending"
        self.save()

        if updated:
            frappe.msgprint(
                _("Total Daily Payments updated on {0} POS Closing Shift(s).").format(updated),
                title=_("Updated"),
                indicator="green",
            )
        else:
            frappe.msgprint(
                _("Nothing to update — the stored figures are already correct."),
                title=_("No Change"),
                indicator="blue",
            )

        return updated

    def evaluate_single_shift_by_name(self, pos_closing_shift):
        shifts = _get_submitted_shifts(branch=self.branch, name=pos_closing_shift)
        if not shifts:
            frappe.throw(
                _("{0} is not a submitted POS Closing Shift of the selected Branch.").format(
                    pos_closing_shift
                )
            )

        return _evaluate_shift(shifts[0])

    def apply_correction(self, evaluated):
        """Update the read-only reconciliation figures and leave an audit comment."""
        values = {"total_daily_payments": evaluated.correct_total_daily_payments}
        message = _("Total Daily Payments corrected from {0} to {1} by {2}.").format(
            flt(evaluated.current_total_daily_payments),
            flt(evaluated.correct_total_daily_payments),
            self.name,
        )

        if self.update_actual_amount:
            values["actual_amount"] = evaluated.correct_actual_amount
            message += " " + _("Actual Amount corrected from {0} to {1}.").format(
                flt(evaluated.current_actual_amount),
                flt(evaluated.correct_actual_amount),
            )

        frappe.db.set_value(
            "POS Closing Shift",
            evaluated.pos_closing_shift,
            values,
            update_modified=False,
        )
        frappe.get_doc("POS Closing Shift", evaluated.pos_closing_shift).add_comment(
            "Comment", message
        )

    def refresh_rows(self, targets):
        """Re-state the child table (or preview) against the freshly written values."""
        if self.update_mode == "Single Closing Shift":
            self.set_single_shift_preview()
            return

        self.affected_shifts = []
        for evaluated in targets:
            shifts = _get_submitted_shifts(name=evaluated.pos_closing_shift)
            row = _evaluate_shift(shifts[0]) if shifts else evaluated
            row.updated = 1
            self.append("affected_shifts", row)


@frappe.whitelist()
def affected_closing_shift_query(doctype, txt, searchfield, start, page_len, filters):
    """Link query listing only closing shifts with an out-of-date Total Daily Payments."""
    _check_permitted()

    branch = (filters or {}).get("branch")
    search = (txt or "").lower()

    matches = [
        [
            row.pos_closing_shift,
            row.branch or "",
            flt(row.current_total_daily_payments),
            flt(row.correct_total_daily_payments),
        ]
        for row in get_affected_shifts(branch=branch)
        if search in (row.pos_closing_shift or "").lower()
    ]

    return matches[cint(start) : cint(start) + cint(page_len)]
