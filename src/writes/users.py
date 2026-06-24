"""app_users management — login provisioning + role/language admin."""
from typing import Optional

import aiosqlite

from src import config
from src.db import write_db_uri
from src.writes import audit

VALID_ROLES = ("admin", "accountant", "production", "sales")


async def ensure_user_on_login(tg_user_id: int, name: Optional[str],
                               username: Optional[str]) -> dict:
    """Called at login. Creates the row if missing.

    The very first user (or any ALLOWED_USERS bootstrap id) becomes admin so
    the system is never locked out; subsequent users default to 'sales' and
    must be promoted by an admin.
    """
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM app_users WHERE tg_user_id = ?", (tg_user_id,)
        ) as cur:
            row = await cur.fetchone()

        if row:
            # Refresh display fields, keep role/active as-is.
            await db.execute(
                "UPDATE app_users SET name = COALESCE(?, name), "
                "username = COALESCE(?, username) WHERE tg_user_id = ?",
                (name, username, tg_user_id),
            )
            await db.commit()
            async with db.execute(
                "SELECT * FROM app_users WHERE tg_user_id = ?", (tg_user_id,)
            ) as cur:
                return dict(await cur.fetchone())

        async with db.execute("SELECT COUNT(*) FROM app_users") as cur:
            is_first = (await cur.fetchone())[0] == 0
        role = "admin" if (is_first or tg_user_id in config.ALLOWED_USERS) else "sales"

        cur = await db.execute(
            "INSERT INTO app_users (tg_user_id, name, username, role) "
            "VALUES (?, ?, ?, ?)",
            (tg_user_id, name, username, role),
        )
        new_id = cur.lastrowid
        await audit.log(
            actor={"actor_user_id": tg_user_id, "actor_name": name, "actor_role": role},
            entity="app_users", entity_id=new_id, action="create",
            after={"tg_user_id": tg_user_id, "name": name, "role": role},
            summary=f"app_user provisioned: {name or tg_user_id} ({role})", db=db,
        )
        await db.commit()
        async with db.execute(
            "SELECT * FROM app_users WHERE id = ?", (new_id,)
        ) as cur:
            return dict(await cur.fetchone())


async def set_role(actor: dict, user_row_id: int, role: str) -> bool:
    if role not in VALID_ROLES:
        raise ValueError("invalid role")
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM app_users WHERE id = ?", (user_row_id,)
        ) as cur:
            before = await cur.fetchone()
        if not before:
            return False
        before = dict(before)
        await db.execute(
            "UPDATE app_users SET role = ? WHERE id = ?", (role, user_row_id)
        )
        await audit.log(
            actor=actor, entity="app_users", entity_id=user_row_id, action="update",
            before={"role": before.get("role")}, after={"role": role},
            summary=f"role changed: {before.get('name') or before.get('tg_user_id')} -> {role}",
            db=db,
        )
        await db.commit()
        return True


async def set_active(actor: dict, user_row_id: int, active: bool) -> bool:
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        cur = await db.execute(
            "UPDATE app_users SET active = ? WHERE id = ?",
            (1 if active else 0, user_row_id),
        )
        if cur.rowcount == 0:
            return False
        await audit.log(
            actor=actor, entity="app_users", entity_id=user_row_id, action="update",
            after={"active": 1 if active else 0},
            summary=f"user {'activated' if active else 'deactivated'}", db=db,
        )
        await db.commit()
        return True


async def set_language(actor: dict, tg_user_id: int, language: str) -> bool:
    if language not in ("ar", "en"):
        raise ValueError("invalid language")
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        cur = await db.execute(
            "UPDATE app_users SET language = ? WHERE tg_user_id = ?",
            (language, tg_user_id),
        )
        await db.commit()
        return cur.rowcount > 0
