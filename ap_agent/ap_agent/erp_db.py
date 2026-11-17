"""SQLite Enterprise University ERP Database Layer.
Provides persistent storage, querying, and double-entry ledger bookkeeping.
"""
import sqlite3
import os
from decimal import Decimal as D
from datetime import date, datetime
from typing import Dict, List, Optional, Any

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "erp_system.db")
DB_PATH = os.environ.get("ERP_DB_PATH")

def _resolve_db_path() -> str:
    global DB_PATH
    if DB_PATH:
        return DB_PATH
    # In serverless environments (Cloud Functions, Lambda), use /tmp if local dir is read-only
    target_dir = os.path.dirname(__file__)
    if not os.access(target_dir, os.W_OK) or os.environ.get("K_SERVICE") or os.environ.get("FUNCTION_TARGET"):
        import tempfile, shutil
        tmp_db = os.path.join(tempfile.gettempdir(), "erp_system.db")
        if not os.path.exists(tmp_db) and os.path.exists(DEFAULT_DB_PATH):
            shutil.copy2(DEFAULT_DB_PATH, tmp_db)
        DB_PATH = tmp_db
    else:
        DB_PATH = DEFAULT_DB_PATH
    return DB_PATH

def get_connection():
    conn = sqlite3.connect(_resolve_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def reset_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
    DROP TABLE IF EXISTS proposal_approvals;
    DROP TABLE IF EXISTS quotation_items;
    DROP TABLE IF EXISTS quotations;
    DROP TABLE IF EXISTS procurement_proposals;
    DROP TABLE IF EXISTS audit_logs;
    DROP TABLE IF EXISTS ledger_entries;
    DROP TABLE IF EXISTS payment_schedule;
    DROP TABLE IF EXISTS approvals;
    DROP TABLE IF EXISTS invoice_issues;
    DROP TABLE IF EXISTS invoice_lines;
    DROP TABLE IF EXISTS invoices;
    DROP TABLE IF EXISTS grn_lines;
    DROP TABLE IF EXISTS grn;
    DROP TABLE IF EXISTS po_lines;
    DROP TABLE IF EXISTS purchase_orders;
    DROP TABLE IF EXISTS budgets;
    DROP TABLE IF EXISTS vendors;
    """)
    conn.commit()
    conn.close()
    init_db(seed_data=True)

def init_db(seed_data=True):
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS vendors (
        vendor_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        gstin TEXT,
        terms_days INTEGER DEFAULT 30,
        msme BOOLEAN DEFAULT 0,
        discount_pct REAL DEFAULT 0.0,
        discount_days INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS purchase_orders (
        po_number TEXT PRIMARY KEY,
        vendor_id TEXT NOT NULL,
        department TEXT NOT NULL,
        tax_rate REAL DEFAULT 0.18,
        currency TEXT DEFAULT 'INR',
        status TEXT DEFAULT 'OPEN',
        created_date TEXT,
        FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
    );

    CREATE TABLE IF NOT EXISTS po_lines (
        po_number TEXT NOT NULL,
        line_no INTEGER NOT NULL,
        item_code TEXT NOT NULL,
        description TEXT NOT NULL,
        qty REAL NOT NULL,
        unit_price REAL NOT NULL,
        PRIMARY KEY (po_number, line_no),
        FOREIGN KEY (po_number) REFERENCES purchase_orders(po_number)
    );

    CREATE TABLE IF NOT EXISTS grn (
        grn_no TEXT PRIMARY KEY,
        po_number TEXT NOT NULL,
        received_date TEXT NOT NULL,
        received_by TEXT,
        remarks TEXT,
        FOREIGN KEY (po_number) REFERENCES purchase_orders(po_number)
    );

    CREATE TABLE IF NOT EXISTS grn_lines (
        grn_no TEXT NOT NULL,
        item_code TEXT NOT NULL,
        qty REAL NOT NULL,
        PRIMARY KEY (grn_no, item_code),
        FOREIGN KEY (grn_no) REFERENCES grn(grn_no)
    );

    CREATE TABLE IF NOT EXISTS budgets (
        department TEXT PRIMARY KEY,
        allocated REAL NOT NULL,
        actual REAL DEFAULT 0.0,
        committed REAL DEFAULT 0.0,
        fiscal_year INTEGER DEFAULT 2026
    );

    CREATE TABLE IF NOT EXISTS invoices (
        id TEXT PRIMARY KEY,
        vendor_id TEXT,
        vendor_name TEXT,
        invoice_no TEXT NOT NULL,
        invoice_no_norm TEXT NOT NULL,
        invoice_date TEXT NOT NULL,
        po_number TEXT,
        subtotal REAL NOT NULL,
        tax REAL NOT NULL,
        total REAL NOT NULL,
        currency TEXT DEFAULT 'INR',
        status TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        source TEXT DEFAULT 'portal',
        maker_summary TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (vendor_id, invoice_no_norm)
    );

    CREATE TABLE IF NOT EXISTS invoice_lines (
        invoice_id TEXT NOT NULL,
        line_no INTEGER NOT NULL,
        item_code TEXT,
        description TEXT,
        qty REAL NOT NULL,
        unit_price REAL NOT NULL,
        amount REAL NOT NULL,
        PRIMARY KEY (invoice_id, line_no),
        FOREIGN KEY (invoice_id) REFERENCES invoices(id)
    );

    CREATE TABLE IF NOT EXISTS invoice_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id TEXT NOT NULL,
        code TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        line_no INTEGER,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id)
    );

    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id TEXT NOT NULL,
        seq INTEGER NOT NULL,
        role TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        acted_by TEXT,
        acted_at TEXT,
        comments TEXT,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id)
    );

    CREATE TABLE IF NOT EXISTS payment_schedule (
        invoice_id TEXT PRIMARY KEY,
        pay_on TEXT NOT NULL,
        due_date TEXT NOT NULL,
        amount REAL NOT NULL,
        discount_captured REAL DEFAULT 0.0,
        msme_capped BOOLEAN DEFAULT 0,
        status TEXT DEFAULT 'SCHEDULED',
        notes TEXT,
        paid_at TEXT,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id)
    );

    CREATE TABLE IF NOT EXISTS ledger_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref TEXT NOT NULL,
        kind TEXT NOT NULL,
        side TEXT NOT NULL CHECK(side IN ('DR', 'CR')),
        account TEXT NOT NULL,
        amount REAL NOT NULL,
        posted_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id TEXT,
        stage TEXT NOT NULL,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS procurement_proposals (
        id TEXT PRIMARY KEY,
        department TEXT NOT NULL,
        title TEXT NOT NULL,
        item_description TEXT,
        estimated_cost REAL NOT NULL,
        status TEXT DEFAULT 'PENDING_HOD',
        recommended_quotation_id TEXT,
        created_by TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        po_number TEXT
    );

    CREATE TABLE IF NOT EXISTS quotations (
        id TEXT PRIMARY KEY,
        proposal_id TEXT NOT NULL,
        vendor_name TEXT NOT NULL,
        vendor_id TEXT,
        is_existing_vendor BOOLEAN DEFAULT 0,
        subtotal REAL NOT NULL,
        tax REAL NOT NULL,
        total_amount REAL NOT NULL,
        delivery_days INTEGER DEFAULT 14,
        warranty_months INTEGER DEFAULT 12,
        after_sales_service TEXT,
        payment_terms TEXT,
        score_price REAL DEFAULT 0.0,
        score_delivery REAL DEFAULT 0.0,
        score_warranty REAL DEFAULT 0.0,
        score_service REAL DEFAULT 0.0,
        total_score REAL DEFAULT 0.0,
        recommendation_badge TEXT,
        raw_text TEXT,
        FOREIGN KEY (proposal_id) REFERENCES procurement_proposals(id)
    );

    CREATE TABLE IF NOT EXISTS quotation_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quotation_id TEXT NOT NULL,
        item_name TEXT NOT NULL,
        qty REAL NOT NULL,
        unit_price REAL NOT NULL,
        total_price REAL NOT NULL,
        market_benchmark_price REAL,
        market_variance_pct REAL,
        FOREIGN KEY (quotation_id) REFERENCES quotations(id)
    );

    CREATE TABLE IF NOT EXISTS proposal_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proposal_id TEXT NOT NULL,
        seq INTEGER NOT NULL,
        role TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        acted_by TEXT,
        acted_at TEXT,
        comments TEXT,
        FOREIGN KEY (proposal_id) REFERENCES procurement_proposals(id)
    );
    """)
    conn.commit()

    if seed_data:
        c.execute("SELECT COUNT(*) as c FROM vendors")
        if c.fetchone()["c"] == 0:
            seed_initial_data(conn)
    conn.close()

