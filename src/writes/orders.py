"""Manufacturing-order writes.

Order creation selects the customer's sample and which fabric rolls (colors)
the order will use — each chosen roll becomes a "planned" cut line with no
quantity yet and no stock deducted. During the Cutting stage the user fills in
each line (rolls used, units/pieces, sizes, roll leftover), which deducts the
roll lot and records an inventory issue. Order quantity = sum of cut units;
est_total = unit_cost x quantity. Advancing past Cutting requires unit cost and
quantity > 0.
"""
from typing import Optional

import aiosqlite

from src.db import write_db_uri
from src.writes import audit

STAGES = ("new", "prep", "cutting", "printing", "sewing",
          "finishing", "packing", "ready", "delivered", "cancelled")

_LEFTOVER_FRAC = {"full": 0.0, "three_quarter": 0.75, "half": 0.5, "quarter": 0.25}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
async def _get_roll(db: aiosqlite.Connection, roll_id: Optional[int]) -> Optional[dict]:
    if not roll_id:
        return None
    async with db.execute("SELECT * FROM fabric_rolls WHERE id = ?", (roll_id,)) as c:
        row = await c.fetchone()
        return dict(row) if row else None


def _leftover(label: str, custom_milli: int, per_roll: int) -> int:
    if label == "custom":
        return max(0, int(custom_milli or 0))
    return int(_LEFTOVER_FRAC.get(label, 0.0) * per_roll)


def _consumed(rolls_used: int, per_roll: int, leftover: int) -> int:
    return max(0, rolls_used * per_roll - leftover)


async def _apply_roll(db, roll_id, d_rolls: int, d_remaining: int) -> None:
    """Adjust a roll lot's count + remaining meters (deltas may be +/-)."""
    roll = await _get_roll(db, roll_id)
    if not roll:
        return
    await db.execute(
        "UPDATE fabric_rolls SET rolls_count = ?, remaining_m_milli = ? WHERE id = ?",
        (max(0, (roll.get("rolls_count") or 0) + d_rolls),
         max(0, (roll.get("remaining_m_milli") or 0) + d_remaining), roll_id))


async def _sync_inventory(db, cut_id, order_id, roll, consumed, rolls_used, units) -> None:
    """Replace any prior movement for this cut with one reflecting `consumed`."""
    await db.execute(
        "UPDATE inventory_movements SET deleted_at = datetime('now') "
        "WHERE cut_id = ? AND deleted_at IS NULL", (cut_id,))
    if roll and consumed > 0:
        await db.execute(
            """
            INSERT INTO inventory_movements
              (item_type, item_id, item_name, owner, customer_id,
               movement_type, qty_milli, ref_order_id, cut_id, note)
            VALUES ('fabric', ?, ?, ?, ?, 'issue', ?, ?, ?, ?)
            """,
            (roll["id"], f"{roll.get('color') or ''} {roll.get('fabric_type') or ''}".strip(),
             roll.get("owner") or "factory", roll.get("customer_id"),
             consumed, order_id, cut_id, f"cut: {rolls_used} roll(s), {units} pcs"))


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


# --------------------------------------------------------------------------- #
# create / cost
# --------------------------------------------------------------------------- #
async def create_order(
    actor: dict, *,
    customer_id: int,
    sample_id: Optional[int] = None,
    code: Optional[str] = None,
    order_date: Optional[str] = None,
    delivery_date: Optional[str] = None,
    roll_lines: Optional[list] = None,   # [{fabric_roll_id, rolls_used}]
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

        # One cut line per selected roll/color with its rolls count. The rolls
        # are reserved (deducted) now; units/sizes/leftover are filled at cutting.
        for line in (roll_lines or []):
            rid = line.get("fabric_roll_id")
            ru = max(0, int(line.get("rolls_used") or 0))
            roll = await _get_roll(db, rid)
            cur2 = await db.execute(
                "INSERT INTO order_cuts (order_id, fabric_roll_id, color, "
                "remaining_label, remaining_m_milli) VALUES (?, ?, ?, 'full', 0)",
                (order_id, rid, (roll or {}).get("color")))
            if ru > 0:
                await _write_cut(db, actor, order_id, cur2.lastrowid,
                                 {"fabric_roll_id": rid, "rolls_used": ru,
                                  "units": 0, "remaining_label": "full"})

        async with db.execute(
            "SELECT * FROM manufacturing_orders WHERE id = ?", (order_id,)) as c:
            after = dict(await c.fetchone())
        await audit.log(actor=actor, entity="manufacturing_orders", entity_id=order_id,
                        action="create", after=after,
                        summary=f"order created: {code or order_id}"
                                + (f", {len(roll_lines)} color(s)" if roll_lines else ""),
                        db=db)
        await db.commit()
        return order_id


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


# --------------------------------------------------------------------------- #
# cut lines
# --------------------------------------------------------------------------- #
async def add_cut(actor: dict, order_id: int, **fields) -> int:
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT 1 FROM manufacturing_orders WHERE id = ? AND deleted_at IS NULL",
            (order_id,)) as c:
            if not await c.fetchone():
                raise ValueError("order not found")
        roll = await _get_roll(db, fields.get("fabric_roll_id"))
        cur = await db.execute(
            "INSERT INTO order_cuts (order_id, fabric_roll_id, color, "
            "remaining_label, remaining_m_milli) VALUES (?, ?, ?, 'full', 0)",
            (order_id, fields.get("fabric_roll_id"), (roll or {}).get("color")))
        cut_id = cur.lastrowid
        await _write_cut(db, actor, order_id, cut_id, fields)
        await db.commit()
        return cut_id


