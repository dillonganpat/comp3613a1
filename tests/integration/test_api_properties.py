"""Integration tests: /api/properties (public search, landlord create/delete)."""
from decimal import Decimal

from tests.conftest import bearer

NEW_PROPERTY = {
    "title": "Evans Street Loft", "location": "5 Evans Street, St. Augustine",
    "description": "Quiet loft.", "price_per_night": "520.00", "bedrooms": 2, "bathrooms": 1,
}


# ------------------------------------------------------------ read (public)
def test_list_properties_is_public_and_returns_listing(client, listing):
    resp = client.get("/api/properties")
    assert resp.status_code == 200
    assert [p["title"] for p in resp.json()] == ["Watts Street Studio"]


def test_list_properties_filter_by_location(client, listing):
    assert len(client.get("/api/properties", params={"location": "watts"}).json()) == 1
    assert client.get("/api/properties", params={"location": "tobago"}).json() == []


def test_list_properties_filter_by_price(client, listing):
    assert len(client.get("/api/properties", params={"min_price": 400, "max_price": 500}).json()) == 1
    assert client.get("/api/properties", params={"max_price": 100}).json() == []


def test_list_properties_min_above_max_is_422(client, listing):
    assert client.get("/api/properties", params={"min_price": 900, "max_price": 100}).status_code == 422


def test_list_properties_non_numeric_price_is_422(client):
    assert client.get("/api/properties", params={"max_price": "abc"}).status_code == 422


def test_get_property_by_id(client, listing):
    resp = client.get(f"/api/properties/{listing.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == listing.id and body["owner_id"] == listing.owner_id
    assert Decimal(body["price_per_night"]) == Decimal("450")


def test_get_missing_property_is_404(client):
    assert client.get("/api/properties/9999").status_code == 404


# ----------------------------------------------------------- create (landlord)
def test_landlord_creates_property_and_it_becomes_searchable(client, landlord_headers, landlord):
    resp = client.post("/api/properties", json=NEW_PROPERTY, headers=landlord_headers)
    assert resp.status_code == 201
    created = resp.json()
    assert created["owner_id"] == landlord.id and created["available"] is True
    titles = [p["title"] for p in client.get("/api/properties").json()]
    assert "Evans Street Loft" in titles


def test_create_property_without_token_is_401(client):
    resp = client.post("/api/properties", json=NEW_PROPERTY)
    assert resp.status_code == 401
    assert resp.headers["content-type"].startswith("application/json")


def test_create_property_as_tenant_is_403(client, tenant_headers):
    assert client.post("/api/properties", json=NEW_PROPERTY, headers=tenant_headers).status_code == 403


def test_create_property_negative_price_is_422(client, landlord_headers):
    resp = client.post("/api/properties", json={**NEW_PROPERTY, "price_per_night": "-10"}, headers=landlord_headers)
    assert resp.status_code == 422


def test_create_property_missing_title_is_422(client, landlord_headers):
    body = {k: v for k, v in NEW_PROPERTY.items() if k != "title"}
    assert client.post("/api/properties", json=body, headers=landlord_headers).status_code == 422


# ----------------------------------------------------------- delete (owner)
def test_owner_can_delete_own_property(client, landlord_headers, listing):
    assert client.delete(f"/api/properties/{listing.id}", headers=landlord_headers).status_code == 204
    assert client.get(f"/api/properties/{listing.id}").status_code == 404


def test_other_landlord_cannot_delete_property_403(client, landlord2_headers, listing):
    assert client.delete(f"/api/properties/{listing.id}", headers=landlord2_headers).status_code == 403
    assert client.get(f"/api/properties/{listing.id}").status_code == 200  # still there


def test_tenant_cannot_delete_property_403(client, tenant_headers, listing):
    assert client.delete(f"/api/properties/{listing.id}", headers=tenant_headers).status_code == 403


def test_delete_without_token_is_401(client, listing):
    assert client.delete(f"/api/properties/{listing.id}").status_code == 401


def test_delete_missing_property_is_404(client, landlord_headers):
    assert client.delete("/api/properties/9999", headers=landlord_headers).status_code == 404


def test_cannot_delete_property_that_has_bookings_409(client, landlord_headers, tenant_headers, listing):
    """Bookings reference the property; deleting it must be refused, not crash (500) on PostgreSQL."""
    from tests.conftest import future
    client.post("/api/bookings", headers=tenant_headers, json={
        "property_id": listing.id, "check_in": future(10).isoformat(), "check_out": future(12).isoformat()})
    resp = client.delete(f"/api/properties/{listing.id}", headers=landlord_headers)
    assert resp.status_code == 409
    assert client.get(f"/api/properties/{listing.id}").status_code == 200
