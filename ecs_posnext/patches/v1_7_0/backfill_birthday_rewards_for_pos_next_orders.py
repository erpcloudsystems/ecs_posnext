"""Backfill birthday voucher + points for party orders closed through POS Next.

close_party_reservation used to mark the Sales Order Executed with db.set_value,
which skips document hooks, so loyalty_engine never issued the birthday voucher
or staged the birthday points for those orders.

Scope (all must hold):
- submitted Sales Order, pos_status = Executed, select_event matches an enabled
  Birthday Package Rule, party (delivery) date on/after the POS Next rollout
  (2026-07-01);
- no Version entry recording pos_status -> Executed (i.e. it was NOT executed by a
  normal save, where the hook would already have run and decided).

Each reward is checked separately, so the patch is safe to re-run and completes
orders a previous run left half-done:
- points are staged only if the order has no Pending Loyalty Reward yet;
- a voucher is issued only if no Birthday Voucher is linked to the order yet.

No savepoints/rollback: ecs_vim's "*" before_insert hook (enable_customer_if_exists)
commits on every insert, so each reward is committed as soon as it is created.
A failure on one order is logged and the patch moves on; it never aborts migrate.
Failed orders can be retried after fixing the data by re-running this module with
`bench --site <site> execute ecs_posnext.patches.v1_7_0.backfill_birthday_rewards_for_pos_next_orders.execute`.

Issuing a Birthday Voucher sends the customer the usual voucher SMS/notifications,
exactly as the normal (non-bugged) flow would have.
"""

import frappe
from frappe.utils import cint, flt, today

POS_NEXT_ROLLOUT = "2026-07-01"


def execute():
	if "loyalty_engine" not in frappe.get_installed_apps():
		return

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
				SELECT 1 FROM `tabVersion` v
				WHERE v.ref_doctype = 'Sales Order' AND v.docname = so.name
					AND v.data REGEXP '"pos_status",[[:space:]]*"[^"]*",[[:space:]]*"Executed"'
			)
		ORDER BY so.delivery_date, so.creation
		""",
		{"since": POS_NEXT_ROLLOUT},
	)

	stats = {"points": 0, "vouchers": 0, "skipped": 0}
	failed = []
	frappe.flags.mute_messages = True
	try:
		for name in orders:
			try:
				_backfill_order(name, stats)
			except Exception:
				failed.append(name)
				frappe.log_error(
					title="Birthday reward backfill failed",
					message=f"Sales Order: {name}\n\n{frappe.get_traceback()}",
				)
	finally:
		frappe.flags.mute_messages = False

	print(
		f"Birthday reward backfill: {len(orders)} candidate orders, "
		f"{stats['points']} points staged, {stats['vouchers']} vouchers issued, "
		f"{stats['skipped']} skipped (already rewarded / voucher limit), {len(failed)} failed"
	)
	if failed:
		print("Failed (see Error Log 'Birthday reward backfill failed'): " + ", ".join(failed))


def _backfill_order(name, stats):
	"""Mirror loyalty_engine.hooks.sales_order._process_birthday_rewards_for_order,
	but create only the rewards this order is still missing."""
	from loyalty_engine.loyalty_engine.doctype.pending_loyalty_reward.pending_loyalty_reward import (
		create_pending_reward,
	)
	from loyalty_engine.loyalty_engine.services.voucher import issue_birthday_voucher

	doc = frappe.get_doc("Sales Order", name)
	rule_name = frappe.db.get_value(
		"Birthday Package Rule", {"item_code": doc.select_event, "enabled": 1}, "name"
	)
	if not rule_name:
		return
	rule = frappe.get_doc("Birthday Package Rule", rule_name)
	did_something = False

	# 1. Points (staged; credited by the 8 AM pending-reward job)
	if not frappe.db.exists(
		"Pending Loyalty Reward", {"reference_doctype": "Sales Order", "reference_name": name}
	):
		points = 0
		if flt(rule.percentage_of_net_total) > 0:
			points = flt(flt(doc.net_total) * (rule.percentage_of_net_total / 100), 2)
		elif cint(rule.fixed_points) > 0:
			points = cint(rule.fixed_points)
		if points > 0:
			create_pending_reward(
				customer=doc.customer,
				reference_doctype="Sales Order",
				reference_name=name,
				posting_date=doc.get("transaction_date") or today(),
				reward_type="Points",
				points=points,
			)
			stats["points"] += 1
			did_something = True

	# 2. Voucher
	if flt(rule.voucher_amount) > 0 and not frappe.db.exists(
		"Birthday Voucher", {"original_order": name}
	):
		voucher = issue_birthday_voucher(
			customer=doc.customer,
			package_rule=rule,
			original_order=name,
			child_name=doc.get("custom_child_name") or doc.get("customer_name") or doc.customer,
		)
		if voucher:
			stats["vouchers"] += 1
			did_something = True

	if not did_something:
		stats["skipped"] += 1
