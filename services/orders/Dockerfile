# Зависимости собираются отдельно и кешируются до изменения pyproject.toml.
FROM python:3.12-slim AS dependencies
WORKDIR /build
COPY pyproject.toml .
RUN python -m venv /opt/venv \
    && python -c 'import tomllib; print("\n".join(tomllib.load(open("pyproject.toml", "rb"))["project"]["dependencies"]))' > requirements.txt \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app \
    && mkdir /app && chown app:app /app
WORKDIR /app
COPY --from=dependencies /opt/venv /opt/venv
COPY --chown=app:app orders ./orders
USER app
EXPOSE 8000
CMD ["uvicorn", "orders.main:app", "--host", "0.0.0.0", "--port", "8000"]
