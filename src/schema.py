"""Database schema + idempotent migrations for the garment-factory ERP.

The ERP owns its database outright. On startup we:
  1. ensure the data directory exists,
  2. set WAL mode (safe concurrent reads/writes),
  3. apply every migration not yet recorded in `schema_migrations`.

Money is stored as integer piastres (1 EGP = 100). Lengths/quantities that
need fractions are stored in milli-units (e.g. `length_m_milli` = metres x1000)
so all arithmetic stays integer and exact.

Every business table carries `created_at` and a nullable `deleted_at`
(soft delete). `activity_log` is the exception: it is append-only.
"""
import logging
import os

import aiosqlite

from src import config
from src.db import write_db_uri

logger = logging.getLogger(__name__)


MIGRATIONS: list[tuple[str, str]] = [
    # ---- People / access -------------------------------------------------
    ("0001_app_users", """
        CREATE TABLE IF NOT EXISTS app_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_user_id INTEGER NOT NULL UNIQUE,
            name TEXT,
            username TEXT,
            role TEXT NOT NULL DEFAULT 'sales'
              CHECK (role IN ('admin','accountant','production','sales')),
            language TEXT NOT NULL DEFAULT 'ar',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),

    ("0002_customers", """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),

    ("0003_suppliers", """
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            material_types TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),

    # ---- Samples + components -------------------------------------------
    ("0004_samples", """
        CREATE TABLE IF NOT EXISTS samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customers(id),
            code TEXT,
            name TEXT NOT NULL,
            image_path TEXT,
            status TEXT NOT NULL DEFAULT 'draft'
              CHECK (status IN ('draft','approved','archived')),
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
    ("0005_sample_fabric", """
        CREATE TABLE IF NOT EXISTS sample_fabric (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL REFERENCES samples(id),
            fabric_type TEXT,
            qty_milli INTEGER NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT 'meter' CHECK (unit IN ('meter','kg')),
            cost_cents INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT 'factory'
              CHECK (source IN ('customer','factory')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
    ("0006_sample_blueprint", """
        CREATE TABLE IF NOT EXISTS sample_blueprint (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL REFERENCES samples(id),
            design_name TEXT,
            file_path TEXT,
            version TEXT,
            approved_sizes TEXT,
            approved_at TEXT,
            cost_cents INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT 'factory'
              CHECK (source IN ('customer','factory')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
    ("0007_sample_printing", """
        CREATE TABLE IF NOT EXISTS sample_printing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL REFERENCES samples(id),
            print_type TEXT,
            description TEXT,
            cost_cents INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT 'factory'
              CHECK (source IN ('customer','factory')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
    ("0008_sample_manufacturing", """
        CREATE TABLE IF NOT EXISTS sample_manufacturing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL REFERENCES samples(id),
            cut_cost_cents INTEGER NOT NULL DEFAULT 0,
            sew_cost_cents INTEGER NOT NULL DEFAULT 0,
            finish_cost_cents INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),

    # ---- Product spec (BOM) ---------------------------------------------
    ("0009_product_specs", """
        CREATE TABLE IF NOT EXISTS product_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL REFERENCES samples(id),
            fabric_meters_per_piece_milli INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT,
            UNIQUE(sample_id)
        )
    """),
    ("0010_spec_accessories", """
        CREATE TABLE IF NOT EXISTS spec_accessories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL REFERENCES samples(id),
            accessory_id INTEGER NOT NULL REFERENCES accessories(id),
            qty_per_piece_milli INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),

    # ---- Materials -------------------------------------------------------
    ("0011_accessories", """
        CREATE TABLE IF NOT EXISTS accessories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'piece',
            stock_qty_milli INTEGER NOT NULL DEFAULT 0,
            unit_price_cents INTEGER NOT NULL DEFAULT 0,
            source TEXT NOT NULL DEFAULT 'factory'
              CHECK (source IN ('customer','factory')),
            customer_id INTEGER REFERENCES customers(id),
            supplier_id INTEGER REFERENCES suppliers(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
    ("0012_fabric_rolls", """
        CREATE TABLE IF NOT EXISTS fabric_rolls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            color TEXT,
            fabric_type TEXT,
            length_m_milli INTEGER NOT NULL DEFAULT 0,
            remaining_m_milli INTEGER NOT NULL DEFAULT 0,
            owner TEXT NOT NULL DEFAULT 'factory'
              CHECK (owner IN ('customer','factory')),
            customer_id INTEGER REFERENCES customers(id),
            supplier_id INTEGER REFERENCES suppliers(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),

    # ---- Manufacturing orders + production stages -----------------------
    ("0013_manufacturing_orders", """
        CREATE TABLE IF NOT EXISTS manufacturing_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            sample_id INTEGER REFERENCES samples(id),
            order_date TEXT,
            delivery_date TEXT,
            quantity INTEGER NOT NULL DEFAULT 0,
            unit_cost_cents INTEGER,
            est_total_cents INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'new'
              CHECK (status IN ('new','prep','cutting','printing','sewing',
                                'finishing','packing','ready','delivered','cancelled')),
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
    ("0014_order_stages", """
        CREATE TABLE IF NOT EXISTS order_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES manufacturing_orders(id),
            stage TEXT NOT NULL
              CHECK (stage IN ('new','prep','cutting','printing','sewing',
                               'finishing','packing','ready','delivered','cancelled')),
            start_date TEXT,
            end_date TEXT,
            responsible TEXT,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),

    # ---- Inventory -------------------------------------------------------
    ("0015_inventory_movements", """
        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_type TEXT NOT NULL CHECK (item_type IN ('fabric','accessory','packing')),
            item_id INTEGER,
            item_name TEXT,
            owner TEXT NOT NULL DEFAULT 'factory'
              CHECK (owner IN ('customer','factory')),
            customer_id INTEGER REFERENCES customers(id),
            movement_type TEXT NOT NULL
              CHECK (movement_type IN ('add','issue','transfer','return')),
            qty_milli INTEGER NOT NULL DEFAULT 0,
            ref_order_id INTEGER REFERENCES manufacturing_orders(id),
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
    ("0016_accessory_surplus", """
        CREATE TABLE IF NOT EXISTS accessory_surplus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER REFERENCES manufacturing_orders(id),
            accessory_id INTEGER REFERENCES accessories(id),
            customer_id INTEGER REFERENCES customers(id),
            action TEXT NOT NULL CHECK (action IN ('return','store')),
            qty_milli INTEGER NOT NULL DEFAULT 0,
            surplus_date TEXT,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),

    # ---- Invoices + payments --------------------------------------------
    ("0017_invoices", """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            order_id INTEGER REFERENCES manufacturing_orders(id),
            invoice_date TEXT,
            subtotal_cents INTEGER NOT NULL DEFAULT 0,
            discount_cents INTEGER NOT NULL DEFAULT 0,
            tax_cents INTEGER NOT NULL DEFAULT 0,
            total_cents INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'unpaid'
              CHECK (status IN ('unpaid','partial','paid')),
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
    ("0018_invoice_lines", """
        CREATE TABLE IF NOT EXISTS invoice_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL REFERENCES invoices(id),
            description TEXT,
            qty INTEGER NOT NULL DEFAULT 0,
            unit_price_cents INTEGER NOT NULL DEFAULT 0,
            line_total_cents INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
    ("0019_payments", """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            order_id INTEGER REFERENCES manufacturing_orders(id),
            invoice_id INTEGER REFERENCES invoices(id),
            amount_cents INTEGER NOT NULL DEFAULT 0,
            kind TEXT NOT NULL DEFAULT 'progress'
              CHECK (kind IN ('advance','progress','final')),
            payment_date TEXT,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),

    # ---- Activity log (append-only, immutable from the app) -------------
    ("0020_activity_log", """
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            actor_user_id INTEGER,
            actor_name TEXT,
            actor_role TEXT,
            entity TEXT NOT NULL,
            entity_id INTEGER,
            action TEXT NOT NULL,
            before_json TEXT,
            after_json TEXT,
            summary TEXT,
            ip TEXT,
            user_agent TEXT
        )
    """),

    # ---- Indexes ---------------------------------------------------------
    ("0021_idx_activity_main",
     "CREATE INDEX IF NOT EXISTS idx_activity_main ON activity_log(ts DESC, id DESC)"),
    ("0022_idx_activity_entity",
     "CREATE INDEX IF NOT EXISTS idx_activity_entity ON activity_log(entity, entity_id)"),
    ("0023_idx_activity_actor",
     "CREATE INDEX IF NOT EXISTS idx_activity_actor ON activity_log(actor_user_id)"),
    ("0024_idx_orders_customer",
     "CREATE INDEX IF NOT EXISTS idx_orders_customer ON manufacturing_orders(customer_id, status)"),
    ("0025_idx_stages_order",
     "CREATE INDEX IF NOT EXISTS idx_stages_order ON order_stages(order_id, id)"),
    ("0026_idx_payments_order",
     "CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id, invoice_id)"),
    ("0027_idx_invoices_customer",
     "CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id, status)"),
    ("0028_idx_inventory_item",
     "CREATE INDEX IF NOT EXISTS idx_inventory_item ON inventory_movements(item_type, item_id, owner)"),
]


async def apply_migrations() -> None:
    """Create the DB (if missing), enable WAL, and apply pending migrations."""
    os.makedirs(os.path.dirname(config.DB_PATH) or ".", exist_ok=True)
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)

    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.commit()

        for name, stmt in MIGRATIONS:
            async with db.execute(
                "SELECT 1 FROM schema_migrations WHERE name = ?", (name,)
            ) as cur:
                if await cur.fetchone():
                    continue
            try:
                await db.execute(stmt)
                await db.execute(
                    "INSERT INTO schema_migrations (name) VALUES (?)", (name,)
                )
                logger.info("Applied migration: %s", name)
            except Exception as e:
                logger.warning("Migration %s skipped or failed: %s", name, e)
        await db.commit()
