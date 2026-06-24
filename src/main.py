"""Garment-factory ERP — FastAPI backend.

Auth: Telegram Login Widget -> JWT cookie, role-gated.
Most entities are served by uniform REST routes generated from
`src.entities.REGISTRY`; every mutation flows through `crud.Table`, which
writes an `activity_log` row in the same transaction. Orders, invoices,
payments, the dashboard, file uploads and the activity viewer have bespoke
routes below.
"""
import logging
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import (Depends, FastAPI, File, Form, HTTPException, Request,
                     Response, UploadFile)
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src import auth, config
from src.entities import REGISTRY
from src.middleware import rate_limit
from src.schema import apply_migrations
from src.writes import audit, users as w_users
from src.queries import audit as q_audit
from src.queries import lookups as q_lookups
from src.queries import orders as q_orders
from src.queries import invoices as q_invoices
from src.queries.base import fetch_all
from src.writes import orders as w_orders
from src.writes import invoices as w_invoices
from src.writes import payments as w_payments

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_DEPLOY_TS = str(int(time.time()))

app = FastAPI(docs_url=None, redoc_url=None)
STATIC_DIR = Path(__file__).parent / "static"


@app.on_event("startup")
async def _startup():
    try:
        await apply_migrations()
    except Exception as e:  # noqa: BLE001
        logger.exception("apply_migrations failed: %s", e)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.get("/api/config")
async def api_config():
    return {"bot_username": config.BOT_USERNAME}


@app.post("/api/auth/telegram")
async def telegram_auth(request: Request, response: Response):
    data = await request.json()
    if not auth.verify_telegram_hash(data):
        raise HTTPException(status_code=403, detail="Invalid Telegram auth")
    tg_user_id = int(data["id"])
    name = " ".join(p for p in (data.get("first_name"), data.get("last_name")) if p)

    existing = await auth.get_app_user(tg_user_id)
    if existing is None and tg_user_id not in config.ALLOWED_USERS:
        # New person: self-register as an inactive (pending) account that an
        # admin must approve from the Users screen. They cannot log in yet.
        await w_users.register_pending(tg_user_id, name or None, data.get("username"))
        raise HTTPException(
            status_code=403,
            detail="تم إنشاء حسابك وهو بانتظار موافقة المدير / "
                   "Your account was created and is awaiting admin approval.")

    user = await w_users.ensure_user_on_login(tg_user_id, name or None,
                                              data.get("username"))
    if not user.get("active"):
        raise HTTPException(
            status_code=403,
            detail="حسابك بانتظار موافقة المدير أو معطّل / "
                   "Your account is awaiting admin approval or is disabled.")

    token = auth.create_session_token(tg_user_id)
    response.set_cookie(key="session", value=token, httponly=True, secure=True,
                        samesite="lax", max_age=auth.SESSION_DAYS * 86400)
    actor = await auth.actor_context(tg_user_id, request)
    await audit.log(actor=actor, entity="auth", action="login",
                    summary=f"login: {name or tg_user_id}")
    return {"ok": True, "name": name, "role": user.get("role")}


@app.post("/api/logout")
async def logout(request: Request, response: Response,
                 user_id: int = Depends(auth.get_current_user)):
    actor = await auth.actor_context(user_id, request)
    await audit.log(actor=actor, entity="auth", action="logout", summary="logout")
    response.delete_cookie("session")
    return {"ok": True}


@app.get("/api/me")
async def me(user_id: int = Depends(auth.get_current_user)):
    user = await auth.get_app_user(user_id)
    role = await auth.get_role(user_id)
    return {
        "user_id": user_id,
        "name": (user or {}).get("name"),
        "role": role,
        "language": (user or {}).get("language") or "ar",
    }


