"""Autonomous Gemini Accounts Payable (AP) Agent.
Acts as the autonomous 'Maker' in the Maker-Checker enterprise framework.
Decomposes goals, invokes ERP tools over MCP, performs self-reflection,
and produces tailored views for Procurement, Accounts, and Department Heads.
"""
import os
import json
import uuid
import re
from datetime import datetime, date
from decimal import Decimal as D
from typing import Dict, Any, List, Optional, Generator
import requests

from .erp_mcp_server import mcp_server
from . import erp_db
from .parser import parse_invoice_text

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

class APAgentMaker:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.mcp = mcp_server

    def _call_gemini_vision(self, file_bytes: bytes, mime_type: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes Gemini Multimodal Vision to extract structured invoice JSON."""
        if not self.api_key:
            return None
        import base64
        b64_data = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"inline_data": {"mime_type": mime_type, "data": b64_data}},
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }
        try:
            resp = requests.post(
                f"{GEMINI_API_URL}?key={self.api_key}",
                json=payload,
                timeout=30
            )
            if resp.status_code == 200:
                result = resp.json()
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception as e:
            print(f"[Gemini Vision Warning] Fallback triggered: {e}")
        return None

    def _call_gemini_reflection(self, audit_summary: Dict[str, Any]) -> str:
        """Invokes Gemini LLM to synthesize human-readable Maker-Checker findings."""
        if not self.api_key:
            return self._default_reflection_summary(audit_summary)
        prompt = f"""
You are an expert AI Autonomous Accounts Payable Auditor acting as the 'Maker' in a Maker-Checker framework for a University ERP.
Analyze this invoice audit dossier and generate a concise, professional executive recommendation for the human Checkers (Procurement Officer, Accounts Division, Department Head).

Audit Dossier:
{json.dumps(audit_summary, indent=2)}

Include:
1. Executive Verdict (Recommend Approval / Hold for Exception / Reject Duplicate).
2. Key Findings (3-way match tolerances, delivery verification, tax calculation).
3. Financial & Compliance Note (MSME 45-day rule, cash discount opportunities, budget encumbrance).
Format in clean Markdown with bullet points.
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        try:
            resp = requests.post(
                f"{GEMINI_API_URL}?key={self.api_key}",
                json=payload,
                timeout=20
            )
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass
        return self._default_reflection_summary(audit_summary)

    def _default_reflection_summary(self, audit: Dict[str, Any]) -> str:
        status = audit.get("recommended_status", "PENDING_APPROVAL")
        issues = audit.get("issues", [])
        if status == "REJECTED_DUPLICATE":
            return "### ⚠️ MAKER VERDICT: REJECT DUPLICATE\n- **Critical Risk:** This invoice was identified as an exact or suspected duplicate billing.\n- **Action Required:** Immediate rejection to prevent fraudulent or double university payment."
        elif status == "HOLD_EXCEPTION":
            issue_list = "\n".join([f"- **{i['code']}** ({i['severity']}): {i['message']}" for i in issues])
            return f"### 🛑 MAKER VERDICT: HOLD FOR EXCEPTIONS\n- **Discrepancies Detected during 3-Way Reconciliation:**\n{issue_list}\n- **Action Required:** Sent to Procurement Officer and Vendor for dispute resolution."
        else:
            return "### ✅ MAKER VERDICT: RECOMMEND FOR APPROVAL\n- **3-Way Match Verified:** Goods receipts match purchase order quantities within allowable 2% price tolerances.\n- **Compliance & Budget Validated:** Department budget has sufficient uncommitted headroom.\n- **Action:** Ready for sequential human Checker sign-off (Dept Head & Finance Controller)."

    def process_invoice(self,
                        invoice_text: Optional[str] = None,
                        file_bytes: Optional[bytes] = None,
                        mime_type: Optional[str] = None,
                        invoice_id: Optional[str] = None) -> Generator[Dict[str, Any], None, Dict[str, Any]]:
        """Autonomous ReAct loop yielding real-time observability steps."""
        inv_id = invoice_id or f"INV-{uuid.uuid4().hex[:8].upper()}"
        logs: List[Dict[str, Any]] = []

        def log_step(stage: str, thought: str, tool: Optional[str] = None,
                     tool_input: Optional[Any] = None, tool_output: Optional[Any] = None,
                     reflection: Optional[str] = None):
            entry = {
                "step": len(logs) + 1,
                "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "stage": stage,
                "thought": thought,
                "tool": tool,
                "tool_input": tool_input,
                "tool_output": tool_output,
                "reflection": reflection
            }
            logs.append(entry)
            return entry

        # --- STEP 1: Goal Decomposition ---
        yield log_step(
            stage="GOAL_DECOMPOSITION",
            thought=f"Initiating autonomous AP Maker audit for invoice {inv_id}. Planning multi-step verification: "
                    f"1) Multimodal ingestion, 2) ERP Vendor lookup via MCP, 3) Duplicate billing audit, "
                    f"4) 3-Way Match against PO & GRN receipts, 5) Department Budget verification, "
                    f"6) Self-reflection & Maker dossier generation for Procurement, Accounts, and Department Checkers."
        )

        # --- STEP 2: Ingestion & Document Understanding ---
        extracted_data = None
        if file_bytes and mime_type and self.api_key:
            yield log_step(
                stage="DOCUMENT_UNDERSTANDING",
                thought="Calling Gemini Multimodal Vision API to parse invoice document directly into structured JSON.",
                tool="gemini_vision_extract",
                tool_input={"mime_type": mime_type, "size_bytes": len(file_bytes)}
            )
            v_prompt = """Extract invoice details in JSON format:
            {
              "invoice_no": "...", "vendor_name": "...", "invoice_date": "YYYY-MM-DD",
              "po_number": "...", "currency": "INR", "subtotal": 0.0, "tax": 0.0, "total": 0.0,
              "lines": [{"line_no": 1, "item_code": "...", "description": "...", "qty": 1.0, "unit_price": 0.0, "amount": 0.0}]
            }"""
            extracted_data = self._call_gemini_vision(file_bytes, mime_type, v_prompt)

        if not extracted_data and invoice_text:
            yield log_step(
                stage="DOCUMENT_UNDERSTANDING",
                thought="Parsing invoice using deterministic semantic regex engine with confidence scoring.",
                tool="regex_parser",
                tool_input={"text_length": len(invoice_text)}
            )
            parsed_obj = parse_invoice_text(invoice_text)
            extracted_data = {
                "invoice_no": parsed_obj.invoice_no,
                "vendor_name": parsed_obj.vendor_name,
                "invoice_date": parsed_obj.invoice_date.strftime("%Y-%m-%d") if parsed_obj.invoice_date else "2026-11-15",
                "po_number": parsed_obj.po_number,
                "currency": parsed_obj.currency,
                "subtotal": float(parsed_obj.subtotal),
                "tax": float(parsed_obj.tax),
                "total": float(parsed_obj.total),
                "confidence": parsed_obj.confidence,
                "lines": [
                    {
                        "line_no": l.line_no,
                        "item_code": l.item_code,
                        "description": l.description,
                        "qty": float(l.qty),
                        "unit_price": float(l.unit_price),
                        "amount": float(l.amount)
                    } for l in parsed_obj.lines
                ]
            }

        if not extracted_data:
            extracted_data = {
                "invoice_no": "UNKNOWN", "vendor_name": "UNKNOWN", "invoice_date": "2026-11-15",
                "po_number": "", "subtotal": 0.0, "tax": 0.0, "total": 0.0, "confidence": 0.0, "lines": []
            }

        inv_no = extracted_data.get("invoice_no") or "INV-UNKNOWN"
        vendor_name = extracted_data.get("vendor_name") or "Unknown"
        po_no = extracted_data.get("po_number")
        inv_date = extracted_data.get("invoice_date") or "2026-11-15"
        total = float(extracted_data.get("total", 0.0))
        subtotal = float(extracted_data.get("subtotal", 0.0))
        tax = float(extracted_data.get("tax", 0.0))
        lines = extracted_data.get("lines", [])
        confidence = float(extracted_data.get("confidence", 1.0))

        yield log_step(
            stage="EXTRACTION_VERIFICATION",
            thought=f"Extracted Invoice #{inv_no} from '{vendor_name}', Total: ₹{total:,.2f}, PO Ref: {po_no}. Confidence: {confidence:.2f}.",
            tool_output=extracted_data,
            reflection="Checking arithmetic integrity: subtotal + tax vs total."
        )

        issues: List[Dict[str, Any]] = []

        # Arithmetic integrity
        calc_line_sum = sum(l["amount"] for l in lines)
        if lines and abs(calc_line_sum - subtotal) > 0.05:
            issues.append({"code": "SUBTOTAL_MISMATCH", "severity": "MAJOR", "message": f"Lines sum (₹{calc_line_sum:,.2f}) != subtotal (₹{subtotal:,.2f})"})
        if abs(subtotal + tax - total) > 1.0:
            issues.append({"code": "TOTAL_MISMATCH", "severity": "MAJOR", "message": f"Subtotal + tax (₹{subtotal+tax:,.2f}) != total (₹{total:,.2f})"})

        # --- STEP 3: ERP Vendor Resolution (MCP Tool) ---
        yield log_step(
            stage="MCP_TOOL_CALL",
            thought=f"Resolving vendor '{vendor_name}' in University Vendor Master via ERP MCP tool.",
            tool="erp_lookup_vendor",
            tool_input={"name": vendor_name}
        )
        vendor_resp = self.mcp.execute_tool("erp_lookup_vendor", {"name": vendor_name})
        vendor = vendor_resp.get("vendor")
        vendor_id = vendor["vendor_id"] if vendor else None

        if not vendor:
            issues.append({"code": "UNKNOWN_VENDOR", "severity": "CRITICAL", "message": f"Vendor '{vendor_name}' not registered in University Vendor Master"})
            yield log_step(
                stage="REFLECTION",
                thought="Vendor could not be verified in ERP master. Flagging UNKNOWN_VENDOR critical exception.",
                tool_output=vendor_resp,
                reflection="Cannot proceed with standard matching without authenticated vendor record."
            )
        else:
            yield log_step(
                stage="MCP_TOOL_RESULT",
                thought=f"Vendor resolved: {vendor['name']} (ID: {vendor['vendor_id']}, Terms: {vendor['terms_days']}d, MSME: {bool(vendor['msme'])})",
                tool_output=vendor_resp
            )

        # --- STEP 4: Duplicate Billing Check (MCP Tool) ---
        dup_result = {"is_duplicate": False}
        if vendor_id:
            yield log_step(
                stage="MCP_TOOL_CALL",
                thought="Executing duplicate billing audit: exact normalized invoice number & 30-day window check.",
                tool="erp_check_duplicate",
                tool_input={"vendor_id": vendor_id, "invoice_no": inv_no, "total": total, "po_number": po_no, "invoice_date": inv_date}
            )
            dup_resp = self.mcp.execute_tool("erp_check_duplicate", {
                "vendor_id": vendor_id, "invoice_no": inv_no, "total": total, "po_number": po_no, "invoice_date": inv_date
            })
            dup_result = dup_resp.get("duplicate_analysis", {})
            if dup_result.get("is_duplicate"):
                dup_code = "DUPLICATE_EXACT" if dup_result.get("type") == "EXACT" else "DUPLICATE_SUSPECTED"
                issues.append({"code": dup_code, "severity": "CRITICAL", "message": dup_result.get("reason")})
                yield log_step(
                    stage="REFLECTION",
                    thought=f"CRITICAL FRAUD/ERROR ALERT: {dup_result.get('reason')}. Marking invoice for rejection.",
                    tool_output=dup_resp,
                    reflection="Duplicate invoice detected. Halting auto-approval recommendation."
                )

        # --- STEP 5: Purchase Order & Goods Receipt 3-Way Match ---
        po = None
        grns = []
        prior_billed = {}
        if po_no and not dup_result.get("is_duplicate"):
            yield log_step(
                stage="MCP_TOOL_CALL",
                thought=f"Fetching Purchase Order {po_no} details and authorized lines from ERP.",
                tool="erp_lookup_po",
                tool_input={"po_number": po_no}
            )
            po_resp = self.mcp.execute_tool("erp_lookup_po", {"po_number": po_no})
            po = po_resp.get("po")
            if not po:
                issues.append({"code": "PO_NOT_FOUND", "severity": "CRITICAL", "message": f"PO {po_no} does not exist in ERP"})
            else:
                # Fetch GRNs
                grn_resp = self.mcp.execute_tool("erp_get_grns", {"po_number": po_no})
                grns = grn_resp.get("grns", [])
                
                # Fetch prior cumulative billed
                cum_resp = self.mcp.execute_tool("erp_get_cumulative_billed", {"po_number": po_no, "exclude_invoice_id": inv_id})
                prior_billed = cum_resp.get("cumulative_billed", {})

                yield log_step(
                    stage="3_WAY_MATCHING",
                    thought=f"Reconciling Invoice vs PO {po_no} vs {len(grns)} Goods Receipts.",
                    tool="execute_three_way_match",
                    tool_input={"po_lines_count": len(po.get("lines", [])), "grns_found": len(grns)}
                )

                # Execute matching
                received_map: Dict[str, float] = {}
                for g in grns:
                    for gl in g.get("lines", []):
                        code = gl["item_code"].upper()
                        received_map[code] = received_map.get(code, 0.0) + float(gl["qty"])

                po_lines_by_code = {pl["item_code"].upper(): pl for pl in po.get("lines", [])}

                # Check tax rate
                expected_tax = subtotal * float(po.get("tax_rate", 0.18))
                if abs(expected_tax - tax) > 1.0:
                    issues.append({"code": "TAX_MISMATCH", "severity": "MAJOR",
                                   "message": f"Billed tax (₹{tax:,.2f}) != expected tax (₹{expected_tax:,.2f}) at {po.get('tax_rate', 0.18)*100:.0f}% GST"})

                # Match each line
                for l in lines:
                    code = (l.get("item_code") or "").upper()
                    pl = po_lines_by_code.get(code)
                    if not pl:
                        issues.append({"code": "NO_PO_LINE", "severity": "CRITICAL",
                                       "message": f"Item '{l.get('item_code')}' ({l.get('description')}) was not ordered on PO {po_no}",
                                       "line_no": l.get("line_no")})
                        continue

                    # Price tolerance check (2%)
                    po_price = float(pl["unit_price"])
                    inv_price = float(l["unit_price"])
                    if po_price > 0 and abs(inv_price - po_price) / po_price > 0.02:
                        diff = (inv_price - po_price) * float(l["qty"])
                        issues.append({"code": "PRICE_VARIANCE", "severity": "MAJOR",
                                       "message": f"Billed unit price ₹{inv_price:,.2f} exceeds PO agreed price ₹{po_price:,.2f} by >2% (Impact: ₹{diff:+,.2f})",
                                       "line_no": l.get("line_no")})

                    # Quantity checks
                    billed_qty = float(l["qty"])
                    prior_qty = float(prior_billed.get(code, {}).get("billed_qty", 0.0))
                    total_billed = prior_qty + billed_qty
                    rec_qty = received_map.get(code, 0.0)

                    if rec_qty == 0:
                        issues.append({"code": "NOT_RECEIVED", "severity": "CRITICAL",
                                       "message": f"No goods receipt record found for {code} in university stores",
                                       "line_no": l.get("line_no")})
                    elif total_billed > rec_qty:
                        issues.append({"code": "QTY_EXCEEDS_RECEIPT", "severity": "CRITICAL",
                                       "message": f"Cumulative billed quantity ({total_billed:.1f}) exceeds goods received ({rec_qty:.1f})",
                                       "line_no": l.get("line_no")})

                    if total_billed > float(pl["qty"]):
                        issues.append({"code": "QTY_EXCEEDS_PO", "severity": "CRITICAL",
                                       "message": f"Cumulative billed quantity ({total_billed:.1f}) exceeds PO ordered quantity ({pl['qty']:.1f})",
                                       "line_no": l.get("line_no")})

        # --- STEP 6: Department Budget Encumbrance Check ---
        budget_info = None
        budget_exceeded = False
        if po and not dup_result.get("is_duplicate"):
            dept = po.get("department", "GENERAL")
            yield log_step(
                stage="MCP_TOOL_CALL",
                thought=f"Auditing budget headroom for Department '{dept}' via ERP MCP tool.",
                tool="erp_check_budget",
                tool_input={"department": dept, "invoice_total": total}
            )
            b_resp = self.mcp.execute_tool("erp_check_budget", {"department": dept, "invoice_total": total})
            budget_info = b_resp
            if b_resp.get("status") == "success":
                budget_exceeded = b_resp.get("budget_exceeded", False)
                if budget_exceeded:
                    issues.append({"code": "BUDGET_EXCEEDED", "severity": "MAJOR",
                                   "message": f"Invoice increment exceeds available budget in Department {dept} (Available: ₹{b_resp['available']:,.2f})"})
                elif b_resp.get("warning_near_limit"):
                    issues.append({"code": "BUDGET_NEAR_LIMIT", "severity": "INFO",
                                   "message": f"Department {dept} budget will reach {b_resp['utilization_pct_after']}% after posting"})
            else:
                issues.append({"code": "NO_BUDGET", "severity": "CRITICAL", "message": b_resp.get("message")})

        # --- STEP 7: Status & DoA Approval Chain Determination ---
        has_critical = any(i["severity"] == "CRITICAL" for i in issues)
        has_major = any(i["severity"] == "MAJOR" and not i["code"].startswith("BUDGET") for i in issues)

        if dup_result.get("is_duplicate"):
            final_status = "REJECTED_DUPLICATE"
        elif has_critical or has_major:
            final_status = "HOLD_EXCEPTION"
        else:
            final_status = "PENDING_APPROVAL"

        # DoA approval tiers
        doa_chain = []
        if final_status == "PENDING_APPROVAL":
            if total <= 50000:
                doa_chain = ["DEPARTMENT_HEAD"]
            elif total <= 250000:
                doa_chain = ["DEPARTMENT_HEAD", "FINANCE_CONTROLLER"]
            elif total <= 1000000:
                doa_chain = ["DEPARTMENT_HEAD", "FINANCE_CONTROLLER", "REGISTRAR"]
            else:
                doa_chain = ["DEPARTMENT_HEAD", "FINANCE_CONTROLLER", "REGISTRAR", "VICE_CHANCELLOR"]

            # Dynamic escalation for budget overrun
            if budget_exceeded and "FINANCE_CONTROLLER" not in doa_chain:
                doa_chain.insert(1, "FINANCE_CONTROLLER")

        # Payment Terms & Discounts
        payment_preview = None
        if vendor:
            from datetime import timedelta
            inv_dt = datetime.strptime(inv_date, "%Y-%m-%d").date()
            t_days = vendor["terms_days"]
            msme_cap = False
            if vendor["msme"] and t_days > 45:
                t_days = 45
                msme_cap = True
            due_dt = inv_dt + timedelta(days=t_days)
            disc_amt = 0.0
            pay_dt = due_dt
            notes = []
            if msme_cap:
                notes.append("MSME 45-day statutory prompt-payment cap applied.")
            if vendor["discount_pct"] > 0 and vendor["discount_days"] > 0:
                d_cut = inv_dt + timedelta(days=vendor["discount_days"])
                if date(2026, 11, 15) <= d_cut:
                    disc_amt = round(subtotal * vendor["discount_pct"], 2)
                    pay_dt = d_cut
                    notes.append(f"Early payment discount {vendor['discount_pct']*100:.1f}%: ₹{disc_amt:,.2f} potential saving.")
            payment_preview = {
                "pay_on": pay_dt.strftime("%Y-%m-%d"),
                "due_date": due_dt.strftime("%Y-%m-%d"),
                "amount": total - disc_amt,
                "discount_saving": disc_amt,
                "msme_capped": msme_cap,
                "notes": notes
            }

        # --- STEP 8: Constructing Tailored Checker Views ---
        maker_summary_text = self._call_gemini_reflection({
            "invoice_no": inv_no, "vendor": vendor_name, "total": total,
            "recommended_status": final_status, "issues": issues,
            "budget": budget_info, "payment": payment_preview
        })

        # Save to database
        import re
        norm_no = re.sub(r"[^A-Z0-9]", "", (inv_no or "").upper()).lstrip("0")
        db_norm_no = norm_no if final_status != "REJECTED_DUPLICATE" else f"{norm_no}_DUP_{inv_id}"
        conn = erp_db.get_connection()
        c = conn.cursor()
        c.execute("""
        INSERT OR REPLACE INTO invoices 
        (id, vendor_id, vendor_name, invoice_no, invoice_no_norm, invoice_date, po_number,
         subtotal, tax, total, currency, status, confidence, maker_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inv_id, vendor_id, vendor_name, inv_no, db_norm_no, inv_date, po_no,
            subtotal, tax, total, "INR", final_status, confidence, maker_summary_text
        ))
        
        # Insert lines
        c.execute("DELETE FROM invoice_lines WHERE invoice_id = ?", (inv_id,))
        for l in lines:
            c.execute("""
            INSERT INTO invoice_lines (invoice_id, line_no, item_code, description, qty, unit_price, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (inv_id, l.get("line_no", 1), l.get("item_code"), l.get("description"),
                  l.get("qty", 0.0), l.get("unit_price", 0.0), l.get("amount", 0.0)))

        # Insert issues
        c.execute("DELETE FROM invoice_issues WHERE invoice_id = ?", (inv_id,))
        for iss in issues:
            c.execute("""
            INSERT INTO invoice_issues (invoice_id, code, severity, message, line_no)
            VALUES (?, ?, ?, ?, ?)
            """, (inv_id, iss["code"], iss["severity"], iss["message"], iss.get("line_no")))

        # Insert approval steps
        c.execute("DELETE FROM approvals WHERE invoice_id = ?", (inv_id,))
        for idx, role in enumerate(doa_chain):
            c.execute("""
            INSERT INTO approvals (invoice_id, seq, role, status)
            VALUES (?, ?, ?, 'PENDING')
            """, (inv_id, idx + 1, role))

        conn.commit()
        conn.close()

        # Build Tailored Roles
        checker_views = {
            "procurement_officer_view": {
                "po_number": po_no,
                "po_status": po.get("status") if po else "NOT_FOUND",
                "vendor_name": vendor_name,
                "lines_comparison": [
                    {
                        "item_code": l.get("item_code"),
                        "description": l.get("description"),
                        "billed_qty": l.get("qty"),
                        "ordered_qty": next((pl["qty"] for pl in po.get("lines", []) if pl["item_code"] == l.get("item_code")), 0.0) if po else 0.0,
                        "received_qty": next((gl["qty"] for g in grns for gl in g.get("lines", []) if gl["item_code"] == l.get("item_code")), 0.0),
                        "billed_price": l.get("unit_price"),
                        "po_price": next((pl["unit_price"] for pl in po.get("lines", []) if pl["item_code"] == l.get("item_code")), 0.0) if po else 0.0,
                    } for l in lines
                ],
                "procurement_alerts": [i for i in issues if i["code"] in ("NO_PO_LINE", "PRICE_VARIANCE", "NOT_RECEIVED", "QTY_EXCEEDS_RECEIPT", "QTY_EXCEEDS_PO")]
            },
            "accounts_division_view": {
                "subtotal": subtotal,
                "tax_billed": tax,
                "tax_expected": subtotal * float(po.get("tax_rate", 0.18)) if po else tax,
                "total": total,
                "tax_compliant": not any(i["code"] in ("TAX_MISMATCH", "TOTAL_MISMATCH", "LINE_MATH") for i in issues),
                "msme_applicable": vendor.get("msme") if vendor else False,
                "payment_schedule": payment_preview,
                "draft_ledger_entry": [
                    {"side": "DR", "account": "5000-Departmental-Expense", "amount": subtotal},
                    {"side": "DR", "account": "1400-Input-Tax-GST", "amount": tax},
                    {"side": "CR", "account": "2000-Accounts-Payable", "amount": total}
                ],
                "accounts_alerts": [i for i in issues if i["code"] in ("TAX_MISMATCH", "TOTAL_MISMATCH", "SUBTOTAL_MISMATCH", "DUPLICATE_EXACT", "DUPLICATE_SUSPECTED")]
            },
            "respective_department_view": {
                "department": po.get("department") if po else "GENERAL",
                "purpose": f"Purchase against PO {po_no} for {vendor_name}",
                "budget_allocated": budget_info.get("allocated") if budget_info else 0.0,
                "budget_actual": budget_info.get("actual") if budget_info else 0.0,
                "budget_committed": budget_info.get("committed") if budget_info else 0.0,
                "budget_available": budget_info.get("available") if budget_info else 0.0,
                "invoice_cost": total,
                "utilization_after": budget_info.get("utilization_pct_after") if budget_info else 0.0,
                "department_alerts": [i for i in issues if i["code"].startswith("BUDGET")]
            }
        }

        final_packet = {
            "invoice_id": inv_id,
            "invoice_no": inv_no,
            "vendor_name": vendor_name,
            "po_number": po_no,
            "total": total,
            "status": final_status,
            "confidence": confidence,
            "issues": issues,
            "approval_chain": doa_chain,
            "payment_preview": payment_preview,
            "maker_verdict_markdown": maker_summary_text,
            "checker_views": checker_views,
            "observability_logs": logs
        }

        yield log_step(
            stage="MAKER_DOSSIER_COMPLETE",
            thought=f"Maker dossier compiled with status '{final_status}'. Prepared 3 role-tailored views (Procurement, Accounts, Department) awaiting human Checker verification.",
            tool="generate_maker_dossier",
            tool_output={"status": final_status, "approvers": doa_chain, "issues_count": len(issues)}
        )

        yield final_packet
        return final_packet

    def run_invoice(self,
                    invoice_text: Optional[str] = None,
                    file_bytes: Optional[bytes] = None,
                    mime_type: Optional[str] = None,
                    invoice_id: Optional[str] = None) -> Dict[str, Any]:
        """Synchronously processes an invoice and returns the completed Maker Dossier."""
        packet = None
        for step in self.process_invoice(invoice_text=invoice_text, file_bytes=file_bytes,
                                         mime_type=mime_type, invoice_id=invoice_id):
            if isinstance(step, dict) and "invoice_id" in step:
                packet = step
        return packet
