"""
URL configuration for UltraShop. Root domain vs store subdomain routing
is handled in each app's urls; middleware sets request.store.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("platform/admin/", admin.site.urls),
    path("platform/", include("platform_admin.urls")),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("", include("catalog.urls")),
    path("", include("orders.urls")),
    path("", include("payments.urls")),
    path("", include("accounting.urls")),
    path("", include("shipping.urls")),
    path("", include("stores.urls")),
    path("", include("customers.urls")),
]
if settings.MEDIA_URL and getattr(settings, "MEDIA_ROOT", None):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
