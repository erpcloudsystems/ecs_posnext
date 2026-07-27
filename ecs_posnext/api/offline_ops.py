# -*- coding: utf-8 -*-
# Copyright (c) 2025, BrainWise and contributors
# For license information, please see license.txt

"""Generic idempotency layer for offline write operations.

Whitelisted write endpoints (open_shift, close_shift, attendance, daily_payment,
customer, ...) accept an optional ``op_id`` and use these helpers to guarantee
each queued client operation produces exactly one server document, even if the
client re-syncs the same op after a dropped response.

Mirrors the invoice-specific flow in ``ecs_posnext.api.invoices`` but keyed on a
generic Offline Operation Sync record instead of Offline Invoice Sync.
"""

import frappe

from ecs_posnext.pos_next.doctype.offline_operation_sync.offline_operation_sync import (
    OfflineOperationSync,
)


@frappe.whitelist()
def is_op_synced(op_id):
    """Return whether an offline operation has already been synced.

    Used by the client sync engine for a pre-sync deduplication check.
    """
    return OfflineOperationSync.is_synced(op_id)


def ensure_op_once(op_id, op_type=None):
    """Return the already-created document name for ``op_id``, else ``None``.

    Call at the top of a whitelisted write that accepts ``op_id``. When it
    returns a name, the caller should skip creation and return that existing
    document (the operation was already synced on a previous attempt).
    """
    if not op_id:
        return None

    result = OfflineOperationSync.is_synced(op_id)
    return result.get("ref_name") if result.get("synced") else None


def create_op_sync_record(op_id, op_type=None, ref_doctype=None, ref_name=None, status="Synced"):
    """Record that ``op_id`` produced ``ref_name`` (idempotent)."""
    if not op_id:
        return None

    return OfflineOperationSync.create_sync_record(
        op_id=op_id,
        op_type=op_type,
        ref_doctype=ref_doctype,
        ref_name=ref_name,
        status=status,
    )
