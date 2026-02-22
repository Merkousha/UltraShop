from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import TemplateView


def favicon_view(request):
    """Serve a minimal favicon to avoid 404 when browsers request /favicon.ico."""
    svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        b'<rect width="32" height="32" rx="6" fill="%236366f1"/>'
        b'<text x="16" y="22" text-anchor="middle" fill="white" font-size="18" font-weight="bold" font-family="sans-serif">U</text>'
        b"</svg>"
    )
    return HttpResponse(svg, content_type="image/svg+xml")


urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("favicon.ico", favicon_view),
    path("admin/", admin.site.urls),
    path("platform/", include("platform_admin.urls")),
    path("accounts/", include("core.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("s/<slug:store_username>/", include("storefront.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

