"""Настройки сервиса заказов."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    service_name: str = "orders"

    # Адрес сервиса клиентов
    accounts_url: str = "http://localhost:8001"

    # Время ожидания ответа сервиса клиентов
    accounts_timeout_seconds: float = 2.0

    # Подключение к базе данных
    database_url: str = "sqlite:///./orders.db"


settings = Settings()
