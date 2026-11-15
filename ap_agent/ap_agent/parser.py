"""Invoice document understanding.
extract_text(): pdfplumber for digital PDFs, pytesseract for scans/images (if installed).
parse_invoice_text(): deterministic regex parser; llm_extract() is the pluggable fallback
for low-confidence documents (Claude vision / API)."""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from .models import Invoice, InvLine

def _num(s):
    try:
        return Decimal(s.replace(",", "").strip())
    except InvalidOperation:
        return None

DATE_FORMATS = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d-%b-%Y"]

def _date(s):
    for f in DATE_FORMATS:
        try:
            return datetime.strptime(s.strip(), f).date()
        except ValueError:
            pass
    return None

def extract_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            if text.strip():
                return text
        except ImportError:
            pass
    try:
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(path))
    except ImportError:
        raise RuntimeError("Install pdfplumber / pytesseract+Pillow for file OCR, or pass text.")

def llm_extract(raw: str):  # hook: call Claude vision/API and return Invoice dict
    raise NotImplementedError("Wire to Claude API for low-confidence documents")

def _find(pattern, text, flags=re.I):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None

LINE_RE = re.compile(
    r"^\s*(\d+)\s+(\S+)\s+(.+?)\s+(\d+(?:\.\d+)?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*$", re.M)

def parse_invoice_text(text: str, source="email") -> Invoice:
    inv_no = _find(r"invoice\s*(?:no|number|#)\.?\s*[:\-]?\s*([A-Za-z0-9][^\n]*?)\s*$", text, re.I | re.M)
    vendor = _find(r"vendor\s*[:\-]\s*(.+)", text)
    po = _find(r"p\.?o\.?\s*(?:no|number|#)?\.?\s*[:\-]?\s*(PO[-A-Za-z0-9]+)", text)
    d = _date(_find(r"(?:invoice\s*)?date\s*[:\-]\s*([0-9A-Za-z/\- ]+)", text) or "")
    lines = [InvLine(int(a), b, c.strip(), _num(q), _num(p), _num(amt))
             for a, b, c, q, p, amt in LINE_RE.findall(text)]
    sub = _num(_find(r"^\s*sub\s*-?total\s*[:\-]?\s*([\d,]+\.\d{2})\s*$", text, re.I | re.M) or "")
    tax = _num(_find(r"^\s*(?:total\s*)?(?:igst|cgst|sgst|gst|vat|tax)[^\n]*?[:\-]\s*([\d,]+\.\d{2})\s*$", text, re.I | re.M) or "")
    tot = _num(_find(r"^\s*(?:grand\s*)?total(?:\s*amount)?\s*[:\-]?\s*([\d,]+\.\d{2})\s*$", text, re.I | re.M) or "")
    # confidence: fraction of mandatory fields found
    found = [inv_no, vendor, po, d, lines or None, sub, tax, tot]
    conf = sum(x is not None for x in found) / len(found)
    z = Decimal(0)
    return Invoice(invoice_no=inv_no or "", vendor_name=vendor or "", invoice_date=d, po_number=po,
                   lines=lines, subtotal=sub or z, tax=tax or z, total=tot or z,
                   source=source, confidence=round(conf, 2))
