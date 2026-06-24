"""aiosqlite access to the ERP's own database.

`db_uri()` returns a read-only URI (`?mode=ro`) used by all query helpers.
`write_db_uri()` returns a read-write URI used by `src.writes.*`.
The ERP is the sole owner of this database; WAL mode (set on startup) keeps
concurrent reads and writes safe.
"""
import aiosqlite

from src import config


def db_uri() -> str:
    """Read-only URI — used by query modules."""
    return f"file:{config.DB_PATH}?mode=ro"


def write_db_uri() -> str:
    """Read-write URI — used only by `src.writes.*` and schema setup."""
    return f"file:{config.DB_PATH}"
