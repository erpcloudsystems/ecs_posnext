import frappe
import requests
from frappe import _


def get_token(app_key, app_secret, base_url):
	"""Get M-Pesa OAuth token.

	Args:
		app_key: Consumer key from M-Pesa app
		app_secret: Consumer secret from M-Pesa app
		base_url: Safaricom API base URL

	Returns:
		Access token string
	"""
	url = base_url + "/oauth/v1/generate?grant_type=client_credentials"
	response = requests.get(url, auth=(app_key, app_secret))
	response.raise_for_status()
	return response.json().get("access_token")


@frappe.whitelist(allow_guest=True)
def validation(**kwargs):
	"""M-Pesa C2B validation callback."""
	return {"ResultCode": 0, "ResultDesc": "Accepted"}


@frappe.whitelist(allow_guest=True)
def confirmation(**kwargs):
	"""M-Pesa C2B confirmation callback.

	Creates an Mpesa Payment Register record from the M-Pesa transaction data.
	"""
	data = frappe.request.get_json(force=True) if frappe.request else kwargs

	try:
		doc = frappe.get_doc(
			{
				"doctype": "Mpesa Payment Register",
				"transactiontype": data.get("TransactionType"),
				"transid": data.get("TransID"),
				"transamount": data.get("TransAmount"),
				"businessshortcode": data.get("BusinessShortCode"),
				"billrefnumber": data.get("BillRefNumber"),
				"invoicenumber": data.get("InvoiceNumber"),
				"orgaccountbalance": data.get("OrgAccountBalance"),
				"thirdpartytransid": data.get("ThirdPartyTransID"),
				"msisdn": data.get("MSISDN"),
				"firstname": data.get("FirstName"),
				"middlename": data.get("MiddleName"),
				"lastname": data.get("LastName"),
				"posting_date": frappe.utils.nowdate(),
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="M-Pesa Confirmation Error")

	return {"ResultCode": 0, "ResultDesc": "Accepted"}
