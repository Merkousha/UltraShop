import logging
import os
import sys
import threading
import time

from django.apps import AppConfig

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
        # Start the scheduler only in the actual web-server process.
        # - Django dev server: RUN_MAIN=true is set by the reloader in the child process.
        # - Gunicorn / Uvicorn workers: their entry point is in sys.argv[0].
        # Avoid starting during `migrate`, `shell`, `test`, etc.
        is_devserver_worker = os.environ.get("RUN_MAIN") == "true"
        is_prod_worker = any(
            name in (sys.argv[0] if sys.argv else "")
            for name in ("gunicorn", "uvicorn", "daphne")
        )
        if not (is_devserver_worker or is_prod_worker):
            return

        thread = threading.Thread(
            target=_cart_recovery_scheduler,
            name="cart-recovery-scheduler",
            daemon=True,
        )
        thread.start()
        logger.info("Cart recovery background scheduler started.")
