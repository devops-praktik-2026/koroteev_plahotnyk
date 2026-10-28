"""Создание заказов."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from orders.db import get_session
from orders.models import Order
from orders.schemas import OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["Заказы"])


@router.post("", response_model=OrderRead, status_code=201, summary="Создать заказ")
def create_order(
    payload: OrderCreate,
    session: Session = Depends(get_session),
) -> Order:
    """Создать заказ и вернуть его карточку."""

    order = Order(**payload.model_dump())

    session.add(order)
    session.commit()
    session.refresh(order)

    return order
