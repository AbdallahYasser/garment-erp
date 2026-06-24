"use strict";
/* Garment ERP — bilingual (AR/EN, RTL) single-page app, no build step. */

// ---------------------------------------------------------------------------
// i18n
// ---------------------------------------------------------------------------
const I18N = {
  ar: {
    app_title: "نظام إدارة مصنع الملابس", app_short: "المصنع",
    login_hint: "سجّل الدخول عبر تيليجرام للمتابعة", logout: "خروج",
    dashboard: "لوحة التحكم", customers: "العملاء", suppliers: "الموردون",
    samples: "العينات", accessories: "الإكسسوارات", fabric_rolls: "رولات القماش",
    orders: "أوامر التصنيع", inventory_movements: "المخزون", invoices: "الفواتير",
    payments: "المدفوعات", activity: "سجل النشاط", users: "المستخدمون",
    grp_sales: "المبيعات", grp_production: "الإنتاج", grp_finance: "الحسابات", grp_admin: "الإدارة",
    add: "إضافة", edit: "تعديل", del: "حذف", save: "حفظ", cancel: "إلغاء",
    search: "بحث…", history: "السجل", manage: "إدارة", actions: "إجراءات",
    confirm_del: "تأكيد الحذف؟", saved: "تم الحفظ", deleted: "تم الحذف",
    none: "لا توجد بيانات", required: "حقل مطلوب", profile: "ملف العميل",
    name: "الاسم", company: "الشركة", phone: "الهاتف", email: "البريد",
    address: "العنوان", notes: "ملاحظات", material_types: "أنواع المواد",
    code: "الكود", status: "الحالة", customer: "العميل", supplier: "المورد",
    sample: "العينة", quantity: "الكمية", unit: "الوحدة", color: "اللون", kg: "كجم",
    fabric_type: "نوع القماش", roll_no: "رقم الرول", owner: "المالك",
    length_m: "الطول (متر)", remaining_m: "المتبقي (متر)", unit_price: "سعر الوحدة",
    stock_qty: "المخزون", source: "المصدر", customer_src: "من العميل", factory_src: "من المصنع",
    supplied_by_customer: "الخامة يوفّرها العميل — التكلفة تُحتسب صفر",
    order_date: "تاريخ الطلب", delivery_date: "تاريخ التسليم", unit_cost: "تكلفة القطعة",
    est_total: "التكلفة التقديرية", paid: "المدفوع", balance: "المتبقي",
    stage: "المرحلة", advance_stage: "تقديم المرحلة", responsible: "المسؤول",
    required_fabric: "القماش المطلوب", required_acc: "الإكسسوارات المطلوبة",
    invoice_no: "رقم الفاتورة", invoice_date: "تاريخ الفاتورة", discount: "الخصم",
    tax: "الضريبة", subtotal: "الإجمالي الفرعي", total: "الإجمالي", description: "الوصف",
    line_total: "الإجمالي", add_line: "إضافة بند", record_payment: "تسجيل دفعة",
    amount: "المبلغ", kind: "النوع", advance: "عربون", progress: "أثناء الإنتاج", final: "نهائي",
    role: "الصلاحية", active: "نشط", language: "اللغة", created: "تاريخ الإنشاء",
    actor: "المنفّذ", entity: "الكيان", action: "الإجراء", when: "التوقيت",
    open_orders: "أوامر مفتوحة", unpaid_invoices: "فواتير غير مدفوعة", low_stock: "مخزون منخفض",
    recent_activity: "آخر النشاطات", est_breakdown: "تفصيل التكلفة",
    fabric_per_piece: "قماش/قطعة (متر)", design_name: "اسم التصميم", version: "النسخة",
    approved_sizes: "المقاسات المعتمدة", print_type: "نوع الطباعة", archived: "مؤرشف",
    cut_cost: "تكلفة القص", sew_cost: "تكلفة الخياطة", finish_cost: "تكلفة التشطيب",
    components: "مكونات العينة", spec: "مواصفات الاستهلاك", upload: "رفع ملف",
    hint_consumption: "هذا الرقم (متر/قطعة) هو ما يستخدمه النظام لحساب القماش المطلوب في أوامر التصنيع. إذا تركته فارغًا، يأخذ النظام الكمية تلقائيًا من بند «القماش» بالمتر.",
    hint_fabric: "يسجّل قماش العينة النموذجية. تُستخدَم كميته بالمتر في تخطيط الإنتاج فقط عند عدم وجود «مواصفات استهلاك» (التي لها الأولوية دائمًا).",
    fabric_per_piece_used: "القماش لكل قطعة المستخدَم",
    src_spec: "المصدر: مواصفات الاستهلاك", src_fabric: "المصدر: بند القماش (احتياطي)",
    src_none: "غير محدد — أضف مواصفات استهلاك أو بند قماش بالمتر",
    movement_type: "نوع الحركة", add_mv: "إضافة", issue: "صرف", transfer: "تحويل", return_mv: "إرجاع",
    item_type: "نوع الصنف", item_name: "اسم الصنف", fabric: "قماش", packing: "تعبئة",
    blueprint: "الباترون", printing: "الطباعة", manufacturing: "التصنيع", draft: "مسودة", approved: "معتمد",
    "new": "جديد", prep: "تجهيز", cutting: "قص", sewing: "خياطة", finishing: "تشطيب",
    ready: "جاهز", delivered: "تم التسليم", cancelled: "ملغي",
    no_perm: "لا تملك صلاحية لهذا الإجراء", role_admin: "مدير", role_accountant: "محاسب",
    role_production: "إنتاج", role_sales: "مبيعات",
  },
  en: {
    app_title: "Garment Factory ERP", app_short: "Factory",
    login_hint: "Sign in with Telegram to continue", logout: "Logout",
    dashboard: "Dashboard", customers: "Customers", suppliers: "Suppliers",
    samples: "Samples", accessories: "Accessories", fabric_rolls: "Fabric Rolls",
    orders: "Orders", inventory_movements: "Inventory", invoices: "Invoices",
    payments: "Payments", activity: "Activity Log", users: "Users",
    grp_sales: "Sales", grp_production: "Production", grp_finance: "Finance", grp_admin: "Admin",
    add: "Add", edit: "Edit", del: "Delete", save: "Save", cancel: "Cancel",
    search: "Search…", history: "History", manage: "Manage", actions: "Actions",
    confirm_del: "Confirm delete?", saved: "Saved", deleted: "Deleted",
    none: "No data", required: "Required", profile: "Customer profile",
    name: "Name", company: "Company", phone: "Phone", email: "Email",
    address: "Address", notes: "Notes", material_types: "Material types",
    code: "Code", status: "Status", customer: "Customer", supplier: "Supplier",
    sample: "Sample", quantity: "Quantity", unit: "Unit", color: "Color", kg: "kg",
    fabric_type: "Fabric type", roll_no: "Roll #", owner: "Owner",
    length_m: "Length (m)", remaining_m: "Remaining (m)", unit_price: "Unit price",
    stock_qty: "Stock", source: "Source", customer_src: "From customer", factory_src: "From factory",
    supplied_by_customer: "Supplied by the customer — cost counted as zero",
    order_date: "Order date", delivery_date: "Delivery date", unit_cost: "Unit cost",
    est_total: "Estimated total", paid: "Paid", balance: "Balance",
    stage: "Stage", advance_stage: "Advance stage", responsible: "Responsible",
    required_fabric: "Required fabric", required_acc: "Required accessories",
    invoice_no: "Invoice #", invoice_date: "Invoice date", discount: "Discount",
    tax: "Tax", subtotal: "Subtotal", total: "Total", description: "Description",
    line_total: "Total", add_line: "Add line", record_payment: "Record payment",
    amount: "Amount", kind: "Kind", advance: "Advance", progress: "Progress", final: "Final",
    role: "Role", active: "Active", language: "Language", created: "Created",
    actor: "Actor", entity: "Entity", action: "Action", when: "When",
    open_orders: "Open orders", unpaid_invoices: "Unpaid invoices", low_stock: "Low stock",
    recent_activity: "Recent activity", est_breakdown: "Cost breakdown",
    fabric_per_piece: "Fabric/piece (m)", design_name: "Design name", version: "Version",
    approved_sizes: "Approved sizes", print_type: "Print type", archived: "Archived",
    cut_cost: "Cut cost", sew_cost: "Sew cost", finish_cost: "Finish cost",
    components: "Sample components", spec: "Consumption spec", upload: "Upload",
    hint_consumption: "This number (m/piece) is what the system uses to compute the required fabric on manufacturing orders. If you leave it empty, the system falls back to the Fabric quantity (in meters).",
    hint_fabric: "Records the prototype's fabric. Its meter quantity is used for production planning ONLY when no Consumption spec is set (the spec always takes priority).",
    fabric_per_piece_used: "Fabric per piece used",
    src_spec: "source: Consumption spec", src_fabric: "source: Fabric (fallback)",
    src_none: "not set - add a Consumption spec or a meter Fabric entry",
    movement_type: "Movement", add_mv: "Add", issue: "Issue", transfer: "Transfer", return_mv: "Return",
    item_type: "Item type", item_name: "Item name", fabric: "Fabric", packing: "Packing",
    blueprint: "Blueprint", printing: "Printing", manufacturing: "Manufacturing", draft: "Draft", approved: "Approved",
    "new": "New", prep: "Prep", cutting: "Cutting", sewing: "Sewing", finishing: "Finishing",
    ready: "Ready", delivered: "Delivered", cancelled: "Cancelled",
    no_perm: "You don't have permission for this action", role_admin: "Admin",
    role_accountant: "Accountant", role_production: "Production", role_sales: "Sales",
  },
};

