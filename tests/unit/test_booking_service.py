"""Unit tests: BookingService business rules with the repository mocked.

The repository is a stub (see Testing slides: Stubs & Drivers), so no database
is touched. Overlap detection against real rows is covered by integration tests.
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.booking_service import BookingConflictError, BookingService


@pytest.fixture
def repo():
    repo = MagicMock()
    repo.has_overlap.return_value = False
    repo.create.side_effect = lambda data: data
    return repo


@pytest.fixture
def service(repo):
    return BookingService(repo)


def d(days):
    return date.today() + timedelta(days=days)


def test_valid_booking_is_created_as_pending(service, repo):
    booking = service.create_booking(1, 5, d(10), d(12), Decimal("900.00"))
    assert booking.property_id == 1
    assert booking.tenant_id == 5
    assert booking.status == "pending"
    assert booking.total_price == Decimal("900.00")
    repo.create.assert_called_once()


def test_check_in_today_is_allowed(service):
    assert service.create_booking(1, 5, d(0), d(1), Decimal("450")) is not None


def test_check_in_in_the_past_is_rejected(service, repo):
    with pytest.raises(ValueError, match="cannot be in the past"):
        service.create_booking(1, 5, d(-1), d(2), Decimal("0"))
    repo.create.assert_not_called()


def test_check_out_same_day_as_check_in_is_rejected(service, repo):
    with pytest.raises(ValueError, match="after check-in"):
        service.create_booking(1, 5, d(5), d(5), Decimal("0"))
    repo.create.assert_not_called()


def test_check_out_before_check_in_is_rejected(service, repo):
    with pytest.raises(ValueError, match="after check-in"):
        service.create_booking(1, 5, d(8), d(5), Decimal("0"))
    repo.create.assert_not_called()


def test_overlapping_dates_raise_conflict_error(service, repo):
    repo.has_overlap.return_value = True
    with pytest.raises(BookingConflictError, match="already booked"):
        service.create_booking(1, 5, d(10), d(12), Decimal("900"))
    repo.create.assert_not_called()


def test_conflict_error_is_a_value_error():
    assert issubclass(BookingConflictError, ValueError)  # HTML route still catches it


def test_overlap_check_receives_the_requested_range(service, repo):
    service.create_booking(3, 5, d(10), d(12), Decimal("900"))
    repo.has_overlap.assert_called_once_with(3, d(10), d(12))


def test_list_my_bookings_delegates_to_repository(service, repo):
    repo.list_by_tenant.return_value = ["a", "b"]
    assert service.list_my_bookings(5) == ["a", "b"]
    repo.list_by_tenant.assert_called_once_with(5)
