# Финансовый учёт

Веб-приложение для учёта личных доходов и расходов. Django, server-side rendering, без JavaScript.

## Стек

| Слой | Технология |
|------|-----------|
| Бэкенд | Python 3.13, Django 4.2.3 |
| БД | SQLite (локально) / PostgreSQL 15 (Docker) |
| Кэш | LocMemCache (без Redis) / RedisCache |
| Фоновые задачи | Celery + Redis (опционально) |
| Фильтрация | django-filter |
| Контейнеризация | Docker + docker-compose |
| Тестирование | pytest + pytest-django + pytest-cov (84 теста, 95% покрытие) |
| Линтинг | ruff, mypy, pre-commit |

## Локальный запуск (без Docker)

Redis и Celery **не требуются**. Проект работает на SQLite + LocMemCache.

1. Клонируйте репозиторий и перейдите в папку проекта:
   ```bash
   git clone https://github.com/Verper1/Financial_accounting.git
   cd Financial_accounting
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # Linux / macOS
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Примените миграции:
   ```bash
   python manage.py migrate
   ```

5. Загрузите предустановленные категории (обязательно — без них не будут работать формы):
   ```bash
   python manage.py loaddata categories.json
   ```

6. Запустите сервер:
   ```bash
   python manage.py runserver
   ```

7. Откройте http://127.0.0.1:8000/ и зарегистрируйтесь через «Регистрация».

Для доступа к админ-панели (/admin/) создайте суперпользователя:
```bash
python manage.py createsuperuser
```

## Запуск через Docker

1. Скопируйте `.env.example` в `.env`:
   ```bash
   cp .env.example .env
   ```

2. Минимальный запуск (web + PostgreSQL, без Redis/Celery):
   ```bash
   docker-compose up --build
   ```

3. Полный запуск (с Redis и Celery):
   ```bash
   docker-compose --profile full up --build
   ```

4. В отдельном терминале — миграции и категории:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py loaddata categories.json
   ```

5. Откройте http://localhost:8000/ и зарегистрируйтесь.

Для админ-панели:
```bash
docker-compose exec web python manage.py createsuperuser
```

## Тесты

```bash
pip install pytest pytest-django pytest-cov ruff mypy django-stubs[compatible-mypy]
pytest
```

84 теста, покрытие 95%+ (минимум 80% по требованиям).

```bash
ruff check finance/ tests/ finance_settings/   # линтер
mypy finance/ finance_settings/                 # типы
```

## Структура проекта

```
finance/                  — основное приложение
├── models.py             — модели Category и Transaction
├── forms.py              — TransactionForm, ProfileUsernameForm, ProfilePasswordForm
├── filters.py            — TransactionFilter (django-filter: тип, категория, год, месяц)
├── views.py              — views: дашборд, список, CRUD, signup, profile
├── urls.py               — URL-маршруты
├── tasks.py              — Celery задача recalculate_monthly_cache
├── admin.py              — настройка админки
├── fixtures/             — 13 предустановленных категорий
├── templates/            — HTML-шаблоны (Django Templates, SSR)
└── static/css/           — стили

finance_settings/         — настройки проекта
├── settings.py           — условный CACHES/Celery (Redis или LocMemCache)
├── test_settings.py      — SQLite + LocMemCache + CELERY_TASK_ALWAYS_EAGER
├── celery.py             — конфиг Celery
└── urls.py               — подключение finance.urls + auth

tests/                    — тесты pytest
├── conftest.py           — фикстуры (user, categories, transactions, cache clear)
├── test_models.py        — 8 тестов
├── test_forms.py         — 21 тест
├── test_views.py         — 52 теста
└── test_tasks.py         — 3 теста
```

## Модели данных

### Category — категория операции
| Поле | Тип | Описание |
|------|-----|----------|
| name | CharField(100) | Название («Зарплата», «Продукты») |
| type | CharField(7) | income / expense |

Предустановлено 13 категорий через fixture `categories.json`.

### Transaction — финансовая операция
| Поле | Тип | Описание |
|------|-----|----------|
| user | FK(User) | Пользователь (изоляция данных) |
| date | DateField | Дата операции |
| type | CharField(7) | income / expense |
| category | FK(Category, PROTECT) | Категория |
| source | CharField(200) | Описание (откуда / куда) |
| amount | Decimal(12, 2) | Сумма |
| is_mandatory | Boolean(null=True) | Обязательный расход (только для expense) |
| created_at | DateTimeField(auto) | Дата создания |
| updated_at | DateTimeField(auto) | Дата обновления |

## Функциональность

### Дашборд (/)
- Доход за текущий месяц
- Расход за текущий месяц
- Общий баланс (все доходы − все расходы)
- Красный цвет при отрицательном балансе
- Кэширование: сначала из кэша, fallback на SQL

### Список операций (/transactions/)
- Фильтры: тип операции, категория, год (input number), месяц
- Пагинация по 20 записей
- Итоговые суммы: «Всего заработано» / «Всего потрачено» / оба

### CRUD операций
- Создание: `/transactions/create/?type=income` — заголовок «Добавить доход»
- Редактирование: `/transactions/<pk>/edit/` → редирект на список
- Удаление: `/transactions/<pk>/delete/` → подтверждение → редирект на список
- Валидация: дата не в будущем и не старше 5 лет, сумма > 0, категория соответствует типу
- Изоляция: пользователь видит и редактирует только свои записи (чужие → 404)

### Авторизация
- Регистрация (/signup/)
- Вход/выход (django.contrib.auth)
- Профиль (/profile/): смена ника + смена пароля на одной странице

### Кэширование и Celery
- **С Redis**: ночной пересчёт кэша через Celery Beat (00:01), быстрое чтение на дашборде
- **Без Redis**: LocMemCache (кэш пуст → SQL), Celery отключён
- При CUD: инвалидация ключа баланса, фоновый пересчёт если Redis доступен

## Docker-сервисы

| Сервис | Профиль | Описание |
|--------|---------|----------|
| db | — | PostgreSQL 15 (обязательный) |
| web | — | Django runserver (обязательный) |
| redis | full | Redis 7 (опционально) |
| celery-worker | full | Celery worker (опционально) |
| celery-beat | full | Celery beat — ночной пересчёт (опционально) |

Минимальный запуск: `docker-compose up web db`
Полный: `docker-compose --profile full up`
