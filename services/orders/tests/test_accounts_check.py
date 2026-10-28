"""Проверка клиента должна происходить до записи заказа."""

import time

import httpx
import pytest

from orders.config import settings

PAYLOAD = {"account_id": 7, "item": "Книга", "quantity": 1}


def test_requests_configured_account_url(client, monkeypatch):
    calls = []
    monkeypatch.setattr(settings, "accounts_url", "http://example.test/custom/")
    monkeypatch.setattr(settings, "accounts_timeout_seconds", 0.4)

    async def get(self, url, *, timeout):
        calls.append((url, timeout))
        return httpx.Response(200, json={"id": 7}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    assert client.post("/orders", json=PAYLOAD).status_code == 201
    assert calls == [("http://example.test/custom/accounts/7", 0.4)]


@pytest.mark.parametrize("upstream,expected", [(404, 404), (500, 503), (401, 503), (302, 503)])
def test_account_error_does_not_save_order(client, monkeypatch, upstream, expected):
    async def get(self, url, **kw):
        return httpx.Response(upstream)

    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    assert client.post("/orders", json=PAYLOAD).status_code == expected
    assert client.get("/orders?account_id=7").json() == []


@pytest.mark.parametrize("error", [httpx.ConnectError, httpx.ReadTimeout])
def test_network_failure_is_fast_503(client, monkeypatch, error):
    async def unavailable(*args, **kwargs):
        raise error("unavailable")

    monkeypatch.setattr(httpx.AsyncClient, "get", unavailable)
    start = time.monotonic()
    response = client.post("/orders", json=PAYLOAD)
    assert response.status_code == 503
    assert time.monotonic() - start < 3
    assert client.get("/orders?account_id=7").json() == []


@pytest.mark.parametrize("body", [b"not json", b"[]", b'{"id":8}', b'{"id":true}'])
def test_invalid_account_card_is_503(client, monkeypatch, body):
    async def get(*a, **kw):
        return httpx.Response(200, content=body)

    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    assert client.post("/orders", json=PAYLOAD).status_code == 503
    assert client.get("/orders?account_id=7").json() == []


def test_total_deadline_cancels_stalled_lookup(client, monkeypatch):
    import asyncio

    monkeypatch.setattr(settings, "accounts_timeout_seconds", 0.1)

    async def stalled(*args, **kwargs):
        await asyncio.sleep(5)
        return httpx.Response(200, json={"id": 7})

    monkeypatch.setattr(httpx.AsyncClient, "get", stalled)
    start = time.monotonic()
    assert client.post("/orders", json=PAYLOAD).status_code == 503
    assert time.monotonic() - start < 1
    assert client.get("/orders?account_id=7").json() == []
