"""
Management command: send_inventory_alerts  (SO-53)

Sends a weekly inventory summary email to each store owner listing
variants with critical or warning stock levels.

Usage:
    python manage.py send_inventory_alerts
    python manage.py send_inventory_alerts --dry-run
    python manage.py send_inventory_alerts --store-id 3
"""

import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Send weekly inventory summary emails to store owners "
        "for variants with critical / warning stock levels (SO-53)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be sent without actually sending emails.",
        )
        parser.add_argument(
            "--store-id",
            type=int,
            default=None,
            help="Restrict to a single store (by pk).",
        )

    def handle(self, *args, **options):
        from core.models import Store

        dry_run = options["dry_run"]
        store_id = options.get("store_id")

        stores = Store.objects.filter(is_active=True)
        if store_id:
            stores = stores.filter(pk=store_id)

        total_stores = stores.count()
        sent = 0
        skipped = 0

        for store in stores:
            result = send_inventory_alert_for_store(store, dry_run=dry_run)
            if result:
                sent += 1
                if dry_run:
                    self.stdout.write(f"[DRY RUN] Would notify: {store.name}")
                else:
                    self.stdout.write(self.style.SUCCESS(f"Sent: {store.name}"))
            else:
                skipped += 1

        summary = f"Done. {sent}/{total_stores} store(s) notified, {skipped} skipped."
        self.stdout.write(self.style.SUCCESS(summary))


def send_inventory_alert_for_store(store, dry_run: bool = False) -> bool:
    """
    Compute inventory forecast for *store* and, if there are any critical or
    warning items, email the store owner.

    Returns True if a notification was attempted/would be attempted.
    """
    from dashboard.inventory_forecast_service import get_inventory_forecast

    forecasts = get_inventory_forecast(store)
    alerts = [f for f in forecasts if f["urgency"] in ("critical", "warning")]

    if not alerts:
        return False

    owner = getattr(store, "owner", None)
    if not owner or not owner.email:
        return False

    if dry_run:
        return True

    try:
        _send_email(store, owner.email, alerts)
        return True
    except Exception:
        logger.exception("Failed to send inventory alert for store %s", store.pk)
        return False


def _send_email(store, recipient: str, alerts: list) -> None:
    from django.conf import settings as django_settings
    from django.core.mail import send_mail

    critical = [a for a in alerts if a["urgency"] == "critical"]
    warning = [a for a in alerts if a["urgency"] == "warning"]

    lines = []
    if critical:
        lines.append("🔴 بحرانی (کمتر از ۷ روز موجودی):")
        for a in critical:
            days = f"{a['days_until_stockout']} روز" if a["days_until_stockout"] is not None else "اتمام"
            lines.append(
                f"  • {a['product_name']} — {a['variant_name']}  |  "
                f"موجودی: {a['current_stock']}  |  روز تا اتمام: {days}"
            )
        lines.append("")

    if warning:
        lines.append("🟡 هشدار (کمتر از ۳۰ روز موجودی):")
        for a in warning:
            days = f"{a['days_until_stockout']} روز" if a["days_until_stockout"] is not None else "اتمام"
            lines.append(
                f"  • {a['product_name']} — {a['variant_name']}  |  "
                f"موجودی: {a['current_stock']}  |  روز تا اتمام: {days}"
            )

    body = (
        f"سلام،\n\n"
        f"گزارش هفتگی موجودی فروشگاه «{store.name}»:\n\n"
        + "\n".join(lines)
        + f"\n\nبرای مشاهده جزئیات وارد داشبورد شوید.\n\nتیم UltraShop"
    )

    from_email = getattr(django_settings, "DEFAULT_FROM_EMAIL", "noreply@ultra-shop.com")
    send_mail(
        subject=f"گزارش هفتگی موجودی — {store.name}",
        message=body,
        from_email=from_email,
        recipient_list=[recipient],
        fail_silently=False,
    )
