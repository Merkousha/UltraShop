from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    """
    URL-based tenant entry for django-tenants.
    We map /s/<store_slug>/... to a tenant schema using this store_slug.
    """

    name = models.CharField(max_length=200)
    store_slug = models.SlugField(max_length=60, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    auto_create_schema = True

    class Meta:
        db_table = "tenants"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
    """
    Required by django-tenants settings. Not used for routing in URL-path mode.
    """

    class Meta:
        db_table = "tenant_domains"
