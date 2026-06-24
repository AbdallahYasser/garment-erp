"""Invoice reads — list + detail with lines, payments and balance."""
from typing import Optional

from src.queries.base import fetch_all, fetch_one


async def list_invoices(*, status: Optional[str] = None,
                        customer_id: Optional[int] = None,
                        include_deleted: bool = False) -> list[dict]:
    where = [] if include_deleted else ["i.deleted_at IS NULL"]
    params: list = []
    if status:
        where.append("i.status = ?"); params.append(status)
    if customer_id:
        where.append("i.customer_id = ?"); params.append(customer_id)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    rows = await fetch_all(
        f"""
        SELECT i.*, c.name AS customer_name,
               COALESCE((SELECT SUM(amount_cents) FROM payments p
                         WHERE p.invoice_id = i.id AND p.deleted_at IS NULL),0) AS paid_cents
        FROM invoices i
        LEFT JOIN customers c ON c.id = i.customer_id
        {where_sql}
        ORDER BY i.id DESC
        """, tuple(params))
    for r in rows:
        r["balance_cents"] = (r.get("total_cents") or 0) - (r.get("paid_cents") or 0)
    return rows


async def get_detail(invoice_id: int) -> Optional[dict]:
    inv = await fetch_one(
        """
        SELECT i.*, c.name AS customer_name
        FROM invoices i LEFT JOIN customers c ON c.id = i.customer_id
        WHERE i.id = ?
        """, (invoice_id,))
    if not inv:
        return None
    inv["lines"] = await fetch_all(
        "SELECT * FROM invoice_lines WHERE invoice_id = ? AND deleted_at IS NULL "
        "ORDER BY id", (invoice_id,))
    inv["payments"] = await fetch_all(
        "SELECT * FROM payments WHERE invoice_id = ? AND deleted_at IS NULL "
        "ORDER BY id", (invoice_id,))
    paid = sum(p["amount_cents"] for p in inv["payments"])
    inv["paid_cents"] = paid
    inv["balance_cents"] = (inv.get("total_cents") or 0) - paid
    return inv
