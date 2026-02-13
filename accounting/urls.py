from django.urls import path
from . import views

app_name = "accounting"

urlpatterns = [
    path("dashboard/accounting/", views.LedgerView.as_view(), name="ledger"),
    path("dashboard/accounting/export/", views.LedgerExportView.as_view(), name="ledger_export"),
    path("dashboard/accounting/summary/", views.AccountingSummaryView.as_view(), name="summary"),
    path("dashboard/accounting/payouts/", views.PayoutRequestView.as_view(), name="payouts"),
]
