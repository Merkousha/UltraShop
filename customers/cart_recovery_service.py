"""
Cart recovery service — core logic for sending abandoned-cart recovery messages.

Used by:
  - customers/apps.py AppConfig.ready() background scheduler (every hour)
  - customers/management/commands/send_cart_recovery.py (manual / cron)
"""

import logging
import secrets
import string

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)

# Discount offered in recovery messages (percent).
RECOVERY_DISCOUNT_PERCENT = 10
# How long the auto-generated recovery discount code is valid (hours).
RECOVERY_DISCOUNT_EXPIRY_HOURS = 24


def process_abandoned_carts(dry_run: bool = False) -> dict:
    """
    Find carts idle > 2 hours with no recovery message sent, send recovery
    messages (including a one-time discount code) and mark recovery_sent_at.

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

        if dry_run:
            logger.info(
                "[DRY RUN] Cart #%d | store=%s | recipient=%s | items=%d",
                cart.pk,
                cart.store.name,
                recipient or "—",
                cart.item_count,
            )
            continue

        discount_code = _get_or_create_recovery_discount(cart)
        message = _build_message(cart, discount_code)

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


def _get_or_create_recovery_discount(cart) -> str:
    """
    Create (or reuse) a one-time recovery DiscountCode for this cart's store.

    Returns the discount code string, or "" on any error.
    """
    try:
        from catalog.models import DiscountCode

        # Reuse an existing unexpired recovery code for this store so we don't
        # flood the discount_codes table with every recovery run.
        prefix = "CART"
        now = timezone.now()
        expiry = now + timezone.timedelta(hours=RECOVERY_DISCOUNT_EXPIRY_HOURS)

        existing = DiscountCode.objects.filter(
            store=cart.store,
            code__startswith=prefix,
            discount_type=DiscountCode.DiscountType.PERCENT,
            value=RECOVERY_DISCOUNT_PERCENT,
            max_uses=1,
            used_count=0,
            is_active=True,
            expires_at__gt=now,
        ).first()

        if existing:
            return existing.code

        # Generate a short random alphanumeric suffix.
        alphabet = string.ascii_uppercase + string.digits
        suffix = "".join(secrets.choice(alphabet) for _ in range(6))
        code = f"{prefix}{suffix}"

        DiscountCode.objects.create(
            store=cart.store,
            code=code,
            discount_type=DiscountCode.DiscountType.PERCENT,
            value=RECOVERY_DISCOUNT_PERCENT,
            max_uses=1,
            used_count=0,
            is_active=True,
            expires_at=expiry,
        )
        return code

    except Exception:
        logger.exception(
            "Failed to create recovery discount for store=%s cart=%d",
            cart.store.pk,
            cart.pk,
        )
        return ""


def _build_message(cart, discount_code: str = "") -> str:
    recovery_url = _build_recovery_url(cart)
    if discount_code:
        return (
            f"سلام! سبد خرید شما در فروشگاه «{cart.store.name}» با {cart.item_count} قلم محصول "
            f"هنوز منتظر است. با کد تخفیف «{discount_code}» ({RECOVERY_DISCOUNT_PERCENT}٪ تخفیف) "
            f"خریدتان را تکمیل کنید: {recovery_url}"
        )
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
