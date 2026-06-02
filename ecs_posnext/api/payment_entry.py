import frappe
from frappe import _


def create_payment_entry(
	company,
	customer,
	amount,
	currency,
	mode_of_payment,
	posting_date,
	reference_no,
	reference_date,
	sales_invoice=None,
	submit=False,
):
	"""Create a Payment Entry for M-Pesa payments.

	Args:
		company: Company name
		customer: Customer name
		amount: Payment amount
		currency: Currency code (e.g. KES)
		mode_of_payment: Mode of Payment name
		posting_date: Date of payment
		reference_no: Transaction reference number
		reference_date: Reference date
		sales_invoice: Optional Sales Invoice to link
		submit: Whether to submit the Payment Entry

	Returns:
		Payment Entry document
	"""
	mode_of_payment_doc = frappe.get_doc("Mode of Payment", mode_of_payment)
	company_account = None
	for account in mode_of_payment_doc.accounts:
		if account.company == company:
			company_account = account.default_account
			break

	if not company_account:
		frappe.throw(
			_("No default account set for Mode of Payment {0} in Company {1}").format(
				mode_of_payment, company
			)
		)

	payment_entry = frappe.get_doc(
		{
			"doctype": "Payment Entry",
			"payment_type": "Receive",
			"posting_date": posting_date,
			"company": company,
			"mode_of_payment": mode_of_payment,
			"party_type": "Customer",
			"party": customer,
			"paid_amount": amount,
			"received_amount": amount,
			"paid_to": company_account,
			"paid_to_account_currency": currency,
			"reference_no": reference_no,
			"reference_date": reference_date,
		}
	)

	if sales_invoice:
		payment_entry.append(
			"references",
			{
				"reference_doctype": "Sales Invoice",
				"reference_name": sales_invoice,
				"allocated_amount": amount,
			},
		)

	payment_entry.insert(ignore_permissions=True)

	if submit:
		payment_entry.submit()

	return payment_entry
