"""Context processors for core app."""
def platform_settings(request):
    """Expose platform settings to templates (e.g. name, support email, legal URLs)."""
    try:
        from .models import PlatformSettings
        return {"platform_settings": PlatformSettings.get_settings()}
    except Exception:
        return {"platform_settings": None}
