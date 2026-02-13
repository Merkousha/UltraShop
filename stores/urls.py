from django.urls import path
from . import views

app_name = "stores"

urlpatterns = [
    path("stores/create/", views.CreateStoreView.as_view(), name="create"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("dashboard/settings/", views.SettingsView.as_view(), name="settings"),
    path("dashboard/settings/domains/", views.DomainSettingsView.as_view(), name="domain_settings"),
    path("dashboard/settings/domains/<int:domain_id>/verify/", views.VerifyDomainView.as_view(), name="verify_domain"),
    path("dashboard/settings/domains/<int:domain_id>/primary/", views.SetPrimaryDomainView.as_view(), name="set_primary_domain"),
    path("dashboard/settings/branding/", views.BrandingSettingsView.as_view(), name="branding_settings"),
    path("dashboard/settings/staff/", views.StaffListView.as_view(), name="staff_list"),
    path("dashboard/settings/staff/add/", views.AddStaffView.as_view(), name="add_staff"),
    path("dashboard/settings/staff/<int:user_id>/remove/", views.RemoveStaffView.as_view(), name="remove_staff"),
]
