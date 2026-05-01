"""Тесты views."""

import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from finance.models import Category, Transaction


@pytest.mark.django_db
class TestDashboard:
    """Тесты главной страницы."""

    def test_dashboard_requires_login(self, client: Client) -> None:
        response = client.get(reverse("dashboard"))
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_dashboard_authenticated(
        self,
        authenticated_client: Client,
    ) -> None:
        response = authenticated_client.get(reverse("dashboard"))
        assert response.status_code == 200

    def test_dashboard_shows_monthly_sums(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
        expense_category: Category,
    ) -> None:
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Зарплата",
            amount=Decimal("50000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="expense",
            category=expense_category,
            source="Продукты",
            amount=Decimal("5000.00"),
            is_mandatory=True,
        )

        response = authenticated_client.get(reverse("dashboard"))
        assert response.status_code == 200
        assert "50000" in response.content.decode()
        assert "5000" in response.content.decode()

    def test_dashboard_shows_balance(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
        expense_category: Category,
    ) -> None:
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Зарплата",
            amount=Decimal("10000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="expense",
            category=expense_category,
            source="Продукты",
            amount=Decimal("3000.00"),
            is_mandatory=False,
        )

        response = authenticated_client.get(reverse("dashboard"))
        content = response.content.decode()
        assert "7000" in content


@pytest.mark.django_db
class TestTransactionList:
    """Тесты списка операций."""

    def test_list_requires_login(self, client: Client) -> None:
        response = client.get(reverse("transaction_list"))
        assert response.status_code == 302

    def test_list_authenticated(
        self,
        authenticated_client: Client,
    ) -> None:
        response = authenticated_client.get(reverse("transaction_list"))
        assert response.status_code == 200

    def test_list_shows_user_transactions(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
    ) -> None:
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Моя запись",
            amount=Decimal("1000.00"),
        )

        response = authenticated_client.get(reverse("transaction_list"))
        content = response.content.decode()
        assert "Моя запись" in content

    def test_list_hides_other_user_transactions(
        self,
        authenticated_client: Client,
        user: User,
        other_user: User,
        income_category: Category,
    ) -> None:
        Transaction.objects.create(
            user=other_user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Чужая запись",
            amount=Decimal("99999.00"),
        )

        response = authenticated_client.get(reverse("transaction_list"))
        content = response.content.decode()
        assert "Чужая запись" not in content

    def test_list_filter_by_type(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
        expense_category: Category,
    ) -> None:
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Источник Доход",
            amount=Decimal("1000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="expense",
            category=expense_category,
            source="Источник Расход",
            amount=Decimal("500.00"),
            is_mandatory=True,
        )

        response = authenticated_client.get(
            reverse("transaction_list") + "?type=income",
        )
        content = response.content.decode()
        assert "Источник Доход" in content
        assert "Источник Расход" not in content

    def test_list_filter_by_month(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
    ) -> None:
        Transaction.objects.create(
            user=user,
            date=datetime.date(2026, 3, 15),
            type="income",
            category=income_category,
            source="Источник Март",
            amount=Decimal("1000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date(2026, 4, 15),
            type="income",
            category=income_category,
            source="Источник Апрель",
            amount=Decimal("2000.00"),
        )

        response = authenticated_client.get(
            reverse("transaction_list") + "?month=2026-04",
        )
        content = response.content.decode()
        assert "Источник Апрель" in content
        assert "Источник Март" not in content


@pytest.mark.django_db
class TestTransactionCreate:
    """Тесты создания операции."""

    def test_create_requires_login(self, client: Client) -> None:
        response = client.get(reverse("transaction_create"))
        assert response.status_code == 302

    def test_create_page_rendered(
        self,
        authenticated_client: Client,
    ) -> None:
        response = authenticated_client.get(reverse("transaction_create"))
        assert response.status_code == 200

    def test_create_transaction(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
    ) -> None:
        response = authenticated_client.post(
            reverse("transaction_create"),
            {
                "date": datetime.date.today(),
                "type": "income",
                "category": income_category.id,
                "source": "Новая запись",
                "amount": "5000.00",
            },
        )
        assert response.status_code == 302
        assert response.url == reverse("dashboard")
        assert Transaction.objects.filter(user=user).count() == 1

    def test_create_invalid_data(
        self,
        authenticated_client: Client,
    ) -> None:
        response = authenticated_client.post(
            reverse("transaction_create"),
            {
                "date": "",
                "type": "income",
                "category": "",
                "source": "",
                "amount": "",
            },
        )
        assert response.status_code == 200
        assert Transaction.objects.count() == 0

    def test_create_with_type_income_param(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
    ) -> None:
        """Форма с ?type=income передаёт initial и скрывает is_mandatory."""
        response = authenticated_client.get(
            reverse("transaction_create") + "?type=income",
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "is_mandatory" not in content

    def test_create_with_type_expense_param(
        self,
        authenticated_client: Client,
        user: User,
        expense_category: Category,
    ) -> None:
        """Форма с ?type=expense показывает is_mandatory."""
        response = authenticated_client.get(
            reverse("transaction_create") + "?type=expense",
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "is_mandatory" in content


@pytest.mark.django_db
class TestTransactionUpdate:
    """Тесты редактирования операции."""

    def test_edit_page(
        self,
        authenticated_client: Client,
        income_transaction: Transaction,
    ) -> None:
        response = authenticated_client.get(
            reverse("transaction_edit", kwargs={"pk": income_transaction.pk}),
        )
        assert response.status_code == 200

    def test_edit_transaction(
        self,
        authenticated_client: Client,
        income_transaction: Transaction,
        income_category: Category,
    ) -> None:
        response = authenticated_client.post(
            reverse("transaction_edit", kwargs={"pk": income_transaction.pk}),
            {
                "date": datetime.date.today(),
                "type": "income",
                "category": income_category.id,
                "source": "Обновлённый источник",
                "amount": "60000.00",
            },
        )
        assert response.status_code == 302
        income_transaction.refresh_from_db()
        assert income_transaction.source == "Обновлённый источник"

    def test_edit_other_user_transaction_404(
        self,
        authenticated_client: Client,
        other_user: User,
        income_category: Category,
    ) -> None:
        """Нельзя редактировать чужую запись."""
        t = Transaction.objects.create(
            user=other_user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Чужая",
            amount=Decimal("1000.00"),
        )
        response = authenticated_client.get(
            reverse("transaction_edit", kwargs={"pk": t.pk}),
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestTransactionDelete:
    """Тесты удаления операции."""

    def test_delete_page(
        self,
        authenticated_client: Client,
        income_transaction: Transaction,
    ) -> None:
        response = authenticated_client.get(
            reverse("transaction_delete", kwargs={"pk": income_transaction.pk}),
        )
        assert response.status_code == 200

    def test_delete_transaction(
        self,
        authenticated_client: Client,
        income_transaction: Transaction,
    ) -> None:
        response = authenticated_client.post(
            reverse("transaction_delete", kwargs={"pk": income_transaction.pk}),
        )
        assert response.status_code == 302
        assert Transaction.objects.count() == 0

    def test_delete_other_user_transaction_404(
        self,
        authenticated_client: Client,
        other_user: User,
        income_category: Category,
    ) -> None:
        """Нельзя удалить чужую запись."""
        t = Transaction.objects.create(
            user=other_user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Чужая",
            amount=Decimal("1000.00"),
        )
        response = authenticated_client.post(
            reverse("transaction_delete", kwargs={"pk": t.pk}),
        )
        assert response.status_code == 404
        assert Transaction.objects.count() == 1
