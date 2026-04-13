import logging
import os
import sys
import threading
import time

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)

_RECOVERY_INTERVAL_SECONDS = 3600  # check every hour


def _cart_recovery_scheduler():
    """Background daemon thread: run abandoned-cart recovery every hour."""
    # Brief startup delay so Django is fully initialized before first run.
    time.sleep(15)
    while True:
        try:
            from customers.cart_recovery_service import process_abandoned_carts

            result = process_abandoned_carts()
            if result["found"]:
                logger.info(
                    "Scheduled cart recovery: found=%d processed=%d",
                    result["found"],
                    result["processed"],
                )
        except Exception:
            logger.exception("Scheduled cart recovery error")
        time.sleep(_RECOVERY_INTERVAL_SECONDS)


class CustomersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "customers"

    def ready(self):
        # In django-tenants mode, customers tables live in tenant schemas.
        # This scheduler runs in the public process context, so skip startup
        # until a tenant-aware scheduler is introduced.
        if getattr(settings, "USE_DJANGO_TENANTS", False):
            logger.info("Cart recovery scheduler disabled in django-tenants mode.")
            return

        # Start the scheduler only in the actual web-server process.
        # - Django dev server: RUN_MAIN=true is set by the reloader in the child process.
        # - Gunicorn / Uvicorn workers: their entry point is in sys.argv[0].
        # Avoid starting during `migrate`, `shell`, `test`, etc.
        is_devserver_worker = os.environ.get("RUN_MAIN") == "true"
        argv0_basename = os.path.basename(sys.argv[0]) if sys.argv else ""
        is_prod_worker = argv0_basename in ("gunicorn", "uvicorn", "daphne")
        if not (is_devserver_worker or is_prod_worker):
            return

        thread = threading.Thread(
            target=_cart_recovery_scheduler,
            name="cart-recovery-scheduler",
            daemon=True,
        )
        thread.start()
        logger.info("Cart recovery background scheduler started.")
