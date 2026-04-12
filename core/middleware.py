from django.http import HttpResponse
from django.conf import settings

from core.models import Store, StoreDomain


class CSPMiddleware:
    """
    Set Content-Security-Policy header. Custom CSS is injected as <style> (safe).
    Set CSP_ENABLED=False in settings to disable.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(settings, "CSP_ENABLED", True) and hasattr(response, "get"):
            csp = getattr(
                settings,
                "CSP_HEADER",
                "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; script-src 'self';",
            )
            response["Content-Security-Policy"] = csp
        return response


class ThemeCSPMiddleware:
    """
    Set Content-Security-Policy header specifically for HTML responses.
    Allows inline styles/scripts needed for dynamic theme rendering.
    """
    CSP_VALUE = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self';"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        content_type = response.get("Content-Type", "")
        if "text/html" in content_type:
            response["Content-Security-Policy"] = self.CSP_VALUE
        return response


class StoreMiddleware:
    """
    Resolve current store from subdomain or custom domain.
    Sets request.store (or None for platform URLs).
    """

    PLATFORM_PATHS = ("/platform/", "/admin/", "/accounts/", "/dashboard/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.store = None
        host = request.get_host().split(":")[0].lower()
        path = request.path

        # Skip store resolution for platform/admin paths
        if any(path.startswith(p) for p in self.PLATFORM_PATHS):
            return self.get_response(request)

        # Skip for static/media
        if path.startswith(("/static/", "/media/")):
            return self.get_response(request)

        platform_domain = getattr(settings, "PLATFORM_DOMAIN", "localhost:8000").split(":")[0]

        # Try subdomain
        if host.endswith(f".{platform_domain}"):
            subdomain = host.replace(f".{platform_domain}", "")
            store = Store.objects.filter(username=subdomain).first()
        elif host == platform_domain or host in ("localhost", "127.0.0.1"):
            # Platform root — no store context
            # If storefront URL, try to get store from URL pattern
            return self.get_response(request)
        else:
            # Custom domain lookup
            domain_obj = StoreDomain.objects.filter(
                domain=host, verified=True
            ).select_related("store").first()
            store = domain_obj.store if domain_obj else None

        if store and not store.is_active:
            return HttpResponse(
                "<h1>این فروشگاه در دسترس نیست</h1><p>فروشگاه موقتاً غیرفعال شده است.</p>",
                content_type="text/html; charset=utf-8",
                status=503,
            )

        request.store = store
        return self.get_response(request)
