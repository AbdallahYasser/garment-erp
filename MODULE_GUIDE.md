# Module Guide — How to Add a New Module to the Garment ERP

**Audience:** a developer (or AI session) adding a new module to this system.
**Rule zero:** the result will be code-reviewed against the checklist at the end
of this document. Follow the existing patterns exactly — do not introduce new
frameworks, build steps, ORMs, or dependencies. If you think something in this
guide is wrong for your case, stop and ask before deviating.

---

## 1. The system in five minutes

```
Browser (vanilla-JS SPA, src/static/app.js)
   │  fetch /api/...  (JWT session cookie, httpOnly)
   ▼
FastAPI (src/main.py)
   │  auth.require_role(...) / auth.get_current_user   ← role gate
   │  rate_limit("write", user_id)                     ← on every mutation
   ▼
writes/*  (mutations)          queries/*  (reads)
   │  crud.Table or custom SQL    │  Reader or custom SQL
   │  audit.log(..., db=db)  ←──  every mutation logs in the SAME transaction
   ▼
SQLite (WAL) — the app owns the DB; schema.py applies idempotent
migrations on startup. Soft delete everywhere (`deleted_at`).
```

Key files:

| File | Role |
|---|---|
| `src/schema.py` | ALL tables + migrations (numbered, idempotent, append-only list) |
| `src/entities.py` | registry of standard CRUD entities → REST routes are generated |
| `src/writes/crud.py` | generic audited create/update/soft-delete/restore |
| `src/writes/audit.py` | `log()` — the ONLY way anything is written to `activity_log` |
| `src/writes/<module>.py` | custom mutations (computed totals, stock side-effects) |
| `src/queries/base.py` | `fetch_all/fetch_one/scalar` + generic `Reader` |
| `src/queries/<module>.py` | custom reads (detail views, joins, aggregates) |
| `src/queries/lookups.py` | dropdown data (`/api/lookups`) + customer 360 + dashboard |
| `src/main.py` | routes: generated CRUD (top) + custom endpoints per module |
| `src/static/app.js` | the whole frontend: i18n, `ENTITIES` config, `NAV`, view router |

## 2. Golden rules (non-negotiable)

1. **Money is integer piastres** — column names end in `_cents` (1 EGP = 100).
   Never store or compute with floats. The frontend converts: field type
   `money` multiplies by 100 on save, divides by 100 on display.
2. **Fractional quantities are integer milli-units** — columns end in `_milli`
   (×1000). Frontend field type `milli` handles the conversion.
3. **Dates are TEXT** in ISO format (`YYYY-MM-DD` or `datetime('now')`).
4. **Every business table** has `id INTEGER PRIMARY KEY AUTOINCREMENT`,
   `created_at TEXT NOT NULL DEFAULT (datetime('now'))`, `deleted_at TEXT`.
   Delete = set `deleted_at`; every read filters `deleted_at IS NULL`.
5. **Every mutation is audited in the same transaction.** Either it goes
   through `crud.Table` (automatic), or your custom write calls
   `await audit.log(..., db=db)` **before** `await db.commit()`. Never
   INSERT into `activity_log` directly; never commit without the log row.
6. **Every mutation endpoint** has `rate_limit("write", user_id)` and a
   `require_role(...)` dependency. Roles are `admin / accountant /
   production / sales`; admin passes every check automatically — never add
   special admin handling yourself.
7. **Domain validation raises `ValueError`** in `writes/*`; route handlers
   convert it: `except ValueError as e: raise HTTPException(400, str(e))`.
   Any `int(...)` cast of request data must be inside the `try`.
8. **Bilingual or it doesn't ship.** Every visible label gets a key in BOTH
   `I18N.ar` and `I18N.en` in `app.js`. Arabic is the primary language (RTL).
9. **Escape everything** you render: wrap user data in `esc(...)` in any
   HTML template string.
10. **Update `REQUIREMENTS.md`** — add/extend the module's section under
    "Functional Requirements" AND append a change-log entry. This is a
    standing project rule; the review will reject the PR without it.
11. **Never push to `main`.** `git push` to `main` auto-deploys to
    production via Coolify. Work on a feature branch
    (`feature/<module-name>`), open a PR, and wait for review.
12. **Run the checks** before handing over:
    `python -m pytest` (all green) and `node --check src/static/app.js`.

## 3. Decide your path: registry entity vs custom module

**Path A — registry entity** (~30 lines total). Use when the module is a
plain table: create/edit/soft-delete rows, list with search/filter/sort,
no side effects on other tables, no computed totals.
Examples in the codebase: `customers`, `suppliers`, `accessories`.

**Path B — custom module.** Use when a write must do MORE than change its own
row: computed/derived totals, stock adjustments, status recomputation,
multi-table transactions, workflow stages. Examples: orders
(`writes/orders.py`), invoices (`writes/invoices.py`), payments
(`writes/payments.py`).

