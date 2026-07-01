# Copyright (c) 2021, Youssef Restom and contributors
# For license information, please see license.txt

import frappe, erpnext, json
from frappe import _
from frappe.utils import nowdate, getdate, flt
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.journal_entry.journal_entry import (
    get_default_bank_cash_account,
)
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account
from posawesome.posawesome.api.m_pesa import submit_mpesa_payment
from erpnext.accounts.utils import QueryPaymentLedger, get_outstanding_invoices as _get_outstanding_invoices


def validate_payment_entry(doc, method):
    """Validate Payment Entry to prevent duplicate payments for same invoice"""
    if doc.docstatus != 0:
        return
    
    for ref in doc.get("references") or []:
        if ref.reference_doctype == "Sales Invoice" and ref.reference_name:
            inv_name = ref.reference_name
            current_outstanding = frappe.db.get_value("Sales Invoice", inv_name, "outstanding_amount") or 0
            
            if flt(current_outstanding) <= 0:
                frappe.throw(
                    _("Invoice {0} is already fully paid. Cannot create duplicate payment.").format(inv_name)
                )
            
            if flt(ref.allocated_amount) > flt(current_outstanding):
                frappe.throw(
                    _("Allocated amount {0} for invoice {1} exceeds outstanding amount {2}").format(
                        ref.allocated_amount, inv_name, current_outstanding
                    )
                )


def create_payment_entry(
    company,
    customer,
    amount,
    currency,
    mode_of_payment,
    reference_date=None,
    reference_no=None,
    posting_date=None,
    cost_center=None,
    submit=0,
):
    # TODO : need to have a better way to handle currency
    date = nowdate() if not posting_date else posting_date
    party_type = "Customer"
    party_account = get_party_account(party_type, customer, company)
    party_account_currency = get_account_currency(party_account)
    if party_account_currency != currency:
        frappe.throw(
            _(
                "Currency is not correct, party account currency is {party_account_currency} and transaction currency is {currency}"
            ).format(party_account_currency=party_account_currency, currency=currency)
        )
    payment_type = "Receive"

    bank = get_bank_cash_account(company, mode_of_payment)
    company_currency = frappe.get_value("Company", company, "default_currency")
    conversion_rate = get_exchange_rate(currency, company_currency, date, "for_selling")
    paid_amount, received_amount = set_paid_amount_and_received_amount(
        party_account_currency, bank, amount, payment_type, None, conversion_rate
    )

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = payment_type
    pe.company = company
    pe.cost_center = cost_center or erpnext.get_default_cost_center(company)
    pe.posting_date = date
    pe.mode_of_payment = mode_of_payment
    pe.party_type = party_type
    pe.party = customer

    pe.paid_from = party_account if payment_type == "Receive" else bank.account
    pe.paid_to = party_account if payment_type == "Pay" else bank.account
    pe.paid_from_account_currency = (
        party_account_currency if payment_type == "Receive" else bank.account_currency
    )
    pe.paid_to_account_currency = (
        party_account_currency if payment_type == "Pay" else bank.account_currency
    )
    pe.paid_amount = paid_amount
    pe.received_amount = received_amount
    pe.letter_head = frappe.get_value("Company", company, "default_letter_head")
    pe.reference_date = reference_date
    pe.reference_no = reference_no
    if pe.party_type in ["Customer", "Supplier"]:
        bank_account = get_party_bank_account(pe.party_type, pe.party)
        pe.set("bank_account", bank_account)
        pe.set_bank_account_data()

    pe.setup_party_account_field()
    pe.set_missing_values()

    if party_account and bank:
        pe.set_amounts()
    if submit:
        pe.docstatus = 1
    pe.insert(ignore_permissions=True)
    return pe


def get_bank_cash_account(company, mode_of_payment, bank_account=None):
    bank = get_default_bank_cash_account(
        company, "Bank", mode_of_payment=mode_of_payment, account=bank_account
    )

    if not bank:
        bank = get_default_bank_cash_account(
            company, "Cash", mode_of_payment=mode_of_payment, account=bank_account
        )

    return bank


