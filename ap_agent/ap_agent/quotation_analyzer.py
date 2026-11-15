"""Autonomous Quotation Scrutiny & Multi-Factor Comparison Engine.
Analyzes 2-3 or more vendor quotations, benchmarks prices against online platforms,
and evaluates non-cost parameters (delivery timeline, warranty, after-sales service, vendor trust).
"""
import re
import uuid
from typing import Dict, Any, List, Optional
from .market_search import benchmark_item_price
from . import erp_db

def parse_quotation_text(text: str) -> Dict[str, Any]:
    """Extracts structured quotation terms from vendor proposal text."""
    lines = text.strip().split("\n")
    vendor_name = "Unknown Vendor"
    total_amount = 0.0
    subtotal = 0.0
    tax = 0.0
    delivery_days = 14
    warranty_months = 12
    after_sales = "Standard 1-Year Support"
    payment_terms = "30 Days Net"
    items = []

    for l in lines:
        line_clean = l.strip()
        # Vendor
        v_match = re.search(r"vendor\s*[:\-]\s*(.+)", line_clean, re.I)
        if v_match:
            vendor_name = v_match.group(1).strip()
            continue

        # Total
        tot_match = re.search(r"(?:total|grand\s*total)\s*[:\-]?\s*₹?\s*([\d,]+\.?\d*)", line_clean, re.I)
        if tot_match:
            try:
                total_amount = float(tot_match.group(1).replace(",", ""))
            except ValueError:
                pass
            continue

        # Subtotal
        sub_match = re.search(r"subtotal\s*[:\-]?\s*₹?\s*([\d,]+\.?\d*)", line_clean, re.I)
        if sub_match:
            try:
                subtotal = float(sub_match.group(1).replace(",", ""))
            except ValueError:
                pass
            continue

        # Delivery
        del_match = re.search(r"(?:delivery|dispatch|timeline)\s*[:\-]?\s*(\d+)\s*(?:days?|weeks?)", line_clean, re.I)
        if del_match:
            val = int(del_match.group(1))
            if "week" in line_clean.lower():
                val = val * 7
            delivery_days = val
            continue

        # Warranty
        war_match = re.search(r"(?:warranty|guarantee)\s*[:\-]?\s*(\d+)\s*(?:years?|months?)", line_clean, re.I)
        if war_match:
            val = int(war_match.group(1))
            if "year" in line_clean.lower():
                val = val * 12
            warranty_months = val
            continue

        # After sales
        if any(k in line_clean.lower() for k in ["support", "sla", "onsite", "maintenance", "service"]):
            after_sales = line_clean.split(":", 1)[-1].strip() if ":" in line_clean else line_clean
            continue

        # Items format: 1  ITEM-CODE  Description  Qty  UnitPrice  Amount
        # or: Description - Qty x Price = Amount
        item_m = re.search(r"(?:^\d+\s+)?([A-Za-z0-9\-]+)?\s+(.+?)\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d,]+\.?\d*)", line_clean)
        if item_m:
            try:
                desc = item_m.group(2).strip()
                qty = float(item_m.group(3))
                price = float(item_m.group(4).replace(",", ""))
                amt = float(item_m.group(5).replace(",", ""))
                items.append({
                    "item_name": desc,
                    "qty": qty,
                    "unit_price": price,
                    "total_price": amt
                })
            except Exception:
                pass

    if subtotal == 0.0 and items:
        subtotal = sum(i["total_price"] for i in items)
    if total_amount == 0.0:
        total_amount = round(subtotal * 1.18, 2)  # default 18% GST
    tax = round(total_amount - subtotal, 2)

    return {
        "vendor_name": vendor_name,
        "subtotal": subtotal,
        "tax": tax,
        "total_amount": total_amount,
        "delivery_days": delivery_days,
        "warranty_months": warranty_months,
        "after_sales_service": after_sales,
        "payment_terms": payment_terms,
        "items": items,
        "raw_text": text
    }