async def update_cut(actor: dict, order_id: int, cut_id: int, **fields) -> bool:
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM order_cuts WHERE id = ? AND order_id = ? AND deleted_at IS NULL",
            (cut_id, order_id)) as c:
            if not await c.fetchone():
                return False
        await _write_cut(db, actor, order_id, cut_id, fields)
        await db.commit()
        return True


async def _write_cut(db, actor, order_id, cut_id, fields) -> None:
    """Apply cut detail: reverse the cut's previous stock effect, then apply new.

    rolls_used is set at order creation and kept; at cutting only `units`,
    `sizes` and `remaining_rolls_milli` (rolls left after the cut) are entered.
    """
    async with db.execute("SELECT * FROM order_cuts WHERE id = ?", (cut_id,)) as c:
        cut = dict(await c.fetchone())
    roll = await _get_roll(db, cut.get("fabric_roll_id"))
    per_roll = (roll or {}).get("length_m_milli") or 0

    # Reverse previous deduction for this cut.
    old_consumed = _consumed(cut.get("rolls_used") or 0, per_roll, cut.get("remaining_m_milli") or 0)
    if roll and (cut.get("rolls_used") or 0) > 0:
        await _apply_roll(db, roll["id"], cut.get("rolls_used") or 0, old_consumed)
        roll = await _get_roll(db, roll["id"])  # refresh after restore

    # rolls_used: only changes if explicitly provided (order creation); else kept.
    if fields.get("rolls_used") is not None:
        rolls_used = max(0, int(fields["rolls_used"]))
    else:
        rolls_used = cut.get("rolls_used") or 0
    units = max(0, int(fields.get("units") if fields.get("units") is not None else cut.get("units") or 0))
    sizes = fields.get("sizes") if "sizes" in fields else cut.get("sizes")

    rem_rolls_milli = max(0, int(fields.get("remaining_rolls_milli") or 0))
    if rolls_used > 0 and rem_rolls_milli >= rolls_used * 1000:
        raise ValueError(f"roll remaining must be less than the {rolls_used} rolls of this color")
    leftover = rem_rolls_milli * per_roll // 1000   # leftover meters
    consumed = _consumed(rolls_used, per_roll, leftover)

    await db.execute(
        "UPDATE order_cuts SET rolls_used = ?, units = ?, sizes = ?, "
        "remaining_label = 'rolls', remaining_rolls_milli = ?, remaining_m_milli = ? WHERE id = ?",
        (rolls_used, units, sizes, rem_rolls_milli, leftover, cut_id))

    if roll and rolls_used > 0:
        await _apply_roll(db, roll["id"], -rolls_used, -consumed)
    await _sync_inventory(db, cut_id, order_id, roll, consumed, rolls_used, units)
    await _recompute_totals(db, order_id)
    await audit.log(actor=actor, entity="manufacturing_orders", entity_id=order_id,
                    action="update",
                    after={"cut_id": cut_id, "color": cut.get("color"),
                           "units": units, "sizes": sizes, "rolls_used": rolls_used},
                    summary=f"cut: {cut.get('color') or '-'} {units} pcs [{sizes or ''}]", db=db)


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
        roll = await _get_roll(db, cut.get("fabric_roll_id"))
        per_roll = (roll or {}).get("length_m_milli") or 0
        if roll and (cut.get("rolls_used") or 0) > 0:
            consumed = _consumed(cut["rolls_used"], per_roll, cut.get("remaining_m_milli") or 0)
            await _apply_roll(db, roll["id"], cut["rolls_used"], consumed)
        await _sync_inventory(db, cut_id, order_id, None, 0, 0, 0)
        await db.execute(
            "UPDATE order_cuts SET deleted_at = datetime('now') WHERE id = ?", (cut_id,))
        await _recompute_totals(db, order_id)
        await audit.log(actor=actor, entity="manufacturing_orders", entity_id=order_id,
                        action="update", before={"removed_cut": cut_id},
                        summary=f"cut removed: {cut.get('color') or '-'}", db=db)
        await db.commit()
        return True


