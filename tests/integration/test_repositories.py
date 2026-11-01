"""Integration tests: repositories + services against a real (in-memory) database."""
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.booking import BookingBase
from app.models.property import Property, PropertyBase
from app.repositories.booking import BookingRepository
from app.repositories.property import PropertyRepository
from app.repositories.user import UserRepository
from app.schemas.user import RegularUserCreate, UserUpdate
from app.services.booking_service import BookingConflictError, BookingService
from tests.conftest import future


def make_booking(repo, prop_id, tenant_id, a, b):
    return repo.create(BookingBase(property_id=prop_id, tenant_id=tenant_id, check_in=future(a), check_out=future(b)))


# ------------------------------------------------------------------ users
def test_create_user_persists_correct_values(session):
    repo = UserRepository(session)
    created = repo.create(RegularUserCreate(username="carol", email="carol@example.com", password_hash="x"))
    fetched = repo.get_by_username("carol")
    assert fetched.id == created.id
    assert fetched.email == "carol@example.com"
    assert fetched.role == "regular_user"


def test_duplicate_username_is_rejected_by_database(session, tenant):
    repo = UserRepository(session)
    with pytest.raises(IntegrityError):
        repo.create(RegularUserCreate(username="bob", email="other@example.com", password_hash="x"))


def test_duplicate_email_is_rejected_by_database(session, tenant):
    repo = UserRepository(session)
    with pytest.raises(IntegrityError):
        repo.create(RegularUserCreate(username="bob2", email="bob@example.com", password_hash="x"))


def test_update_user_returns_updated_values(session, tenant):
    repo = UserRepository(session)
    repo.update_user(tenant.id, UserUpdate(username="bobby", email="bobby@example.com"))
    assert repo.get_by_id(tenant.id).username == "bobby"


def test_get_all_users_returns_every_user(session, tenant, landlord):
    assert {u.username for u in UserRepository(session).get_all_users()} == {"bob", "alice"}


# ------------------------------------------------------------- properties
def add_property(session, owner_id, title, location, price, available=True):
    return PropertyRepository(session).create(PropertyBase(
        title=title, location=location, description="d", price_per_night=Decimal(price),
        bedrooms=1, bathrooms=1, available=available, owner_id=owner_id))


def test_created_property_persists_with_owner(session, landlord):
    prop = add_property(session, landlord.id, "Loft", "Curepe", "500")
    assert PropertyRepository(session).get_by_id(prop.id).owner_id == landlord.id


def test_list_all_filters_by_location_case_insensitive(session, landlord):
    add_property(session, landlord.id, "A", "St. Augustine", "400")
    add_property(session, landlord.id, "B", "Curepe", "500")
    result = PropertyRepository(session).list_all(location="augustine")
    assert [p.title for p in result] == ["A"]


def test_list_all_filters_by_price_range_inclusive(session, landlord):
    for title, price in [("cheap", "300"), ("mid", "500"), ("pricey", "900")]:
        add_property(session, landlord.id, title, "X", price)
    result = PropertyRepository(session).list_all(min_price=Decimal("300"), max_price=Decimal("500"))
    assert [p.title for p in result] == ["cheap", "mid"]


def test_list_all_is_sorted_by_price_ascending(session, landlord):
    add_property(session, landlord.id, "b", "X", "700")
    add_property(session, landlord.id, "a", "X", "200")
    assert [p.title for p in PropertyRepository(session).list_all()] == ["a", "b"]


def test_list_all_hides_unavailable_properties(session, landlord):
    add_property(session, landlord.id, "hidden", "X", "100", available=False)
    assert PropertyRepository(session).list_all() == []


def test_list_by_owner_only_returns_that_owners_properties(session, landlord, landlord2):
    add_property(session, landlord.id, "mine", "X", "100")
    add_property(session, landlord2.id, "theirs", "X", "100")
    assert [p.title for p in PropertyRepository(session).list_by_owner(landlord.id)] == ["mine"]


def test_delete_removes_property(session, listing):
    repo = PropertyRepository(session)
    assert repo.delete(listing.id) is True
    assert repo.get_by_id(listing.id) is None


def test_delete_missing_property_returns_false(session):
    assert PropertyRepository(session).delete(9999) is False


# --------------------------------------------------------------- bookings
@pytest.mark.parametrize("a,b,expected", [
    (10, 15, True),    # identical range
    (8, 12, True),     # overlaps the start
    (13, 18, True),    # overlaps the end
    (11, 14, True),    # fully inside
    (5, 20, True),     # fully contains
    (15, 18, False),   # back-to-back after (check-in == existing check-out)
    (5, 10, False),    # back-to-back before (check-out == existing check-in)
    (20, 25, False),   # clearly after
])
def test_has_overlap_cases(session, listing, tenant, a, b, expected):
    repo = BookingRepository(session)
    make_booking(repo, listing.id, tenant.id, 10, 15)
    assert repo.has_overlap(listing.id, future(a), future(b)) is expected


def test_overlap_is_per_property(session, listing, landlord, tenant):
    other = add_property(session, landlord.id, "Other", "X", "100")
    repo = BookingRepository(session)
    make_booking(repo, listing.id, tenant.id, 10, 15)
    assert repo.has_overlap(other.id, future(10), future(15)) is False


def test_list_by_tenant_returns_only_own_bookings_newest_first(session, listing, tenant, landlord):
    repo = BookingRepository(session)
    make_booking(repo, listing.id, tenant.id, 10, 12)
    make_booking(repo, listing.id, tenant.id, 20, 22)
    make_booking(repo, listing.id, landlord.id, 30, 32)
    mine = repo.list_by_tenant(tenant.id)
    assert [b.check_in for b in mine] == [future(20), future(10)]


def test_service_creates_booking_in_database(session, listing, tenant):
    service = BookingService(BookingRepository(session))
    booking = service.create_booking(listing.id, tenant.id, future(5), future(7), Decimal("900"))
    saved = BookingRepository(session).get_by_id(booking.id)
    assert (saved.property_id, saved.tenant_id, saved.status) == (listing.id, tenant.id, "pending")


def test_service_blocks_double_booking_using_real_rows(session, listing, tenant):
    service = BookingService(BookingRepository(session))
    service.create_booking(listing.id, tenant.id, future(5), future(8), Decimal("1350"))
    with pytest.raises(BookingConflictError):
        service.create_booking(listing.id, tenant.id, future(6), future(9), Decimal("1350"))


def test_service_allows_back_to_back_stays(session, listing, tenant):
    service = BookingService(BookingRepository(session))
    service.create_booking(listing.id, tenant.id, future(5), future(8), Decimal("1350"))
    assert service.create_booking(listing.id, tenant.id, future(8), future(10), Decimal("900")).id is not None


def test_has_bookings_true_only_when_property_is_booked(session, listing, tenant, landlord):
    repo = BookingRepository(session)
    other = add_property(session, landlord.id, "Other", "X", "100")
    make_booking(repo, listing.id, tenant.id, 10, 12)
    assert repo.has_bookings(listing.id) is True
    assert repo.has_bookings(other.id) is False
