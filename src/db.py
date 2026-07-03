"""aiosqlite access to the ERP's own database.

`db_uri()` returns a read-only URI (`?mode=ro`) used by all query helpers.
`write_db_uri()` returns a read-write URI used by schema setup.
`write_conn()` is the async context manager every write module must use —
it opens a read-write connection and immediately sets PRAGMA foreign_keys=ON,
which SQLite requires on every connection (it does not persist across closes).
The ERP is the sole owner of this database; WAL mode (set on startup) keeps
concurrent reads and writes safe.
"""
from contextlib import asynccontextmanager

import aiosqlite

from src import config


def db_uri() -> str:
    """Read-only URI — used by query modules."""
    return f"file:{config.DB_PATH}?mode=ro"


def write_db_uri() -> str:
    """Read-write URI — used by write_conn() and schema setup."""
    return f"file:{config.DB_PATH}"


@asynccontextmanager
async def write_conn():
    """Read-write connection with PRAGMA foreign_keys=ON.

    SQLite resets foreign-key enforcement on every new connection, so this
    context manager is the single place that enforces it. All write modules
    must use this instead of aiosqlite.connect(write_db_uri()) directly.
    """
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        yield db
