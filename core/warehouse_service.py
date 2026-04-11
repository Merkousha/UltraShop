"""Warehouse helpers (Sprint 4 — SO-50, SO-51)."""

from .models import Warehouse


# Default fallback when no plan is assigned
_DEFAULT_MAX_WAREHOUSES = 5
_DEFAULT_MAX_PRODUCTS = 100


def get_max_warehouses_for_store(store) -> int:
    """Return warehouse limit from the store's plan, or fallback default."""
    if store.plan_id and store.plan:
        return store.plan.max_warehouses
    return _DEFAULT_MAX_WAREHOUSES


def get_max_products_for_store(store) -> int:
    """Return product limit from the store's plan, or fallback default."""
    if store.plan_id and store.plan:
        return store.plan.max_products
    return _DEFAULT_MAX_PRODUCTS


# Keep legacy constant for backward compatibility (used in existing views)
MAX_WAREHOUSES_PER_STORE = _DEFAULT_MAX_WAREHOUSES


def get_default_warehouse(store):
    """Return the default warehouse for the store (is_default=True or first)."""
    return (
        Warehouse.objects.filter(store=store, is_active=True)
        .order_by("-is_default", "priority", "pk")
        .first()
    )


def set_default_warehouse_quantity(store, variant, quantity):
    """Set quantity for variant in store's default warehouse; sync variant.stock to total (backward compat)."""
    from catalog.models import WarehouseStock
    from django.db.models import Sum

    default_wh = get_default_warehouse(store)
    if not default_wh:
        return
    quantity = max(0, int(quantity))
    ws, _ = WarehouseStock.objects.get_or_create(
        warehouse=default_wh, variant=variant, defaults={"quantity": 0}
    )
    ws.quantity = quantity
    ws.save(update_fields=["quantity"])
    # Keep variant.stock in sync with sum of warehouse stocks
    agg = variant.warehouse_stocks.aggregate(s=Sum("quantity"), r=Sum("reserved"))
    total = max(0, (agg["s"] or 0) - (agg["r"] or 0))
    if variant.stock != total:
        variant.stock = total
        variant.save(update_fields=["stock"])


def get_warehouses_for_user(store, user):
    """Warehouses the user can manage (owner: all; staff with empty warehouses: all; staff with warehouses: only those)."""
    if store.owner_id == user.id:
        return Warehouse.objects.filter(store=store)
    staff = store.staff_members.filter(user=user).first()
    if not staff:
        return Warehouse.objects.none()
    if not staff.warehouses.exists():
        return Warehouse.objects.filter(store=store)
    return staff.warehouses.all()
