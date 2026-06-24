def test_config_is_public(anon_client):
    r = anon_client.get("/api/config")
    assert r.status_code == 200
    assert "bot_username" in r.json()


def test_me_requires_auth(anon_client):
    assert anon_client.get("/api/me").status_code == 401


def test_admin_me(client):
    r = client.get("/api/me")
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_index_served(anon_client):
    r = anon_client.get("/")
    assert r.status_code == 200
    assert "app.js?v=" in r.text  # cache-busting injection
