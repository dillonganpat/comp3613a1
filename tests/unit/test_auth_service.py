"""Unit tests: AuthService with UserRepository mocked."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest

from app.config import get_settings
from app.services.auth_service import AuthService
from app.utilities.security import encrypt_password


@pytest.fixture
def repo():
    return MagicMock()


@pytest.fixture
def service(repo):
    return AuthService(repo)


def stored_user(role="regular_user"):
    return SimpleNamespace(id=4, role=role, password_hash=encrypt_password("bobpass"))


def test_authenticate_with_valid_credentials_returns_token(service, repo):
    repo.get_by_username.return_value = stored_user("regular_user")
    token = service.authenticate_user("bob", "bobpass")
    payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
    assert payload["sub"] == "4"
    assert payload["role"] == "regular_user"


def test_authenticate_with_wrong_password_returns_none(service, repo):
    repo.get_by_username.return_value = stored_user()
    assert service.authenticate_user("bob", "nope") is None


def test_authenticate_unknown_user_returns_none(service, repo):
    repo.get_by_username.return_value = None
    assert service.authenticate_user("ghost", "x") is None


def test_register_user_stores_hash_not_plaintext_and_tenant_role(service, repo):
    repo.create.side_effect = lambda data: data
    new_user = service.register_user("carol", "carol@example.com", "secret123")
    assert new_user.password_hash != "secret123"
    assert new_user.role == "regular_user"
    assert new_user.username == "carol"
