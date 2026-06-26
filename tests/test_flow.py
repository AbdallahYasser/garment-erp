"""End-to-end core flow: sample -> order estimate -> order -> invoice -> payment."""


def _make_sample_with_spec(client):
    cid = client.post("/api/customers", json={"name": "FlowCo"}).json()["id"]
    sid = client.post("/api/samples", json={"name": "Tee", "customer_id": cid}).json()["id"]
    client.post("/api/sample_manufacturing", json={"sample_id": sid, "cost_cents": 1700})
    client.post("/api/product_specs", json={"sample_id": sid, "fabric_meters_per_piece_milli": 1500})
    aid = client.post("/api/accessories", json={"name": "Btn", "unit_price_cents": 250}).json()["id"]
    client.post("/api/spec_accessories", json={"sample_id": sid, "accessory_id": aid, "qty_per_piece_milli": 1000})
    return cid, sid


def test_estimate_math(client):
    cid, sid = _make_sample_with_spec(client)
    est = client.get("/api/orders/estimate", params={"sample_id": sid, "quantity": 500}).json()
    # 500 * (mfg 1700 + acc 250) = 975000 ; fabric is reference-only, not costed
    assert est["est_total_cents"] == 975000


def test_order_and_invoice_balance(client):
    cid, sid = _make_sample_with_spec(client)
    oid = client.post("/api/orders", json={"customer_id": cid, "sample_id": sid,
                                           "quantity": 500, "code": "O1"}).json()["id"]
    # advance stage
    o = client.post(f"/api/orders/{oid}/advance", json={"stage": "cutting"}).json()
    assert o["status"] == "cutting"

    iid = client.post("/api/invoices", json={
        "customer_id": cid, "order_id": oid, "invoice_no": "INV1",
        "lines": [{"description": "Tee", "qty": 500, "unit_price_cents": 9500}]}).json()["id"]
    inv = client.get(f"/api/invoices/{iid}").json()
    assert inv["total_cents"] == 4750000
    assert inv["status"] == "unpaid"

    client.post("/api/payments", json={"customer_id": cid, "invoice_id": iid,
                                       "amount_cents": 2000000, "kind": "advance"})
    inv = client.get(f"/api/invoices/{iid}").json()
    assert inv["status"] == "partial"
    assert inv["balance_cents"] == 2750000

    # full payment -> paid
    client.post("/api/payments", json={"customer_id": cid, "invoice_id": iid,
                                       "amount_cents": 2750000, "kind": "final"})
    inv = client.get(f"/api/invoices/{iid}").json()
    assert inv["status"] == "paid"
    assert inv["balance_cents"] == 0


def test_customer_supplied_component_is_zero_cost(client):
    cid = client.post("/api/customers", json={"name": "ZeroCo"}).json()["id"]
    sid = client.post("/api/samples", json={"name": "Hoodie", "customer_id": cid}).json()["id"]
    r = client.post("/api/sample_fabric", json={
        "sample_id": sid, "fabric_type": "cotton", "qty_milli": 100000,
        "cost_cents": 99999, "source": "customer"})
    assert r.status_code == 201
    assert r.json()["cost_cents"] == 0  # forced to zero per FRS
