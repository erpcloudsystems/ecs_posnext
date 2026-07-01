import frappe

def run():
    print("--- Branch Fields ---")
    meta = frappe.get_meta("Branch")
    for f in meta.fields:
        if "warehouse" in f.fieldname or "pos" in f.fieldname or "profile" in f.fieldname:
            print(f"{f.label}: {f.fieldname}")

    print("\n--- Sample Branch Data ---")
    branches = frappe.get_all("Branch", limit=5)
    for b in branches:
        doc = frappe.get_doc("Branch", b.name)
        print(f"Branch: {doc.name}")
        for f in doc.as_dict():
            if "warehouse" in f or "pos" in f or "profile" in f:
                 print(f"  {f}: {doc.get(f)}")

if __name__ == "__main__":
    run()
