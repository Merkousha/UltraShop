from core.models import PlatformSettings


def platform_settings(request):
    try:
        ps = PlatformSettings.load()
    except Exception:
        ps = None
    return {"platform_settings": ps}
