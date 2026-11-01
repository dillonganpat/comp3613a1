"""Unit tests: authentication dependencies (stub request, mocked user lookup)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.dependencies.auth import get_current_user, is_admin, require_admin_api
from app.utilities.security import create_access_token

pytestmark = pytest.mark.asyncio


def fake_request(cookie=None, auth_header=None):
    headers = {"Authorization": auth_header} if auth_header else {}
    cookies = {"access_token": cookie} if cookie else {}
    return SimpleNamespace(cookies=cookies, headers=headers)


@pytest.fixture
def repo_returning_user():
    user = SimpleNamespace(id=3, role="regular_user")
    with patch("app.dependencies.auth.UserRepository") as repo_cls:
        repo_cls.return_value.get_by_id.return_value = user
        yield user


async def test_missing_token_is_401():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(fake_request(), MagicMock())
    assert exc.value.status_code == 401


async def test_garbage_token_is_401():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(fake_request(cookie="not.a.jwt"), MagicMock())
    assert exc.value.status_code == 401


async def test_valid_cookie_token_returns_user(repo_returning_user):
    token = create_access_token({"sub": "3"})
    assert await get_current_user(fake_request(cookie=token), MagicMock()) is repo_returning_user


async def test_valid_bearer_header_returns_user(repo_returning_user):
    token = create_access_token({"sub": "3"})
    request = fake_request(auth_header=f"Bearer {token}")
    assert await get_current_user(request, MagicMock()) is repo_returning_user


async def test_token_for_deleted_user_is_401():
    with patch("app.dependencies.auth.UserRepository") as repo_cls:
        repo_cls.return_value.get_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await get_current_user(fake_request(cookie=create_access_token({"sub": "99"})), MagicMock())
    assert exc.value.status_code == 401


async def test_is_admin_true_only_for_admin_role():
    assert await is_admin(SimpleNamespace(role="admin")) is True
    assert await is_admin(SimpleNamespace(role="regular_user")) is False


async def test_require_admin_api_returns_403_for_tenant():
    with pytest.raises(HTTPException) as exc:
        await require_admin_api(SimpleNamespace(role="regular_user"))
    assert exc.value.status_code == 403