# --------------------------------------------------------------------------- #
# stages
# --------------------------------------------------------------------------- #
async def delete_order(actor: dict, order_id: int) -> bool:
    """Soft-delete one order (+ its cuts/stages/inventory movements) and restore
    the fabric-roll stock its cuts had consumed."""
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM manufacturing_orders WHERE id = ? AND deleted_at IS NULL",
            (order_id,)) as c:
            order = await c.fetchone()
        if not order:
            return False
        order = dict(order)
        async with db.execute(
            "SELECT * FROM order_cuts WHERE order_id = ? AND deleted_at IS NULL",
            (order_id,)) as c:
            cuts = [dict(r) for r in await c.fetchall()]
        for cut in cuts:
            if cut.get("fabric_roll_id") and (cut.get("rolls_used") or 0) > 0:
                roll = await _get_roll(db, cut["fabric_roll_id"])
                if roll:
                    per_roll = roll.get("length_m_milli") or 0
                    consumed = _consumed(cut["rolls_used"], per_roll,
                                         cut.get("remaining_m_milli") or 0)
                    await _apply_roll(db, roll["id"], cut["rolls_used"], consumed)
        await db.execute("UPDATE inventory_movements SET deleted_at = datetime('now') "
                         "WHERE ref_order_id = ? AND deleted_at IS NULL", (order_id,))
        await db.execute("UPDATE order_cuts SET deleted_at = datetime('now') "
                         "WHERE order_id = ? AND deleted_at IS NULL", (order_id,))
        await db.execute("UPDATE order_stages SET deleted_at = datetime('now') "
                         "WHERE order_id = ? AND deleted_at IS NULL", (order_id,))
        await db.execute("UPDATE manufacturing_orders SET deleted_at = datetime('now') "
                         "WHERE id = ?", (order_id,))
        await audit.log(actor=actor, entity="manufacturing_orders", entity_id=order_id,
                        action="delete", before=order,
                        summary=f"order deleted: {order.get('code') or order_id}; "
                                f"roll stock restored", db=db)
        await db.commit()
        return True


async def wipe_all_orders(actor: dict) -> dict:
    """Delete every order + its cuts/stages/order-linked inventory movements,
    restoring the fabric-roll stock the cuts had consumed. Append-only audit
    keeps the record. Irreversible."""
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM order_cuts WHERE deleted_at IS NULL") as c:
            cuts = [dict(r) for r in await c.fetchall()]
        for cut in cuts:
            if cut.get("fabric_roll_id") and (cut.get("rolls_used") or 0) > 0:
                roll = await _get_roll(db, cut["fabric_roll_id"])
                if roll:
                    per_roll = roll.get("length_m_milli") or 0
                    consumed = _consumed(cut["rolls_used"], per_roll,
                                         cut.get("remaining_m_milli") or 0)
                    await _apply_roll(db, roll["id"], cut["rolls_used"], consumed)
        async with db.execute("SELECT COUNT(*) AS n FROM manufacturing_orders") as c:
            n = (await c.fetchone())["n"]
        await db.execute("DELETE FROM inventory_movements WHERE ref_order_id IS NOT NULL")
        await db.execute("DELETE FROM order_cuts")
        await db.execute("DELETE FROM order_stages")
        await db.execute("DELETE FROM manufacturing_orders")
        await audit.log(actor=actor, entity="manufacturing_orders", action="wipe",
                        summary=f"all orders deleted ({n}); roll stock restored", db=db)
        await db.commit()
        return {"deleted_orders": n, "rolls_restored_lines": len(cuts)}


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

        cut_idx = STAGES.index("cutting")
        target_idx = STAGES.index(stage)
        if stage != "cancelled" and target_idx > cut_idx:
            if not (order["unit_cost_cents"] or 0):
                raise ValueError("enter the unit cost before advancing past Cutting")
            async with db.execute(
                "SELECT COUNT(*) AS total, "
                "SUM(CASE WHEN units > 0 THEN 1 ELSE 0 END) AS filled "
                "FROM order_cuts WHERE order_id = ? AND deleted_at IS NULL",
                (order_id,)) as c:
                row = await c.fetchone()
            total, filled = row["total"], (row["filled"] or 0)
            if total == 0:
                raise ValueError("select a fabric roll/color for this order first")
            if filled < total:
                raise ValueError(
                    f"enter cut details for all colors before advancing "
                    f"({filled}/{total} done)")

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
