import frappe
from frappe import _
from frappe.utils import flt
from ecs_posnext.pos_next.doctype.pos_closing_shift.pos_closing_shift import _auto_detect_cash_accounts

def _get_cash_accounts_from_profile(pos_profile, company):
    payments = frappe.get_all("POS Payment Method", filters={"parent": pos_profile, "parenttype": "POS Profile"}, fields=["mode_of_payment"])
    
    branch_cash_account = None
    
    for p in payments:
        mop_type = frappe.db.get_value("Mode of Payment", p.mode_of_payment, "type")
        if mop_type == "Cash" or p.mode_of_payment == "Cash":
            branch_cash_account = frappe.db.get_value("Mode of Payment Account", {"parent": p.mode_of_payment, "company": company}, "default_account")
            break
            
    auto_branch, auto_manager = _auto_detect_cash_accounts(pos_profile, company)
    
    return branch_cash_account or auto_branch, auto_manager

@frappe.whitelist()
def get_cash_balance(pos_profile, company):
    """
    Get the current balance of the branch cash account linked to the POS Profile.
    """
    if not pos_profile or not company:
        return {"balance": 0.0, "account": None}

    branch_cash_account, _ = _get_cash_accounts_from_profile(pos_profile, company)

    if not branch_cash_account:
        return {"balance": 0.0, "account": None}

    # Get the current total balance of the branch cash account from GL
    gl_result = frappe.db.sql(
        """
        SELECT SUM(debit) - SUM(credit) AS balance
        FROM `tabGL Entry`
        WHERE account = %s
          AND company = %s
          AND is_cancelled = 0
        """,
        (branch_cash_account, company),
        as_dict=True,
    )

    balance = flt(gl_result[0].balance) if gl_result and gl_result[0].balance else 0.0

    return {
        "balance": balance,
        "account": branch_cash_account,
        "currency": frappe.get_cached_value("Company", company, "default_currency")
    }

@frappe.whitelist()
def transfer_cash(pos_profile, company, amount, to_account=None, remarks=None):
    """
    Transfer cash from the branch cash account to another account (default manager account).
    """
    _require_cash_management_access()
    amount = flt(amount)
    if amount <= 0:
        frappe.throw(_("Amount to transfer must be greater than zero."))

    # Enforce branch scope: a restricted user may only transfer from a POS
    # Profile / Branch they are permitted to see.
    restricted, allowed_profiles, allowed_branches = _get_user_branch_scope()
    if restricted:
        permitted = (pos_profile in allowed_profiles) if allowed_profiles else False
        if not permitted and allowed_branches:
            profile_branch = frappe.db.get_value("POS Profile", pos_profile, "branch")
            permitted = profile_branch in allowed_branches
        if not permitted:
            frappe.throw(_("You are not permitted to transfer cash from this branch."))

    branch_cash_account, manager_cash_account = _get_cash_accounts_from_profile(pos_profile, company)

    if not branch_cash_account:
        frappe.throw(_("Could not determine the branch cash account for POS Profile: {0}").format(pos_profile))

    target_account = to_account or manager_cash_account
    if not target_account:
        frappe.throw(_("Please specify a destination account for the transfer."))

    # Check current balance
    current_balance_info = get_cash_balance(pos_profile, company)
    current_balance = current_balance_info.get("balance", 0.0)

    if amount > current_balance:
        frappe.throw(_("Cannot transfer {0}. Available balance is {1}.").format(
            frappe.format_value(amount, {"fieldtype": "Currency"}),
            frappe.format_value(current_balance, {"fieldtype": "Currency"})
        ))

    company_currency = frappe.get_cached_value("Company", company, "default_currency")

    # Create Payment Entry - Internal Transfer
    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Internal Transfer"
    pe.company = company
    pe.posting_date = frappe.utils.today()
    pe.paid_from = branch_cash_account
    pe.paid_to = target_account
    pe.paid_amount = amount
    pe.received_amount = amount
    pe.paid_from_account_currency = company_currency
    pe.paid_to_account_currency = company_currency
    pe.reference_date = frappe.utils.today()
    pe.remarks = remarks or _("Manual cash transfer from POS for {0}").format(pos_profile)

    pe.insert(ignore_permissions=True)
    pe.submit()

    return {
        "name": pe.name,
        "message": _("Successfully transferred {0} from {1} to {2}").format(
            frappe.format_value(amount, {"fieldtype": "Currency"}),
            branch_cash_account,
            target_account
        )
    }

