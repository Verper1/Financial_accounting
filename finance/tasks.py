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
        balance = _get_total_balance(user)
        month_key = f"{today.year}-{today.month:02d}"

        try:
            cache.set(
                f"finance:monthly:{user.id}:{month_key}:income",
                f"{income:.2f}",
                timeout=None,
            )
            cache.set(
                f"finance:monthly:{user.id}:{month_key}:expense",
                f"{expense:.2f}",
                timeout=None,
            )
            cache.set(
                f"finance:balance:{user.id}",
                f"{balance:.2f}",
                timeout=None,
            )
        except Exception:
            pass
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


def _get_total_balance(user: User) -> Decimal:
    """Баланс = все доходы минус все расходы."""
    income = Transaction.objects.filter(
        user=user,
        type="income",
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    expense = Transaction.objects.filter(
        user=user,
        type="expense",
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    return income - expense