def set_paid_amount_and_received_amount(
    party_account_currency,
    bank,
    outstanding_amount,
    payment_type,
    bank_amount,
    conversion_rate,
):
    paid_amount = received_amount = 0
    if party_account_currency == bank.account_currency:
        paid_amount = received_amount = abs(outstanding_amount)
    elif payment_type == "Receive":
        paid_amount = abs(outstanding_amount)
        if bank_amount:
            received_amount = bank_amount
        else:
            received_amount = paid_amount * conversion_rate

    else:
        received_amount = abs(outstanding_amount)
        if bank_amount:
            paid_amount = bank_amount
        else:
            # if party account currency and bank currency is different then populate paid amount as well
            paid_amount = received_amount * conversion_rate

    return paid_amount, received_amount


@frappe.whitelist()
def get_outstanding_invoices_driver(company, currency, driver=None,customer=None, pos_profile_name=None):
    if driver:
        filters = {
            "company": company,
            "outstanding_amount": (">", 0),
            "docstatus": 1,
            "is_return": 0,
            "currency": currency,
        }
        if driver:
            filters.update({"driver": driver})
        if pos_profile_name:
            filters.update({"pos_profile": pos_profile_name})
        invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=[
                "name",
                "customer",
                "customer_name",
                "outstanding_amount",
                "grand_total",
                "due_date",
                "posting_date",
                "currency",
                "pos_profile",
                "driver",
                "custom_payment_type",
                "custom_so_type",
                "custom_receipt_number",
                "custom_number_order"
            ],
            order_by="due_date desc",
        )
        return invoices
    
    else:
        filters = {
            "company": company,
            "outstanding_amount": (">", 0),
            "docstatus": 1,
            "is_return": 0,
            "currency": currency,
        }
        if customer:
            filters.update({"customer": customer})
        if pos_profile_name:
            filters.update({"pos_profile": pos_profile_name})
        invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=[
                "name",
                "customer",
                "customer_name",
                "outstanding_amount",
                "grand_total",
                "due_date",
                "posting_date",
                "currency",
                "pos_profile",
                "driver",
                "custom_payment_type",
                "custom_so_type",
                "custom_receipt_number",
                "custom_number_order"
            ],
            order_by="due_date desc",
        )
        for inv in invoices:
            voucher_no = inv.name
            custom_number_order = inv.get("custom_number_order")
            inv["custom_number_order_display"] = (
                f"# {custom_number_order}" if custom_number_order else f"# {voucher_no}"
            )
        return invoices

# i used this instead of the above function to avoid the error of the custom_number_order not being set and used sql instead of frappe.get_all
@frappe.whitelist()
def get_outstanding_invoices_driver_cpy(company, currency, driver=None, customer=None, pos_profile_name=None):
    # Build WHERE conditions dynamically
    conditions = [
        "si.company=%s",
        "si.outstanding_amount > 0",
        "si.docstatus=1",
        "si.is_return=0",
        "si.currency=%s"
    ]
    values = [company, currency]

    if driver:
        conditions.append("si.driver=%s")
        values.append(driver)
    if customer:
        conditions.append("si.customer=%s")
        values.append(customer)
    if pos_profile_name:
        conditions.append("si.pos_profile=%s")
        values.append(pos_profile_name)

    where_clause = " AND ".join(conditions)

    invoices = frappe.db.sql(f"""
        SELECT 
            si.name,
            si.customer,
            si.customer_name,
            si.outstanding_amount,
            si.grand_total,
            si.due_date,
            si.posting_date,
            si.currency,
            si.pos_profile,
            si.driver,
            si.custom_payment_type,
            si.custom_so_type,
            si.custom_receipt_number,
            CASE 
                WHEN so.custom_number_order IS NOT NULL AND so.custom_number_order != ''
                THEN CONCAT('# ', so.custom_number_order)
                ELSE CONCAT('# ', si.name)
            END AS custom_number_order
        FROM `tabSales Invoice` si
        LEFT JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabSales Order` so ON so.name = sii.sales_order
        WHERE {where_clause}
        ORDER BY si.due_date DESC
    """, tuple(values), as_dict=True)

    return invoices


