"""Arabic-capable invoice PDF generation (Wave-style layout).

Uses reportlab + arabic_reshaper + python-bidi with the bundled Amiri font so
Arabic item names and the "Omar مختار" header render correctly (shaped + RTL).
"""
import io
import os
from datetime import datetime

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

_FONT_DIR = os.path.join(os.path.dirname(__file__), "pdf_assets", "fonts")
_REGISTERED = False
COMPANY_NAME = "Omar مختار"


def _ensure_fonts() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    pdfmetrics.registerFont(TTFont("Amiri", os.path.join(_FONT_DIR, "Amiri-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Amiri-Bold", os.path.join(_FONT_DIR, "Amiri-Bold.ttf")))
    _REGISTERED = True


def ar(s) -> str:
    """Shape Arabic + apply bidi so mixed AR/Latin text renders correctly.

    base_dir='L' keeps an LTR layout (Latin-first), so "Omar مختار" stays in
    that order while the Arabic word is still shaped right-to-left internally.
    """
    return get_display(arabic_reshaper.reshape(str(s if s is not None else "")),
                       base_dir="L")


def money(cents) -> str:
    return f"EGP {(cents or 0) / 100:,.2f}"


def _fmt_date(d) -> str:
    if not d:
        d = datetime.utcnow().strftime("%Y-%m-%d")
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%B %d, %Y")
    except ValueError:
        return str(d)


def build_invoice_pdf(inv: dict) -> bytes:
    _ensure_fonts()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    L, R = 50, W - 50
    F, FB = "Amiri", "Amiri-Bold"

    def right(x, y, text, font=F, size=10, color=(0, 0, 0)):
        c.setFont(font, size); c.setFillColorRGB(*color)
        c.drawRightString(x, y, ar(text))

    def left(x, y, text, font=F, size=10, color=(0, 0, 0)):
        c.setFont(font, size); c.setFillColorRGB(*color)
        c.drawString(x, y, ar(text))

    # --- Header (company name top-right; no big "INVOICE" word) ----------
    right(R, H - 70, COMPANY_NAME, FB, 20)
    c.setStrokeColorRGB(0.85, 0.85, 0.85); c.setLineWidth(1)
    c.line(L, H - 95, R, H - 95)

    # --- Bill to (left) + meta (right) -----------------------------------
    y = H - 125
    left(L, y, "BILL TO", F, 9, (0.5, 0.5, 0.5))
    left(L, y - 16, inv.get("customer_name") or "-", FB, 12)

    paid = inv.get("paid_cents") or 0
    due = (inv.get("total_cents") or 0) - paid
    meta = [
        ("Invoice Number:", str(inv.get("invoice_no") or inv.get("id") or "")),
        ("Invoice Date:", _fmt_date(inv.get("invoice_date"))),
        ("Amount Due (EGP):", money(due)),
    ]
    my = y
    for label, val in meta:
        right(R - 120, my, label, FB, 10)
        right(R, my, val, F, 10)
        my -= 18

    # --- Items table -----------------------------------------------------
    ty = y - 70
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.rect(L, ty - 6, R - L, 22, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    QTY_X, PRICE_X, AMT_X = L + 295, L + 380, R - 4
    left(L + 8, ty, "Items", FB, 10)
    right(QTY_X, ty, "Quantity", FB, 10)
    right(PRICE_X, ty, "Price", FB, 10)
    right(AMT_X, ty, "Amount", FB, 10)

    ry = ty - 28
    for ln in (inv.get("lines") or []):
        left(L + 8, ry, ln.get("description") or "-", FB, 10)
        right(QTY_X, ry, str(ln.get("qty") or 0), F, 10)
        right(PRICE_X, ry, money(ln.get("unit_price_cents")), F, 10)
        right(AMT_X, ry, money(ln.get("line_total_cents")), F, 10)
        ry -= 26
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(L, ry + 8, R, ry + 8)

    # --- Totals ----------------------------------------------------------
    sy = ry - 10
    rows = [("Subtotal:", money(inv.get("subtotal_cents")), False)]
    if (inv.get("discount_cents") or 0) > 0:
        rows.append(("Discount:", f"(EGP {(inv['discount_cents']) / 100:,.2f})", False))
    if (inv.get("tax_cents") or 0) > 0:
        rows.append(("Tax:", money(inv.get("tax_cents")), False))
    rows.append(("Total:", money(inv.get("total_cents")), True))
    if paid > 0:
        rows.append(("Paid:", money(paid), False))
    rows.append(("Amount Due (EGP):", money(due), True))
    for label, val, bold in rows:
        right(R - 120, sy, label, FB if bold else F, 11 if bold else 10)
        right(R, sy, val, FB if bold else F, 11 if bold else 10)
        sy -= 22

    # --- Footer ----------------------------------------------------------
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont(FB, 11)
    c.drawCentredString(W / 2, 60, ar(f"Powered by {COMPANY_NAME}"))

    c.showPage(); c.save()
    return buf.getvalue()
