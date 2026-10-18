import frappe, traceback, re, html as H
OUT="/tmp/claude-1000/-home-frappe-frappe-bench/aa15222c-e455-489e-a3e6-ef8af7ea1bd4/scratchpad/t2.out"
def w(l):
    with open(OUT,"a") as f: f.write(str(l)+"\n")
def run():
    try:
        open(OUT,"w").close()
        for N,label in (("ACC-SINV-2026-79659","الأصل M-47"),("ACC-SINV-2026-79663","الإضافة M-47-1")):
            out=frappe.get_print("Sales Invoice",N,print_format="print format sales")
            txt=re.sub(r"<[^>]+>"," ",out)
            txt=H.unescape(re.sub(r"\s+"," ",txt))
            w("=== %s | %s ===" % (N,label))
            for kw in ("Subtotal","Delivery","TOTAL","Additions","ORDER TOTAL","PAID","UNPAID","Outstanding","this receipt","Addition to order"):
                for m in re.finditer(re.escape(kw)+r"[^A-Za-z]{0,3}([^A-Za-z]{0,40})",txt):
                    seg=txt[max(0,m.start()-3):m.start()+70].strip()
                    w("   %-18s → %s" % (kw,seg)); break
            w("")
    except Exception:
        with open(OUT,"a") as f: traceback.print_exc(file=f)
