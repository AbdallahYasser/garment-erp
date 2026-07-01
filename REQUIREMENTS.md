# Garment Factory ERP — Requirements & System Specification

**Product:** Omar مختار — Garment Factory ERP
**Type:** Web application (bilingual Arabic/English), no chatbot
**Status:** In production at `https://erp.bode1.site`
**Last updated:** 2026-07-01

This document describes **what the system does today** (functional + non‑functional requirements) and a **change log** of every adjustment requested during development. It reflects the *current* behavior after all iterations.

---

## 1. Overview

### 1.1 Purpose
Manage all operational and financial activity of a garment factory: from receiving a customer and creating a sample, through manufacturing (cutting → sewing → … → delivery), inventory of fabric and accessories, invoicing, payments, and reporting — with a full audit trail of every change.

### 1.2 Scope (implemented)
- Customers, Suppliers
- Samples and their components (fabric, blueprint/sizes, printing, manufacturing cost)
- Accessories, Fabric rolls (by lot/colour)
- Manufacturing orders with per‑colour cutting details and production‑stage tracking
- Inventory movements (factory + per‑customer)
- Invoices (multi‑order, auto‑filled), PDF export (download + Telegram), payments & balances
- Customer 360 profile
- Activity log (every change, everyone, immutable)
- User management & role‑based access
- Bilingual (AR‑RTL / EN) responsive UI with per‑list search / filter / sort
- Admin tools: bulk delete orders, factory reset

### 1.3 Key business decisions
- **Sizes** are part of the **Blueprint** (not a separate entity). The customer chooses which sizes; the blueprint records the approved sizes.
- **Colours** are tied to **fabric rolls** the customer brings (each roll lot has a colour). An order can contain **more than one colour**.
- **Fabric is reference‑only**: its type/quantity/cost is recorded on the sample for reference but is **not** part of the manufacturing‑order cost calculation.
- Customer‑supplied components cost **zero** (fabric/blueprint/printing supplied by the customer are not charged).
- The **order is the bill**: the customer profile’s financial totals are driven by orders, not invoices.

---

## 2. Technology & Architecture

- **Backend:** Python 3.12, FastAPI, `aiosqlite` (SQLite in WAL mode). The app **owns its own database** and applies idempotent migrations on startup.
- **Auth:** Telegram Login Widget → HMAC verify → JWT (30‑day httpOnly cookie). Role‑gated.
- **Frontend:** Single‑page app in vanilla JS/CSS (no build step), bilingual with RTL support, served as static files.
- **PDF:** `reportlab` + `arabic-reshaper` + `python-bidi` with a bundled **Amiri** font (Arabic + Latin).
- **Money:** stored as integer **piastres** (1 EGP = 100). **Fractional quantities** stored in **milli‑units** (×1000) so all arithmetic is exact integers.
- **Deployment:** Docker + Coolify on a **dedicated AWS EC2** (Ubuntu 24.04, 2 GB RAM + 2 GB swap) behind Cloudflare; auto‑deploy on `git push` (GitHub webhook) with Telegram “deploy started/finished” notifications.
- **Repo:** `github.com/AbdallahYasser/garment-erp` (public), branch `main`.

### Backend structure
```
src/
  config.py        env config
  db.py            read-only / read-write SQLite URIs
  schema.py        all tables + idempotent migrations (WAL on startup)
  auth.py          Telegram login, JWT, get_role(), require_role()
  entities.py      registry of standard CRUD entities -> generated REST routes
  pdf.py           Arabic invoice PDF (build_invoice_pdf, invoice_filename)
  notify.py        Telegram sendMessage / sendDocument helpers
  writes/          audited create/update/delete (crud.Table), orders, invoices,
                   payments, users, admin (reset), rolls, audit (activity log)
  queries/         reads: base, audit, orders, invoices, lookups, ...
  main.py          FastAPI app: auth, generated CRUD, custom routes, uploads, static
  static/          index.html, style.css, app.js (the SPA)
  pdf_assets/fonts Amiri-Regular.ttf, Amiri-Bold.ttf
```

---

## 3. Roles & Access Control

Four roles; **admin** always passes every check.

| Role | Can manage |
|------|------------|
| **admin** | Everything + Users + Activity log + admin tools |
| **accountant** | Invoices, payments |
| **production** | Suppliers, accessories, fabric rolls, orders, cutting/stages, inventory |
| **sales** | Customers, samples & components |

