"""Shared pytest setup.

* Tests NEVER touch your real database: DATABASE_URI is forced to a throw-away
  value and every API/web test runs against an in-memory SQLite database.
* Run from anywhere: the project root is added to sys.path and used as cwd
  (the app loads templates/static with relative paths).
"""
import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# Must be set before `app` is imported anywhere.
os.environ["DATABASE_URI"] = "sqlite:///./.pytest_unused.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789-abcdefghij"
os.environ["ENV"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import event  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402,F401  (registers tables on SQLModel.metadata)
from app.database import get_session  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.models.property import Property  # noqa: E402
from app.models.user import User  # noqa: E402
from app.utilities.security import encrypt_password  # noqa: E402

PASSWORDS = {"bob": "bobpass", "alice": "alicepass", "admin": "adminpass"}


# ---------------------------------------------------------------- helpers
def future(days: int) -> date:
    """A date `days` from today (tests must never hard-code calendar dates)."""
    return date.today() + timedelta(days=days)


# ------------------------------------------------------------- database
@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Production uses PostgreSQL, which enforces foreign keys. SQLite does not
    # unless asked, so switch it on to make the tests behave like production.
    @event.listens_for(eng, "connect")
    def _enforce_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as db:
        yield db


def _make_user(db: Session, username: str, role: str) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=encrypt_password(PASSWORDS[username]),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def tenant(session):
    return _make_user(session, "bob", "regular_user")


@pytest.fixture
def landlord(session):
    return _make_user(session, "alice", "admin")


@pytest.fixture
def landlord2(session):
    return _make_user(session, "admin", "admin")


@pytest.fixture
def listing(session, landlord):
    prop = Property(
        title="Watts Street Studio",
        location="12 Watts Street, St. Augustine",
        description="Bright studio near UWI.",
        price_per_night=450,
        bedrooms=1,
        bathrooms=1,
        available=True,
        owner_id=landlord.id,
    )
    session.add(prop)
    session.commit()
    session.refresh(prop)
    return prop


# ------------------------------------------------------------ HTTP client
@pytest.fixture
def client(engine):
    def override_session():
        with Session(engine) as db:
            yield db

    fastapi_app.dependency_overrides[get_session] = override_session
    # No `with` block: lifespan (which would touch the real DB) is not started.
    yield TestClient(fastapi_app, follow_redirects=False)
    fastapi_app.dependency_overrides.clear()


def login_token(client: TestClient, username: str) -> str:
    resp = client.post("/api/auth", json={"username": username, "password": PASSWORDS[username]})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tenant_headers(client, tenant):
    return bearer(login_token(client, "bob"))


@pytest.fixture
def landlord_headers(client, landlord):
    return bearer(login_token(client, "alice"))


@pytest.fixture
def landlord2_headers(client, landlord2):
    return bearer(login_token(client, "admin"))