@frappe.whitelist()
def get_outstanding_invoices(company, currency, customer=None, pos_profile_name=None, driver=None):
    if customer:
        precision = frappe.get_precision("Sales Invoice", "outstanding_amount") or 2
        outstanding_invoices = _get_outstanding_invoices(
            party_type="Customer",
            party=customer,
            account=get_party_account("Customer", customer, company),
        )
        invoices_list = []
        customer_name = frappe.get_cached_value("Customer", customer, "customer_name")

        for invoice in outstanding_invoices:
            if invoice.get("currency") == currency:
                # If pos_profile_name provided and NOT "Call Center", apply filter
                if pos_profile_name and pos_profile_name != "Call Center":
                    if frappe.get_cached_value("Sales Invoice", invoice.get("voucher_no"), "pos_profile") != pos_profile_name:
                        continue

                invoice_driver = frappe.get_cached_value(
                    "Sales Invoice", invoice.get("voucher_no"), "driver"
                )
                if driver and invoice_driver != driver:
                    continue

                voucher_no = invoice.get("voucher_no")
                custom_number_order = None
                custom_table_no = None
                if voucher_no:
                    sales_order = frappe.db.get_value(
                        "Sales Invoice Item", {"parent": voucher_no}, "sales_order"
                    )
                    if sales_order:
                        custom_number_order = frappe.db.get_value(
                            "Sales Order", sales_order, "custom_number_order"
                        )
                        custom_table_no = frappe.get_cached_value(
                            "Sales Order", sales_order, "custom_table_no"
                        )

                outstanding_amount = invoice.outstanding_amount
                if outstanding_amount > 0.5 / (10**precision):
                    invoices_list.append({
                        "name": voucher_no,
                        "customer": customer,
                        "customer_name": customer_name,
                        "outstanding_amount": invoice.get("outstanding_amount"),
                        "grand_total": invoice.get("invoice_amount"),
                        "due_date": invoice.get("due_date"),
                        "posting_date": invoice.get("posting_date"),
                        "currency": invoice.get("currency"),
                        "custom_table_no": custom_table_no if custom_table_no else "",
                        "custom_number_order": f"# {custom_number_order}" if custom_number_order else f"# {voucher_no}",
                        "custom_payment_type": frappe.get_cached_value("Sales Invoice", invoice.get("voucher_no"), "custom_payment_type"),
                        "custom_so_type": frappe.get_cached_value("Sales Invoice", invoice.get("voucher_no"), "custom_so_type") ,
                        "pos_profile": pos_profile_name,
                        "driver": invoice_driver,
                    })
        return invoices_list

    else:
        filters = {
            "company": company,
            "outstanding_amount": (">", 0),
            "docstatus": 1,
            "is_return": 0,
            "currency": currency,
        }
        if customer:
            filters.update({"customer": customer})
        # Only filter by pos_profile if it's provided and NOT "Call Center"
        if pos_profile_name and pos_profile_name != "Call Center":
            filters.update({"pos_profile": pos_profile_name})
        if driver:
            filters.update({"driver": driver})

        invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=[
                "name",
                "customer",
                "customer_name",
                "outstanding_amount",
                "grand_total",
                "due_date",
                "posting_date",
                "currency",
                "pos_profile",
                "driver",
                "custom_payment_type",
                "custom_so_type",
                "custom_receipt_number",
            ],
            order_by="posting_date desc",
        )

        for invoice in invoices:
            sales_order = frappe.db.get_value(
                "Sales Invoice Item", {"parent": invoice["name"]}, "sales_order"
            )
            if sales_order:
                custom_number_order = frappe.db.get_value(
                    "Sales Order", sales_order, "custom_number_order"
                )
                invoice["custom_number_order"] = f"# {custom_number_order}" if custom_number_order else f"# {invoice.get('name')}"
                custom_table_no = frappe.get_cached_value(
                            "Sales Order", sales_order, "custom_table_no"
                        )
                invoice["custom_table_no"] = f"{custom_table_no}" if custom_table_no else f""
                
        return invoices