Most modules are Path A. If only one or two operations are special, do
Path A for the base entity + a small Path B write module for the special
operations (see how `fabric_rolls` is a registry entity but has a custom
`/api/fabric_rolls/lot` route backed by `writes/rolls.py`).

---

## 4. Path A — step by step

Worked example throughout: a **`machines`** module (factory machines with
maintenance cost tracking). Adapt names to your module.

### Step A1 — Migration (`src/schema.py`)

Append to the END of the `MIGRATIONS` list. Never edit an existing
migration — they already ran in production. Use the next free number.

```python
    ("0038_machines", """
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            machine_type TEXT,
            status TEXT NOT NULL DEFAULT 'working'
              CHECK (status IN ('working','maintenance','broken')),
            purchase_date TEXT,
            purchase_cost_cents INTEGER NOT NULL DEFAULT 0,
            supplier_id INTEGER REFERENCES suppliers(id),
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            deleted_at TEXT
        )
    """),
```

Conventions: `CHECK` constraints for enum-like columns; `REFERENCES` for
FKs; `_cents` / `_milli` suffixes; add an index migration only if the table
will be queried by a non-id column at scale (see `0035_idx_order_cuts`).

### Step A2 — Register the entity (`src/entities.py`)

```python
_reg(Entity("machines", "machines",
    ("name", "machine_type", "status", "purchase_date",
     "purchase_cost_cents", "supplier_id", "notes"),
    roles=("production",), required=("name",), label="name",
    search_cols=("name", "machine_type")))
```

- `columns` = the writable columns ONLY (never `id/created_at/deleted_at`).
- `roles` = the non-admin roles allowed to mutate (reads are open to all
  logged-in users).
- `label` = column used in audit summaries.
- `transform` = optional dict→dict hook applied before create/update (see
  `_zero_cost_if_customer` for the pattern). Use it for field-level business
  rules; raise nothing here — normalization only.

**That's the whole backend.** `main.py` generates
`GET/POST /api/machines`, `GET/PUT/DELETE /api/machines/{id}`,
`POST .../restore`, `GET .../history` — all audited, role-gated,
rate-limited.

### Step A3 — Lookups (only if other forms need a dropdown of your rows)

Add a lightweight list to `all_lookups()` in `src/queries/lookups.py`:

```python
        "machines": await fetch_all(
            "SELECT id, name FROM machines WHERE deleted_at IS NULL ORDER BY name"),
```

Frontend `select` fields with `lookup: "machines"` will then just work.

### Step A4 — Frontend (`src/static/app.js`) — four edits

**(1) i18n** — add every new label to BOTH `I18N.ar` and `I18N.en`:

```js
// in I18N.ar:
machines: "الماكينات", machine_type: "نوع الماكينة", purchase_cost: "تكلفة الشراء",
purchase_date: "تاريخ الشراء", working: "تعمل", maintenance: "صيانة", broken: "معطلة",
// in I18N.en:
machines: "Machines", machine_type: "Machine type", purchase_cost: "Purchase cost",
purchase_date: "Purchase date", working: "Working", maintenance: "Maintenance", broken: "Broken",
```

Reuse existing keys (`name`, `status`, `supplier`, `notes`, `sort_newest`,
`sort_name`…) — do not duplicate them.

**(2) `ENTITIES` config** — drives the table, the form, and the controls bar:

```js
  machines: { roles: ["production"], label: "machines", search: true,
    columns: ["name", "machine_type", "status", "purchase_cost_cents:money"],
    fields: [
      { k: "name", t: "name", type: "text", req: true },
      { k: "machine_type", t: "machine_type", type: "text" },
      { k: "status", t: "status", type: "select",
        options: [["working", "working"], ["maintenance", "maintenance"], ["broken", "broken"]] },
      { k: "purchase_date", t: "purchase_date", type: "date" },
      { k: "purchase_cost_cents", t: "purchase_cost", type: "money" },
      { k: "supplier_id", t: "supplier", type: "select", lookup: "suppliers" },
      { k: "notes", t: "notes", type: "textarea", full: true },
    ],
    controls: {
      filters: [
        { id: "status", label: "status",
          options: [["working", "working"], ["maintenance", "maintenance"], ["broken", "broken"]],
          get: (o) => o.status },
      ],
      sorts: [
        { v: "newest", label: "sort_newest", cmp: (a, b) => b.id - a.id },
        { v: "name", label: "sort_name", cmp: (a, b) => String(a.name || "").localeCompare(String(b.name || "")) },
      ],
    } },
```

Field type reference:

