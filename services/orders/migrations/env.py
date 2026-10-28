"""Подготовка окружения для миграций.

Миграция — это записанное изменение структуры базы данных. Каждое такое
изменение лежит отдельным файлом в migrations/versions и применяется
командой `alembic upgrade head`.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from orders import models  # noqa: F401  нужен, чтобы таблицы попали в Base.metadata
from orders.config import settings
from orders.db import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        version_table="alembic_version_orders",
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="alembic_version_orders",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
