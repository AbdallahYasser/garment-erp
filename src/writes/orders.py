"""Manufacturing-order writes — minimal create, then cutting details.

Order header carries no quantity/cost at creation. During the Cutting stage the
user records the unit cost and one or more cut lines (per color); the order
quantity is the sum of the cut units and est_total = unit_cost x quantity.
Advancing past Cutting requires both unit cost and quantity > 0.
"""
from typing import Optional

import aiosqlite

from src.db import write_db_uri
from src.writes import audit

STAGES = ("new", "prep", "cutting", "printing", "sewing",
          "finishing", "packing", "ready", "delivered", "cancelled")

# Fraction of a roll left uncut for each preset leftover option.
_LEFTOVER_FRAC = {"full": 0.0, "three_quarter": 0.75, "half": 0.5, "quarter": 0.25}


async def create_order(
    actor: dict, *,
    customer_id: int,
    sample_id: Optional[int] = None,
    code: Optional[str] = None,
    order_date: Optional[str] = None,
    delivery_date: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    if not customer_id:
        raise ValueError("customer_id is required")
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            INSERT INTO manufacturing_orders
              (code, customer_id, sample_id, order_date, delivery_date,
               quantity, est_total_cents, status, notes)
            VALUES (?, ?, ?, ?, ?, 0, 0, 'new', ?)
            """,
            (code, customer_id, sample_id, order_date, delivery_date, notes))
        order_id = cur.lastrowid
        await db.execute(
            "INSERT INTO order_stages (order_id, stage, start_date) "
            "VALUES (?, 'new', datetime('now'))", (order_id,))
        async with db.execute(
            "SELECT * FROM manufacturing_orders WHERE id = ?", (order_id,)) as c:
            after = dict(await c.fetchone())
        await audit.log(actor=actor, entity="manufacturing_orders", entity_id=order_id,
                        action="create", after=after,
                        summary=f"order created: {code or order_id}", db=db)
        await db.commit()
        return order_id


async def _recompute_totals(db: aiosqlite.Connection, order_id: int) -> None:
    db.row_factory = aiosqlite.Row
    async with db.execute(
        "SELECT COALESCE(SUM(units),0) AS q FROM order_cuts "
        "WHERE order_id = ? AND deleted_at IS NULL", (order_id,)) as c:
        qty = (await c.fetchone())["q"]
    async with db.execute(
        "SELECT unit_cost_cents FROM manufacturing_orders WHERE id = ?", (order_id,)) as c:
        unit = (await c.fetchone())["unit_cost_cents"] or 0
    await db.execute(
        "UPDATE manufacturing_orders SET quantity = ?, est_total_cents = ? WHERE id = ?",
        (qty, unit * qty, order_id))


async def set_unit_cost(actor: dict, order_id: int, unit_cost_cents: int) -> bool:
    unit_cost_cents = max(0, int(unit_cost_cents or 0))
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT unit_cost_cents FROM manufacturing_orders "
            "WHERE id = ? AND deleted_at IS NULL", (order_id,)) as c:
            row = await c.fetchone()
        if not row:
            return False
        before = row["unit_cost_cents"]
        await db.execute(
            "UPDATE manufacturing_orders SET unit_cost_cents = ? WHERE id = ?",
            (unit_cost_cents, order_id))
        await _recompute_totals(db, order_id)
        await audit.log(actor=actor, entity="manufacturing_orders", entity_id=order_id,
                        action="update", before={"unit_cost_cents": before},
                        after={"unit_cost_cents": unit_cost_cents},
                        summary=f"order {order_id}: unit cost {unit_cost_cents/100:.2f}", db=db)
        await db.commit()
        return True


async def add_cut(
    actor: dict, order_id: int, *,
    fabric_roll_id: Optional[int] = None,
    rolls_used: int = 0,
    units: int = 0,
    sizes: Optional[str] = None,
    remaining_label: str = "full",
    remaining_custom_m_milli: int = 0,
) -> int:
    rolls_used = max(0, int(rolls_used or 0))
    units = max(0, int(units or 0))
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM manufacturing_orders WHERE id = ? AND deleted_at IS NULL",
            (order_id,)) as c:
            if not await c.fetchone():
                raise ValueError("order not found")

        color, per_roll = None, 0
        roll = None
        if fabric_roll_id:
            async with db.execute(
                "SELECT * FROM fabric_rolls WHERE id = ? AND deleted_at IS NULL",
                (fabric_roll_id,)) as c:
                roll = await c.fetchone()
            if roll:
                roll = dict(roll)
                color = roll.get("color")
                per_roll = roll.get("length_m_milli") or 0

        # Leftover meters of the (last) roll left uncut.
        if remaining_label == "custom":
            leftover = max(0, int(remaining_custom_m_milli or 0))
        else:
            leftover = int(_LEFTOVER_FRAC.get(remaining_label, 0.0) * per_roll)
        consumed = max(0, rolls_used * per_roll - leftover)

        cur = await db.execute(
            """
            INSERT INTO order_cuts
              (order_id, fabric_roll_id, color, rolls_used, units, sizes,
               remaining_label, remaining_m_milli)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (order_id, fabric_roll_id, color, rolls_used, units, sizes,
             remaining_label, leftover))
        cut_id = cur.lastrowid

        if roll and rolls_used > 0:
            new_count = max(0, (roll.get("rolls_count") or 0) - rolls_used)
            new_remaining = max(0, (roll.get("remaining_m_milli") or 0) - consumed)
            await db.execute(
                "UPDATE fabric_rolls SET rolls_count = ?, remaining_m_milli = ? WHERE id = ?",
                (new_count, new_remaining, fabric_roll_id))
            await db.execute(
                """
                INSERT INTO inventory_movements
                  (item_type, item_id, item_name, owner, customer_id,
                   movement_type, qty_milli, ref_order_id, note)
                VALUES ('fabric', ?, ?, ?, ?, 'issue', ?, ?, ?)
                """,
                (fabric_roll_id, f"{color or ''} {roll.get('fabric_type') or ''}".strip(),
                 roll.get("owner") or "factory", roll.get("customer_id"),
                 consumed, order_id, f"cut: {rolls_used} roll(s), {units} pcs"))

        await _recompute_totals(db, order_id)
        await audit.log(actor=actor, entity="manufacturing_orders", entity_id=order_id,
                        action="update", after={"cut_id": cut_id, "color": color,
                        "units": units, "sizes": sizes, "rolls_used": rolls_used},
                        summary=f"cut: {color or '-'} {units} pcs [{sizes or ''}]", db=db)
        await db.commit()
        return cut_id


