"""Тесты создания заказа."""

import pytest


@pytest.fixture()
def payload():
    return {
        "account_id": 1,
        "item": "Кофемолка",
        "quantity": 2,
    }


def test_create_order_returns_201(client, payload):
    response = client.post("/orders", json=payload)

    assert response.status_code == 201

    body = response.json()

    assert body["id"] > 0

    assert body["account_id"] == payload["account_id"]
    assert body["item"] == payload["item"]
    assert body["quantity"] == payload["quantity"]

    assert body["created_at"]


@pytest.mark.parametrize(
    "changes",
    [
        {"quantity": 0},
        {"quantity": -1},
        {"account_id": 0},
        {"item": ""},
        {"item": "x" * 201},
    ],
)
def test_invalid_payload_returns_422(client, payload, changes):
    response = client.post("/orders", json=payload | changes)

    assert response.status_code == 422

    assert response.json()["detail"][0]["loc"][-1] == next(iter(changes))


@pytest.mark.parametrize(
    "field",
    ["account_id", "item", "quantity"],
)
def test_required_fields(client, payload, field):
    del payload[field]

    response = client.post("/orders", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == field


def test_filter_and_limit(client, payload):
    """Список содержит только заказы выбранного клиента."""

    for account_id in [1, 2, 1]:
        response = client.post(
            "/orders",
            json=payload | {"account_id": account_id},
        )
        assert response.status_code == 201

    response = client.get("/orders", params={"account_id": 1})

    assert response.status_code == 200

    orders = response.json()

    assert len(orders) == 2
    assert all(order["account_id"] == 1 for order in orders)

    # Ограничение количества заказов
    limited_response = client.get(
        "/orders",
        params={"account_id": 1, "limit": 1},
    )

    assert limited_response.status_code == 200
    assert limited_response.json() == orders[:1]

    # Пропуск первого заказа
    offset_response = client.get(
        "/orders",
        params={"account_id": 1, "offset": 1},
    )

    assert offset_response.status_code == 200
    assert offset_response.json() == orders[1:]


def test_empty_order_list(client):
    """Для клиента без заказов возвращается пустой список."""

    response = client.get("/orders", params={"account_id": 999})

    assert response.status_code == 200
    assert response.json() == []


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
    """Некорректные параметры запроса возвращают HTTP 422."""

    response = client.get(f"/orders?{query}")

    assert response.status_code == 422
