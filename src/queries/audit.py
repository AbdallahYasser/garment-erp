"""Activity-log queries — global feed + per-record history with diffs."""
import json
from typing import Any, Optional

from src.queries.base import fetch_all, scalar


def _decode(s: Optional[str]) -> Optional[dict]:
    if not s:
        return None
    try:
        return json.loads(s)
    except (TypeError, ValueError):
        return None


def _attach_diff(rows: list[dict]) -> list[dict]:
    for r in rows:
        before = _decode(r.pop("before_json", None))
        after = _decode(r.pop("after_json", None))
        r["before"] = before
        r["after"] = after
        if r.get("action") == "update" and before and after:
            d: dict[str, Any] = {}
            for k, av in after.items():
                bv = before.get(k)
                if av != bv:
                    d[k] = {"from": bv, "to": av}
            r["diff"] = d
        else:
            r["diff"] = None
    return rows


async def search(
    *,
    actor_user_id: Optional[int] = None,
    entity: Optional[str] = None,
    entity_id: Optional[int] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    where: list[str] = []
    params: list[Any] = []
    if actor_user_id is not None:
        where.append("actor_user_id = ?"); params.append(actor_user_id)
    if entity:
        where.append("entity = ?"); params.append(entity)
    if entity_id is not None:
        where.append("entity_id = ?"); params.append(entity_id)
    if action:
        where.append("action = ?"); params.append(action)
    if date_from:
        where.append("ts >= ?"); params.append(date_from)
    if date_to:
        where.append("ts <= ?"); params.append(date_to)
    if q:
        like = "%" + q.strip() + "%"
        where.append("(summary LIKE ? OR actor_name LIKE ? OR before_json LIKE ? OR after_json LIKE ?)")
        params.extend([like, like, like, like])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    total = await scalar(f"SELECT COUNT(*) FROM activity_log {where_sql}", tuple(params))

    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    rows = await fetch_all(
        f"""
        SELECT id, ts, actor_user_id, actor_name, actor_role, entity, entity_id,
               action, before_json, after_json, summary, ip, user_agent
        FROM activity_log {where_sql}
        ORDER BY ts DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        tuple(params) + (page_size, (page - 1) * page_size),
    )
    return {
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "rows": _attach_diff(rows),
    }


async def history_for(entity: str, entity_id: int) -> list[dict]:
    """Full change timeline for a single record, newest first."""
    rows = await fetch_all(
        """
        SELECT id, ts, actor_user_id, actor_name, actor_role, entity, entity_id,
               action, before_json, after_json, summary
        FROM activity_log
        WHERE entity = ? AND entity_id = ?
        ORDER BY ts DESC, id DESC
        """,
        (entity, entity_id),
    )
    return _attach_diff(rows)
