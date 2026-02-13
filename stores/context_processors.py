def current_store(request):
    """Expose current store and path prefix (for /store/username/ links) in template context."""
    return {
        "store": getattr(request, "store", None),
        "store_path_prefix": getattr(request, "store_path_prefix", "") or "",
    }
