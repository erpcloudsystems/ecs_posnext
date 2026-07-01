# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesOrder as BaseSalesOrder


import frappe
from frappe import _, msgprint, throw
from frappe.contacts.doctype.address.address import get_address_display
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.utils import add_days, cint, cstr, flt, formatdate, get_link_to_form, getdate, nowdate

import erpnext
from erpnext.accounts.deferred_revenue import validate_service_stop_date
from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
    get_loyalty_program_details_with_points,
    validate_loyalty_points,
)
from erpnext.accounts.doctype.repost_accounting_ledger.repost_accounting_ledger import (
    validate_docs_for_deferred_accounting,
    validate_docs_for_voucher_types,
)
from erpnext.accounts.doctype.tax_withholding_category.tax_withholding_category import (
    get_party_tax_withholding_details,
)
from erpnext.accounts.general_ledger import get_round_off_account_and_cost_center
from erpnext.accounts.doctype.sales_invoice.sales_invoice import update_multi_mode_option
from erpnext.accounts.party import get_due_date, get_party_account, get_party_details
from erpnext.accounts.utils import (
    cancel_exchange_gain_loss_journal,
    get_account_currency,
    update_voucher_outstanding,
)
from erpnext.assets.doctype.asset.depreciation import (
    depreciate_asset,
    get_disposal_account_and_cost_center,
    get_gl_entries_on_asset_disposal,
    get_gl_entries_on_asset_regain,
    reset_depreciation_schedule,
    reverse_depreciation_entry_made_after_disposal,
)
from erpnext.controllers.accounts_controller import validate_account_head
from erpnext.controllers.selling_controller import SellingController
from erpnext.projects.doctype.timesheet.timesheet import get_projectwise_timesheet_data
from erpnext.setup.doctype.company.company import update_company_current_month_sales
from erpnext.stock.doctype.batch.batch import set_batch_nos
from erpnext.stock.doctype.delivery_note.delivery_note import update_billed_amount_based_on_so
from erpnext.stock.doctype.serial_no.serial_no import (
    get_delivery_note_serial_no,
    get_serial_nos,
    update_serial_nos_after_submit,
)
def check_item_maintains_stock(item_code):
    maintain_stock = frappe.db.get_value("Item", item_code, "is_stock_item")
    return bool(maintain_stock)
class SalesOrder(BaseSalesOrder):
    def update_packing_list(self):

    # if cint(self.update_stock) == 1:
    # 	from erpnext.stock.doctype.packed_item.packed_item import make_packing_list

    # 	make_packing_list(self)
    # else:
    # 	self.set("packed_items", [])
        pass
    
    def get_item_list(self):
        il = []
        for d in self.get("items"):
            if d.qty is None:
                frappe.throw(_("Row {0}: Qty is mandatory").format(d.idx))
            # frappe.throw(f"{il}")
            for p in self.get("packed_items"):
                if check_item_maintains_stock(p.item_code):
                    # if p.parent_detail_docname == d.name and p.parent_item == d.item_code:
                        # the packing details table's qty is already multiplied with parent's qty
                        
                    il.append(
                        frappe._dict(
                            {
                                "warehouse": p.warehouse or d.warehouse,
                                "item_code": p.item_code,
                                "qty": flt(p.qty),
                                "uom": p.uom,
                                "batch_no": cstr(p.batch_no).strip(),
                                "serial_no": cstr(p.serial_no).strip(),
                                "name": d.name,
                                "target_warehouse": p.target_warehouse,
                                "company": self.company,
                                "voucher_type": self.doctype,
                                "allow_zero_valuation": d.allow_zero_valuation_rate,
                                "sales_invoice_item": d.get("sales_invoice_item"),
                                "dn_detail": d.get("dn_detail"),
                                "incoming_rate": p.get("incoming_rate"),
                                "item_row": p,
                            }
                        )
                    )
        return il
    
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt



from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
    validate_inter_company_party,
)
from erpnext.manufacturing.doctype.blanket_order.blanket_order import (
    validate_against_blanket_order,
)

from erpnext.selling.doctype.sales_order.sales_order import  SalesOrder as BaseSalesOrder
form_grid_templates = {"items": "templates/form_grid/item_grid.html"}


class WarehouseRequired(frappe.ValidationError):
    pass
    
class SalesOrder(BaseSalesOrder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self):
        super().validate()
        # self.validate_delivery_date()
        self.validate_proj_cust()
        self.validate_po()
        self.validate_uom_is_integer("stock_uom", "stock_qty")
        self.validate_uom_is_integer("uom", "qty")
        self.validate_for_items()
        self.validate_warehouse()
        self.validate_drop_ship()
        self.validate_serial_no_based_delivery()
        validate_against_blanket_order(self)
        validate_inter_company_party(
            self.doctype, self.customer, self.company, self.inter_company_order_reference
        )

        if self.coupon_code:
            from erpnext.accounts.doctype.pricing_rule.utils import validate_coupon_code

            validate_coupon_code(self.coupon_code)

        from erpnext.stock.doctype.packed_item.packed_item import make_packing_list

        # make_packing_list(self)

        self.validate_with_previous_doc()
        self.set_status()

        if not self.billing_status:
            self.billing_status = "Not Billed"
        if not self.delivery_status:
            self.delivery_status = "Not Delivered"

        self.reset_default_field_value("set_warehouse", "items", "warehouse")