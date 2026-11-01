"""Unit tests: request-schema validation rules (pure pydantic, no database)."""
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.api import ApiSignup, BookingCreate, PropertyCreate

VALID_PROPERTY = dict(title="Loft", location="Curepe", description="Nice", price_per_night="450.00")


def test_property_create_accepts_valid_data():
    prop = PropertyCreate(**VALID_PROPERTY)
    assert prop.bedrooms == 1 and prop.bathrooms == 1


@pytest.mark.parametrize("price", ["0", "-5", "abc"])
def test_property_create_rejects_bad_price(price):
    with pytest.raises(ValidationError):
        PropertyCreate(**{**VALID_PROPERTY, "price_per_night": price})


@pytest.mark.parametrize("field", ["title", "location", "description"])
def test_property_create_rejects_empty_text_fields(field):
    with pytest.raises(ValidationError):
        PropertyCreate(**{**VALID_PROPERTY, field: ""})


def test_property_create_rejects_zero_bedrooms():
    with pytest.raises(ValidationError):
        PropertyCreate(**{**VALID_PROPERTY, "bedrooms": 0})


def test_booking_create_parses_iso_dates():
    booking = BookingCreate(property_id=1, check_in="2030-01-10", check_out="2030-01-12")
    assert booking.check_in == date(2030, 1, 10)


def test_booking_create_rejects_invalid_date():
    with pytest.raises(ValidationError):
        BookingCreate(property_id=1, check_in="not-a-date", check_out="2030-01-12")


def test_signup_rejects_invalid_email():
    with pytest.raises(ValidationError):
        ApiSignup(username="carol", email="not-an-email", password="secret123")


def test_signup_rejects_short_password():
    with pytest.raises(ValidationError):
        ApiSignup(username="carol", email="c@example.com", password="123")