let LANG = localStorage.getItem("erp_lang") || "ar";
const t = (k) => (I18N[LANG][k] ?? k);

// ---------------------------------------------------------------------------
// State + API
// ---------------------------------------------------------------------------
const state = { me: null, lookups: {} };

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  const r = await fetch(path, opts);
  if (r.status === 204) return null;
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || ("HTTP " + r.status));
  return data;
}
const ROLE_OK = (...roles) => state.me && (state.me.role === "admin" || roles.includes(state.me.role));

// ---------------------------------------------------------------------------
// formatting
// ---------------------------------------------------------------------------
const money = (c) => ((c || 0) / 100).toLocaleString(LANG === "ar" ? "ar-EG" : "en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " " + (LANG === "ar" ? "ج.م" : "EGP");
const milli = (m) => ((m || 0) / 1000).toLocaleString();
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function statusTag(s) {
  const map = { paid: "green", delivered: "green", approved: "green", partial: "amber",
    ready: "amber", unpaid: "red", cancelled: "red", "new": "gray", draft: "gray" };
  return `<span class="tag ${map[s] || "gray"}">${esc(t(s) !== s ? t(s) : s)}</span>`;
}

// ---------------------------------------------------------------------------
// toast + modal
// ---------------------------------------------------------------------------
function toast(msg, kind = "ok") {
  const el = document.createElement("div");
  el.className = "toast " + kind; el.textContent = msg;
  document.getElementById("toast-root").appendChild(el);
  setTimeout(() => el.remove(), 3000);
}
function modal(title, innerHTML, onMount) {
  const root = document.getElementById("modal-root");
  root.innerHTML = `<div class="modal-bg"><div class="modal"><h3>${esc(title)}</h3>${innerHTML}</div></div>`;
  root.querySelector(".modal-bg").addEventListener("mousedown", (e) => { if (e.target.classList.contains("modal-bg")) closeModal(); });
  if (onMount) onMount(root);
}
const closeModal = () => { document.getElementById("modal-root").innerHTML = ""; };

// ---------------------------------------------------------------------------
// Entity config (generic CRUD)
// field types: text, num, money, milli, date, textarea, select(options|lookup)
// ---------------------------------------------------------------------------
const ENTITIES = {
  customers: { roles: ["sales"], label: "customers", search: true, profile: true,
    columns: ["name", "company", "phone", "email"],
    fields: [
      { k: "name", t: "name", type: "text", req: true }, { k: "company", t: "company", type: "text" },
      { k: "phone", t: "phone", type: "text" }, { k: "email", t: "email", type: "text" },
      { k: "address", t: "address", type: "text", full: true }, { k: "notes", t: "notes", type: "textarea", full: true },
    ] },
  suppliers: { roles: ["production"], label: "suppliers", search: true,
    columns: ["name", "phone", "material_types"],
    fields: [
      { k: "name", t: "name", type: "text", req: true }, { k: "phone", t: "phone", type: "text" },
      { k: "material_types", t: "material_types", type: "text", full: true },
      { k: "address", t: "address", type: "text", full: true }, { k: "notes", t: "notes", type: "textarea", full: true },
    ] },
  accessories: { roles: ["production"], label: "accessories", search: true,
    columns: ["name", "unit", "stock_qty_milli:milli", "unit_price_cents:money", "source"],
    fields: [
      { k: "name", t: "name", type: "text", req: true }, { k: "unit", t: "unit", type: "text" },
      { k: "stock_qty_milli", t: "stock_qty", type: "milli" }, { k: "unit_price_cents", t: "unit_price", type: "money" },
      { k: "source", t: "source", type: "select", options: [["factory", "factory_src"], ["customer", "customer_src"]] },
      { k: "customer_id", t: "customer", type: "select", lookup: "customers" },
      { k: "supplier_id", t: "supplier", type: "select", lookup: "suppliers" },
    ] },
  fabric_rolls: { roles: ["production"], label: "fabric_rolls", search: true,
    columns: ["roll_no", "color", "fabric_type", "remaining_m_milli:milli", "owner"],
    fields: [
      { k: "roll_no", t: "roll_no", type: "text" }, { k: "color", t: "color", type: "text" },
      { k: "fabric_type", t: "fabric_type", type: "text" },
      { k: "length_m_milli", t: "length_m", type: "milli" }, { k: "remaining_m_milli", t: "remaining_m", type: "milli" },
      { k: "owner", t: "owner", type: "select", options: [["factory", "factory_src"], ["customer", "customer_src"]] },
      { k: "customer_id", t: "customer", type: "select", lookup: "customers" },
      { k: "supplier_id", t: "supplier", type: "select", lookup: "suppliers" },
    ] },
  inventory_movements: { roles: ["production"], label: "inventory_movements", search: true,
    columns: ["item_type", "item_name", "movement_type", "qty_milli:milli", "owner"],
    fields: [
      { k: "item_type", t: "item_type", type: "select", options: [["fabric", "fabric"], ["accessory", "accessories"], ["packing", "packing"]], req: true },
      { k: "item_name", t: "item_name", type: "text" },
      { k: "movement_type", t: "movement_type", type: "select", options: [["add", "add_mv"], ["issue", "issue"], ["transfer", "transfer"], ["return", "return_mv"]], req: true },
      { k: "qty_milli", t: "quantity", type: "milli" },
      { k: "owner", t: "owner", type: "select", options: [["factory", "factory_src"], ["customer", "customer_src"]] },
      { k: "customer_id", t: "customer", type: "select", lookup: "customers" },
      { k: "ref_order_id", t: "orders", type: "select", lookup: "orders" },
      { k: "note", t: "notes", type: "textarea", full: true },
    ] },
  samples: { roles: ["sales"], label: "samples", search: true,
    columns: ["code", "name", "status"],
    fields: [
      { k: "name", t: "name", type: "text", req: true }, { k: "code", t: "code", type: "text" },
      { k: "customer_id", t: "customer", type: "select", lookup: "customers" },
      { k: "status", t: "status", type: "select", options: [["draft", "draft"], ["approved", "approved"], ["archived", "archived"]] },
      { k: "notes", t: "notes", type: "textarea", full: true },
    ] },
};

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
const NAV = [
  { group: "grp_admin", items: [{ id: "dashboard", icon: "📊" }] },
  { group: "grp_sales", items: [{ id: "customers", icon: "👥" }, { id: "samples", icon: "🧵" }] },
  { group: "grp_production", items: [
    { id: "suppliers", icon: "🏭" }, { id: "accessories", icon: "🔘" }, { id: "fabric_rolls", icon: "🎽" },
    { id: "orders", icon: "📦" }, { id: "inventory_movements", icon: "📥" }] },
  { group: "grp_finance", items: [{ id: "invoices", icon: "🧾" }] },
  { group: "grp_admin", items: [{ id: "activity", icon: "📝", admin: true }, { id: "users", icon: "⚙️", admin: true }] },
];

let currentView = "dashboard";

function renderNav() {
  const nav = document.getElementById("nav");
  nav.innerHTML = "";
  for (const g of NAV) {
    const items = g.items.filter((it) => !it.admin || state.me.role === "admin");
    if (!items.length) continue;
    const grp = document.createElement("div");
    grp.className = "nav-group"; grp.textContent = t(g.group);
    nav.appendChild(grp);
    for (const it of items) {
      const el = document.createElement("div");
      el.className = "nav-item" + (it.id === currentView ? " active" : "");
      el.innerHTML = `<span>${it.icon}</span><span>${t(it.id)}</span>`;
      el.onclick = () => navigate(it.id);
      nav.appendChild(el);
    }
  }
}

function navigate(id) { currentView = id; renderNav(); document.getElementById("crumb").textContent = t(id); renderView(id); }

// ---------------------------------------------------------------------------
// View router
// ---------------------------------------------------------------------------
async function renderView(id) {
  const view = document.getElementById("view");
  view.innerHTML = `<p class="muted">…</p>`;
  try {
    if (id === "dashboard") return await renderDashboard(view);
    if (id === "orders") return await renderOrders(view);
    if (id === "invoices") return await renderInvoices(view);
    if (id === "activity") return await renderActivity(view);
    if (id === "users") return await renderUsers(view);
    if (id === "samples") return await renderSamples(view);
    return await renderEntity(view, id);
  } catch (e) { view.innerHTML = `<p class="error">${esc(e.message)}</p>`; }
}

function colHeader(cfg, spec) {
  const k = spec.split(":")[0];
  const f = cfg.fields.find((x) => x.k === k);
  return t(f ? f.t : k);
}
function cellValue(row, spec) {
  const [k, type] = spec.split(":");
  const v = row[k];
  if (type === "money") return money(v);
  if (type === "milli") return milli(v);
  if (k === "status" || k === "source" || k === "owner" || k === "movement_type" || k === "item_type") return statusTag(v);
  return esc(v ?? "");
}

async function renderEntity(view, id) {
  const cfg = ENTITIES[id];
  const canWrite = ROLE_OK(...cfg.roles);
  const data = await api("GET", `/api/${id}?limit=500`);
  const rows = data.rows || [];
  const head = cfg.columns.map((c) => `<th>${colHeader(cfg, c)}</th>`).join("");
  view.innerHTML = `
    <div class="section-head">
      <h2>${t(id)}</h2>
      <div class="toolbar">
        ${cfg.search ? `<input id="q" placeholder="${t("search")}">` : ""}
        ${canWrite ? `<button class="btn" id="add">+ ${t("add")}</button>` : ""}
      </div>
    </div>
    <div class="card"><table><thead><tr>${head}<th>${t("actions")}</th></tr></thead>
    <tbody id="tb">${rowsHtml(id, rows, cfg)}</tbody></table>
    ${rows.length ? "" : `<p class="muted" style="padding:14px">${t("none")}</p>`}</div>`;
  if (canWrite) document.getElementById("add").onclick = () => entityForm(id, null);
  if (cfg.search) {
    const q = document.getElementById("q");
    q.oninput = debounce(async () => {
      const d = await api("GET", `/api/${id}?limit=500&q=${encodeURIComponent(q.value)}`);
      document.getElementById("tb").innerHTML = rowsHtml(id, d.rows || [], cfg);
      bindRowActions(id, cfg);
    }, 250);
  }
  bindRowActions(id, cfg);
}

function rowsHtml(id, rows, cfg) {
  const canWrite = ROLE_OK(...cfg.roles);
  return rows.map((r) => `<tr data-id="${r.id}">
    ${cfg.columns.map((c) => `<td>${cellValue(r, c)}</td>`).join("")}
    <td>
      ${cfg.profile ? `<a data-act="profile">${t("profile")}</a> · ` : ""}
      ${id === "samples" ? `<a data-act="components">${t("components")}</a> · ` : ""}
      ${canWrite ? `<a data-act="edit">${t("edit")}</a> · <a data-act="del">${t("del")}</a>` : ""}
      ${state.me.role === "admin" ? ` · <a data-act="hist">${t("history")}</a>` : ""}
    </td></tr>`).join("");
}

function bindRowActions(id, cfg) {
  document.querySelectorAll("#tb tr").forEach((tr) => {
    const rid = tr.dataset.id;
    tr.querySelectorAll("a[data-act]").forEach((a) => {
      a.onclick = async () => {
        const act = a.dataset.act;
        if (act === "edit") { const row = await api("GET", `/api/${id}/${rid}`); entityForm(id, row); }
        else if (act === "del") { if (confirm(t("confirm_del"))) { await api("DELETE", `/api/${id}/${rid}`); toast(t("deleted")); renderView(id); } }
        else if (act === "hist") showHistory(id, rid);
        else if (act === "profile") showCustomerProfile(rid);
        else if (act === "components") manageSample(rid);
      };
    });
  });
}

function fieldInput(f, val) {
  const id = "f_" + f.k;
  if (f.type === "textarea") return `<textarea id="${id}">${esc(val ?? "")}</textarea>`;
  if (f.type === "select") {
    let opts = `<option value="">—</option>`;
    if (f.lookup) {
      for (const o of (state.lookups[f.lookup] || [])) opts += `<option value="${o.id}" ${String(val) === String(o.id) ? "selected" : ""}>${esc(o.name || o.code || o.id)}</option>`;
    } else for (const [v, lk] of f.options) opts += `<option value="${v}" ${val === v ? "selected" : ""}>${t(lk)}</option>`;
    return `<select id="${id}">${opts}</select>`;
  }
  let v = val ?? "";
  if (f.type === "money" && val != null) v = (val / 100);
  if (f.type === "milli" && val != null) v = (val / 1000);
  const type = (f.type === "num" || f.type === "money" || f.type === "milli") ? "number" : (f.type === "date" ? "date" : "text");
  return `<input id="${id}" type="${type}" step="any" value="${esc(v)}">`;
}

const LOOKUP_INT_KEYS = ["customer_id", "supplier_id", "ref_order_id", "accessory_id", "sample_id", "order_id"];
function collectFields(fields) {
  const out = {};
  for (const f of fields) {
    const el = document.getElementById("f_" + f.k);
    if (!el) continue;
    let v = el.value;
    if (v === "") { out[f.k] = null; continue; }
    if (f.type === "money") v = Math.round(parseFloat(v) * 100);
    else if (f.type === "milli") v = Math.round(parseFloat(v) * 1000);
    else if (f.type === "num") v = parseInt(v, 10);
    else if (f.type === "select" && (f.lookup || LOOKUP_INT_KEYS.includes(f.k))) v = parseInt(v, 10);
    out[f.k] = v;
  }
  return out;
}

function entityForm(id, row, cfgOverride, onSaved) {
  const cfg = cfgOverride || ENTITIES[id];
  const body = `<div class="form-grid">${cfg.fields.map((f) => `
    <div class="field ${f.full ? "full" : ""}"><label>${t(f.t)}${f.req ? " *" : ""}</label>${fieldInput(f, row ? row[f.k] : f.default)}</div>`).join("")}</div>
    <div class="modal-actions"><button class="btn secondary" id="m-cancel">${t("cancel")}</button>
    <button class="btn" id="m-save">${t("save")}</button></div>`;
  modal((row ? t("edit") : t("add")) + " · " + t(cfg.label || id), body, () => {
    bindSourceCostToggle(document);
    document.getElementById("m-cancel").onclick = closeModal;
    document.getElementById("m-save").onclick = async () => {
      const payload = collectFields(cfg.fields);
      try {
        if (row) await api("PUT", `/api/${id}/${row.id}`, payload);
        else await api("POST", `/api/${id}`, payload);
        toast(t("saved")); closeModal();
        if (onSaved) onSaved(); else renderView(id);
        await refreshLookups();
      } catch (e) { toast(e.message, "err"); }
    };
  });
}

function debounce(fn, ms) { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; }

// When a component's Source is "customer", its cost is forced to 0 (FRS rule).
// Reflect that in the form: zero + disable the cost field with a hint.
function bindSourceCostToggle(scope) {
  const root = scope || document;
  const src = root.querySelector("#f_source");
  const cost = root.querySelector("#f_cost_cents");
  if (!src || !cost) return;
  let hint = cost.parentElement.querySelector(".cost-hint");
  if (!hint) {
    hint = document.createElement("div");
    hint.className = "cost-hint muted"; hint.style.fontSize = "11px"; hint.style.marginTop = "4px";
    cost.parentElement.appendChild(hint);
  }
  const apply = () => {
    const isCust = src.value === "customer";
    cost.disabled = isCust;
    cost.style.opacity = isCust ? "0.5" : "1";
    if (isCust) cost.value = 0;
    hint.textContent = isCust ? t("supplied_by_customer") : "";
  };
  src.addEventListener("change", apply); apply();
}

// ---------------------------------------------------------------------------
// History (admin)
// ---------------------------------------------------------------------------
function diffHtml(d) {
  if (!d || !Object.keys(d).length) return "";
  return `<div class="diff">${Object.entries(d).map(([k, v]) =>
    `${esc(k)}: <span class="from">${esc(v.from)}</span> → <span class="to">${esc(v.to)}</span>`).join("<br>")}</div>`;
}
function feedItem(r) {
  return `<div class="feed-item"><div class="feed-head">
    <b>${esc(r.actor_name || r.actor_user_id || "—")}</b>
    <span class="tag gray">${esc(r.action)}</span>
    <span class="muted">${esc(r.entity)}${r.entity_id ? " #" + r.entity_id : ""}</span>
    <span class="muted" style="margin-inline-start:auto">${esc(r.ts)}</span>
  </div>${r.summary ? `<div class="muted">${esc(r.summary)}</div>` : ""}${diffHtml(r.diff)}</div>`;
}
async function showHistory(entity, id) {
  const data = await api("GET", `/api/${entity}/${id}/history`);
  const items = (data.history || []).map(feedItem).join("") || `<p class="muted">${t("none")}</p>`;
  modal(t("history") + " · " + entity + " #" + id,
    items + `<div class="modal-actions"><button class="btn secondary" id="m-close">${t("cancel")}</button></div>`,
    (root) => root.querySelector("#m-close").onclick = closeModal);
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------
const stat = (n, l) => `<div class="card stat"><div class="n">${n ?? 0}</div><div class="l">${t(l)}</div></div>`;
const emptyRow = () => `<tr><td class="muted">${t("none")}</td></tr>`;
async function renderDashboard(view) {
  const d = await api("GET", "/api/dashboard");
  const c = d.counts;
  view.innerHTML = `
    <div class="row" style="margin-bottom:18px">
      ${stat(c.customers, "customers")}${stat(c.open_orders, "open_orders")}
      ${stat(c.unpaid_invoices, "unpaid_invoices")}${stat(c.samples, "samples")}
    </div>
    <div class="row">
      <div class="card" style="flex:2;min-width:320px"><h3>${t("open_orders")}</h3>
        <table><tbody>${(d.open_orders || []).map((o) => `<tr><td>${esc(o.code || o.id)}</td><td>${esc(o.customer_name || "")}</td><td>${esc(o.quantity)}</td><td>${statusTag(o.status)}</td><td class="muted">${esc(o.delivery_date || "")}</td></tr>`).join("") || emptyRow()}</tbody></table></div>
      <div class="card" style="flex:2;min-width:320px"><h3>${t("unpaid_invoices")}</h3>
        <table><tbody>${(d.unpaid_invoices || []).map((i) => `<tr><td>${esc(i.invoice_no || i.id)}</td><td>${esc(i.customer_name || "")}</td><td>${money(i.balance_cents)}</td><td>${statusTag(i.status)}</td></tr>`).join("") || emptyRow()}</tbody></table></div>
    </div>
    <div class="row" style="margin-top:18px">
      <div class="card" style="flex:1;min-width:320px"><h3>${t("low_stock")}</h3>
        <table><tbody>${(d.low_stock_rolls || []).map((r) => `<tr><td>${esc(r.roll_no || r.id)}</td><td>${esc(r.color || "")}</td><td>${milli(r.remaining_m_milli)} m</td></tr>`).join("") || emptyRow()}</tbody></table></div>
      <div class="card" style="flex:2;min-width:320px"><h3>${t("recent_activity")}</h3>
        ${(d.recent_activity || []).map((r) => `<div class="feed-item"><div class="feed-head"><b>${esc(r.actor_name || "—")}</b><span class="tag gray">${esc(r.action)}</span><span class="muted">${esc(r.summary || r.entity)}</span><span class="muted" style="margin-inline-start:auto">${esc(r.ts)}</span></div></div>`).join("") || `<p class="muted">${t("none")}</p>`}</div>
    </div>`;
}

// ---------------------------------------------------------------------------
// Samples + components
// ---------------------------------------------------------------------------
async function renderSamples(view) { await renderEntity(view, "samples"); }

const SAMPLE_PARTS = [
  { id: "sample_fabric", title: "fabric", hint: "hint_fabric", cols: ["fabric_type", "qty_milli:milli", "unit", "cost_cents:money", "source"],
    fields: [{ k: "fabric_type", t: "fabric_type", type: "text" }, { k: "qty_milli", t: "quantity", type: "milli" },
      { k: "unit", t: "unit", type: "select", options: [["meter", "length_m"], ["kg", "kg"]] },
      { k: "cost_cents", t: "unit_cost", type: "money" },
      { k: "source", t: "source", type: "select", options: [["factory", "factory_src"], ["customer", "customer_src"]] }] },
  { id: "sample_blueprint", title: "blueprint", cols: ["design_name", "version", "approved_sizes", "cost_cents:money", "source"],
    fields: [{ k: "design_name", t: "design_name", type: "text" }, { k: "version", t: "version", type: "text" },
      { k: "approved_sizes", t: "approved_sizes", type: "text" }, { k: "cost_cents", t: "unit_cost", type: "money" },
      { k: "source", t: "source", type: "select", options: [["factory", "factory_src"], ["customer", "customer_src"]] }] },
  { id: "sample_printing", title: "printing", cols: ["print_type", "description", "cost_cents:money", "source"],
    fields: [{ k: "print_type", t: "print_type", type: "text" }, { k: "description", t: "description", type: "text" },
      { k: "cost_cents", t: "unit_cost", type: "money" },
      { k: "source", t: "source", type: "select", options: [["factory", "factory_src"], ["customer", "customer_src"]] }] },
  { id: "sample_manufacturing", title: "manufacturing", cols: ["cut_cost_cents:money", "sew_cost_cents:money", "finish_cost_cents:money"],
    fields: [{ k: "cut_cost_cents", t: "cut_cost", type: "money" }, { k: "sew_cost_cents", t: "sew_cost", type: "money" },
      { k: "finish_cost_cents", t: "finish_cost", type: "money" }] },
  { id: "product_specs", title: "spec", hint: "hint_consumption", cols: ["fabric_meters_per_piece_milli:milli"],
    fields: [{ k: "fabric_meters_per_piece_milli", t: "fabric_per_piece", type: "milli" }] },
  { id: "spec_accessories", title: "required_acc", cols: ["accessory_id:acc", "qty_per_piece_milli:milli"],
    fields: [{ k: "accessory_id", t: "accessories", type: "select", lookup: "accessories" },
      { k: "qty_per_piece_milli", t: "quantity", type: "milli" }] },
];

function partCell(r, c) {
  const [k, type] = c.split(":");
  if (type === "money") return money(r[k]); if (type === "milli") return milli(r[k]);
  if (type === "acc") { const a = (state.lookups.accessories || []).find((x) => x.id === r[k]); return esc(a ? a.name : r[k]); }
  if (k === "source") return statusTag(r[k]);
  return esc(r[k] ?? "");
}

async function manageSample(sampleId) {
  const canWrite = ROLE_OK("sales", "production");
  const blocks = [];
  for (const p of SAMPLE_PARTS) {
    const d = await api("GET", `/api/${p.id}?limit=200`);
    const rows = (d.rows || []).filter((r) => String(r.sample_id) === String(sampleId));
    blocks.push(`<div class="card" style="margin-bottom:12px"><div class="section-head"><h3 style="margin:0">${t(p.title)}</h3>
      ${canWrite ? `<button class="btn small" data-part="${p.id}">+ ${t("add")}</button>` : ""}</div>
      ${p.hint ? `<p class="muted" style="font-size:12px;margin:0 0 10px">💡 ${t(p.hint)}</p>` : ""}
      <table><tbody>${rows.map((r) => `<tr><td>${p.cols.map((c) => partCell(r, c)).join("</td><td>")}</td>
        ${canWrite ? `<td><a data-del="${p.id}:${r.id}">${t("del")}</a></td>` : ""}</tr>`).join("") || `<tr><td class="muted">${t("none")}</td></tr>`}</tbody></table></div>`);
  }
  modal(t("components") + " · #" + sampleId, blocks.join("") +
    `<div class="modal-actions"><button class="btn secondary" id="m-close">${t("cancel")}</button></div>`, (root) => {
    root.querySelector("#m-close").onclick = closeModal;
    root.querySelectorAll("[data-part]").forEach((b) => {
      b.onclick = () => {
        const part = SAMPLE_PARTS.find((p) => p.id === b.dataset.part);
        modal(t("add") + " · " + t(part.title),
          `<div class="form-grid">${part.fields.map((f) => `<div class="field ${f.full ? "full" : ""}"><label>${t(f.t)}</label>${fieldInput(f, f.default)}</div>`).join("")}</div>
           <div class="modal-actions"><button class="btn secondary" id="m-cancel">${t("cancel")}</button><button class="btn" id="m-save">${t("save")}</button></div>`,
          (r2) => {
            bindSourceCostToggle(r2);
            r2.querySelector("#m-cancel").onclick = () => manageSample(sampleId);
            r2.querySelector("#m-save").onclick = async () => {
              const payload = collectFields(part.fields); payload.sample_id = parseInt(sampleId, 10);
              try { await api("POST", `/api/${part.id}`, payload); toast(t("saved")); await refreshLookups(); manageSample(sampleId); }
              catch (e) { toast(e.message, "err"); }
            };
          });
      };
    });
    root.querySelectorAll("[data-del]").forEach((a) => {
      a.onclick = async () => { const [pid, rid] = a.dataset.del.split(":"); if (confirm(t("confirm_del"))) { await api("DELETE", `/api/${pid}/${rid}`); manageSample(sampleId); } };
    });
  });
}

// ---------------------------------------------------------------------------
// Orders
// ---------------------------------------------------------------------------
const STAGES = ["new", "prep", "cutting", "printing", "sewing", "finishing", "packing", "ready", "delivered"];
async function renderOrders(view) {
  const d = await api("GET", "/api/orders");
  const canWrite = ROLE_OK("production", "sales");
  view.innerHTML = `<div class="section-head"><h2>${t("orders")}</h2>
    ${canWrite ? `<button class="btn" id="add">+ ${t("add")}</button>` : ""}</div>
    <div class="card"><table><thead><tr><th>${t("code")}</th><th>${t("customer")}</th><th>${t("sample")}</th>
    <th>${t("quantity")}</th><th>${t("est_total")}</th><th>${t("status")}</th><th>${t("actions")}</th></tr></thead>
    <tbody>${(d.rows || []).map((o) => `<tr><td>${esc(o.code || o.id)}</td><td>${esc(o.customer_name || "")}</td>
      <td>${esc(o.sample_name || "")}</td><td>${esc(o.quantity)}</td><td>${money(o.est_total_cents)}</td>
      <td>${statusTag(o.status)}</td><td><a data-open="${o.id}">${t("manage")}</a>${state.me.role === "admin" ? ` · <a data-hist="${o.id}">${t("history")}</a>` : ""}</td></tr>`).join("") || emptyRow()}</tbody></table></div>`;
  if (canWrite) document.getElementById("add").onclick = orderForm;
  view.querySelectorAll("[data-open]").forEach((a) => a.onclick = () => orderDetail(a.dataset.open));
  view.querySelectorAll("[data-hist]").forEach((a) => a.onclick = () => showHistory("orders", a.dataset.hist));
}

function orderForm() {
  const fields = [
    { k: "code", t: "code", type: "text" },
    { k: "customer_id", t: "customer", type: "select", lookup: "customers", req: true },
    { k: "sample_id", t: "sample", type: "select", lookup: "samples" },
    { k: "quantity", t: "quantity", type: "num" },
    { k: "order_date", t: "order_date", type: "date" }, { k: "delivery_date", t: "delivery_date", type: "date" },
    { k: "unit_cost_cents", t: "unit_cost", type: "money" },
    { k: "notes", t: "notes", type: "textarea", full: true },
  ];
  modal(t("add") + " · " + t("orders"),
    `<div class="form-grid">${fields.map((f) => `<div class="field ${f.full ? "full" : ""}"><label>${t(f.t)}${f.req ? " *" : ""}</label>${fieldInput(f, f.default)}</div>`).join("")}</div>
     <div class="modal-actions"><button class="btn secondary" id="m-cancel">${t("cancel")}</button><button class="btn" id="m-save">${t("save")}</button></div>`,
    (root) => {
      root.querySelector("#m-cancel").onclick = closeModal;
      root.querySelector("#m-save").onclick = async () => {
        const p = collectFields(fields);
        try { await api("POST", "/api/orders", p); toast(t("saved")); closeModal(); renderView("orders"); }
        catch (e) { toast(e.message, "err"); }
      };
    });
}

async function orderDetail(id) {
  const o = await api("GET", `/api/orders/${id}`);
  const est = o.estimate || {};
  const stageIdx = STAGES.indexOf(o.status);
  const pills = STAGES.map((s, i) => `<span class="stage-pill ${i < stageIdx ? "done" : i === stageIdx ? "current" : ""}">${t(s)}</span>`).join("");
  const accRows = (est.required_accessories || []).map((a) => `<tr><td>${esc(a.name)}</td><td>${milli(a.required_milli)}</td><td>${money(a.cost_total_cents)}</td></tr>`).join("");
  const canAdvance = ROLE_OK("production");
  modal(`${t("orders")} · ${esc(o.code || o.id)}`, `
    <div class="row"><div class="card stat"><div class="n">${money(o.est_total_cents)}</div><div class="l">${t("est_total")}</div></div>
    <div class="card stat"><div class="n">${money(o.paid_cents)}</div><div class="l">${t("paid")}</div></div>
    <div class="card stat"><div class="n">${money(o.balance_cents)}</div><div class="l">${t("balance")}</div></div></div>
    <h4>${t("stage")}</h4><div class="stages">${pills}</div>
    ${canAdvance ? `<div class="toolbar"><select id="stage-sel">${STAGES.map((s) => `<option value="${s}" ${s === o.status ? "selected" : ""}>${t(s)}</option>`).join("")}</select>
      <input id="stage-resp" placeholder="${t("responsible")}"><button class="btn" id="adv">${t("advance_stage")}</button></div>` : ""}
    <h4>${t("est_breakdown")}</h4>
    <p class="muted">${t("fabric_per_piece_used")}: ${milli(est.fabric_per_piece_milli)} m · ${t("src_" + (est.fabric_source || "none"))}</p>
    <p class="muted">${t("required_fabric")}: ${milli(est.required_fabric_milli)} m</p>
    <table><thead><tr><th>${t("accessories")}</th><th>${t("quantity")}</th><th>${t("line_total")}</th></tr></thead><tbody>${accRows || emptyRow()}</tbody></table>
    <div class="modal-actions"><button class="btn secondary" id="m-close">${t("cancel")}</button></div>`, (root) => {
    root.querySelector("#m-close").onclick = closeModal;
    const adv = root.querySelector("#adv");
    if (adv) adv.onclick = async () => {
      try { await api("POST", `/api/orders/${id}/advance`, { stage: root.querySelector("#stage-sel").value, responsible: root.querySelector("#stage-resp").value });
        toast(t("saved")); orderDetail(id); } catch (e) { toast(e.message, "err"); }
    };
  });
}

// ---------------------------------------------------------------------------
// Invoices + payments
// ---------------------------------------------------------------------------
async function renderInvoices(view) {
  const d = await api("GET", "/api/invoices");
  const canWrite = ROLE_OK("accountant");
  view.innerHTML = `<div class="section-head"><h2>${t("invoices")}</h2>
    ${canWrite ? `<button class="btn" id="add">+ ${t("add")}</button>` : ""}</div>
    <div class="card"><table><thead><tr><th>${t("invoice_no")}</th><th>${t("customer")}</th><th>${t("total")}</th>
    <th>${t("paid")}</th><th>${t("balance")}</th><th>${t("status")}</th><th>${t("actions")}</th></tr></thead>
    <tbody>${(d.rows || []).map((i) => `<tr><td>${esc(i.invoice_no || i.id)}</td><td>${esc(i.customer_name || "")}</td>
      <td>${money(i.total_cents)}</td><td>${money(i.paid_cents)}</td><td>${money(i.balance_cents)}</td>
      <td>${statusTag(i.status)}</td><td><a data-open="${i.id}">${t("manage")}</a></td></tr>`).join("") || emptyRow()}</tbody></table></div>`;
  if (canWrite) document.getElementById("add").onclick = invoiceForm;
  view.querySelectorAll("[data-open]").forEach((a) => a.onclick = () => invoiceDetail(a.dataset.open));
}

function invoiceForm() {
  let lines = [{ description: "", qty: 1, unit_price: 0 }];
  const lineRow = (l, i) => `<div class="form-grid" style="margin-bottom:6px">
    <div class="field full"><input data-l="${i}" data-f="description" placeholder="${t("description")}" value="${esc(l.description)}"></div>
    <div class="field"><input data-l="${i}" data-f="qty" type="number" placeholder="${t("quantity")}" value="${l.qty}"></div>
    <div class="field"><input data-l="${i}" data-f="unit_price" type="number" step="any" placeholder="${t("unit_price")}" value="${l.unit_price}"></div></div>`;
  const html = `<div class="form-grid">
      <div class="field"><label>${t("customer")} *</label><select id="f_customer_id">${(state.lookups.customers || []).map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("")}</select></div>
      <div class="field"><label>${t("orders")}</label><select id="f_order_id"><option value="">—</option>${(state.lookups.orders || []).map((o) => `<option value="${o.id}">${esc(o.code || o.id)}</option>`).join("")}</select></div>
      <div class="field"><label>${t("invoice_no")}</label><input id="f_invoice_no"></div>
      <div class="field"><label>${t("invoice_date")}</label><input id="f_invoice_date" type="date"></div>
      <div class="field"><label>${t("discount")}</label><input id="f_discount" type="number" step="any" value="0"></div>
      <div class="field"><label>${t("tax")}</label><input id="f_tax" type="number" step="any" value="0"></div>
    </div><h4>${t("add_line")}</h4><div id="lines"></div><button class="btn small secondary" id="add-line">+ ${t("add_line")}</button>
    <div class="modal-actions"><button class="btn secondary" id="m-cancel">${t("cancel")}</button><button class="btn" id="m-save">${t("save")}</button></div>`;
  modal(t("add") + " · " + t("invoices"), html, (root) => {
    const drawLines = () => { root.querySelector("#lines").innerHTML = lines.map(lineRow).join(""); bindLineInputs(); };
    const bindLineInputs = () => root.querySelectorAll("[data-l]").forEach((inp) => inp.oninput = () => { lines[+inp.dataset.l][inp.dataset.f] = inp.value; });
    drawLines();
    root.querySelector("#add-line").onclick = () => { lines.push({ description: "", qty: 1, unit_price: 0 }); drawLines(); };
    root.querySelector("#m-cancel").onclick = closeModal;
    root.querySelector("#m-save").onclick = async () => {
      const payload = {
        customer_id: parseInt(root.querySelector("#f_customer_id").value, 10),
        order_id: root.querySelector("#f_order_id").value ? parseInt(root.querySelector("#f_order_id").value, 10) : null,
        invoice_no: root.querySelector("#f_invoice_no").value || null,
        invoice_date: root.querySelector("#f_invoice_date").value || null,
        discount_cents: Math.round(parseFloat(root.querySelector("#f_discount").value || 0) * 100),
        tax_cents: Math.round(parseFloat(root.querySelector("#f_tax").value || 0) * 100),
        lines: lines.filter((l) => l.description).map((l) => ({ description: l.description, qty: parseInt(l.qty, 10) || 0, unit_price_cents: Math.round(parseFloat(l.unit_price || 0) * 100) })),
      };
      try { await api("POST", "/api/invoices", payload); toast(t("saved")); closeModal(); renderView("invoices"); }
      catch (e) { toast(e.message, "err"); }
    };
  });
}

async function invoiceDetail(id) {
  const inv = await api("GET", `/api/invoices/${id}`);
  const canPay = ROLE_OK("accountant");
  const lines = (inv.lines || []).map((l) => `<tr><td>${esc(l.description || "")}</td><td>${esc(l.qty)}</td><td>${money(l.unit_price_cents)}</td><td>${money(l.line_total_cents)}</td></tr>`).join("");
  const pays = (inv.payments || []).map((p) => `<tr><td>${t(p.kind)}</td><td>${money(p.amount_cents)}</td><td class="muted">${esc(p.payment_date || "")}</td>${canPay ? `<td><a data-delpay="${p.id}">${t("del")}</a></td>` : ""}</tr>`).join("");
  modal(`${t("invoices")} · ${esc(inv.invoice_no || inv.id)}`, `
    <div class="row"><div class="card stat"><div class="n">${money(inv.total_cents)}</div><div class="l">${t("total")}</div></div>
    <div class="card stat"><div class="n">${money(inv.paid_cents)}</div><div class="l">${t("paid")}</div></div>
    <div class="card stat"><div class="n">${money(inv.balance_cents)}</div><div class="l">${t("balance")}</div></div>
    <div class="card stat"><div class="n">${statusTag(inv.status)}</div><div class="l">${t("status")}</div></div></div>
    <table><thead><tr><th>${t("description")}</th><th>${t("quantity")}</th><th>${t("unit_price")}</th><th>${t("line_total")}</th></tr></thead><tbody>${lines || emptyRow()}</tbody></table>
    <h4>${t("payments")}</h4><table><tbody>${pays || emptyRow()}</tbody></table>
    ${canPay ? `<div class="toolbar" style="margin-top:10px">
      <input id="pay-amt" type="number" step="any" placeholder="${t("amount")}">
      <select id="pay-kind"><option value="advance">${t("advance")}</option><option value="progress" selected>${t("progress")}</option><option value="final">${t("final")}</option></select>
      <button class="btn" id="pay-btn">${t("record_payment")}</button></div>` : ""}
    <div class="modal-actions"><button class="btn secondary" id="m-close">${t("cancel")}</button></div>`, (root) => {
    root.querySelector("#m-close").onclick = closeModal;
    const pb = root.querySelector("#pay-btn");
    if (pb) pb.onclick = async () => {
      try { await api("POST", "/api/payments", { customer_id: inv.customer_id, invoice_id: inv.id, order_id: inv.order_id,
        amount_cents: Math.round(parseFloat(root.querySelector("#pay-amt").value || 0) * 100), kind: root.querySelector("#pay-kind").value });
        toast(t("saved")); invoiceDetail(id); } catch (e) { toast(e.message, "err"); }
    };
    root.querySelectorAll("[data-delpay]").forEach((a) => a.onclick = async () => { if (confirm(t("confirm_del"))) { await api("DELETE", `/api/payments/${a.dataset.delpay}`); invoiceDetail(id); } });
  });
}

// ---------------------------------------------------------------------------
// Customer profile
// ---------------------------------------------------------------------------
async function showCustomerProfile(id) {
  const c = await api("GET", `/api/customers/${id}/profile`);
  modal(t("profile") + " · " + esc(c.name), `
    <div class="row"><div class="card stat"><div class="n">${money(c.billed_cents)}</div><div class="l">${t("total")}</div></div>
    <div class="card stat"><div class="n">${money(c.paid_cents)}</div><div class="l">${t("paid")}</div></div>
    <div class="card stat"><div class="n">${money(c.balance_cents)}</div><div class="l">${t("balance")}</div></div></div>
    <p class="muted">${esc(c.phone || "")} · ${esc(c.email || "")}</p>
    <h4>${t("orders")}</h4><table><tbody>${(c.orders || []).map((o) => `<tr><td>${esc(o.code || o.id)}</td><td>${esc(o.quantity)}</td><td>${statusTag(o.status)}</td><td>${money(o.est_total_cents)}</td></tr>`).join("") || emptyRow()}</tbody></table>
    <h4>${t("samples")}</h4><table><tbody>${(c.samples || []).map((s) => `<tr><td>${esc(s.name)}</td><td>${statusTag(s.status)}</td></tr>`).join("") || emptyRow()}</tbody></table>
    <h4>${t("fabric_rolls")}</h4><table><tbody>${(c.fabric_rolls || []).map((r) => `<tr><td>${esc(r.roll_no || r.id)}</td><td>${esc(r.color || "")}</td><td>${milli(r.remaining_m_milli)} m</td></tr>`).join("") || emptyRow()}</tbody></table>
    <div class="modal-actions"><button class="btn secondary" id="m-close">${t("cancel")}</button></div>`,
    (root) => root.querySelector("#m-close").onclick = closeModal);
}

// ---------------------------------------------------------------------------
// Activity log (admin)
// ---------------------------------------------------------------------------
async function renderActivity(view) {
  view.innerHTML = `<div class="section-head"><h2>${t("activity")}</h2>
    <div class="toolbar"><input id="aq" placeholder="${t("search")}"><button class="btn secondary" id="arefresh">↻</button></div></div>
    <div class="card" id="afeed"></div>`;
  const load = async () => {
    const q = document.getElementById("aq").value;
    const d = await api("GET", `/api/activity?page_size=100&q=${encodeURIComponent(q)}`);
    document.getElementById("afeed").innerHTML = (d.rows || []).map(feedItem).join("") || `<p class="muted">${t("none")}</p>`;
  };
  document.getElementById("aq").oninput = debounce(load, 300);
  document.getElementById("arefresh").onclick = load;
  await load();
}

// ---------------------------------------------------------------------------
// Users (admin)
// ---------------------------------------------------------------------------
async function renderUsers(view) {
  const d = await api("GET", "/api/users");
  const roles = ["admin", "accountant", "production", "sales"];
  view.innerHTML = `<div class="section-head"><h2>${t("users")}</h2></div><div class="card"><table>
    <thead><tr><th>${t("name")}</th><th>ID</th><th>${t("role")}</th><th>${t("active")}</th></tr></thead>
    <tbody>${(d.rows || []).map((u) => `<tr><td>${esc(u.name || u.username || "")}</td><td class="muted">${u.tg_user_id}</td>
      <td><select data-role="${u.id}">${roles.map((r) => `<option value="${r}" ${u.role === r ? "selected" : ""}>${t("role_" + r)}</option>`).join("")}</select></td>
      <td><input type="checkbox" data-active="${u.id}" ${u.active ? "checked" : ""}></td></tr>`).join("")}</tbody></table></div>`;
  view.querySelectorAll("[data-role]").forEach((s) => s.onchange = async () => { try { await api("PUT", `/api/users/${s.dataset.role}/role`, { role: s.value }); toast(t("saved")); } catch (e) { toast(e.message, "err"); } });
  view.querySelectorAll("[data-active]").forEach((c) => c.onchange = async () => { try { await api("PUT", `/api/users/${c.dataset.active}/active`, { active: c.checked }); toast(t("saved")); } catch (e) { toast(e.message, "err"); } });
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
async function refreshLookups() { try { state.lookups = await api("GET", "/api/lookups"); } catch (e) {} }

function applyLang() {
  document.documentElement.lang = LANG; document.documentElement.dir = LANG === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((el) => el.textContent = t(el.dataset.i18n));
  const lt = document.getElementById("lang-toggle"); if (lt) lt.textContent = LANG === "ar" ? "English" : "عربي";
}

function updateWhoami() {
  if (!state.me) return;
  const el = document.getElementById("whoami");
  if (el) el.textContent = `${state.me.name || state.me.user_id} · ${t("role_" + state.me.role)}`;
}

async function boot() {
  applyLang();
  try {
    state.me = await api("GET", "/api/me");
    LANG = state.me.language || LANG; localStorage.setItem("erp_lang", LANG); applyLang();
    await refreshLookups();
    document.getElementById("login").classList.add("hidden");
    document.getElementById("shell").classList.remove("hidden");
    updateWhoami();
    renderNav(); navigate("dashboard");
  } catch (e) {
    await showLogin();
  }
  document.getElementById("logout").onclick = async () => { try { await api("POST", "/api/logout"); } catch (e) {} location.reload(); };
  document.getElementById("lang-toggle").onclick = async () => {
    LANG = LANG === "ar" ? "en" : "ar"; localStorage.setItem("erp_lang", LANG); applyLang();
    try { await api("PUT", "/api/me/language", { language: LANG }); } catch (e) {}
    updateWhoami();
    renderNav(); document.getElementById("crumb").textContent = t(currentView); renderView(currentView);
  };
}

async function showLogin() {
  document.getElementById("shell").classList.add("hidden");
  document.getElementById("login").classList.remove("hidden");
  const cfg = await api("GET", "/api/config").catch(() => ({}));
  window.onTelegramAuth = async (user) => {
    try { await api("POST", "/api/auth/telegram", user); location.reload(); }
    catch (e) { const er = document.getElementById("login-error"); er.textContent = e.message; er.classList.remove("hidden"); }
  };
  const cont = document.getElementById("tg-login-container");
  if (cfg.bot_username) {
    const s = document.createElement("script");
    s.async = true; s.src = "https://telegram.org/js/telegram-widget.js?22";
    s.setAttribute("data-telegram-login", cfg.bot_username);
    s.setAttribute("data-size", "large");
    s.setAttribute("data-onauth", "onTelegramAuth(user)");
    s.setAttribute("data-request-access", "write");
    cont.appendChild(s);
  } else {
    cont.innerHTML = `<p class="muted">Set BOT_USERNAME to enable Telegram login.</p>`;
  }
}

boot();
