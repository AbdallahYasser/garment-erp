# Garment Factory ERP

A bilingual (Arabic RTL / English) web ERP for a garment factory, implementing
the FRS core flow: customers, samples (fabric / blueprint+sizes / printing /
manufacturing), fabric rolls & colors, accessories, suppliers, product specs
(BOM), manufacturing orders with auto cost estimation and production-stage
tracking, inventory (factory + per-customer), invoices, payments & balances,
and a **full activity log** that records every change by every user — including
admins.

Built in the house style: **FastAPI + aiosqlite (WAL) + Telegram-login JWT +
no-build vanilla-JS SPA + Docker + Coolify**.

## Stack
- **Backend:** FastAPI, aiosqlite (the app owns its own SQLite DB, WAL mode).
- **Auth:** Telegram Login Widget → HMAC verify → JWT httpOnly cookie, role-gated
  (admin / accountant / production / sales).
- **Frontend:** single-page app in `src/static/` (no build step).
- **Money:** integer piastres (1 EGP = 100). **Fractional quantities:** milli-units
  (×1000) so all arithmetic is exact integer.

## Architecture
```
src/
  config.py        env config
  db.py            read-only / read-write SQLite URIs
  schema.py        all tables + idempotent migrations (run on startup, sets WAL)
  auth.py          Telegram login, JWT, get_role(), require_role()
  entities.py      registry of standard CRUD entities -> uniform REST routes
  writes/
    crud.py        generic audited Table (every mutation writes activity_log)
    audit.py       central log() — the single append point for the activity log
    orders.py      order create (auto estimate) + stage transitions
    invoices.py    invoice totals + payment-status recompute
    payments.py    payments + status refresh
    users.py       app_users (login provisioning, role/active admin)
  queries/
    base.py        generic Reader + fetch helpers
    audit.py       activity feed + per-record history (with diffs)
    orders.py      material + cost estimate
    invoices.py    invoice detail + balance
    lookups.py     dropdowns, customer 360, dashboard
  main.py          FastAPI app: auth, generated CRUD, custom routes, uploads, static
```

### Activity log (log everything)
Every create / update / delete / restore flows through `writes/crud.py`, which
writes an `activity_log` row **in the same transaction** — a change can never be
persisted without its audit entry. Logins, logouts, stage changes, payments,
file uploads and exports are logged explicitly. The table is append-only (no
update/delete path in the data layer), so the trail is immutable from the app.
Admins are logged identically to everyone else. View it under **Activity Log**
(admin only) or per-record via the **History** link.

## Local development
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # fill BOT_TOKEN, BOT_USERNAME, SECRET_KEY, ALLOWED_USERS
export DB_PATH=./data/erp.db UPLOAD_DIR=./data/uploads
uvicorn src.main:app --reload --port 8080
```
The first Telegram user to log in (or any id in `ALLOWED_USERS`) becomes **admin**;
everyone else defaults to **sales** until an admin promotes them under **Users**.

Run tests:
```bash
pip install pytest
PYTHONPATH=. python -m pytest
```

## Environment variables
| Var | Purpose |
|-----|---------|
| `BOT_TOKEN` | Telegram bot token (verifies the Login Widget hash) |
| `BOT_USERNAME` | Bot username (no `@`) for the login button |
| `SECRET_KEY` | JWT signing secret (`python3 -c "import secrets;print(secrets.token_hex(32))"`) |
| `DB_PATH` | SQLite file path (in the Coolify volume in prod) |
| `UPLOAD_DIR` | Upload directory (in the volume) |
| `ALLOWED_USERS` | Comma-separated Telegram IDs that bootstrap as admin |
| `NOTIFY_BOT_TOKEN` / `NOTIFY_CHAT_ID` | Optional in-app business notifications |
| `TIMEZONE`, `LOG_LEVEL` | Display tz / logging |

## Deployment (EC2 + Coolify)
1. Push this repo to GitHub.
2. Create the app in the Coolify **UI** from the repo (Docker Compose, path `/docker-compose.yml`).
3. Configure via the Coolify API (see `../coolify-migration/COOLIFY_DEPLOY_GUIDE.md`):
   - `watch_paths`: `src/**\nrequirements.txt\nDockerfile`
   - env vars with `is_preview: false`
   - GitHub webhook secret for auto-deploy
4. **Deploy notifications:** set `pre_deployment_command` (⚡ Deploy started) and
   `post_deployment_command` (✅ Deploy finished) per the guide — the Dockerfile
   already includes `curl`.
5. Assign your subdomain (e.g. `erp.<your-domain>`) in Coolify. The persistent
   volume `garment-erp-data` holds the SQLite DB + uploads.

> Telegram login requires the domain to be registered with @BotFather
> (`/setdomain`) for the bot whose `BOT_USERNAME` you use.
