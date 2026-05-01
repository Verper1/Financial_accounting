# Финансовый учёт

Однопользовательское веб-приложение для учёта доходов и расходов.

## Стек

- Python 3.13, Django 4.2.3
- PostgreSQL 15, Redis 7, Celery + Celery Beat
- Docker + docker-compose
- pytest, pytest-django, pytest-cov
- ruff, mypy

## Запуск через Docker

1. Скопируйте `.env.example` в `.env` и при необходимости измените значения:
   ```bash
   cp .env.example .env
   ```

2. Запустите проект:
   ```bash
   docker-compose up --build
   ```

3. В отдельном терминале примените миграции и загрузите категории:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py loaddata categories.json
   ```

4. Создайте суперпользователя:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. Откройте http://localhost:8000/

## Локальный запуск (без Docker)

1. Установите зависимости:
   ```bash
   uv sync
   ```

2. Примените миграции:
   ```bash
   uv run python manage.py migrate --settings=finance_settings.test_settings
   ```

3. Загрузите фикстуры категорий:
   ```bash
   uv run python manage.py loaddata categories.json --settings=finance_settings.test_settings
   ```

4. Создайте суперпользователя:
   ```bash
   uv run python manage.py createsuperuser --settings=finance_settings.test_settings
   ```

5. Запустите сервер:
   ```bash
   uv run python manage.py runserver --settings=finance_settings.test_settings
   ```

## Тесты

```bash
uv run pytest
```

Покрытие: 97%+ (минимум 80% по требованиям).

## Команды Make

| Команда | Описание |
|---------|----------|
| `make up` | Запустить docker-compose |
| `make down` | Остановить docker-compose |
| `make test` | Запустить тесты |
| `make lint` | Проверка ruff |
| `make format` | Автоформатирование |
| `make type-check` | Проверка mypy |
| `make check` | Все проверки |

## Структура

```
finance/                  — основное приложение
├── models.py             — модели Category и Transaction
├── forms.py              — форма TransactionForm с валидацией
├── filters.py            — фильтр TransactionFilter (django-filter)
├── views.py              — views: дашборд, список, CRUD
├── urls.py               — URL-маршруты
├── tasks.py              — Celery задача recalculate_monthly_cache
├── admin.py              — настройка админки
├── fixtures/             — фикстура с предустановленными категориями
├── templates/            — HTML-шаблоны
└── static/css/           — стили

finance_settings/         — настройки проекта
tests/                    — тесты pytest
docker-compose.yml        — Docker-конфигурация
```

## Функциональность

- Дашборд с суммами доходов/расходов за месяц и балансом
- Список операций с фильтрами (тип, категория, месяц) и пагинацией
- Создание, редактирование и удаление операций
- Валидация: дата не в будущем и не старше 5 лет, сумма > 0, категория соответствует типу
- Изоляция данных: каждый пользователь видит только свои записи
- Celery Beat: ежедневный пересчёт кэша сумм в Redis
