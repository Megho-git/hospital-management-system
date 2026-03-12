from datetime import datetime


def compute_totals(subtotal, tax_percent=0.0, discount=0.0):
    subtotal = float(subtotal or 0)
    tax_percent = float(tax_percent or 0)
    discount = float(discount or 0)
    tax_amount = round(subtotal * (tax_percent / 100.0), 2)
    total = round(subtotal + tax_amount - discount, 2)
    return {
        "subtotal": round(subtotal, 2),
        "tax_percent": tax_percent,
        "tax_amount": tax_amount,
        "discount": round(discount, 2),
        "total": total,
    }


def generate_invoice_number(invoice_id):
    # Stable human-friendly format; uniqueness enforced at DB layer.
    return f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{invoice_id:06d}"

