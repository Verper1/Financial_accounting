from django.urls import path

from finance.views import (
    TransactionCreateView,
    TransactionDeleteView,
    TransactionUpdateView,
    dashboard,
    transaction_list,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("transactions/", transaction_list, name="transaction_list"),
    path(
        "transactions/create/",
        TransactionCreateView.as_view(),
        name="transaction_create",
    ),
    path(
        "transactions/<int:pk>/edit/",
        TransactionUpdateView.as_view(),
        name="transaction_edit",
    ),
    path(
        "transactions/<int:pk>/delete/",
        TransactionDeleteView.as_view(),
        name="transaction_delete",
    ),
]
