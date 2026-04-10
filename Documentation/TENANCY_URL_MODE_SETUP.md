# Django-Tenants URL Mode Setup

This project can run django-tenants in URL-path mode (no subdomain required).

## URL pattern

Storefront tenant resolution is based on this pattern:

`/s/<store_slug>/...`

Example:

`/s/my-store/products/`

## Environment flags

Set these values in `.env`:

```env
DATABASE_URL=postgres://user:password@host:5432/dbname
USE_DJANGO_TENANTS=True
TENANT_PATH_PREFIX=s
```

## What is configured

- `tenancy.Tenant` and `tenancy.Domain` models added.
- Middleware `tenancy.middleware.URLPathTenantMiddleware` resolves tenant from URL path.
- Tenant mode is optional and controlled by `USE_DJANGO_TENANTS`.
- If tenant mode is enabled, DB engine switches to `django_tenants.postgresql_backend`.

## Create tenant records

Run migrations first:

```powershell
python manage.py makemigrations tenancy
python manage.py migrate
```

Create tenant rows in Django admin or shell.

Minimal shell example:

```python
from tenancy.models import Tenant

Tenant.objects.create(
    schema_name="store_my_store",
    name="My Store",
    store_slug="my-store",
)
```

Then create at least one domain row (required by django-tenants model contract), even if routing is path-based:

```python
from tenancy.models import Tenant, Domain

t = Tenant.objects.get(store_slug="my-store")
Domain.objects.get_or_create(domain="placeholder.local", tenant=t, defaults={"is_primary": True})
```

## Important note

This is URL-based tenant routing with schema switching. It does not require wildcard subdomains.
