"""Создание и чтение заказов."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from orders.accounts_client import ensure_account_exists
from orders.db import get_session
from orders.models import Order
from orders.schemas import OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["Заказы"])


@router.post("", response_model=OrderRead, status_code=201, summary="Создать заказ")
def create_order(payload: OrderCreate, session: Session = Depends(get_session)) -> Order:
    ensure_account_exists(payload.account_id)
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
    statement = (
        select(Order)
        .where(Order.account_id == account_id)
        .order_by(Order.id)
        .limit(limit)
        .offset(offset)
    )
    return list(session.scalars(statement))


@router.get("/{order_id}", response_model=OrderRead, summary="Получить заказ")
def get_order(order_id: int, session: Session = Depends(get_session)) -> Order:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Заказ {order_id} не найден")
    return order
