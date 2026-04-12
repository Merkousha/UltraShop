"""
Inventory Forecast Service (SO-53).
"""
from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone


def get_inventory_forecast(store, warehouse=None):
    """
    Returns a list of dicts for each active variant with forecast data.
    """
    from catalog.models import ProductVariant, WarehouseStock
    from orders.models import OrderLine

    now = timezone.now()
    period_start = now - timedelta(days=90)

    PAID_STATUSES = ["paid", "packed", "shipped", "delivered"]

    # Get all active variants for this store
    variants_qs = ProductVariant.objects.filter(
        product__store=store, product__status="active"
    ).select_related("product")

    results = []
    for variant in variants_qs:
        # Current stock (from WarehouseStock if available, otherwise variant.stock)
        try:
            wh_stocks = WarehouseStock.objects.filter(
                variant=variant, warehouse__store=store
            )
            if warehouse:
                wh_stocks = wh_stocks.filter(warehouse=warehouse)
            current_stock = wh_stocks.aggregate(t=Sum("quantity"))["t"] or 0
        except Exception:
            current_stock = variant.stock

        if current_stock == 0 and variant.stock == 0:
            continue  # Skip out-of-stock

        # Average daily sales in last 90 days
        total_sold = OrderLine.objects.filter(
            order__store=store,
            order__status__in=PAID_STATUSES,
            order__created_at__gte=period_start,
            variant=variant,
        ).aggregate(t=Sum("quantity"))["t"] or 0

        avg_daily = round(total_sold / 90, 2) if total_sold > 0 else 0

        # Days until stockout
        if avg_daily > 0 and current_stock > 0:
            days_until_stockout = int(current_stock / avg_daily)
        elif current_stock > 0:
            days_until_stockout = 999  # 999 = effectively infinite
        else:
            days_until_stockout = 0

        # Suggested reorder quantity (30-day supply)
        suggested_reorder = max(0, int(avg_daily * 30) - current_stock) if avg_daily > 0 else 0

        # Urgency
        if days_until_stockout <= 7:
            urgency = "critical"
            urgency_label = "🔴 بحرانی"
        elif days_until_stockout <= 30:
            urgency = "warning"
            urgency_label = "🟡 هشدار"
        else:
            urgency = "ok"
            urgency_label = "🟢 خوب"

        results.append({
            "variant": variant,
            "product_name": variant.product.name,
            "variant_name": variant.name,
            "current_stock": current_stock,
            "avg_daily_sales": avg_daily,
            "days_until_stockout": days_until_stockout if days_until_stockout < 999 else None,
            "suggested_reorder": suggested_reorder,
            "urgency": urgency,
            "urgency_label": urgency_label,
        })

    # Sort by days_until_stockout ascending (critical first), None last
    results.sort(key=lambda x: x["days_until_stockout"] if x["days_until_stockout"] is not None else 9999)
    return results
