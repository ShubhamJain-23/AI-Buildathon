import uuid
from datetime import date
from decimal import Decimal as D
from difflib import SequenceMatcher
from .models import *
from .duplicates import find_duplicates
from .matching import three_way_match
from .budget import check_budget
from .approval import build_chain, act
from .payments import schedule_payment
from .erp import MockERP

ACTIVE = {"PENDING_APPROVAL", "APPROVED", "SCHEDULED", "PAID"}

class Store:
    def __init__(self, today=None):
        self.today = today or date.today()
        self.vendors, self.pos, self.grns, self.budgets = {}, {}, [], {}
        self.invoices, self.schedule = {}, []
        self.erp = MockERP()

    def vendor_by_name(self, name):
        best, score = None, 0
        for v in self.vendors.values():
            s = SequenceMatcher(None, v.name.lower(), (name or "").lower()).ratio()
            if s > score:
                best, score = v, s
        return best if score >= 0.8 else None

    def prior_invoiced(self, po_number, exclude_id):
        out = {}
        for i in self.invoices.values():
            if i.po_number == po_number and i.status in ACTIVE and i.id != exclude_id:
                for l in i.lines:
                    out[l.item_code.upper()] = out.get(l.item_code.upper(), D(0)) + l.qty
        return out

    def po_outstanding(self, po, exclude_id):
        used = sum((i.total for i in self.invoices.values()
                    if i.po_number == po.po_number and i.status in ACTIVE and i.id != exclude_id), D(0))
        return max(D(0), po.gross_total - used)

def process_invoice(store: Store, inv: Invoice) -> Invoice:
    inv.id = inv.id or "INV-" + uuid.uuid4().hex[:8].upper()
    v = store.vendor_by_name(inv.vendor_name)
    inv.vendor_id = v.vendor_id if v else None
    issues = []
    if not v:
        issues.append(Issue("UNKNOWN_VENDOR", "CRITICAL", f"Vendor '{inv.vendor_name}' not in master"))
    if inv.confidence < 0.75:
        issues.append(Issue("LOW_OCR_CONFIDENCE", "MAJOR", f"Parse confidence {inv.confidence}; manual review"))

    dups = find_duplicates(inv, [i for i in store.invoices.values() if i.status != "REJECTED_DUPLICATE"])
    po = store.pos.get(inv.po_number)
    grns = [g for g in store.grns if po and g.po_number == po.po_number]
    if not dups:
        issues += three_way_match(inv, po, grns, v, store.prior_invoiced(inv.po_number, inv.id))
    budget_exc = False
    if po and not dups:
        b = check_budget(store.budgets.get(po.department), inv.total, store.po_outstanding(po, inv.id))
        issues += b
        budget_exc = any(i.code in ("BUDGET_EXCEEDED", "NO_BUDGET") for i in b)
    issues = dups + issues
    inv.issues = issues
    store.invoices[inv.id] = inv

    if dups:
        inv.status = "REJECTED_DUPLICATE"
    elif any(i.severity in ("CRITICAL", "MAJOR") and not i.code.startswith("BUDGET") for i in issues):
        inv.status = "HOLD_EXCEPTION"
    else:
        inv.status = "PENDING_APPROVAL"
        inv.approvals = build_chain(inv.total, budget_exc)
    return inv

def approve(store: Store, inv_id, role, approve_=True, by="user"):
    inv = store.invoices[inv_id]
    act(inv, role, approve_, by)
    if inv.status == "APPROVED":
        store.erp.post_invoice(inv)
        po = store.pos[inv.po_number]
        b = store.budgets[po.department]
        released = min(inv.total, store.po_outstanding(po, inv.id))
        b.committed -= released
        b.actual += inv.total
        item = schedule_payment(inv, store.vendors[inv.vendor_id], store.today)
        store.schedule.append(item)
        inv.status = "SCHEDULED"
    return inv

def execute_payment(store, inv_id):
    inv = store.invoices[inv_id]
    item = next(s for s in store.schedule if s["invoice_id"] == inv_id)
    store.erp.pay(inv_id, item["amount"], inv.total - item["amount"])
    inv.status = "PAID"
    return item
