"""Lightweight lists for dropdowns + customer 360 + dashboard."""
from typing import Optional

from src.queries.base import fetch_all, fetch_one


async def all_lookups() -> dict:
    return {
        "customers": await fetch_all(
            "SELECT id, name, company FROM customers WHERE deleted_at IS NULL ORDER BY name"),
        "suppliers": await fetch_all(
            "SELECT id, name FROM suppliers WHERE deleted_at IS NULL ORDER BY name"),
        "samples": await fetch_all(
            "SELECT id, name, code, customer_id FROM samples WHERE deleted_at IS NULL ORDER BY id DESC"),
        "accessories": await fetch_all(
            "SELECT id, name, unit, unit_price_cents FROM accessories WHERE deleted_at IS NULL ORDER BY name"),
        "fabric_rolls": await fetch_all(
            "SELECT id, color, fabric_type, rolls_count, owner, customer_id "
            "FROM fabric_rolls WHERE deleted_at IS NULL AND rolls_count > 0 ORDER BY id DESC"),
        "orders": await fetch_all(
            "SELECT o.id, o.code, o.customer_id, o.quantity, o.unit_cost_cents, "
            "o.status, s.name AS sample_name "
            "FROM manufacturing_orders o LEFT JOIN samples s ON s.id = o.sample_id "
            "WHERE o.deleted_at IS NULL ORDER BY o.id DESC"),
    }


async def customer_360(customer_id: int) -> Optional[dict]:
    cust = await fetch_one("SELECT * FROM customers WHERE id = ?", (customer_id,))
    if not cust:
        return None
    cust["samples"] = await fetch_all(
        "SELECT id, name, code, status FROM samples "
        "WHERE customer_id = ? AND deleted_at IS NULL ORDER BY id DESC", (customer_id,))
    cust["orders"] = await fetch_all(
        "SELECT id, code, quantity, status, est_total_cents FROM manufacturing_orders "
        "WHERE customer_id = ? AND deleted_at IS NULL ORDER BY id DESC", (customer_id,))
    cust["invoices"] = await fetch_all(
        "SELECT id, invoice_no, total_cents, status FROM invoices "
        "WHERE customer_id = ? AND deleted_at IS NULL ORDER BY id DESC", (customer_id,))
    paid = await fetch_one(
        "SELECT COALESCE(SUM(amount_cents),0) AS s FROM payments "
        "WHERE customer_id = ? AND deleted_at IS NULL", (customer_id,))
    # Headline financials follow the ORDERS (the order is the bill): total =
    # sum of order costs (excluding cancelled), balance = total - payments.
    orders_total = await fetch_one(
        "SELECT COALESCE(SUM(est_total_cents),0) AS s FROM manufacturing_orders "
        "WHERE customer_id = ? AND deleted_at IS NULL AND status != 'cancelled'",
        (customer_id,))
    invoiced = await fetch_one(
        "SELECT COALESCE(SUM(total_cents),0) AS s FROM invoices "
        "WHERE customer_id = ? AND deleted_at IS NULL", (customer_id,))
    cust["paid_cents"] = (paid or {}).get("s") or 0
    cust["orders_total_cents"] = (orders_total or {}).get("s") or 0
    cust["invoiced_cents"] = (invoiced or {}).get("s") or 0
    cust["billed_cents"] = cust["orders_total_cents"]
    cust["balance_cents"] = cust["billed_cents"] - cust["paid_cents"]
    # Customer-owned stock
    cust["fabric_rolls"] = await fetch_all(
        "SELECT id, roll_no, color, fabric_type, rolls_count, remaining_m_milli "
        "FROM fabric_rolls WHERE customer_id = ? AND owner = 'customer' "
        "AND deleted_at IS NULL ORDER BY id", (customer_id,))
    cust["accessories"] = await fetch_all(
        "SELECT id, name, stock_qty_milli, unit FROM accessories "
        "WHERE customer_id = ? AND source = 'customer' AND deleted_at IS NULL", (customer_id,))
    return cust


async def dashboard() -> dict:
    open_orders = await fetch_all(
        """
        SELECT o.id, o.code, o.quantity, o.status, o.delivery_date,
               c.name AS customer_name
        FROM manufacturing_orders o LEFT JOIN customers c ON c.id = o.customer_id
        WHERE o.deleted_at IS NULL AND o.status NOT IN ('delivered','cancelled')
        ORDER BY o.delivery_date IS NULL, o.delivery_date LIMIT 25
        """)
    unpaid = await fetch_all(
        """
        SELECT i.id, i.invoice_no, i.total_cents, i.status, c.name AS customer_name,
               COALESCE((SELECT SUM(amount_cents) FROM payments p
                         WHERE p.invoice_id = i.id AND p.deleted_at IS NULL),0) AS paid_cents
        FROM invoices i LEFT JOIN customers c ON c.id = i.customer_id
        WHERE i.deleted_at IS NULL AND i.status != 'paid'
        ORDER BY i.id DESC LIMIT 25
        """)
    for u in unpaid:
        u["balance_cents"] = (u.get("total_cents") or 0) - (u.get("paid_cents") or 0)
    low_rolls = await fetch_all(
        "SELECT id, roll_no, color, fabric_type, remaining_m_milli FROM fabric_rolls "
        "WHERE deleted_at IS NULL AND remaining_m_milli <= 5000 ORDER BY remaining_m_milli LIMIT 25")
    counts = {
        "customers": await _count("customers"),
        "open_orders": len(open_orders),
        "unpaid_invoices": len(unpaid),
        "samples": await _count("samples"),
    }
    recent_activity = await fetch_all(
        "SELECT ts, actor_name, entity, entity_id, action, summary FROM activity_log "
        "ORDER BY id DESC LIMIT 15")
    return {
        "counts": counts,
        "open_orders": open_orders,
        "unpaid_invoices": unpaid,
        "low_stock_rolls": low_rolls,
        "recent_activity": recent_activity,
    }


async def _count(table: str) -> int:
    row = await fetch_one(f"SELECT COUNT(*) AS c FROM {table} WHERE deleted_at IS NULL")
    return (row or {}).get("c") or 0
