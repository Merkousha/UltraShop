"""
Management command: send_cart_recovery

Finds AbandonedCart records where:
  - recovery_sent_at IS NULL
  - updated_at < now - 2 hours
  - recovered = False

For each, logs (or sends if SMS/email configured) a recovery message and
sets recovery_sent_at to now.

Usage:
    python manage.py send_cart_recovery
    python manage.py send_cart_recovery --dry-run
"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from customers.models import AbandonedCart

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Send recovery messages to customers with abandoned carts (idle > 2 hours)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be sent without actually marking records.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        threshold = timezone.now() - timezone.timedelta(hours=2)

        carts = AbandonedCart.objects.filter(
            recovery_sent_at__isnull=True,
            recovered=False,
            updated_at__lt=threshold,
        ).select_related("store", "customer").order_by("updated_at")

        total = carts.count()
        self.stdout.write(
            self.style.NOTICE(
                f"{'[DRY RUN] ' if dry_run else ''}Found {total} abandoned cart(s) to process."
            )
        )

        processed = 0
        for cart in carts:
            recipient = ""
            if cart.customer:
                recipient = cart.customer.phone or cart.customer.email
            elif cart.phone:
                recipient = cart.phone
            elif cart.email:
                recipient = cart.email

            item_count = cart.item_count
            store_name = cart.store.name

            message = (
                f"سلام! سبد خرید شما در فروشگاه «{store_name}» با {item_count} قلم محصول "
                f"هنوز منتظر است. برای تکمیل خرید بازگردید."
            )
            from django.urls import reverse
            from django.conf import settings as django_settings
            try:
                recovery_path = reverse(
                    "storefront:cart-recover",
                    kwargs={
                        "store_username": cart.store.username,
                        "token": str(cart.recovery_token),
                    },
                )
                platform_domain = getattr(django_settings, "PLATFORM_DOMAIN", "localhost:8080")
                recovery_url = f"https://{platform_domain}{recovery_path}"
            except Exception:
                recovery_url = ""

            message = (
                f"سلام! سبد خرید شما در فروشگاه «{store_name}» با {item_count} قلم محصول "
                f"هنوز منتظر است. برای تکمیل خرید اینجا کلیک کنید: {recovery_url}"
            )
            sent = False
            if recipient and not dry_run:
                try:
                    from core.services import send_notification
                    send_notification(cart.store, recipient, message)
                    sent = True
                except (ImportError, AttributeError):
                    # Notification service not configured — log instead
                    logger.info(
                        "Cart recovery [store=%s, cart_id=%d, recipient=%s]: %s",
                        store_name,
                        cart.pk,
                        recipient or "(no contact)",
                        message,
                    )
                    sent = True

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Cart #{cart.pk} | store={store_name} | "
                    f"recipient={recipient or '—'} | items={item_count}"
                )
            else:
                AbandonedCart.objects.filter(pk=cart.pk).update(
                    recovery_sent_at=timezone.now()
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Cart #{cart.pk} | store={store_name} | "
                        f"recipient={recipient or '—'} | items={item_count}"
                    )
                )
                processed += 1

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"Done. Processed {processed}/{total} cart(s).")
            )
        else:
            self.stdout.write(self.style.WARNING(f"Dry run complete. {total} cart(s) would be processed."))
