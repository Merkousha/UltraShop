def current_customer(request):
    """Expose current customer in template context (storefront)."""
    return {"customer": getattr(request, "customer", None)}