def seed_initial_data(conn):
    c = conn.cursor()
    # Vendors
    c.executemany("""
    INSERT INTO vendors (vendor_id, name, gstin, terms_days, msme, discount_pct, discount_days)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ("V001", "Sharma Lab Supplies Pvt Ltd", "08ABCDE1234F1Z5", 30, 1, 0.02, 10),
        ("V002", "CampusTech Services LLP", "08PQRST5678G1Z2", 45, 0, 0.0, 0),
        ("V003", "National Scientific Instruments Co", "07AAACN1234Q1Z8", 60, 1, 0.015, 15),
        ("V004", "Dell India Enterprise Solutions", "29AABBD1234H1Z1", 30, 0, 0.0, 0),
        ("V005", "Lenovo Commercial Tech Pvt Ltd", "06AABCL5678J1Z3", 30, 0, 0.0, 0),
        ("V006", "MicroTech Systems & Peripherals", "08XYZAB9876K1Z9", 15, 1, 0.02, 7),
        ("V007", "Modern University Press & Printers", "08LMNOP4321P1Z4", 30, 1, 0.03, 10),
    ])

    # Budgets for All 12 University Departments (plus test aliases)
    c.executemany("""
    INSERT INTO budgets (department, allocated, actual, committed, fiscal_year)
    VALUES (?, ?, ?, ?, ?)
    """, [
        ("IET", 5000000.0, 1200000.0, 800000.0, 2026),     # 1. Institute of Engineering and Technology
        ("IM", 3500000.0, 800000.0, 400000.0, 2026),       # 2. Institute of Management
        ("ID", 2500000.0, 500000.0, 300000.0, 2026),       # 3. Institute of Design
        ("ADMIN", 4000000.0, 1500000.0, 500000.0, 2026),   # 4. Administration
        ("HOSTEL", 3500000.0, 1000000.0, 600000.0, 2026),  # 5. Hostels
        ("MDC", 2000000.0, 400000.0, 200000.0, 2026),      # 6. MDC
        ("SEC", 1500000.0, 300000.0, 150000.0, 2026),      # 7. Security
        ("MKT", 2500000.0, 600000.0, 400000.0, 2026),      # 8. Marketing
        ("ADM", 3000000.0, 800000.0, 500000.0, 2026),      # 9. Admissions and Outreach
        ("HR", 1500000.0, 250000.0, 100000.0, 2026),       # 10. HR
        ("ACC", 1200000.0, 200000.0, 100000.0, 2026),      # 11. Accounts
        ("CHEM", 200000.0, 20000.0, 50740.0, 2026),
        ("IT", 500000.0, 50000.0, 472000.0, 2026),
        ("BIO", 350000.0, 120000.0, 80000.0, 2026),
    ])

    # Purchase Orders
    c.execute("""
    INSERT INTO purchase_orders (po_number, vendor_id, department, tax_rate, currency, status, created_date)
    VALUES ('PO-1001', 'V001', 'CHEM', 0.18, 'INR', 'OPEN', '2026-10-15')
    """)
    c.executemany("""
    INSERT INTO po_lines (po_number, line_no, item_code, description, qty, unit_price)
    VALUES (?, ?, ?, ?, ?, ?)
    """, [
        ("PO-1001", 1, "LAB-REAG-01", "Reagent kit", 100.0, 450.0),
        ("PO-1001", 2, "LAB-GLOVE-02", "Nitrile gloves box", 50.0, 200.0),
    ])

    c.execute("""
    INSERT INTO purchase_orders (po_number, vendor_id, department, tax_rate, currency, status, created_date)
    VALUES ('PO-1002', 'V002', 'IT', 0.18, 'INR', 'OPEN', '2026-10-20')
    """)
    c.execute("""
    INSERT INTO po_lines (po_number, line_no, item_code, description, qty, unit_price)
    VALUES ('PO-1002', 1, 'AMC-SRV-01', 'Server AMC annual', 1.0, 400000.0)
    """)

    # Goods Receipts (GRN)
    c.execute("""
    INSERT INTO grn (grn_no, po_number, received_date, received_by, remarks)
    VALUES ('GRN-101', 'PO-1001', '2026-11-05', 'Stores Bay 3', 'Initial batch received in good condition')
    """)
    c.executemany("""
    INSERT INTO grn_lines (grn_no, item_code, qty)
    VALUES (?, ?, ?)
    """, [
        ("GRN-101", "LAB-REAG-01", 60.0),
        ("GRN-101", "LAB-GLOVE-02", 50.0),
    ])

    c.execute("""
    INSERT INTO grn (grn_no, po_number, received_date, received_by, remarks)
    VALUES ('GRN-102', 'PO-1002', '2026-11-01', 'Data Center Admin', 'Server maintenance contract active')
    """)
    c.execute("""
    INSERT INTO grn_lines (grn_no, item_code, qty)
    VALUES ('GRN-102', 'AMC-SRV-01', 1.0)
    """)

    conn.commit()

# --- Helper Query Functions for ERP MCP Server ---

def get_vendor(vendor_id: str = None, name: str = None):
    conn = get_connection()
    c = conn.cursor()
    if vendor_id:
        c.execute("SELECT * FROM vendors WHERE vendor_id = ?", (vendor_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    elif name:
        c.execute("SELECT * FROM vendors")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        from difflib import SequenceMatcher
        best, best_score = None, 0.0
        for r in rows:
            score = SequenceMatcher(None, r["name"].lower(), name.lower()).ratio()
            if score > best_score:
                best, best_score = r, score
        return best if best_score >= 0.75 else None
    conn.close()
    return None

def lookup_po(po_number: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT po.*, v.name as vendor_name, v.terms_days, v.msme, v.discount_pct, v.discount_days
    FROM purchase_orders po
    JOIN vendors v ON po.vendor_id = v.vendor_id
    WHERE po.po_number = ?
    """, (po_number,))
    po = c.fetchone()
    if not po:
        conn.close()
        return None
    po_dict = dict(po)
    c.execute("SELECT * FROM po_lines WHERE po_number = ? ORDER BY line_no", (po_number,))
    po_dict["lines"] = [dict(r) for r in c.fetchall()]
    conn.close()
    return po_dict

