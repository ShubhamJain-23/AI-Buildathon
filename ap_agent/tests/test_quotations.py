"""Unit Tests for Multi-Quotation Scrutiny, Market Benchmarking & Institutional Approval.
Verifies the University Workflow:
HoD (Uploads Quotations) -> Purchase Officer (Scrutiny & Comparison) -> Accounts (Budget Check) -> CFO (Final Approval)
"""
import pytest
from ap_agent.quotation_analyzer import parse_quotation_text, analyze_proposals
from ap_agent.market_search import benchmark_item_price
from ap_agent.erp_db import reset_db, save_proposal, get_proposal_full, act_proposal, get_all_departments

QUOTE_A = """TAX QUOTATION
Vendor: Dell India Enterprise Solutions
Item: Dell Latitude 5440 Core i5 16GB 512GB SSD
Qty: 10
Unit Price: 76,000.00
Amount: 760,000.00
Subtotal: 760,000.00
GST 18%: 136,800.00
Total: 896,800.00
Delivery: 7 days
Warranty: 3 years
Service: 24x7 4-Hour Response Onsite Premier Support with OEM Certified Engineers
Payment Terms: 30 Days Net
"""

QUOTE_B = """TAX QUOTATION
Vendor: MicroTech Systems & Peripherals
Item: Dell Latitude 5440 Core i5 16GB 512GB SSD
Qty: 10
Unit Price: 73,500.00
Amount: 735,000.00
Subtotal: 735,000.00
GST 18%: 132,300.00
Total: 867,300.00
Delivery: 28 days
Warranty: 1 year
Service: Standard Carry-in Warranty (No Onsite Support)
Payment Terms: 100% Advance
"""

QUOTE_C = """TAX QUOTATION
Vendor: Lenovo Commercial Tech Pvt Ltd
Item: ThinkPad E14 Core i5 16GB 512GB SSD
Qty: 10
Unit Price: 79,000.00
Amount: 790,000.00
Subtotal: 790,000.00
GST 18%: 142,200.00
Total: 932,200.00
Delivery: 10 days
Warranty: 3 years
Service: 3-Year Premier Onsite Support
Payment Terms: 30 Days Net
"""

def test_quotation_parsing():
    q = parse_quotation_text(QUOTE_A)
    assert q["vendor_name"] == "Dell India Enterprise Solutions"
    assert q["total_amount"] == 896800.0
    assert q["delivery_days"] == 7
    assert q["warranty_months"] == 36
    assert "Onsite" in q["after_sales_service"]

def test_market_benchmarking():
    bench = benchmark_item_price("Dell Latitude 5440", 76000.0)
    assert bench["benchmark_price"] == 78000.0
    assert bench["variance_pct"] < 0  # 76k is cheaper than 78k benchmark
    assert "GeM" in bench["source"]

def test_multi_factor_scoring_recommends_best_value_not_just_cheapest():
    """Validates that organizations don't always pick L1 (Quote B is cheaper by ₹29k,
    but Quote A has 3-year warranty vs 1-year and 7-day delivery vs 28-day)."""
    analysis = analyze_proposals(
        proposal_title="10 Laptops for IET Department",
        department="IET",
        raw_quotations=[QUOTE_A, QUOTE_B, QUOTE_C]
    )
    # Dell (Quote A) should be recommended despite Quote B having lower initial price
    assert analysis["recommended_vendor"] == "Dell India Enterprise Solutions"
    quotes = analysis["quotations"]
    dell_q = next(q for q in quotes if "Dell" in q["vendor_name"])
    micro_q = next(q for q in quotes if "MicroTech" in q["vendor_name"])
    
    assert dell_q["total_score"] > micro_q["total_score"]
    assert dell_q["recommendation_tag"] == "RECOMMENDED_BEST_VALUE"
    assert micro_q["recommendation_tag"] == "LOWEST_COST_L1"

def test_full_institutional_approval_chain_and_po_generation():
    reset_db()
    analysis = analyze_proposals(
        proposal_title="10 Laptops for IET Lab",
        department="IET",
        raw_quotations=[QUOTE_A, QUOTE_B, QUOTE_C]
    )
    prop_id = save_proposal(analysis)
    p = get_proposal_full(prop_id)
    assert p["status"] == "PENDING_HOD"
    
    # 4-Step Chain: HOD -> PURCHASE_OFFICER -> ACCOUNTS -> CFO
    roles = [a["role"] for a in p["approvals"]]
    assert roles == ["HOD", "PURCHASE_OFFICER", "ACCOUNTS", "CFO"]

    # Out of sequence should fail
    with pytest.raises(PermissionError):
        act_proposal(prop_id, "CFO", approve=True)

    # 1. HoD Approves
    r1 = act_proposal(prop_id, "HOD", approve=True, acted_by="Prof. R. K. Sharma (HoD IET)")
    assert r1["status"] == "IN_PROGRESS"

    # 2. Purchase Officer Scrutinizes & Approves
    r2 = act_proposal(prop_id, "PURCHASE_OFFICER", approve=True, acted_by="Mr. V. Verma (Purchase Officer)")
    assert r2["status"] == "IN_PROGRESS"

    # 3. Accounts Checks Budget & Approves
    r3 = act_proposal(prop_id, "ACCOUNTS", approve=True, acted_by="Accounts Dept")
    assert r3["status"] == "IN_PROGRESS"

    # 4. CFO Grants Final Approval -> Generates PO and encumbers budget
    r4 = act_proposal(prop_id, "CFO", approve=True, acted_by="Dr. M. S. Rao (CFO)")
    assert r4["status"] == "PO_ISSUED"
    assert "PO-IET-2026-" in r4["po_number"]

    # Verify budget commitment in ERP
    depts = {d["code"]: d for d in get_all_departments()}
    iet = depts["IET"]
    # Original committed was 8,00,000 + 8,96,800 = 16,96,800
    assert iet["committed"] == 1696800.0