# @frappe.whitelist()
# def get_outstanding_invoices(company, currency, customer=None, pos_profile_name=None, driver=None):
#     if customer:
#         precision = frappe.get_precision("Sales Invoice", "outstanding_amount") or 2
#         outstanding_invoices = _get_outstanding_invoices(
#             party_type="Customer",
#             party=customer,
#             account=get_party_account("Customer", customer, company),
#         )
#         invoices_list = []
#         customer_name = frappe.get_cached_value("Customer", customer, "customer_name")
#         for invoice in outstanding_invoices:
#             if invoice.get("currency") == currency:
#                 if pos_profile_name and frappe.get_cached_value(
#                     "Sales Invoice", invoice.get("voucher_no"), "pos_profile"
#                 ) != pos_profile_name:
#                     continue
#                 outstanding_amount = invoice.outstanding_amount
#                 if outstanding_amount > 0.5 / (10**precision):
#                     invoice_dict = {
#                         "name": invoice.get("voucher_no"),
#                         "customer": customer,
#                         "customer_name": customer_name,
#                         "outstanding_amount": invoice.get("outstanding_amount"),
#                         "grand_total": invoice.get("invoice_amount"),
#                         "due_date": invoice.get("due_date"),
#                         "posting_date": invoice.get("posting_date"),
#                         "currency": invoice.get("currency"),
#                         "pos_profile": pos_profile_name,
#                         "driver": invoice.get("driver"),

#                     }
#                     invoices_list.append(invoice_dict)
#         return invoices_list
#     else:
#         filters = {
#             "company": company,
#             "outstanding_amount": (">", 0),
#             "docstatus": 1,
#             "is_return": 0,
#             "currency": currency,
#         }
#         if customer:
#             filters.update({"customer": customer})
#         if pos_profile_name:
#             filters.update({"pos_profile": pos_profile_name})
#         invoices = frappe.get_all(
#             "Sales Invoice",
#             filters=filters,
#             fields=[
#                 "name",
#                 "customer",
#                 "customer_name",
#                 "outstanding_amount",
#                 "grand_total",
#                 "due_date",
#                 "posting_date",
#                 "currency",
#                 "pos_profile",
#             ],
#             order_by="due_date asc",
#         )
#         return invoices


@frappe.whitelist()
def get_unallocated_payments(customer, company, currency, mode_of_payment=None):
    filters = {
        "party": customer,
        "company": company,
        "docstatus": 1,
        "party_type": "Customer",
        "payment_type": "Receive",
        "unallocated_amount": [">", 0],
        "paid_from_account_currency": currency,
    }
    if mode_of_payment:
        filters.update({"mode_of_payment": mode_of_payment})
    unallocated_payment = frappe.get_all(
        "Payment Entry",
        filters=filters,
        fields=[
            "name",
            "paid_amount",
            "party_name as customer_name",
            "received_amount",
            "posting_date",
            "unallocated_amount",
            "mode_of_payment",
            "paid_from_account_currency as currency",
        ],
        order_by="posting_date asc",
    )
    return unallocated_payment