### 3.1 Login & user provisioning
- Staff log in via **Telegram** (bot **@omar_erp_bot**).
- **Bootstrap owners:** any Telegram ID listed in the `ALLOWED_USERS` env var is **always admin** and can never be locked out (break‑glass account).
- **Self‑register → approve:** a brand‑new Telegram user who logs in is created as an **inactive (pending)** account (role *sales*) and cannot enter until an **admin approves** them (Users screen → set role + tick *Active*). A clear message tells pending users to wait.
- To receive PDFs via Telegram, a user must have pressed **Start** on the bot at least once.

---

## 4. Functional Requirements by Module

### 4.1 Customers
- Fields: name (required), company, phone, email, address, notes.
- **Customer profile (360):** headline **Total / Paid / Balance**, where **Total = sum of the customer’s order costs** (excluding cancelled) and **Balance = Total − payments**; plus lists of the customer’s orders, samples, and **customer‑owned fabric rolls** (shown as colour · type · number of rolls · remaining) and accessories.
- The **invoiced** amount is tracked separately (does not drive the headline balance).

### 4.2 Suppliers
- Fields: name (required), phone, address, material types, notes. Linkable from purchased items.

### 4.3 Samples & components
A sample belongs to a customer (name, status: draft/approved/archived, optional image). “**Components**” (per sample):
- **Fabric** *(reference only)* — fabric type, quantity (meter/kg), cost, source (factory/customer → cost forced to 0 if customer). **Not used in the order cost.**
- **Blueprint** — design name, version, **approved sizes** (tickable **S / M / L / XL / XXL**), cost, source.
- **Printing** — type, description, cost, source.
- **Manufacturing** — a **single “Manufacturing cost / piece”** value (replaced the earlier cut/sew/finish split).
- **Required accessories** — per‑piece accessory consumption (accessory + qty per piece), used to compute order accessory cost.

*(There is no separate “Consumption spec” — it was removed.)*

### 4.4 Accessories
- Fields: name, unit, stock qty, unit price, source (factory/customer), optional customer, optional supplier.

### 4.5 Fabric rolls (by lot)
- Added **by lot**, not one roll at a time: colour, fabric type, **length per roll**, **number of rolls**, owner (factory/customer), customer, supplier. There is **no “Roll #”** field.
- The system stores the lot with **total remaining metres = length × number of rolls**.

### 4.6 Manufacturing Orders

**Creation** (minimal):
- Select **Customer** → then choose one of **that customer’s Samples** (dropdown filtered by customer).
- Select the **fabric roll colours** for the order and enter the **number of rolls per colour** (reserved/deducted immediately, one planned “cut line” per colour).
- Order date, delivery date, notes.
- **No quantity, no unit cost, and no “Code” field at creation.**

**Cutting stage** (where quantities & cost are entered):
- Enter a single **Unit cost** (per piece) for the order.
- For each colour’s **cut line** (Edit): enter **Units (pieces)**, tick **Sizes**, and **Roll remaining after cut** — expressed as a **number of rolls** (e.g. `1`, `1.25`, `1.5`) that must be **less than** the rolls used for that colour. The leftover metres are returned to that roll’s stock. (Rolls‑used is read‑only here — set at creation.)
- Each cut deducts its roll lot and logs an **inventory “issue”** movement; editing a cut reverses and re‑applies cleanly (no duplicate stock movements); deleting a cut restores stock.
- **Order quantity = sum of cut units; Estimated total = unit cost × quantity.**

**Production‑stage tracking:** New → Prep → Cutting → Printing → Sewing → Finishing → Packing → Ready → Delivered (+ Cancelled). Each stage records start/end, responsible, notes.
- **Gate:** to advance **past Cutting** you must have entered the **unit cost** **and** filled in **every colour’s cut details** (all cut lines must have units). The message shows progress, e.g. “enter cut details for all colours (1/2 done)”.

**Order detail** shows Total units, Unit cost, Estimated total, Paid, Balance, the stage tracker, the cut lines, and a required‑accessories reference (units × per‑piece).

**Deletion:** deleting an order restores the fabric‑roll stock its cuts consumed and removes its cuts/stages/order‑linked inventory movements (soft delete). Admin **“Delete all orders”** does the same in bulk.

### 4.7 Inventory movements
- Ledger of material movements: item type (fabric/accessory/packing), item, owner (factory/customer), movement type (add/issue/transfer/return), quantity, optional linked order, note. Fabric issues from cutting are recorded here automatically.

