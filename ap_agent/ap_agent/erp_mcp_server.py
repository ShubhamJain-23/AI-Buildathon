"""Model Context Protocol (MCP) Server for Enterprise University ERP.
Exposes standard ERP query and ledger mutation tools for AI Agents.
Can be executed as a standalone stdio/SSE server or imported directly as a tool provider.
"""
import json
from typing import Dict, Any, List, Optional
from . import erp_db

ERP_TOOLS_SPEC = [
    {
        "name": "erp_lookup_vendor",
        "description": "Lookup vendor in the University Vendor Master by name or ID. Returns credit terms, MSME certification status, and early-payment discount terms.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Vendor name (fuzzy matched)"},
                "vendor_id": {"type": "string", "description": "Unique vendor identifier (e.g. V001)"}
            }
        }
    },
    {
        "name": "erp_lookup_po",
        "description": "Fetch official Purchase Order (PO) details from the ERP, including ordered line items, approved quantities, unit prices, department, and tax rate.",
        "parameters": {
            "type": "object",
            "properties": {
                "po_number": {"type": "string", "description": "Purchase Order number (e.g. PO-1001)"}
            },
            "required": ["po_number"]
        }
    },
    {
        "name": "erp_get_grns",
        "description": "Retrieve all Goods Receipt Notes (GRN) logged by university stores/receiving bays for a specific Purchase Order.",
        "parameters": {
            "type": "object",
            "properties": {
                "po_number": {"type": "string", "description": "Purchase Order number to check goods receipts for"}
            },
            "required": ["po_number"]
        }
    },
    {
        "name": "erp_check_budget",
        "description": "Check department budget availability. Computes allocated, actual, committed, and available balance, and assesses whether the invoice amount causes a budget overrun.",
        "parameters": {
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "Department code (e.g. CHEM, IT, BIO)"},
                "invoice_total": {"type": "number", "description": "Total gross amount of the invoice"},
                "po_outstanding": {"type": "number", "description": "Remaining committed amount already encumbered on the PO"}
            },
            "required": ["department", "invoice_total"]
        }
    },
    {
        "name": "erp_check_duplicate",
        "description": "Audit for exact normalized invoice numbers and suspected duplicate billings within a 30-day window for the same vendor and amount.",
        "parameters": {
            "type": "object",
            "properties": {
                "vendor_id": {"type": "string", "description": "Vendor identifier"},
                "invoice_no": {"type": "string", "description": "Invoice number to inspect"},
                "total": {"type": "number", "description": "Total invoice amount"},
                "po_number": {"type": "string", "description": "Purchase order number"},
                "invoice_date": {"type": "string", "description": "Invoice date in YYYY-MM-DD format"}
            },
            "required": ["vendor_id", "invoice_no", "total"]
        }
    },
    {
        "name": "erp_get_cumulative_billed",
        "description": "Retrieve the cumulative quantity and amounts already billed on earlier accepted invoices for a given PO to prevent cumulative overbilling.",
        "parameters": {
            "type": "object",
            "properties": {
                "po_number": {"type": "string", "description": "Purchase Order number"},
                "exclude_invoice_id": {"type": "string", "description": "Current invoice ID to exclude from cumulative sum"}
            },
            "required": ["po_number"]
        }
    },
    {
        "name": "erp_post_invoice_liability",
        "description": "[GATED ACTION] Post double-entry accounting ledger entries to record accounts payable liability upon human approval.",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "description": "Invoice ID"},
                "subtotal": {"type": "number", "description": "Net expense subtotal (DR)"},
                "tax": {"type": "number", "description": "Input tax GST (DR)"},
                "total": {"type": "number", "description": "Gross accounts payable liability (CR)"},
                "expense_account": {"type": "string", "description": "Debit expense account name"}
            },
            "required": ["invoice_id", "subtotal", "tax", "total"]
        }
    },
    {
        "name": "erp_schedule_payment",
        "description": "Calculate payment schedule adhering to MSME statutory 45-day caps and capturing vendor cash discounts.",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_id": {"type": "string", "description": "Invoice ID"},
                "vendor_id": {"type": "string", "description": "Vendor ID"},
                "invoice_date": {"type": "string", "description": "Invoice date YYYY-MM-DD"},
                "total": {"type": "number", "description": "Invoice total amount"},
                "subtotal": {"type": "number", "description": "Invoice subtotal amount"}
            },
            "required": ["invoice_id", "vendor_id", "invoice_date", "total", "subtotal"]
        }
    }
]

