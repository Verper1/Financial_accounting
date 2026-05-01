from datetime import date
from decimal import Decimal
from typing import Any

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from finance.models import Category, Transaction


class TransactionForm(forms.ModelForm):
    """Форма создания/редактирования финансовой операции."""

    class Meta:
        model = Transaction
        fields = (
            "date",
            "type",
            "category",
            "source",
            "amount",
            "is_mandatory",
        )
        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "type": forms.Select(attrs={"id": "id_type"}),
            "category": forms.Select(attrs={"id": "id_category"}),
        }

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        *args: Any,
        user: User | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(data, *args, **kwargs)

        self._user = user

        transaction_type = self._get_transaction_type()
        if transaction_type == Transaction.TransactionType.INCOME:
            del self.fields["is_mandatory"]
            self.fields["category"].queryset = Category.objects.filter(  # type: ignore[attr-defined]
                type=Transaction.TransactionType.INCOME,
            )
        elif transaction_type == Transaction.TransactionType.EXPENSE:
            self.fields["category"].queryset = Category.objects.filter(  # type: ignore[attr-defined]
                type=Transaction.TransactionType.EXPENSE,
            )
            self.fields["is_mandatory"].required = True

    def _get_transaction_type(self) -> str | None:
        """Определяет тип операции из данных формы или instance."""
        if self.data.get("type"):
            return str(self.data.get("type"))
        if self.instance and self.instance.pk and self.instance.type:
            return self.instance.type
        if self.initial.get("type"):
            return str(self.initial.get("type"))
        return None

    def clean_date(self) -> date:
        """Проверяет, что дата не в будущем и не старше 5 лет."""
        transaction_date: date = self.cleaned_data["date"]
        today = date.today()

        if transaction_date > today:
            raise ValidationError("Дата не может быть в будущем.")

        five_years_ago = date(today.year - 5, today.month, today.day)
        if transaction_date < five_years_ago:
            raise ValidationError("Дата не может быть старше 5 лет.")

        return transaction_date

    def clean_amount(self) -> Decimal:
        """Проверяет, что сумма больше нуля."""
        amount: Decimal = self.cleaned_data["amount"]
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше нуля.")
        return amount

    def clean(self) -> dict[str, Any] | None:
        """Проверяет соответствие категории типу операции."""
        cleaned = super().clean()
        if not cleaned:
            return cleaned

        category: Category | None = cleaned.get("category")
        transaction_type: str | None = cleaned.get("type")

        if category and transaction_type:
            if category.type != transaction_type:
                raise ValidationError(
                    "Категория не соответствует типу операции.",
                )

        return cleaned

    def save(self, commit: bool = True) -> Transaction:
        """Сохраняет операцию, привязывая к пользователю."""
        transaction = super().save(commit=False)
        if self._user:
            transaction.user = self._user
        if transaction.type == Transaction.TransactionType.INCOME:
            transaction.is_mandatory = None
        if commit:
            transaction.save()
        return transaction
