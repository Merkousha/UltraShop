def current_store(request):
    """Expose current store in template context."""
    return {"store": getattr(request, "store", None)}
