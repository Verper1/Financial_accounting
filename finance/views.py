from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.db.models import QuerySet, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from finance.filters import TransactionFilter
from finance.forms import TransactionForm
from finance.models import Transaction


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Главная страница — дашборд с суммами за месяц и балансом."""
    user = request.user
    assert isinstance(user, User)
    today = date.today()

    monthly_income = _get_monthly_sum(user, "income", today)
    monthly_expense = _get_monthly_sum(user, "expense", today)
    total_balance = _get_total_balance(user)

    context = {
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
        "total_balance": total_balance,
    }
    return render(request, "finance/dashboard.html", context)


def _get_monthly_sum(
    user: User,
    transaction_type: str,
    today: date,
) -> Decimal:
    """Сумма операций заданного типа за текущий месяц."""
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


@login_required
def transaction_list(request: HttpRequest) -> HttpResponse:
    """Список операций с фильтрацией и пагинацией."""
    queryset = Transaction.objects.filter(
        user=request.user,  # type: ignore[misc]
    ).select_related("category")

    filter_set = TransactionFilter(request.GET, queryset=queryset)

    paginator = Paginator(filter_set.qs, 20)
    page_number = request.GET.get("page", 1)
    page = paginator.get_page(page_number)

    context = {
        "filter": filter_set,
        "page_obj": page,
        "transactions": page.object_list,
    }
    return render(request, "finance/transaction_list.html", context)


class TransactionCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Создание новой финансовой операции."""

    model = Transaction
    form_class = TransactionForm
    template_name = "finance/transaction_form.html"
    success_url = reverse_lazy("dashboard")
    success_message = "Запись добавлена"

    def get_form_kwargs(self) -> dict:
        """Передаёт пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self) -> dict:
        """Передаёт type из GET-параметра в initial формы."""
        initial = super().get_initial()
        transaction_type = self.request.GET.get("type")
        if transaction_type in ("income", "expense"):
            initial["type"] = transaction_type
        return initial


class TransactionUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Редактирование финансовой операции."""

    model = Transaction
    form_class = TransactionForm
    template_name = "finance/transaction_form.html"
    success_url = reverse_lazy("dashboard")
    success_message = "Запись обновлена"

    def get_queryset(self) -> QuerySet[Transaction]:
        """Ограничивает записи текущим пользователем."""
        return Transaction.objects.filter(user=self.request.user)  # type: ignore[misc]

    def get_form_kwargs(self) -> dict:
        """Передаёт пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TransactionDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Удаление финансовой операции."""

    model = Transaction
    template_name = "finance/transaction_confirm_delete.html"
    success_url = reverse_lazy("dashboard")
    success_message = "Запись удалена"

    def get_queryset(self) -> QuerySet[Transaction]:
        """Ограничивает записи текущим пользователем."""
        return Transaction.objects.filter(user=self.request.user)  # type: ignore[misc]
