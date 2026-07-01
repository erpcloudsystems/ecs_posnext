import re

with open('ecs_posnext/api/customers.py', 'r') as f:
    content = f.read()

# Find the get_customers function and add search_term logic
old_logic = """        if modified_since:
            # Delta sync: include disabled customers so frontend can purge them
            filters["modified"] = [">=", modified_since]
        else:
            # Full fetch: only active customers
            filters["disabled"] = 0"""

new_logic = """        if modified_since:
            # Delta sync: include disabled customers so frontend can purge them
            filters["modified"] = [">=", modified_since]
        else:
            # Full fetch: only active customers
            filters["disabled"] = 0
            
        or_filters = {}
        if search_term:
            or_filters = {
                "name": ["like", f"%{search_term}%"],
                "customer_name": ["like", f"%{search_term}%"],
                "mobile_no": ["like", f"%{search_term}%"],
                "custom_other_mobile_no": ["like", f"%{search_term}%"],
                "email_id": ["like", f"%{search_term}%"],
            }"""

old_get_all = """        result = frappe.get_all(
            "Customer",
            filters=filters,
            fields=["name", "customer_name", "mobile_no", "custom_other_mobile_no", "email_id", "disabled"],
            limit=customer_limit,
            order_by="customer_name asc",
        )"""

new_get_all = """        result = frappe.get_all(
            "Customer",
            filters=filters,
            or_filters=or_filters,
            fields=["name", "customer_name", "mobile_no", "custom_other_mobile_no", "email_id", "disabled"],
            limit=customer_limit,
            order_by="customer_name asc",
        )"""

content = content.replace(old_logic, new_logic)
content = content.replace(old_get_all, new_get_all)

with open('ecs_posnext/api/customers.py', 'w') as f:
    f.write(content)
