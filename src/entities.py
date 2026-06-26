"""Registry of all standard CRUD entities.

Each entry binds a table to its writable columns, the roles allowed to mutate
it, search columns, a label column (for activity summaries) and an optional
`transform` applied to the field dict before create/update (used e.g. to force
customer-supplied component costs to zero, per the FRS).

main.py generates uniform REST routes from this registry; every mutation goes
through `crud.Table`, so all of them are activity-logged automatically.
"""
from typing import Callable, Optional

from src.queries.base import Reader
from src.writes.crud import Table


def _zero_cost_if_customer(fields: dict) -> dict:
    """FRS rule: when a component is supplied by the customer, its cost is 0."""
    if fields.get("source") == "customer":
        for c in ("cost_cents",):
            if c in fields:
                fields[c] = 0
    return fields


class Entity:
    def __init__(
        self,
        name: str,
        table: str,
        columns: tuple[str, ...],
        *,
        roles: tuple[str, ...],
        required: tuple[str, ...] = (),
        search_cols: tuple[str, ...] = (),
        label: Optional[str] = None,
        transform: Optional[Callable[[dict], dict]] = None,
    ):
        self.name = name
        self.roles = roles
        self.transform = transform
        self.table = Table(table, name, columns, required=required, label=label)
        self.reader = Reader(table, search_cols=search_cols)


REGISTRY: dict[str, Entity] = {}


def _reg(e: Entity) -> Entity:
    REGISTRY[e.name] = e
    return e


# --- People / parties ----------------------------------------------------
_reg(Entity("customers", "customers",
    ("name", "company", "phone", "email", "address", "notes"),
    roles=("sales",), required=("name",), label="name",
    search_cols=("name", "company", "phone", "email")))

_reg(Entity("suppliers", "suppliers",
    ("name", "phone", "address", "material_types", "notes"),
    roles=("production",), required=("name",), label="name",
    search_cols=("name", "phone", "material_types")))

# --- Samples + components ------------------------------------------------
_reg(Entity("samples", "samples",
    ("customer_id", "code", "name", "image_path", "status", "notes"),
    roles=("sales",), required=("name",), label="name",
    search_cols=("name", "code")))

_reg(Entity("sample_fabric", "sample_fabric",
    ("sample_id", "fabric_type", "qty_milli", "unit", "cost_cents", "source"),
    roles=("sales",), required=("sample_id",), label="fabric_type",
    transform=_zero_cost_if_customer))

_reg(Entity("sample_blueprint", "sample_blueprint",
    ("sample_id", "design_name", "file_path", "version", "approved_sizes",
     "approved_at", "cost_cents", "source"),
    roles=("sales",), required=("sample_id",), label="design_name",
    transform=_zero_cost_if_customer))

_reg(Entity("sample_printing", "sample_printing",
    ("sample_id", "print_type", "description", "cost_cents", "source"),
    roles=("sales",), required=("sample_id",), label="print_type",
    transform=_zero_cost_if_customer))

_reg(Entity("sample_manufacturing", "sample_manufacturing",
    ("sample_id", "cost_cents"),
    roles=("sales",), required=("sample_id",)))

# --- Product spec / BOM --------------------------------------------------
_reg(Entity("product_specs", "product_specs",
    ("sample_id", "fabric_meters_per_piece_milli"),
    roles=("production", "sales"), required=("sample_id",)))

_reg(Entity("spec_accessories", "spec_accessories",
    ("sample_id", "accessory_id", "qty_per_piece_milli"),
    roles=("production", "sales"), required=("sample_id", "accessory_id")))

# --- Materials -----------------------------------------------------------
_reg(Entity("accessories", "accessories",
    ("name", "unit", "stock_qty_milli", "unit_price_cents", "source",
     "customer_id", "supplier_id"),
    roles=("production",), required=("name",), label="name",
    search_cols=("name",)))

_reg(Entity("fabric_rolls", "fabric_rolls",
    ("roll_no", "color", "fabric_type", "length_m_milli", "remaining_m_milli",
     "owner", "customer_id", "supplier_id"),
    roles=("production",), label="roll_no",
    search_cols=("roll_no", "color", "fabric_type")))

# --- Inventory -----------------------------------------------------------
_reg(Entity("inventory_movements", "inventory_movements",
    ("item_type", "item_id", "item_name", "owner", "customer_id",
     "movement_type", "qty_milli", "ref_order_id", "note"),
    roles=("production",), required=("item_type", "movement_type"),
    label="item_name", search_cols=("item_name", "note")))

_reg(Entity("accessory_surplus", "accessory_surplus",
    ("order_id", "accessory_id", "customer_id", "action", "qty_milli",
     "surplus_date", "note"),
    roles=("production",), required=("action",)))

# --- Order stages (orders/invoices/payments have custom routes) ----------
_reg(Entity("order_stages", "order_stages",
    ("order_id", "stage", "start_date", "end_date", "responsible", "notes"),
    roles=("production",), required=("order_id", "stage"), label="stage"))

_reg(Entity("invoice_lines", "invoice_lines",
    ("invoice_id", "description", "qty", "unit_price_cents", "line_total_cents"),
    roles=("accountant",), required=("invoice_id",), label="description"))
