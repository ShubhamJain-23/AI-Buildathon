---
name: ap-agent
description: Complete guide and operational toolkit for the Accounts Payable (AP) Invoice Automation Agent (PS-09). Use when building, testing, extending, operating, or integrating the AP invoice processing agent — covers invoice ingestion (OCR/regex/LLM), duplicate detection, 3-way matching (PO, GRN, invoice lines), budget verification, DoA approval chains, MSME compliance, early-payment discounts, double-entry ERP accounting, FastAPI endpoints, and PostgreSQL schema.
---

# Accounts Payable (AP) Invoice Automation Agent (PS-09)

The AP Invoice Automation Agent automates end-to-end accounts payable processing: from multi-channel invoice intake and document understanding to 3-way matching, duplicate detection, budget checking, sequential approval workflows, payment scheduling, and ERP ledger posting.

---

## 1. System Architecture & Pipeline Workflow

```
[ Invoice Document ] (PDF / Image / Raw Text / Email / Portal)
         │
         ▼
[ Ingestion & OCR ] ─── pdfplumber / pytesseract / LLM Vision Fallback
         │
         ▼
[ Structured Extraction ] ─── Header (Inv#, Vendor, PO#, Date), Lines, Taxes, Totals
         │
         ├─────────────────────────────────────────┐
         ▼                                         ▼
[ Vendor Master Resolution ]             [ Duplicate Detection ]
(Fuzzy name matching >= 80%)             - Exact: Alphanumeric normalized Inv#
         │                               - Suspected: Same Vendor + PO + Total (<= 30d)
         ▼                                         │
[ 3-Way Matching Engine ]                          │
- Invoice vs Purchase Order (PO)                   │
- Invoice vs Goods Receipt Notes (GRN)             │
- Price variance (<= 2% tolerance)                 │
- Cumulative billing vs received qty               │
- Tax rate & line arithmetic                       │
         │                                         │
         ▼                                         ▼
[ Departmental Budget Check ]             [ Status Determination ]
- Uncommitted increment against available   - REJECTED_DUPLICATE (Critical duplicate)
- Near-limit alert (> 90% utilization)      - HOLD_EXCEPTION (Price/Qty/Tax variance)
         │                                  - PENDING_APPROVAL (Passed validation)
         ▼
[ Delegation of Authority (DoA) Approvals ]
- Tier 1 (<= ₹50k): Department Head
- Tier 2 (<= ₹250k): Dept Head + Finance Controller
- Tier 3 (<= ₹1M): Dept Head + Finance Controller + Registrar
- Tier 4 (> ₹1M): Dept Head + Finance Controller + Registrar + Vice Chancellor
(Auto-injects Finance Controller if budget exceeded)
         │
         ▼ (Upon Full Approval)
[ ERP Posting & Payment Scheduling ]
- Double-Entry Ledger: DR Expense, DR Input Tax, CR Accounts Payable
- Release PO commitment, update department actual spend
- Schedule Payment: MSME 45-day cap, early discount capture (e.g. 2% in 10 days)
         │
         ▼
[ Payment Execution ] ─── DR Accounts Payable, CR Bank, CR Purchase Discount
```

---

## 2. Core Modules in `ap_agent/`

