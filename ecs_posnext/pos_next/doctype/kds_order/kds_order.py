import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class KDSOrder(Document):
    def before_save(self):
        # Stamp ready_time the first time status reaches "Ready"
        if self.status == "Ready" and not self.ready_time:
            self.ready_time = now_datetime()
        if self.status == "Completed" and not self.completed_time:
            self.completed_time = now_datetime()
