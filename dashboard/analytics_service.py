"""
BI Dashboard Analytics Service (Phase 4).

Provides get_store_analytics(store, days=30) returning a dict with:
  - ltv              : Customer Lifetime Value (IRR, integer)
  - cac              : Customer Acquisition Cost (IRR, integer)
                       Computed as: total expense transactions / new customers acquired.
                       Returns 0 when no new customers or no expense data.
  - new_customers    : Number of first-time paying customers in the period
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
    Returns a dict with LTV, CAC, new_customers, conversion_rate,
    revenue_trend (list), and top_products (list).

    All monetary values are in IRR (integer).
    """
    now = timezone.now()
    period_start = now - timedelta(days=days)

    # ── Paid orders (all time, for LTV/CAC) ─────────────────────────────
    paid_qs = Order.objects.filter(store=store, status__in=PAID_STATUSES)

    # ── LTV: avg order value × avg orders per unique customer ────────────
    ltv = _compute_ltv(paid_qs)

    # ── New customers acquired in this period ────────────────────────────
    new_customers = _compute_new_customers(store, period_start)

    # ── CAC: total expense transactions in period / new customers ────────
    cac = _compute_cac(store, period_start, new_customers)

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
        "new_customers": new_customers,
        "conversion_rate": conversion_rate,
        "revenue_trend": revenue_trend,
        "top_products": top_products,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _compute_ltv(paid_qs):
    """Average order value × average orders per paying customer (IRR, int)."""
    orders = list(paid_qs.prefetch_related("lines"))
    if not orders:
        return 0

    order_totals = [o.total for o in orders]
    avg_order_value = sum(order_totals) / len(order_totals)

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
        avg_orders_per_customer = 1

    return int(avg_order_value * avg_orders_per_customer)


def _compute_new_customers(store, period_start):
    """
    Count customers whose first paid order is within the given period.
    These are newly acquired customers.
    """
    # Find all paying customers (ever)
    paying_customers = (
        Order.objects.filter(store=store, status__in=PAID_STATUSES, customer__isnull=False)
        .values("customer")
        .annotate(first_order=Count("id"))  # we only need the group, not count
    )

    # Among those, find ones whose earliest paid order falls in the period
    new_customer_count = (
        Order.objects.filter(
            store=store,
            status__in=PAID_STATUSES,
            customer__isnull=False,
            created_at__gte=period_start,
        )
        .values("customer")
        .annotate(earliest=Count("id"))
        .count()
    )

    # Subtract customers who also had a paid order *before* the period
    returning_customers = (
        Order.objects.filter(
            store=store,
            status__in=PAID_STATUSES,
            customer__isnull=False,
            created_at__lt=period_start,
        )
        .values_list("customer", flat=True)
        .distinct()
    )

    first_time = (
        Order.objects.filter(
            store=store,
            status__in=PAID_STATUSES,
            customer__isnull=False,
            created_at__gte=period_start,
        )
        .exclude(customer__in=returning_customers)
        .values("customer")
        .distinct()
        .count()
    )

    return first_time


def _compute_cac(store, period_start, new_customers: int) -> int:
    """
    Customer Acquisition Cost = total marketing/expense spend in the period
    divided by new customers acquired.

    Uses StoreTransaction records of type EXPENSE as a proxy for marketing spend.
    Returns 0 when there are no expense transactions or no new customers.
    """
    if new_customers == 0:
        return 0

    from accounting.models import StoreTransaction

    expense_total = (
        StoreTransaction.objects.filter(
            store=store,
            type=StoreTransaction.Type.EXPENSE,
            created_at__gte=period_start,
        )
        .aggregate(total=Sum("amount"))
        .get("total")
    ) or 0

    # Expenses are stored as negative debits; take absolute value
    expense_total = abs(expense_total)
    if expense_total == 0:
        return 0

    return int(expense_total / new_customers)


def _compute_revenue_trend(store, days, now, period_start):
    """
    Return list of {date: str, revenue: int} for each of the last `days` days.
    """
    paid_in_period = list(
        Order.objects.filter(
            store=store,
            status__in=PAID_STATUSES,
            created_at__gte=period_start,
        ).prefetch_related("lines")
    )

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

