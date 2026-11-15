-- PostgreSQL schema (prototype store is in-memory; this is the production target)
CREATE TABLE vendors(vendor_id text PRIMARY KEY, name text, gstin text, terms_days int, msme bool, discount_pct numeric(5,4), discount_days int);
CREATE TABLE purchase_orders(po_number text PRIMARY KEY, vendor_id text REFERENCES vendors, department text, tax_rate numeric(5,4), currency char(3), status text);
CREATE TABLE po_lines(po_number text REFERENCES purchase_orders, line_no int, item_code text, description text, qty numeric, unit_price numeric, PRIMARY KEY(po_number,line_no));
CREATE TABLE grn(grn_no text PRIMARY KEY, po_number text REFERENCES purchase_orders, received_date date);
CREATE TABLE grn_lines(grn_no text REFERENCES grn, item_code text, qty numeric);
CREATE TABLE budgets(department text, fiscal_year int, allocated numeric, actual numeric, committed numeric, PRIMARY KEY(department,fiscal_year));
CREATE TABLE invoices(id text PRIMARY KEY, vendor_id text, invoice_no text, invoice_no_norm text, invoice_date date, po_number text, subtotal numeric, tax numeric, total numeric, status text, confidence numeric, raw_file text,
  UNIQUE(vendor_id, invoice_no_norm));            -- hard DB-level duplicate guard
CREATE TABLE invoice_lines(invoice_id text REFERENCES invoices, line_no int, item_code text, description text, qty numeric, unit_price numeric, amount numeric);
CREATE TABLE invoice_issues(invoice_id text REFERENCES invoices, code text, severity text, message text, line_no int);
CREATE TABLE approvals(invoice_id text REFERENCES invoices, seq int, role text, status text, acted_by text, acted_at timestamptz);
CREATE TABLE payment_schedule(invoice_id text PRIMARY KEY REFERENCES invoices, pay_on date, due_date date, amount numeric, notes text, paid_at timestamptz);
CREATE TABLE ledger_entries(id bigserial PRIMARY KEY, ref text, kind text, side char(2), account text, amount numeric, posted_at timestamptz DEFAULT now());
CREATE TABLE audit_log(id bigserial PRIMARY KEY, invoice_id text, event text, actor text, at timestamptz DEFAULT now());
