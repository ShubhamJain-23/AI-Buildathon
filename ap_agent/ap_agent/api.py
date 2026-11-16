"""FastAPI Backend and Glass-Box Maker-Checker Observability Dashboard.
Implements the 3 role-tailored Checker views:
1) Procurement Officer View
2) Accounts Division View
3) Respective Department View
"""
import os
import json
import tempfile
from datetime import date
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .erp_db import (
    init_db, get_connection, post_erp_payment, get_ledger_balance,
    get_department_budget, lookup_po, get_all_departments,
    save_proposal, get_proposals_list, get_proposal_full, act_proposal
)
from .quotation_analyzer import analyze_proposals
from .market_search import benchmark_item_price
from .document_loader import extract_text_from_bytes
from .gemini_agent import APAgentMaker
from .erp_mcp_server import mcp_server
from decimal import Decimal as D
from .models import Vendor, PO, POLine, GRN, GRNLine, Budget
from .pipeline import Store

def seed(today=date(2026, 11, 15)):
    s = Store(today)
    s.vendors["V001"] = Vendor("V001", "Sharma Lab Supplies Pvt Ltd", "08ABCDE1234F1Z5", 30, True, D("0.02"), 10)
    s.vendors["V002"] = Vendor("V002", "CampusTech Services LLP", "08PQRST5678G1Z2", 45)
    s.pos["PO-1001"] = PO("PO-1001", "V001", "CHEM", [
        POLine(1, "LAB-REAG-01", "Reagent kit", D(100), D("450.00")),
        POLine(2, "LAB-GLOVE-02", "Nitrile gloves box", D(50), D("200.00"))])
    s.pos["PO-1002"] = PO("PO-1002", "V002", "IT", [POLine(1, "AMC-SRV-01", "Server AMC annual", D(1), D("400000.00"))])
    s.grns.append(GRN("GRN-1", "PO-1001", date(2026, 11, 5), [GRNLine("LAB-REAG-01", D(60)), GRNLine("LAB-GLOVE-02", D(50))]))
    s.grns.append(GRN("GRN-2", "PO-1002", date(2026, 11, 1), [GRNLine("AMC-SRV-01", D(1))]))
    s.budgets["CHEM"] = Budget("CHEM", D("200000"), D("20000"), s.pos["PO-1001"].gross_total)
    s.budgets["IT"] = Budget("IT", D("500000"), D("50000"), s.pos["PO-1002"].gross_total)
    return s

store = seed()

# Initialize ERP DB
init_db(seed_data=True)