@frappe.whitelist()
def create_pos_payment_entry(payload):
    data = json.loads(payload)
    data = frappe._dict(data)
    invoice_doc = frappe.get_doc("Sales Invoice", data.selected_invoice)
    
    # Check if invoice is already fully paid
    if flt(invoice_doc.outstanding_amount) <= 0:
        if invoice_name:
            frappe.cache().redis.delete(lock_key)
        frappe.throw(_("Invoice {0} is already fully paid").format(invoice_name))
    if not data.pos_profile.get("posa_use_pos_awesome_payments"):
        frappe.throw(_("POS Awesome Payments is not enabled for this POS Profile"))
    if invoice_doc.custom_table_number and invoice_doc.custom_so_type == "Dinin":
        frappe.log_error('Table Number', invoice_doc.custom_table_number)
        frappe.db.set_value('Table Number', invoice_doc.custom_table_number,"disabled", 0)
    # validate data
    # if not data.customer:
    #     frappe.throw(_("Customer is required"))
    # if not data.company:
    #     frappe.throw(_("Company is required"))
    # if not data.currency:
    #     frappe.throw(_("Currency is required"))
    # if not data.pos_profile_name:
    #     frappe.throw(_("POS Profile is required"))
    # if not data.pos_opening_shift_name:
    #     frappe.throw(_("POS Opening Shift is required"))
    party_type = "Customer"
    party_account = get_party_account(party_type, invoice_doc.customer, invoice_doc.company)
    party_account_currency = get_account_currency(party_account)
    if party_account_currency != invoice_doc.currency:
        frappe.throw(
            _(
                "Currency is not correct, party account currency is {party_account_currency} and transaction currency is {currency}"
            ).format(party_account_currency=party_account_currency, currency=invoice_doc.currency)
        )
    payment_type = "Receive"



    pos_opening_shift_name = data.pos_opening_shift_name
    pos_profile_name = data.pos_profile_name or ""
    is_call_center = pos_profile_name == "Call Center"
    # frappe.throw(f"{is_call_center}")
    # Get branch from invoice
    invoice_branch = invoice_doc.get("branch") or ""
    
    today = nowdate()
    errors = []

    new_payments_entry = []
    all_payments_entry = []
    for payment_method in data.payment_methods:
        amount = flt(payment_method.get("amount") or 0)
        if not amount:
            continue
        bank = get_bank_cash_account(invoice_doc.company, payment_method.get("mode_of_payment"))
        company_currency = frappe.get_value("Company", invoice_doc.company, "default_currency")
        conversion_rate = get_exchange_rate(invoice_doc.currency, company_currency, frappe.utils.today(), "for_selling")
        paid_amount, received_amount = set_paid_amount_and_received_amount(
            party_account_currency, bank, amount, payment_type, None, conversion_rate
        )
        paid_to = party_account if payment_type == "Pay" else bank.account
        paid_from_account_currency = (
            party_account_currency if payment_type == "Receive" else bank.account_currency
        )
        paid_to_account_currency = (
            party_account_currency if payment_type == "Pay" else bank.account_currency
        )
        payment_entry_doc = frappe.get_doc({
            "doctype": "Payment Entry",
            "posting_date": frappe.utils.today(),
            "payment_type": "Receive",
            "party_type": "Customer",
            "party": invoice_doc.customer,
            "paid_amount": amount,
            "received_amount": amount,
            "paid_from": invoice_doc.debit_to,
            "paid_to": paid_to,
            "company": invoice_doc.company,
            "paid_from_account_currency":paid_from_account_currency,
            "paid_to_account_currency": paid_to_account_currency,
            "mode_of_payment": payment_method.get("mode_of_payment"),
            "reference_no": pos_opening_shift_name,
            "reference_date": frappe.utils.today(),
            "target_exchange_rate": 1,
            "branch": invoice_branch,
        })

        payment_reference = {
            "allocated_amount": amount,
            "due_date": data.get("due_date"),
            "reference_doctype": "Sales Invoice",
            "reference_name": invoice_doc.name,
        }

        payment_entry_doc.append("references", payment_reference)
        payment_entry_doc.flags.ignore_permissions = True
        frappe.flags.ignore_account_permission = True
        payment_entry_doc.save()
        
        # Only submit if NOT Call Center - keep as Draft for Call Center
        if not is_call_center:
            payment_entry_doc.submit()
