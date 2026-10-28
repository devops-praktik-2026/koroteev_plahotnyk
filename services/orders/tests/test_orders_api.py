"""Контракт заказов: создание, чтение и выдача только заказов клиента."""

import pytest


@pytest.fixture()
def payload():
    return {"account_id": 1, "item": "Кофемолка", "quantity": 2}


def test_create_order_returns_201(client, payload):
    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert {key: body[key] for key in payload} == payload
    assert body["created_at"]
    assert client.get(f"/orders/{body['id']}").json() == body


@pytest.mark.parametrize(
    "changes",
    [{"quantity": 0}, {"quantity": -1}, {"account_id": 0}, {"item": ""}, {"item": "x" * 201}],
)
def test_invalid_payload_returns_422(client, payload, changes):
    response = client.post("/orders", json=payload | changes)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == next(iter(changes))


@pytest.mark.parametrize("field", ["account_id", "item", "quantity"])
def test_required_fields(client, payload, field):
    del payload[field]
    assert client.post("/orders", json=payload).status_code == 422


def test_missing_order_has_number(client):
    response = client.get("/orders/999")
    assert response.status_code == 404
    assert "999" in response.json()["detail"]


def test_filter_and_limit(client, payload):
    for account_id in [1, 2, 1]:
        assert client.post("/orders", json=payload | {"account_id": account_id}).status_code == 201
    response = client.get("/orders", params={"account_id": 1})
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 2
    assert all(order["account_id"] == 1 for order in orders)
    assert client.get("/orders?account_id=1&limit=1").json() == orders[:1]
    assert client.get("/orders?account_id=1&offset=1").json() == orders[1:]
    assert client.get("/orders?account_id=3").json() == []


@pytest.mark.parametrize(
    "query",
    [
        "",
        "account_id=0",
        "account_id=1&limit=0",
        "account_id=1&limit=201",
        "account_id=1&offset=-1",
    ],
)
def test_invalid_list_query(client, query):
    assert client.get(f"/orders?{query}").status_code == 422