@app.put("/api/me/language")
async def set_language(request: Request, user_id: int = Depends(auth.get_current_user)):
    body = await request.json()
    actor = await auth.actor_context(user_id, request)
    try:
        await w_users.set_language(actor, user_id, body.get("language"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True, "language": body.get("language")}


# ---------------------------------------------------------------------------
# Generic entity CRUD (generated from the registry)
# ---------------------------------------------------------------------------
def _register_entity_routes(name: str) -> None:
    ent = REGISTRY[name]
    base = f"/api/{name}"
    writer_dep = auth.require_role(*ent.roles)

    @app.get(base, name=f"{name}_list")
    async def _list(q: str | None = None, include_deleted: bool = False,
                    limit: int = 500, offset: int = 0,
                    user_id: int = Depends(auth.get_current_user)):
        return {"rows": await ent.reader.list(q=q, include_deleted=include_deleted,
                                              limit=limit, offset=offset)}

    @app.get(base + "/{row_id}", name=f"{name}_get")
    async def _get(row_id: int, user_id: int = Depends(auth.get_current_user)):
        row = await ent.reader.get(row_id)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return row

    @app.post(base, status_code=201, name=f"{name}_create")
    async def _create(request: Request, user_id: int = Depends(writer_dep)):
        rate_limit("write", user_id)
        body = await request.json()
        if ent.transform:
            body = ent.transform(dict(body))
        actor = await auth.actor_context(user_id, request)
        try:
            new_id = await ent.table.create(actor, **body)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return await ent.reader.get(new_id)

    @app.put(base + "/{row_id}", name=f"{name}_update")
    async def _update(row_id: int, request: Request, user_id: int = Depends(writer_dep)):
        rate_limit("write", user_id)
        body = await request.json()
        if ent.transform:
            body = ent.transform(dict(body))
        actor = await auth.actor_context(user_id, request)
        try:
            row = await ent.table.update(actor, row_id, **body)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        if row is None:
            raise HTTPException(status_code=404, detail="Not found")
        return row

    @app.delete(base + "/{row_id}", status_code=204, name=f"{name}_delete")
    async def _delete(row_id: int, request: Request, user_id: int = Depends(writer_dep)):
        rate_limit("write", user_id)
        actor = await auth.actor_context(user_id, request)
        if not await ent.table.soft_delete(actor, row_id):
            raise HTTPException(status_code=404, detail="Not found or already deleted")
        return Response(status_code=204)

    @app.post(base + "/{row_id}/restore", name=f"{name}_restore")
    async def _restore(row_id: int, request: Request, user_id: int = Depends(writer_dep)):
        rate_limit("write", user_id)
        actor = await auth.actor_context(user_id, request)
        if not await ent.table.restore(actor, row_id):
            raise HTTPException(status_code=404, detail="Not found or not deleted")
        return {"ok": True, "id": row_id}

    @app.get(base + "/{row_id}/history", name=f"{name}_history")
    async def _history(row_id: int, user_id: int = Depends(auth.require_role("admin"))):
        return {"entity": name, "id": row_id,
                "history": await q_audit.history_for(name, row_id)}


for _name in REGISTRY:
    _register_entity_routes(_name)


# ---------------------------------------------------------------------------
# Lookups + customer 360 + dashboard
# ---------------------------------------------------------------------------
@app.get("/api/lookups")
async def lookups(user_id: int = Depends(auth.get_current_user)):
    return await q_lookups.all_lookups()


@app.get("/api/customers/{customer_id}/profile")
async def customer_profile(customer_id: int, user_id: int = Depends(auth.get_current_user)):
    data = await q_lookups.customer_360(customer_id)
    if not data:
        raise HTTPException(status_code=404, detail="Customer not found")
    return data


@app.get("/api/dashboard")
async def dashboard(user_id: int = Depends(auth.get_current_user)):
    return await q_lookups.dashboard()


# ---------------------------------------------------------------------------
# Manufacturing orders (custom: auto-estimate + stage tracking)
# ---------------------------------------------------------------------------
@app.get("/api/orders")
async def orders_list(status: str | None = None, customer_id: int | None = None,
                      include_deleted: bool = False,
                      user_id: int = Depends(auth.get_current_user)):
    return {"rows": await q_orders.list_orders(status=status, customer_id=customer_id,
                                              include_deleted=include_deleted)}


@app.get("/api/orders/estimate")
async def orders_estimate(sample_id: int | None = None, quantity: int = 0,
                          user_id: int = Depends(auth.get_current_user)):
    return await q_orders.compute_estimate(sample_id, quantity)


@app.get("/api/orders/{order_id}")
async def order_detail(order_id: int, user_id: int = Depends(auth.get_current_user)):
    row = await q_orders.get_detail(order_id)
    if not row:
        raise HTTPException(status_code=404, detail="Order not found")
    return row


@app.get("/api/orders/{order_id}/history")
async def order_history(order_id: int, user_id: int = Depends(auth.require_role("admin"))):
    return {"entity": "manufacturing_orders", "id": order_id,
            "history": await q_audit.history_for("manufacturing_orders", order_id)}


@app.post("/api/orders", status_code=201)
async def order_create(request: Request,
                       user_id: int = Depends(auth.require_role("production", "sales"))):
    rate_limit("write", user_id)
    body = await request.json()
    actor = await auth.actor_context(user_id, request)
    try:
        new_id = await w_orders.create_order(
            actor, customer_id=body.get("customer_id"), sample_id=body.get("sample_id"),
            code=body.get("code"), quantity=int(body.get("quantity", 0)),
            order_date=body.get("order_date"), delivery_date=body.get("delivery_date"),
            unit_cost_cents=body.get("unit_cost_cents"), notes=body.get("notes"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await q_orders.get_detail(new_id)


@app.post("/api/orders/{order_id}/advance")
async def order_advance(order_id: int, request: Request,
                        user_id: int = Depends(auth.require_role("production"))):
    rate_limit("write", user_id)
    body = await request.json()
    actor = await auth.actor_context(user_id, request)
    try:
        ok = await w_orders.advance_stage(actor, order_id, body.get("stage"),
                                          responsible=body.get("responsible"),
                                          notes=body.get("notes"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Order not found")
    return await q_orders.get_detail(order_id)


# ---------------------------------------------------------------------------
# Invoices + payments (custom: totals + status recompute)
# ---------------------------------------------------------------------------
@app.get("/api/invoices")
async def invoices_list(status: str | None = None, customer_id: int | None = None,
                        user_id: int = Depends(auth.get_current_user)):
    return {"rows": await q_invoices.list_invoices(status=status, customer_id=customer_id)}


@app.get("/api/invoices/{invoice_id}")
async def invoice_detail(invoice_id: int, user_id: int = Depends(auth.get_current_user)):
    row = await q_invoices.get_detail(invoice_id)
    if not row:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return row


@app.post("/api/invoices", status_code=201)
async def invoice_create(request: Request,
                         user_id: int = Depends(auth.require_role("accountant"))):
    rate_limit("write", user_id)
    body = await request.json()
    actor = await auth.actor_context(user_id, request)
    try:
        new_id = await w_invoices.create_invoice(
            actor, customer_id=body.get("customer_id"), order_id=body.get("order_id"),
            invoice_no=body.get("invoice_no"), invoice_date=body.get("invoice_date"),
            discount_cents=int(body.get("discount_cents", 0)),
            tax_cents=int(body.get("tax_cents", 0)), notes=body.get("notes"),
            lines=body.get("lines") or [])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await q_invoices.get_detail(new_id)


@app.post("/api/payments", status_code=201)
async def payment_create(request: Request,
                         user_id: int = Depends(auth.require_role("accountant"))):
    rate_limit("write", user_id)
    body = await request.json()
    actor = await auth.actor_context(user_id, request)
    try:
        new_id = await w_payments.record_payment(
            actor, customer_id=body.get("customer_id"),
            amount_cents=int(body.get("amount_cents", 0)), kind=body.get("kind", "progress"),
            order_id=body.get("order_id"), invoice_id=body.get("invoice_id"),
            payment_date=body.get("payment_date"), note=body.get("note"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": new_id}


@app.delete("/api/payments/{payment_id}", status_code=204)
async def payment_delete(payment_id: int, request: Request,
                         user_id: int = Depends(auth.require_role("accountant"))):
    rate_limit("write", user_id)
    actor = await auth.actor_context(user_id, request)
    if not await w_payments.delete_payment(actor, payment_id):
        raise HTTPException(status_code=404, detail="Payment not found")
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# User administration (admin only)
# ---------------------------------------------------------------------------
@app.get("/api/users")
async def users_list(user_id: int = Depends(auth.require_role("admin"))):
    return {"rows": await fetch_all(
        "SELECT id, tg_user_id, name, username, role, language, active, created_at "
        "FROM app_users WHERE deleted_at IS NULL ORDER BY id")}


@app.put("/api/users/{row_id}/role")
async def users_set_role(row_id: int, request: Request,
                         user_id: int = Depends(auth.require_role("admin"))):
    body = await request.json()
    actor = await auth.actor_context(user_id, request)
    try:
        ok = await w_users.set_role(actor, row_id, body.get("role"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}


@app.put("/api/users/{row_id}/active")
async def users_set_active(row_id: int, request: Request,
                           user_id: int = Depends(auth.require_role("admin"))):
    body = await request.json()
    actor = await auth.actor_context(user_id, request)
    if not await w_users.set_active(actor, row_id, bool(body.get("active"))):
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Activity log viewer (admin only)
# ---------------------------------------------------------------------------
@app.get("/api/activity")
async def activity(actor_user_id: int | None = None, entity: str | None = None,
                   entity_id: int | None = None, action: str | None = None,
                   date_from: str | None = None, date_to: str | None = None,
                   q: str | None = None, page: int = 1, page_size: int = 50,
                   user_id: int = Depends(auth.require_role("admin"))):
    return await q_audit.search(actor_user_id=actor_user_id, entity=entity,
                                entity_id=entity_id, action=action,
                                date_from=date_from, date_to=date_to, q=q,
                                page=page, page_size=page_size)


# ---------------------------------------------------------------------------
# File uploads (sample images / blueprint files)
# ---------------------------------------------------------------------------
_ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf",
                ".svg", ".ai", ".psd", ".dxf", ".plt"}


@app.post("/api/files", status_code=201)
async def upload_file(request: Request, file: UploadFile = File(...),
                      kind: str = Form("misc"),
                      user_id: int = Depends(auth.get_current_user)):
    rate_limit("upload", user_id, max_per_minute=30)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")
    safe = f"{kind}_{uuid.uuid4().hex}{ext}"
    dest = Path(config.UPLOAD_DIR) / safe
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 25MB)")
    dest.write_bytes(data)
    actor = await auth.actor_context(user_id, request)
    await audit.log(actor=actor, entity="files", action="file_upload",
                    summary=f"uploaded {file.filename} -> {safe}")
    return {"path": safe, "url": f"/api/files/{safe}"}


@app.get("/api/files/{name}")
async def serve_file(name: str, user_id: int = Depends(auth.get_current_user)):
    safe = Path(name).name  # prevent path traversal
    dest = Path(config.UPLOAD_DIR) / safe
    if not dest.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(dest))


# ---------------------------------------------------------------------------
# Static frontend (mounted last so /api/* takes precedence)
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    content = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    content = content.replace('src="./app.js"', f'src="./app.js?v={_DEPLOY_TS}"')
    content = content.replace('href="./style.css"', f'href="./style.css?v={_DEPLOY_TS}"')
    return HTMLResponse(content=content, headers={"Cache-Control": "no-store"})


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store"
        return response


app.mount("/", NoCacheStaticFiles(directory=str(STATIC_DIR), html=True), name="static")
