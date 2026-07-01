import frappe
import json
from frappe.utils.caching import redis_cache

@frappe.whitelist()
def get_branches(pos_profile):
    _pos_profile = json.loads(pos_profile)
    ttl = _pos_profile.get("posa_server_cache_duration")
    if ttl:
        ttl = int(ttl) * 60

    @redis_cache(ttl=ttl or 1800)
    def __get_branches_names(pos_profile):
        return _get_branches_names(pos_profile)

    def _get_branches_names(pos_profile):
        pos_profile = json.loads(pos_profile)
       
        branches = frappe.db.sql(
            """
            SELECT name
            FROM `tabBranch`
            ORDER by name
            """.format(
                
            ),
            as_dict=1,
        )
        return branches

    if _pos_profile.get("posa_use_server_cache"):
        return __get_branches_names(pos_profile)
    else:
        return _get_branches_names(pos_profile)