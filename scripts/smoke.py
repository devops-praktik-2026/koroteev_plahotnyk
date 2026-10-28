"""Проверка запущенной системы: python scripts/smoke.py [--unavailable]."""

import argparse
import json
import os
import time
import urllib.error
import urllib.request
import uuid


def request(base, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        base + path, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def check(accounts, orders, unavailable=False):
    payload = {"account_id": 1, "item": "Проверочный заказ", "quantity": 2}
    if unavailable:
        start = time.monotonic()
        status, _ = request(orders, "/orders", payload)
        elapsed = time.monotonic() - start
        assert status == 503, status
        assert elapsed < 3, elapsed
        print(f"Отключённый сервис клиентов: 503 за {elapsed:.3f} с")
        return

    email = f"smoke-{uuid.uuid4().hex}@example.com"
    status, account = request(accounts, "/accounts", {"name": "Проверка", "email": email})
    assert status == 201, (status, account)
    payload["account_id"] = account["id"]
    status, order = request(orders, "/orders", payload)
    assert status == 201, (status, order)
    assert order["account_id"] == account["id"]
    assert request(orders, f"/orders/{order['id']}") == (200, order)
    status, listing = request(orders, f"/orders?account_id={account['id']}&limit=1")
    assert status == 200 and listing == [order], (status, listing)
    print(f"Созданы клиент {account['id']} и заказ {order['id']}; чтение и фильтрация работают")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unavailable", action="store_true")
    args = parser.parse_args()
    check(
        os.environ.get("SMOKE_ACCOUNTS_URL", "http://localhost:8001"),
        os.environ.get("SMOKE_ORDERS_URL", "http://localhost:8002"),
        args.unavailable,
    )
