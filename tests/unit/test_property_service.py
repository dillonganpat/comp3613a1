"""Unit tests: PropertyService with the repository mocked."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.services.property_service import PropertyService


@pytest.fixture
def repo():
    repo = MagicMock()
    repo.create.side_effect = lambda data: data
    return repo


@pytest.fixture
def service(repo):
    return PropertyService(repo)


def test_create_property_builds_correct_record(service, repo):
    prop = service.create_property(
        owner_id=2, title="Loft", location="Curepe", description="Nice",
        price_per_night=Decimal("500"), bedrooms="2", bathrooms="1",
    )
    assert prop.owner_id == 2
    assert prop.title == "Loft"
    assert prop.bedrooms == 2          # numeric strings from form posts become ints
    assert prop.available is True
    repo.create.assert_called_once()


def test_empty_image_url_is_stored_as_none(service):
    prop = service.create_property(2, "Loft", "Curepe", "Nice", Decimal("500"), 1, 1, image_url="")
    assert prop.image_url is None


def test_create_property_rejects_negative_price(service):
    with pytest.raises(ValidationError):
        service.create_property(2, "Loft", "Curepe", "Nice", Decimal("-1"), 1, 1)


def test_list_properties_passes_filters_to_repository(service, repo):
    service.list_properties(location="Curepe", min_price=Decimal("100"), max_price=Decimal("600"))
    repo.list_all.assert_called_once_with(location="Curepe", min_price=Decimal("100"), max_price=Decimal("600"))


def test_delete_property_by_owner_calls_repository(service, repo):
    repo.get_by_id.return_value = SimpleNamespace(owner_id=2)
    repo.delete.return_value = True
    assert service.delete_property(10, user_id=2) is True
    repo.delete.assert_called_once_with(10)


def test_delete_property_by_non_owner_is_refused(service, repo):
    repo.get_by_id.return_value = SimpleNamespace(owner_id=2)
    assert service.delete_property(10, user_id=99) is False
    repo.delete.assert_not_called()


def test_delete_missing_property_returns_false(service, repo):
    repo.get_by_id.return_value = None
    assert service.delete_property(10, user_id=2) is False
    repo.delete.assert_not_called()
