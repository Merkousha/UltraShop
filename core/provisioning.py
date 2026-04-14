"""
Dynamic database schema provisioning for multi-tenant mode.

When USE_DJANGO_TENANTS=True (PostgreSQL + django_tenants), calling
provision_store_schema(store) will:
  1. Create a Tenant record linked to the Store's username as schema_name.
  2. django_tenants auto-creates the PostgreSQL schema on Tenant.save().
  3. Runs tenant-aware migrations on the new schema.

When USE_DJANGO_TENANTS=False (SQLite or shared-schema mode) this is a no-op.
"""

import logging

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


def provision_store_schema(store):
    """
    Provision a dedicated database schema for the given store.

    In USE_DJANGO_TENANTS=True mode: creates Tenant + Domain records and
    triggers django_tenants schema auto-creation + migration.

    In USE_DJANGO_TENANTS=False mode: logs a debug message and returns None.

    Returns the Tenant instance (or None in no-op mode).
    Raises RuntimeError if provisioning fails so callers can handle gracefully.
    """
    if not getattr(settings, "USE_DJANGO_TENANTS", False):
        logger.debug("USE_DJANGO_TENANTS=False — skipping DB provisioning for store %s", store.pk)
        return None

    try:
        from tenancy.models import Domain, Tenant

        schema_name = _safe_schema_name(store.username)

        # Idempotent: don't re-provision if schema already exists
        tenant = Tenant.objects.filter(schema_name=schema_name).first()
        if tenant:
            logger.info("Schema already exists for store %s (schema=%s)", store.pk, schema_name)
            return tenant

        # Create the Tenant — django_tenants will auto-create the schema on save()
        tenant = Tenant(
            schema_name=schema_name,
            name=store.name,
            store_slug=store.username,
            is_active=True,
        )
        tenant.save()  # triggers auto_create_schema

        # Create a required Domain record (django_tenants needs at least one)
        platform_domain = getattr(settings, "PLATFORM_DOMAIN", "localhost")
        domain = f"{store.username}.{platform_domain}"
        Domain.objects.get_or_create(
            tenant=tenant,
            defaults={"domain": domain, "is_primary": True},
        )

        logger.info(
            "Provisioned schema '%s' for store pk=%s (domain=%s)",
            schema_name,
            store.pk,
            domain,
        )
        return tenant

    except Exception as exc:
        logger.exception("Failed to provision schema for store %s: %s", store.pk, exc)
        raise RuntimeError(f"Schema provisioning failed: {exc}") from exc


def sync_store_tenant_slug(store, old_username: str):
    """Sync an existing tenant's store_slug after a Store.username change.

    This keeps the existing schema_name intact and only updates the lookup key
    used by URLPathTenantMiddleware. If a duplicate tenant exists for the new
    username (created by older buggy behavior), remove that duplicate first so
    the original tenant can safely claim the new slug.
    """
    if not getattr(settings, "USE_DJANGO_TENANTS", False):
        return None

    old_username = (old_username or "").strip()
    if not old_username or old_username == store.username:
        return None

    try:
        from tenancy.models import Tenant

        with transaction.atomic():
            source_tenant = Tenant.objects.filter(store_slug=old_username, is_active=True).first()
            if not source_tenant:
                logger.warning(
                    "No tenant found for old store slug '%s' while syncing store %s",
                    old_username,
                    store.pk,
                )
                return None

            conflicting_tenant = Tenant.objects.filter(store_slug=store.username, is_active=True).first()
            if conflicting_tenant and conflicting_tenant.pk != source_tenant.pk:
                logger.warning(
                    "Removing conflicting tenant '%s' before renaming tenant '%s' to '%s'",
                    conflicting_tenant.schema_name,
                    source_tenant.schema_name,
                    store.username,
                )
                conflicting_tenant.delete()

            source_tenant.store_slug = store.username
            source_tenant.save(update_fields=["store_slug"])
            logger.info(
                "Synced tenant slug for store %s: %s -> %s",
                store.pk,
                old_username,
                store.username,
            )
            return source_tenant
    except Exception as exc:
        logger.exception("Failed to sync tenant slug for store %s: %s", store.pk, exc)
        raise RuntimeError(f"Tenant slug sync failed: {exc}") from exc


def _safe_schema_name(store_username: str) -> str:
    """
    Convert a store username into a safe PostgreSQL schema name.
    Replaces hyphens with underscores; prepends 'store_' prefix to avoid
    clashing with built-in PostgreSQL schema names.
    """
    safe = store_username.lower().replace("-", "_").replace(" ", "_")
    # Avoid reserved names
    if safe in {"public", "pg_catalog", "information_schema"}:
        safe = f"shop_{safe}"
    return f"store_{safe}"
