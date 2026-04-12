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

from django.core.management.base import BaseCommand

from customers.cart_recovery_service import process_abandoned_carts


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
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(self.style.NOTICE(f"{prefix}Running cart recovery..."))

        result = process_abandoned_carts(dry_run=dry_run)
        found = result["found"]
        processed = result["processed"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"Dry run complete. {found} cart(s) would be processed.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Done. Processed {processed}/{found} cart(s).")
            )
