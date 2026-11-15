from decimal import Decimal as D

TIERS = [  # (upper limit, approver chain)
    (D("50000"),   ["DEPARTMENT_HEAD"]),
    (D("250000"),  ["DEPARTMENT_HEAD", "FINANCE_CONTROLLER"]),
    (D("1000000"), ["DEPARTMENT_HEAD", "FINANCE_CONTROLLER", "REGISTRAR"]),
    (None,         ["DEPARTMENT_HEAD", "FINANCE_CONTROLLER", "REGISTRAR", "VICE_CHANCELLOR"]),
]

def build_chain(total, budget_exception=False):
    chain = next(c for lim, c in TIERS if lim is None or total <= lim)
    chain = list(chain)
    if budget_exception and "FINANCE_CONTROLLER" not in chain:
        chain.insert(1, "FINANCE_CONTROLLER")
    return [{"role": r, "status": "PENDING", "by": None} for r in chain]

def act(invoice, role, approve=True, by="user"):
    """Sequential approvals; a rejection stops the chain."""
    for step in invoice.approvals:
        if step["status"] == "PENDING":
            if step["role"] != role:
                raise PermissionError(f"Awaiting {step['role']}, not {role}")
            step["status"] = "APPROVED" if approve else "REJECTED"
            step["by"] = by
            break
    else:
        raise ValueError("No pending approval step")
    if not approve:
        invoice.status = "REJECTED"
    elif all(s["status"] == "APPROVED" for s in invoice.approvals):
        invoice.status = "APPROVED"
    return invoice
