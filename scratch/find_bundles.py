import frappe

def run():
    items = frappe.db.get_all('Item', filters={'enabled_item_bundle': 1}, fields=['item_code', 'item_name'])
    print(items)

if __name__ == "__main__":
    run()
