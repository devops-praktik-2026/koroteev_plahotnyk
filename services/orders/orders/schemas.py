"""Входные данные и карточка заказа."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    account_id: int = Field(ge=1)
    item: str = Field(min_length=1, max_length=200)
    quantity: int = Field(ge=1)


class OrderRead(OrderCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
