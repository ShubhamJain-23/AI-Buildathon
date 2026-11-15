from decimal import Decimal as D
from difflib import SequenceMatcher
from .models import Issue

PRICE_TOL_PCT = D("0.02")
TAX_TOL = D("1.00")

def _find_po_line(il, po):
    for pl in po.lines:
        if pl.item_code.upper() == il.item_code.upper():
            return pl
    best, score = None, 0.0
    for pl in po.lines:
        s = SequenceMatcher(None, pl.description.lower(), il.description.lower()).ratio()
        if s > score:
            best, score = pl, s
    return best if score >= 0.85 else None

def three_way_match(inv, po, grns, vendor, prior_invoiced=None):
    """prior_invoiced: {item_code: qty already billed on earlier accepted invoices}."""
    prior = prior_invoiced or {}
    issues = []
    if po is None:
        return [Issue("PO_NOT_FOUND", "CRITICAL", f"PO {inv.po_number} not found")]
    if po.status != "OPEN":
        issues.append(Issue("PO_NOT_OPEN", "CRITICAL", f"PO status is {po.status}"))
    if vendor and po.vendor_id != vendor.vendor_id:
        issues.append(Issue("VENDOR_MISMATCH", "CRITICAL", "Invoice vendor differs from PO vendor"))
    if inv.currency != po.currency:
        issues.append(Issue("CURRENCY_MISMATCH", "MAJOR", f"{inv.currency} vs PO {po.currency}"))

    # arithmetic integrity
    line_sum = sum((l.amount for l in inv.lines), D(0))
    for l in inv.lines:
        if abs(l.qty * l.unit_price - l.amount) > D("0.01"):
            issues.append(Issue("LINE_MATH", "MAJOR", "qty x price != line amount", l.line_no))
    if abs(line_sum - inv.subtotal) > D("0.01"):
        issues.append(Issue("SUBTOTAL_MISMATCH", "MAJOR", f"Lines {line_sum} vs subtotal {inv.subtotal}"))
    if abs(inv.subtotal + inv.tax - inv.total) > TAX_TOL:
        issues.append(Issue("TOTAL_MISMATCH", "MAJOR", "subtotal + tax != total"))
    expected_tax = (inv.subtotal * po.tax_rate)
    if abs(expected_tax - inv.tax) > TAX_TOL:
        issues.append(Issue("TAX_MISMATCH", "MAJOR",
                            f"Tax {inv.tax} vs expected {expected_tax.quantize(D('0.01'))} at {po.tax_rate:.0%}"))

    received = {}
    for g in grns:
        for gl in g.lines:
            received[gl.item_code.upper()] = received.get(gl.item_code.upper(), D(0)) + gl.qty

    billed_now = {}
    for l in inv.lines:
        pl = _find_po_line(l, po)
        if pl is None:
            issues.append(Issue("NO_PO_LINE", "CRITICAL", f"{l.item_code} not on PO", l.line_no))
            continue
        code = pl.item_code.upper()
        # price
        if pl.unit_price and abs(l.unit_price - pl.unit_price) / pl.unit_price > PRICE_TOL_PCT:
            diff = (l.unit_price - pl.unit_price) * l.qty
            issues.append(Issue("PRICE_VARIANCE", "MAJOR",
                                f"Billed {l.unit_price} vs PO {pl.unit_price} (impact {diff:+.2f})", l.line_no))
        # quantity: PO ordered, GRN received, previously billed
        billed_now[code] = billed_now.get(code, D(0)) + l.qty
        total_billed = prior.get(code, D(0)) + billed_now[code]
        rec = received.get(code, D(0))
        if rec == 0:
            issues.append(Issue("NOT_RECEIVED", "CRITICAL", f"No goods receipt for {code}", l.line_no))
        elif total_billed > rec:
            issues.append(Issue("QTY_EXCEEDS_RECEIPT", "CRITICAL",
                                f"Billed cumulative {total_billed} > received {rec}", l.line_no))
        if total_billed > pl.qty:
            issues.append(Issue("QTY_EXCEEDS_PO", "CRITICAL",
                                f"Billed cumulative {total_billed} > ordered {pl.qty}", l.line_no))
    return issues
