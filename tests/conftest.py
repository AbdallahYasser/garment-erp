"""Shared fixtures — a fresh temp DB per test module + an authed admin client."""
import os
import tempfile

import pytest

# Configure env BEFORE importing the app/config.
_TMP = tempfile.mkdtemp()
os.environ.setdefault("DB_PATH", os.path.join(_TMP, "erp_test.db"))
os.environ.setdefault("UPLOAD_DIR", os.path.join(_TMP, "uploads"))
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALLOWED_USERS", "111")
os.environ.setdefault("BOT_USERNAME", "test_bot")


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
