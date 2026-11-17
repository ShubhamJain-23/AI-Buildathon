from datetime import timedelta
from decimal import Decimal as D

def schedule_payment(invoice, vendor, today):
    """Due date from terms; MSME cap 45 days; take early-payment discount when still available."""
    terms = vendor.terms_days
    notes = []
    if vendor.msme and terms > 45:
        terms = 45
        notes.append("MSME 45-day cap applied")
    due = invoice.invoice_date + timedelta(days=terms)
    amount = invoice.total
    pay_on = due
    if vendor.discount_pct and vendor.discount_days:
        disc_date = invoice.invoice_date + timedelta(days=vendor.discount_days)
        if today <= disc_date:
            saving = (invoice.subtotal * vendor.discount_pct).quantize(D("0.01"))
            amount = invoice.total - saving
            pay_on = disc_date
            notes.append(f"Early-pay discount {saving} captured")
    return {"invoice_id": invoice.id, "pay_on": pay_on, "due_date": due,
            "amount": amount, "overdue": pay_on < today, "notes": notes}

def payment_run(schedule, run_date, horizon_days=7):
    cutoff = run_date + timedelta(days=horizon_days)
    return [s for s in schedule if s["pay_on"] <= cutoff]