| type | input | conversion on save |
|---|---|---|
| `text` | text input | as-is (`""` → `null`) |
| `textarea` | multi-line | as-is |
| `num` | number | `parseInt` |
| `money` | number (EGP) | ×100 → piastres |
| `milli` | number | ×1000 → milli-units |
| `date` | date picker | ISO string |
| `select` + `options: [[value, i18nKey],…]` | fixed dropdown | string (or int if key in `LOOKUP_INT_KEYS`) |
| `select` + `lookup: "customers"` | dropdown from `/api/lookups` | `parseInt` |
| `sizes` | S/M/L/XL/XXL chips | comma-joined string |

Column spec `"col:money"` / `"col:milli"` formats list cells; `status`,
`source`, `owner` columns render as colored tags automatically.
`full: true` makes a form field span both columns. If you add a new
FK field name not in `LOOKUP_INT_KEYS`, append it there.

**(3) `NAV`** — add the section to the right group:

```js
  { group: "grp_production", items: [ ..., { id: "machines", icon: "🛠️" }] },
```

(Admin-only sections get `admin: true`.)

**(4) Router** — nothing to do for Path A: `renderView` falls through to the
generic `renderEntity(view, id)` for any id in `ENTITIES`.

### Step A5 — Tests (`tests/`)

Add `tests/test_<module>.py`. `conftest.py` gives you `client` (authed admin
on a fresh temp DB) and `anon_client`. Minimum bar:

```python
def test_machines_crud_and_audit(client):
    r = client.post("/api/machines", json={"name": "Juki 8700", "purchase_cost_cents": 1500000})
    assert r.status_code == 201
    mid = r.json()["id"]

    r = client.put(f"/api/machines/{mid}", json={"status": "maintenance"})
    assert r.json()["status"] == "maintenance"

    assert client.delete(f"/api/machines/{mid}").status_code == 204
    assert all(row["id"] != mid for row in client.get("/api/machines").json()["rows"])

    # audit trail exists for the record (admin history endpoint)
    hist = client.get(f"/api/machines/{mid}/history").json()["history"]
    assert [h["action"] for h in hist] == ["delete", "update", "create"]

def test_machines_requires_name(client):
    assert client.post("/api/machines", json={"machine_type": "x"}).status_code == 400
```

Also test any `transform` rule and any role restriction that matters
(see `tests/test_roles.py` for the role-client pattern).

### Step A6 — REQUIREMENTS.md

- Add a `### 4.x <Module>` section describing fields + behavior.
- Append a numbered entry to `## 8. Change Log`.

---

## 5. Path B — custom module

Read `src/writes/invoices.py` (simplest) then `src/writes/orders.py`
(hardest) before writing anything. The shape:

### B1 — Write module template (`src/writes/<module>.py`)

```python
"""<Module> writes — <one line on what's special>."""
from typing import Optional

import aiosqlite

from src.db import write_db_uri
from src.writes import audit


async def create_thing(actor: dict, *, customer_id: int, ...) -> int:
    # 1. validate  -> raise ValueError("human-readable message") on bad input
    if not customer_id:
        raise ValueError("customer_id is required")

    # 2. ONE connection = ONE transaction for the whole operation
    async with aiosqlite.connect(write_db_uri(), uri=True) as db:
        db.row_factory = aiosqlite.Row

        # 3. do all the work: inserts, side effects, recomputed totals
        cur = await db.execute("INSERT INTO ... VALUES (...)", (...))
        new_id = cur.lastrowid
        # ... side effects here ...

        # 4. audit INSIDE the same transaction (db=db), summary is human text
        async with db.execute("SELECT * FROM thing WHERE id = ?", (new_id,)) as c:
            after = dict(await c.fetchone())
        await audit.log(actor=actor, entity="thing", entity_id=new_id,
                        action="create", after=after,
                        summary=f"thing created: {new_id}", db=db)

        # 5. commit LAST — nothing persists without its audit row
        await db.commit()
        return new_id
```

Rules that reviews enforce hard:

- **One connection per operation, commit once at the end.** No nested
  connects, no partial commits.
- **`audit.log(..., db=db)`** — passing the open connection is what puts the
  log row in your transaction. For updates pass `before=`/`after=` dicts
  (only the changed fields is fine); the UI diffs them.
- **Reversible side effects.** If your write adjusts stock/balances, the
  edit path must *reverse the old effect then apply the new one*, and the
  delete path must restore state. Study `_write_cut` / `remove_cut` /
  `delete_order` in `writes/orders.py` — this reverse-then-reapply pattern
  is mandatory for anything touching quantities.
- **Soft delete cascades explicitly**: deleting a parent sets `deleted_at`
  on its children in the same transaction (see `delete_invoice`,
  `delete_order`).
- Return `bool` (found/not-found) for operations on an id, the new id for
  creates. Not-found is a `False` return, not an exception.

### B2 — Query module (`src/queries/<module>.py`)

