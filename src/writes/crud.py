"""Generic audited CRUD over a single table.

Every mutation captures a before/after snapshot and writes an activity_log
row in the SAME transaction, so a change can never be persisted without its
audit entry. Module-specific write files use a `Table` instance for standard
operations and fall back to custom SQL (still calling `audit.log`) only when
they need extra logic (computed totals, cost rules, stock side-effects).
"""
from typing import Any, Optional

import aiosqlite

from src.db import write_db_uri
from src.writes import audit


class Table:
    def __init__(
        self,
        name: str,
        entity: str,
        columns: tuple[str, ...],
        *,
        required: tuple[str, ...] = (),
        label: Optional[str] = None,
    ):
        self.name = name
        self.entity = entity
        self.columns = columns
        self.required = required
        # column used to build a human summary (e.g. "name")
        self.label = label

    # ---- helpers --------------------------------------------------------
    async def _snapshot(self, db: aiosqlite.Connection, row_id: int) -> Optional[dict]:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"SELECT * FROM {self.name} WHERE id = ?", (row_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    def _filter(self, fields: dict) -> dict:
        return {k: v for k, v in fields.items() if k in self.columns}

    def _summary(self, snap: Optional[dict]) -> Optional[str]:
        if snap and self.label and snap.get(self.label):
            return f"{self.entity}: {snap[self.label]}"
        return None

    # ---- reads ----------------------------------------------------------
    async def get(self, row_id: int) -> Optional[dict]:
        async with aiosqlite.connect(write_db_uri(), uri=True) as db:
            return await self._snapshot(db, row_id)

    # ---- writes ---------------------------------------------------------
    async def create(self, actor: Optional[dict], **fields) -> int:
        data = self._filter(fields)
        for r in self.required:
            v = data.get(r)
            if v is None or (isinstance(v, str) and not v.strip()):
                raise ValueError(f"{r} is required")
        cols = list(data.keys())
        placeholders = ", ".join("?" for _ in cols)
        col_sql = ", ".join(cols)
        async with aiosqlite.connect(write_db_uri(), uri=True) as db:
            cur = await db.execute(
                f"INSERT INTO {self.name} ({col_sql}) VALUES ({placeholders})",
                [data[c] for c in cols],
            )
            row_id = cur.lastrowid
            after = await self._snapshot(db, row_id)
            await audit.log(
                actor=actor, entity=self.entity, entity_id=row_id,
                action="create", before=None, after=after,
                summary=self._summary(after), db=db,
            )
            await db.commit()
            return row_id

    async def update(self, actor: Optional[dict], row_id: int, **fields) -> Optional[dict]:
        data = self._filter(fields)
        if not data:
            return await self.get(row_id)
        set_sql = ", ".join(f"{c} = ?" for c in data)
        values = [data[c] for c in data] + [row_id]
        async with aiosqlite.connect(write_db_uri(), uri=True) as db:
            before = await self._snapshot(db, row_id)
            if before is None:
                return None
            await db.execute(
                f"UPDATE {self.name} SET {set_sql} WHERE id = ? AND deleted_at IS NULL",
                values,
            )
            after = await self._snapshot(db, row_id)
            await audit.log(
                actor=actor, entity=self.entity, entity_id=row_id,
                action="update", before=before, after=after,
                summary=self._summary(after), db=db,
            )
            await db.commit()
            return after

    async def soft_delete(self, actor: Optional[dict], row_id: int) -> bool:
        async with aiosqlite.connect(write_db_uri(), uri=True) as db:
            before = await self._snapshot(db, row_id)
            if before is None or before.get("deleted_at"):
                return False
            await db.execute(
                f"UPDATE {self.name} SET deleted_at = datetime('now') WHERE id = ?",
                (row_id,),
            )
            after = await self._snapshot(db, row_id)
            await audit.log(
                actor=actor, entity=self.entity, entity_id=row_id,
                action="delete", before=before, after=after,
                summary=self._summary(before), db=db,
            )
            await db.commit()
            return True

    async def restore(self, actor: Optional[dict], row_id: int) -> bool:
        async with aiosqlite.connect(write_db_uri(), uri=True) as db:
            before = await self._snapshot(db, row_id)
            if before is None or not before.get("deleted_at"):
                return False
            await db.execute(
                f"UPDATE {self.name} SET deleted_at = NULL WHERE id = ?",
                (row_id,),
            )
            after = await self._snapshot(db, row_id)
            await audit.log(
                actor=actor, entity=self.entity, entity_id=row_id,
                action="restore", before=before, after=after,
                summary=self._summary(after), db=db,
            )
            await db.commit()
            return True