app = FastAPI(title="Intelligent Accounts Payable & Vendor Invoice Automation Agent (PS-09)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_maker = APAgentMaker()

@app.post("/settings/gemini_key")
def set_gemini_key(api_key: str = Form(...)):
    agent_maker.api_key = api_key.strip()
    return {"status": "success", "message": "Gemini API key updated successfully."}

@app.post("/invoices/intake")
def invoice_intake(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = None
):
    """Processes an invoice through the autonomous Maker agent."""
    file_bytes = None
    mime_type = None
    if file and hasattr(file, "file"):
        file_bytes = file.file.read()
        mime_type = getattr(file, "content_type", "application/pdf")
    
    if not text and not file_bytes:
        raise HTTPException(400, "Please provide invoice raw text or upload a document file (PDF/Image).")

    final_packet = agent_maker.run_invoice(
        invoice_text=text,
        file_bytes=file_bytes,
        mime_type=mime_type
    )
    
    inv_id = final_packet.get("invoice_id") if isinstance(final_packet, dict) else None
    if not inv_id:
        return final_packet

    res = get_invoice_details(inv_id)
    if isinstance(final_packet, dict) and "observability_logs" in final_packet:
        res["observability_logs"] = final_packet["observability_logs"]
    return res

@app.get("/invoices")
def list_invoices(status: Optional[str] = None):
    conn = get_connection()
    c = conn.cursor()
    if status:
        c.execute("SELECT * FROM invoices WHERE status = ? ORDER BY created_at DESC", (status,))
    else:
        c.execute("SELECT * FROM invoices ORDER BY created_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/invoices/{inv_id}")
def get_invoice_details(inv_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM invoices WHERE id = ?", (inv_id,))
    inv = c.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(404, f"Invoice {inv_id} not found")
    
    inv_dict = dict(inv)
    
    # Lines
    c.execute("SELECT * FROM invoice_lines WHERE invoice_id = ? ORDER BY line_no", (inv_id,))
    inv_dict["lines"] = [dict(r) for r in c.fetchall()]

    # Issues
    c.execute("SELECT * FROM invoice_issues WHERE invoice_id = ?", (inv_id,))
    inv_dict["issues"] = [dict(r) for r in c.fetchall()]

    # Approvals
    c.execute("SELECT * FROM approvals WHERE invoice_id = ? ORDER BY seq", (inv_id,))
    inv_dict["approvals"] = [dict(r) for r in c.fetchall()]

    # Payment schedule
    c.execute("SELECT * FROM payment_schedule WHERE invoice_id = ?", (inv_id,))
    ps = c.fetchone()
    inv_dict["payment_schedule"] = dict(ps) if ps else None

    # Fetch PO and GRN for checker views
    po = lookup_po(inv_dict.get("po_number")) if inv_dict.get("po_number") else None
    grns = mcp_server.execute_tool("erp_get_grns", {"po_number": inv_dict.get("po_number")}).get("grns", []) if inv_dict.get("po_number") else []
    budget = get_department_budget(po.get("department")) if po else None

    conn.close()

    # Build the 3 Maker-Checker Role Views
    lines = inv_dict["lines"]
    issues = inv_dict["issues"]
    
    checker_views = {
        "procurement_officer_view": {
            "po_number": inv_dict.get("po_number"),
            "po_status": po.get("status") if po else "NOT_FOUND",
            "vendor_name": inv_dict.get("vendor_name"),
            "lines_comparison": [
                {
                    "item_code": l.get("item_code"),
                    "description": l.get("description"),
                    "billed_qty": l.get("qty"),
                    "ordered_qty": next((pl["qty"] for pl in po.get("lines", []) if pl["item_code"] == l.get("item_code")), 0.0) if po else 0.0,
                    "received_qty": next((gl["qty"] for g in grns for gl in g.get("lines", []) if gl["item_code"] == l.get("item_code")), 0.0),
                    "billed_price": l.get("unit_price"),
                    "po_price": next((pl["unit_price"] for pl in po.get("lines", []) if pl["item_code"] == l.get("item_code")), 0.0) if po else 0.0,
                    "variance_pct": round(((l.get("unit_price", 0) - next((pl["unit_price"] for pl in po.get("lines", []) if pl["item_code"] == l.get("item_code")), l.get("unit_price", 0))) / next((pl["unit_price"] for pl in po.get("lines", []) if pl["item_code"] == l.get("item_code")), 1)) * 100, 2) if po else 0.0
                } for l in lines
            ],
            "procurement_alerts": [i for i in issues if i["code"] in ("NO_PO_LINE", "PRICE_VARIANCE", "NOT_RECEIVED", "QTY_EXCEEDS_RECEIPT", "QTY_EXCEEDS_PO")]
        },
        "accounts_division_view": {
            "subtotal": inv_dict.get("subtotal"),
            "tax_billed": inv_dict.get("tax"),
            "tax_expected": round(inv_dict.get("subtotal", 0) * (po.get("tax_rate", 0.18) if po else 0.18), 2),
            "total": inv_dict.get("total"),
            "tax_compliant": not any(i["code"] in ("TAX_MISMATCH", "TOTAL_MISMATCH", "LINE_MATH") for i in issues),
            "payment_schedule": inv_dict.get("payment_schedule"),
            "draft_ledger_entry": [
                {"side": "DR", "account": "5000-Departmental-Expense", "amount": inv_dict.get("subtotal")},
                {"side": "DR", "account": "1400-Input-Tax-GST", "amount": inv_dict.get("tax")},
                {"side": "CR", "account": "2000-Accounts-Payable", "amount": inv_dict.get("total")}
            ],
            "accounts_alerts": [i for i in issues if i["code"] in ("TAX_MISMATCH", "TOTAL_MISMATCH", "SUBTOTAL_MISMATCH", "DUPLICATE_EXACT", "DUPLICATE_SUSPECTED")]
        },
        "respective_department_view": {
            "department": po.get("department") if po else "GENERAL",
            "department_head_name": f"Head of {po.get('department') if po else 'General'} Department",
            "purpose": f"Procurement against PO {inv_dict.get('po_number')} ({inv_dict.get('vendor_name')})",
            "budget_allocated": budget.get("allocated") if budget else 0.0,
            "budget_actual": budget.get("actual") if budget else 0.0,
            "budget_committed": budget.get("committed") if budget else 0.0,
            "budget_available": budget.get("available") if budget else 0.0,
            "invoice_cost": inv_dict.get("total"),
            "utilization_after": round(((budget.get("actual", 0) + inv_dict.get("total", 0)) / budget.get("allocated", 1)) * 100, 1) if budget else 0.0,
            "department_alerts": [i for i in issues if i["code"].startswith("BUDGET")]
        }
    }
    inv_dict["checker_views"] = checker_views
    return inv_dict

@app.post("/invoices/{inv_id}/decision")
def checker_decision(
    inv_id: str,
    role: Optional[str] = Query(None),
    approve_: Optional[bool] = Query(None),
    approve: Optional[bool] = Query(None),
    by: Optional[str] = Query(None),
    acted_by: Optional[str] = Query(None),
    comments: Optional[str] = Query(None),
    role_form: Optional[str] = Form(None),
    approve_form: Optional[bool] = Form(None)
):
    """Checker role signs off or rejects the Maker's dossier."""
    eff_role = role if isinstance(role, str) else (role_form if isinstance(role_form, str) else "DEPARTMENT_HEAD")
    eff_approve = approve if isinstance(approve, bool) else (approve_ if isinstance(approve_, bool) else True)
    comm_str = comments if isinstance(comments, str) else "Sign-off recorded via Maker-Checker portal"
    act_str = acted_by if isinstance(acted_by, str) else (by if isinstance(by, str) else "officer")
    role_str = str(eff_role)
    approve_bool = bool(eff_approve)

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM approvals WHERE invoice_id = ? ORDER BY seq", (inv_id,))
    steps = [dict(r) for r in c.fetchall()]
    if not steps:
        conn.close()
        raise HTTPException(400, "No pending approval chain for this invoice.")

    # Find the current pending step
    pending_step = next((s for s in steps if s["status"] == "PENDING"), None)
    if not pending_step:
        conn.close()
        raise HTTPException(400, "All approval steps are already finalized.")

    if pending_step["role"] != role_str:
        conn.close()
        raise HTTPException(409, f"Sequence error: Awaiting sign-off from '{pending_step['role']}', not '{role_str}'.")

    new_status = "APPROVED" if approve_bool else "REJECTED"
    c.execute("""
    UPDATE approvals
    SET status = ?, acted_by = ?, acted_at = CURRENT_TIMESTAMP, comments = ?
    WHERE id = ?
    """, (new_status, act_str, comm_str, pending_step["id"]))
    conn.commit()

    if not approve_bool:
        c.execute("UPDATE invoices SET status = 'REJECTED' WHERE id = ?", (inv_id,))
        conn.commit()
        conn.close()
        return {"status": "REJECTED", "invoice_status": "REJECTED", "message": f"Invoice rejected by {eff_role}."}

    # Check if all steps approved
    c.execute("SELECT COUNT(*) as c FROM approvals WHERE invoice_id = ? AND status = 'PENDING'", (inv_id,))
    remaining = c.fetchone()["c"]
    
    if remaining == 0:
        # Full approval achieved! Trigger GATED ERP mutations
        c.execute("SELECT * FROM invoices WHERE id = ?", (inv_id,))
        inv = dict(c.fetchone())
        conn.close()
        
        # 1. Post double-entry liability
        mcp_server.execute_tool("erp_post_invoice_liability", {
            "invoice_id": inv_id,
            "subtotal": inv["subtotal"],
            "tax": inv["tax"],
            "total": inv["total"]
        })
        
        # 2. Schedule payment with MSME cap & cash discount
        mcp_server.execute_tool("erp_schedule_payment", {
            "invoice_id": inv_id,
            "vendor_id": inv["vendor_id"],
            "invoice_date": inv["invoice_date"],
            "total": inv["total"],
            "subtotal": inv["subtotal"]
        })

        # 3. Update department budget actual & release commitment
        po = lookup_po(inv["po_number"]) if inv["po_number"] else None
        if po:
            dept = po["department"]
            b = get_department_budget(dept)
            if b:
                rel = min(inv["total"], b["committed"])
                c_up = get_connection()
                c_up.execute("""
                UPDATE budgets 
                SET committed = committed - ?, actual = actual + ?
                WHERE department = ?
                """, (rel, inv["total"], dept))
                c_up.commit()
                c_up.close()

        c_fin = get_connection()
        c_fin.execute("UPDATE invoices SET status = 'SCHEDULED' WHERE id = ?", (inv_id,))
        c_fin.commit()
        c_fin.close()
        return {"status": "SCHEDULED", "invoice_status": "SCHEDULED",
                "message": "Full DoA approval completed. ERP double-entry ledger posted and payment scheduled."}

    conn.close()
    return {"status": "PENDING_APPROVAL", "invoice_status": "PENDING_APPROVAL",
            "message": f"Approved by {eff_role}. Forwarded to next approver."}

@app.post("/payments/{inv_id}/execute")
def execute_treasury_payout(inv_id: str):
    """Executes bank payment and posts double-entry cash outflow."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM payment_schedule WHERE invoice_id = ?", (inv_id,))
    ps = c.fetchone()
    if not ps:
        conn.close()
        raise HTTPException(404, "No payment scheduled for this invoice.")
    
    ps_dict = dict(ps)
    if ps_dict["status"] == "PAID":
        conn.close()
        raise HTTPException(400, "Invoice is already paid.")

    # Post ERP payment
    entries = post_erp_payment(
        invoice_id=inv_id,
        amount_paid=ps_dict["amount"],
        discount=ps_dict["discount_captured"]
    )
    conn.close()
    return {
        "status": "success",
        "message": f"Treasury payment of ₹{ps_dict['amount']:,.2f} executed successfully.",
        "discount_captured": ps_dict["discount_captured"],
        "ledger_entries": entries
    }

@app.get("/erp/overview")
def get_erp_overview():
    """Returns ERP overview stats: liabilities, departments, and active POs."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM budgets")
    budgets = [dict(r) for r in c.fetchall()]
    for b in budgets:
        b["available"] = round(b["allocated"] - b["actual"] - b["committed"], 2)

    c.execute("SELECT * FROM payment_schedule WHERE status = 'SCHEDULED' ORDER BY pay_on ASC")
    schedule = [dict(r) for r in c.fetchall()]
    
    conn.close()
    ledger = get_ledger_balance()
    return {
        "budgets": budgets,
        "payment_schedule": schedule,
        "ledger_summary": ledger
    }

@app.get("/payments/schedule")
def legacy_payment_schedule(horizon_days: int = 7):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM payment_schedule WHERE status = 'SCHEDULED' ORDER BY pay_on ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/liabilities")
def legacy_liabilities():
    ledger = get_ledger_balance()
    return {"ap_balance": f"{ledger.get('ap_liability', 0.0):.2f}"}

# --- University Department & Procurement Proposal Endpoints ---

@app.get("/departments")
def list_departments():
    """Returns all 12 University Departments with current budget allocations and HoD metadata."""
    return get_all_departments()

@app.get("/market/search")
def search_market(query: str, price: Optional[float] = 0.0):
    """Searches GeM, Amazon Business, and IndiaMART benchmarks for an item."""
    return benchmark_item_price(query, price)

@app.post("/proposals/scrutinize")
async def scrutinize_quotations(
    title: str = Form(...),
    department: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    quotations_json: Optional[str] = Form(None)
):
    """HoD uploads 2-3+ quotations across PDF, Image, Excel, Word (DOCX), PPTX, or Markdown.
    Agent extracts terms, line items, performs multi-factor MCDA scoring (Quality vs L1),
    and automatically queries live market prices across GeM Portal, Amazon Business, and IndiaMART."""
    quotes_list = []

    # 1. Process multi-format uploaded files (PDF, Image, Excel, DOCX, PPTX, Markdown)
    if files:
        for f in files:
            if not f or not f.filename:
                continue
            data = await f.read()
            if not data:
                continue
            text = extract_text_from_bytes(f.filename, data)
            if text and text.strip():
                quotes_list.append(text.strip())

    # 2. Process quotations_json fallback (e.g. for Presets or programmatic testing)
    if quotations_json and quotations_json.strip():
        raw = quotations_json.strip()
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                quotes_list.extend([str(q).strip() for q in parsed if str(q).strip()])
            else:
                quotes_list.append(str(parsed).strip())
        except Exception:
            quotes_list.extend([q.strip() for q in raw.split("---") if q.strip()])

    if len(quotes_list) < 2:
        raise HTTPException(
            400,
            f"University procurement rules (> ₹20,000) require at least 2 competitive vendor quotations. Received {len(quotes_list)} valid quotation(s)."
        )

    analysis = analyze_proposals(title, department, quotes_list)
    prop_id = save_proposal(analysis)
    full_prop = get_proposal_full(prop_id)
    full_prop["comparative_statement_markdown"] = analysis.get("comparative_statement_markdown")
    if not full_prop.get("market_comparisons") and analysis.get("market_comparisons"):
        full_prop["market_comparisons"] = analysis.get("market_comparisons")
    return full_prop

@app.get("/proposals")
def list_proposals():
    return get_proposals_list()

@app.get("/proposals/{prop_id}")
def get_proposal(prop_id: str):
    p = get_proposal_full(prop_id)
    if not p:
        raise HTTPException(404, f"Proposal {prop_id} not found")
    return p

@app.post("/proposals/{prop_id}/decision")
def decide_proposal(
    prop_id: str,
    role: str = Form(...),
    approve: bool = Form(...),
    acted_by: str = Form("officer"),
    comments: Optional[str] = Form(None)
):
    """Enforces the 4-step university workflow: HoD -> Purchase Officer -> Accounts -> CFO."""
    try:
        return act_proposal(prop_id, role, approve, acted_by, comments)
    except (PermissionError, ValueError) as e:
        raise HTTPException(409, str(e))

# --- Glass-Box Observability & Maker-Checker Dashboard ---
@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    with open(os.path.join(os.path.dirname(__file__), "dashboard.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/documentation", response_class=HTMLResponse)
@app.get("/docs-view", response_class=HTMLResponse)
def serve_docs_view():
    with open(os.path.join(os.path.dirname(__file__), "dashboard.html"), "r", encoding="utf-8") as f:
        html = f.read()
        return html.replace("let activeWorkflow = 'quotations';", "let activeWorkflow = 'docs';")
