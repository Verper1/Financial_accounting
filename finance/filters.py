from datetime import date
from typing import Any

import django_filters
from django.db.models import QuerySet

from finance.models import Category, Transaction

MONTH_NAMES = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}


def _generate_month_choices() -> list[tuple[str, str]]:
    """Генерирует список последних 12 месяцев для фильтра."""
    choices: list[tuple[str, str]] = [("", "Все месяцы")]
    today = date.today()
    for i in range(12):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        value = f"{year}-{month:02d}"
        label = f"{MONTH_NAMES[month]} {year}"
        choices.append((value, label))
    return choices


class TransactionFilter(django_filters.FilterSet):
    """Фильтр для списка операций."""

    type = django_filters.ChoiceFilter(
        choices=Transaction.TransactionType.choices,
        label="Тип операции",
    )
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label="Категория",
    )
    month = django_filters.ChoiceFilter(
        method="filter_by_month",
        label="Месяц",
        choices=[],
    )

    class Meta:
        model = Transaction
        fields: list[str] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.filters["month"].extra["choices"] = _generate_month_choices()

    def filter_by_month(
        self,
        queryset: QuerySet[Transaction],
        name: str,
        value: str,
    ) -> QuerySet[Transaction]:
        """Фильтрация по месяцу в формате YYYY-MM."""
        if not value:
            return queryset
        try:
            year, month = value.split("-")
            return queryset.filter(
                date__year=int(year),
                date__month=int(month),
            )
        except (ValueError, AttributeError):
            return queryset
