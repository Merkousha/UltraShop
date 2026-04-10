"""
Cart recovery service — core logic for sending abandoned-cart recovery messages.

Used by:
  - customers/apps.py AppConfig.ready() background scheduler (every hour)
  - customers/management/commands/send_cart_recovery.py (manual / cron)
"""

import logging

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)


def process_abandoned_carts(dry_run: bool = False) -> dict:
    """
    Find carts idle > 2 hours with no recovery message sent, send recovery
    messages and mark recovery_sent_at.

    Returns a summary dict: {"found": int, "processed": int, "skipped": int}.
    """
    from customers.models import AbandonedCart

    threshold = timezone.now() - timezone.timedelta(hours=2)
    carts = (
        AbandonedCart.objects.filter(
            recovery_sent_at__isnull=True,
            recovered=False,
            updated_at__lt=threshold,
        )
        .select_related("store", "customer")
        .order_by("updated_at")
    )

    found = carts.count()
    processed = 0
    skipped = 0

    for cart in carts:
        recipient = _get_recipient(cart)
        message = _build_message(cart)

        if dry_run:
            logger.info(
                "[DRY RUN] Cart #%d | store=%s | recipient=%s | items=%d",
                cart.pk,
                cart.store.name,
                recipient or "—",
                cart.item_count,
            )
            continue

        if recipient:
            try:
                from core.services import send_notification
                send_notification(cart.store, recipient, message)
            except Exception:
                logger.info(
                    "Cart recovery (log-only) [store=%s, cart_id=%d, recipient=%s]: %s",
                    cart.store.name,
                    cart.pk,
                    recipient,
                    message,
                )

        AbandonedCart.objects.filter(pk=cart.pk).update(
            recovery_sent_at=timezone.now()
        )
        processed += 1

    if found and not dry_run:
        logger.info(
            "Cart recovery complete: processed %d / %d cart(s).", processed, found
        )

    return {"found": found, "processed": processed, "skipped": skipped}


# ─── helpers ─────────────────────────────────────────────────────────────────

def _get_recipient(cart) -> str:
    if cart.customer:
        return cart.customer.phone or cart.customer.email or ""
    return cart.phone or cart.email or ""


def _build_message(cart) -> str:
    recovery_url = _build_recovery_url(cart)
    return (
        f"سلام! سبد خرید شما در فروشگاه «{cart.store.name}» با {cart.item_count} قلم محصول "
        f"هنوز منتظر است. برای تکمیل خرید اینجا کلیک کنید: {recovery_url}"
    )


def _build_recovery_url(cart) -> str:
    try:
        path = reverse(
            "storefront:cart-recover",
            kwargs={
                "store_username": cart.store.username,
                "token": str(cart.recovery_token),
            },
        )
        platform_domain = getattr(settings, "PLATFORM_DOMAIN", "localhost:8080")
        return f"https://{platform_domain}{path}"
    except Exception:
        return ""
