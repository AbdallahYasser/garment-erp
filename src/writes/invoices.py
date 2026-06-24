"""Invoice writes — create with lines, recompute totals + payment status."""
from typing import Optional

import aiosqlite

from src.db import write_db_uri
from src.writes import audit


async def _recompute_totals(db: aiosqlite.Connection, invoice_id: int) -> None:
    db.row_factory = aiosqlite.Row
    async with db.execute(
        "SELECT COALESCE(SUM(line_total_cents),0) AS s FROM invoice_lines "
        "WHERE invoice_id = ? AND deleted_at IS NULL", (invoice_id,)) as c:
        subtotal = (await c.fetchone())["s"]
    async with db.execute(
        "SELECT discount_cents, tax_cents FROM invoices WHERE id = ?",
        (invoice_id,)) as c:
        inv = await c.fetchone()
    discount = inv["discount_cents"] or 0
    tax = inv["tax_cents"] or 0
    total = subtotal - discount + tax
    await db.execute(
        "UPDATE invoices SET subtotal_cents = ?, total_cents = ? WHERE id = ?",
        (subtotal, total, invoice_id))
    await _recompute_status(db, invoice_id)


async def _recompute_status(db: aiosqlite.Connection, invoice_id: int) -> None:
    db.row_factory = aiosqlite.Row
    async with db.execute(
        "SELECT total_cents FROM invoices WHERE id = ?", (invoice_id,)) as c:
        total = (await c.fetchone())["total_cents"] or 0
    async with db.execute(
        "SELECT COALESCE(SUM(amount_cents),0) AS s FROM payments "
        "WHERE invoice_id = ? AND deleted_at IS NULL", (invoice_id,)) as c:
        paid = (await c.fetchone())["s"]
    status = "unpaid" if paid <= 0 else ("paid" if paid >= total else "partial")
    await db.execute("UPDATE invoices SET status = ? WHERE id = ?",
                     (status, invoice_id))


async def create_invoice(
    actor: dict, *,
    customer_id: int,
    order_id: Optional[int] = None,
    invoice_no: Optional[str] = None,
    invoice_date: Optional[str] = None,
    discount_cents: int = 0,
    tax_cents: int = 0,
    notes: Optional[str] = None,
    lines: Optional[list[dict]] = None,
) -> int:
    if not customer_id:
        raise ValueError("customer_id is required")
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            INSERT INTO invoices
              (invoice_no, customer_id, order_id, invoice_date,
               discount_cents, tax_cents, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'unpaid')
            """,
            (invoice_no, customer_id, order_id, invoice_date,
             int(discount_cents or 0), int(tax_cents or 0), notes))
        invoice_id = cur.lastrowid
        for ln in (lines or []):
            qty = int(ln.get("qty") or 0)
            unit = int(ln.get("unit_price_cents") or 0)
            await db.execute(
                "INSERT INTO invoice_lines "
                "(invoice_id, description, qty, unit_price_cents, line_total_cents) "
                "VALUES (?, ?, ?, ?, ?)",
                (invoice_id, ln.get("description"), qty, unit, qty * unit))
        await _recompute_totals(db, invoice_id)
        async with db.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)) as c:
            after = dict(await c.fetchone())
        await audit.log(
            actor=actor, entity="invoices", entity_id=invoice_id, action="create",
            after=after, summary=f"invoice created: {invoice_no or invoice_id}", db=db)
        await db.commit()
        return invoice_id


async def recompute(invoice_id: int) -> None:
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        await _recompute_totals(db, invoice_id)
        await db.commit()
