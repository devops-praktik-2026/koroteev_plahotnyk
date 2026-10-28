"""Таблица заказов. Клиенты принадлежат другому сервису."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from orders.db import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("quantity >= 1", name="positive_quantity"),
        CheckConstraint("account_id >= 1", name="positive_account_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(index=True, nullable=False)
    item: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
