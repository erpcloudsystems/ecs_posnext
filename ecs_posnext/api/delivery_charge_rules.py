"""Delivery Charge Rule engine.

A Delivery Charge Rule (custom DocType) discounts a delivery zone's charge —
free delivery, a fixed amount off, or a percentage off — inside a validity
window (dates, days of the week, time of day) and for a scope of branches,
POS Profiles and delivery zones (Delivery Charges), optionally above a
minimum order amount.

The POS fetches the rules active for the selected address (see
get_delivery_charge_for_territory) and picks one locally as the cart total
changes; the invoice is then re-resolved here on save so an expired or
out-of-scope offer can never reach the books.
"""

import frappe
from frappe.utils import cint, flt, getdate, now_datetime

RULE_DOCTYPE = "Delivery Charge Rule"

FREE_DELIVERY = "Free Delivery"
DISCOUNT_AMOUNT = "Discount Amount"
DISCOUNT_PERCENTAGE = "Discount Percentage"

# Indexed by datetime.weekday() (Monday == 0)
DAY_FIELDS = (
	"day_monday",
	"day_tuesday",
	"day_wednesday",
	"day_thursday",
	"day_friday",
	"day_saturday",
	"day_sunday",
)

RULE_FIELDS = [
	"name",
	"title",
	"priority",
	"discount_type",
	"discount_amount",
	"discount_percentage",
	"min_order_amount",
	"from_time",
	"to_time",
	"apply_on_all_branches",
	"apply_on_all_pos_profiles",
	"apply_on_all_zones",
]


def _seconds(value):
	"""Time field value (timedelta from the DB, or 'HH:MM[:SS]' string) -> seconds since midnight."""
	if value in (None, ""):
		return None
	if hasattr(value, "total_seconds"):
		return int(value.total_seconds()) % 86400
	parts = [int(float(p)) for p in str(value).split(":")]
	parts += [0] * (3 - len(parts))
	return parts[0] * 3600 + parts[1] * 60 + parts[2]


def _in_time_window(rule, now_seconds):
	start = _seconds(rule.get("from_time"))
	end = _seconds(rule.get("to_time"))
	if start is None and end is None:
		return True
	if start is None:
		return now_seconds <= end
	if end is None:
		return now_seconds >= start
	if start == end:
		return True
	if start < end:
		return start <= now_seconds <= end
	# Overnight window, e.g. 22:00 -> 02:00
	return now_seconds >= start or now_seconds <= end


def _child_values(doctype, fieldname, parents):
	rows = frappe.get_all(
		doctype,
		filters={"parent": ["in", parents], "parenttype": RULE_DOCTYPE},
		fields=["parent", fieldname],
	)
	values = {}
	for row in rows:
		values.setdefault(row.parent, set()).add(row.get(fieldname))
	return values


def get_active_rules(delivery_charges, branch=None, pos_profile=None, at=None):
	"""Rules valid right now for this zone / branch / POS Profile, best first.

	Minimum order amount is NOT checked here: the cart total changes while the
	order is being taken, so callers apply it via pick_rule().
	"""
	if not delivery_charges or not frappe.db.table_exists(RULE_DOCTYPE):
		return []

	at = at or now_datetime()
	today = getdate(at)

	rules = frappe.get_all(
		RULE_DOCTYPE,
		filters={
			"disabled": 0,
			"valid_from": ["<=", today],
			DAY_FIELDS[today.weekday()]: 1,
		},
		or_filters=[["valid_upto", "is", "not set"], ["valid_upto", ">=", today]],
		fields=RULE_FIELDS,
	)

	now_seconds = at.hour * 3600 + at.minute * 60 + at.second
	rules = [r for r in rules if _in_time_window(r, now_seconds)]
	if not rules:
		return []

	names = [r.name for r in rules]
	branches = _child_values("Delivery Charge Rule Branch", "branch", names)
	profiles = _child_values("Delivery Charge Rule POS Profile", "pos_profile", names)
	zones = _child_values("Delivery Charge Rule Zone", "delivery_charges", names)

	active = []
	for r in rules:
		if not cint(r.apply_on_all_branches) and branch not in branches.get(r.name, ()):
			continue
		if not cint(r.apply_on_all_pos_profiles) and pos_profile not in profiles.get(r.name, ()):
			continue
		if not cint(r.apply_on_all_zones) and delivery_charges not in zones.get(r.name, ()):
			continue
		active.append(
			{
				"name": r.name,
				"title": r.title,
				"priority": cint(r.priority),
				"discount_type": r.discount_type,
				"discount_amount": flt(r.discount_amount),
				"discount_percentage": flt(r.discount_percentage),
				"min_order_amount": flt(r.min_order_amount),
			}
		)

	active.sort(key=lambda r: r["priority"], reverse=True)
	return active


def _currency_precision():
	return cint(frappe.db.get_default("currency_precision")) or 2


def apply_rule(base_rate, rule):
	"""Delivery charge after the rule's discount (never below 0)."""
	base_rate = flt(base_rate)
	precision = _currency_precision()
	if rule["discount_type"] == FREE_DELIVERY:
		return 0.0
	if rule["discount_type"] == DISCOUNT_AMOUNT:
		return max(flt(base_rate - flt(rule["discount_amount"]), precision), 0.0)
	if rule["discount_type"] == DISCOUNT_PERCENTAGE:
		pct = min(max(flt(rule["discount_percentage"]), 0), 100)
		return max(flt(base_rate * (100 - pct) / 100, precision), 0.0)
	return base_rate


def pick_rule(base_rate, rules, order_amount):
	"""Return (rule, final_rate) for the highest-priority rule the order qualifies for.

	Rules sharing the top priority go to whichever gives the customer the lower
	charge. Returns (None, base_rate) when nothing applies.
	"""
	eligible = [r for r in rules if flt(order_amount) >= flt(r["min_order_amount"])]
	if not eligible or flt(base_rate) <= 0:
		return None, flt(base_rate)

	top = max(r["priority"] for r in eligible)
	best = min((r for r in eligible if r["priority"] == top), key=lambda r: apply_rule(base_rate, r))
	return best, apply_rule(base_rate, best)


def resolve_delivery_charge(base_rate, delivery_charges, branch=None, pos_profile=None, order_amount=0, at=None):
	"""Server-side final delivery charge for an order. Returns (rule or None, final_rate)."""
	rules = get_active_rules(delivery_charges, branch=branch, pos_profile=pos_profile, at=at)
	return pick_rule(base_rate, rules, order_amount)
