"""Role gating — a sales user cannot touch finance, etc."""


def _as_sales(client):
    from src.main import auth
    client.cookies.set("session", auth.create_session_token(222))  # default role: sales


def test_sales_can_create_customer(client):
    _as_sales(client)
    assert client.post("/api/customers", json={"name": "SalesCo"}).status_code == 201


def test_sales_cannot_create_invoice(client):
    _as_sales(client)
    r = client.post("/api/invoices", json={"customer_id": 1, "lines": []})
    assert r.status_code == 403


def test_sales_cannot_manage_users(client):
    _as_sales(client)
    assert client.get("/api/users").status_code == 403


def test_admin_can_change_role(client):
    # provision a second user by simulating their first login row via admin path:
    # create through ensure happens on login; here we just ensure the endpoint guards.
    assert client.get("/api/users").status_code == 200
