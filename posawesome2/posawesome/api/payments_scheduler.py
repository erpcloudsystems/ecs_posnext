# -*- coding: utf-8 -*-
# Copyright (c) 2026, and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, add_days, get_datetime, getdate, flt


def create_daily_payments():
    """
    Scheduled job that runs daily at 7 AM.
    Fetches POS Closing Shifts created between 13:00 yesterday and 06:00 today,
    gets their Sales Invoices, and creates Payments documents with payment breakdown.
    """
    today = getdate(nowdate())
    yesterday = add_days(today, -1)
    
    # Time window: yesterday 13:00 to today 06:00
    start_datetime = get_datetime(f"{yesterday} 13:00:00")
    end_datetime = get_datetime(f"{today} 06:00:00")
    
    # Get all submitted POS Closing Shifts in the time window
    closing_shifts = frappe.db.sql("""
        SELECT name, pos_profile, company
        FROM `tabPOS Closing Shift`
        WHERE docstatus = 1
        AND creation BETWEEN %s AND %s
    """, (start_datetime, end_datetime), as_dict=True)
    
    if not closing_shifts:
        frappe.logger().info("No POS Closing Shifts found for the period")
        frappe.log_error("No POS Closing Shifts found for the period", "No POS Closing Shifts found for the period")
        return
    
    # Collect all payment rows
    payment_rows = []
    total_instapay = 0
    total_credit = 0
    total_vodafon_cash = 0
    
    for shift in closing_shifts:
        # Get Sales Invoices from pos_transactions child table
        invoices = frappe.db.sql("""
            SELECT sir.sales_invoice
            FROM `tabSales Invoice Reference` sir
            WHERE sir.parent = %s
        """, shift.name, as_dict=True)
        
        for inv_row in invoices:
            inv_name = inv_row.sales_invoice
            if not inv_name:
                continue
            
            # Get invoice details
            inv = frappe.db.get_value(
                "Sales Invoice",
                inv_name,
                ["name", "owner"],
                as_dict=True
            )
            
            if not inv:
                continue
            
            # Get payments from Sales Invoice Payment (inline payments)
            si_payments = frappe.get_all(
                "Sales Invoice Payment",
                filters={"parent": inv_name},
                fields=["mode_of_payment", "amount"]
            )
            
            # Get payments from Payment Entry (separate payment entries)
            pe_payments = frappe.db.sql("""
                SELECT pe.mode_of_payment, per.allocated_amount as amount
                FROM `tabPayment Entry` pe
                INNER JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
                WHERE per.reference_doctype = 'Sales Invoice'
                AND per.reference_name = %s
                AND pe.docstatus = 1
            """, inv_name, as_dict=True)
            
            # Combine both payment sources
            all_payments = list(si_payments) + list(pe_payments)
            
            instapay = 0
            credit_card = 0
            vodafon_cash = 0
            mode_of_payment = None
            
            for payment in all_payments:
                mop = (payment.mode_of_payment or "").lower()
                if "insta pay" in mop:
                    instapay += flt(payment.amount)
                    mode_of_payment = payment.mode_of_payment
                elif "credit" in mop or "card" in mop or "visa" in mop:
                    credit_card += flt(payment.amount)
                    mode_of_payment = payment.mode_of_payment
                elif "vodafone" in mop or "vodafon" in mop:
                    vodafon_cash += flt(payment.amount)
                    mode_of_payment = payment.mode_of_payment
            
            # Only add if there's a non-cash payment
            if instapay or credit_card or vodafon_cash:
                payment_rows.append({
                    "mode_of_payment": mode_of_payment,
                    "sales_invoice": inv.name,
                    "instapay": instapay,
                    "credit_card": credit_card,
                    "vodafon_cash": vodafon_cash,
                    "created_by": inv.owner,
                })
                total_instapay += instapay
                total_credit += credit_card
                total_vodafon_cash += vodafon_cash
    
    if not payment_rows:
        frappe.logger().info("No non-cash payments found for the period")
        frappe.log_error("No non-cash payments found for the period", "No non-cash payments found for the period")
        
        return
    
    # Check if document already exists for this date
    existing = frappe.db.exists("Payments", {"date": yesterday})
    
    if existing:
        frappe.logger().info(f"Payments document already exists for {yesterday}")
        frappe.log_error("Payments document already exists for {yesterday}", "Payments document already exists for {yesterday}")
        return
    
    # Create new Payments document
    payments_doc = frappe.new_doc("Payments")
    payments_doc.date = yesterday
    payments_doc.total_instapay = total_instapay
    payments_doc.total_credit = total_credit
    payments_doc.total_vodafon_cash = total_vodafon_cash
    
    for row in payment_rows:
        payments_doc.append("payment_table", row)
    
    payments_doc.insert(ignore_permissions=True)
    frappe.db.commit()
    
    frappe.logger().info(f"Created Payments document for {yesterday} with {len(payment_rows)} payments")


@frappe.whitelist()
def run_payments_scheduler_manually():
    """Manual trigger for testing"""
    create_daily_payments()
    return "Done"
