"""Autonomous AP Maker-Checker Agent Demonstration Script.
Showcases End-to-End Enterprise AP Lifecycle (PS-09):

PHASE 1: PRE-PO PROCUREMENT & QUOTATION SCRUTINY (> ₹20,000 UNIVERSITY RULE)
1) Respective Department HoD initiates purchase (> ₹20,000) & uploads 3 vendor quotations.
2) AI Maker Agent runs OCR/parsing, online market price benchmarking (GeM, Amazon, IndiaMART).
3) Multi-Criteria Decision Analysis (MCDA): Quality-over-Price scrutiny (Warranty, Delivery, SLA, Price).
4) Generates Comparative Statement (CS) for HoD & Purchase Officer.
5) Enforces 4-Tier Approval Gate: HoD -> Purchase Officer -> Accounts (Budget Check) -> CFO.
6) Automatically generates approved Purchase Order (PO) in the ERP.

PHASE 2: POST-PO INVOICE PROCESSING & 3-WAY MATCHING
1) AI Maker Agent processes incoming vendor invoices (OCR, 3-way line item match, duplicate checks).
2) Generates 3 Role-Based Checker Views:
   - Procurement Officer View (Line-item qty/price vs PO & GRN)
   - Accounts Division View (GST, MSME 45-day compliance, Early cash discount, Draft journal entry)
   - Respective Department View (Budget consumed vs remaining balance)
3) Human-in-the-Loop Checker Sign-offs.
4) Double-Entry ERP General Ledger Posting & Payment Execution.
"""
import sys
import os

# Ensure package import
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ap_agent.gemini_agent import APAgentMaker
from ap_agent.quotation_analyzer import analyze_proposals
from ap_agent.erp_db import reset_db, save_proposal, get_proposal_full, act_proposal, get_ledger_balance
from ap_agent.api import checker_decision

