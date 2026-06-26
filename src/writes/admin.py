"""Factory reset — wipe all business data + activity log, keep app_users.

For handing the product to a customer as a clean install. Irreversible.
"""
import glob
import os

import aiosqlite

from src import config
from src.db import write_db_uri

# Order matters only loosely (FKs are disabled during the wipe).
WIPE_TABLES = [
    "payments", "invoice_lines", "invoices",
    "inventory_movements", "accessory_surplus",
    "order_cuts", "order_stages", "manufacturing_orders",
    "spec_accessories", "product_specs", "sample_manufacturing",
    "sample_printing", "sample_blueprint", "sample_fabric", "samples",
    "fabric_rolls", "accessories", "suppliers", "customers",
    "activity_log",
]


async def reset_all_data() -> dict:
    counts = {}
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        await db.execute("PRAGMA foreign_keys=OFF")
        for tbl in WIPE_TABLES:
            try:
                cur = await db.execute(f"DELETE FROM {tbl}")
                counts[tbl] = cur.rowcount
            except Exception:  # noqa: BLE001
                pass
        # Reset autoincrement counters so new ids start at 1 ("like new").
        try:
            ph = ",".join("?" for _ in WIPE_TABLES)
            await db.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({ph})", WIPE_TABLES)
        except Exception:  # noqa: BLE001
            pass
        await db.commit()
    # Remove uploaded sample images / blueprint files.
    try:
        for f in glob.glob(os.path.join(config.UPLOAD_DIR, "*")):
            if os.path.isfile(f):
                os.remove(f)
    except Exception:  # noqa: BLE001
        pass
    return {"wiped": counts}
