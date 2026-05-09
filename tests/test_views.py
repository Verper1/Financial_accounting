"""Тесты views."""

import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
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

    def test_dashboard_negative_balance_has_negative_class(
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
            source="Малый доход",
            amount=Decimal("100.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="expense",
            category=expense_category,
            source="Большой расход",
            amount=Decimal("5000.00"),
            is_mandatory=True,
        )

        response = authenticated_client.get(reverse("dashboard"))
        content = response.content.decode()
        assert "negative" in content

    def test_dashboard_has_all_records_link(
        self,
        authenticated_client: Client,
    ) -> None:
        response = authenticated_client.get(reverse("dashboard"))
        content = response.content.decode()
        assert reverse("transaction_list") in content


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

    def test_list_filter_by_year(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
    ) -> None:
        Transaction.objects.create(
            user=user,
            date=datetime.date(2025, 6, 15),
            type="income",
            category=income_category,
            source="Источник 2025",
            amount=Decimal("1000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date(2026, 4, 15),
            type="income",
            category=income_category,
            source="Источник 2026",
            amount=Decimal("2000.00"),
        )

        response = authenticated_client.get(
            reverse("transaction_list") + "?year=2026",
        )
        content = response.content.decode()
        assert "Источник 2026" in content
        assert "Источник 2025" not in content

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
            reverse("transaction_list") + "?month=4",
        )
        content = response.content.decode()
        assert "Источник Апрель" in content
        assert "Источник Март" not in content

    def test_list_year_is_number_input(
        self,
        authenticated_client: Client,
    ) -> None:
        """Поле года — input type=number, а не select."""
        response = authenticated_client.get(reverse("transaction_list"))
        content = response.content.decode()
        assert 'name="year"' in content
        assert 'type="number"' in content

    def test_list_filter_empty_labels(
        self,
        authenticated_client: Client,
    ) -> None:
        """Пустые значения фильтров — человекочитаемые."""
        response = authenticated_client.get(reverse("transaction_list"))
        content = response.content.decode()
        assert "Все операции" in content
        assert "Все категории" in content
        assert "Все месяцы" in content

    def test_list_summary_income_filter(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
        expense_category: Category,
    ) -> None:
        """При фильтре type=income — итог по доходам."""
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Зарплата",
            amount=Decimal("5000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="expense",
            category=expense_category,
            source="Продукты",
            amount=Decimal("1000.00"),
            is_mandatory=True,
        )

        response = authenticated_client.get(
            reverse("transaction_list") + "?type=income",
        )
        content = response.content.decode()
        assert "Всего заработано" in content
        assert "5000" in content
        assert response.context["total_income"] == Decimal("5000.00")

    def test_list_summary_expense_filter(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
        expense_category: Category,
    ) -> None:
        """При фильтре type=expense — итог по расходам."""
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Зарплата",
            amount=Decimal("5000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="expense",
            category=expense_category,
            source="Продукты",
            amount=Decimal("1000.00"),
            is_mandatory=True,
        )

        response = authenticated_client.get(
            reverse("transaction_list") + "?type=expense",
        )
        content = response.content.decode()
        assert "Всего потрачено" in content
        assert "1000" in content
        assert response.context["total_expense"] == Decimal("1000.00")

    def test_list_summary_all_types(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
        expense_category: Category,
    ) -> None:
        """Без фильтра типа — оба итога."""
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="income",
            category=income_category,
            source="Зарплата",
            amount=Decimal("3000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date.today(),
            type="expense",
            category=expense_category,
            source="Продукты",
            amount=Decimal("1500.00"),
            is_mandatory=False,
        )

        response = authenticated_client.get(reverse("transaction_list"))
        content = response.content.decode()
        assert "Доходы:" in content
        assert "Расходы:" in content
        assert response.context["total_income"] == Decimal("3000.00")
        assert response.context["total_expense"] == Decimal("1500.00")

    def test_list_summary_respects_month_filter(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
    ) -> None:
        """Итоги считаются только за отфильтрованный месяц."""
        Transaction.objects.create(
            user=user,
            date=datetime.date(2026, 3, 15),
            type="income",
            category=income_category,
            source="Март",
            amount=Decimal("1000.00"),
        )
        Transaction.objects.create(
            user=user,
            date=datetime.date(2026, 4, 15),
            type="income",
            category=income_category,
            source="Апрель",
            amount=Decimal("2000.00"),
        )

        response = authenticated_client.get(
            reverse("transaction_list") + "?month=3",
        )
        assert response.context["total_income"] == Decimal("1000.00")


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
            reverse("transaction_create") + "?type=income",
            {
                "date": datetime.date.today(),
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
            reverse("transaction_create") + "?type=income",
            {
                "date": "",
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

    def test_create_expense_checkbox_row(
        self,
        authenticated_client: Client,
    ) -> None:
        """Чекбокс is_mandatory обёрнут в .checkbox-row."""
        response = authenticated_client.get(
            reverse("transaction_create") + "?type=expense",
        )
        content = response.content.decode()
        assert "checkbox-row" in content

    def test_create_no_type_field_in_form(
        self,
        authenticated_client: Client,
    ) -> None:
        """Поле type не отображается в форме создания."""
        response = authenticated_client.get(
            reverse("transaction_create") + "?type=income",
        )
        content = response.content.decode()
        assert 'name="type"' not in content

    def test_create_title_income(
        self,
        authenticated_client: Client,
    ) -> None:
        """Заголовок 'Добавить доход' при type=income."""
        response = authenticated_client.get(
            reverse("transaction_create") + "?type=income",
        )
        assert response.context["page_title"] == "Добавить доход"
        assert "Добавить доход" in response.content.decode()

    def test_create_title_expense(
        self,
        authenticated_client: Client,
    ) -> None:
        """Заголовок 'Добавить расход' при type=expense."""
        response = authenticated_client.get(
            reverse("transaction_create") + "?type=expense",
        )
        assert response.context["page_title"] == "Добавить расход"
        assert "Добавить расход" in response.content.decode()

    def test_create_title_default(
        self,
        authenticated_client: Client,
    ) -> None:
        """Заголовок 'Новая запись' без параметра type."""
        response = authenticated_client.get(reverse("transaction_create"))
        assert response.context["page_title"] == "Новая запись"


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
                "category": income_category.id,
                "source": "Обновлённый источник",
                "amount": "60000.00",
            },
        )
        assert response.status_code == 302
        assert response.url == reverse("transaction_list")
        income_transaction.refresh_from_db()
        assert income_transaction.source == "Обновлённый источник"

    def test_edit_no_type_field(
        self,
        authenticated_client: Client,
        income_transaction: Transaction,
    ) -> None:
        """При редактировании поле type не отображается."""
        response = authenticated_client.get(
            reverse("transaction_edit", kwargs={"pk": income_transaction.pk}),
        )
        content = response.content.decode()
        assert 'name="type"' not in content

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
        assert response.url == reverse("transaction_list")
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


@pytest.mark.django_db
class TestSignup:
    """Тесты регистрации."""

    def test_signup_page_renders(self, client: Client) -> None:
        response = client.get(reverse("signup"))
        assert response.status_code == 200

    def test_signup_creates_user(self, client: Client) -> None:
        response = client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "password1": "Str0ng!Pass123",
                "password2": "Str0ng!Pass123",
            },
        )
        assert response.status_code == 302
        assert response.url == reverse("login")
        assert User.objects.filter(username="newuser").exists()

    def test_signup_invalid_data(self, client: Client) -> None:
        response = client.post(
            reverse("signup"),
            {
                "username": "",
                "password1": "short",
                "password2": "short",
            },
        )
        assert response.status_code == 200
        assert User.objects.count() == 0

    def test_signup_redirects_if_authenticated(
        self,
        authenticated_client: Client,
    ) -> None:
        response = authenticated_client.get(reverse("signup"))
        assert response.status_code == 302