def run_phase1_quotation_scrutiny():
    print("=" * 85)
    print("  PHASE 1: PRE-PO MULTI-QUOTATION SCRUTINY & APPROVAL (RULE > ₹20,000)")
    print("=" * 85)
    print("  University Policy: Expenses > ₹20,000 require multi-quotation scrutiny.")
    print("  Workflow Gate: HoD (Upload) -> Purchase (Scrutiny) -> Accounts (Budget) -> CFO (Sanction)")
    print("  Decision Rule: Organizations do NOT always buy cheapest (L1); evaluate Quality, Delivery & SLA.")
    print("-" * 85)

    quote_dell = """TAX QUOTATION
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

    quote_micro = """TAX QUOTATION
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

    quote_lenovo = """TAX QUOTATION
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

    print("  ▶ Scenario: Institute of Engineering and Technology (IET) procuring 10 High-Performance Laptops")
    print("    • Total Est. Spend: ~₹9,00,000 (> ₹20,000 threshold)")
    print("    • HoD uploads 3 competitive bids: Dell Enterprise, MicroTech (L1), Lenovo Commercial\n")

    # Maker Agent Analyzes & Scrutinizes
    analysis = analyze_proposals(
        proposal_title="10 Laptops for IET AI/Robotics Lab",
        department="IET",
        raw_quotations=[quote_dell, quote_micro, quote_lenovo]
    )

    quotes = analysis["quotations"]
    l1_quote = min(quotes, key=lambda q: q["total_amount"])
    best_quote = next((q for q in quotes if q["vendor_name"] == analysis["recommended_vendor"]), quotes[0])

    print("  [AI Maker Quotation Scrutiny Summary]")
    print(f"  • Recommended Proposal: {analysis['recommended_vendor']} (₹{analysis['recommended_amount']:,.2f})")
    print(f"  • Lowest Commercial Bid (L1): {l1_quote['vendor_name']} (₹{l1_quote['total_amount']:,.2f})")
    if best_quote != l1_quote:
        print(f"  • Value Trade-off: Recommended proposal offers {best_quote['warranty_months'] - l1_quote['warranty_months']} extra months warranty & {l1_quote['delivery_days'] - best_quote['delivery_days']} days faster delivery.")
    print()

    print("  [Multi-Factor Comparative Statement (MCDA Evaluation Matrix)]")
    print("  " + "-" * 81)
    print(f"  {'Vendor':<32} | {'Total (₹)':<12} | {'Delivery':<10} | {'Warranty':<10} | {'Score':<6} | {'Verdict'}")
    print("  " + "-" * 81)
    for q in analysis["quotations"]:
        badge = "🏆 BEST VALUE" if "BEST" in q["recommendation_tag"] else ("🏷️ L1 (LOWEST)" if "L1" in q["recommendation_tag"] else "⚪ COMPLIANT")
        print(f"  {q['vendor_name'][:32]:<32} | ₹{q['total_amount']:<11,.0f} | {q['delivery_days']:<2} days    | {q['warranty_months']//12:<2} years   | {q['total_score']:<5.1f} | {badge}")
    print("  " + "-" * 81)

    print("\n  [Online Market Price Benchmarking Engine (GeM, Amazon Business, IndiaMART)]")
    for q in analysis["quotations"]:
        for item in q.get("items", []):
            print(f"  • {item['item_name']}: Quoted ₹{item['unit_price']:,.2f} vs Market Benchmark ₹{item.get('market_benchmark_price', 0):,.2f} ({item.get('market_variance_pct', 0):+.1f}%) - {item.get('market_verdict')}")

    # Save to ERP
    prop_id = save_proposal(analysis)
    print(f"\n  • Proposal saved in ERP Database with ID: {prop_id} [Status: PENDING_HOD]")

    # Simulate Institutional 4-Tier Approval Flow
    print("\n  [Simulating 4-Tier Human Approval Gate]")
    approvals_to_run = [
        ("HOD", "Prof. K. Sharma (HoD IET)", "Approved. Essential for upcoming semester AI curriculum."),
        ("PURCHASE_OFFICER", "Mr. V. Patel (Purchase)", "Scrutiny verified. Recommending Dell for 3-yr onsite warranty despite MicroTech L1."),
        ("ACCOUNTS", "Ms. S. Iyer (Accounts)", "Budget verified. IET Equipment Capex has sufficient balance."),
        ("CFO", "Dr. R. Gupta (CFO)", "Sanctioned. Issue official Purchase Order to Dell Enterprise.")
    ]

    for role, user, remarks in approvals_to_run:
        res = act_proposal(prop_id, role, True, acted_by=user, comments=remarks)
        print(f"    ✔ {role:<16} signed by {user:<28} -> Proposal Status: {res.get('status')}")
        if res.get("po_generated"):
            print(f"      🎉 Official Purchase Order Created in ERP: [{res.get('po_generated')}] for ₹{res.get('po_total'):,.2f}")

    print("\n" + "=" * 85)


def run_phase2_invoice_matching():
    print("  PHASE 2: POST-PO INVOICE 3-WAY MATCHING & ERP LEDGER POSTING")
    print("=" * 85)
    maker = APAgentMaker()

    cases = [
        ("1. Clean Partial Delivery (Under ₹50k)", """TAX INVOICE
Vendor: Sharma Lab Supplies Pvt Ltd
Invoice No: INV-101
Invoice Date: 10-11-2026
PO Number: PO-1001
1  LAB-REAG-01  Reagent kit  40  450.00  18,000.00
Subtotal: 18,000.00
GST 18%: 3,240.00
Total: 21,240.00"""),

        ("2. Price Variance (+4.4% on Unit Price)", """TAX INVOICE
Vendor: Sharma Lab Supplies Pvt Ltd
Invoice No: INV-102
Invoice Date: 12-11-2026
PO Number: PO-1001
1  LAB-REAG-01  Reagent kit  10  470.00  4,700.00
Subtotal: 4,700.00
GST 18%: 846.00
Total: 5,546.00"""),

        ("3. Over-Billing (Cumulative 40 + 30 > 60 received)", """TAX INVOICE
Vendor: Sharma Lab Supplies Pvt Ltd
Invoice No: INV-103
Invoice Date: 13-11-2026
PO Number: PO-1001
1  LAB-REAG-01  Reagent kit  30  450.00  13,500.00
Subtotal: 13,500.00
GST 18%: 2,430.00
Total: 15,930.00"""),

        ("4. Duplicate Invoice (Normalized 'inv 101')", """TAX INVOICE
Vendor: Sharma Lab Supplies Pvt Ltd
Invoice No: inv 101
Invoice Date: 10-11-2026
PO Number: PO-1001
1  LAB-REAG-01  Reagent kit  40  450.00  18,000.00
Subtotal: 18,000.00
GST 18%: 3,240.00
Total: 21,240.00"""),

        ("5. Unordered Item on PO (Laptop on Chemistry PO)", """TAX INVOICE
