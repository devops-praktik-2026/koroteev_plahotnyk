"""Общая подготовка для тестов сервиса заказов.

Каждый тест получает свою пустую базу данных в оперативной памяти.
Так тесты не зависят друг от друга и не требуют запущенного PostgreSQL.
"""

from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from orders.db import Base, get_session
from orders.main import app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_session() -> Iterator[Session]:
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def available_accounts(monkeypatch):
    async def get(self, url, **kwargs):
        return httpx.Response(200, json={"id": int(url.rsplit("/", 1)[-1])})

    monkeypatch.setattr(httpx.AsyncClient, "get", get)