@pytest.mark.django_db
class TestProfile:
    """Тесты личного кабинета."""

    def test_profile_requires_login(self, client: Client) -> None:
        response = client.get(reverse("profile"))
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_profile_page_renders(
        self,
        authenticated_client: Client,
    ) -> None:
        response = authenticated_client.get(reverse("profile"))
        assert response.status_code == 200

    def test_profile_change_username(
        self,
        authenticated_client: Client,
        user: User,
    ) -> None:
        response = authenticated_client.post(
            reverse("profile"),
            {
                "update_username": "",
                "username": "newusername",
            },
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.username == "newusername"

    def test_profile_change_username_duplicate(
        self,
        authenticated_client: Client,
        user: User,
        other_user: User,
    ) -> None:
        response = authenticated_client.post(
            reverse("profile"),
            {
                "update_username": "",
                "username": "otheruser",
            },
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.username == "testuser"

    def test_profile_same_username_no_message(
        self,
        authenticated_client: Client,
        user: User,
    ) -> None:
        """При отправке того же ника — редирект без сообщения."""
        response = authenticated_client.post(
            reverse("profile"),
            {
                "update_username": "",
                "username": "testuser",
            },
        )
        assert response.status_code == 302
        assert response.url == reverse("profile")
        user.refresh_from_db()
        assert user.username == "testuser"

    def test_profile_change_password(
        self,
        authenticated_client: Client,
        user: User,
    ) -> None:
        response = authenticated_client.post(
            reverse("profile"),
            {
                "update_password": "",
                "old_password": "testpass123",
                "new_password1": "Str0ng!NewPass1",
                "new_password2": "Str0ng!NewPass1",
            },
        )
        assert response.status_code == 302
        assert response.url == reverse("login")
        user.refresh_from_db()
        assert user.check_password("Str0ng!NewPass1")

    def test_profile_change_password_wrong_old(
        self,
        authenticated_client: Client,
        user: User,
    ) -> None:
        response = authenticated_client.post(
            reverse("profile"),
            {
                "update_password": "",
                "old_password": "wrongpass",
                "new_password1": "Str0ng!NewPass1",
                "new_password2": "Str0ng!NewPass1",
            },
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestCacheInvalidation:
    """Тесты инвалидации кэша при CUD операциях."""

    def test_create_invalidates_balance_cache(
        self,
        authenticated_client: Client,
        user: User,
        income_category: Category,
    ) -> None:
        cache.set(f"finance:balance:{user.id}", "999.99")
        authenticated_client.post(
            reverse("transaction_create") + "?type=income",
            {
                "date": datetime.date.today(),
                "category": income_category.id,
                "source": "Тест",
                "amount": "1000.00",
            },
        )
        assert cache.get(f"finance:balance:{user.id}") is None

    def test_update_invalidates_balance_cache(
        self,
        authenticated_client: Client,
        user: User,
        income_transaction: Transaction,
        income_category: Category,
    ) -> None:
        cache.set(f"finance:balance:{user.id}", "999.99")
        authenticated_client.post(
            reverse("transaction_edit", kwargs={"pk": income_transaction.pk}),
            {
                "date": datetime.date.today(),
                "category": income_category.id,
                "source": "Обновлённый",
                "amount": "60000.00",
            },
        )
        assert cache.get(f"finance:balance:{user.id}") is None

    def test_delete_invalidates_balance_cache(
        self,
        authenticated_client: Client,
        user: User,
        income_transaction: Transaction,
    ) -> None:
        cache.set(f"finance:balance:{user.id}", "999.99")
        authenticated_client.post(
            reverse("transaction_delete", kwargs={"pk": income_transaction.pk}),
        )
        assert cache.get(f"finance:balance:{user.id}") is None
