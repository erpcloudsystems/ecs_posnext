import frappe

def run():
    branches = frappe.get_all("Branch", fields=["name"])
    print("BRANCHES:")
    print(branches)

if __name__ == "__main__":
    run()