def get_grns_for_po(po_number: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM grn WHERE po_number = ?", (po_number,))
    grns = [dict(r) for r in c.fetchall()]
    for g in grns:
        c.execute("SELECT * FROM grn_lines WHERE grn_no = ?", (g["grn_no"],))
        g["lines"] = [dict(r) for r in c.fetchall()]
    conn.close()
    return grns

def get_department_budget(department: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM budgets WHERE department = ?", (department,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["available"] = round(d["allocated"] - d["actual"] - d["committed"], 2)
    return d

def get_cumulative_invoiced(po_number: str, exclude_invoice_id: str = None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT il.item_code, SUM(il.qty) as billed_qty, SUM(il.amount) as billed_amt
    FROM invoice_lines il
    JOIN invoices inv ON il.invoice_id = inv.id
    WHERE inv.po_number = ? AND inv.status IN ('PENDING_APPROVAL', 'APPROVED', 'SCHEDULED', 'PAID')
      AND (inv.id != ? OR ? IS NULL)
    GROUP BY il.item_code
    """, (po_number, exclude_invoice_id or "", exclude_invoice_id))
    billed = {r["item_code"].upper(): dict(r) for r in c.fetchall()}
    conn.close()
    return billed

def check_duplicate(vendor_id: str, invoice_no: str, total: float, po_number: str, invoice_date: str):
    import re
    norm_no = re.sub(r"[^A-Z0-9]", "", (invoice_no or "").upper()).lstrip("0")
    conn = get_connection()
    c = conn.cursor()
    
    # Exact duplicate check (same vendor + normalized invoice no)
    c.execute("""
    SELECT id, invoice_no, total, status, invoice_date FROM invoices 
    WHERE vendor_id = ? AND invoice_no_norm = ? AND status != 'REJECTED_DUPLICATE'
    """, (vendor_id, norm_no))
    exact = c.fetchone()
    if exact:
        conn.close()
        return {"is_duplicate": True, "type": "EXACT", "matched_invoice": dict(exact),
                "reason": f"Exact match with prior invoice {exact['id']} ({exact['invoice_no']})"}

    # Suspected duplicate check (same vendor, PO, and total within 30 days)
    c.execute("""
    SELECT id, invoice_no, total, status, invoice_date FROM invoices
    WHERE vendor_id = ? AND po_number = ? AND ABS(total - ?) < 0.05 AND status != 'REJECTED_DUPLICATE'
    """, (vendor_id, po_number, total))
    candidates = [dict(r) for r in c.fetchall()]
    conn.close()

    if candidates and invoice_date:
        inv_dt = datetime.strptime(invoice_date, "%Y-%m-%d").date()
        for cand in candidates:
            try:
                cand_dt = datetime.strptime(cand["invoice_date"], "%Y-%m-%d").date()
                if abs((inv_dt - cand_dt).days) <= 30:
                    return {"is_duplicate": True, "type": "SUSPECTED", "matched_invoice": cand,
                            "reason": f"Suspected duplicate: same vendor, PO {po_number}, and amount {total} within 30 days of {cand['id']}"}
            except Exception:
                pass
    return {"is_duplicate": False}

def post_erp_liability(invoice_id: str, subtotal: float, tax: float, total: float, expense_account: str = "5000-Departmental-Expense"):
    conn = get_connection()
    c = conn.cursor()
    entries = [
        (invoice_id, "INVOICE", "DR", expense_account, subtotal),
        (invoice_id, "INVOICE", "DR", "1400-Input-Tax-GST", tax),
        (invoice_id, "INVOICE", "CR", "2000-Accounts-Payable", total),
    ]
    c.executemany("""
    INSERT INTO ledger_entries (ref, kind, side, account, amount)
    VALUES (?, ?, ?, ?, ?)
    """, entries)
    conn.commit()
    conn.close()
    return entries

def post_erp_payment(invoice_id: str, amount_paid: float, discount: float = 0.0):
    conn = get_connection()
    c = conn.cursor()
    entries = [
        (invoice_id, "PAYMENT", "DR", "2000-Accounts-Payable", amount_paid + discount),
        (invoice_id, "PAYMENT", "CR", "1000-University-Treasury-Bank", amount_paid),
    ]
    if discount > 0:
        entries.append((invoice_id, "PAYMENT", "CR", "4900-Purchase-Cash-Discount-Earned", discount))
    c.executemany("""
    INSERT INTO ledger_entries (ref, kind, side, account, amount)
    VALUES (?, ?, ?, ?, ?)
    """, entries)
    c.execute("UPDATE payment_schedule SET status = 'PAID', paid_at = CURRENT_TIMESTAMP WHERE invoice_id = ?", (invoice_id,))
    c.execute("UPDATE invoices SET status = 'PAID' WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()
    return entries

def get_ledger_balance():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT account,
           SUM(CASE WHEN side = 'DR' THEN amount ELSE 0 END) as total_dr,
           SUM(CASE WHEN side = 'CR' THEN amount ELSE 0 END) as total_cr
    FROM ledger_entries
    GROUP BY account
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    summary = {}
    for r in rows:
        if r["account"].startswith("2000"):
            summary["ap_liability"] = round(r["total_cr"] - r["total_dr"], 2)
        elif r["account"].startswith("1000"):
            summary["bank_outflow"] = round(r["total_cr"] - r["total_dr"], 2)
        elif r["account"].startswith("4900"):
            summary["discounts_captured"] = round(r["total_cr"], 2)
    summary["entries_count"] = len(rows)
    return summary

UNIVERSITY_DEPARTMENTS_META = [
    {"code": "IET", "name": "Institute of Engineering and Technology (IET)", "hod": "Dr. Tapas Kumar (Dean, IET) & Dr. Umesh Gupta (Dean Academic Affairs)"},
    {"code": "IM", "name": "Institute of Management (IM)", "hod": "Dr. Sheetal Mundra (Acting Head, Institute of Management)"},
    {"code": "ID", "name": "Institute of Design (ID)", "hod": "Prof. Rattan Gangadhar (Dean, Institute of Design)"},
    {"code": "ADMIN", "name": "Administration", "hod": "Mr. Sonjay Dahiya (DGM, Administration) / CA K.K. Maheshwari (Registrar)"},
    {"code": "HOSTEL", "name": "Hostels & Student Housing", "hod": "Dr. Devika Kataria (Chief Warden, Hostels)"},
    {"code": "SEC", "name": "Security & Vigilance", "hod": "Mr. Varun Rathi (Senior Security Officer & Member Secretary)"},
    {"code": "MKT", "name": "Marketing & Brand Outreach", "hod": "Mr. Somesh Bang (Head, Brand & Marketing Outreach)"},
    {"code": "ADM", "name": "Admissions and Outreach", "hod": "Mr. Aseem Bhatnagar (Head, Admissions and Outreach)"},
    {"code": "HR", "name": "Human Resources (HR)", "hod": "Ms. Rashmi Chaudhary (Head HR)"},
    {"code": "ACC", "name": "Finance & Accounts Division", "hod": "CA. Arvind Kumar (DGM, Finance & Accounts) / CA K.K. Maheshwari (CFO)"},
    {"code": "IT", "name": "Information Technology Infrastructure", "hod": "Mr. Vikrant Sharma"},
]

def get_all_departments():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM budgets")
    budgets = {r["department"]: dict(r) for r in c.fetchall()}
    conn.close()

    result = []
    for d in UNIVERSITY_DEPARTMENTS_META:
        b = budgets.get(d["code"], {})
        alloc = b.get("allocated", 0.0)
        actual = b.get("actual", 0.0)
        comm = b.get("committed", 0.0)
        avail = round(alloc - actual - comm, 2)
        result.append({
            **d,
            "allocated": alloc,
            "actual": actual,
            "committed": comm,
            "available": avail
        })
    return result

def save_proposal(proposal_data: Dict[str, Any]):
    """Persists a new HoD proposal with scrutinized quotations and approval chain."""
    import uuid
    prop_id = f"PROP-{uuid.uuid4().hex[:8].upper()}"
    conn = get_connection()
    c = conn.cursor()

    rec_amount = proposal_data.get("recommended_amount", 0.0)
    dept = proposal_data.get("department", "IET")

    c.execute("""
    INSERT INTO procurement_proposals (id, department, title, item_description, estimated_cost, status, created_by)
    VALUES (?, ?, ?, ?, ?, 'PENDING_HOD', ?)
    """, (
        prop_id,
        dept,
        proposal_data.get("title", "Procurement Proposal"),
        proposal_data.get("title", ""),
        rec_amount,
        f"HoD ({dept})"
    ))

    # Insert quotations
    best_quote_id = None
    for idx, q in enumerate(proposal_data.get("quotations", [])):
        q_id = f"Q-{prop_id}-{idx+1}"
        if q.get("recommendation_tag") == "RECOMMENDED_BEST_VALUE":
            best_quote_id = q_id

        c.execute("""
        INSERT INTO quotations 
        (id, proposal_id, vendor_name, vendor_id, is_existing_vendor, subtotal, tax, total_amount,
         delivery_days, warranty_months, after_sales_service, payment_terms,
         score_price, score_delivery, score_warranty, score_service, total_score, recommendation_badge, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            q_id, prop_id, q.get("vendor_name"), q.get("vendor_id"),
            1 if q.get("is_existing_vendor") else 0,
            q.get("subtotal", 0.0), q.get("tax", 0.0), q.get("total_amount", 0.0),
            q.get("delivery_days", 14), q.get("warranty_months", 12),
            q.get("after_sales_service", "Standard Support"), q.get("payment_terms", "30 Days Net"),
            q.get("score_price", 0.0), q.get("score_delivery", 0.0),
            q.get("score_warranty", 0.0), q.get("score_service", 0.0),
            q.get("total_score", 0.0), q.get("badge_text", ""), q.get("raw_text", "")
        ))

        # Insert quotation line items
        for it in q.get("items", []):
            c.execute("""
            INSERT INTO quotation_items 
            (quotation_id, item_name, qty, unit_price, total_price, market_benchmark_price, market_variance_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                q_id, it.get("item_name", "Item"), it.get("qty", 1.0),
                it.get("unit_price", 0.0), it.get("total_price", 0.0),
                it.get("market_benchmark_price", 0.0), it.get("market_variance_pct", 0.0)
            ))

    if best_quote_id:
        c.execute("UPDATE procurement_proposals SET recommended_quotation_id = ? WHERE id = ?", (best_quote_id, prop_id))

    # University Institutional Workflow Rule:
    # Expenses > 20,000 follow: HoD -> Purchase Officer -> Accounts -> CFO
    chain = ["HOD", "PURCHASE_OFFICER", "ACCOUNTS", "CFO"] if rec_amount > 20000 else ["HOD", "PURCHASE_OFFICER"]
    for s_idx, role in enumerate(chain):
        c.execute("""
        INSERT INTO proposal_approvals (proposal_id, seq, role, status)
        VALUES (?, ?, ?, 'PENDING')
        """, (prop_id, s_idx + 1, role))

    conn.commit()
    conn.close()
    return prop_id

def get_proposals_list():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT p.*, q.vendor_name as recommended_vendor, q.recommendation_badge
    FROM procurement_proposals p
    LEFT JOIN quotations q ON p.recommended_quotation_id = q.id
    ORDER BY p.created_at DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_proposal_full(proposal_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT p.*, q.vendor_name as recommended_vendor, q.total_amount as recommended_amount
    FROM procurement_proposals p
    LEFT JOIN quotations q ON p.recommended_quotation_id = q.id
    WHERE p.id = ?
    """, (proposal_id,))
    p = c.fetchone()
    if not p:
        conn.close()
        return None
    p_dict = dict(p)

    c.execute("SELECT * FROM quotations WHERE proposal_id = ? ORDER BY total_score DESC", (proposal_id,))
    quotes = [dict(r) for r in c.fetchall()]
    market_comparisons = []
    for q in quotes:
        c.execute("SELECT * FROM quotation_items WHERE quotation_id = ?", (q["id"],))
        items = [dict(r) for r in c.fetchall()]
        q["items"] = items
        for it in items:
            market_comparisons.append({
                "item_name": it["item_name"],
                "unit_price": it["unit_price"],
                "benchmark_price": it["market_benchmark_price"],
                "variance_pct": it["market_variance_pct"],
                "source": "GeM Portal & Amazon B2B"
            })
    p_dict["quotations"] = quotes
    p_dict["market_comparisons"] = market_comparisons

    c.execute("SELECT * FROM proposal_approvals WHERE proposal_id = ? ORDER BY seq ASC", (proposal_id,))
    p_dict["approvals"] = [dict(r) for r in c.fetchall()]

    b = get_department_budget(p_dict["department"])
    p_dict["department_budget"] = b

    conn.close()
    return p_dict

def act_proposal(proposal_id: str, role: str, approve: bool, acted_by: str = "officer", comments: str = None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM proposal_approvals WHERE proposal_id = ? ORDER BY seq ASC", (proposal_id,))
    steps = [dict(r) for r in c.fetchall()]
    if not steps:
        conn.close()
        raise ValueError("No active approval chain for this proposal.")

    pending_step = next((s for s in steps if s["status"] == "PENDING"), None)
    if not pending_step:
        conn.close()
        raise ValueError("Proposal is already finalized.")

    if pending_step["role"] != role:
        conn.close()
        raise PermissionError(f"Sequence mismatch: Awaiting approval from '{pending_step['role']}', not '{role}'.")

    new_st = "APPROVED" if approve else "REJECTED"
    c.execute("""
    UPDATE proposal_approvals
    SET status = ?, acted_by = ?, acted_at = CURRENT_TIMESTAMP, comments = ?
    WHERE id = ?
    """, (new_st, acted_by, comments or f"Approved by {role}", pending_step["id"]))

    if not approve:
        c.execute("UPDATE procurement_proposals SET status = 'REJECTED' WHERE id = ?", (proposal_id,))
        conn.commit()
        conn.close()
        return {"status": "REJECTED", "message": f"Proposal rejected by {role}."}

    c.execute("SELECT COUNT(*) as c FROM proposal_approvals WHERE proposal_id = ? AND status = 'PENDING'", (proposal_id,))
    rem = c.fetchone()["c"]

    if rem == 0:
        # Full institutional approval completed! (HoD -> Purchase -> Accounts -> CFO)
        # 1. Encumber department budget
        c.execute("SELECT * FROM procurement_proposals WHERE id = ?", (proposal_id,))
        p = dict(c.fetchone())
        c.execute("""
        UPDATE budgets 
        SET committed = committed + ?
        WHERE department = ?
        """, (p["estimated_cost"], p["department"]))

        # 2. Generate official University Purchase Order (PO)
        import uuid
        po_no = f"PO-{p['department']}-2026-{uuid.uuid4().hex[:4].upper()}"
        c.execute("SELECT * FROM quotations WHERE id = ?", (p["recommended_quotation_id"],))
        rec_q = c.fetchone()
        v_id = rec_q["vendor_id"] if rec_q and rec_q["vendor_id"] else "V001"

        c.execute("""
        INSERT INTO purchase_orders (po_number, vendor_id, department, tax_rate, currency, status, created_date)
        VALUES (?, ?, ?, 0.18, 'INR', 'OPEN', CURRENT_DATE)
        """, (po_no, v_id, p["department"]))

        c.execute("UPDATE procurement_proposals SET status = 'PO_ISSUED', po_number = ? WHERE id = ?", (po_no, proposal_id))
        conn.commit()
        conn.close()
        return {
            "status": "PO_ISSUED",
            "po_number": po_no,
            "message": f"Final approval by CFO granted! Encumbered ₹{p['estimated_cost']:,.2f} on {p['department']} budget and generated Purchase Order {po_no}."
        }

    c.execute("UPDATE procurement_proposals SET status = ? WHERE id = ?", (f"PENDING_{steps[pending_step['seq']]['role']}", proposal_id))
    conn.commit()
    conn.close()
    return {
        "status": "IN_PROGRESS",
        "message": f"Signed off by {role}. Forwarded to next checkpoint."
    }

