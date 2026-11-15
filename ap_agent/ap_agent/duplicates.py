import re
from datetime import timedelta
from .models import Issue

def norm_no(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper()).lstrip("0")

def find_duplicates(inv, history):
    """history: previously accepted invoices (not rejected). Returns list of Issue."""
    out = []
    for h in history:
        if h.id == inv.id or h.vendor_id != inv.vendor_id:
            continue
        if norm_no(h.invoice_no) == norm_no(inv.invoice_no):
            out.append(Issue("DUPLICATE_EXACT", "CRITICAL",
                             f"Invoice no. matches {h.id} ({h.invoice_no}) for same vendor"))
        elif (h.total == inv.total and h.po_number == inv.po_number
              and abs((h.invoice_date - inv.invoice_date).days) <= 30):
            out.append(Issue("DUPLICATE_SUSPECTED", "CRITICAL",
                             f"Same vendor, PO and amount as {h.id} ({h.invoice_no}) within 30 days"))
    return out
