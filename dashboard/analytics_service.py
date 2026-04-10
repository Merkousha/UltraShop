"""
BI Dashboard Analytics Service (Phase 4).

Provides get_store_analytics(store, days=30) returning a dict with:
  - ltv              : Customer Lifetime Value (IRR, integer)
  - cac              : Customer Acquisition Cost (None — needs ad spend data)
  - conversion_rate  : (paid orders / total orders) × 100  [%]
  - revenue_trend    : list of {date, revenue} for last `days` days
  - top_products     : top 5 products by units sold
"""

from datetime import timedelta

from django.db.models import Count, ExpressionWrapper, F, Sum, fields
from django.utils import timezone

from orders.models import Order, OrderLine


# Statuses that represent a completed/paying transaction
PAID_STATUSES = [
    Order.Status.PAID,
    Order.Status.PACKED,
    Order.Status.SHIPPED,
    Order.Status.DELIVERED,
]


def get_store_analytics(store, days=30):
    """
    Returns a dict with LTV, CAC (placeholder), conversion_rate,
    revenue_trend (list), and top_products (list).

    All monetary values are in IRR (integer).
    """
    now = timezone.now()
    period_start = now - timedelta(days=days)

    # ── Paid orders (all time, for LTV/CAC) ─────────────────────────────
    paid_qs = Order.objects.filter(store=store, status__in=PAID_STATUSES)

    # ── LTV: avg order value × avg orders per unique customer ────────────
    ltv = _compute_ltv(paid_qs)

    # ── CAC: placeholder (needs advertising spend data) ──────────────────
    cac = None

    # ── Conversion rate: paid orders / total orders (× 100) ─────────────
    total_orders = Order.objects.filter(store=store).count()
    paid_orders_count = paid_qs.count()
    conversion_rate = (
        round(paid_orders_count / total_orders * 100, 1) if total_orders > 0 else 0.0
    )

    # ── Revenue trend: {date, revenue} per day for the last `days` days ──
    revenue_trend = _compute_revenue_trend(store, days, now, period_start)

    # ── Top 5 products by units sold (paid orders) ───────────────────────
    top_products = _compute_top_products(paid_qs)

    return {
        "ltv": ltv,
        "cac": cac,
        "conversion_rate": conversion_rate,
        "revenue_trend": revenue_trend,
        "top_products": top_products,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _compute_ltv(paid_qs):
    """Average order value × average orders per paying customer (IRR, int)."""
    # Fetch just the orders we need to compute totals for
    orders = list(paid_qs.prefetch_related("lines"))
    if not orders:
        return 0

    # Average order value
    order_totals = [o.total for o in orders]
    avg_order_value = sum(order_totals) / len(order_totals)

    # Average orders per customer (only customers with a linked Customer FK)
    customer_counts = (
        paid_qs.filter(customer__isnull=False)
        .values("customer")
        .annotate(cnt=Count("id"))
    )
    if customer_counts.exists():
        total_customer_orders = sum(c["cnt"] for c in customer_counts)
        num_unique_customers = customer_counts.count()
        avg_orders_per_customer = total_customer_orders / num_unique_customers
    else:
        # No identified customers yet — assume each order = 1 customer
        avg_orders_per_customer = 1

    return int(avg_order_value * avg_orders_per_customer)


def _compute_revenue_trend(store, days, now, period_start):
    """
    Return list of {date: str, revenue: int} for each of the last `days` days.

    Fetches all paid orders in the period once, then groups them in Python to
    avoid N+1 queries.
    """
    paid_in_period = list(
        Order.objects.filter(
            store=store,
            status__in=PAID_STATUSES,
            created_at__gte=period_start,
        ).prefetch_related("lines")
    )

    # Build a map: date_str -> total revenue
    revenue_map = {}
    for order in paid_in_period:
        date_str = order.created_at.date().isoformat()
        revenue_map[date_str] = revenue_map.get(date_str, 0) + order.total

    trend = []
    for i in range(days - 1, -1, -1):
        day = (now - timedelta(days=i)).date()
        date_str = day.isoformat()
        trend.append({"date": date_str, "revenue": revenue_map.get(date_str, 0)})

    return trend


def _compute_top_products(paid_qs):
    """
    Top 5 products by total units sold in paid orders.
    Returns list of dicts with keys: product_name, total_qty, total_revenue.
    """
    line_expr = ExpressionWrapper(
        F("quantity") * F("unit_price"),
        output_field=fields.BigIntegerField(),
    )

    top = (
        OrderLine.objects.filter(order__in=paid_qs)
        .values("product_name")
        .annotate(
            total_qty=Sum("quantity"),
            total_revenue=Sum(line_expr),
        )
        .order_by("-total_qty")[:5]
    )
    return list(top)
