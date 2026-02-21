from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("platform/", include("platform_admin.urls")),
    path("accounts/", include("core.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("s/<slug:store_username>/", include("storefront.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

