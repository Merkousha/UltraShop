"""
Resolve current store from request host.
- host = username.platform_domain (e.g. mystore.ultrashop.local) -> request.store
- host = platform_domain or localhost -> request.store = None (platform: home, login, signup)
- If store is inactive, return "store unavailable" page.
"""
from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from .models import Store


class StoreMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.root_domain = getattr(settings, "PLATFORM_ROOT_DOMAIN", "ultrashop.local")
        self.sep = getattr(settings, "STORE_SUBDOMAIN_SEPARATOR", ".")

    def __call__(self, request):
        request.store = None
        host = request.get_host().split(":")[0].lower()

        # Platform root: no store
        if host == self.root_domain or host in ("localhost", "127.0.0.1"):
            return self.get_response(request)

        # subdomain.root_domain (e.g. mystore.ultrashop.local)
        suffix = "." + self.root_domain
        if host.endswith(suffix):
            subdomain = host[: -len(suffix)].split(".")[-1]
            if subdomain:
                try:
                    request.store = Store.objects.get(username=subdomain)
                except Store.DoesNotExist:
                    pass
            if getattr(request, "store", None) and not request.store.is_active:
                return HttpResponse(loader.render_to_string("core/store_unavailable.html", {"store": request.store}, request))
            return self.get_response(request)

        # mystore.localhost (development only)
        if host.endswith(".localhost"):
            subdomain = host.split(".")[0]
            if subdomain:
                try:
                    request.store = Store.objects.get(username=subdomain)
                except Store.DoesNotExist:
                    pass
            if getattr(request, "store", None) and not request.store.is_active:
                return HttpResponse(loader.render_to_string("core/store_unavailable.html", {"store": request.store}, request))
            return self.get_response(request)

        # Custom domain: host matches a verified StoreDomain
        from .models import StoreDomain
        custom = StoreDomain.objects.filter(domain=host, verified=True).select_related("store").first()
        if custom:
            request.store = custom.store
        if getattr(request, "store", None) and not request.store.is_active:
            return HttpResponse(loader.render_to_string("core/store_unavailable.html", {"store": request.store}, request))
        return self.get_response(request)
