"""Подключение к базе данных.

Здесь намеренно используется синхронный SQLAlchemy: он проще читается,
а FastAPI сам выносит такие обработчики в отдельный поток.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from orders.config import settings


class Base(DeclarativeBase):
    """Общий предок для всех таблиц."""


def _engine_options(url: str) -> dict:
    # SQLite по умолчанию запрещает работу из нескольких потоков,
    # а FastAPI как раз использует пул потоков.
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_engine(settings.database_url, **_engine_options(settings.database_url))
SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Отдаёт сессию базы данных на время одного запроса.

    FastAPI подставляет её в обработчики через Depends(get_session).
    В тестах эта зависимость подменяется на сессию к временной базе.
    """
    with SessionFactory() as session:
        yield session
