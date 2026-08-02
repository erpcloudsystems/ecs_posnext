import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

# Used when an order type has no target of its own. Mirrors the fallback in
# ecs_posnext.api.kds._get_target_minutes.
FALLBACK_TARGET_MINUTES = 15

ORDER_TYPE_TARGET_FIELDS = (
    "pickup_target_minutes",
    "delivery_target_minutes",
    "dine_in_target_minutes",
    "talabat_target_minutes",
)


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
        minutes = cint(self.warning_threshold_minutes)
        if not minutes:
            return

        # Every order type must be able to turn amber before it turns red, so the
        # warning has to sit below each configured target. Order types left at 0
        # fall back to FALLBACK_TARGET_MINUTES, which has to clear the bar too.
        for fieldname in ORDER_TYPE_TARGET_FIELDS:
            target = cint(self.get(fieldname))
            if target and minutes >= target:
                frappe.throw(
                    _("Warning After ({0} min) must be less than {1} ({2} min).").format(
                        minutes, _(self.meta.get_label(fieldname)), target
                    )
                )

        targets = [cint(self.get(f)) for f in ORDER_TYPE_TARGET_FIELDS]
        if not all(targets):
            if minutes >= FALLBACK_TARGET_MINUTES:
                frappe.throw(
                    _(
                        "Warning After ({0} min) must be less than the {1} min fallback"
                        " used by order types with no target of their own."
                    ).format(minutes, FALLBACK_TARGET_MINUTES)
                )
            targets.append(FALLBACK_TARGET_MINUTES)

        # The percentage is applied against each order's own target, so basing it
        # on the shortest one keeps the amber step ahead of red for all of them.
        shortest = min(t for t in targets if t)

        # Clamp to 1..99: 0 would turn every order amber immediately, and 100
        # would never fire before the order is already overdue (red).
        pct = round((minutes / shortest) * 100)
        self.warning_threshold_pct = max(1, min(99, pct))
