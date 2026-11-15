from decimal import Decimal as D
from .models import Issue

def check_budget(budget, invoice_total, po_outstanding_commitment):
    """Invoices against an existing PO only consume the *uncommitted* increment;
    the PO's own commitment is released as the invoice posts to actuals."""
    if budget is None:
        return [Issue("NO_BUDGET", "CRITICAL", "No budget record for department")]
    increment = max(D(0), invoice_total - po_outstanding_commitment)
    issues = []
    if increment > budget.available:
        issues.append(Issue("BUDGET_EXCEEDED", "MAJOR",
            f"Incremental {increment} exceeds available {budget.available} in {budget.department}"))
    else:
        used_after = (budget.actual + budget.committed - po_outstanding_commitment
                      + invoice_total) / budget.allocated
        if used_after > D("0.90"):
            issues.append(Issue("BUDGET_NEAR_LIMIT", "INFO", f"Utilisation after posting {used_after:.0%}"))
    return issues
