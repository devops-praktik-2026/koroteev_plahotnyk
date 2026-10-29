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

def test_get_existing_order(client, payload):
    created = client.post("/orders", json=payload)
    assert created.status_code == 201
    order = created.json()

    response = client.get(f"/orders/{order['id']}")

    assert response.status_code == 200
    assert response.json() == order


def test_get_missing_order(client):
    response = client.get("/orders/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Заказ 999 не найден"}
