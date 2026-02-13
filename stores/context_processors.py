def current_store(request):
    """Expose current store, path prefix, and platform domain for template context."""
    from django.conf import settings
    return {
        "store": getattr(request, "store", None),
        "store_path_prefix": getattr(request, "store_path_prefix", "") or "",
        "platform_root_domain": getattr(settings, "PLATFORM_ROOT_DOMAIN", "ultrashop.local"),
        "use_path_based_store_urls": getattr(settings, "PLATFORM_USE_PATH_BASED_STORE_URLS", False),
    }
