"""Тесты Celery-задач."""

import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache

from finance.models import Category, Transaction
from finance.tasks import recalculate_monthly_cache


@pytest.mark.django_db
class TestRecalculateMonthlyCache:
    """Тесты задачи recalculate_monthly_cache."""

    def test_task_updates_cache(
        self,
        user: User,
        income_category: Category,
        expense_category: Category,
    ) -> None:
        today = datetime.date.today()
        Transaction.objects.create(
            user=user,
            date=today,
            type="income",
            category=income_category,
            source="Зарплата",
            amount=Decimal("50000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=today,
            type="expense",
            category=expense_category,
            source="Продукты",
            amount=Decimal("10000.00"),
            is_mandatory=True,
        )

        result = recalculate_monthly_cache()

        assert "1" in result
        month_key = f"{today.year}-{today.month:02d}"
        income_cache = cache.get(
            f"finance:monthly:{user.id}:{month_key}:income",
        )
        expense_cache = cache.get(
            f"finance:monthly:{user.id}:{month_key}:expense",
        )
        assert income_cache == "50000.00"
        assert expense_cache == "10000.00"

    def test_task_with_no_transactions(
        self,
        user: User,
    ) -> None:
        result = recalculate_monthly_cache()
        assert "1" in result

        today = datetime.date.today()
        month_key = f"{today.year}-{today.month:02d}"
        income_cache = cache.get(
            f"finance:monthly:{user.id}:{month_key}:income",
        )
        assert income_cache == "0.00"

    def test_task_multiple_users(
        self,
        user: User,
        other_user: User,
        income_category: Category,
    ) -> None:
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Тест",
            amount=Decimal("3000.00"),
        )

        result = recalculate_monthly_cache()
        assert "2" in result
