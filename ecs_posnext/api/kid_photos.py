# -*- coding: utf-8 -*-
# Kid's photo for ticket (subscription) items sold in POS Next.
#
# Flow (no schema change):
#   1. POS cart: the cashier takes/uploads a photo per ticket on a ticket item row;
#      upload_kid_photo() stores it as a private File and returns its URL. The cart
#      row carries the URLs as `kid_photos` (a transient attribute, not a DB column).
#   2. Sales Invoice validate: link those Files to the invoice and remember, per item
#      code, the photo order in the cache (the transient attribute is gone once the
#      background submit reloads the invoice).
#   3. Sales Invoice on_submit (after ecs_vim_ticket.generate_tickets): after commit,
#      copy each photo onto Ticket.image, in the same order tickets were generated.

import base64
import json

import frappe
from frappe import _
from frappe.utils import cint
from frappe.utils.file_manager import save_file

CACHE_KEY = "ecs_posnext:kid_photos:{0}"
CACHE_TTL = 3 * 24 * 60 * 60
MAX_PHOTO_BYTES = 5 * 1024 * 1024


@frappe.whitelist()
def get_ticket_item_codes():
    """Item codes that generate a Ticket when sold (have Ticket Settings)."""
    return frappe.get_all("Ticket Settings", filters={"item": ["is", "set"]}, pluck="item", distinct=True)


@frappe.whitelist()
def upload_kid_photo(data_url, filename=None):
    """Save a captured/uploaded photo (data URL) as a private File; returns its URL."""
    if not data_url or "," not in data_url or not data_url.startswith("data:image/"):
        frappe.throw(_("Invalid photo"))

    header, encoded = data_url.split(",", 1)
    try:
        content = base64.b64decode(encoded)
    except Exception:
        frappe.throw(_("Invalid photo"))
    if len(content) > MAX_PHOTO_BYTES:
        frappe.throw(_("Photo is too large (max 5 MB)"))

    ext = "png" if "image/png" in header else "jpg"
    fname = f"kid-photo-{frappe.generate_hash(length=10)}.{ext}"
    file_doc = save_file(fname, content, None, None, is_private=1)
    return {"file_url": file_doc.file_url, "name": file_doc.name}


@frappe.whitelist()
def set_ticket_kid_photo(ticket_name, file_url=None):
    """Set (or clear, when file_url is empty) the kid photo on an existing Ticket."""
    if not frappe.db.exists("Ticket", ticket_name):
        frappe.throw(_("Ticket {0} not found").format(ticket_name))

    file_url = (file_url or "").strip()
    if file_url:
        file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
        if not file_name:
            frappe.throw(_("Photo file not found"))
        # Attach a freshly uploaded photo to the ticket (leave already-attached files alone).
        if not frappe.db.get_value("File", file_name, "attached_to_name"):
            frappe.db.set_value(
                "File",
                file_name,
                {"attached_to_doctype": "Ticket", "attached_to_name": ticket_name},
                update_modified=False,
            )

    frappe.db.set_value("Ticket", ticket_name, "image", file_url or None)
    frappe.get_doc("Ticket", ticket_name).add_comment(
        "Comment", _("Kid photo updated from POS") if file_url else _("Kid photo removed from POS")
    )
    frappe.db.commit()
    return {"ticket": ticket_name, "image": file_url}


def _row_photos(row):
    photos = row.get("kid_photos")
    if isinstance(photos, str):
        try:
            photos = json.loads(photos)
        except Exception:
            photos = [photos]
    return [p for p in (photos or []) if isinstance(p, str) and p]


def link_kid_photos(doc, method=None):
    """Sales Invoice validate: remember photo order per item and attach the Files."""
    if doc.doctype != "Sales Invoice" or not doc.name:
        return

    per_item = {}
    for row in doc.get("items") or []:
        photos = _row_photos(row)
        if not photos:
            continue
        # One ticket per unit: ignore photos beyond the row qty.
        per_item.setdefault(row.item_code, []).extend(photos[: max(cint(row.qty), 0)])

    if not per_item:
        return

    for urls in per_item.values():
        for url in urls:
            file_name = frappe.db.get_value(
                "File", {"file_url": url, "attached_to_name": ["is", "not set"]}, "name"
            )
            if file_name:
                frappe.db.set_value(
                    "File",
                    file_name,
                    {"attached_to_doctype": "Sales Invoice", "attached_to_name": doc.name},
                    update_modified=False,
                )

    frappe.cache().set_value(CACHE_KEY.format(doc.name), per_item, expires_in_sec=CACHE_TTL)


def assign_kid_photos_on_submit(doc, method=None):
    """Sales Invoice on_submit: copy photos to the generated tickets after commit."""
    if not frappe.cache().get_value(CACHE_KEY.format(doc.name)):
        return
    frappe.enqueue(
        "ecs_posnext.api.kid_photos.apply_kid_photos_to_tickets",
        queue="short",
        sales_invoice=doc.name,
        enqueue_after_commit=True,
    )


def apply_kid_photos_to_tickets(sales_invoice):
    key = CACHE_KEY.format(sales_invoice)
    per_item = frappe.cache().get_value(key)
    if not per_item:
        return

    try:
        for item_code, urls in per_item.items():
            # generate_tickets creates tickets row by row, in invoice item order.
            tickets = frappe.get_all(
                "Ticket",
                filters={"sales_invoice": sales_invoice, "item": item_code},
                fields=["name", "image"],
                order_by="creation asc, name asc",
            )
            for ticket, url in zip(tickets, urls):
                if not ticket.image:
                    frappe.db.set_value("Ticket", ticket.name, "image", url, update_modified=False)
        frappe.db.commit()
        frappe.cache().delete_value(key)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Kid photo -> Ticket failed for {sales_invoice}")