| Module | File | Purpose |
|---|---|---|
| **Models** | `ap_agent/models.py` | Dataclasses for `Invoice`, `InvLine`, `PO`, `POLine`, `GRN`, `GRNLine`, `Vendor`, `Budget`, and `Issue`. |
| **Parser** | `ap_agent/parser.py` | Multi-format text extraction (`pdfplumber`, `pytesseract`) + regex line-item parsing and confidence scoring. |
| **Duplicates** | `ap_agent/duplicates.py` | Alphanumeric normalization and exact/suspected duplicate detection. |
| **Matching** | `ap_agent/matching.py` | 3-way matching logic: PO status, vendor match, line item resolution (fuzzy & code), quantity vs GRN receipts, price tolerance (2%), and tax calculation. |
| **Budget** | `ap_agent/budget.py` | Tracks allocated vs actual vs committed budget. Calculates incremental uncommitted liability. |
| **Approval** | `ap_agent/approval.py` | Multi-tier DoA chain generation and sequential role-based approval execution. |
| **Payments** | `ap_agent/payments.py` | Payment terms scheduling, MSME prompt payment enforcement (45-day cap), early payment cash discount optimization, and payment run batches. |
| **ERP** | `ap_agent/erp.py` | Balanced double-entry accounting ledger mock (`MockERP`) with liability queries. |
| **Pipeline** | `ap_agent/pipeline.py` | State store (`Store`), lifecycle transitions, approval posting, commitment release, and payment dispatch. |
| **API** | `ap_agent/api.py` | FastAPI application exposing intake, decision, scheduling, liabilities, and HTML dashboard. |

---

## 3. Validation Rules & Exception Codes

The agent tags issues with severity levels: `CRITICAL`, `MAJOR`, `MINOR`, and `INFO`.

| Code | Severity | Description / Condition |
|---|---|---|
| `DUPLICATE_EXACT` | CRITICAL | Alphanumeric normalized invoice number matches an active invoice for the vendor. |
| `DUPLICATE_SUSPECTED` | CRITICAL | Same vendor, PO number, and amount within ±30 days. |
| `UNKNOWN_VENDOR` | CRITICAL | Vendor name fuzzy match score < 80% against Vendor master. |
| `PO_NOT_FOUND` | CRITICAL | Referenced PO does not exist. |
| `PO_NOT_OPEN` | CRITICAL | PO status is closed or cancelled. |
| `VENDOR_MISMATCH` | CRITICAL | Invoice vendor does not match PO vendor ID. |
| `NO_PO_LINE` | CRITICAL | Item code and description not found on PO lines. |
| `NOT_RECEIVED` | CRITICAL | No Goods Receipt Note (GRN) on file for the item. |
| `QTY_EXCEEDS_RECEIPT` | CRITICAL | Cumulative billed quantity exceeds GRN received quantity. |
| `QTY_EXCEEDS_PO` | CRITICAL | Cumulative billed quantity exceeds PO ordered quantity. |
| `PRICE_VARIANCE` | MAJOR | Billed unit price deviates by > 2% from PO agreed price. |
| `SUBTOTAL_MISMATCH` | MAJOR | Sum of line items does not equal extracted subtotal. |
| `LINE_MATH` | MAJOR | `qty * unit_price != line amount` (variance > 0.01). |
| `TAX_MISMATCH` | MAJOR | Calculated tax deviates from `subtotal * tax_rate` by > ₹1.00. |
| `TOTAL_MISMATCH` | MAJOR | `subtotal + tax != grand total` (variance > ₹1.00). |
| `CURRENCY_MISMATCH` | MAJOR | Currency code differs from PO currency. |
| `LOW_OCR_CONFIDENCE` | MAJOR | OCR extraction confidence < 0.75. Routed to manual review. |
| `BUDGET_EXCEEDED` | MAJOR | Incremental invoice cost exceeds remaining departmental budget. |
| `NO_BUDGET` | CRITICAL | Department has no allocated budget record. |
| `BUDGET_NEAR_LIMIT` | INFO | Department budget utilization exceeds 90% post-invoice. |

---

## 4. Delegation of Authority (DoA) Approval Tiers

Thresholds and sequential roles:
- **≤ ₹50,000**: `["DEPARTMENT_HEAD"]`
- **≤ ₹250,000**: `["DEPARTMENT_HEAD", "FINANCE_CONTROLLER"]`
- **≤ ₹1,000,000**: `["DEPARTMENT_HEAD", "FINANCE_CONTROLLER", "REGISTRAR"]`
- **> ₹1,000,000**: `["DEPARTMENT_HEAD", "FINANCE_CONTROLLER", "REGISTRAR", "VICE_CHANCELLOR"]`

