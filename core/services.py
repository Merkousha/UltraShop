import logging

from django.conf import settings
from django.core.mail import send_mail

from core.models import AuditLog


logger = logging.getLogger(__name__)


def log_action(*, actor=None, store=None, action, resource_type="", resource_id="", details=None):
    AuditLog.objects.create(
        actor=actor,
        store=store,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else "",
        details=details or {},
    )


def send_notification(store, recipient: str, message: str, subject: str = "اطلاع‌رسانی فروشگاه") -> bool:
    """
    Send a best-effort notification.

    Current behavior:
    - Email recipients: send via Django email backend.
    - Phone-like recipients: log-only fallback (SMS provider hooks can be added later).

    Returns True when the notification is accepted for sending/logging.
    """
    if not recipient:
        return False

    recipient = recipient.strip()
    if not recipient:
        return False

    try:
        # Simple heuristic: if recipient contains '@', treat it as email.
        if "@" in recipient:
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ultra-shop.com")
            send_mail(subject, message, from_email, [recipient], fail_silently=True)
            return True

        # SMS gateway integration is intentionally deferred.
        logger.info(
            "Notification (sms-log) [store=%s recipient=%s]: %s",
            getattr(store, "pk", None),
            recipient,
            message,
        )
        return True
    except Exception:
        logger.exception(
            "Failed to send notification [store=%s recipient=%s]",
            getattr(store, "pk", None),
            recipient,
        )
        return False


# ─── Plan Limit Enforcement ──────────────────────────────────

class PlanLimitExceeded(Exception):
    """Raised when a store exceeds its plan resource limit."""
    pass


_RESOURCE_META = {
    "warehouses": ("max_warehouses", "انبار"),
    "products": ("max_products", "محصول"),
    "ai_requests": ("max_ai_requests_daily", "درخواست AI روزانه"),
}

_DEFAULT_LIMITS = {
    "max_warehouses": 5,
    "max_products": 100,
    "max_ai_requests_daily": 10,
    "allow_custom_domain": False,
}


def get_store_plan_limits(store):
    """Return the StorePlan for the store, or a default-limits object if no plan assigned."""
    from core.models import StorePlan
    if store.plan_id and store.plan:
        return store.plan
    # Return an unsaved StorePlan-like object with platform defaults
    plan = StorePlan(
        name="پیش‌فرض",
        slug="default",
        max_warehouses=_DEFAULT_LIMITS["max_warehouses"],
        max_products=_DEFAULT_LIMITS["max_products"],
        max_ai_requests_daily=_DEFAULT_LIMITS["max_ai_requests_daily"],
        allow_custom_domain=_DEFAULT_LIMITS["allow_custom_domain"],
    )
    return plan


def check_plan_limit(store, resource, current_count):
    """
    Raise PlanLimitExceeded if current_count has reached the plan limit for resource.
    resource: 'warehouses' | 'products' | 'ai_requests'
    Limit of 0 means unlimited.
    """
    field, label = _RESOURCE_META.get(resource, (None, resource))
    if not field:
        return  # unknown resource, skip
    plan = get_store_plan_limits(store)
    limit = getattr(plan, field, 0)
    if limit == 0:
        return  # unlimited
    if current_count >= limit:
        raise PlanLimitExceeded(
            f"محدودیت پلن: حداکثر {limit} {label} برای پلن «{plan.name}» مجاز است."
        )
