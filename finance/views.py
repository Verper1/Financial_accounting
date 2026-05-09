from datetime import date
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import QuerySet, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from finance.filters import TransactionFilter
from finance.forms import (
    ProfilePasswordForm,
    ProfileUsernameForm,
    TransactionForm,
)
from finance.models import Transaction
from finance.tasks import recalculate_monthly_cache


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Главная страница — дашборд с суммами за месяц и балансом."""
    user = request.user
    assert isinstance(user, User)
    today = date.today()

    monthly_income = _get_cached_or_db_sum(user, "income", today.year, today.month)
    monthly_expense = _get_cached_or_db_sum(user, "expense", today.year, today.month)
    total_balance = _get_cached_or_db_balance(user)

    context = {
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
        "total_balance": total_balance,
    }
    return render(request, "finance/dashboard.html", context)


def _get_cached_or_db_sum(
    user: User,
    transaction_type: str,
    year: int,
    month: int,
) -> Decimal:
    """Сумма операций из кэша или SQL."""
    cache_key = f"finance:monthly:{user.id}:{year}-{month:02d}:{transaction_type}"
    try:
        cached = cache.get(cache_key)
        if cached is not None:
            return Decimal(str(cached))
    except Exception:
        pass

    result = Transaction.objects.filter(
        user=user,
        type=transaction_type,
        date__year=year,
        date__month=month,
    ).aggregate(total=Sum("amount"))
    return result["total"] or Decimal("0")


def _get_cached_or_db_balance(user: User) -> Decimal:
    """Баланс из кэша или SQL."""
    cache_key = f"finance:balance:{user.id}"
    try:
        cached = cache.get(cache_key)
        if cached is not None:
            return Decimal(str(cached))
    except Exception:
        pass

    income = Transaction.objects.filter(
        user=user,
        type="income",
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    expense = Transaction.objects.filter(
        user=user,
        type="expense",
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    return income - expense


def _invalidate_balance_cache(user: object) -> None:
    """Удаляет кэш баланса пользователя."""
    try:
        cache.delete(f"finance:balance:{user.id}")  # type: ignore[attr-defined]
    except Exception:
        pass


@login_required
def transaction_list(request: HttpRequest) -> HttpResponse:
    """Список операций с фильтрацией и пагинацией."""
    queryset = Transaction.objects.filter(
        user=request.user,  # type: ignore[misc]
    ).select_related("category")

    filter_set = TransactionFilter(request.GET, queryset=queryset)

    get_no_type = request.GET.copy()
    get_no_type.pop("type", None)

    income_params = get_no_type.copy()
    income_params["type"] = "income"
    total_income = TransactionFilter(
        income_params,
        queryset=queryset,
    ).qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    expense_params = get_no_type.copy()
    expense_params["type"] = "expense"
    total_expense = TransactionFilter(
        expense_params,
        queryset=queryset,
    ).qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    paginator = Paginator(filter_set.qs, 20)
    page_number = request.GET.get("page", 1)
    page = paginator.get_page(page_number)

    context = {
        "filter": filter_set,
        "page_obj": page,
        "transactions": page.object_list,
        "total_income": total_income,
        "total_expense": total_expense,
        "current_type": request.GET.get("type", ""),
    }
    return render(request, "finance/transaction_list.html", context)


class TransactionCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Создание новой финансовой операции."""

    model = Transaction
    form_class = TransactionForm
    template_name = "finance/transaction_form.html"
    success_url = reverse_lazy("dashboard")
    success_message = "Запись добавлена"

    def get_context_data(self, **kwargs: object) -> dict:
        """Передаёт заголовок страницы в шаблон."""
        context = super().get_context_data(**kwargs)
        transaction_type = self.request.GET.get("type")
        if transaction_type == "income":
            context["page_title"] = "Добавить доход"
        elif transaction_type == "expense":
            context["page_title"] = "Добавить расход"
        else:
            context["page_title"] = "Новая запись"
        return context

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

    def form_valid(self, form: TransactionForm) -> HttpResponse:
        response = super().form_valid(form)
        _invalidate_balance_cache(self.request.user)
        if settings.CELERY_BROKER_URL:
            recalculate_monthly_cache.delay()
        return response


class TransactionUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Редактирование финансовой операции."""

    model = Transaction
    form_class = TransactionForm
    template_name = "finance/transaction_form.html"
    success_url = reverse_lazy("transaction_list")
    success_message = "Запись обновлена"

    def get_context_data(self, **kwargs: object) -> dict:
        """Передаёт заголовок страницы в шаблон."""
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Редактирование записи"
        return context

    def get_queryset(self) -> QuerySet[Transaction]:
        """Ограничивает записи текущим пользователем."""
        return Transaction.objects.filter(user=self.request.user)  # type: ignore[misc]

    def get_form_kwargs(self) -> dict:
        """Передаёт пользователя в форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: TransactionForm) -> HttpResponse:
        response = super().form_valid(form)
        _invalidate_balance_cache(self.request.user)
        if settings.CELERY_BROKER_URL:
            recalculate_monthly_cache.delay()
        return response


class TransactionDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Удаление финансовой операции."""

    model = Transaction
    template_name = "finance/transaction_confirm_delete.html"
    success_url = reverse_lazy("transaction_list")
    success_message = "Запись удалена"

    def get_queryset(self) -> QuerySet[Transaction]:
        """Ограничивает записи текущим пользователем."""
        return Transaction.objects.filter(user=self.request.user)  # type: ignore[misc]

    def form_valid(self, form: Any) -> HttpResponse:
        response = super().form_valid(form)
        _invalidate_balance_cache(self.request.user)
        if settings.CELERY_BROKER_URL:
            recalculate_monthly_cache.delay()
        return response


def signup(request: HttpRequest) -> HttpResponse:
    """Регистрация нового пользователя."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form: UserCreationForm = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "finance/signup.html", {"form": form})


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """Личный кабинет: смена ника и пароля."""
    user = request.user
    assert isinstance(user, User)

    username_form = ProfileUsernameForm(instance=user)
    password_form = ProfilePasswordForm(user=user)

    if request.method == "POST":
        if "update_username" in request.POST:
            username_form = ProfileUsernameForm(request.POST, instance=user)
            if username_form.is_valid():
                new_username = username_form.cleaned_data["username"]
                old_username = User.objects.get(pk=user.pk).username
                if new_username != old_username:
                    username_form.save()
                    messages.success(request, "Данные обновлены")
                return redirect("profile")

        elif "update_password" in request.POST:
            password_form = ProfilePasswordForm(request.POST, user=user)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Пароль обновлён. Войдите заново.")
                return redirect("login")

    context = {
        "username_form": username_form,
        "password_form": password_form,
    }
    return render(request, "finance/profile.html", context)
