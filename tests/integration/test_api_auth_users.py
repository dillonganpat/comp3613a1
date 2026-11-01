"""Integration tests: /api/signup, /api/auth, /api/users (HTTP + database)."""
from tests.conftest import bearer, login_token


# ----------------------------------------------------------------- signup
def test_signup_creates_account(client):
    resp = client.post("/api/signup", json={"username": "carol", "email": "carol@example.com", "password": "secret123"})
    assert resp.status_code == 201
    assert resp.json() == {"message": "account created"}


def test_new_account_can_log_in_and_is_a_tenant(client):
    client.post("/api/signup", json={"username": "carol", "email": "carol@example.com", "password": "secret123"})
    resp = client.post("/api/auth", json={"username": "carol", "password": "secret123"})
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    # a tenant must not be able to use landlord-only routes
    denied = client.post("/api/properties", headers=bearer(resp.json()["access_token"]),
                         json={"title": "t", "location": "l", "description": "d", "price_per_night": "100"})
    assert denied.status_code == 403


def test_signup_duplicate_username_is_400(client, tenant):
    resp = client.post("/api/signup", json={"username": "bob", "email": "new@example.com", "password": "secret123"})
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_signup_duplicate_email_is_400(client, tenant):
    resp = client.post("/api/signup", json={"username": "newbob", "email": "bob@example.com", "password": "secret123"})
    assert resp.status_code == 400


def test_signup_invalid_email_is_422(client):
    resp = client.post("/api/signup", json={"username": "carol", "email": "nope", "password": "secret123"})
    assert resp.status_code == 422


def test_signup_short_password_is_422(client):
    resp = client.post("/api/signup", json={"username": "carol", "email": "c@example.com", "password": "123"})
    assert resp.status_code == 422


def test_signup_missing_field_is_422(client):
    assert client.post("/api/signup", json={"username": "carol"}).status_code == 422


# ------------------------------------------------------------------- auth
def test_login_success_returns_token(client, tenant):
    resp = client.post("/api/auth", json={"username": "bob", "password": "bobpass"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_wrong_password_is_400(client, tenant):
    resp = client.post("/api/auth", json={"username": "bob", "password": "wrong"})
    assert resp.status_code == 400
    assert resp.json() == {"detail": "invalid credentials"}


def test_login_unknown_user_is_400(client):
    assert client.post("/api/auth", json={"username": "ghost", "password": "x"}).status_code == 400


# ------------------------------------------------------------------ users
def test_list_users_requires_token(client):
    resp = client.get("/api/users")
    assert resp.status_code == 401
    assert resp.headers["content-type"].startswith("application/json")


def test_list_users_forbidden_for_tenant(client, tenant_headers):
    assert client.get("/api/users", headers=tenant_headers).status_code == 403


def test_list_users_for_landlord_hides_password_hashes(client, landlord_headers, tenant):
    resp = client.get("/api/users", headers=landlord_headers)
    assert resp.status_code == 200
    users = resp.json()
    assert {u["username"] for u in users} == {"alice", "bob"}
    assert all("password" not in key for u in users for key in u)


def test_invalid_token_is_401(client):
    assert client.get("/api/users", headers=bearer("garbage")).status_code == 401
