"""Создание заказов."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
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


@router.get("", response_model=list[OrderRead], summary="Заказы клиента")
def list_orders(
    account_id: int = Query(ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[Order]:
    """Вернуть список заказов указанного клиента."""

    statement = (
        select(Order)
        .where(Order.account_id == account_id)
        .order_by(Order.id)
        .limit(limit)
        .offset(offset)
    )

    return list(session.scalars(statement))
