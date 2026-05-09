import django_filters
from django import forms

from finance.models import Category, Transaction

MONTH_CHOICES: list[tuple[str, str]] = [
    ("1", "Январь"),
    ("2", "Февраль"),
    ("3", "Март"),
    ("4", "Апрель"),
    ("5", "Май"),
    ("6", "Июнь"),
    ("7", "Июль"),
    ("8", "Август"),
    ("9", "Сентябрь"),
    ("10", "Октябрь"),
    ("11", "Ноябрь"),
    ("12", "Декабрь"),
]


class TransactionFilter(django_filters.FilterSet):
    """Фильтр для списка операций."""

    type = django_filters.ChoiceFilter(
        choices=Transaction.TransactionType.choices,
        label="Тип операции",
        empty_label="Все операции",
    )
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label="Категория",
        empty_label="Все категории",
    )
    year = django_filters.NumberFilter(
        field_name="date",
        lookup_expr="year",
        label="Год",
        widget=forms.NumberInput(attrs={"placeholder": "Год"}),
    )
    month = django_filters.ChoiceFilter(
        field_name="date",
        lookup_expr="month",
        label="Месяц",
        choices=MONTH_CHOICES,
        empty_label="Все месяцы",
    )

    class Meta:
        model = Transaction
        fields: list[str] = []
