from datetime import date
from decimal import Decimal as D
import pytest
from fastapi.testclient import TestClient
from ap_agent.api import seed, app
import ap_agent.api as api_mod
from ap_agent.parser import parse_invoice_text
from ap_agent.pipeline import process_invoice, approve, execute_payment
from ap_agent.budget import check_budget
from ap_agent.approval import build_chain
from ap_agent.payments import schedule_payment
from ap_agent.models import Budget, Vendor, Invoice

def text(no="INV-001", date_="10-11-2026", po="PO-1001", vendor="Sharma Lab Supplies Pvt Ltd",
         item="LAB-REAG-01", desc="Reagent kit", qty=60, price="450.00", tax_rate="0.18", tax=None, total=None):
    amt = D(qty) * D(price)
    t = D(tax) if tax is not None else (amt * D(tax_rate)).quantize(D("0.01"))
    tot = D(total) if total is not None else amt + t
    return f"""TAX INVOICE
Vendor: {vendor}
Invoice No: {no}
Invoice Date: {date_}
PO Number: {po}
1  {item}  {desc}  {qty}  {price}  {amt:,.2f}
Subtotal: {amt:,.2f}
GST 18%: {t:,.2f}
Total: {tot:,.2f}
"""

@pytest.fixture
def s():
    return seed()

def run(s, **kw):
    return process_invoice(s, parse_invoice_text(text(**kw)))

def codes(inv): return {i.code for i in inv.issues}

def test_parser_extracts_fields():
    inv = parse_invoice_text(text())
    assert inv.invoice_no == "INV-001" and inv.po_number == "PO-1001"
    assert inv.invoice_date == date(2026, 11, 10)
    assert inv.total == D("31860.00") and len(inv.lines) == 1 and inv.confidence == 1.0

def test_clean_invoice_goes_to_dept_head_only(s):
    inv = run(s)
    assert inv.status == "PENDING_APPROVAL", inv.issues
    assert [a["role"] for a in inv.approvals] == ["DEPARTMENT_HEAD"]

def test_price_variance_held(s):
    assert "PRICE_VARIANCE" in codes(run(s, price="460.00"))
    assert run(seed(), price="460.00").status == "HOLD_EXCEPTION"

def test_price_within_tolerance_passes(s):
    assert run(s, price="458.00").status == "PENDING_APPROVAL"   # 1.8%

def test_overbilling_vs_goods_receipt(s):
    inv = run(s, qty=80)
    assert "QTY_EXCEEDS_RECEIPT" in codes(inv) and inv.status == "HOLD_EXCEPTION"

def test_cumulative_billing_across_invoices(s):
    assert run(s, no="A1", qty=40).status == "PENDING_APPROVAL"
    second = run(s, no="A2", qty=30)          # 40+30=70 > 60 received
    assert "QTY_EXCEEDS_RECEIPT" in codes(second)

def test_exact_duplicate_with_reformatted_number(s):
    run(s, no="INV-001")
    d = run(s, no="inv 001")
    assert d.status == "REJECTED_DUPLICATE" and "DUPLICATE_EXACT" in codes(d)

def test_suspected_duplicate_different_number(s):
    run(s, no="INV-001")
    d = run(s, no="INV-777")                  # same vendor, PO, amount
    assert "DUPLICATE_SUSPECTED" in codes(d)

def test_no_po(s):
    assert "PO_NOT_FOUND" in codes(run(s, po="PO-9999"))

def test_unknown_vendor(s):
    assert "UNKNOWN_VENDOR" in codes(run(s, vendor="Fly By Night Traders"))

def test_not_received_item(s):
    s.grns.clear()
    assert "NOT_RECEIVED" in codes(run(s))

def test_tax_and_total_mismatch(s):
    inv = run(s, tax="5000.00", total="33000.00")
    assert {"TAX_MISMATCH", "TOTAL_MISMATCH"} <= codes(inv)

def test_item_not_on_po(s):
    assert "NO_PO_LINE" in codes(run(s, item="XYZ-99", desc="Unordered laptop"))

def test_low_ocr_confidence_goes_to_manual_review(s):
    inv = process_invoice(s, parse_invoice_text("Invoice No: 55\nVendor: Sharma Lab Supplies Pvt Ltd"))
    assert inv.status == "HOLD_EXCEPTION" and "LOW_OCR_CONFIDENCE" in codes(inv)

