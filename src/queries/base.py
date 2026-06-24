"""Generic read helpers shared by query modules."""
from typing import Any, Optional

import aiosqlite

from src.db import db_uri


async def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, params) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def fetch_one(sql: str, params: tuple = ()) -> Optional[dict]:
    async with aiosqlite.connect(db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, params) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def scalar(sql: str, params: tuple = ()) -> Any:
    async with aiosqlite.connect(db_uri(), uri=True) as db:
        async with db.execute(sql, params) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


class Reader:
    """Standard list / get / search for one table."""

    def __init__(self, name: str, *, search_cols: tuple[str, ...] = ()):
        self.name = name
        self.search_cols = search_cols

    async def list(
        self,
        *,
        include_deleted: bool = False,
        q: Optional[str] = None,
        order: str = "id DESC",
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict]:
        where = [] if include_deleted else ["deleted_at IS NULL"]
        params: list[Any] = []
        if q and self.search_cols:
            like = "%" + q.strip() + "%"
            ors = " OR ".join(f"{c} LIKE ?" for c in self.search_cols)
            where.append(f"({ors})")
            params.extend([like] * len(self.search_cols))
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        params.extend([limit, offset])
        return await fetch_all(
            f"SELECT * FROM {self.name} {where_sql} ORDER BY {order} LIMIT ? OFFSET ?",
            tuple(params),
        )

    async def get(self, row_id: int) -> Optional[dict]:
        return await fetch_one(f"SELECT * FROM {self.name} WHERE id = ?", (row_id,))