@frappe.whitelist()
def process_pos_payment(payload):
    data = json.loads(payload)
    data = frappe._dict(data)
    if not data.pos_profile.get("posa_use_pos_awesome_payments"):
        frappe.throw(_("POS Awesome Payments is not enabled for this POS Profile"))

    # validate data
    if not data.customer:
        frappe.throw(_("Customer is required"))
    if not data.company:
        frappe.throw(_("Company is required"))
    if not data.currency:
        frappe.throw(_("Currency is required"))
    if not data.pos_profile_name:
        frappe.throw(_("POS Profile is required"))
    if not data.pos_opening_shift_name:
        frappe.throw(_("POS Opening Shift is required"))
    
    # Validate selected invoices - check if any invoice is already fully paid
    for invoice in data.get("selected_invoices") or []:
        inv_name = invoice.get("name")
        if inv_name:
            current_outstanding = frappe.db.get_value("Sales Invoice", inv_name, "outstanding_amount") or 0
            if flt(current_outstanding) <= 0:
                frappe.throw(_("Invoice {0} is already fully paid").format(inv_name))

    company = data.company
    currency = data.currency
    customer = data.customer
    pos_opening_shift_name = data.pos_opening_shift_name
    
    allow_make_new_payments = data.pos_profile.get("posa_allow_make_new_payments")
    allow_reconcile_payments = data.pos_profile.get("posa_allow_reconcile_payments")
    allow_mpesa_reconcile_payments = data.pos_profile.get(
        "posa_allow_mpesa_reconcile_payments"
    )
    today = nowdate()

    new_payments_entry = []
    all_payments_entry = []
    errors = []
    reconcile_doc = None

    # first process mpesa payments
    if (
        allow_mpesa_reconcile_payments
        and len(data.selected_mpesa_payments) > 0
        and data.total_selected_mpesa_payments > 0
    ):
        for mpesa_payment in data.selected_mpesa_payments:
            try:
                new_mpesa_payment = submit_mpesa_payment(
                    mpesa_payment.get("name"), customer
                )
                new_payments_entry.append(new_mpesa_payment)
                all_payments_entry.append(new_mpesa_payment)
            except Exception as e:
                errors.append(e)

    # then process the new payments
    if (
        allow_make_new_payments
        and len(data.payment_methods) > 0
        and data.total_payment_methods > 0
    ):
        for payment_method in data.payment_methods:
            try:
                if not payment_method.get("amount"):
                    continue
                new_payment_entry = create_payment_entry(
                    company=company,
                    customer=customer,
                    currency=currency,
                    amount=flt(payment_method.get("amount")),
                    mode_of_payment=payment_method.get("mode_of_payment"),
                    posting_date=today,
                    reference_no=pos_opening_shift_name,
                    reference_date=today,
                    cost_center=data.pos_profile.get("cost_center"),
                    submit=1,
                )
                new_payments_entry.append(new_payment_entry)
                all_payments_entry.append(new_payment_entry)
            except Exception as e:
                errors.append(e)
        

    # then then reconcile the new payments and the unallocated payments with the outstanding invoices
    if len(data.selected_invoices) > 0 and data.total_selected_invoices > 0:
        if (
            allow_reconcile_payments
            and len(data.selected_payments) > 0
            and data.total_selected_payments > 0
        ):
            # add the unallocated payments to the all payments entry
            for selected_payment in data.selected_payments:
                all_payments_entry.append(selected_payment)

        if len(all_payments_entry) > 0:
            # sort the all payments entry by posting date
            all_payments_entry = sorted(
                all_payments_entry,
                key=lambda k: getdate(str(k.get("posting_date"))),
                reverse=True,
            )
            all_invoices_list = sorted(
                data.selected_invoices,
                key=lambda k: getdate(k.get("posting_date")),
                reverse=True,
            )
            reconcile_doc = frappe.new_doc("Payment Reconciliation")
            reconcile_doc.party_type = "Customer"
            reconcile_doc.party = customer
            reconcile_doc.company = company
            reconcile_doc.receivable_payable_account = get_party_account(
                "Customer", customer, company
            )
            reconcile_doc.get_unreconciled_entries()
            args = {
                "invoices": [],
                "payments": [],
            }
            for invoice in all_invoices_list:
                if invoice.get("name"):
                    inv = frappe.get_doc('Sales Invoice', invoice.get("name"))
                    if inv.custom_table_number and inv.custom_so_type == "Dinin":
                        frappe.db.set_value('Table Number', inv.custom_table_number,"disabled", 0)
                args["invoices"].append(
                    {
                        "invoice_type": "Sales Invoice",
                        "invoice_number": invoice.get("name"),
                        "invoice_date": invoice.get("posting_date"),
                        "amount": invoice.get("grand_total"),
                        "outstanding_amount": invoice.get("outstanding_amount"),
                        "currency": invoice.get("currency"),
                        "exchange_rate": 0,
                    }
                )
                
                if data.custom_receipt_number:
                    frappe.db.set_value(
                        "Sales Invoice",
                        invoice.get("name"),
                        "custom_receipt_number",
                        data.custom_receipt_number
                    )
            # frappe.throw(f"{args['invoices']}")
            for payment in all_payments_entry:
                args["payments"].append(
                    {
                        "reference_type": "Payment Entry",
                        "reference_name": payment.get("name"),
                        "posting_date": payment.get("posting_date"),
                        "amount": payment.get("unallocated_amount"),
                        "unallocated_amount": payment.get("unallocated_amount"),
                        "difference_amount": 0,
                        "currency": payment.get("currency"),
                        "exchange_rate": 0,
                    }
                )
            reconcile_doc.allocate_entries(args)
            reconcile_doc.reconcile()

    # then show the results
    msg = ""
    if len(new_payments_entry) > 0:
        msg += "<h4>New Payments</h4>"
        msg += "<table class='table table-bordered'>"
        msg += "<thead><tr><th>Payment Entry</th><th>Amount</th></tr></thead>"
        msg += "<tbody>"
        for payment_entry in new_payments_entry:
            msg += "<tr><td>{0}</td><td>{1}</td></tr>".format(
                payment_entry.get("name"), payment_entry.get("unallocated_amount")
            )
        msg += "</tbody>"
        msg += "</table>"
    if len(all_payments_entry) > 0 and len(data.selected_invoices) > 0:
        msg += "<h4>Reconciled Payments</h4>"
        msg += "<table class='table table-bordered'>"
        msg += "<thead><tr><th>Payment Entry</th><th>Amount</th></tr></thead>"
        msg += "<tbody>"
        for payment_entry in all_payments_entry:
            msg += "<tr><td>{0}</td><td>{1}</td></tr>".format(
                payment_entry.get("name"), payment_entry.get("unallocated_amount")
            )
        msg += "</tbody>"
        msg += "</table>"
    if len(data.selected_invoices) > 0 and data.total_selected_invoices > 0:
        msg += "<h4>Reconciled Invoices</h4>"
        msg += "<table class='table table-bordered'>"
        msg += "<thead><tr><th>Invoice</th><th>Amount</th></tr></thead>"
        msg += "<tbody>"
        for invoice in data.selected_invoices:
            msg += "<tr><td>{0}</td><td>{1}</td></tr>".format(
                invoice.get("name"), invoice.get("outstanding_amount")
            )
        msg += "</tbody>"
        msg += "</table>"
    if len(errors) > 0:
        msg += "<h4>Errors</h4>"
        msg += "<table class='table table-bordered'>"
        msg += "<thead><tr><th>Error</th></tr></thead>"
        msg += "<tbody>"
        for error in errors:
            msg += "<tr><td>{0}</td></tr>".format(error)
        msg += "</tbody>"
        msg += "</table>"
    # if len(msg) > 0:
    #     frappe.msgprint(msg)

    return {
        "new_payments_entry": new_payments_entry,
        "all_payments_entry": all_payments_entry,
        "errors": errors,
        "reconcile_doc": reconcile_doc,
    }


