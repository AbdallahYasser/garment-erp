"""Shared fixtures — a fresh temp DB per test module + an authed admin client."""
import asyncio
import os
import tempfile

import aiosqlite
import pytest

# Configure env BEFORE importing the app/config.
_TMP = tempfile.mkdtemp()
os.environ.setdefault("DB_PATH", os.path.join(_TMP, "erp_test.db"))
os.environ.setdefault("UPLOAD_DIR", os.path.join(_TMP, "uploads"))
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALLOWED_USERS", "111")
os.environ.setdefault("BOT_USERNAME", "test_bot")


def make_test_user(tg_user_id: int, role: str = "sales") -> None:
    """Insert an active user directly into the test DB.

    Required for tests that use non-ALLOWED_USERS ids: Fix 1 now checks the
    DB on every request, so a token for a user who has no DB row returns 401.
    """
    from src import config

    async def _insert():
        async with aiosqlite.connect(config.DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO app_users "
                "(tg_user_id, name, role, active) VALUES (?, ?, ?, 1)",
                (tg_user_id, f"TestUser{tg_user_id}", role),
            )
            await db.commit()

    asyncio.run(_insert())


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from src.main import app, auth
    with TestClient(app) as c:
        # Admin bootstrap user (111 is in ALLOWED_USERS).
        c.cookies.set("session", auth.create_session_token(111))
        yield c


@pytest.fixture()
def anon_client():
    from fastapi.testclient import TestClient
    from src.main import app
    with TestClient(app) as c:
        yield c
