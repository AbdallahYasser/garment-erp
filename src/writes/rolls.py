"""Fabric-roll writes — create a lot of N identical rolls in one action."""
from typing import Optional

import aiosqlite

from src.db import write_db_uri
from src.writes import audit


async def create_lot(
    actor: dict, *,
    color: Optional[str] = None,
    fabric_type: Optional[str] = None,
    length_m_milli: int = 0,
    rolls_count: int = 1,
    owner: str = "factory",
    customer_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
) -> int:
    """Insert one fabric_rolls row representing `rolls_count` identical rolls.

    length_m_milli is the length of each roll; remaining starts at the lot
    total (length x count).
    """
    rolls_count = max(1, int(rolls_count or 1))
    length = int(length_m_milli or 0)
    total_remaining = length * rolls_count
    if owner not in ("factory", "customer"):
        owner = "factory"
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            INSERT INTO fabric_rolls
              (color, fabric_type, length_m_milli, remaining_m_milli,
               rolls_count, owner, customer_id, supplier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (color, fabric_type, length, total_remaining, rolls_count,
             owner, customer_id, supplier_id),
        )
        roll_id = cur.lastrowid
        async with db.execute("SELECT * FROM fabric_rolls WHERE id = ?", (roll_id,)) as c:
            after = dict(await c.fetchone())
        await audit.log(
            actor=actor, entity="fabric_rolls", entity_id=roll_id, action="create",
            after=after,
            summary=f"fabric lot: {rolls_count} x {length/1000:g}m {color or ''} {fabric_type or ''}".strip(),
            db=db)
        await db.commit()
        return roll_id
