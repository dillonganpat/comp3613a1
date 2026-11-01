"""Integration tests: the browser-facing HTML pages (cookie login, redirects, access control)."""
from tests.conftest import future


def web_login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def test_login_page_loads(client):
    resp = client.get("/login")
    assert resp.status_code == 200 and "Sign in" in resp.text


def test_tenant_login_redirects_to_app_and_sets_cookie(client, tenant):
    resp = web_login(client, "bob", "bobpass")
    assert resp.status_code == 303
    assert resp.headers["location"].endswith("/app")
    assert "access_token" in resp.cookies


def test_landlord_login_redirects_to_admin(client, landlord):
    resp = web_login(client, "alice", "alicepass")
    assert resp.status_code == 303 and resp.headers["location"].endswith("/admin")


def test_wrong_password_returns_to_login_without_cookie(client, tenant):
    resp = web_login(client, "bob", "nope")
    assert resp.status_code == 303 and resp.headers["location"].endswith("/login")
    assert "access_token" not in resp.cookies


def test_browse_page_requires_login(client):
    resp = client.get("/app")
    assert resp.status_code == 401
    assert "Unauthorized" in resp.text


def test_logged_in_tenant_sees_listings_and_filter_works(client, tenant, listing):
    web_login(client, "bob", "bobpass")
    assert "Watts Street Studio" in client.get("/app").text
    assert "No listings match" in client.get("/app", params={"location": "tobago"}).text


def test_tenant_cannot_open_landlord_dashboard(client, tenant):
    web_login(client, "bob", "bobpass")
    assert client.get("/admin").status_code == 401
    assert client.get("/properties/new").status_code == 401


def test_landlord_can_open_dashboard_and_add_property_form(client, landlord):
    web_login(client, "alice", "alicepass")
    assert client.get("/admin").status_code == 200
    assert client.get("/properties/new").status_code == 200


def test_landlord_publishes_property_through_form(client, landlord):
    web_login(client, "alice", "alicepass")
    resp = client.post("/properties/new", data={
        "title": "Rapsey Loft", "location": "21 Rapsey St", "description": "Nice",
        "price_per_night": "550", "bedrooms": "1", "bathrooms": "1"})
    assert resp.status_code == 303
    assert "Rapsey Loft" in client.get("/admin").text


def test_tenant_books_through_detail_page_form(client, tenant, listing):
    web_login(client, "bob", "bobpass")
    resp = client.post("/bookings/create", data={
        "property_id": listing.id, "check_in": future(10).isoformat(), "check_out": future(12).isoformat()})
    assert resp.status_code == 303 and resp.headers["location"].endswith("/app")


def test_booking_unknown_property_is_404_not_500(client, tenant):
    web_login(client, "bob", "bobpass")
    resp = client.post("/bookings/create", data={
        "property_id": 9999, "check_in": future(10).isoformat(), "check_out": future(12).isoformat()})
    assert resp.status_code == 404


def test_logout_clears_cookie_and_redirects(client, tenant):
    web_login(client, "bob", "bobpass")
    resp = client.get("/logout")
    assert resp.status_code == 303 and resp.headers["location"].endswith("/login")


def test_register_creates_account_that_can_log_in(client):
    resp = client.post("/register", data={"username": "erin", "email": "erin@example.com", "password": "erinpass1"})
    assert resp.status_code == 303 and resp.headers["location"].endswith("/login")
    assert web_login(client, "erin", "erinpass1").headers["location"].endswith("/app")


def test_health_endpoint(client):
    assert client.get("/health").json() == {"ok": True}


def test_landlord_cannot_delete_property_with_bookings_from_dashboard(client, tenant, landlord, listing):
    web_login(client, "bob", "bobpass")
    client.post("/bookings/create", data={
        "property_id": listing.id, "check_in": future(10).isoformat(), "check_out": future(12).isoformat()})
    client.cookies.clear()
    web_login(client, "alice", "alicepass")
    resp = client.post(f"/properties/{listing.id}/delete")
    assert resp.status_code == 303                       # redirected back with a message, not a 500
    assert "Watts Street Studio" in client.get("/admin").text