*Budget Exception Rule*: If `BUDGET_EXCEEDED` or `NO_BUDGET` is flagged and total is ≤ ₹50,000, `FINANCE_CONTROLLER` is automatically inserted into the approval chain.

---

## 5. Payment Optimization & Compliance

1. **MSME Compliance (Micro, Small & Medium Enterprises Development Act)**:
   - If `vendor.msme == True` and agreed terms exceed 45 days, the due date is strictly clamped to `invoice_date + 45 days`.
2. **Early Payment Cash Discount**:
   - If vendor offers terms like 2/10 net 30 (`discount_pct: 0.02`, `discount_days: 10`), and today's date is within the discount window:
     - Payment scheduled for `invoice_date + 10 days`.
     - Savings captured: `subtotal * discount_pct`.
     - Net payment amount reduced accordingly.
3. **Payment Run**:
   - `payment_run(schedule, run_date, horizon_days=7)` aggregates due/discounted payments within the window for treasury disbursement.

---

## 6. Double-Entry Accounting Ledger Entries

The agent maintains balanced journal entries:

### On Invoice Approval (`post_invoice`)
```
Debit:   5000-Expense              (Subtotal)
Debit:   1400-Input Tax (GST)       (Tax amount)
Credit:  2000-Accounts Payable     (Total amount)
```

### On Payment Execution (`pay`)
With early payment discount:
```
Debit:   2000-Accounts Payable     (Total invoice amount)
Credit:  1000-Bank                 (Net disbursed amount)
Credit:  4900-Purchase Discount    (Discount earned)
```
Without discount:
```
Debit:   2000-Accounts Payable     (Total amount)
Credit:  1000-Bank                 (Total amount)
```

---

## 7. REST API Reference

| Endpoint | Method | Params / Payload | Description |
|---|---|---|---|
| `/invoices/intake` | `POST` | `text: str` or `file: UploadFile` | Ingests document, parses fields, runs 3-way match & budget check. |
| `/invoices` | `GET` | `status: Optional[str]` | Lists invoices filtered by status (`PENDING_APPROVAL`, `HOLD_EXCEPTION`, `SCHEDULED`, etc.). |
| `/invoices/{id}/decision` | `POST` | `role: str`, `approve_: bool`, `by: str` | Records approval or rejection from authorized role in sequential order. |
| `/payments/schedule` | `GET` | `horizon_days: int` (default 7) | Returns upcoming payment schedule within horizon. |
| `/payments/{id}/execute` | `POST` | - | Posts payment journal to ledger and marks invoice `PAID`. |
| `/liabilities` | `GET` | - | Returns current outstanding Accounts Payable balance. |
| `/budgets` | `GET` | - | Returns department budget allocation, actual, committed, and available. |
| `/` | `GET` | - | Lightweight real-time HTML dashboard. |

---

## 8. Database Schema (Production PostgreSQL)

The prototype uses an in-memory `Store`, with `schema.sql` providing the PostgreSQL DDL:
- `vendors`: Vendor master with MSME status and payment discount terms.
- `purchase_orders` & `po_lines`: PO master and line items.
- `grn` & `grn_lines`: Goods Receipt Notes with received quantities.
- `budgets`: Fiscal year department budget limits and spend counters.
- `invoices` & `invoice_lines`: Parsed invoice data with `UNIQUE(vendor_id, invoice_no_norm)`.
- `invoice_issues`: Line-level and invoice-level exception flags.
- `approvals`: Audit trail of sequential approval actions.
- `payment_schedule`: Scheduled disbursement dates, amounts, and notes.
- `ledger_entries`: Double-entry accounting transaction log.
- `audit_log`: Chronological event and actor tracking.

---

## 9. Running & Testing

### Installation & Server Start
```bash
cd ap_agent
pip install fastapi uvicorn pytest httpx python-multipart pdfplumber pytesseract Pillow
uvicorn ap_agent.api:app --reload --port 8000
```

### Run Demonstration Scenarios
```bash
python demo.py
```

### Execute Test Suite (21 Tests)
```bash
pytest -v tests/test_ap.py
```
