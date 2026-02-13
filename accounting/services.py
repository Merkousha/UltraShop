"""Post accounting entries when order is paid, refunded, or payout approved."""
from decimal import Decimal
from django.db import transaction as db_transaction


def get_store_balance(store):
    """Current balance = sum of all transaction amounts (positive = credit)."""
    from django.db.models import Sum
    from .models import StoreTransaction
    result = StoreTransaction.objects.filter(store=store).aggregate(total=Sum("amount"))
    return result["total"] or Decimal("0")


def post_order_paid(order):
    """When order is paid: credit store (revenue) and optionally deduct platform commission."""
    from django.conf import settings
    from .models import StoreTransaction, PlatformCommission
    if order.total <= 0:
        return
    rate = getattr(settings, "PLATFORM_COMMISSION_RATE", 0)
    try:
        rate = float(rate)
    except (TypeError, ValueError):
        rate = 0
    commission = (order.total * rate) if rate > 0 else 0
    with db_transaction.atomic():
        StoreTransaction.objects.create(
            store=order.store,
            amount=order.total,
            description=f"سفارش #{order.pk} پرداخت شد",
            order=order,
        )
        if commission > 0:
            StoreTransaction.objects.create(
                store=order.store,
                amount=-commission,
                description=f"کمیسیون پلتفرم سفارش #{order.pk}",
                order=order,
            )
            PlatformCommission.objects.create(
                store=order.store,
                order=order,
                amount=commission,
            )


def post_order_refunded(order, amount=None, reason=None):
    """When order (or partial) is refunded: debit store."""
    from .models import StoreTransaction
    amt = amount or order.total
    if amt <= 0:
        return
    desc = f"بازپرداخت سفارش #{order.pk}"
    if reason and reason.strip():
        desc += f" — {reason.strip()}"
    with db_transaction.atomic():
        StoreTransaction.objects.create(
            store=order.store,
            amount=-amt,
            description=desc,
            order=order,
        )


def post_payout_approved(payout_request):
    """When platform approves payout: debit store."""
    from .models import StoreTransaction
    with db_transaction.atomic():
        StoreTransaction.objects.create(
            store=payout_request.store,
            amount=-payout_request.amount,
            description=f"تسویه #{payout_request.pk}",
            payout_request=payout_request,
        )
