"""Pytest fixtures. Sets a temp SQLite DB before importing the app."""
from __future__ import annotations

import os
import re
import tempfile

_tmpdir = tempfile.mkdtemp(prefix="exercises-test-")

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["SESSION_SECURE"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["PRODUCTS_CONFIG_PATH"] = "config/products.example.yaml"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import AppSettings, ExerciseLog, User, WorkoutDay  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        for table in (ExerciseLog, WorkoutDay, AppSettings, User):
            conn.execute(table.__table__.delete())


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def admin_user(db):
    user = User(username="test", password_hash=hash_password("password123"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def extract_csrf(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return match.group(1) if match else ""


@pytest.fixture()
def csrf_token(client):
    resp = client.get("/training/login")
    return extract_csrf(resp.text)


@pytest.fixture()
def logged_in_client(client, admin_user, csrf_token):
    resp = client.post(
        "/training/login",
        data={"username": "test", "password": "password123", "csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    return client
