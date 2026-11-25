"""Backfill birthday voucher + points for party orders closed through POS Next.

close_party_reservation used to mark the Sales Order Executed with db.set_value,
which skips document hooks, so loyalty_engine never issued the birthday voucher
or staged the birthday points for those orders.

Scope (all must hold):
- submitted Sales Order, pos_status = Executed, select_event matches an enabled
  Birthday Package Rule, party (delivery) date on/after the POS Next rollout
  (2026-07-01);
- no Birthday Voucher and no Pending Loyalty Reward already linked to the order;
- no Version entry recording pos_status -> Executed (i.e. it was NOT executed by a
  normal save, where the hook would already have run and decided).

Only the loyalty reward function is called; the order is not re-saved, so no party
coupon / SMS is sent for past parties.
"""

import frappe

POS_NEXT_ROLLOUT = "2026-07-01"


def execute():
	if "loyalty_engine" not in frappe.get_installed_apps():
		return

	from loyalty_engine.loyalty_engine.hooks.sales_order import _process_birthday_rewards_for_order
	from loyalty_engine.loyalty_engine.services.validators import is_loyalty_enabled

	if not is_loyalty_enabled():
		return

	orders = frappe.db.sql_list(
		"""
		SELECT so.name
		FROM `tabSales Order` so
		INNER JOIN `tabBirthday Package Rule` bpr
			ON bpr.item_code = so.select_event AND bpr.enabled = 1
		WHERE so.docstatus = 1
			AND so.pos_status = 'Executed'
			AND so.delivery_date >= %(since)s
			AND NOT EXISTS (
				SELECT 1 FROM `tabBirthday Voucher` bv WHERE bv.original_order = so.name
			)
			AND NOT EXISTS (
				SELECT 1 FROM `tabPending Loyalty Reward` plr
				WHERE plr.reference_doctype = 'Sales Order' AND plr.reference_name = so.name
			)
			AND NOT EXISTS (
				SELECT 1 FROM `tabVersion` v
				WHERE v.ref_doctype = 'Sales Order' AND v.docname = so.name
					AND v.data REGEXP '"pos_status",[[:space:]]*"[^"]*",[[:space:]]*"Executed"'
			)
		ORDER BY so.delivery_date, so.creation
		""",
		{"since": POS_NEXT_ROLLOUT},
	)

	done, failed = [], []
	frappe.flags.mute_messages = True
	try:
		for name in orders:
			frappe.db.savepoint("birthday_backfill")
			try:
				_process_birthday_rewards_for_order(frappe.get_doc("Sales Order", name))
				done.append(name)
			except Exception:
				frappe.db.rollback(save_point="birthday_backfill")
				failed.append(name)
				frappe.log_error(
					title="Birthday reward backfill failed",
					message=f"Sales Order: {name}\n\n{frappe.get_traceback()}",
				)
	finally:
		frappe.flags.mute_messages = False

	print(f"Birthday reward backfill: {len(orders)} candidate orders, {len(done)} processed, {len(failed)} failed")
	if failed:
		print("Failed (see Error Log 'Birthday reward backfill failed'): " + ", ".join(failed))
