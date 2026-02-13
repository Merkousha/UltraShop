from django.urls import path, reverse_lazy
from django.views.generic import RedirectView
from . import views

app_name = "platform_admin"

urlpatterns = [
    path("", RedirectView.as_view(url=reverse_lazy("platform_admin:dashboard"), permanent=False), name="index"),
    path("login/", views.PlatformLoginView.as_view(), name="login"),
    path("dashboard/", views.PlatformDashboardView.as_view(), name="dashboard"),
    path("stores/", views.StoreListView.as_view(), name="store_list"),
    path("stores/<slug:username>/", views.StoreDetailView.as_view(), name="store_detail"),
    path("stores/<slug:username>/suspend/", views.StoreSuspendView.as_view(), name="store_suspend"),
    path("stores/<slug:username>/reactivate/", views.StoreReactivateView.as_view(), name="store_reactivate"),
    path("payouts/", views.PayoutRequestListView.as_view(), name="payout_list"),
    path("payouts/<int:pk>/approve/", views.PayoutApproveView.as_view(), name="payout_approve"),
    path("payouts/<int:pk>/reject/", views.PayoutRejectView.as_view(), name="payout_reject"),
    path("commission/", views.CommissionReportView.as_view(), name="commission_report"),
    path("audit-log/", views.AuditLogListView.as_view(), name="audit_log"),
    path("password-change/", views.PlatformPasswordChangeView.as_view(), name="password_change"),
    path("settings/", views.PlatformSettingsUpdateView.as_view(), name="platform_settings"),
    path("carriers/", views.ShippingCarrierListView.as_view(), name="carrier_list"),
    path("carriers/add/", views.ShippingCarrierCreateView.as_view(), name="carrier_create"),
    path("carriers/<int:pk>/edit/", views.ShippingCarrierUpdateView.as_view(), name="carrier_edit"),
    path("carriers/<int:pk>/delete/", views.ShippingCarrierDeleteView.as_view(), name="carrier_delete"),
]
