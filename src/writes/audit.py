"""Central activity log — every change by anyone (staff and admin) is recorded.

`log()` is the single append point. It is called by the generic CRUD helper
(`src.writes.crud.Table`) for every create/update/delete/restore, and directly
for non-row events (login/logout, exports, uploads, stage changes, payments,
danger actions). The table is append-only — there is intentionally no update
or delete path here, so the trail is immutable from the application.
"""
import json
from datetime import datetime, timezone
from typing import Any, Optional

import aiosqlite

from src.db import write_db_uri


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dump(obj: Optional[dict]) -> Optional[str]:
    return json.dumps(obj, ensure_ascii=False, default=str) if obj is not None else None


async def log(
    *,
    actor: Optional[dict],
    entity: str,
    action: str,
    entity_id: Optional[int] = None,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
    summary: Optional[str] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: Optional[aiosqlite.Connection] = None,
) -> None:
    """Append one row to activity_log.

    `actor` is the dict from `auth.actor_context()` ({actor_user_id, actor_name,
    actor_role}). Passing an open `db` connection reuses the caller's
    transaction; otherwise a short-lived connection is opened.
    """
    actor = actor or {}
    params = (
        _now_utc_iso(),
        actor.get("actor_user_id"),
        actor.get("actor_name"),
        actor.get("actor_role"),
        entity,
        entity_id,
        action,
        _dump(before),
        _dump(after),
        summary,
        ip or actor.get("ip"),
        user_agent or actor.get("user_agent"),
    )
    sql = """
        INSERT INTO activity_log
          (ts, actor_user_id, actor_name, actor_role, entity, entity_id,
           action, before_json, after_json, summary, ip, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    if db is not None:
        await db.execute(sql, params)
        return
    async with aiosqlite.connect(write_db_uri(), uri=True) as conn:
        await conn.execute(sql, params)
        await conn.commit()


def diff(before: Optional[dict], after: Optional[dict]) -> dict[str, Any]:
    """Field-level diff used for human-readable summaries and the UI."""
    out: dict[str, Any] = {}
    if not before or not after:
        return out
    for k, av in after.items():
        bv = before.get(k)
        if av != bv:
            out[k] = {"from": bv, "to": av}
    return out
