"""
Resolve current store from request host or from path (helpio.ir/store/username/).
- host = username.platform_domain -> request.store (subdomain)
- host = platform_domain or localhost + path /store/username/ -> request.store (path-based)
- If store is inactive, return "store unavailable" page.
"""
from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from .models import Store


def _is_platform_root(host, root_domain):
    return host == root_domain or host == ("www." + root_domain) or host in ("localhost", "127.0.0.1")


def _path_based_store_prefix(username):
    return f"/store/{username}"


class StoreMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.root_domain = getattr(settings, "PLATFORM_ROOT_DOMAIN", "ultrashop.local")
        self.sep = getattr(settings, "STORE_SUBDOMAIN_SEPARATOR", ".")
        self.use_path_based = getattr(settings, "PLATFORM_USE_PATH_BASED_STORE_URLS", False)

    def __call__(self, request):
        request.store = None
        request.store_from_path = False
        request.store_path_prefix = ""
        host = request.get_host().split(":")[0].lower()
        path_info = request.path_info

        # Platform root: resolve store from path /store/<username>/ when enabled
        if self.use_path_based and _is_platform_root(host, self.root_domain):
            if path_info.startswith("/store/"):
                parts = path_info.strip("/").split("/")
                if len(parts) >= 2 and parts[0] == "store":
                    username = parts[1]
                    remainder = "/" + "/".join(parts[2:]) if len(parts) > 2 else "/"
                    if not remainder.endswith("/") and remainder != "/":
                        remainder = remainder + "/"
                    try:
                        store = Store.objects.get(username=username)
                        if not store.is_active:
                            return HttpResponse(
                                loader.render_to_string("core/store_unavailable.html", {"store": store}, request)
                            )
                        request.store = store
                        request.store_from_path = True
                        request.store_path_prefix = _path_based_store_prefix(username)
                        request.path_info = remainder
                        request.path = request.path.replace(f"/store/{username}", "", 1) or "/"
                        if not request.path.startswith("/"):
                            request.path = "/" + request.path
                    except Store.DoesNotExist:
                        pass  # leave path as-is; URL resolver will 404
            return self.get_response(request)

        # Platform root (no path-based): no store
        if _is_platform_root(host, self.root_domain):
            return self.get_response(request)

        # subdomain.root_domain (e.g. mystore.ultrashop.local); skip www
        suffix = "." + self.root_domain
        if host.endswith(suffix):
            subdomain = host[: -len(suffix)].split(".")[-1]
            if subdomain and subdomain != "www":
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
