"""
Sales Order hooks for POS sales.

The POS submits a Sales Order for every sale, so the rules that used to live on
Sales Invoice belong here now.
"""

import frappe
from frappe import _

# The customer a room-service sale is booked against until the room says who the
# guest actually is. It is the POS Profile's default customer, so a sale that was
# never attributed to anybody lands on it - which is exactly the case this module
# refuses to let through. The name is the same literal the "POS Customer Type"
# field offers, and the two must be changed together.
ROOM_CUSTOMER = "Room Customer"


def validate(doc, method=None):
	require_room_for_room_customer(doc)


def is_pos_order(doc):
	"""Whether the POS created this order, rather than the back office."""
	return bool(doc.get("posa_pos_opening_shift") or doc.get("pos_stock_entry"))


def require_room_for_room_customer(doc):
	"""
	Refuse a room-customer sale that names no room.

	A sale on the Room Customer is a charge to a guest's folio, and the room is
	the only thing that says whose. Without it the sale cannot reach Protel at
	all: the posting hook finds neither a room nor an employee and stops, leaving
	the charge in ERPNext and nowhere else, so nobody is ever billed for it.

	Blocking it at the till costs the cashier one tap - pick the room, or put the
	sale on a walk-in customer. Letting it through costs the hotel the money.
	"""
	if not is_pos_order(doc):
		return

	# Either signal is enough. The type alone would let a stale draft through - it
	# can still be carrying "Guest Customer" from before the cashier switched - and
	# the customer alone would miss a sale the POS typed as a room charge against
	# some other customer record.
	is_room_sale = (
		(doc.get("posa_customer_type") or "").strip() == ROOM_CUSTOMER
		or doc.get("customer") == ROOM_CUSTOMER
	)

	if is_room_sale and not doc.get("room"):
		frappe.throw(
			_(
				"Select the room this sale is charged to. A sale on {0} is a charge to "
				"a guest's folio and cannot be posted without it - put it on a walk-in "
				"customer instead if nobody is being charged."
			).format(doc.get("customer") or ROOM_CUSTOMER),
			title=_("Room Required"),
		)
