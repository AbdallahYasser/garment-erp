"""Manufacturing-order reads: list, detail, auto material + cost estimate.

Quantities in milli-units (x1000). Money in piastres (x100). The estimate is
best-effort per the FRS cost model and is also recomputable on demand.
"""
from typing import Optional

from src.queries.base import fetch_all, fetch_one


async def compute_estimate(sample_id: Optional[int], quantity: int) -> dict:
    """Cost breakdown for `quantity` pieces.

    Fabric is reference-only and intentionally NOT part of this estimate.
    Cost = quantity x (manufacturing/piece + accessories/piece) + one-off
    (factory-supplied blueprint + printing).
    """
    breakdown = {
        "quantity": quantity,
        "required_accessories": [],   # [{accessory_id, name, required_milli, cost_cents}]
        "manufacturing_per_piece_cents": 0,
        "accessories_per_piece_cents": 0,
        "one_off_cents": 0,
        "est_total_cents": 0,
    }
    if not sample_id or quantity <= 0:
        return breakdown

    # Per-piece accessory consumption x unit price.
    acc_rows = await fetch_all(
        """
        SELECT sa.accessory_id, sa.qty_per_piece_milli,
               a.name, a.unit_price_cents
        FROM spec_accessories sa
        JOIN accessories a ON a.id = sa.accessory_id
        WHERE sa.sample_id = ? AND sa.deleted_at IS NULL
        """, (sample_id,))
    acc_per_piece = 0
    for r in acc_rows:
        req_milli = (r["qty_per_piece_milli"] or 0) * quantity
        line_cost = ((r["qty_per_piece_milli"] or 0) * (r["unit_price_cents"] or 0)) // 1000
        acc_per_piece += line_cost
        breakdown["required_accessories"].append({
            "accessory_id": r["accessory_id"],
            "name": r["name"],
            "required_milli": req_milli,
            "cost_per_piece_cents": line_cost,
            "cost_total_cents": line_cost * quantity,
        })
    breakdown["accessories_per_piece_cents"] = acc_per_piece

    mfg = await fetch_one(
        "SELECT cost_cents, cut_cost_cents, sew_cost_cents, finish_cost_cents "
        "FROM sample_manufacturing WHERE sample_id = ? AND deleted_at IS NULL "
        "ORDER BY id DESC LIMIT 1", (sample_id,))
    mfg_pp = 0
    if mfg:
        # Prefer the single cost; fall back to the legacy cut+sew+finish sum.
        mfg_pp = mfg.get("cost_cents") or (
            (mfg.get("cut_cost_cents") or 0) + (mfg.get("sew_cost_cents") or 0)
            + (mfg.get("finish_cost_cents") or 0))
    breakdown["manufacturing_per_piece_cents"] = mfg_pp

    # One-off sample-level costs (blueprint + printing only; fabric excluded).
    one_off = 0
    for tbl in ("sample_blueprint", "sample_printing"):
        row = await fetch_one(
            f"SELECT COALESCE(SUM(cost_cents),0) AS s FROM {tbl} "
            f"WHERE sample_id = ? AND deleted_at IS NULL", (sample_id,))
        one_off += (row or {}).get("s") or 0
    breakdown["one_off_cents"] = one_off

    breakdown["est_total_cents"] = (
        quantity * (mfg_pp + acc_per_piece) + one_off
    )
    return breakdown


async def get_detail(order_id: int) -> Optional[dict]:
    order = await fetch_one(
        """
        SELECT o.*, c.name AS customer_name, s.name AS sample_name,
               fr.color AS roll_color, fr.fabric_type AS roll_fabric_type
        FROM manufacturing_orders o
        LEFT JOIN customers c ON c.id = o.customer_id
        LEFT JOIN samples s ON s.id = o.sample_id
        LEFT JOIN fabric_rolls fr ON fr.id = o.fabric_roll_id
        WHERE o.id = ?
        """, (order_id,))
    if not order:
        return None
    order["stages"] = await fetch_all(
        "SELECT * FROM order_stages WHERE order_id = ? AND deleted_at IS NULL "
        "ORDER BY id", (order_id,))
    order["cuts"] = await fetch_all(
        "SELECT * FROM order_cuts WHERE order_id = ? AND deleted_at IS NULL "
        "ORDER BY id", (order_id,))
    order["estimate"] = await compute_estimate(order.get("sample_id"), order.get("quantity") or 0)
    paid = await fetch_one(
        "SELECT COALESCE(SUM(amount_cents),0) AS s FROM payments "
        "WHERE order_id = ? AND deleted_at IS NULL", (order_id,))
    order["paid_cents"] = (paid or {}).get("s") or 0
    order["balance_cents"] = (order.get("est_total_cents") or 0) - order["paid_cents"]
    return order


async def list_orders(*, status: Optional[str] = None, customer_id: Optional[int] = None,
                      include_deleted: bool = False) -> list[dict]:
    where = [] if include_deleted else ["o.deleted_at IS NULL"]
    params: list = []
    if status:
        where.append("o.status = ?"); params.append(status)
    if customer_id:
        where.append("o.customer_id = ?"); params.append(customer_id)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    return await fetch_all(
        f"""
        SELECT o.*, c.name AS customer_name, s.name AS sample_name
        FROM manufacturing_orders o
        LEFT JOIN customers c ON c.id = o.customer_id
        LEFT JOIN samples s ON s.id = o.sample_id
        {where_sql}
        ORDER BY o.id DESC
        """, tuple(params))
