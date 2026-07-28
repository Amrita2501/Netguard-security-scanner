"""
Shared pytest fixtures.

Critically, this sets NETGUARD_DATA_DIR to a fresh temp directory *before*
any `app.*` module is imported, so the test suite runs against an isolated
SQLite database and never touches real dev/demo data in backend/data/.
"""
import os
import tempfile

_TEST_DATA_DIR = tempfile.mkdtemp(prefix="netguard-test-")
os.environ["NETGUARD_DATA_DIR"] = _TEST_DATA_DIR
os.environ["NETGUARD_SESSION_SECRET"] = "test-secret-not-for-production"

import pytest  # noqa: E402  (must come after the env vars above are set)
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app import database as db  # noqa: E402
from app.seed_data import seed_if_empty  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _initialize_test_database():
    """Runs once for the whole test session: create schema + seed demo data."""
    db.init_db()
    seed_if_empty()
    yield


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_token(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture()
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