### 4.8 Invoices
- **Create from multiple orders:** pick the customer, then tick **one or more of that customer’s orders**; line items **auto‑fill** from each order (piece name = sample, quantity, unit cost). Orders with the **same item at the same price are merged** (quantities summed). Manual lines can still be added/edited.
- Fields: invoice no, date, **Discount** and **Tax** (flat EGP amounts), line items (description, qty, unit price).
- **Calculation:** `line total = qty × unit price`; `subtotal = Σ line totals`; `total = subtotal − discount + tax`.
- **Status:** unpaid → partial → paid (from payments recorded against the invoice). Invoice balance = total − payments on that invoice.
- **PDF export** (two options, same content):
  - **Download** (opens/saves in the browser).
  - **Send to Telegram** — delivers the PDF to the logged‑in user’s chat via the ERP bot (solves iPhone Safari opening PDFs inline; savable/shareable natively).
  - **File name:** `«customer» - «item/items» - «date».pdf` (Arabic‑safe).
  - PDF layout (Wave‑style): header **“Omar مختار”**, Bill‑To, items table, Subtotal/Discount/Tax/Total/Amount Due, footer **“Powered by Omar مختار”**. Arabic renders shaped + right‑to‑left.
- **PDFs are not stored on disk** — generated on demand from the saved invoice data. Only the invoice **record** is persisted.
- **Delete invoice** (accountant/admin): soft‑deletes the invoice + lines; payments are kept.

### 4.9 Payments
- Recorded against a customer and (optionally) an invoice/order; kind = advance / progress / final. Reduce the customer’s balance and drive invoice status.

### 4.10 Activity log (audit)
- **Every** create/update/delete/restore across the system, plus logins/logouts, stage changes, payments, file uploads/exports — recorded in an **append‑only, immutable** log with: timestamp, actor (Telegram id, name, role — **admins are logged identically**), entity, action, **before/after field‑level diff**, IP/user‑agent.
- **Admin‑only History viewer:** global feed with filters (actor, entity, action, date, free text) + per‑record timeline with highlighted diffs.

### 4.11 Users administration (admin)
- List/approve users, set **role**, toggle **Active**. Help text explains the self‑register → approve flow and the `ALLOWED_USERS` owner‑admin path.
- **Danger zone → “Reset all data (keep users)”:** factory reset for handover — wipes all business data + the activity log, resets id counters, clears uploads, **keeps the user accounts**. Requires typing `RESET`.

---

## 5. Cross‑cutting Features

### 5.1 Bilingual + RTL
- Arabic (RTL) and English (LTR) with a language toggle (persisted per user). All labels translated.

### 5.2 Responsive (mobile + desktop)
- On phones/tablets the sidebar becomes an off‑canvas **drawer** (hamburger), forms go single‑column, tables scroll horizontally, and the layout adapts.

### 5.3 Per‑list search / filter / sort
- **Orders, Fabric Rolls, Samples, Invoices** each have a controls bar: instant **search**, **filter** dropdowns, and **sort**, with a live **shown / total** count. Client‑side (no reload).
  - Orders: filter by Status, Customer · sort by newest/oldest/customer/qty/total/status.
  - Fabric Rolls: filter by Owner, Customer · sort by newest, rolls (high/low), remaining (high/low), colour.
  - Samples: filter by Status, Customer · sort by newest, name, status.
  - Invoices: filter by Status, Customer · sort by newest, total (high/low), paid, balance.
- **Selection persistence:** filter/sort/search selections **survive incidental re‑renders** (closing a detail popup, saving, deleting) but **reset when you click the section in the sidebar** (fresh view).

### 5.4 Navigation / refresh behaviour
- The current section is remembered, so pressing **refresh (F5)** keeps you on the same page instead of returning to the Dashboard (admin‑only pages fall back to Dashboard for non‑admins).
- Newly added records appear immediately in dropdowns and lists (forms fetch fresh lookups when opened; detail popups refresh their list on close).

### 5.5 File uploads
- Sample images / blueprint files can be uploaded (stored in the server volume) and served via an auth‑gated endpoint.

---

## 6. Data Model (summary)

Every business table has `id`, `created_at`, and a nullable `deleted_at` (soft delete). Key tables:

