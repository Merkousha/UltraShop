from django.conf import settings
from django.db import connection
from django.http import HttpResponseNotFound

from .models import Tenant


class URLPathTenantMiddleware:
    """
    Resolve tenant from URL prefix: /<TENANT_PATH_PREFIX>/<store_slug>/...
    Example default: /s/my-store/
    """

    PLATFORM_PATHS = ("/platform/", "/admin/", "/accounts/", "/dashboard/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        prefix = f"/{getattr(settings, 'TENANT_PATH_PREFIX', 's').strip('/')}/"

        request.tenant = None

        # Platform and static/media paths stay on public schema.
        if any(path.startswith(p) for p in self.PLATFORM_PATHS) or path.startswith(("/static/", "/media/")):
            connection.set_schema_to_public()
            return self.get_response(request)

        # Storefront path-based tenant mode.
        if path.startswith(prefix):
            remainder = path[len(prefix):]
            store_slug = remainder.split("/", 1)[0].strip()
            if not store_slug:
                connection.set_schema_to_public()
                return HttpResponseNotFound("Store identifier is missing in URL.")

            tenant = Tenant.objects.filter(store_slug=store_slug, is_active=True).first()
            if not tenant:
                connection.set_schema_to_public()
                return HttpResponseNotFound("Store not found.")

            request.tenant = tenant
            connection.set_tenant(tenant)
        else:
            connection.set_schema_to_public()

        try:
            return self.get_response(request)
        finally:
            # Avoid schema leakage across requests in persistent workers.
            connection.set_schema_to_public()
