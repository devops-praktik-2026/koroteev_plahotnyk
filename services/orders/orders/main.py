"""Точка входа сервиса заказов.

Запуск вручную:
    uvicorn orders.main:app --reload --port 8002
"""

from fastapi import FastAPI
from pydantic import BaseModel

from orders.api import router
from orders.config import settings

app = FastAPI(
    title="Сервис заказов",
    description="Создание и просмотр заказов клиентов.",
    version="0.1.0",
)


class HealthRead(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthRead, tags=["Служебное"], summary="Жив ли сервис")
def health() -> HealthRead:
    return HealthRead(status="ok", service=settings.service_name)


app.include_router(router)
