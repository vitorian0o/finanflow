import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-finanflow-32chars-min")
os.environ.setdefault("CORS_ORIGINS", "http://testserver")
os.environ.setdefault("ENVIRONMENT", "test")

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.main import app
from app.models import entities  # noqa: F401

get_settings.cache_clear()
Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_client(client: TestClient) -> tuple[TestClient, dict]:
    payload = {
        "name": "Ana Costa",
        "email": "ana@aurora.example.com",
        "password": "senha1234",
        "company_name": "Aurora Teste",
    }
    register = client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 201, register.text
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return client, headers
