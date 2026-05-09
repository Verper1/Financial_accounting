from django.contrib.auth.models import User
from django.db import models


class Category(models.Model):
    """Предустановленная категория дохода или расхода."""

    class CategoryType(models.TextChoices):
        INCOME = "income", "Доход"
        EXPENSE = "expense", "Расход"

    name = models.CharField("Название", max_length=100)
    type = models.CharField(
        "Тип",
        max_length=7,
        choices=CategoryType.choices,
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["type", "name"]

    def __str__(self) -> str:
        return self.name


class Transaction(models.Model):
    """Финансовая операция пользователя."""

    class TransactionType(models.TextChoices):
        INCOME = "income", "Доход"
        EXPENSE = "expense", "Расход"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Пользователь",
    )
    date = models.DateField("Дата операции")
    type = models.CharField(
        "Тип операции",
        max_length=7,
        choices=TransactionType.choices,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Категория",
    )
    source = models.CharField("Источник / Место", max_length=200)
    amount = models.DecimalField(
        "Сумма",
        max_digits=12,
        decimal_places=2,
    )
    is_mandatory = models.BooleanField(
        "Обязательный расход",
        null=True,
        blank=True,
        default=None,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Операция"
        verbose_name_plural = "Операции"
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.date} | {self.get_type_display()} | {self.amount}"
