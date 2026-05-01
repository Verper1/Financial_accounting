"""Тесты форм."""

import datetime

import pytest
from django.contrib.auth.models import User

from finance.forms import TransactionForm
from finance.models import Category


@pytest.mark.django_db
class TestTransactionForm:
    """Тесты формы TransactionForm."""

    def test_valid_income_form(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        form = TransactionForm(
            data={
                "date": datetime.date.today(),
                "type": "income",
                "category": income_category.id,
                "source": "ООО Тест",
                "amount": "10000.00",
            },
            user=user,
        )
        assert form.is_valid(), form.errors

    def test_valid_expense_form(
        self,
        user: User,
        expense_category: Category,
    ) -> None:
        form = TransactionForm(
            data={
                "date": datetime.date.today(),
                "type": "expense",
                "category": expense_category.id,
                "source": "Магазин",
                "amount": "500.00",
                "is_mandatory": True,
            },
            user=user,
        )
        assert form.is_valid(), form.errors

    def test_future_date_invalid(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        form = TransactionForm(
            data={
                "date": datetime.date.today() + datetime.timedelta(days=1),
                "type": "income",
                "category": income_category.id,
                "source": "Тест",
                "amount": "100.00",
            },
            user=user,
        )
        assert not form.is_valid()
        assert "date" in form.errors

    def test_date_too_old(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        form = TransactionForm(
            data={
                "date": datetime.date.today() - datetime.timedelta(days=365 * 6),
                "type": "income",
                "category": income_category.id,
                "source": "Тест",
                "amount": "100.00",
            },
            user=user,
        )
        assert not form.is_valid()
        assert "date" in form.errors

    def test_zero_amount_invalid(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        form = TransactionForm(
            data={
                "date": datetime.date.today(),
                "type": "income",
                "category": income_category.id,
                "source": "Тест",
                "amount": "0.00",
            },
            user=user,
        )
        assert not form.is_valid()
        assert "amount" in form.errors

    def test_negative_amount_invalid(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        form = TransactionForm(
            data={
                "date": datetime.date.today(),
                "type": "income",
                "category": income_category.id,
                "source": "Тест",
                "amount": "-100.00",
            },
            user=user,
        )
        assert not form.is_valid()
        assert "amount" in form.errors

    def test_category_type_mismatch(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        """Нельзя выбрать категорию дохода для расхода."""
        form = TransactionForm(
            data={
                "date": datetime.date.today(),
                "type": "expense",
                "category": income_category.id,
                "source": "Тест",
                "amount": "100.00",
                "is_mandatory": True,
            },
            user=user,
        )
        assert not form.is_valid()

    def test_is_mandatory_hidden_for_income(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        """Поле is_mandatory скрыто для дохода (через data)."""
        form = TransactionForm(
            data={
                "type": "income",
            },
            user=user,
        )
        assert "is_mandatory" not in form.fields

    def test_is_mandatory_required_for_expense(
        self,
        user: User,
        expense_category: Category,
    ) -> None:
        """Поле is_mandatory обязательно для расхода."""
        form = TransactionForm(
            data={
                "type": "expense",
            },
            user=user,
        )
        assert "is_mandatory" in form.fields
        assert form.fields["is_mandatory"].required is True

    def test_category_queryset_filtered_for_income(
        self,
        user: User,
        categories: list,
    ) -> None:
        """Для дохода показываются только категории дохода."""
        form = TransactionForm(
            data={"type": "income"},
            user=user,
        )
        qs = form.fields["category"].queryset
        assert qs.count() == 2
        assert all(c.type == "income" for c in qs)

    def test_category_queryset_filtered_for_expense(
        self,
        user: User,
        categories: list,
    ) -> None:
        """Для расхода показываются только категории расхода."""
        form = TransactionForm(
            data={"type": "expense"},
            user=user,
        )
        qs = form.fields["category"].queryset
        assert qs.count() == 2
        assert all(c.type == "expense" for c in qs)

    def test_save_sets_user(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        """Метод save привязывает запись к пользователю."""
        form = TransactionForm(
            data={
                "date": datetime.date.today(),
                "type": "income",
                "category": income_category.id,
                "source": "Тест",
                "amount": "100.00",
            },
            user=user,
        )
        assert form.is_valid()
        transaction = form.save()
        assert transaction.user == user
        assert transaction.is_mandatory is None

    def test_income_sets_is_mandatory_none(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        """Для дохода is_mandatory всегда None."""
        form = TransactionForm(
            data={
                "date": datetime.date.today(),
                "type": "income",
                "category": income_category.id,
                "source": "Тест",
                "amount": "5000.00",
            },
            user=user,
        )
        assert form.is_valid()
        transaction = form.save()
        assert transaction.is_mandatory is None

    def test_initial_type_filters_categories_income(
        self,
        user: User,
        categories: list,
    ) -> None:
        """Initial type=income фильтрует категории и скрывает is_mandatory."""
        form = TransactionForm(
            initial={"type": "income"},
            user=user,
        )
        qs = form.fields["category"].queryset
        assert qs.count() == 2
        assert all(c.type == "income" for c in qs)
        assert "is_mandatory" not in form.fields

    def test_initial_type_filters_categories_expense(
        self,
        user: User,
        categories: list,
    ) -> None:
        """Initial type=expense фильтрует категории и делает is_mandatory обязательным."""
        form = TransactionForm(
            initial={"type": "expense"},
            user=user,
        )
        qs = form.fields["category"].queryset
        assert qs.count() == 2
        assert all(c.type == "expense" for c in qs)
        assert form.fields["is_mandatory"].required is True

    def test_instance_type_filters_on_edit(
        self,
        user: User,
        income_category: Category,
        income_transaction: object,
    ) -> None:
        """При редактировании дохода категории фильтруются по instance.type."""
        form = TransactionForm(
            instance=income_transaction,
            user=user,
        )
        qs = form.fields["category"].queryset
        assert all(c.type == "income" for c in qs)
        assert "is_mandatory" not in form.fields
