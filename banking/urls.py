from django.urls import path

from .views import (
    AccountListCreateView,
    TransferCreateView,
    TransferHistoryView,
    DepositCreateView,
)

urlpatterns = [

    path(
        "accounts/",
        AccountListCreateView.as_view(),
        name="accounts"
    ),

    path(
        "transfers/",
        TransferCreateView.as_view(),
        name="transfer-create"
    ),

    path(
        "transfers/history/",
        TransferHistoryView.as_view(),
        name="transfer-history"
    ),

    path(
        "deposits/",
        DepositCreateView.as_view(),
        name="deposit-create"
    ),

]
