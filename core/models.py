from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """Append-only log for sensitive actions (PA-03)."""
    ACTION_REFUND = "refund"
    ACTION_PAYOUT_APPROVED = "payout_approved"
    ACTION_PAYOUT_REJECTED = "payout_rejected"  # keep same as action value in log_audit
    ACTION_STORE_SUSPENDED = "store_suspended"
    ACTION_STORE_REACTIVATED = "store_reactivated"
    ACTION_CHOICES = [
        (ACTION_REFUND, "بازپرداخت"),
        (ACTION_PAYOUT_APPROVED, "تأیید تسویه"),
        (ACTION_PAYOUT_REJECTED, "رد تسویه"),
        (ACTION_STORE_SUSPENDED, "تعلیق فروشگاه"),
        (ACTION_STORE_REACTIVATED, "فعال‌سازی فروشگاه"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50, blank=True)  # e.g. order, payout_request, store
    resource_id = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit log"
        verbose_name_plural = "Audit logs"

    def __str__(self):
        return f"{self.action} {self.resource_type}:{self.resource_id} at {self.created_at}"


def log_audit(actor, action, resource_type="", resource_id="", details="", store=None):
    """Create an append-only audit log entry."""
    AuditLog.objects.create(
        actor=actor,
        store=store,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        details=details[:2000] if details else "",
    )


class PlatformSettings(models.Model):
    """PA-10: Global platform config (singleton)."""
    name = models.CharField("Platform name", max_length=255, default="UltraShop")
    support_email = models.EmailField("Support email", blank=True)
    terms_url = models.URLField("Terms of service URL", blank=True)
    privacy_url = models.URLField("Privacy policy URL", blank=True)
    logo = models.ImageField("Logo", upload_to="platform/", blank=True, null=True)
    favicon = models.ImageField("Favicon", upload_to="platform/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform settings"
        verbose_name_plural = "Platform settings"

    def __str__(self):
        return self.name

    @classmethod
    def get_settings(cls):
        """Return the single settings row (create if missing)."""
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"name": "UltraShop"})
        return obj
