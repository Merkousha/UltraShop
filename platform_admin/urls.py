from django.urls import path
from platform_admin import views

app_name = "platform_admin"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("login/", views.PlatformLoginView.as_view(), name="login"),

    # PA-10: Platform settings
    path("settings/", views.PlatformSettingsView.as_view(), name="settings"),

    # PA-11: Default store settings
    path("settings/defaults/", views.DefaultStoreSettingsView.as_view(), name="default-settings"),

    # PA-12: Reserved usernames
    path("settings/reserved-usernames/", views.ReservedUsernamesView.as_view(), name="reserved-usernames"),

    # PA-15: SMS/Email config
    path("settings/providers/", views.ProviderConfigView.as_view(), name="provider-config"),
    path("settings/providers/test-sms/", views.TestSMSView.as_view(), name="test-sms"),
    path("settings/providers/test-email/", views.TestEmailView.as_view(), name="test-email"),

    # PA-13: AI config (Sprint 5)
    path("settings/ai/", views.AISettingsView.as_view(), name="ai-settings"),
    path("settings/ai/test/", views.TestAIView.as_view(), name="test-ai"),

    # PA-20: Shipping toggle
    path("shipping/toggle/", views.ShippingToggleView.as_view(), name="shipping-toggle"),

    # PA-22: All shipments
    path("shipments/", views.ShipmentListView.as_view(), name="shipment-list"),
    path("shipments/<int:pk>/", views.ShipmentDetailView.as_view(), name="shipment-detail"),

    # PA-23: Update shipment status
    path("shipments/<int:pk>/update-status/", views.ShipmentUpdateStatusView.as_view(), name="shipment-update-status"),

    # PA-30: Stores
    path("stores/", views.StoreListView.as_view(), name="store-list"),
    path("stores/<int:pk>/", views.StoreDetailView.as_view(), name="store-detail"),

    # PA-33: Payouts
    path("payouts/", views.PayoutListView.as_view(), name="payout-list"),

    # PA-34: Commission report
    path("commission/", views.CommissionReportView.as_view(), name="commission-report"),

    # PA-03: Audit log
    path("audit-log/", views.AuditLogView.as_view(), name="audit-log"),

    # PA-14: Theme Presets
    path("theme-presets/", views.ThemePresetListView.as_view(), name="theme-preset-list"),
    path("theme-presets/create/", views.ThemePresetCreateView.as_view(), name="theme-preset-create"),
    path("theme-presets/<int:pk>/edit/", views.ThemePresetEditView.as_view(), name="theme-preset-edit"),
    path("theme-presets/<int:pk>/deprecate/", views.ThemePresetDeprecateView.as_view(), name="theme-preset-deprecate"),

    # Plans
    path("plans/", views.PlanListView.as_view(), name="plan-list"),
    path("plans/create/", views.PlanCreateView.as_view(), name="plan-create"),
    path("plans/<int:pk>/edit/", views.PlanEditView.as_view(), name="plan-edit"),
]
