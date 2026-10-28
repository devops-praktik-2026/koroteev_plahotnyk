# Короткие команды проекта. Один файл на все системы.
#
#     make            список команд
#     make check      проверить, что на компьютере всё есть
#     make setup      собрать окружение
#     make test       прогнать тесты
#
# Makefile сам определяет систему и подставляет нужные пути: на Windows
# окружение лежит в .venv\Scripts, на Linux и macOS — в .venv/bin.
# Пути записаны для каждой системы отдельно и полностью — так понятнее,
# чем хитрые подстановки, и не ломается на разделителях.
#
# Если на Windows нет команды py, но есть python:
#     make setup PY=python

ifeq ($(OS),Windows_NT)
    # ---------- Windows ----------
    # Закрепляем командный интерпретатор явно: иначе make может подхватить
    # sh.exe из состава Git и запутаться в путях.
    SHELL       := cmd.exe
    .SHELLFLAGS := /c

    PY         ?= py -3
    PYTHON     := .venv\Scripts\python.exe
    PYTEST     := .venv\Scripts\pytest.exe
    RUFF       := .venv\Scripts\ruff.exe

    ACCOUNTS   := services\accounts
    ORDERS     := services\orders
    CHECK_ENV  := scripts\check_env.py
    COMMANDS   := scripts\commands.py

    # Те же программы, но вызванные из подпапки сервиса
    ALEMBIC_UP := ..\..\.venv\Scripts\alembic.exe
    UVICORN_UP := ..\..\.venv\Scripts\uvicorn.exe
else
    # ---------- Linux и macOS ----------
    PY         ?= python3
    PYTHON     := .venv/bin/python
    PYTEST     := .venv/bin/pytest
    RUFF       := .venv/bin/ruff

    ACCOUNTS   := services/accounts
    ORDERS     := services/orders
    CHECK_ENV  := scripts/check_env.py
    COMMANDS   := scripts/commands.py

    ALEMBIC_UP := ../../.venv/bin/alembic
    UVICORN_UP := ../../.venv/bin/uvicorn
endif

.DEFAULT_GOAL := help
.PHONY: help check setup test cov lint fmt run run-orders migrate migrate-orders up down logs ps clean

help: ## Показать список команд
	@$(PY) $(COMMANDS)

check: ## Проверить, что на компьютере есть всё нужное
	$(PY) $(CHECK_ENV)

setup: ## Создать окружение и поставить зависимости обоих сервисов
	$(PY) -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e "./services/accounts[dev]" -e "./services/orders[dev]"
	@$(PY) $(COMMANDS)

test: ## Прогнать все тесты
	$(PYTEST)

cov: ## Прогнать тесты и показать покрытие построчно
	$(PYTEST) --cov-report=term-missing

lint: ## Проверить стиль кода
	$(RUFF) check .
	$(RUFF) format --check .

fmt: ## Привести код к единому виду
	$(RUFF) format .
	$(RUFF) check --fix .

migrate: ## Применить миграции базы данных к сервису клиентов
	cd $(ACCOUNTS) && $(ALEMBIC_UP) upgrade head

run: migrate ## Запустить сервис клиентов: http://localhost:8001/docs
	cd $(ACCOUNTS) && $(UVICORN_UP) accounts.main:app --reload --port 8001

migrate-orders: ## Применить миграции базы данных заказов
	cd $(ORDERS) && $(ALEMBIC_UP) upgrade head

run-orders: migrate-orders ## Запустить сервис заказов: http://localhost:8002/docs
	cd $(ORDERS) && $(UVICORN_UP) orders.main:app --reload --port 8002

up: ## Поднять всю систему в контейнерах
	docker compose up --build -d
	@echo http://localhost:8001/docs
	@echo http://localhost:8002/docs

down: ## Остановить систему и удалить данные
	docker compose down -v

logs: ## Показать журналы всех сервисов
	docker compose logs -f

ps: ## Показать состояние контейнеров
	docker compose ps

ifeq ($(OS),Windows_NT)
clean: ## Удалить окружение и временные файлы
	if exist .venv rmdir /s /q .venv
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist .ruff_cache rmdir /s /q .ruff_cache
	if exist .coverage del /q .coverage
else
clean: ## Удалить окружение и временные файлы
	rm -rf .venv .pytest_cache .ruff_cache .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
endif
