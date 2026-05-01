from datetime import date
from decimal import Decimal

from celery import shared_task
from django.contrib.auth.models import User
from django.db.models import Sum

from finance.models import Transaction


@shared_task
def recalculate_monthly_cache() -> str:
    """Пересчитывает кэш сумм доходов/расходов за текущий месяц для всех пользователей."""
    from django.core.cache import cache

    today = date.today()
    users = User.objects.all()
    updated = 0

    for user in users:
        income = _get_month_sum(user, "income", today)
        expense = _get_month_sum(user, "expense", today)
        month_key = f"{today.year}-{today.month:02d}"

        cache_key_income = f"finance:monthly:{user.id}:{month_key}:income"
        cache_key_expense = f"finance:monthly:{user.id}:{month_key}:expense"

        cache.set(cache_key_income, f"{income:.2f}", timeout=None)
        cache.set(cache_key_expense, f"{expense:.2f}", timeout=None)
        updated += 1

    return f"Обновлено пользователей: {updated}"


def _get_month_sum(user: User, transaction_type: str, today: date) -> Decimal:
    """Сумма операций за текущий месяц."""
    result = Transaction.objects.filter(
        user=user,
        type=transaction_type,
        date__year=today.year,
        date__month=today.month,
    ).aggregate(total=Sum("amount"))
    return result["total"] or Decimal("0")