CASH_MANAGEMENT_ROLES = ("System Manager", "Bransh Manager")


def _require_cash_management_access():
    """Only Branch Managers and System Managers may use Cash Management."""
    user = frappe.session.user
    if user == "Administrator":
        return
    if not set(CASH_MANAGEMENT_ROLES) & set(frappe.get_roles(user)):
        frappe.throw(
            _("You are not permitted to access Cash Management."),
            frappe.PermissionError,
        )


def _get_user_branch_scope():
    """
    Restrict Global Cash Management to what the current user is allowed to see
    via Frappe User Permissions.

    Returns (restricted, pos_profiles, branches):
      - restricted: True if the user is limited (non-superuser with permissions)
      - pos_profiles / branches: allowed values for each doctype
    System Managers / Administrator are never restricted (see all branches).
    """
    user = frappe.session.user
    if user == "Administrator" or "System Manager" in frappe.get_roles(user):
        return False, [], []

    perms = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": ["in", ["POS Profile", "Branch"]]},
        fields=["allow", "for_value"],
    )
    pos_profiles = [p.for_value for p in perms if p.allow == "POS Profile"]
    branches = [p.for_value for p in perms if p.allow == "Branch"]

    # No explicit permissions → standard Frappe behaviour: unrestricted.
    if not pos_profiles and not branches:
        return False, [], []
    return True, pos_profiles, branches


@frappe.whitelist()
def get_all_branches_cash_balances():
    """
    Get cash balances for the POS Profiles (Branches) the current user is
    permitted to see (via User Permission on POS Profile / Branch).
    """
    _require_cash_management_access()
    pp_filters = {"disabled": 0}
    restricted, allowed_profiles, allowed_branches = _get_user_branch_scope()
    if restricted:
        if allowed_profiles:
            pp_filters["name"] = ["in", allowed_profiles]
        if allowed_branches:
            pp_filters["branch"] = ["in", allowed_branches]

    profiles = frappe.get_list(
        "POS Profile",
        filters=pp_filters,
        fields=["name", "company", "currency"]
    )

    results = []

    for profile in profiles:
        pos_profile = profile.name
        company = profile.company
        
        branch_cash_account, manager_cash_account = _get_cash_accounts_from_profile(pos_profile, company)

        if not branch_cash_account:
            continue

        gl_result = frappe.db.sql(
            """
            SELECT SUM(debit) - SUM(credit) AS balance
            FROM `tabGL Entry`
            WHERE account = %s
              AND company = %s
              AND is_cancelled = 0
            """,
            (branch_cash_account, company),
            as_dict=True,
        )

        balance = flt(gl_result[0].balance) if gl_result and gl_result[0].balance else 0.0

        results.append({
            "pos_profile": pos_profile,
            "company": company,
            "account": branch_cash_account,
            "manager_account": manager_cash_account,
            "balance": balance,
            "currency": profile.currency or frappe.get_cached_value("Company", company, "default_currency")
        })

    return results

@frappe.whitelist()
def get_destination_accounts(company):
    """
    Get a list of valid destination accounts (Cash or Bank) for the given company.
    """
    if not company:
        return []

    accounts = frappe.get_list(
        "Account",
        filters={
            "company": company,
            "is_group": 0,
            "account_type": ["in", ["Cash", "Bank"]]
        },
        fields=["name", "account_name", "account_type"],
        order_by="name asc"
    )
    
    return accounts
