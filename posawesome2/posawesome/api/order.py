
import frappe

# v14/v15 import compatibility
try:
    from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification
except ModuleNotFoundError:
    from frappe.core.doctype.notification_log.notification_log import enqueue_create_notification

def _pos_users_global():
    # all active users having "POS User" role (skip Guest)
    users = frappe.get_all("Has Role", filters={"role": "POS User"}, fields=["parent"])
    users = [u.parent for u in users if u.parent != "Guest"]
    # keep only enabled
    enabled = set(
        u for (u, en) in frappe.get_all("User", filters={"name": ("in", users)},
                                        fields=["name as u", "enabled as en"], as_list=True)
        if en
    )
    frappe.log_error(title="FDF", message=list(enabled))

    return list(enabled)

def _users_by_branch(branch):
    if not branch:
        return []
    # users who have a User Permission for this Branch
    ups = frappe.get_all("User Permission",
                         filters={"allow": "Branch", "for_value": branch},
                         fields=["user"])
    ups = [r.user for r in ups if r.user and r.user != "Guest"]
    # keep only enabled
    enabled = set(
        u for (u, en) in frappe.get_all("User", filters={"name": ("in", ups)},
                                        fields=["name as u", "enabled as en"], as_list=True)
        if en
    )
    frappe.log_error(title="FDF", message=list(enabled))

    return list(enabled)

def notify_pos_on_so(doc, method):
    # figure branch field (adjust if your field is custom)
    branch = getattr(doc, "branch", None) or getattr(doc, "custom_branch", None)
    # recipients = POS users (global) ∪ users permitted on this branch
    recipients = set(_pos_users_global()) | set(_users_by_branch(branch))
    if not recipients:
        return

    subject = frappe._("New Sales Order {0}").format(doc.name)
    amount = frappe.format_value(doc.grand_total, {"fieldtype": "Currency", "currency": doc.currency})
    body = f"<div>{frappe._('Customer')}: <b>{frappe.utils.escape_html(doc.customer or '')}</b><br>{frappe._('Amount')}: <b>{amount}</b></div>"
    notification_doc = {
        "type": "Alert",                   # show as standard bell alert
        "document_type": "Sales Order",
        "document_name": doc.name,
        "subject": subject,
        "from_user": frappe.session.user,  # who triggered the event
        "email_content": body,             # HTML is fine (same as assign_to.py)
    }

    # one Notification Log per user (same pattern as assign_to.py)
    for user in recipients:
        enqueue_create_notification(user, notification_doc)
        frappe.log_error(user)
        frappe.publish_realtime(
            "so_notify_sound",
            {"so": doc.name, "branch": branch},
            user=user,
            after_commit=True,
        )

def submit(doc, method):
    notify_pos_on_so(doc, method)