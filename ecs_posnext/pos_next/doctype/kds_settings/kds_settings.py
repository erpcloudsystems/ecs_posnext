import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class KDSSettings(Document):
    def validate(self):
        self.set_warning_threshold_pct()

    def set_warning_threshold_pct(self):
        """Derive the percentage the KDS timers use from the minutes entered here.

        The KDS screens compare elapsed time against each order's own target,
        which varies by order type, so the amber threshold has to be a proportion
        of that target rather than a fixed clock time. Staff think in minutes, so
        minutes are what gets configured and the percentage is computed.
        """
        target = cint(self.default_target_minutes)
        minutes = cint(self.warning_threshold_minutes)

        if not target or not minutes:
            return

        if minutes >= target:
            frappe.throw(
                _("Warning After ({0} min) must be less than Target Minutes ({1} min).").format(
                    minutes, target
                )
            )

        # Clamp to 1..99: 0 would turn every order amber immediately, and 100
        # would never fire before the order is already overdue (red).
        pct = round((minutes / target) * 100)
        self.warning_threshold_pct = max(1, min(99, pct))
