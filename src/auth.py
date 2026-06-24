"""Telegram Login Widget verification + JWT session cookies + role lookup.

Spec: https://core.telegram.org/widgets/login#checking-authorization
Auth pattern adapted from finance-web; extended with ERP role gating.
"""
import hashlib
import hmac
import time

import aiosqlite
from fastapi import Cookie, Depends, HTTPException

from src import config
from src.db import db_uri

ALGORITHM = "HS256"
SESSION_DAYS = 30


def verify_telegram_hash(data: dict) -> bool:
    """Verify the hash sent by the Telegram Login Widget."""
    received_hash = data.get("hash", "")
    check_data = {k: v for k, v in data.items() if k != "hash"}
    data_check_string = "\n".join(
        sorted(f"{k}={v}" for k, v in check_data.items())
    )
    secret_key = hashlib.sha256(config.BOT_TOKEN.encode()).digest()
    expected = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if expected != received_hash:
        return False
    auth_date = int(data.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        return False
    return True


def create_session_token(user_id: int) -> str:
    exp = int(time.time()) + SESSION_DAYS * 86400
    return jwt_encode({"user_id": user_id, "exp": exp})


def jwt_encode(payload: dict) -> str:
    from jose import jwt
    return jwt.encode(payload, config.SECRET_KEY, algorithm=ALGORITHM)


def decode_session_token(token: str) -> int:
    """Returns user_id, raises HTTPException(401) on invalid/expired token."""
    from jose import JWTError, jwt
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid session")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid session")


async def get_app_user(tg_user_id: int) -> dict | None:
    """Fetch the active app_user row for a Telegram id."""
    async with aiosqlite.connect(db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM app_users WHERE tg_user_id = ? AND deleted_at IS NULL",
            (tg_user_id,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def is_user_allowed(tg_user_id: int) -> bool:
    """Allowed if they have an active app_user row, or are an ALLOWED_USERS
    bootstrap id (which auto-provisions an admin on first login)."""
    if tg_user_id in config.ALLOWED_USERS:
        return True
    user = await get_app_user(tg_user_id)
    return bool(user and user.get("active"))


def get_current_user(session: str | None = Cookie(default=None)) -> int:
    """FastAPI dependency — returns Telegram user_id from cookie or 401s."""
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return decode_session_token(session)


async def get_role(tg_user_id: int) -> str:
    # Bootstrap owners (ALLOWED_USERS) are always admin — a break-glass account
    # that cannot be locked out, even if their stored role was changed.
    if tg_user_id in config.ALLOWED_USERS:
        return "admin"
    user = await get_app_user(tg_user_id)
    if user:
        return user.get("role") or "sales"
    return "sales"


def require_role(*roles: str):
    """Dependency factory: 403 unless the current user's role is allowed.

    admin always passes.
    """
    async def _dep(user_id: int = Depends(get_current_user)) -> int:
        role = await get_role(user_id)
        if role != "admin" and role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user_id
    return _dep


async def actor_context(tg_user_id: int, request=None) -> dict:
    """Build the actor descriptor threaded into every write for logging."""
    user = await get_app_user(tg_user_id)
    ctx = {
        "actor_user_id": tg_user_id,
        "actor_name": (user or {}).get("name") or (user or {}).get("username"),
        "actor_role": (user or {}).get("role")
        or ("admin" if tg_user_id in config.ALLOWED_USERS else None),
    }
    if request is not None:
        client = getattr(request, "client", None)
        ctx["ip"] = getattr(client, "host", None)
        ctx["user_agent"] = request.headers.get("user-agent")
    return ctx
