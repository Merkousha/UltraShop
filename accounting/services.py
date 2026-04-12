from django.conf import settings

from accounting.models import StoreTransaction, PlatformCommission


def get_store_balance(store):
    from django.db.models import Sum
    result = store.transactions.aggregate(total=Sum("amount"))
    return result["total"] or 0


def post_order_paid(order):
    total = order.total
    commission_rate = getattr(settings, "PLATFORM_COMMISSION_RATE", 0.05)
    commission_amount = int(total * commission_rate)
    net_amount = total - commission_amount

    StoreTransaction.objects.create(
        store=order.store,
        amount=net_amount,
        type=StoreTransaction.Type.REVENUE,
        description=f"فروش سفارش #{order.pk}",
        order=order,
    )

    if commission_amount > 0:
        StoreTransaction.objects.create(
            store=order.store,
            amount=-commission_amount,
            type=StoreTransaction.Type.COMMISSION,
            description=f"کمیسیون پلتفرم سفارش #{order.pk}",
            order=order,
        )
        PlatformCommission.objects.create(
            store=order.store,
            order=order,
            amount=commission_amount,
        )

    # ── CRM: record payment activity on the customer profile ─────────
    try:
        from crm.models import ContactActivity
        from customers.models import Customer

        customer = None
        phone = getattr(order, "guest_phone", "") or ""
        if phone:
            customer = Customer.objects.filter(store=order.store, phone=phone).first()

        ContactActivity.objects.get_or_create(
            store=order.store,
            activity_type=ContactActivity.ActivityType.ORDER,
            reference_id=str(order.pk),
            defaults={
                "customer": customer,
                "description": f"پرداخت سفارش #{order.pk} به مبلغ {order.total:,} ریال تأیید شد.",
            },
        )
    except Exception:
        pass


def post_order_refunded(order, amount, reason=""):
    StoreTransaction.objects.create(
        store=order.store,
        amount=-amount,
        type=StoreTransaction.Type.REFUND,
        description=f"بازگشت وجه سفارش #{order.pk}" + (f" — {reason}" if reason else ""),
        order=order,
    )


def post_payout_approved(payout_request):
    StoreTransaction.objects.create(
        store=payout_request.store,
        amount=-payout_request.amount,
        type=StoreTransaction.Type.PAYOUT,
        description=f"برداشت #{payout_request.pk}",
        payout_request=payout_request,
    )
