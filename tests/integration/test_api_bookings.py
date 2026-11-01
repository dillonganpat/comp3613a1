"""Integration tests: /api/bookings (tenant booking flow and its rules)."""
from decimal import Decimal

from tests.conftest import future


def body(listing, a, b):
    return {"property_id": listing.id, "check_in": future(a).isoformat(), "check_out": future(b).isoformat()}


def test_tenant_books_property_total_is_nights_times_rate(client, tenant_headers, tenant, listing):
    resp = client.post("/api/bookings", json=body(listing, 10, 13), headers=tenant_headers)
    assert resp.status_code == 201
    booking = resp.json()
    assert booking["tenant_id"] == tenant.id
    assert booking["status"] == "pending"
    assert Decimal(booking["total_price"]) == Decimal("1350.00")   # 3 nights x 450


def test_booking_appears_in_my_bookings(client, tenant_headers, listing):
    client.post("/api/bookings", json=body(listing, 10, 12), headers=tenant_headers)
    mine = client.get("/api/bookings/mine", headers=tenant_headers).json()
    assert len(mine) == 1 and mine[0]["property_id"] == listing.id


def test_my_bookings_only_shows_own_bookings(client, tenant_headers, listing, session):
    from app.utilities.security import encrypt_password
    from app.models.user import User
    other = User(username="dave", email="dave@example.com", password_hash=encrypt_password("davepass1"), role="regular_user")
    session.add(other); session.commit()
    token = client.post("/api/auth", json={"username": "dave", "password": "davepass1"}).json()["access_token"]
    client.post("/api/bookings", json=body(listing, 10, 12), headers=tenant_headers)
    assert client.get("/api/bookings/mine", headers={"Authorization": f"Bearer {token}"}).json() == []


def test_overlapping_booking_is_409(client, tenant_headers, listing):
    assert client.post("/api/bookings", json=body(listing, 10, 14), headers=tenant_headers).status_code == 201
    resp = client.post("/api/bookings", json=body(listing, 12, 16), headers=tenant_headers)
    assert resp.status_code == 409
    assert "already booked" in resp.json()["detail"]


def test_back_to_back_booking_is_allowed(client, tenant_headers, listing):
    client.post("/api/bookings", json=body(listing, 10, 14), headers=tenant_headers)
    assert client.post("/api/bookings", json=body(listing, 14, 16), headers=tenant_headers).status_code == 201


def test_past_check_in_is_400(client, tenant_headers, listing):
    resp = client.post("/api/bookings", json=body(listing, -3, 2), headers=tenant_headers)
    assert resp.status_code == 400
    assert "past" in resp.json()["detail"]


def test_check_out_before_check_in_is_400(client, tenant_headers, listing):
    resp = client.post("/api/bookings", json=body(listing, 10, 8), headers=tenant_headers)
    assert resp.status_code == 400
    assert "after check-in" in resp.json()["detail"]


def test_malformed_date_is_422(client, tenant_headers, listing):
    resp = client.post("/api/bookings", json={"property_id": listing.id, "check_in": "tomorrow", "check_out": "later"},
                       headers=tenant_headers)
    assert resp.status_code == 422


def test_unknown_property_is_404(client, tenant_headers):
    resp = client.post("/api/bookings", json={"property_id": 9999, "check_in": future(5).isoformat(),
                                              "check_out": future(7).isoformat()}, headers=tenant_headers)
    assert resp.status_code == 404


def test_booking_without_token_is_401(client, listing):
    assert client.post("/api/bookings", json=body(listing, 10, 12)).status_code == 401


def test_landlord_cannot_book_403(client, landlord_headers, listing):
    assert client.post("/api/bookings", json=body(listing, 10, 12), headers=landlord_headers).status_code == 403


def test_my_bookings_without_token_is_401(client):
    assert client.get("/api/bookings/mine").status_code == 401
