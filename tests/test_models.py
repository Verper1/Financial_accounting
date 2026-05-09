"""Тесты моделей."""

import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from finance.models import Category, Transaction


@pytest.mark.django_db
class TestCategory:
    """Тесты модели Category."""

    def test_create_category(self) -> None:
        category = Category.objects.create(name="Зарплата", type="income")
        assert category.name == "Зарплата"
        assert category.type == "income"

    def test_category_str(self) -> None:
        category = Category.objects.create(name="Фриланс", type="income")
        assert str(category) == "Фриланс"

    def test_category_ordering(self) -> None:
        Category.objects.create(name="Продукты", type="expense")
        Category.objects.create(name="Зарплата", type="income")
        cats = list(Category.objects.all())
        assert cats[0].type == "expense"


@pytest.mark.django_db
class TestTransaction:
    """Тесты модели Transaction."""

    def test_create_income_transaction(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        t = Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="ООО Тест",
            amount=Decimal("10000.00"),
        )
        assert t.type == "income"
        assert t.amount == Decimal("10000.00")
        assert t.is_mandatory is None

    def test_create_expense_transaction(
        self,
        user: User,
        expense_category: Category,
    ) -> None:
        t = Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="expense",
            category=expense_category,
            source="Магазин",
            amount=Decimal("500.00"),
            is_mandatory=True,
        )
        assert t.type == "expense"
        assert t.is_mandatory is True

    def test_transaction_str(
        self,
        income_transaction: Transaction,
    ) -> None:
        result = str(income_transaction)
        assert str(datetime.date.today()) in result
        assert "Доход" in result

    def test_transaction_user_isolation(
        self,
        user: User,
        other_user: User,
        income_category: Category,
    ) -> None:
        """Пользователь видит только свои записи."""
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Тест1",
            amount=Decimal("100.00"),
        )
        Transaction.objects.create(
            user=other_user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Тест2",
            amount=Decimal("200.00"),
        )

        user_transactions = Transaction.objects.filter(user=user)
        assert user_transactions.count() == 1
        assert user_transactions.first().source == "Тест1"

    def test_transaction_ordering(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        """Новые записи должны быть сверху."""
        Transaction.objects.create(
            user=user,
            date=datetime.date(2026, 4, 1),
            type="income",
            category=income_category,
            source="Старая",
            amount=Decimal("100.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date(2026, 5, 1),
            type="income",
            category=income_category,
            source="Новая",
            amount=Decimal("200.00"),
        )
        transactions = list(Transaction.objects.filter(user=user))
        assert transactions[0].source == "Новая"

    def test_auto_timestamps(
        self,
        income_transaction: Transaction,
    ) -> None:
        assert income_transaction.created_at is not None
        assert income_transaction.updated_at is not None