def test_budget_check_logic():
    b = Budget("X", D("100000"), D("60000"), D("30000"))        # available 10k
    assert check_budget(b, D("20000"), D("20000")) == [] or all(i.severity == "INFO" for i in check_budget(b, D("20000"), D("20000")))
    assert check_budget(b, D("25000"), D("10000"))[0].code == "BUDGET_EXCEEDED"   # +15k > 10k
    assert check_budget(None, D(1), D(0))[0].code == "NO_BUDGET"

def test_budget_exception_adds_finance_step():
    assert [a["role"] for a in build_chain(D("40000"), True)] == ["DEPARTMENT_HEAD", "FINANCE_CONTROLLER"]

def test_approval_tiers():
    assert len(build_chain(D("50000"))) == 1
    assert len(build_chain(D("50001"))) == 2
    assert len(build_chain(D("472000"))) == 3
    assert len(build_chain(D("2000000"))) == 4

def test_full_lifecycle_ledger_budget_and_payment(s):
    inv = run(s, po="PO-1002", vendor="CampusTech Services LLP", item="AMC-SRV-01",
              desc="Server AMC annual", qty=1, price="400000.00", no="CT-1")
    assert inv.status == "PENDING_APPROVAL" and len(inv.approvals) == 3
    with pytest.raises(PermissionError):
        approve(s, inv.id, "REGISTRAR")                         # out of sequence
    for r in ["DEPARTMENT_HEAD", "FINANCE_CONTROLLER", "REGISTRAR"]:
        approve(s, inv.id, r)
    assert inv.status == "SCHEDULED"
    assert s.budgets["IT"].committed == 0 and s.budgets["IT"].actual == D("50000") + D("472000")
    assert s.erp.liability() == D("472000")
    item = execute_payment(s, inv.id)
    assert inv.status == "PAID" and s.erp.liability() == 0

def test_rejection_stops_chain(s):
    inv = run(s)
    approve(s, inv.id, "DEPARTMENT_HEAD", approve_=False)
    assert inv.status == "REJECTED" and not s.schedule

def test_payment_schedule_discount_and_msme():
    v = Vendor("V", "n", terms_days=60, msme=True, discount_pct=D("0.02"), discount_days=10)
    inv = Invoice("1", "n", date(2026, 11, 1), "P", [], D("1000"), D("180"), D("1180"), id="I")
    early = schedule_payment(inv, v, date(2026, 11, 5))
    assert early["amount"] == D("1160.00") and early["pay_on"] == date(2026, 11, 11)
    late = schedule_payment(inv, v, date(2026, 11, 20))
    assert late["amount"] == D("1180") and late["due_date"] == date(2026, 12, 16)   # 45 days, not 60
    assert "MSME 45-day cap applied" in late["notes"]

class MockResp:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data
    def json(self):
        return self._data

class DirectClient:
    def post(self, url, data=None, params=None):
        from fastapi import HTTPException
        if url == "/invoices/intake":
            txt = (data or {}).get("text")
            r = api_mod.invoice_intake(text=txt)
            return MockResp(200, r)
        elif "/decision" in url:
            inv_id = url.split("/")[2]
            role = (params or {}).get("role")
            try:
                r = api_mod.checker_decision(inv_id=inv_id, role=role, approve=True)
                return MockResp(200, r)
            except HTTPException as e:
                return MockResp(e.status_code, {"detail": str(e.detail)})
        raise ValueError(f"Unknown POST url {url}")

    def get(self, url):
        if url.startswith("/payments/schedule"):
            r = api_mod.legacy_payment_schedule()
            return MockResp(200, r)
        elif url == "/liabilities":
            r = api_mod.legacy_liabilities()
            return MockResp(200, r)
        elif url == "/":
            r = api_mod.serve_dashboard()
            return MockResp(200, r)
        raise ValueError(f"Unknown GET url {url}")

def test_api_end_to_end():
    from ap_agent.erp_db import reset_db
    reset_db()
    c = DirectClient()
    r = c.post("/invoices/intake", data={"text": text()}).json()
    assert r["status"] == "PENDING_APPROVAL"
    dup = c.post("/invoices/intake", data={"text": text(no="inv001")}).json()
    assert dup["status"] == "REJECTED_DUPLICATE"
    bad = c.post(f"/invoices/{r['id']}/decision", params={"role": "REGISTRAR"})
    assert bad.status_code == 409
    ok = c.post(f"/invoices/{r['id']}/decision", params={"role": "DEPARTMENT_HEAD"}).json()
    assert ok["status"] == "SCHEDULED"
    sched = c.get("/payments/schedule?horizon_days=30").json()
    assert sched and sched[0]["notes"] and "discount" in sched[0]["notes"].lower()
    assert c.get("/liabilities").json()["ap_balance"] == "31860.00"
    assert c.get("/").status_code == 200
