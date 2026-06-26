"""Manufacturing-order writes — create with auto estimate, stage transitions."""
from typing import Optional

import aiosqlite

from src.db import write_db_uri
from src.queries.orders import compute_estimate
from src.writes import audit

STAGES = ("new", "prep", "cutting", "printing", "sewing",
          "finishing", "packing", "ready", "delivered", "cancelled")


async def create_order(
    actor: dict,
    *,
    customer_id: int,
    sample_id: Optional[int] = None,
    code: Optional[str] = None,
    quantity: int = 0,
    order_date: Optional[str] = None,
    delivery_date: Optional[str] = None,
    unit_cost_cents: Optional[int] = None,
    fabric_roll_id: Optional[int] = None,
    rolls_used: int = 0,
    notes: Optional[str] = None,
) -> int:
    if not customer_id:
        raise ValueError("customer_id is required")
    quantity = int(quantity or 0)
    rolls_used = max(0, int(rolls_used or 0))

    if unit_cost_cents is not None:
        est_total = int(unit_cost_cents) * quantity
    else:
        est = await compute_estimate(sample_id, quantity)
        est_total = est["est_total_cents"]

    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            INSERT INTO manufacturing_orders
              (code, customer_id, sample_id, order_date, delivery_date,
               quantity, unit_cost_cents, est_total_cents, status,
               fabric_roll_id, rolls_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
            """,
            (code, customer_id, sample_id, order_date, delivery_date,
             quantity, unit_cost_cents, est_total, fabric_roll_id, rolls_used),
        )
        order_id = cur.lastrowid
        # Open the first production stage.
        await db.execute(
            "INSERT INTO order_stages (order_id, stage, start_date) "
            "VALUES (?, 'new', datetime('now'))", (order_id,))
        if notes:
            await db.execute(
                "UPDATE manufacturing_orders SET notes = ? WHERE id = ?",
                (notes, order_id))

        # Allocate fabric rolls to the order: deduct from the lot and record an
        # inventory "issue" movement so the stock ledger stays consistent.
        if fabric_roll_id and rolls_used > 0:
            async with db.execute(
                "SELECT * FROM fabric_rolls WHERE id = ? AND deleted_at IS NULL",
                (fabric_roll_id,)) as c:
                roll = await c.fetchone()
            if roll:
                roll = dict(roll)
                per_roll = roll.get("length_m_milli") or 0
                use_rolls = min(rolls_used, roll.get("rolls_count") or 0) or rolls_used
                issued_milli = per_roll * use_rolls
                new_count = max(0, (roll.get("rolls_count") or 0) - use_rolls)
                new_remaining = max(0, (roll.get("remaining_m_milli") or 0) - issued_milli)
                await db.execute(
                    "UPDATE fabric_rolls SET rolls_count = ?, remaining_m_milli = ? "
                    "WHERE id = ?", (new_count, new_remaining, fabric_roll_id))
                await db.execute(
                    """
                    INSERT INTO inventory_movements
                      (item_type, item_id, item_name, owner, customer_id,
                       movement_type, qty_milli, ref_order_id, note)
                    VALUES ('fabric', ?, ?, ?, ?, 'issue', ?, ?, ?)
                    """,
                    (fabric_roll_id,
                     f"{roll.get('color') or ''} {roll.get('fabric_type') or ''}".strip(),
                     roll.get("owner") or "factory", roll.get("customer_id"),
                     issued_milli, order_id,
                     f"{use_rolls} roll(s) issued to order {code or order_id}"))

        async with db.execute(
            "SELECT * FROM manufacturing_orders WHERE id = ?", (order_id,)
        ) as c:
            after = dict(await c.fetchone())
        await audit.log(
            actor=actor, entity="manufacturing_orders", entity_id=order_id,
            action="create", after=after,
            summary=f"order created: {code or order_id} x{quantity}"
                    + (f", {rolls_used} roll(s)" if rolls_used else ""), db=db,
        )
        await db.commit()
        return order_id


async def set_pieces(actor: dict, order_id: int, pieces_count: int) -> bool:
    pieces_count = max(0, int(pieces_count or 0))
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT pieces_count FROM manufacturing_orders "
            "WHERE id = ? AND deleted_at IS NULL", (order_id,)) as c:
            row = await c.fetchone()
        if not row:
            return False
        before = row["pieces_count"]
        await db.execute(
            "UPDATE manufacturing_orders SET pieces_count = ? WHERE id = ?",
            (pieces_count, order_id))
        await audit.log(
            actor=actor, entity="manufacturing_orders", entity_id=order_id,
            action="update", before={"pieces_count": before},
            after={"pieces_count": pieces_count},
            summary=f"order {order_id}: pieces set to {pieces_count}", db=db)
        await db.commit()
        return True


async def advance_stage(
    actor: dict, order_id: int, stage: str,
    *, responsible: Optional[str] = None, notes: Optional[str] = None,
) -> bool:
    if stage not in STAGES:
        raise ValueError("invalid stage")
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM manufacturing_orders WHERE id = ? AND deleted_at IS NULL",
            (order_id,)) as c:
            order = await c.fetchone()
        if not order:
            return False
        before_status = order["status"]

        # Gate: cannot advance PAST cutting until the cut piece count is entered.
        cut_idx = STAGES.index("cutting")
        target_idx = STAGES.index(stage)
        if stage != "cancelled" and target_idx > cut_idx and not (order["pieces_count"] or 0):
            raise ValueError("enter the number of pieces (cut) before advancing past Cutting")

        # Close the currently-open stage, open the new one.
        await db.execute(
            "UPDATE order_stages SET end_date = datetime('now') "
            "WHERE order_id = ? AND end_date IS NULL", (order_id,))
        await db.execute(
            "INSERT INTO order_stages (order_id, stage, start_date, responsible, notes) "
            "VALUES (?, ?, datetime('now'), ?, ?)",
            (order_id, stage, responsible, notes))
        await db.execute(
            "UPDATE manufacturing_orders SET status = ? WHERE id = ?",
            (stage, order_id))
        await audit.log(
            actor=actor, entity="manufacturing_orders", entity_id=order_id,
            action="stage_change",
            before={"status": before_status}, after={"status": stage},
            summary=f"order {order_id}: {before_status} -> {stage}", db=db,
        )
        await db.commit()
        return True
