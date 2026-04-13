"""
CRM task reminder service.

Sends best-effort reminders for:
- tasks due today (first reminder)
- overdue tasks (first overdue reminder)
"""

from django.utils import timezone

from crm.models import SaleTask


def process_task_reminders(dry_run: bool = False) -> dict:
    """Send due/overdue reminders and mark tasks to avoid duplicate sends."""
    today = timezone.localdate()
    now = timezone.now()

    due_qs = SaleTask.objects.filter(
        is_done=False,
        due_date=today,
        reminder_sent_at__isnull=True,
    ).select_related("store", "assigned_to", "lead")

    overdue_qs = SaleTask.objects.filter(
        is_done=False,
        due_date__lt=today,
        overdue_reminder_sent_at__isnull=True,
    ).select_related("store", "assigned_to", "lead")

    sent_due = 0
    sent_overdue = 0
    skipped = 0

    for task in due_qs:
        recipient = _task_recipient(task)
        if not recipient:
            skipped += 1
            continue

        message = _build_due_message(task)
        if dry_run:
            sent_due += 1
            continue

        from core.services import send_notification

        ok = send_notification(
            task.store,
            recipient,
            message,
            subject="یادآوری وظیفه CRM",
        )
        if ok:
            task.reminder_sent_at = now
            task.save(update_fields=["reminder_sent_at"])
            sent_due += 1

    for task in overdue_qs:
        recipient = _task_recipient(task)
        if not recipient:
            skipped += 1
            continue

        message = _build_overdue_message(task)
        if dry_run:
            sent_overdue += 1
            continue

        from core.services import send_notification

        ok = send_notification(
            task.store,
            recipient,
            message,
            subject="هشدار تاخیر وظیفه CRM",
        )
        if ok:
            task.overdue_reminder_sent_at = now
            task.save(update_fields=["overdue_reminder_sent_at"])
            sent_overdue += 1

    return {
        "due_found": due_qs.count(),
        "overdue_found": overdue_qs.count(),
        "sent_due": sent_due,
        "sent_overdue": sent_overdue,
        "skipped": skipped,
    }


def _task_recipient(task: SaleTask) -> str:
    """Pick best notification target for a CRM task."""
    if task.assigned_to and task.assigned_to.email:
        return task.assigned_to.email
    if task.lead and task.lead.phone:
        return task.lead.phone
    if task.lead and task.lead.email:
        return task.lead.email
    return ""


def _build_due_message(task: SaleTask) -> str:
    lead_name = task.lead.name if task.lead else "بدون سرنخ"
    due_str = task.due_date.isoformat() if task.due_date else "امروز"
    return (
        f"یادآوری CRM: وظیفه «{task.title}» برای سرنخ «{lead_name}» "
        f"در تاریخ {due_str} سررسید شده است."
    )


def _build_overdue_message(task: SaleTask) -> str:
    lead_name = task.lead.name if task.lead else "بدون سرنخ"
    due_str = task.due_date.isoformat() if task.due_date else "نامشخص"
    return (
        f"هشدار CRM: وظیفه «{task.title}» برای سرنخ «{lead_name}» "
        f"از تاریخ {due_str} معوق مانده است."
    )
