import logging
import os
import sys
import threading
import time

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)

_REMINDER_INTERVAL_SECONDS = 3600  # every hour


def _crm_task_reminder_scheduler():
    # Let Django fully bootstrap before first run.
    time.sleep(20)
    while True:
        try:
            from crm.reminder_service import process_task_reminders

            result = process_task_reminders()
            if result["sent_due"] or result["sent_overdue"]:
                logger.info(
                    "CRM reminders: due=%d overdue=%d skipped=%d",
                    result["sent_due"],
                    result["sent_overdue"],
                    result["skipped"],
                )
        except Exception:
            logger.exception("CRM reminder scheduler error")
        time.sleep(_REMINDER_INTERVAL_SECONDS)


class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crm"
    verbose_name = "CRM"

    def ready(self):
        # In django-tenants mode, CRM tables are tenant-scoped and not present
        # on public schema; skip the public-process scheduler.
        if getattr(settings, "USE_DJANGO_TENANTS", False):
            logger.info("CRM task reminder scheduler disabled in django-tenants mode.")
            return

        is_devserver_worker = os.environ.get("RUN_MAIN") == "true"
        argv0_basename = os.path.basename(sys.argv[0]) if sys.argv else ""
        is_prod_worker = argv0_basename in ("gunicorn", "uvicorn", "daphne")
        if not (is_devserver_worker or is_prod_worker):
            return

        thread = threading.Thread(
            target=_crm_task_reminder_scheduler,
            name="crm-task-reminder-scheduler",
            daemon=True,
        )
        thread.start()
        logger.info("CRM task reminder scheduler started.")