@frappe.whitelist()
def get_available_pos_profiles(company, currency):
    pos_profiles_list = frappe.get_list(
        "POS Profile",
        filters={"disabled": 0, "company": company, "currency": currency},
        page_length=1000,
        pluck="name",
    )
    return pos_profiles_list

@frappe.whitelist()
def get_mode_of_payment_custom_sales_person(mode_of_payment_name):
    mop = frappe.get_doc("Mode of Payment", mode_of_payment_name)
    return mop.custom_sales_person


@frappe.whitelist()
def get_pending_payment_entries(branch=None, date_from=None, date_to=None):
    """Get draft payment entries for supervisor approval"""
    # Check if user has Branch supervisor role
    if "Branch supervisor" not in frappe.get_roles():
        frappe.throw(_("You do not have permission to view pending payments"))
    
    # Get branches user has permission to see
    allowed_branches = frappe.get_list(
        "User Permission",
        filters={
            "user": frappe.session.user,
            "allow": "Branch"
        },
        pluck="for_value"
    )
    
    filters = {
        "docstatus": 0,  # Draft
        "payment_type": "Receive",
    }
    
    # Filter by allowed branches
    if branch:
        # If specific branch requested, check if user has permission
        if allowed_branches and branch not in allowed_branches:
            frappe.throw(_("You do not have permission to view this branch"))
        filters["branch"] = branch
    elif allowed_branches:
        # If no specific branch, filter by all allowed branches
        filters["branch"] = ["in", allowed_branches]
    
    if date_from:
        filters["posting_date"] = [">=", date_from]
    
    if date_to:
        if "posting_date" in filters:
            filters["posting_date"] = ["between", [date_from, date_to]]
        else:
            filters["posting_date"] = ["<=", date_to]
    
    payments = frappe.get_all(
        "Payment Entry",
        filters=filters,
        fields=[
            "name",
            "posting_date",
            "party",
            "party_name",
            "branch",
            "mode_of_payment",
            "paid_amount",
            "reference_no",
            "custom_closed"
        ],
        order_by="posting_date desc",
        limit_page_length=200,
    )
    
    # Get invoice references for each payment
    for payment in payments:
        refs = frappe.get_all(
            "Payment Entry Reference",
            filters={"parent": payment.name},
            fields=["reference_doctype", "reference_name", "allocated_amount"],
        )
        payment["references"] = refs
    
    return payments


