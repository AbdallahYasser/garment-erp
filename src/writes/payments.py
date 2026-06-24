"""Payment writes — record a payment and refresh the invoice status."""
from typing import Optional

import aiosqlite

from src.db import write_db_uri
from src.writes import audit
from src.writes.invoices import _recompute_status


async def record_payment(
    actor: dict, *,
    customer_id: int,
    amount_cents: int,
    kind: str = "progress",
    order_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    payment_date: Optional[str] = None,
    note: Optional[str] = None,
) -> int:
    if kind not in ("advance", "progress", "final"):
        raise ValueError("invalid kind")
    if not customer_id:
        raise ValueError("customer_id is required")
    amount_cents = int(amount_cents or 0)
    if amount_cents <= 0:
        raise ValueError("amount must be positive")
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            INSERT INTO payments
              (customer_id, order_id, invoice_id, amount_cents, kind, payment_date, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (customer_id, order_id, invoice_id, amount_cents, kind, payment_date, note))
        payment_id = cur.lastrowid
        if invoice_id:
            await _recompute_status(db, invoice_id)
        await audit.log(
            actor=actor, entity="payments", entity_id=payment_id, action="payment",
            after={"customer_id": customer_id, "order_id": order_id,
                   "invoice_id": invoice_id, "amount_cents": amount_cents, "kind": kind},
            summary=f"payment {kind}: {amount_cents/100:.2f} EGP", db=db)
        await db.commit()
        return payment_id


async def delete_payment(actor: dict, payment_id: int) -> bool:
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM payments WHERE id = ? AND deleted_at IS NULL",
            (payment_id,)) as c:
            before = await c.fetchone()
        if not before:
            return False
        before = dict(before)
        await db.execute(
            "UPDATE payments SET deleted_at = datetime('now') WHERE id = ?",
            (payment_id,))
        if before.get("invoice_id"):
            await _recompute_status(db, before["invoice_id"])
        await audit.log(
            actor=actor, entity="payments", entity_id=payment_id, action="delete",
            before=before, summary=f"payment removed: {before['amount_cents']/100:.2f} EGP",
            db=db)
        await db.commit()
        return True
