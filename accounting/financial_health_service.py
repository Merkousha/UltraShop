"""
Financial Health Service (SO-35).
Provides get_financial_health(store, days=30) returning a dict with
revenue, expenses, profit, trend data, top products, and low-stock alerts.
"""
from datetime import timedelta

from django.db.models import F, Sum
from django.utils import timezone


def get_financial_health(store, days=30):
    """
    Returns financial health metrics for the given store over the last `days` days.

    Keys returned:
        revenue, prev_revenue, commission, total_expense, net_profit,
        profit_margin, growth, revenue_trend, expense_by_category,
        top_products, low_stock, alerts, days
    """
    from accounting.models import Expense, StoreTransaction
    from catalog.models import ProductVariant
    from orders.models import OrderLine

    now = timezone.now()
    period_start = now - timedelta(days=days)
    prev_start = now - timedelta(days=days * 2)

    PAID_STATUSES = ["paid", "packed", "shipped", "delivered"]

    # ── Revenue (current period) ─────────────────────────────────────────────
    revenue = (
        StoreTransaction.objects.filter(
            store=store, type="revenue", created_at__gte=period_start
        ).aggregate(t=Sum("amount"))["t"]
        or 0
    )

    # ── Revenue (previous period for growth calc) ────────────────────────────
    prev_revenue = (
        StoreTransaction.objects.filter(
            store=store,
            type="revenue",
            created_at__gte=prev_start,
            created_at__lt=period_start,
        ).aggregate(t=Sum("amount"))["t"]
        or 0
    )

    # ── Platform commission deducted ─────────────────────────────────────────
    commission = abs(
        StoreTransaction.objects.filter(
            store=store, type="commission", created_at__gte=period_start
        ).aggregate(t=Sum("amount"))["t"]
        or 0
    )

    # ── Expenses (from Expense model, SO-34) ──────────────────────────────────
    total_expense = (
        Expense.objects.filter(
            store=store, date__gte=period_start.date()
        ).aggregate(t=Sum("amount"))["t"]
        or 0
    )

    # ── Net profit & margin ───────────────────────────────────────────────────
    net_profit = revenue - commission - total_expense
    profit_margin = round((net_profit / revenue * 100), 1) if revenue > 0 else 0

    # ── Revenue growth % vs previous period ──────────────────────────────────
    growth = 0
    if prev_revenue > 0:
        growth = round((revenue - prev_revenue) / prev_revenue * 100, 1)

    # ── Monthly revenue trend (last 6 months) ────────────────────────────────
    revenue_trend = []
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if i == 0:
            month_end = now
        else:
            month_end = (now - timedelta(days=30 * (i - 1))).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

        rev = (
            StoreTransaction.objects.filter(
                store=store,
                type="revenue",
                created_at__gte=month_start,
                created_at__lt=month_end,
            ).aggregate(t=Sum("amount"))["t"]
            or 0
        )

        revenue_trend.append(
            {
                "label": month_start.strftime("%Y/%m"),
                "revenue": rev,
            }
        )

    # ── Expense breakdown by category ─────────────────────────────────────────
    category_map = dict(Expense.Category.choices)
    raw_expense_by_category = list(
        Expense.objects.filter(store=store, date__gte=period_start.date())
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    # Enrich each row with a human-readable category label
    expense_by_category = [
        {
            **item,
            "category_display": category_map.get(item["category"], item["category"]),
        }
        for item in raw_expense_by_category
    ]

    # ── Top 5 products by units sold ─────────────────────────────────────────
    # line_total is a property (not a DB field), so we compute quantity*unit_price
    top_products = list(
        OrderLine.objects.filter(
            order__store=store,
            order__status__in=PAID_STATUSES,
            order__created_at__gte=period_start,
        )
        .values("product_name")
        .annotate(
            total_units=Sum("quantity"),
            total_revenue=Sum(F("quantity") * F("unit_price")),
        )
        .order_by("-total_units")[:5]
    )

    # ── Low stock variants (stock < 5, active products) ───────────────────────
    low_stock = list(
        ProductVariant.objects.filter(
            product__store=store,
            product__status="active",
            stock__lt=5,
        ).select_related("product")[:10]
    )

    # ── Alerts ────────────────────────────────────────────────────────────────
    alerts = []
    if profit_margin < 10 and revenue > 0:
        alerts.append(
            {
                "type": "warning",
                "message": "حاشیه سود کمتر از ۱۰٪ است — بررسی هزینه‌ها توصیه می‌شود.",
            }
        )
    if growth < 0:
        alerts.append(
            {
                "type": "danger",
                "message": f"روند فروش نزولی است ({growth:+.1f}٪ نسبت به دوره قبل).",
            }
        )
    if low_stock:
        alerts.append(
            {
                "type": "info",
                "message": f"{len(low_stock)} محصول با موجودی کم شناسایی شد.",
            }
        )

    return {
        "revenue": revenue,
        "prev_revenue": prev_revenue,
        "commission": commission,
        "total_expense": total_expense,
        "net_profit": net_profit,
        "profit_margin": profit_margin,
        "growth": growth,
        "revenue_trend": revenue_trend,
        "expense_by_category": expense_by_category,
        "top_products": top_products,
        "low_stock": low_stock,
        "alerts": alerts,
        "days": days,
    }