Read-only, uses `fetch_all/fetch_one` from `queries.base` (read-only DB URI).
Provide `list_things(filters...)` and `get_detail(id)` (row + children +
computed numbers). Always `WHERE deleted_at IS NULL`. Join names the UI
needs (e.g. `c.name AS customer_name`) instead of making the frontend
stitch lookups.

### B3 — Routes (`src/main.py`)

Add a clearly-commented section, following this exact pattern:

```python
@app.post("/api/things", status_code=201)
async def thing_create(request: Request,
                       user_id: int = Depends(auth.require_role("production"))):
    rate_limit("write", user_id)
    body = await request.json()
    actor = await auth.actor_context(user_id, request)
    try:
        new_id = await w_things.create_thing(
            actor, customer_id=body.get("customer_id"),
            amount_cents=int(body.get("amount_cents", 0)))   # int() INSIDE try
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await q_things.get_detail(new_id)
```

- GET list/detail: `Depends(auth.get_current_user)` (any logged-in user).
- Mutations: `Depends(auth.require_role(...))` + `rate_limit("write", user_id)`.
- Mutations return the fresh detail (`get_detail`) so the UI can re-render
  without a second request; deletes return `Response(status_code=204)`.
- Destructive bulk actions: admin-only, `rate_limit("danger", ..., max_per_minute=3)`,
  and require a typed confirmation string in the body (see `orders_wipe_all`).

### B4 — Frontend custom view

If the generic table isn't enough (detail popup, sub-lines, stage buttons),
write a `renderThings(view)` function and add one line to `renderView`:

```js
    if (id === "things") return await renderThings(view);
```

Copy the structure of `renderInvoices`/`renderOrders`: fetch rows → build
`controlsBarHtml(opts)` + table → `wireControls(...)` with the section id as
`stateKey` (this is what makes filter/sort survive popup close) → detail
popups via `modal(...)`, and on popup close re-render the list. Use
`entityForm(id, row, cfgOverride, onSaved)` for sub-forms where possible
instead of hand-building modals.

### B5 — Tests

Path B modules need more than CRUD tests: cover the computed math, the
side-effect reversal (create → edit → delete leaves other tables exactly
as they started), the not-found paths, and any gate/validation rule.
`tests/test_flow.py` shows the end-to-end style.

---

## 6. Pitfalls (things previous iterations got wrong — don't repeat)

- Adding a column to `schema.py`'s CREATE TABLE **without** a new
  `ALTER TABLE` migration — existing production DBs won't get it. New
  column = new numbered `("00xx_...", "ALTER TABLE ... ADD COLUMN ...")`.
- Forgetting `deleted_at IS NULL` in a custom query — soft-deleted rows
  reappear in lists/totals.
- Doing float math on money/quantities anywhere (backend or frontend).
  Convert at the edges (`money`/`milli` field types), compute in integers.
- Writing to `activity_log` after `commit()` or on a separate connection —
  breaks the "no change without its audit row" invariant.
- Adding an i18n key to `ar` but not `en` (or vice versa) — the UI shows the
  raw key.
- Interpolating anything user-controlled into SQL strings. Table/column
  names come only from the registry/code; all values go through `?` params.
- New JS that fails `node --check` (template-literal typos are common).
- Pushing to `main` "just to test" — that IS production.

## 7. Definition of Done — the review checklist

The code review will check, in order:

**Correctness**
- [ ] Migration is appended (never edited), idempotent, numbered next in sequence
- [ ] Money/quantities are integers (`_cents`/`_milli`); no float arithmetic
- [ ] All reads filter `deleted_at IS NULL`; deletes are soft + cascade to children
- [ ] Side effects (stock/balances/status) reverse cleanly on edit and delete
- [ ] Validation raises `ValueError` → mapped to HTTP 400; `int()` casts inside `try`

**Audit & security**
- [ ] Every mutation produces an `activity_log` row in the same transaction
- [ ] Every mutation route: `require_role(...)` + `rate_limit(...)`; reads: `get_current_user`
- [ ] All SQL values parameterized; all rendered user data wrapped in `esc()`

**Frontend**
- [ ] All labels in both `I18N.ar` and `I18N.en`; existing keys reused
- [ ] `ENTITIES`/custom view + `NAV` entry; filters/sorts where the list will grow
- [ ] Form fields use correct types (`money`, `milli`, `date`, `select`+`lookup`)
- [ ] `node --check src/static/app.js` passes; works in both AR (RTL) and EN

**Process**
- [ ] `python -m pytest` green, including new tests for the module's logic
- [ ] `REQUIREMENTS.md`: functional section added/updated + change-log entry
- [ ] Feature branch + PR — no direct push to `main`
- [ ] No new dependencies, no build step, no framework additions

Hand over the PR link (or branch name) and one paragraph describing what the
module does and any place you knowingly deviated from this guide and why.
