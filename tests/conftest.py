"""Фикстуры для pytest."""

import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from finance.models import Category, Transaction


@pytest.fixture
def user(db: object) -> User:
    """Создаёт тестового пользователя."""
    return User.objects.create_user(
        username="testuser",
        password="testpass123",
    )


@pytest.fixture
def other_user(db: object) -> User:
    """Создаёт второго пользователя для проверки изоляции."""
    return User.objects.create_user(
        username="otheruser",
        password="testpass123",
    )


@pytest.fixture
def income_category(db: object) -> Category:
    """Категория дохода."""
    return Category.objects.create(name="Зарплата", type="income")


@pytest.fixture
def expense_category(db: object) -> Category:
    """Категория расхода."""
    return Category.objects.create(name="Продукты", type="expense")


@pytest.fixture
def categories(db: object) -> list[Category]:
    """Создаёт все предустановленные категории."""
    cats = [
        Category.objects.create(name="Зарплата", type="income"),
        Category.objects.create(name="Фриланс", type="income"),
        Category.objects.create(name="Продукты", type="expense"),
        Category.objects.create(name="Транспорт", type="expense"),
    ]
    return cats


@pytest.fixture
def income_transaction(
    user: User,
    income_category: Category,
) -> Transaction:
    """Транзакция дохода."""
    return Transaction.objects.create(
        user=user,
        date=datetime.date.today(),
        type="income",
        category=income_category,
        source="ООО Ромашка",
        amount=Decimal("50000.00"),
    )


@pytest.fixture
def expense_transaction(
    user: User,
    expense_category: Category,
) -> Transaction:
    """Транзакция расхода."""
    return Transaction.objects.create(
        user=user,
        date=datetime.date.today(),
        type="expense",
        category=expense_category,
        source="Пятёрочка",
        amount=Decimal("3500.50"),
        is_mandatory=True,
    )


@pytest.fixture
def authenticated_client(client: object, user: User) -> object:
    """Клиент с авторизованным пользователем."""
    client.login(username="testuser", password="testpass123")
    return client
