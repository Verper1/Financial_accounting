.PHONY: help test lint format type-check check up down migrate

help:
	@echo "Команды:"
	@echo "  up           — Запустить docker-compose"
	@echo "  down         — Остановить docker-compose"
	@echo "  migrate      — Применить миграции"
	@echo "  test         — Запустить тесты (pytest)"
	@echo "  lint         — Проверка ruff"
	@echo "  format       — Автоформатирование ruff"
	@echo "  type-check   — Проверка типов mypy"
	@echo "  check        — Все проверки (lint, type-check, test)"

up:
	docker-compose up --build

down:
	docker-compose down

migrate:
	uv run python manage.py migrate

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

type-check:
	uv run mypy .

check: lint type-check test
