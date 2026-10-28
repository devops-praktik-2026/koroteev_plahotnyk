"""Проверка клиента по HTTP до сохранения заказа."""

import asyncio

import httpx
from fastapi import HTTPException

from orders.config import settings


async def ensure_account_exists(account_id: int) -> None:
    url = f"{settings.accounts_url.rstrip('/')}/accounts/{account_id}"
    try:
        async with asyncio.timeout(settings.accounts_timeout_seconds):
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=settings.accounts_timeout_seconds)
    except (httpx.RequestError, TimeoutError) as error:
        raise HTTPException(status_code=503, detail="Сервис клиентов не отвечает") from error
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Клиент {account_id} не найден")
    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="Ошибка сервиса клиентов")
    try:
        body = response.json()
    except ValueError as error:
        raise HTTPException(
            status_code=503, detail="Некорректный ответ сервиса клиентов"
        ) from error
    if not isinstance(body, dict) or type(body.get("id")) is not int or body["id"] != account_id:
        raise HTTPException(status_code=503, detail="Некорректная карточка клиента")