class ERPMCPServer:
    """In-process and callable tool handler for the ERP MCP server."""
    
    def __init__(self):
        erp_db.init_db(seed_data=True)

    def list_tools(self) -> List[Dict[str, Any]]:
        return ERP_TOOLS_SPEC

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an MCP tool call to the ERP backend."""
        try:
            if name == "erp_lookup_vendor":
                vendor = erp_db.get_vendor(vendor_id=arguments.get("vendor_id"), name=arguments.get("name"))
                if not vendor:
                    return {"status": "error", "message": f"Vendor not found in ERP Master"}
                return {"status": "success", "vendor": vendor}

            elif name == "erp_lookup_po":
                po = erp_db.lookup_po(arguments["po_number"])
                if not po:
                    return {"status": "error", "message": f"PO {arguments['po_number']} not found in ERP"}
                return {"status": "success", "po": po}

            elif name == "erp_get_grns":
                grns = erp_db.get_grns_for_po(arguments["po_number"])
                return {"status": "success", "grns": grns}

            elif name == "erp_check_budget":
                dept = arguments["department"]
                inv_total = float(arguments["invoice_total"])
                po_out = float(arguments.get("po_outstanding", 0.0))
                b = erp_db.get_department_budget(dept)
                if not b:
                    return {"status": "error", "code": "NO_BUDGET", "message": f"No budget allocated for department {dept}"}
                
                # Invoices against an existing PO only consume the uncommitted increment
                increment = max(0.0, inv_total - po_out)
                is_exceeded = increment > b["available"]
                pct_after = round(((b["actual"] + b["committed"] - po_out + inv_total) / b["allocated"]) * 100, 1) if b["allocated"] > 0 else 100.0

                return {
                    "status": "success",
                    "department": dept,
                    "allocated": b["allocated"],
                    "actual": b["actual"],
                    "committed": b["committed"],
                    "available": b["available"],
                    "incremental_consumption": increment,
                    "budget_exceeded": is_exceeded,
                    "utilization_pct_after": pct_after,
                    "warning_near_limit": pct_after > 90.0
                }

            elif name == "erp_check_duplicate":
                res = erp_db.check_duplicate(
                    arguments["vendor_id"],
                    arguments["invoice_no"],
                    float(arguments["total"]),
                    arguments.get("po_number", ""),
                    arguments.get("invoice_date", "")
                )
                return {"status": "success", "duplicate_analysis": res}

            elif name == "erp_get_cumulative_billed":
                billed = erp_db.get_cumulative_invoiced(arguments["po_number"], arguments.get("exclude_invoice_id"))
                return {"status": "success", "cumulative_billed": billed}

            elif name == "erp_post_invoice_liability":
                entries = erp_db.post_erp_liability(
                    arguments["invoice_id"],
                    float(arguments["subtotal"]),
                    float(arguments["tax"]),
                    float(arguments["total"]),
                    arguments.get("expense_account", "5000-Departmental-Expense")
                )
                return {"status": "success", "entries_posted": entries, "message": "Double-entry AP liability successfully posted."}

            elif name == "erp_schedule_payment":
                from datetime import datetime, timedelta
                vendor = erp_db.get_vendor(vendor_id=arguments["vendor_id"])
                if not vendor:
                    return {"status": "error", "message": "Vendor not found"}
                
                inv_dt = datetime.strptime(arguments["invoice_date"], "%Y-%m-%d").date()
                terms = vendor["terms_days"]
                msme_applied = False
                if vendor["msme"] and terms > 45:
                    terms = 45
                    msme_applied = True
                
                due_date = inv_dt + timedelta(days=terms)
                pay_on = due_date
                total = float(arguments["total"])
                subtotal = float(arguments["subtotal"])
                discount_captured = 0.0
                notes = []

                if msme_applied:
                    notes.append("MSME 45-day statutory prompt-payment cap applied.")
                
                if vendor["discount_pct"] > 0 and vendor["discount_days"] > 0:
                    disc_cutoff = inv_dt + timedelta(days=vendor["discount_days"])
                    # Check if today is eligible
                    from datetime import date
                    today = date(2026, 11, 15)  # Simulated current date
                    if today <= disc_cutoff:
                        discount_captured = round(subtotal * vendor["discount_pct"], 2)
                        pay_on = disc_cutoff
                        notes.append(f"Early payment discount {vendor['discount_pct']*100:.1f}% captured: ₹{discount_captured:,.2f} saved.")

                conn = erp_db.get_connection()
                c = conn.cursor()
                c.execute("""
                INSERT OR REPLACE INTO payment_schedule (invoice_id, pay_on, due_date, amount, discount_captured, msme_capped, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    arguments["invoice_id"],
                    pay_on.strftime("%Y-%m-%d"),
                    due_date.strftime("%Y-%m-%d"),
                    total - discount_captured,
                    discount_captured,
                    1 if msme_applied else 0,
                    "; ".join(notes)
                ))
                conn.commit()
                conn.close()

                return {
                    "status": "success",
                    "pay_on": pay_on.strftime("%Y-%m-%d"),
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "amount_payable": total - discount_captured,
                    "discount_captured": discount_captured,
                    "msme_capped": msme_applied,
                    "notes": notes
                }

            else:
                return {"status": "error", "message": f"Unknown tool '{name}'"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

# Singleton server instance
mcp_server = ERPMCPServer()
