# Зависимости кешируются независимо от исходного кода приложения.
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml ./
RUN python -c "import tomllib; from pathlib import Path; Path('requirements.txt').write_text('\n'.join(tomllib.loads(Path('pyproject.toml').read_text())['project']['dependencies']))" \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 1000 app
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=app:app orders ./orders
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations ./migrations
# При локальном запуске образа SQLite должна быть доступна для записи.
RUN chown app:app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["sh", "-c", "alembic upgrade head && uvicorn orders.main:app --host 0.0.0.0 --port 8000"]