- `app_users` (tg_user_id, name, username, role, language, active)
- `customers`, `suppliers`
- `samples`, `sample_fabric`, `sample_blueprint`, `sample_printing`, `sample_manufacturing` (single `cost_cents`), `spec_accessories`
- `accessories`, `fabric_rolls` (`rolls_count`, `length_m_milli`, `remaining_m_milli`, owner, customer/supplier)
- `manufacturing_orders` (customer, sample, `quantity` = Σ cut units, `unit_cost_cents`, `est_total_cents`, status, order/delivery dates), `order_stages`, `order_cuts` (colour, rolls_used, units, sizes, remaining as rolls + metres)
- `inventory_movements` (with `cut_id` link), `accessory_surplus`
- `invoices`, `invoice_lines`, `payments`
- `activity_log` (append‑only)

Amounts in piastres (×100); fractional quantities in milli‑units (×1000).

---

## 7. Non‑functional Requirements

- **Security:** JWT httpOnly cookies; role‑gated endpoints; rate limiting on writes; append‑only immutable audit; secrets via env vars (never committed — the public repo excludes `*.pem`, `*.local.md`, `.env`).
- **Performance:** dedicated EC2 (no resource contention); typical response ~0.3 s. Client‑side search/filter/sort for instant lists. Tiny data footprint (SQLite ~KB/record; PDFs not stored).
- **Reliability / DR:** SQLite WAL; the app owns its DB; migrations idempotent on boot. Old server retained as rollback during migration; DB backups taken during moves.
- **Deployability:** `git push` → GitHub webhook → Coolify auto‑build & deploy on the dedicated EC2 → Telegram ⚡ started / ✅ finished notifications. Cache‑busting on assets each deploy.
- **Testing:** backend test suite (pytest) covering auth, activity logging, the manufacturing flow, roles, and estimates; frontend syntax‑checked on each change.

---

## 8. Change Log — fixes & enhancements requested

In roughly chronological order:

1. **Activity log** — added a first‑class, log‑everything audit trail (including admins) with an admin History viewer.
2. **Deployment** — EC2 + Coolify, custom domain `erp.bode1.site`, Telegram deploy‑start/finish notifications; created the ERP login bot.
3. **Sample cost rule clarified** — customer‑supplied components (fabric/blueprint/printing) forced to **0**; the cost field disables/zeros live when source = customer.
4. **Fabric vs consumption** — clarified/priced; later **Consumption spec removed** and **Fabric made reference‑only** (excluded from order cost).
5. **Manufacturing cost** — collapsed cut/sew/finish into a **single** cost per piece.
6. **Blueprint sizes** — turned “approved sizes” into **S/M/L/XL/XXL checkboxes**.
7. **Fabric rolls** — add **by lot with a roll count**; removed **Roll #**.
8. **Orders redesign** —
   - removed the **Quantity** field at creation (entered at cutting);
   - moved **Unit cost** to the cutting stage;
   - **select fabric rolls/colours at creation**, with **number of rolls per colour**;
   - per‑colour **cut lines**: units, sizes, and **roll remaining as a rolls number** (must be < rolls used); rolls‑used no longer re‑entered at cutting;
   - **stage gate** requires unit cost + **all** colours’ cut details before advancing past Cutting (with progress message);
   - removed the **Code** column from the list.
9. **Users** — added **self‑register → admin‑approve**, and “only keep the two users” handled via the reset (keeps users) + Users screen.
10. **Reset tools** — **Delete all orders** (restores roll stock) and full **factory reset** (keep users, clear activity log) for handover.
11. **Customer profile** — number of fabric rolls now matches the main list; **order cost reflects automatically** in the profile total/balance.
12. **Per‑order & per‑invoice delete** — added, stock‑aware for orders.
13. **Invoices** — multi‑order selection with **auto‑fill + merge**; **Arabic PDF export**; **Send to Telegram**; filename = *customer ‑ items ‑ date*.
14. **Remove Code field** from sample and order add forms.
15. **Performance / migration** — diagnosed slow cold‑starts (undersized shared EC2, swapping) and **migrated the ERP to a dedicated EC2** with no data loss and the same domain; response times went from 11–15 s to ~0.3 s.
16. **UI sync fixes** —
    - new sample/customer/roll/order now appears in dropdowns without a page refresh (forms fetch fresh lookups on open);
    - order/invoice detail changes reflect in the list on close (Cancel **and** click‑outside);
    - refresh (F5) keeps the current page instead of the Dashboard.
17. **Sort & select (filter)** — added instant search/filter/sort to Orders, then Fabric Rolls, Samples, Invoices; filter/sort selections persist across incidental re‑renders and reset on explicit navigation.

---

*This document reflects the implemented system. For infrastructure credentials and server details see the (gitignored, non‑committed) `migration-secrets.local.md`.*