def analyze_proposals(proposal_title: str, department: str, raw_quotations: List[str]) -> Dict[str, Any]:
    """Performs multi-criteria decision analysis and market benchmarking on 2-3+ quotations."""
    parsed_quotes = [parse_quotation_text(q) for q in raw_quotations if q.strip()]
    if not parsed_quotes:
        raise ValueError("No valid quotations provided for scrutiny.")

    # Check vendor in ERP Vendor Master
    for q in parsed_quotes:
        v_rec = erp_db.get_vendor(name=q["vendor_name"])
        q["vendor_id"] = v_rec["vendor_id"] if v_rec else None
        q["is_existing_vendor"] = bool(v_rec)
        q["vendor_rating"] = "Verified University Partner" if v_rec else "New External Vendor"

    # Benchmark all items against online market prices (GeM, Amazon, IndiaMART)
    market_comparisons = []
    for q in parsed_quotes:
        q["item_benchmarks"] = []
        for it in q.get("items", []):
            b = benchmark_item_price(it["item_name"], it["unit_price"])
            it["market_benchmark_price"] = b["benchmark_price"]
            it["market_variance_pct"] = b["variance_pct"]
            it["market_verdict"] = b["badge"]
            q["item_benchmarks"].append(b)
            market_comparisons.append(b)

    # Multi-Criteria Scoring (Weights: Price 40%, Delivery 20%, Warranty 20%, After-Sales 20%)
    min_price = min(q["total_amount"] for q in parsed_quotes)
    min_delivery = min(q["delivery_days"] for q in parsed_quotes)
    max_warranty = max(q["warranty_months"] for q in parsed_quotes)

    for q in parsed_quotes:
        # 1. Price Score (40 pts max): Relative to L1
        price_ratio = min_price / q["total_amount"] if q["total_amount"] > 0 else 1.0
        score_price = round(price_ratio * 40.0, 1)

        # 2. Delivery Score (20 pts max): Faster is better
        # If delivery <= min_delivery -> 20 pts, decreases as delivery days increase
        del_ratio = min_delivery / max(1, q["delivery_days"])
        score_del = round(del_ratio * 20.0, 1)

        # 3. Warranty Score (20 pts max): Longer warranty is better
        war_ratio = q["warranty_months"] / max(1, max_warranty)
        score_war = round(war_ratio * 20.0, 1)

        # 4. After-Sales & Vendor Trust (20 pts max)
        score_service = 10.0  # Base
        if q["is_existing_vendor"]:
            score_service += 5.0
        text_lower = (q["after_sales_service"] + " " + q.get("raw_text", "")).lower()
        if "onsite" in text_lower or "24x7" in text_lower or "24hr" in text_lower:
            score_service += 3.0
        if "oem" in text_lower or "authorized" in text_lower or "premier" in text_lower:
            score_service += 2.0
        score_service = min(20.0, score_service)

        total_score = round(score_price + score_del + score_war + score_service, 1)
        q["score_price"] = score_price
        q["score_delivery"] = score_del
        q["score_warranty"] = score_war
        q["score_service"] = score_service
        q["total_score"] = total_score

    # Assign Badges
    best_overall = max(parsed_quotes, key=lambda x: x["total_score"])
    lowest_cost = min(parsed_quotes, key=lambda x: x["total_amount"])
    fastest_del = min(parsed_quotes, key=lambda x: x["delivery_days"])
    max_war = max(parsed_quotes, key=lambda x: x["warranty_months"])

    for q in parsed_quotes:
        badges = []
        if q == best_overall:
            badges.append("🏆 Best Overall Value (Recommended)")
            q["recommendation_tag"] = "RECOMMENDED_BEST_VALUE"
        elif q == lowest_cost:
            badges.append("🏷️ Lowest Initial Bid (L1 Commercial)")
            q["recommendation_tag"] = "LOWEST_COST_L1"
        elif q == fastest_del:
            badges.append("⚡ Fastest Delivery")
            q["recommendation_tag"] = "FASTEST_DELIVERY"
        elif q == max_war:
            badges.append("🛡️ Maximum Warranty Assurance")
            q["recommendation_tag"] = "MAX_WARRANTY"
        else:
            badges.append("⚪ Standard Proposal")
            q["recommendation_tag"] = "STANDARD_PROPOSAL"
        q["badge_text"] = " • ".join(badges)

    # Executive Summary for HoD & Purchase Officer
    summary_md = f"""### 📋 Executive Quotation Scrutiny Summary (Comparative Statement)
**Proposal:** {proposal_title} | **Department:** {department}

- **Quotation Count Analyzed:** {len(parsed_quotes)} vendor bids evaluated across **Commercial Price, Delivery Lead-Time, Warranty Protection, and After-Sales Service SLA**.
- **Recommended Proposal:** **{best_overall['vendor_name']}** (Total Composite Score: **{best_overall['total_score']} / 100**).
  - Quoted Amount: **₹{best_overall['total_amount']:,.2f}** (Includes GST)
  - Delivery Timeline: **{best_overall['delivery_days']} days**
  - Warranty / Guarantee: **{best_overall['warranty_months']} months** ({best_overall['after_sales_service']})
  - Vendor Status: **{best_overall['vendor_rating']}**

#### Why Not Always the Lowest Cost (L1)?
"""
    if best_overall != lowest_cost:
        diff_amt = best_overall["total_amount"] - lowest_cost["total_amount"]
        summary_md += f"""- **Price vs Quality Trade-off:** While **{lowest_cost['vendor_name']}** offers the lowest initial quote (₹{lowest_cost['total_amount']:,.2f}, diff ₹{diff_amt:,.2f}), **{best_overall['vendor_name']}** provides **{best_overall['warranty_months'] - lowest_cost['warranty_months']} additional months of warranty**, faster delivery ({best_overall['delivery_days']}d vs {lowest_cost['delivery_days']}d), and superior onsite SLA—minimizing university lifecycle costs and hardware downtime.
"""
    else:
        summary_md += f"- **Dominant Winner:** **{best_overall['vendor_name']}** achieved both the lowest commercial cost and superior delivery/service terms.\n"

    return {
        "title": proposal_title,
        "department": department,
        "recommended_vendor": best_overall["vendor_name"],
        "recommended_amount": best_overall["total_amount"],
        "quotations": parsed_quotes,
        "market_comparisons": market_comparisons,
        "comparative_statement_markdown": summary_md
    }