@frappe.whitelist()
def approve_payment_entry(payment_entry):
    """Submit a draft payment entry (approve it)"""
    # Check if user has Branch supervisor role
    if "Branch supervisor" not in frappe.get_roles():
        frappe.throw(_("You do not have permission to approve payments"))
    
    pe = frappe.get_doc("Payment Entry", payment_entry)
    if pe.docstatus != 0:
        frappe.throw(_("Payment Entry is not in Draft status"))
    
    pe.flags.ignore_permissions = True
    frappe.flags.ignore_account_permission = True
    pe.submit()
    frappe.db.commit()
    
    return {"status": "success", "message": _("Payment Entry approved")}


@frappe.whitelist()
def reject_payment_entry(payment_entry, reason=None):
    """Cancel/delete a draft payment entry (reject it)"""
    # Check if user has Branch supervisor role
    if "Branch supervisor" not in frappe.get_roles():
        frappe.throw(_("You do not have permission to reject payments"))
    
    pe = frappe.get_doc("Payment Entry", payment_entry)
    if pe.docstatus != 0:
        frappe.throw(_("Payment Entry is not in Draft status"))
    
    # Log the rejection reason
    if reason:
        frappe.log_error(
            title=f"Payment Entry Rejected: {payment_entry}",
            message=f"Reason: {reason}\nRejected by: {frappe.session.user}"
        )
    

    if pe.custom_closed == 1:
        frappe.throw("Payment Entry is already rejected")
    else:
        pe.custom_closed = 1
        pe.flags.ignore_permissions = True
        pe.save()
        frappe.db.commit()
    
    return {"status": "success", "message": _("Payment Entry rejected")}
