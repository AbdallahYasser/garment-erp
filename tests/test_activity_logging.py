"""The core requirement: every change (including the admin's) is logged."""


def test_crud_is_fully_logged(client):
    # create
    r = client.post("/api/customers", json={"name": "LogCo", "phone": "1"})
    assert r.status_code == 201
    cid = r.json()["id"]

    # update
    assert client.put(f"/api/customers/{cid}", json={"phone": "2"}).status_code == 200
    # delete
    assert client.delete(f"/api/customers/{cid}").status_code == 204

    # history for this record shows create + update + delete, all by admin 111
    hist = client.get(f"/api/customers/{cid}/history").json()["history"]
    actions = [h["action"] for h in hist]
    assert "create" in actions and "update" in actions and "delete" in actions
    assert all(h["actor_user_id"] == 111 for h in hist)
    assert all(h["actor_role"] == "admin" for h in hist)

    # the update entry carries a field-level diff
    upd = next(h for h in hist if h["action"] == "update")
    assert upd["diff"] and "phone" in upd["diff"]
    assert upd["diff"]["phone"]["from"] == "1"
    assert upd["diff"]["phone"]["to"] == "2"


def test_activity_feed_admin_only(client):
    assert client.get("/api/activity").status_code == 200


def test_activity_feed_blocked_for_non_admin(client):
    from src.main import auth
    # a plain sales user (222 not in ALLOWED_USERS) gets a valid token but no admin
    client.cookies.set("session", auth.create_session_token(222))
    assert client.get("/api/activity").status_code == 403
