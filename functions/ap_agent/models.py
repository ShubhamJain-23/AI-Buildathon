from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional

D = Decimal

@dataclass
class InvLine:
    line_no: int
    item_code: str
    description: str
    qty: Decimal
    unit_price: Decimal
    amount: Decimal

@dataclass
class Invoice:
    invoice_no: str
    vendor_name: str
    invoice_date: date
    po_number: Optional[str]
    lines: List[InvLine]
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    currency: str = "INR"
    vendor_id: Optional[str] = None
    source: str = "portal"
    confidence: float = 1.0
    id: Optional[str] = None
    status: str = "RECEIVED"
    issues: list = field(default_factory=list)
    approvals: list = field(default_factory=list)

@dataclass
class POLine:
    line_no: int
    item_code: str
    description: str
    qty: Decimal
    unit_price: Decimal

@dataclass
class PO:
    po_number: str
    vendor_id: str
    department: str
    lines: List[POLine]
    tax_rate: Decimal = D("0.18")
    currency: str = "INR"
    status: str = "OPEN"

    @property
    def net_total(self):
        return sum((l.qty * l.unit_price for l in self.lines), D(0))

    @property
    def gross_total(self):
        return (self.net_total * (1 + self.tax_rate)).quantize(D("0.01"))

@dataclass
class GRNLine:
    item_code: str
    qty: Decimal

@dataclass
class GRN:
    grn_no: str
    po_number: str
    received_date: date
    lines: List[GRNLine]

@dataclass
class Vendor:
    vendor_id: str
    name: str
    gstin: str = ""
    terms_days: int = 30
    msme: bool = False
    discount_pct: Decimal = D(0)
    discount_days: int = 0

@dataclass
class Budget:
    department: str
    allocated: Decimal
    actual: Decimal = D(0)
    committed: Decimal = D(0)

    @property
    def available(self):
        return self.allocated - self.actual - self.committed

@dataclass
class Issue:
    code: str
    severity: str  # CRITICAL / MAJOR / MINOR / INFO
    message: str
    line_no: Optional[int] = None
