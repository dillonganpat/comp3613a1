"""Unit tests: app/utilities/security.py (no database, no network)."""
from datetime import timedelta

import jwt
import pytest

from app.config import get_settings
from app.utilities.security import create_access_token, encrypt_password, verify_password


def test_hashed_password_is_not_plaintext():
    hashed = encrypt_password("mypass")
    assert hashed != "mypass"
    assert "mypass" not in hashed


def test_same_password_hashes_differently_each_time():
    assert encrypt_password("mypass") != encrypt_password("mypass")  # salted


def test_verify_password_accepts_correct_password():
    assert verify_password("mypass", encrypt_password("mypass")) is True


def test_verify_password_rejects_wrong_password():
    assert verify_password("wrong", encrypt_password("mypass")) is False


def test_access_token_contains_subject_role_and_expiry():
    token = create_access_token({"sub": "7", "role": "admin"})
    payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().jwt_algorithm])
    assert payload["sub"] == "7"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_expired_token_is_rejected():
    token = create_access_token({"sub": "7"}, expires_delta=timedelta(seconds=-5))
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().jwt_algorithm])


def test_token_signed_with_other_key_is_rejected():
    forged = jwt.encode({"sub": "1"}, "a-different-secret-key-0123456789-abcdefghijkl", algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(forged, get_settings().secret_key, algorithms=["HS256"])
