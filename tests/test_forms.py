"""Тесты форм."""

import datetime

import pytest
from django.contrib.auth.models import User

from finance.forms import (
    ProfilePasswordForm,
    ProfileUsernameForm,
    TransactionForm,
)
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
                "category": income_category.id,
                "source": "ООО Тест",
                "amount": "10000.00",
            },
            user=user,
            initial={"type": "income"},
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
                "category": expense_category.id,
                "source": "Магазин",
                "amount": "500.00",
                "is_mandatory": True,
            },
            user=user,
            initial={"type": "expense"},
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
                "category": income_category.id,
                "source": "Тест",
                "amount": "100.00",
            },
            user=user,
            initial={"type": "income"},
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
                "category": income_category.id,
                "source": "Тест",
                "amount": "100.00",
            },
            user=user,
            initial={"type": "income"},
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
                "category": income_category.id,
                "source": "Тест",
                "amount": "0.00",
            },
            user=user,
            initial={"type": "income"},
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
                "category": income_category.id,
                "source": "Тест",
                "amount": "-100.00",
            },
            user=user,
            initial={"type": "income"},
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
                "category": income_category.id,
                "source": "Тест",
                "amount": "100.00",
                "is_mandatory": True,
            },
            user=user,
            initial={"type": "expense"},
        )
        assert not form.is_valid()

    def test_is_mandatory_hidden_for_income(
        self,
        user: User,
    ) -> None:
        """Поле is_mandatory скрыто для дохода."""
        form = TransactionForm(
            user=user,
            initial={"type": "income"},
        )
        assert "is_mandatory" not in form.fields

    def test_is_mandatory_required_for_expense(
        self,
        user: User,
    ) -> None:
        """Поле is_mandatory обязательно для расхода."""
        form = TransactionForm(
            user=user,
            initial={"type": "expense"},
        )
        assert "is_mandatory" in form.fields
        assert form.fields["is_mandatory"].required is True

    def test_type_field_not_in_form(
        self,
        user: User,
    ) -> None:
        """Поле type не отображается в форме."""
        form = TransactionForm(
            user=user,
            initial={"type": "income"},
        )
        assert "type" not in form.fields

    def test_category_queryset_filtered_for_income(
        self,
        user: User,
        categories: list,
    ) -> None:
        """Для дохода показываются только категории дохода."""
        form = TransactionForm(
            user=user,
            initial={"type": "income"},
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
            user=user,
            initial={"type": "expense"},
        )
        qs = form.fields["category"].queryset
        assert qs.count() == 2
        assert all(c.type == "expense" for c in qs)

    def test_save_sets_user_and_type_from_initial(
        self,
        user: User,
        income_category: Category,
    ) -> None:
        """Метод save привязывает запись к пользователю и ставит тип из initial."""
        form = TransactionForm(
            data={
                "date": datetime.date.today(),
                "category": income_category.id,
                "source": "Тест",
                "amount": "100.00",
            },
            user=user,
            initial={"type": "income"},
        )
        assert form.is_valid()
        transaction = form.save()
        assert transaction.user == user
        assert transaction.type == "income"
        assert transaction.is_mandatory is None

    def test_save_expense_type_from_initial(
        self,
        user: User,
        expense_category: Category,
    ) -> None:
        """Для расхода type и is_mandatory сохраняются корректно."""
        form = TransactionForm(
            data={
                "date": datetime.date.today(),
                "category": expense_category.id,
                "source": "Тест",
                "amount": "500.00",
                "is_mandatory": True,
            },
            user=user,
            initial={"type": "expense"},
        )
        assert form.is_valid()
        transaction = form.save()
        assert transaction.type == "expense"
        assert transaction.is_mandatory is True

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
        assert "type" not in form.fields


@pytest.mark.django_db
class TestProfileUsernameForm:
    """Тесты формы смены ника."""

    def test_valid_username_change(self, user: User) -> None:
        form = ProfileUsernameForm(
            data={"username": "newname"},
            instance=user,
        )
        assert form.is_valid(), form.errors

    def test_duplicate_username_rejected(
        self,
        user: User,
        other_user: User,
    ) -> None:
        form = ProfileUsernameForm(
            data={"username": "otheruser"},
            instance=user,
        )
        assert not form.is_valid()
        assert "username" in form.errors

    def test_same_username_allowed(self, user: User) -> None:
        form = ProfileUsernameForm(
            data={"username": "testuser"},
            instance=user,
        )
        assert form.is_valid()


@pytest.mark.django_db
class TestProfilePasswordForm:
    """Тесты формы смены пароля."""

    def test_valid_password_change(self, user: User) -> None:
        form = ProfilePasswordForm(
            data={
                "old_password": "testpass123",
                "new_password1": "Str0ng!NewPass",
                "new_password2": "Str0ng!NewPass",
            },
            user=user,
        )
        assert form.is_valid(), form.errors

    def test_wrong_old_password(self, user: User) -> None:
        form = ProfilePasswordForm(
            data={
                "old_password": "wrongpass",
                "new_password1": "Str0ng!NewPass",
                "new_password2": "Str0ng!NewPass",
            },
            user=user,
        )
        assert not form.is_valid()

    def test_passwords_dont_match(self, user: User) -> None:
        form = ProfilePasswordForm(
            data={
                "old_password": "testpass123",
                "new_password1": "Str0ng!NewPass",
                "new_password2": "DifferentPass1",
            },
            user=user,
        )
        assert not form.is_valid()
