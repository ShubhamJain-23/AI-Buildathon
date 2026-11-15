"""Mock ERP ledger + bank API. Double-entry, always balanced."""
class MockERP:
    def __init__(self):
        self.entries = []
    def post_invoice(self, inv, expense_acct="5000-Expense"):
        e = [("DR", expense_acct, inv.subtotal), ("DR", "1400-Input Tax", inv.tax),
             ("CR", "2000-Accounts Payable", inv.total)]
        self._post(inv.id, "INVOICE", e); return e
    def pay(self, inv_id, amount, discount=0):
        e = [("DR", "2000-Accounts Payable", amount + discount), ("CR", "1000-Bank", amount)]
        if discount:
            e.append(("CR", "4900-Purchase Discount", discount))
        self._post(inv_id, "PAYMENT", e); return e
    def _post(self, ref, kind, e):
        dr = sum(a for s, _, a in e if s == "DR"); cr = sum(a for s, _, a in e if s == "CR")
        assert dr == cr, f"Unbalanced entry {dr} != {cr}"
        self.entries.append({"ref": ref, "kind": kind, "lines": e})
    def liability(self):
        bal = 0
        for en in self.entries:
            for s, a, amt in en["lines"]:
                if a.startswith("2000"):
                    bal += amt if s == "CR" else -amt
        return bal