async def remove_cut(actor: dict, order_id: int, cut_id: int) -> bool:
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM order_cuts WHERE id = ? AND order_id = ? AND deleted_at IS NULL",
            (cut_id, order_id)) as c:
            cut = await c.fetchone()
        if not cut:
            return False
        cut = dict(cut)
        await db.execute(
            "UPDATE order_cuts SET deleted_at = datetime('now') WHERE id = ?", (cut_id,))
        # Restore the roll stock that this cut had consumed.
        if cut.get("fabric_roll_id") and (cut.get("rolls_used") or 0) > 0:
            async with db.execute(
                "SELECT * FROM fabric_rolls WHERE id = ?", (cut["fabric_roll_id"],)) as c:
                roll = await c.fetchone()
            if roll:
                roll = dict(roll)
                per_roll = roll.get("length_m_milli") or 0
                consumed = max(0, cut["rolls_used"] * per_roll - (cut.get("remaining_m_milli") or 0))
                await db.execute(
                    "UPDATE fabric_rolls SET rolls_count = ?, remaining_m_milli = ? WHERE id = ?",
                    ((roll.get("rolls_count") or 0) + cut["rolls_used"],
                     (roll.get("remaining_m_milli") or 0) + consumed, cut["fabric_roll_id"]))
        await _recompute_totals(db, order_id)
        await audit.log(actor=actor, entity="manufacturing_orders", entity_id=order_id,
                        action="update", before={"removed_cut": cut_id},
                        summary=f"cut removed: {cut.get('color') or '-'}", db=db)
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

        # Gate: cannot advance PAST cutting until unit cost + quantity are set.
        cut_idx = STAGES.index("cutting")
        target_idx = STAGES.index(stage)
        if stage != "cancelled" and target_idx > cut_idx:
            if not (order["unit_cost_cents"] or 0):
                raise ValueError("enter the unit cost before advancing past Cutting")
            if not (order["quantity"] or 0):
                raise ValueError("add at least one cut (quantity) before advancing past Cutting")

        await db.execute(
            "UPDATE order_stages SET end_date = datetime('now') "
            "WHERE order_id = ? AND end_date IS NULL", (order_id,))
        await db.execute(
            "INSERT INTO order_stages (order_id, stage, start_date, responsible, notes) "
            "VALUES (?, ?, datetime('now'), ?, ?)", (order_id, stage, responsible, notes))
        await db.execute(
            "UPDATE manufacturing_orders SET status = ? WHERE id = ?", (stage, order_id))
        await audit.log(actor=actor, entity="manufacturing_orders", entity_id=order_id,
                        action="stage_change", before={"status": before_status},
                        after={"status": stage},
                        summary=f"order {order_id}: {before_status} -> {stage}", db=db)
        await db.commit()
        return True