Vendor: Sharma Lab Supplies Pvt Ltd
Invoice No: INV-105
Invoice Date: 14-11-2026
PO Number: PO-1001
1  LAP-77  Dell Latitude Laptop  1  90000.00  90,000.00
Subtotal: 90,000.00
GST 18%: 16,200.00
Total: 106,200.00"""),

        ("6. High-Value IT Server AMC (Multi-Tier DoA)", """TAX INVOICE
Vendor: CampusTech Services LLP
Invoice No: CT-999
Invoice Date: 10-11-2026
PO Number: PO-1002
1  AMC-SRV-01  Server AMC annual  1  400000.00  400,000.00
Subtotal: 400,000.00
GST 18%: 72,000.00
Total: 472,000.00""")
    ]

    for title, inv_text in cases:
        print("-" * 85)
        print(f"▶ SCENARIO: {title}")
        print("-" * 85)

        # Run Maker Agent
        final_dossier = maker.run_invoice(invoice_text=inv_text)

        inv_id = final_dossier["invoice_id"]
        status = final_dossier["status"]
        issues = final_dossier.get("issues", [])
        doa = final_dossier.get("approval_chain", [])
        views = final_dossier.get("checker_views", {})

        print(f"  • AI Maker Recommendation: [{status}]")
        print(f"  • Flags / Issues: {', '.join([i['code'] for i in issues]) or 'None (Clean Match)'}")
        print(f"  • DoA Approval Chain: {' -> '.join(doa) or 'None (Auto-Held/Rejected)'}")

        # View 1: Procurement Officer
        proc = views.get("procurement_officer_view", {})
        print(f"\n  [Checker View 1: Procurement Officer]")
        for l in proc.get("lines_comparison", []):
            print(f"    - Item {l['item_code']}: Billed {l['billed_qty']} | GRN Received {l['received_qty']} | PO Ordered {l['ordered_qty']} | Variance: {l['billed_price']} vs {l['po_price']}")

        # View 2: Accounts Division
        acc = views.get("accounts_division_view", {})
        ps = acc.get("payment_schedule") or {}
        print(f"\n  [Checker View 2: Accounts Division]")
        print(f"    - Subtotal: ₹{acc.get('subtotal', 0):,.2f} | GST: ₹{acc.get('tax_billed', 0):,.2f} | Total: ₹{acc.get('total', 0):,.2f}")
        print(f"    - MSME 45-day Due: {ps.get('due_date')} | Early Cash Discount Saved: ₹{ps.get('discount_saving', 0):,.2f}")
        print(f"    - Draft Ledger: DR Expense ₹{acc.get('subtotal', 0):,.2f}, DR GST ₹{acc.get('tax_billed', 0):,.2f}, CR AP ₹{acc.get('total', 0):,.2f}")

        # View 3: Respective Department
        dept = views.get("respective_department_view", {})
        print(f"\n  [Checker View 3: Respective Department ({dept.get('department')})]")
        print(f"    - Budget Allocated: ₹{dept.get('budget_allocated', 0):,.2f} | Available: ₹{dept.get('budget_available', 0):,.2f}")
        print(f"    - Post-Invoice Utilization: {dept.get('utilization_after', 0):.1f}%")

        # Simulate Human Checker Approval if pending
        if status == "PENDING_APPROVAL":
            print(f"\n  [Simulating Human-in-the-Loop Checkers]")
            for role in doa:
                res = checker_decision(inv_id=inv_id, role=role, approve=True, acted_by=f"{role}_OFFICER")
                print(f"    ✔ Signed off by {role}: {res.get('message')}")
        print()

    print("=" * 85)
    print("  FINAL ERP GENERAL LEDGER SUMMARY:")
    bal = get_ledger_balance()
    print(f"  • Outstanding Accounts Payable Liability: ₹{bal.get('ap_liability', 0):,.2f}")
    print(f"  • Cash Discounts Earned: ₹{bal.get('discounts_captured', 0):,.2f}")
    print(f"  • Total Balanced Journal Entries: {bal.get('entries_count', 0)}")
    print("=" * 85)

def main():
    print("=" * 85)
    print("  APEX-AP: ENTERPRISE AI ACCOUNTS PAYABLE & PROCUREMENT AGENT")
    print("  Problem Statement PS-09 | Built for University ERP System Integration")
    print("=" * 85)
    print()
    reset_db()
    run_phase1_quotation_scrutiny()
    run_phase2_invoice_matching()

if __name__ == "__main__":
    main()

